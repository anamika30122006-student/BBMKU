from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.models.audit import AuditLog
from app.utils.decorators import permission_required

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')


@audit_bp.route('', methods=['GET'])
@login_required
@permission_required('view_audit_logs')
def index():
    """Audit Log viewer for university compliance and oversight."""
    page = request.args.get('page', 1, type=int)
    per_page = 25

    query = AuditLog.query

    # Search filter
    search = request.args.get('search', '').strip()
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                AuditLog.action.ilike(search_filter),
                AuditLog.user_name.ilike(search_filter),
                AuditLog.file_number.ilike(search_filter),
                AuditLog.remarks.ilike(search_filter)
            )
        )

    action = request.args.get('action', '').strip()
    if action:
        query = query.filter(AuditLog.action == action)

    pagination = query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'audit/index.html',
        pagination=pagination,
        logs=pagination.items,
        search=search,
        action=action,
        title='System Audit Logs'
    )
