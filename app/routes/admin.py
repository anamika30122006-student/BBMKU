from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User, Role, Permission
from app.models.department import Department, Section
from app.models.setting import SystemSetting
from app.forms.admin import UserForm, DepartmentForm, SectionForm, SettingForm
from app.services.audit_service import log_audit_event
from app.utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# --- DEPARTMENTS & SECTIONS ---
@admin_bp.route('/departments', methods=['GET', 'POST'])
@login_required
@admin_required
def departments():
    """Manage University Departments."""
    form = DepartmentForm()
    if form.validate_on_submit():
        dept = Department(
            name=form.name.data.strip(),
            code=form.code.data.strip().upper(),
            description=form.description.data.strip() if form.description.data else None,
            is_active=form.is_active.data
        )
        db.session.add(dept)
        db.session.commit()
        log_audit_event('Department Created', remarks=f"Created department: {dept.code} - {dept.name}")
        flash(f"Department '{dept.name}' ({dept.code}) created successfully.", 'success')
        return redirect(url_for('admin.departments'))

    departments_list = Department.query.order_by(Department.name).all()
    return render_template(
        'admin/departments.html',
        form=form,
        departments=departments_list,
        title='Departments & Sections'
    )


@admin_bp.route('/departments/<int:dept_id>/sections/create', methods=['POST'])
@login_required
@admin_required
def create_section(dept_id: int):
    """Add a section to a department."""
    dept = Department.query.get_or_404(dept_id)
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip().upper()
    description = request.form.get('description', '').strip()

    if name and code:
        sec = Section(department_id=dept.id, name=name, code=code, description=description)
        db.session.add(sec)
        db.session.commit()
        log_audit_event('Section Created', remarks=f"Section {code} created in {dept.code}")
        flash(f"Section '{name}' ({code}) added to {dept.name}.", 'success')
    else:
        flash('Both section name and code are required.', 'danger')

    return redirect(url_for('admin.departments'))


# --- OFFICERS & USERS ---
@admin_bp.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users():
    """Manage University Officers & Users."""
    form = UserForm()
    roles = Role.query.order_by(Role.display_name).all()
    form.role_id.choices = [(r.id, r.display_name) for r in roles]

    depts = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    form.department_id.choices = [(0, '-- None / Central Administration --')] + [(d.id, f"{d.code} - {d.name}") for d in depts]

    sections = Section.query.filter_by(is_active=True).order_by(Section.name).all()
    form.section_id.choices = [(0, '-- None --')] + [(s.id, f"{s.department.code} / {s.name}") for s in sections]

    if form.validate_on_submit():
        existing = User.query.filter((User.username == form.username.data.strip()) | (User.email == form.email.data.strip().lower())).first()
        if existing:
            flash('A user with this username or email already exists.', 'danger')
        else:
            dept_id = form.department_id.data if form.department_id.data and form.department_id.data > 0 else None
            sec_id = form.section_id.data if form.section_id.data and form.section_id.data > 0 else None
            
            pwd = form.password.data if form.password.data else 'Bbmku@2026'

            new_user = User(
                username=form.username.data.strip(),
                email=form.email.data.strip().lower(),
                full_name=form.full_name.data.strip(),
                designation=form.designation.data.strip(),
                phone=form.phone.data.strip() if form.phone.data else None,
                role_id=form.role_id.data,
                department_id=dept_id,
                section_id=sec_id,
                is_active=form.is_active.data
            )
            new_user.set_password(pwd)
            db.session.add(new_user)
            db.session.commit()

            log_audit_event('User Created', remarks=f"Created user {new_user.username} ({new_user.designation})")
            flash(f"Officer account for '{new_user.full_name}' created successfully.", 'success')
            return redirect(url_for('admin.users'))

    users_list = User.query.order_by(User.full_name).all()
    return render_template(
        'admin/users.html',
        form=form,
        users=users_list,
        title='Officers & Users Management'
    )


# --- SETTINGS ---
@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """System & SLA Threshold Settings."""
    form = SettingForm()

    if request.method == 'GET':
        form.sla_warning_days.data = int(SystemSetting.get_value('SLA_DELAY_WARNING_DAYS', 3))
        form.sla_critical_days.data = int(SystemSetting.get_value('SLA_DELAY_CRITICAL_DAYS', 7))
        form.sla_overdue_days.data = int(SystemSetting.get_value('SLA_DELAY_OVERDUE_DAYS', 15))
        form.university_name.data = SystemSetting.get_value('UNIVERSITY_NAME', 'Binod Bihari Mahto Koyalanchal University (BBMKU)')
        form.university_code.data = SystemSetting.get_value('UNIVERSITY_CODE', 'BBMKU')

    if form.validate_on_submit():
        SystemSetting.set_value('SLA_DELAY_WARNING_DAYS', form.sla_warning_days.data, 'SLA Warning Threshold in days')
        SystemSetting.set_value('SLA_DELAY_CRITICAL_DAYS', form.sla_critical_days.data, 'SLA Critical Threshold in days')
        SystemSetting.set_value('SLA_DELAY_OVERDUE_DAYS', form.sla_overdue_days.data, 'SLA Overdue Threshold in days')
        SystemSetting.set_value('UNIVERSITY_NAME', form.university_name.data, 'Official University Name')
        SystemSetting.set_value('UNIVERSITY_CODE', form.university_code.data, 'University Code')

        log_audit_event('Settings Updated', remarks="Updated system SLA thresholds and university details.")
        flash('System configuration and SLA thresholds updated successfully.', 'success')
        return redirect(url_for('admin.settings'))

    return render_template(
        'admin/settings.html',
        form=form,
        title='System Settings'
    )
