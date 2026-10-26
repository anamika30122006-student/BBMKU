from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.notification import Notification

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('', methods=['GET'])
@login_required
def index():
    """Notification Center."""
    page = request.args.get('page', 1, type=int)
    pagination = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).paginate(page=page, per_page=20, error_out=False)

    return render_template(
        'notifications/index.html',
        pagination=pagination,
        notifications=pagination.items,
        title='Notifications'
    )


@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_read(notification_id: int):
    """Mark a single notification as read."""
    notif = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()

    if notif.file_id:
        return redirect(url_for('files.detail', file_id=notif.file_id))
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all unread notifications for current user as read."""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications have been marked as read.', 'info')
    return redirect(url_for('notifications.index'))
