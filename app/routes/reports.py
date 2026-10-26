import csv
import io
from datetime import datetime, timezone, timedelta, date
from flask import Blueprint, render_template, Response, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, or_, and_
from app.extensions import db
from app.models.file import FileRecord, FileMovement, FileDecision
from app.models.department import Department
from app.models.user import User
from app.services.metrics_service import get_dashboard_metrics, get_officer_pending_summary
from app.utils.decorators import permission_required

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('', methods=['GET'])
@login_required
@permission_required('view_reports')
def index():
    """Main Reports Hub displaying real-time analytical summaries."""
    metrics = get_dashboard_metrics()
    officer_pending = get_officer_pending_summary()

    # Average processing time (in days) for closed files
    closed_files = FileRecord.query.filter(FileRecord.closure_date.isnot(None)).all()
    avg_days = 0
    if closed_files:
        total_days = sum(f.total_age_days for f in closed_files)
        avg_days = round(total_days / len(closed_files), 1)

    return render_template(
        'reports/index.html',
        metrics=metrics,
        officer_pending=officer_pending,
        avg_processing_days=avg_days,
        total_closed=len(closed_files),
        title='Administrative Reports & Analytics'
    )


@reports_bp.route('/export/csv', methods=['GET'])
@login_required
@permission_required('export_reports')
def export_csv():
    """
    Exports university administrative reports to CSV based on the report_type parameter:
    - total_files
    - pending_files
    - overdue_files
    - department_pending
    - officer_pending
    - decisions
    - returned_files
    - movement_history
    - closed_archived
    """
    report_type = request.args.get('type', 'total_files')
    output = io.StringIO()
    writer = csv.writer(output)
    today = date.today()
    pending_statuses = ['Draft', 'Submitted', 'Under Process', 'Forwarded', 'Awaiting Receipt', 'Pending Approval']

    if report_type == 'total_files':
        filename = f"bbmku_all_files_{today}.csv"
        writer.writerow(['File Number', 'Subject', 'Category', 'Priority', 'Confidentiality', 'Status', 'Initiating Dept', 'Current Officer', 'Current Dept', 'Pending Days', 'Created Date'])
        files = FileRecord.query.order_by(FileRecord.id.desc()).all()
        for f in files:
            writer.writerow([
                f.file_number, f.subject, f.category, f.priority, f.confidentiality, f.status,
                f.initiating_department.name if f.initiating_department else 'N/A',
                f.current_officer.full_name if f.current_officer else 'N/A',
                f.current_department.name if f.current_department else 'N/A',
                f.pending_days, f.created_at.strftime('%Y-%m-%d %H:%M')
            ])

    elif report_type == 'pending_files':
        filename = f"bbmku_pending_files_{today}.csv"
        writer.writerow(['File Number', 'Subject', 'Current Officer', 'Current Department', 'Pending Since', 'Pending Days', 'Due Date', 'Delay Status', 'Next Action'])
        files = FileRecord.query.filter(FileRecord.status.in_(pending_statuses)).order_by(FileRecord.assigned_at.asc()).all()
        for f in files:
            writer.writerow([
                f.file_number, f.subject,
                f.current_officer.full_name if f.current_officer else 'N/A',
                f.current_department.name if f.current_department else 'N/A',
                f.assigned_at.strftime('%Y-%m-%d %H:%M') if f.assigned_at else 'N/A',
                f.pending_days, f.due_date.strftime('%Y-%m-%d') if f.due_date else 'None',
                f.delay_status, f.next_expected_action
            ])

    elif report_type == 'overdue_files':
        filename = f"bbmku_overdue_files_{today}.csv"
        writer.writerow(['File Number', 'Subject', 'Current Officer', 'Department', 'Due Date', 'Days Pending', 'Last Action', 'Remarks'])
        fifteen_days_ago = datetime.now(timezone.utc) - timedelta(days=15)
        files = FileRecord.query.filter(
            FileRecord.status.in_(pending_statuses),
            or_(
                and_(FileRecord.due_date.isnot(None), FileRecord.due_date < today),
                FileRecord.assigned_at < fifteen_days_ago
            )
        ).order_by(FileRecord.assigned_at.asc()).all()
        for f in files:
            writer.writerow([
                f.file_number, f.subject,
                f.current_officer.full_name if f.current_officer else 'N/A',
                f.current_department.name if f.current_department else 'N/A',
                f.due_date.strftime('%Y-%m-%d') if f.due_date else 'Breached 15d SLA',
                f.pending_days, f.last_action, f.last_action_remarks
            ])

    elif report_type == 'department_pending':
        filename = f"bbmku_dept_pending_summary_{today}.csv"
        writer.writerow(['Department Code', 'Department Name', 'Total Pending Files'])
        results = db.session.query(
            Department.code, Department.name, func.count(FileRecord.id)
        ).join(FileRecord, FileRecord.current_department_id == Department.id)\
         .filter(FileRecord.status.in_(pending_statuses))\
         .group_by(Department.id, Department.code, Department.name)\
         .order_by(func.count(FileRecord.id).desc()).all()
        for r in results:
            writer.writerow([r[0], r[1], r[2]])

    elif report_type == 'officer_pending':
        filename = f"bbmku_officer_pending_summary_{today}.csv"
        writer.writerow(['Officer Name', 'Designation', 'Department', 'Total Files in Custody'])
        results = get_officer_pending_summary()
        for r in results:
            writer.writerow([r.full_name, r.designation, r.department_name or 'Central Admin', r.pending_count])

    elif report_type == 'decisions':
        filename = f"bbmku_decisions_report_{today}.csv"
        writer.writerow(['File Number', 'Decision', 'Deciding Officer', 'Designation', 'Date & Time', 'Reason / Remarks', 'Conditions'])
        decisions = FileDecision.query.order_by(FileDecision.decided_at.desc()).all()
        for d in decisions:
            writer.writerow([
                d.file.file_number if d.file else 'N/A',
                d.decision_type,
                d.officer.full_name if d.officer else 'N/A',
                d.officer.designation if d.officer else 'N/A',
                d.decided_at.strftime('%Y-%m-%d %H:%M'),
                d.reason or d.remarks or '',
                d.conditions or ''
            ])

    elif report_type == 'returned_files':
        filename = f"bbmku_returned_files_{today}.csv"
        writer.writerow(['File Number', 'Subject', 'Current Custodian', 'Department', 'Return Reason', 'Correction Instructions', 'Date Returned'])
        returned_files = FileRecord.query.filter_by(status='Returned for Correction').all()
        for rf in returned_files:
            latest_return = FileDecision.query.filter_by(file_id=rf.id, decision_type='Returned for Correction')\
                .order_by(FileDecision.decided_at.desc()).first()
            writer.writerow([
                rf.file_number, rf.subject,
                rf.current_officer.full_name if rf.current_officer else 'N/A',
                rf.current_department.name if rf.current_department else 'N/A',
                latest_return.reason if latest_return else rf.last_action_remarks,
                latest_return.correction_instructions if latest_return else '',
                latest_return.decided_at.strftime('%Y-%m-%d %H:%M') if latest_return else ''
            ])

    elif report_type == 'movement_history':
        filename = f"bbmku_movement_history_{today}.csv"
        writer.writerow(['File Number', 'Movement Type', 'Dispatched By', 'From Dept', 'Dispatched To', 'To Dept', 'Dispatch Date', 'Mode', 'Received Date', 'Status', 'Remarks'])
        movements = FileMovement.query.order_by(FileMovement.created_at.desc()).limit(1000).all()
        for m in movements:
            writer.writerow([
                m.file.file_number if m.file else 'N/A',
                m.movement_type,
                m.from_user.full_name if m.from_user else 'N/A',
                m.from_department.code if m.from_department else 'N/A',
                m.to_user.full_name if m.to_user else 'N/A',
                m.to_department.code if m.to_department else 'N/A',
                m.dispatch_date.strftime('%Y-%m-%d %H:%M') if m.dispatch_date else '',
                m.dispatch_mode or 'Digital',
                m.received_date.strftime('%Y-%m-%d %H:%M') if m.received_date else 'Pending Receipt',
                'Received' if m.is_received else 'In Transit',
                m.remarks or ''
            ])

    elif report_type == 'closed_archived':
        filename = f"bbmku_closed_archived_{today}.csv"
        writer.writerow(['File Number', 'Subject', 'Status', 'Category', 'Closure Date', 'Archive Date', 'Archive Location', 'Closed By', 'Remarks'])
        files = FileRecord.query.filter(FileRecord.status.in_(['Closed', 'Archived'])).order_by(FileRecord.id.desc()).all()
        for f in files:
            writer.writerow([
                f.file_number, f.subject, f.status, f.category,
                f.closure_date.strftime('%Y-%m-%d') if f.closure_date else '',
                f.archived_date.strftime('%Y-%m-%d') if f.archived_date else '',
                f.archived_location or 'N/A',
                f.closed_by.full_name if f.closed_by else 'N/A',
                f.closure_remarks or ''
            ])
    else:
        flash('Invalid report export requested.', 'danger')
        return redirect(url_for('reports.index'))

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
