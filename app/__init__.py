import os
from flask import Flask, render_template
from app.config import config_by_name
from app.extensions import db, login_manager, csrf, migrate
from app.models.user import User
from app.models.notification import Notification
from app.models.file import FileRecord
from app.routes import register_blueprints


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    from app.models.user import AnonymousUser
    login_manager.anonymous_user = AnonymousUser
    csrf.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    register_blueprints(app)

    # Context processors for global template data
    @app.context_processor
    def inject_global_data():
        from flask_login import current_user
        unread_count = 0
        my_pending_count = 0
        if current_user.is_authenticated:
            unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            my_pending_count = FileRecord.query.filter(
                FileRecord.current_officer_id == current_user.id,
                FileRecord.status.notin_(['Closed', 'Archived'])
            ).count()

        return {
            'unread_notifications_count': unread_count,
            'my_pending_files_count': my_pending_count,
            'university_name': app.config.get('UNIVERSITY_NAME', 'Binod Bihari Mahto Koyalanchal University (BBMKU)'),
            'university_code': app.config.get('UNIVERSITY_CODE', 'BBMKU'),
            'university_location': app.config.get('UNIVERSITY_LOCATION', 'Dhanbad, Jharkhand')
        }

    # Custom Jinja filters for university UI
    @app.template_filter('status_badge')
    def status_badge_filter(status):
        badges = {
            'Draft': 'badge-draft',
            'Submitted': 'badge-submitted',
            'Under Process': 'badge-under-process',
            'Forwarded': 'badge-forwarded',
            'Awaiting Receipt': 'badge-awaiting-receipt',
            'Pending Approval': 'badge-pending-approval',
            'Approved': 'badge-approved',
            'Rejected': 'badge-rejected',
            'Returned for Correction': 'badge-returned',
            'Closed': 'badge-closed',
            'Archived': 'badge-archived'
        }
        return badges.get(status, 'badge-default')

    @app.template_filter('priority_badge')
    def priority_badge_filter(priority):
        badges = {
            'Normal': 'priority-normal',
            'Urgent': 'priority-urgent',
            'Immediate': 'priority-immediate'
        }
        return badges.get(priority, 'priority-normal')

    @app.template_filter('delay_badge')
    def delay_badge_filter(delay_status):
        badges = {
            'On Track': 'delay-normal',
            'Delayed': 'delay-warning',
            'Critical Delay': 'delay-critical',
            'Overdue': 'delay-overdue',
            'Completed': 'delay-completed'
        }
        return badges.get(delay_status, 'delay-normal')

    @app.template_filter('format_date')
    def format_date_filter(val):
        if not val:
            return '—'
        return val.strftime('%d-%b-%Y')

    @app.template_filter('format_datetime')
    def format_datetime_filter(val):
        if not val:
            return '—'
        return val.strftime('%d-%b-%Y %I:%M %p')

    @app.template_filter('nl2br')
    def nl2br_filter(val):
        if not val:
            return ''
        from markupsafe import Markup, escape
        escaped_val = escape(val)
        return Markup(escaped_val.replace('\n', '<br>\n'))

    # Error Handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app
