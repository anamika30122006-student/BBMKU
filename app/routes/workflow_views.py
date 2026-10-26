from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models.file import FileRecord, FileDecision
from app.models.department import Department

workflow_views_bp = Blueprint('workflow_views', __name__, url_prefix='/status')


@workflow_views_bp.route('/decisions', methods=['GET'])
@login_required
def decisions():
    """Approval & Decisions View: list of all approved/rejected files."""
    page = request.args.get('page', 1, type=int)
    decision_type = request.args.get('type', '')

    query = FileDecision.query
    if decision_type:
        query = query.filter(FileDecision.decision_type == decision_type)

    pagination = query.order_by(FileDecision.decided_at.desc()).paginate(page=page, per_page=15, error_out=False)

    return render_template(
        'workflow/decisions.html',
        pagination=pagination,
        decisions=pagination.items,
        decision_type=decision_type,
        title='File Decisions & Sanctions'
    )


@workflow_views_bp.route('/returned', methods=['GET'])
@login_required
def returned_files():
    """Returned Files: files sent back for correction."""
    page = request.args.get('page', 1, type=int)
    query = FileRecord.query.filter_by(status='Returned for Correction')

    if current_user.role.name not in ('EC_VIEWER', 'SYSTEM_ADMIN', 'APPROVING_AUTHORITY', 'REGISTRAR'):
        query = query.filter(
            or_(
                FileRecord.current_officer_id == current_user.id,
                FileRecord.initiating_officer_id == current_user.id
            )
        )

    pagination = query.order_by(FileRecord.last_action_at.desc()).paginate(page=page, per_page=15, error_out=False)

    return render_template(
        'workflow/returned.html',
        pagination=pagination,
        files=pagination.items,
        title='Files Returned for Correction'
    )


@workflow_views_bp.route('/closed', methods=['GET'])
@login_required
def closed_files():
    """Closed Files: completed university files."""
    page = request.args.get('page', 1, type=int)
    query = FileRecord.query.filter_by(status='Closed')

    pagination = query.order_by(FileRecord.closure_date.desc()).paginate(page=page, per_page=15, error_out=False)

    return render_template(
        'workflow/closed.html',
        pagination=pagination,
        files=pagination.items,
        title='Closed Files Repository'
    )


@workflow_views_bp.route('/archive', methods=['GET'])
@login_required
def archive():
    """University Central Record Archive."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()

    query = FileRecord.query.filter_by(status='Archived')
    if search:
        query = query.filter(
            or_(
                FileRecord.file_number.ilike(f"%{search}%"),
                FileRecord.subject.ilike(f"%{search}%"),
                FileRecord.archived_location.ilike(f"%{search}%")
            )
        )

    pagination = query.order_by(FileRecord.archived_date.desc()).paginate(page=page, per_page=15, error_out=False)

    return render_template(
        'workflow/archive.html',
        pagination=pagination,
        files=pagination.items,
        search=search,
        title='University File Archive'
    )
