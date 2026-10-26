from datetime import datetime, timezone, date
from app.extensions import db


class FileRecord(db.Model):
    """University official file record."""
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(64), unique=True, nullable=False, index=True)
    subject = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    # Categories: Academic, Financial, Examination, Establishment, Legal, Student Affairs, Purchase/Store, General
    category = db.Column(db.String(50), nullable=False, default='General', index=True)
    
    # Priority: Normal, Urgent, Immediate
    priority = db.Column(db.String(20), nullable=False, default='Normal', index=True)
    
    # Confidentiality: General, Confidential, Strictly Confidential
    confidentiality = db.Column(db.String(30), nullable=False, default='General', index=True)

    # Statuses:
    # Draft, Submitted, Under Process, Forwarded, Awaiting Receipt,
    # Pending Approval, Approved, Rejected, Returned for Correction, Closed, Archived
    status = db.Column(db.String(40), nullable=False, default='Submitted', index=True)

    # Initiator
    initiating_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    initiating_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    initiating_section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)

    # Current Location & Custody
    current_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    current_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False, index=True)
    current_section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)

    # Workflow tracking
    workflow_definition_id = db.Column(db.Integer, db.ForeignKey('workflow_definitions.id'), nullable=True)
    current_step_order = db.Column(db.Integer, default=1)

    # Timestamps & Tracking
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    due_date = db.Column(db.Date, nullable=True, index=True)
    assigned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    received_at = db.Column(db.DateTime, nullable=True)
    
    last_action = db.Column(db.String(100), default='File Registered')
    last_action_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_action_remarks = db.Column(db.Text, nullable=True)
    next_expected_action = db.Column(db.String(120), default='Review by Section Officer')

    # Closure & Archival
    closure_date = db.Column(db.DateTime, nullable=True)
    closure_remarks = db.Column(db.Text, nullable=True)
    closed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    archived_date = db.Column(db.DateTime, nullable=True)
    archived_location = db.Column(db.String(120), nullable=True)
    archived_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    initiating_officer = db.relationship('User', foreign_keys=[initiating_officer_id], back_populates='initiated_files', lazy='joined')
    initiating_department = db.relationship('Department', foreign_keys=[initiating_department_id], back_populates='files_initiated', lazy='joined')
    initiating_section = db.relationship('Section', foreign_keys=[initiating_section_id], lazy='joined')

    current_officer = db.relationship('User', foreign_keys=[current_officer_id], back_populates='assigned_files', lazy='joined')
    current_department = db.relationship('Department', foreign_keys=[current_department_id], back_populates='current_files', lazy='joined')
    current_section = db.relationship('Section', foreign_keys=[current_section_id], lazy='joined')

    closed_by = db.relationship('User', foreign_keys=[closed_by_id])
    archived_by = db.relationship('User', foreign_keys=[archived_by_id])
    workflow_definition = db.relationship('WorkflowDefinition', back_populates='files', lazy='joined')

    movements = db.relationship('FileMovement', back_populates='file', order_by='FileMovement.created_at.desc()', cascade='all, delete-orphan')
    decisions = db.relationship('FileDecision', back_populates='file', order_by='FileDecision.decided_at.desc()', cascade='all, delete-orphan')
    notes = db.relationship('FileNote', back_populates='file', order_by='FileNote.note_number.asc()', cascade='all, delete-orphan')
    documents = db.relationship('FileDocument', back_populates='file', order_by='FileDocument.uploaded_at.desc()', cascade='all, delete-orphan')

    @property
    def pending_days(self) -> int:
        """Calculates days the file has been pending with current officer."""
        if self.status in ('Approved', 'Rejected', 'Closed', 'Archived'):
            return 0
        ref_time = self.received_at or self.assigned_at or self.created_at
        now = datetime.now(timezone.utc)
        # make naive or aware safe
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=timezone.utc)
        delta = now - ref_time
        return max(0, delta.days)

    @property
    def total_age_days(self) -> int:
        """Total age of file in days since creation."""
        now = datetime.now(timezone.utc)
        created = self.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return max(0, (now - created).days)

    @property
    def is_overdue(self) -> bool:
        """Determines if the file has breached its specific due date or max SLA deadline."""
        if self.status in ('Approved', 'Rejected', 'Closed', 'Archived'):
            return False
        if self.due_date and date.today() > self.due_date:
            return True
        # If no explicit due date, check if pending > 15 days
        return self.pending_days >= 15

    @property
    def delay_status(self) -> str:
        """Returns delay category for administrative tracking."""
        if self.status in ('Approved', 'Rejected', 'Closed', 'Archived'):
            return 'Completed'
        if self.is_overdue:
            return 'Overdue'
        if self.pending_days >= 7:
            return 'Critical Delay'
        if self.pending_days >= 3:
            return 'Delayed'
        return 'On Track'

    @property
    def is_awaiting_receipt(self) -> bool:
        return self.status == 'Awaiting Receipt'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<FileRecord {self.file_number} - {self.status}>'


class FileMovement(db.Model):
    """Detailed file movement, forwarding, receipt, and dispatch audit record."""
    __tablename__ = 'file_movements'

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id', ondelete='CASCADE'), nullable=False, index=True)

    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    from_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    to_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)

    movement_type = db.Column(db.String(40), nullable=False) # Forward, Return, Submit, Dispatch, Re-route
    action_taken = db.Column(db.String(100), nullable=False) # e.g. "Forwarded for Verification", "Sent for Approval"
    remarks = db.Column(db.Text, nullable=True)

    dispatch_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    dispatch_number = db.Column(db.String(64), nullable=True) # Physical register reference
    dispatch_mode = db.Column(db.String(40), default='Digital Workflow') # Digital Workflow, Peon Book, Hand Delivery

    received_date = db.Column(db.DateTime, nullable=True)
    is_received = db.Column(db.Boolean, default=False, nullable=False)
    received_remarks = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    file = db.relationship('FileRecord', back_populates='movements')
    from_user = db.relationship('User', foreign_keys=[from_user_id], lazy='joined')
    to_user = db.relationship('User', foreign_keys=[to_user_id], lazy='joined')
    from_department = db.relationship('Department', foreign_keys=[from_department_id], lazy='joined')
    to_department = db.relationship('Department', foreign_keys=[to_department_id], lazy='joined')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<FileMovement File {self.file_id}: {self.from_user_id} -> {self.to_user_id}>'


class FileDecision(db.Model):
    """High-level decisions: Approval, Rejection, Return for Correction, Closure, Archival."""
    __tablename__ = 'file_decisions'

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id', ondelete='CASCADE'), nullable=False, index=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    decision_type = db.Column(db.String(40), nullable=False) # Approved, Rejected, Returned for Correction, Closed, Archived
    remarks = db.Column(db.Text, nullable=True)
    reason = db.Column(db.Text, nullable=True) # Required on rejection/return
    correction_instructions = db.Column(db.Text, nullable=True)
    conditions = db.Column(db.Text, nullable=True)

    decided_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    file = db.relationship('FileRecord', back_populates='decisions')
    officer = db.relationship('User', foreign_keys=[officer_id], lazy='joined')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<FileDecision File {self.file_id}: {self.decision_type} by {self.officer_id}>'


class FileNote(db.Model):
    """Internal file notes (Green Sheet / Notings) entered by officers."""
    __tablename__ = 'file_notes'

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id', ondelete='CASCADE'), nullable=False, index=True)
    note_number = db.Column(db.Integer, nullable=False) # Paragraph/Note 1, 2, 3...
    content = db.Column(db.Text, nullable=False)
    note_type = db.Column(db.String(40), default='Internal Note') # Internal Note, Formal Minute, Legal Opinion

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    author_designation = db.Column(db.String(150), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    file = db.relationship('FileRecord', back_populates='notes')
    author = db.relationship('User', back_populates='notes', lazy='joined')
    department = db.relationship('Department', lazy='joined')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<FileNote #{self.note_number} on File {self.file_id}>'


class FileDocument(db.Model):
    """Uploaded attachments, references, and supporting university documents."""
    __tablename__ = 'file_documents'

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id', ondelete='CASCADE'), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False) # Size in bytes
    mime_type = db.Column(db.String(100), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    version = db.Column(db.Integer, default=1)
    is_confidential = db.Column(db.Boolean, default=False)

    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    file = db.relationship('FileRecord', back_populates='documents')
    uploaded_by = db.relationship('User', lazy='joined')

    @property
    def file_size_display(self) -> str:
        """Human-readable file size."""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<FileDocument {self.original_filename} (File {self.file_id})>'
