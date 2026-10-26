from datetime import datetime, timezone, timedelta, date
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from app.extensions import db
from app.models.file import FileRecord, FileMovement
from app.models.department import Department
from app.models.user import User

tracking_bp = Blueprint('tracking', __name__, url_prefix='/tracking')


@tracking_bp.route('', methods=['GET'])
@login_required
def index():
    """File Movement & Tracking Overview Hub."""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = FileMovement.query.order_by(FileMovement.created_at.desc())

    # Optional filter by department
    dept_id = request.args.get('department_id', type=int)
    if dept_id:
        query = query.filter(
            or_(
                FileMovement.from_department_id == dept_id,
                FileMovement.to_department_id == dept_id
            )
        )

    # Optional filter by movement type
    movement_type = request.args.get('type', '').strip()
    if movement_type:
        query = query.filter(FileMovement.movement_type == movement_type)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()

    return render_template(
        'tracking/index.html',
        pagination=pagination,
        movements=pagination.items,
        departments=departments,
        title='File Movement & Tracking'
    )


@tracking_bp.route('/my-files', methods=['GET'])
@login_required
def my_files():
    """My Assigned Files (currently in custody of logged-in officer)."""
    page = request.args.get('page', 1, type=int)
    per_page = 15

    query = FileRecord.query.filter(
        FileRecord.current_officer_id == current_user.id,
        FileRecord.status.notin_(['Closed', 'Archived'])
    ).order_by(FileRecord.created_at.desc(), FileRecord.id.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'tracking/my_files.html',
        pagination=pagination,
        files=pagination.items,
        title='My Assigned Files'
    )


@tracking_bp.route('/pending', methods=['GET'])
@login_required
def pending_files():
    """
    Pending Files tracking view with SLA filters:
    All, Today, >3 days, >7 days, >15 days, Overdue.
    """
    filter_type = request.args.get('filter', 'all')
    now = datetime.now(timezone.utc)
    today = date.today()
    pending_statuses = ['Draft', 'Submitted', 'Under Process', 'Forwarded', 'Awaiting Receipt', 'Pending Approval']

    query = FileRecord.query.filter(FileRecord.status.in_(pending_statuses))

    if filter_type == 'today':
        yesterday = now - timedelta(days=1)
        query = query.filter(FileRecord.assigned_at >= yesterday)
    elif filter_type == 'gt3':
        three_days_ago = now - timedelta(days=3)
        query = query.filter(FileRecord.assigned_at <= three_days_ago)
    elif filter_type == 'gt7':
        seven_days_ago = now - timedelta(days=7)
        query = query.filter(FileRecord.assigned_at <= seven_days_ago)
    elif filter_type == 'gt15':
        fifteen_days_ago = now - timedelta(days=15)
        query = query.filter(FileRecord.assigned_at <= fifteen_days_ago)
    elif filter_type == 'overdue':
        fifteen_days_ago = now - timedelta(days=15)
        query = query.filter(
            or_(
                and_(FileRecord.due_date.isnot(None), FileRecord.due_date < today),
                FileRecord.assigned_at < fifteen_days_ago
            )
        )

    # If regular officer, can see files related to their department or assigned to them
    if current_user.role.name not in ('EC_VIEWER', 'SYSTEM_ADMIN', 'APPROVING_AUTHORITY', 'REGISTRAR'):
        query = query.filter(
            or_(
                FileRecord.current_department_id == current_user.department_id,
                FileRecord.current_officer_id == current_user.id
            )
        )

    page = request.args.get('page', 1, type=int)
    per_page = 15
    pagination = query.order_by(FileRecord.created_at.desc(), FileRecord.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'tracking/pending.html',
        pagination=pagination,
        files=pagination.items,
        filter_type=filter_type,
        title='Pending Files & Delay Tracking'
    )
