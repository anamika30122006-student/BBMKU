from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, PasswordField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional


class UserForm(FlaskForm):
    """User Management Form."""
    username = StringField('Username *', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email Address *', validators=[DataRequired(), Email(), Length(max=120)])
    full_name = StringField('Full Name *', validators=[DataRequired(), Length(max=120)])
    designation = StringField('Designation *', validators=[DataRequired(), Length(max=120)])
    phone = StringField('Phone / Mobile', validators=[Optional(), Length(max=20)])
    role_id = SelectField('Assigned Role *', coerce=int, validators=[DataRequired()])
    department_id = SelectField('Department', coerce=int, validators=[Optional()])
    section_id = SelectField('Section / Branch', coerce=int, validators=[Optional()])
    password = PasswordField('Password', validators=[Optional(), Length(min=6, max=64)])
    is_active = BooleanField('Active Account', default=True)
    submit = SubmitField('Save User')


class DepartmentForm(FlaskForm):
    """Department Management Form."""
    name = StringField('Department Name *', validators=[DataRequired(), Length(max=120)])
    code = StringField('Department Code * (e.g. ESTB, FIN, EXAM)', validators=[DataRequired(), Length(min=2, max=20)])
    description = TextAreaField('Description', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Department')


class SectionForm(FlaskForm):
    """Section / Cell Management Form."""
    department_id = SelectField('Department *', coerce=int, validators=[DataRequired()])
    name = StringField('Section Name *', validators=[DataRequired(), Length(max=120)])
    code = StringField('Section Code *', validators=[DataRequired(), Length(min=2, max=20)])
    description = TextAreaField('Description', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Section')


class SettingForm(FlaskForm):
    """SLA and System Threshold Settings Form."""
    sla_warning_days = IntegerField('SLA Warning Threshold (Days) *', validators=[DataRequired()])
    sla_critical_days = IntegerField('SLA Critical Threshold (Days) *', validators=[DataRequired()])
    sla_overdue_days = IntegerField('SLA Overdue Threshold (Days) *', validators=[DataRequired()])
    university_name = StringField('University Name *', validators=[DataRequired(), Length(max=150)])
    university_code = StringField('University Code *', validators=[DataRequired(), Length(max=20)])
    submit = SubmitField('Update Settings')
