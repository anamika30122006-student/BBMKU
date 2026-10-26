from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models.file import FileRecord, FileMovement, FileDecision
from app.models.user import User, Role
from app.forms.file import (
    FileForwardForm,
    FileReturnForm,
    FileApproveForm,
    FileRejectForm,
    FileCloseForm,
    FileArchiveForm
)
from app.services.file_service import (
    forward_file,
    confirm_receipt,
    approve_file,
    reject_file,
    return_file_for_correction,
    close_file,
    archive_file
)
from app.utils.decorators import permission_required

workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')


@workflow_bp.route('/forward/<int:file_id>', methods=['POST'])
@login_required
@permission_required('forward_file')
def forward(file_id: int):
    """Forward file to next officer."""
    file_record = FileRecord.query.get_or_404(file_id)

    # Permission check: current user must be current custodian or have admin authority
    if file_record.current_officer_id != current_user.id and not current_user.is_admin:
        flash('You cannot forward this file because it is not currently assigned to you.', 'danger')
        return redirect(url_for('files.detail', file_id=file_id))

    form = FileForwardForm()
    # Populate choices for validation
    active_users = User.query.join(User.role).filter(
        User.is_active == True,
        User.id != current_user.id,
        Role.name != 'EC_VIEWER'
    ).all()
    form.to_user_id.choices = [(u.id, u.full_name) for u in active_users]

    if form.validate_on_submit():
        to_user = User.query.get_or_404(form.to_user_id.data)
        forward_file(
            file_record=file_record,
            from_user=current_user,
            to_user=to_user,
            remarks=form.remarks.data,
            action_type=form.action_type.data,
            dispatch_mode=form.dispatch_mode.data,
            dispatch_number=form.dispatch_number.data
        )
        flash(f"File {file_record.file_number} successfully forwarded to {to_user.full_name} ({to_user.designation}).", 'success')
    else:
        flash('Forwarding failed: please ensure recipient and remarks are properly filled.', 'danger')

    return redirect(url_for('files.detail', file_id=file_id))


@workflow_bp.route('/receive/<int:file_id>', methods=['POST'])
@login_required
@permission_required('receive_file')
def receive(file_id: int):
    """Confirm receipt of forwarded file."""
    file_record = FileRecord.query.get_or_404(file_id)

    if file_record.current_officer_id != current_user.id and not current_user.is_admin:
        flash('You can only acknowledge receipt of files assigned to you.', 'danger')
        return redirect(url_for('files.detail', file_id=file_id))

    remarks = request.form.get('receipt_remarks', 'File received and acknowledged in office custody.')
    confirm_receipt(file_record, current_user, remarks)
    flash(f"Receipt of File {file_record.file_number} confirmed. Status updated to 'Under Process'.", 'success')
    return redirect(url_for('files.detail', file_id=file_id))


@workflow_bp.route('/return/<int:file_id>', methods=['POST'])
@login_required
@permission_required('return_file')
def return_file(file_id: int):
    """Return file for correction to a previous officer."""
    file_record = FileRecord.query.get_or_404(file_id)

    if file_record.current_officer_id != current_user.id and not current_user.is_admin:
        flash('You cannot return this file as it is not in your active custody.', 'danger')
        return redirect(url_for('files.detail', file_id=file_id))

    form = FileReturnForm()
    users = User.query.join(User.role).filter(
        User.is_active == True,
        Role.name != 'EC_VIEWER'
    ).all()
    form.return_to_user_id.choices = [(u.id, u.full_name) for u in users]

    if form.validate_on_submit():
        return_to_user = User.query.get_or_404(form.return_to_user_id.data)
        return_file_for_correction(
            file_record=file_record,
            returning_user=current_user,
            return_to_user=return_to_user,
            reason=form.reason.data,
            correction_instructions=form.correction_instructions.data
        )
        flash(f"File {file_record.file_number} returned to {return_to_user.full_name} for correction.", 'warning')
    else:
        flash('Return action failed: please provide both reason and correction instructions.', 'danger')

    return redirect(url_for('files.detail', file_id=file_id))


@workflow_bp.route('/approve/<int:file_id>', methods=['POST'])
@login_required
@permission_required('approve_file')
def approve(file_id: int):
    """Formally approve file."""
    file_record = FileRecord.query.get_or_404(file_id)

    # University Rule: Prevent users from approving their own files when policy prohibits it
    if file_record.initiating_officer_id == current_user.id and not current_user.role.name in ('APPROVING_AUTHORITY', 'SYSTEM_ADMIN'):
        flash('University Policy Violation: Initiating officer cannot approve their own file.', 'danger')
        return redirect(url_for('files.detail', file_id=file_id))

    form = FileApproveForm()
    if form.validate_on_submit():
        approve_file(
            file_record=file_record,
            approving_user=current_user,
            remarks=form.remarks.data,
            conditions=form.conditions.data
        )
        flash(f"File {file_record.file_number} has been formally APPROVED.", 'success')
    else:
        flash('Approval failed: sanction remarks are required.', 'danger')

    return redirect(url_for('files.detail', file_id=file_id))


@workflow_bp.route('/reject/<int:file_id>', methods=['POST'])
@login_required
@permission_required('reject_file')
def reject(file_id: int):
    """Formally reject file with recorded reasoning."""
    file_record = FileRecord.query.get_or_404(file_id)
    form = FileRejectForm()

    if form.validate_on_submit():
        reject_file(
            file_record=file_record,
            rejecting_user=current_user,
            reason=form.reason.data,
            remarks=form.remarks.data
        )
        flash(f"File {file_record.file_number} has been REJECTED. Reasoning recorded in permanent audit history.", 'danger')
    else:
        flash('Rejection failed: mandatory reasoning must be provided.', 'danger')

    return redirect(url_for('files.detail', file_id=file_id))


@workflow_bp.route('/close/<int:file_id>', methods=['POST'])
@login_required
@permission_required('close_file')
def close(file_id: int):
    """Formally close completed file."""
    file_record = FileRecord.query.get_or_404(file_id)
    form = FileCloseForm()

    if form.validate_on_submit():
        close_file(file_record, current_user, form.remarks.data)
        flash(f"File {file_record.file_number} has been CLOSED.", 'info')
    else:
        flash('Closure failed: final action summary is required.', 'danger')

    return redirect(url_for('files.detail', file_id=file_id))


@workflow_bp.route('/archive/<int:file_id>', methods=['POST'])
@login_required
@permission_required('archive_file')
def archive(file_id: int):
    """Archive file into university record repository."""
    file_record = FileRecord.query.get_or_404(file_id)
    form = FileArchiveForm()

    if form.validate_on_submit():
        archive_file(
            file_record=file_record,
            archiving_user=current_user,
            archive_location=form.archive_location.data,
            remarks=form.remarks.data
        )
        flash(f"File {file_record.file_number} moved to University Archives at: {form.archive_location.data}.", 'success')
    else:
        flash('Archival failed: physical storage rack/location must be recorded.', 'danger')

    return redirect(url_for('files.detail', file_id=file_id))
