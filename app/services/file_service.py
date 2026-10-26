from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Any
from app.extensions import db
from app.models.file import FileRecord, FileMovement, FileDecision, FileNote
from app.models.department import Department
from app.models.user import User
from app.services.audit_service import log_audit_event
from app.services.notification_service import send_notification


def generate_file_number(dept_code: str) -> str:
    """
    Generates official sequential file number:
    Format: BBMKU/{DEPT_CODE}/{YEAR}/{SEQ:04d}
    Example: BBMKU/ESTB/2026/0001
    """
    year = datetime.now(timezone.utc).year
    prefix = f"BBMKU/{dept_code.upper()}/{year}/"
    
    # Query latest file with this prefix
    latest = FileRecord.query.filter(FileRecord.file_number.like(f"{prefix}%"))\
        .order_by(FileRecord.id.desc()).first()
    
    if latest:
        try:
            seq_part = latest.file_number.split('/')[-1]
            next_seq = int(seq_part) + 1
        except (ValueError, IndexError):
            next_seq = FileRecord.query.count() + 1
    else:
        next_seq = 1
        
    return f"{prefix}{next_seq:04d}"


def create_file_record(
    subject: str,
    description: str,
    category: str,
    priority: str,
    confidentiality: str,
    initiating_officer: User,
    initiating_department: Department,
    initiating_section_id: int = None,
    assigned_officer: User = None,
    due_date: date = None,
    initial_remarks: str = None,
    workflow_definition_id: int = None
) -> FileRecord:
    """Creates a new official university file record."""
    assigned_to = assigned_officer or initiating_officer
    dept_code = initiating_department.code or 'GEN'
    file_number = generate_file_number(dept_code)
    
    now = datetime.now(timezone.utc)
    
    file_record = FileRecord(
        file_number=file_number,
        subject=subject.strip(),
        description=description.strip() if description else None,
        category=category,
        priority=priority,
        confidentiality=confidentiality,
        status='Submitted' if assigned_to.id != initiating_officer.id else 'Draft',
        initiating_officer_id=initiating_officer.id,
        initiating_department_id=initiating_department.id,
        initiating_section_id=initiating_section_id,
        current_officer_id=assigned_to.id,
        current_department_id=assigned_to.department_id or initiating_department.id,
        current_section_id=assigned_to.section_id,
        workflow_definition_id=workflow_definition_id,
        created_at=now,
        due_date=due_date,
        assigned_at=now,
        received_at=now if assigned_to.id == initiating_officer.id else None,
        last_action='File Created & Registered',
        last_action_at=now,
        last_action_remarks=initial_remarks,
        next_expected_action='Review and Initial Noting'
    )
    
    db.session.add(file_record)
    db.session.flush() # obtain file_record.id
    
    # Record initial movement
    movement = FileMovement(
        file_id=file_record.id,
        from_user_id=initiating_officer.id,
        to_user_id=assigned_to.id,
        from_department_id=initiating_department.id,
        to_department_id=assigned_to.department_id or initiating_department.id,
        movement_type='Submit' if assigned_to.id != initiating_officer.id else 'Created',
        action_taken='File Registered',
        remarks=initial_remarks or 'File initially created in UFMS',
        dispatch_date=now,
        dispatch_mode='Digital Workflow',
        is_received=(assigned_to.id == initiating_officer.id),
        received_date=now if assigned_to.id == initiating_officer.id else None
    )
    db.session.add(movement)
    
    # If initial remarks provided, add as Note 1
    if initial_remarks:
        note = FileNote(
            file_id=file_record.id,
            note_number=1,
            content=initial_remarks,
            note_type='Internal Note',
            author_id=initiating_officer.id,
            author_designation=initiating_officer.designation,
            department_id=initiating_department.id,
            created_at=now
        )
        db.session.add(note)
    
    db.session.commit()
    
    # Notify assigned officer if different
    if assigned_to.id != initiating_officer.id:
        send_notification(
            user_id=assigned_to.id,
            title=f"New File Assigned: {file_record.file_number}",
            message=f"File '{file_record.subject}' has been assigned to you by {initiating_officer.full_name}.",
            file_id=file_record.id,
            notification_type='Assignment'
        )
    
    log_audit_event(
        action='File Created',
        file_id=file_record.id,
        file_number=file_record.file_number,
        previous_state=None,
        new_state=file_record.status,
        remarks=f"Subject: {file_record.subject}",
        user=initiating_officer
    )
    
    return file_record


def forward_file(
    file_record: FileRecord,
    from_user: User,
    to_user: User,
    remarks: str,
    action_type: str = 'Forwarded for Processing',
    dispatch_mode: str = 'Digital Workflow',
    dispatch_number: str = None
) -> FileMovement:
    """Forwards file to another university officer with tracking."""
    now = datetime.now(timezone.utc)
    prev_status = file_record.status
    
    file_record.current_officer_id = to_user.id
    file_record.current_department_id = to_user.department_id or file_record.current_department_id
    file_record.current_section_id = to_user.section_id
    file_record.status = 'Awaiting Receipt'
    file_record.assigned_at = now
    file_record.received_at = None
    file_record.last_action = f"Forwarded to {to_user.designation}"
    file_record.last_action_at = now
    file_record.last_action_remarks = remarks
    file_record.next_expected_action = f"Awaiting Receipt by {to_user.full_name}"

    movement = FileMovement(
        file_id=file_record.id,
        from_user_id=from_user.id,
        to_user_id=to_user.id,
        from_department_id=from_user.department_id or file_record.current_department_id,
        to_department_id=to_user.department_id or file_record.current_department_id,
        movement_type='Forward',
        action_taken=action_type,
        remarks=remarks,
        dispatch_date=now,
        dispatch_number=dispatch_number,
        dispatch_mode=dispatch_mode,
        is_received=False
    )
    db.session.add(movement)
    db.session.commit()

    send_notification(
        user_id=to_user.id,
        title=f"File Forwarded to You: {file_record.file_number}",
        message=f"{from_user.full_name} ({from_user.designation}) has forwarded file '{file_record.subject}' to you. Remarks: {remarks}",
        file_id=file_record.id,
        notification_type='Movement'
    )

    log_audit_event(
        action='File Forwarded',
        file_id=file_record.id,
        file_number=file_record.file_number,
        previous_state=prev_status,
        new_state=file_record.status,
        remarks=f"From {from_user.full_name} to {to_user.full_name}. Remarks: {remarks}",
        user=from_user
    )

    return movement


def confirm_receipt(file_record: FileRecord, receiving_user: User, remarks: str = None):
    """Confirms receipt of a forwarded file by the receiving officer."""
    now = datetime.now(timezone.utc)
    prev_status = file_record.status

    file_record.status = 'Under Process'
    file_record.received_at = now
    file_record.last_action = f"Received by {receiving_user.designation}"
    file_record.last_action_at = now
    file_record.last_action_remarks = remarks or "File received into custody"
    file_record.next_expected_action = "Action / Noting by Current Officer"

    # Update latest pending movement record
    pending_mov = FileMovement.query.filter_by(
        file_id=file_record.id,
        to_user_id=receiving_user.id,
        is_received=False
    ).order_by(FileMovement.id.desc()).first()

    if pending_mov:
        pending_mov.is_received = True
        pending_mov.received_date = now
        pending_mov.received_remarks = remarks or "Received and acknowledged"

    db.session.commit()

    log_audit_event(
        action='File Received',
        file_id=file_record.id,
        file_number=file_record.file_number,
        previous_state=prev_status,
        new_state=file_record.status,
        remarks=remarks or f"Acknowledged by {receiving_user.full_name}",
        user=receiving_user
    )


def return_file_for_correction(
    file_record: FileRecord,
    returning_user: User,
    return_to_user: User,
    reason: str,
    correction_instructions: str
) -> FileDecision:
    """Returns file to a previous officer with required correction instructions."""
    now = datetime.now(timezone.utc)
    prev_status = file_record.status

    file_record.current_officer_id = return_to_user.id
    file_record.current_department_id = return_to_user.department_id or file_record.current_department_id
    file_record.current_section_id = return_to_user.section_id
    file_record.status = 'Returned for Correction'
    file_record.assigned_at = now
    file_record.received_at = None
    file_record.last_action = f"Returned for Correction by {returning_user.designation}"
    file_record.last_action_at = now
    file_record.last_action_remarks = f"Reason: {reason}. Instructions: {correction_instructions}"
    file_record.next_expected_action = f"Correction by {return_to_user.full_name}"

    decision = FileDecision(
        file_id=file_record.id,
        officer_id=returning_user.id,
        decision_type='Returned for Correction',
        remarks=reason,
        reason=reason,
        correction_instructions=correction_instructions,
        decided_at=now
    )
    db.session.add(decision)

    movement = FileMovement(
        file_id=file_record.id,
        from_user_id=returning_user.id,
        to_user_id=return_to_user.id,
        from_department_id=returning_user.department_id or file_record.current_department_id,
        to_department_id=return_to_user.department_id or file_record.current_department_id,
        movement_type='Return',
        action_taken='Returned for Correction',
        remarks=f"{reason} | Instructions: {correction_instructions}",
        dispatch_date=now,
        is_received=False
    )
    db.session.add(movement)
    db.session.commit()

    send_notification(
        user_id=return_to_user.id,
        title=f"File Returned for Correction: {file_record.file_number}",
        message=f"{returning_user.full_name} returned file '{file_record.subject}'. Reason: {reason}",
        file_id=file_record.id,
        notification_type='Return'
    )

    log_audit_event(
        action='File Returned for Correction',
        file_id=file_record.id,
        file_number=file_record.file_number,
        previous_state=prev_status,
        new_state=file_record.status,
        remarks=f"Reason: {reason}. Instructions: {correction_instructions}",
        user=returning_user
    )

    return decision


def approve_file(
    file_record: FileRecord,
    approving_user: User,
    remarks: str = None,
    conditions: str = None
) -> FileDecision:
    """Approves file by competent authority."""
    now = datetime.now(timezone.utc)
    prev_status = file_record.status

    file_record.status = 'Approved'
    file_record.last_action = f"Approved by {approving_user.designation}"
    file_record.last_action_at = now
    file_record.last_action_remarks = remarks
    file_record.next_expected_action = "Implementation / Issue of Sanction Order / Closure"

    decision = FileDecision(
        file_id=file_record.id,
        officer_id=approving_user.id,
        decision_type='Approved',
        remarks=remarks,
        conditions=conditions,
        decided_at=now
    )
    db.session.add(decision)
    db.session.commit()

    # Notify initiating officer
    send_notification(
        user_id=file_record.initiating_officer_id,
        title=f"File Approved: {file_record.file_number}",
        message=f"File '{file_record.subject}' has been formally APPROVED by {approving_user.full_name} ({approving_user.designation}).",
        file_id=file_record.id,
        notification_type='Approval'
    )

    log_audit_event(
        action='File Approved',
        file_id=file_record.id,
        file_number=file_record.file_number,
        previous_state=prev_status,
        new_state=file_record.status,
        remarks=remarks or "Approved without conditions",
        user=approving_user
    )

    return decision


def reject_file(
    file_record: FileRecord,
    rejecting_user: User,
    reason: str,
    remarks: str = None
) -> FileDecision:
    """Rejects file with mandatory recorded reasoning."""
    now = datetime.now(timezone.utc)
    prev_status = file_record.status

    file_record.status = 'Rejected'
    file_record.last_action = f"Rejected by {rejecting_user.designation}"
    file_record.last_action_at = now
    file_record.last_action_remarks = f"Reason: {reason}"
    file_record.next_expected_action = "File Rejected - No Further Forwarding"

    decision = FileDecision(
        file_id=file_record.id,
        officer_id=rejecting_user.id,
        decision_type='Rejected',
        reason=reason,
        remarks=remarks,
        decided_at=now
    )
    db.session.add(decision)
    db.session.commit()

    send_notification(
        user_id=file_record.initiating_officer_id,
        title=f"File Rejected: {file_record.file_number}",
        message=f"File '{file_record.subject}' has been REJECTED by {rejecting_user.full_name}. Reason: {reason}",
        file_id=file_record.id,
        notification_type='Rejection'
    )

    log_audit_event(
        action='File Rejected',
        file_id=file_record.id,
        file_number=file_record.file_number,
        previous_state=prev_status,
        new_state=file_record.status,
        remarks=f"Reason: {reason}",
        user=rejecting_user
    )

    return decision


def close_file(file_record: FileRecord, closing_user: User, remarks: str) -> FileDecision:
    """Closes completed file."""
    now = datetime.now(timezone.utc)
    prev_status = file_record.status

    file_record.status = 'Closed'
    file_record.closure_date = now
    file_record.closure_remarks = remarks
    file_record.closed_by_id = closing_user.id
    file_record.last_action = f"Closed by {closing_user.designation}"
    file_record.last_action_at = now
    file_record.last_action_remarks = remarks
    file_record.next_expected_action = "Ready for Record Archival"

    decision = FileDecision(
        file_id=file_record.id,
        officer_id=closing_user.id,
        decision_type='Closed',
        remarks=remarks,
        decided_at=now
    )
    db.session.add(decision)
    db.session.commit()

    log_audit_event(
        action='File Closed',
        file_id=file_record.id,
        file_number=file_record.file_number,
        previous_state=prev_status,
        new_state=file_record.status,
        remarks=remarks,
        user=closing_user
    )

    return decision


def archive_file(
    file_record: FileRecord,
    archiving_user: User,
    archive_location: str,
    remarks: str = None
) -> FileDecision:
    """Transfers closed file to university archives."""
    now = datetime.now(timezone.utc)
    prev_status = file_record.status

    file_record.status = 'Archived'
    file_record.archived_date = now
    file_record.archived_location = archive_location
    file_record.archived_by_id = archiving_user.id
    file_record.last_action = f"Archived at {archive_location}"
    file_record.last_action_at = now
    file_record.last_action_remarks = remarks
    file_record.next_expected_action = "Permanent University Record Archive"

    decision = FileDecision(
        file_id=file_record.id,
        officer_id=archiving_user.id,
        decision_type='Archived',
        remarks=f"Location: {archive_location} | {remarks or ''}",
        decided_at=now
    )
    db.session.add(decision)
    db.session.commit()

    log_audit_event(
        action='File Archived',
        file_id=file_record.id,
        file_number=file_record.file_number,
        previous_state=prev_status,
        new_state=file_record.status,
        remarks=f"Archived at: {archive_location}",
        user=archiving_user
    )

    return decision


def add_file_note(
    file_record: FileRecord,
    author: User,
    content: str,
    note_type: str = 'Internal Note'
) -> FileNote:
    """Adds a numbered file noting/green sheet paragraph."""
    now = datetime.now(timezone.utc)
    
    # Calculate next note number for this file
    latest_note = FileNote.query.filter_by(file_id=file_record.id)\
        .order_by(FileNote.note_number.desc()).first()
    next_num = (latest_note.note_number + 1) if latest_note else 1

    note = FileNote(
        file_id=file_record.id,
        note_number=next_num,
        content=content.strip(),
        note_type=note_type,
        author_id=author.id,
        author_designation=author.designation,
        department_id=author.department_id,
        created_at=now
    )
    db.session.add(note)
    
    file_record.last_action = f"Note #{next_num} added by {author.designation}"
    file_record.last_action_at = now
    db.session.commit()

    log_audit_event(
        action='File Note Added',
        file_id=file_record.id,
        file_number=file_record.file_number,
        remarks=f"Note #{next_num} ({note_type}) added",
        user=author
    )

    return note


def delete_file_record(file_record: FileRecord, user: User) -> bool:
    """Permanently deletes a file and its associated history."""
    file_num = file_record.file_number
    file_id = file_record.id
    file_subject = file_record.subject

    log_audit_event(
        action='File Deleted',
        file_id=file_id,
        file_number=file_num,
        remarks=f"File {file_num} ('{file_subject}') deleted from system by {user.designation}",
        user=user
    )

    db.session.delete(file_record)
    db.session.commit()
    return True
