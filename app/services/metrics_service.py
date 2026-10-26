from datetime import date, datetime, timezone, timedelta
from sqlalchemy import func, case, and_, or_
from app.extensions import db
from app.models.file import FileRecord, FileMovement, FileDecision
from app.models.department import Department
from app.models.user import User


def get_dashboard_metrics(user=None) -> dict:
    """
    Computes live dashboard statistics from database records.
    If user is restricted, filters appropriately; EC Sir and Admin see entire university.
    """
    base_query = FileRecord.query
    today = date.today()

    total_files = base_query.count()
    
    # Active Pending Files (Under Process, Submitted, Forwarded, Awaiting Receipt, Pending Approval)
    pending_statuses = ['Draft', 'Submitted', 'Under Process', 'Forwarded', 'Awaiting Receipt', 'Pending Approval']
    pending_files = base_query.filter(FileRecord.status.in_(pending_statuses)).count()
    
    approved_files = base_query.filter(FileRecord.status == 'Approved').count()
    rejected_files = base_query.filter(FileRecord.status == 'Rejected').count()
    returned_files = base_query.filter(FileRecord.status == 'Returned for Correction').count()
    closed_files = base_query.filter(FileRecord.status == 'Closed').count()
    archived_files = base_query.filter(FileRecord.status == 'Archived').count()

    # Overdue/Delayed Files:
    # 1. Active files where due_date is passed: due_date < today
    # OR 2. Active files pending more than 15 days
    fifteen_days_ago = datetime.now(timezone.utc) - timedelta(days=15)
    overdue_files = base_query.filter(
        FileRecord.status.in_(pending_statuses),
        or_(
            and_(FileRecord.due_date.isnot(None), FileRecord.due_date < today),
            FileRecord.assigned_at < fifteen_days_ago
        )
    ).count()

    # A. Files Currently Pending (Top 10 - Newest files first)
    pending_list = base_query.filter(FileRecord.status.in_(pending_statuses))\
        .order_by(FileRecord.created_at.desc(), FileRecord.id.desc())\
        .limit(10).all()

    # B. Recently Updated Files (Top 6)
    recently_updated = base_query.order_by(FileRecord.last_action_at.desc()).limit(6).all()

    # C. Files Pending Beyond Their Due Date
    overdue_list = base_query.filter(
        FileRecord.status.in_(pending_statuses),
        or_(
            and_(FileRecord.due_date.isnot(None), FileRecord.due_date < today),
            FileRecord.assigned_at < fifteen_days_ago
        )
    ).order_by(FileRecord.due_date.asc().nullslast(), FileRecord.assigned_at.asc()).limit(8).all()

    # D. Department-wise Pending Summary
    dept_pending = db.session.query(
        Department.name,
        Department.code,
        func.count(FileRecord.id).label('total_pending')
    ).join(FileRecord, FileRecord.current_department_id == Department.id)\
     .filter(FileRecord.status.in_(pending_statuses))\
     .group_by(Department.id, Department.name, Department.code)\
     .order_by(func.count(FileRecord.id).desc()).all()

    # E. Recent File Decisions (Top 6)
    recent_decisions = FileDecision.query.order_by(FileDecision.decided_at.desc()).limit(6).all()

    return {
        'total_files': total_files,
        'pending_files': pending_files,
        'approved_files': approved_files,
        'rejected_files': rejected_files,
        'returned_files': returned_files,
        'overdue_files': overdue_files,
        'closed_files': closed_files,
        'archived_files': archived_files,
        'pending_list': pending_list,
        'recently_updated': recently_updated,
        'overdue_list': overdue_list,
        'dept_pending': dept_pending,
        'recent_decisions': recent_decisions
    }


def get_officer_pending_summary() -> list:
    """Returns officer-wise count of pending files."""
    pending_statuses = ['Draft', 'Submitted', 'Under Process', 'Forwarded', 'Awaiting Receipt', 'Pending Approval']
    return db.session.query(
        User.id,
        User.full_name,
        User.designation,
        Department.name.label('department_name'),
        func.count(FileRecord.id).label('pending_count')
    ).join(FileRecord, FileRecord.current_officer_id == User.id)\
     .outerjoin(Department, User.department_id == Department.id)\
     .filter(FileRecord.status.in_(pending_statuses))\
     .group_by(User.id, User.full_name, User.designation, Department.name)\
     .order_by(func.count(FileRecord.id).desc()).all()
