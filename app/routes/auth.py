from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User
from app.forms.auth import LoginForm, ChangePasswordForm
from app.services.audit_service import log_audit_event

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            (User.username == form.username.data.strip()) | 
            (User.email == form.username.data.strip().lower())
        ).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated by the University Administrator. Please contact UFMS Cell.', 'danger')
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember.data)
            user.last_login_at = datetime.now(timezone.utc)
            db.session.commit()

            log_audit_event(
                action='User Login',
                remarks=f"User {user.username} ({user.designation}) logged in successfully.",
                user=user
            )

            flash(f"Welcome, {user.full_name} ({user.designation}) to BBMKU UFMS.", 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid username/email or password. Please check your credentials.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    username = current_user.username
    log_audit_event(
        action='User Logout',
        remarks=f"User {username} logged out.",
        user=current_user
    )
    logout_user()
    flash('You have been securely signed out of BBMKU UFMS.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            log_audit_event(
                action='Password Changed',
                remarks="User updated account password.",
                user=current_user
            )
            flash('Your password has been successfully updated.', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Current password entered is incorrect.', 'danger')

    return render_template('auth/profile.html', form=form)
