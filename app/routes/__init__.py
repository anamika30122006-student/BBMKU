from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.files import files_bp
from app.routes.workflow import workflow_bp
from app.routes.tracking import tracking_bp
from app.routes.workflow_views import workflow_views_bp
from app.routes.reports import reports_bp
from app.routes.notifications import notifications_bp
from app.routes.audit import audit_bp
from app.routes.admin import admin_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(workflow_bp)
    app.register_blueprint(tracking_bp)
    app.register_blueprint(workflow_views_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(admin_bp)
