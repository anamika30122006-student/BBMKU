from datetime import datetime, timezone, date, timedelta
from pathlib import Path
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, abort
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from app.extensions import db
from app.models.file import FileRecord, FileDocument, FileNote, FileMovement, FileDecision
from app.models.department import Department, Section
from app.models.user import User, Role
from app.forms.file import (
    FileCreateForm,
    FileFilterForm,
    FileNoteForm,
    FileDocumentUploadForm,
    FileForwardForm,
    FileReturnForm,
    FileApproveForm,
    FileRejectForm,
    FileCloseForm,
    FileArchiveForm
)
from app.services.file_service import create_file_record, add_file_note, delete_file_record
from app.utils.decorators import permission_required
from app.utils.file_storage import save_uploaded_file

files_bp = Blueprint('files', __name__, url_prefix='/files')


def check_confidential_access(file_record: FileRecord) -> bool:
    """Confidentiality filter check."""
    if file_record.confidentiality == 'General':
        return True
    # EC Sir, VC, Registrar, and System Admin have overarching clearance
    if current_user.role.name in ('EC_VIEWER', 'SYSTEM_ADMIN', 'APPROVING_AUTHORITY', 'REGISTRAR'):
        return True
    # Initiating or Current assigned officer has clearance
    if current_user.id in (file_record.initiating_officer_id, file_record.current_officer_id):
        return True
    # Head of initiating or current department has clearance
    if current_user.role.name == 'DEPARTMENT_HEAD' and current_user.department_id in (file_record.initiating_department_id, file_record.current_department_id):
        return True
    return False


@files_bp.route('', methods=['GET'])
@login_required
def list_files():
    """All Files page with multi-parameter search, filters, and pagination."""
    form = FileFilterForm(request.args)
    form.department_id.choices = [(0, 'All Departments')] + [
        (d.id, f"{d.code} - {d.name}") for d in Department.query.filter_by(is_active=True).order_by(Department.name).all()
    ]
    form.category.choices = [('', 'All Categories')] + [
        ('Establishment', 'Establishment / Administration'),
        ('Academic', 'Academic & Curriculum'),
        ('Financial', 'Finance & Accounts'),
        ('Examination', 'Examination & Confidential'),
        ('Student Affairs', 'Student Welfare & Admissions'),
        ('Legal', 'Legal & RTI Cell'),
        ('Purchase/Store', 'Purchase & Tender / Store'),
        ('General', 'General Administrative Matter')
    ]
    form.status.choices = [('', 'All Statuses')] + [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Under Process', 'Under Process'),
        ('Forwarded', 'Forwarded'),
        ('Awaiting Receipt', 'Awaiting Receipt'),
        ('Pending Approval', 'Pending Approval'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Returned for Correction', 'Returned for Correction'),
        ('Closed', 'Closed'),
        ('Archived', 'Archived')
    ]
    form.priority.choices = [('', 'All Priorities'), ('Normal', 'Normal'), ('Urgent', 'Urgent'), ('Immediate', 'Immediate')]
    form.confidentiality.choices = [('', 'All Levels'), ('General', 'General'), ('Confidential', 'Confidential'), ('Strictly Confidential', 'Strictly Confidential')]

    query = FileRecord.query

    # Search term
    search = request.args.get('search', '').strip()
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                FileRecord.file_number.ilike(search_filter),
                FileRecord.subject.ilike(search_filter),
                FileRecord.description.ilike(search_filter)
            )
        )

    # Department filter
    dept_id = request.args.get('department_id', type=int)
    if dept_id and dept_id > 0:
        query = query.filter(
            or_(
                FileRecord.current_department_id == dept_id,
                FileRecord.initiating_department_id == dept_id
            )
        )

    # Category filter
    category = request.args.get('category', '').strip()
    if category:
        query = query.filter(FileRecord.category == category)

    # Status filter
    status = request.args.get('status', '').strip()
    if status:
        query = query.filter(FileRecord.status == status)

    # Priority filter
    priority = request.args.get('priority', '').strip()
    if priority:
        query = query.filter(FileRecord.priority == priority)

    # Confidentiality filter
    confidentiality = request.args.get('confidentiality', '').strip()
    if confidentiality:
        query = query.filter(FileRecord.confidentiality == confidentiality)

    # Delay filter
    delay_filter = request.args.get('delay_filter', '').strip()
    now = datetime.now(timezone.utc)
    today = date.today()
    pending_statuses = ['Draft', 'Submitted', 'Under Process', 'Forwarded', 'Awaiting Receipt', 'Pending Approval']

    if delay_filter == 'today':
        yesterday = now - timedelta(days=1)
        query = query.filter(FileRecord.status.in_(pending_statuses), FileRecord.assigned_at >= yesterday)
    elif delay_filter == 'gt3':
        three_days_ago = now - timedelta(days=3)
        query = query.filter(FileRecord.status.in_(pending_statuses), FileRecord.assigned_at <= three_days_ago)
    elif delay_filter == 'gt7':
        seven_days_ago = now - timedelta(days=7)
        query = query.filter(FileRecord.status.in_(pending_statuses), FileRecord.assigned_at <= seven_days_ago)
    elif delay_filter == 'gt15':
        fifteen_days_ago = now - timedelta(days=15)
        query = query.filter(FileRecord.status.in_(pending_statuses), FileRecord.assigned_at <= fifteen_days_ago)
    elif delay_filter == 'overdue':
        fifteen_days_ago = now - timedelta(days=15)
        query = query.filter(
            FileRecord.status.in_(pending_statuses),
            or_(
                and_(FileRecord.due_date.isnot(None), FileRecord.due_date < today),
                FileRecord.assigned_at < fifteen_days_ago
            )
        )

    # Confidentiality restriction in search results: if regular user, hide Strictly Confidential
    if current_user.role.name not in ('EC_VIEWER', 'SYSTEM_ADMIN', 'APPROVING_AUTHORITY', 'REGISTRAR'):
        query = query.filter(
            or_(
                FileRecord.confidentiality == 'General',
                FileRecord.initiating_officer_id == current_user.id,
                FileRecord.current_officer_id == current_user.id
            )
        )

    # Sorting & Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 15
    pagination = query.order_by(FileRecord.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'files/list.html',
        pagination=pagination,
        files=pagination.items,
        form=form,
        title='All University Files'
    )


@files_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('create_file')
def create():
    """Create New File registration."""
    form = FileCreateForm()
    
    # Populate department choices
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    form.department_id.choices = [(d.id, f"{d.code} - {d.name}") for d in departments]
    
    # Set default initiating department to current user's department
    if request.method == 'GET' and current_user.department_id:
        form.department_id.data = current_user.department_id

    # Populate section choices
    user_dept_id = form.department_id.data or (current_user.department_id or (departments[0].id if departments else 0))
    sections = Section.query.filter_by(department_id=user_dept_id, is_active=True).order_by(Section.name).all()
    form.section_id.choices = [(0, '-- None / Whole Department --')] + [(s.id, f"{s.code} - {s.name}") for s in sections]

    # Populate assigned officer choices (all active processing officers, excluding observer/viewer roles)
    active_users = User.query.join(User.role).filter(
        User.is_active == True,
        Role.name != 'EC_VIEWER'
    ).order_by(User.full_name).all()
    form.assigned_officer_id.choices = [
        (u.id, f"{u.full_name} — {u.designation}") for u in active_users
    ]
    if request.method == 'GET':
        form.assigned_officer_id.data = current_user.id

    if form.validate_on_submit():
        dept = Department.query.get(form.department_id.data)
        assigned_user = User.query.get(form.assigned_officer_id.data)
        section_id = form.section_id.data if form.section_id.data and form.section_id.data > 0 else None

        file_rec = create_file_record(
            subject=form.subject.data,
            description=form.description.data,
            category=form.category.data,
            priority=form.priority.data,
            confidentiality=form.confidentiality.data,
            initiating_officer=current_user,
            initiating_department=dept,
            initiating_section_id=section_id,
            assigned_officer=assigned_user,
            due_date=form.due_date.data,
            initial_remarks=form.initial_remarks.data
        )

        # Handle attachment if uploaded
        if form.document.data:
            orig_name, stored_name, full_path, size_b, mime = save_uploaded_file(form.document.data, custom_prefix='doc_init')
            doc = FileDocument(
                file_id=file_rec.id,
                original_filename=orig_name,
                stored_filename=stored_name,
                file_path=full_path,
                file_size=size_b,
                mime_type=mime,
                title=f"Supporting Doc: {orig_name}",
                uploaded_by_id=current_user.id
            )
            db.session.add(doc)
            db.session.commit()

        flash(f"File successfully created and registered! File Number: {file_rec.file_number}", 'success')
        return redirect(url_for('files.detail', file_id=file_rec.id))

    return render_template(
        'files/create.html',
        form=form,
        title='Register New File'
    )


@files_bp.route('/<int:file_id>', methods=['GET'])
@login_required
def detail(file_id: int):
    """
    Dedicated File Details Page.
    Prominently displays file number, current officer, department, pending duration,
    timeline, notings, documents, decisions, and movement history.
    """
    file_record = FileRecord.query.get_or_404(file_id)

    if not check_confidential_access(file_record):
        flash('This file is confidential. You do not have clearance to view its details.', 'danger')
        abort(403)

    # Forms for actions inside modal / page
    note_form = FileNoteForm()
    doc_form = FileDocumentUploadForm()
    forward_form = FileForwardForm()
    return_form = FileReturnForm()
    approve_form = FileApproveForm()
    reject_form = FileRejectForm()
    close_form = FileCloseForm()
    archive_form = FileArchiveForm()

    # Populate choices for forward: Active processing officers, excluding viewer roles and current user
    active_users = User.query.join(User.role).filter(
        User.is_active == True,
        User.id != current_user.id,
        Role.name != 'EC_VIEWER'
    ).order_by(User.department_id, User.full_name).all()
    forward_form.to_user_id.choices = [
        (
            u.id,
            f"[{u.department.code}] {u.full_name} — {u.designation}" if u.department
            else f"[HQ] {u.full_name} — {u.designation}"
        )
        for u in active_users
    ]

    # Populate return choices: all processing officers who previously handled this file
    previous_officer_ids = {m.from_user_id for m in file_record.movements}.union({file_record.initiating_officer_id})
    previous_officer_ids.discard(current_user.id)
    prev_users = User.query.join(User.role).filter(
        User.id.in_(previous_officer_ids),
        Role.name != 'EC_VIEWER'
    ).all() if previous_officer_ids else active_users
    return_form.return_to_user_id.choices = [
        (
            u.id,
            f"[{u.department.code}] {u.full_name} — {u.designation}" if u.department
            else f"[HQ] {u.full_name} — {u.designation}"
        )
        for u in prev_users
    ]

    return render_template(
        'files/detail.html',
        file=file_record,
        note_form=note_form,
        doc_form=doc_form,
        forward_form=forward_form,
        return_form=return_form,
        approve_form=approve_form,
        reject_form=reject_form,
        close_form=close_form,
        archive_form=archive_form,
        title=f"File: {file_record.file_number}"
    )


@files_bp.route('/<int:file_id>/notes/add', methods=['POST'])
@login_required
@permission_required('add_note')
def add_note(file_id: int):
    """Add green sheet noting to file."""
    file_record = FileRecord.query.get_or_404(file_id)
    form = FileNoteForm()

    if form.validate_on_submit():
        note = add_file_note(
            file_record=file_record,
            author=current_user,
            content=form.content.data,
            note_type=form.note_type.data
        )
        flash(f"Note #{note.note_number} successfully recorded on file green-sheet.", 'success')
    else:
        flash('Failed to add note: noting content cannot be empty.', 'danger')

    return redirect(url_for('files.detail', file_id=file_id))


@files_bp.route('/<int:file_id>/documents/upload', methods=['POST'])
@login_required
@permission_required('upload_document')
def upload_document(file_id: int):
    """Upload supporting document attachment to file."""
    file_record = FileRecord.query.get_or_404(file_id)
    form = FileDocumentUploadForm()

    if form.validate_on_submit():
        orig_name, stored_name, full_path, size_b, mime = save_uploaded_file(form.document.data, custom_prefix='doc_att')
        doc = FileDocument(
            file_id=file_record.id,
            original_filename=orig_name,
            stored_filename=stored_name,
            file_path=full_path,
            file_size=size_b,
            mime_type=mime,
            title=form.title.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            uploaded_by_id=current_user.id
        )
        db.session.add(doc)
        db.session.commit()
        flash(f"Document '{orig_name}' successfully attached to file.", 'success')
    else:
        flash('Failed to upload document. Please ensure a valid file format is selected.', 'danger')

    return redirect(url_for('files.detail', file_id=file_id))


@files_bp.route('/<int:file_id>/documents/<int:doc_id>/download', methods=['GET'])
@login_required
def download_document(file_id: int, doc_id: int):
    """Protected document download endpoint."""
    file_record = FileRecord.query.get_or_404(file_id)
    if not check_confidential_access(file_record):
        abort(403)

    doc = FileDocument.query.filter_by(id=doc_id, file_id=file_id).first_or_404()
    file_path = Path(doc.file_path)

    if not file_path.exists():
        flash('Requested document was not found on the secure storage volume.', 'danger')
        return redirect(url_for('files.detail', file_id=file_id))

    return send_file(
        file_path,
        as_attachment=True,
        download_name=doc.original_filename,
        mimetype=doc.mime_type
    )


@files_bp.route('/<int:file_id>/delete', methods=['POST'])
@login_required
def delete(file_id: int):
    """Delete / Discard an initiated file record."""
    file_record = db.session.get(FileRecord, file_id)
    if not file_record:
        abort(404)

    # Permission check: Admin or initiating officer in active/unclosed stages
    can_delete = current_user.is_admin or (
        file_record.initiating_officer_id == current_user.id and
        file_record.status in ('Draft', 'Submitted', 'Awaiting Receipt', 'Under Process')
    )
    if not can_delete:
        flash('You do not have administrative permission to delete this file.', 'danger')
        return redirect(url_for('files.detail', file_id=file_id))

    file_num = file_record.file_number
    delete_file_record(file_record, current_user)
    flash(f"File {file_num} has been successfully deleted.", 'success')
    return redirect(url_for('files.list_files'))

