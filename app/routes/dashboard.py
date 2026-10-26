from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.services.metrics_service import get_dashboard_metrics

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """
    Consolidated administrative dashboard for EC Sir, VC, Registrar, and University Officers.
    Calculates live stats from actual PostgreSQL database records.
    """
    metrics = get_dashboard_metrics(user=current_user)
    
    return render_template(
        'dashboard/index.html',
        metrics=metrics,
        title='Executive Dashboard'
    )
