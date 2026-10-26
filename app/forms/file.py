from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Optional


class FileCreateForm(FlaskForm):
    """File Registration Form for initiating officers."""
    subject = StringField('File Subject / Title *', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Detailed Description / Purpose', validators=[Optional()])
    
    category = SelectField('File Category *', choices=[
        ('Establishment', 'Establishment / Administration'),
        ('Academic', 'Academic & Curriculum'),
        ('Financial', 'Finance & Accounts'),
        ('Examination', 'Examination & Confidential'),
        ('Student Affairs', 'Student Welfare & Admissions'),
        ('Legal', 'Legal & RTI Cell'),
        ('Purchase/Store', 'Purchase & Tender / Store'),
        ('General', 'General Administrative Matter')
    ], validators=[DataRequired()])

    priority = SelectField('Priority Level *', choices=[
        ('Normal', 'Normal (Routine processing)'),
        ('Urgent', 'Urgent (Priority processing within 3 days)'),
        ('Immediate', 'Immediate (Same day / 24 hours action)')
    ], default='Normal', validators=[DataRequired()])

    confidentiality = SelectField('Confidentiality Level *', choices=[
        ('General', 'General (Open to concerned sections)'),
        ('Confidential', 'Confidential (Designated officers only)'),
        ('Strictly Confidential', 'Strictly Confidential (Executive / VC only)')
    ], default='General', validators=[DataRequired()])

    department_id = SelectField('Initiating Department *', coerce=int, validators=[DataRequired()])
    section_id = SelectField('Section / Branch (Optional)', coerce=int, validators=[Optional()])
    assigned_officer_id = SelectField('Initial Assigned Officer *', coerce=int, validators=[DataRequired()])
    
    due_date = DateField('Expected Action Due Date (Optional)', format='%Y-%m-%d', validators=[Optional()])
    initial_remarks = TextAreaField('Initial Note / Remarks (Green Sheet)', validators=[Optional()])
    document = FileField('Attach Supporting Document (PDF, Word, Excel, Image)', validators=[
        Optional(),
        FileAllowed(['pdf', 'docx', 'doc', 'xlsx', 'xls', 'jpg', 'jpeg', 'png'], 'Allowed formats: PDF, Word, Excel, Images')
    ])
    submit = SubmitField('Register & Initiate File')


class FileForwardForm(FlaskForm):
    """File Forwarding / Movement Form."""
    to_user_id = SelectField('Select Recipient Officer *', coerce=int, validators=[DataRequired()])
    action_type = SelectField('Action Requested *', choices=[
        ('Forwarded for Processing', 'Forwarded for Processing'),
        ('For Verification & Scrutiny', 'For Verification & Scrutiny'),
        ('For Recommendation', 'For Recommendation'),
        ('For Approval / Sanction', 'For Approval / Sanction'),
        ('For Information / Perusal', 'For Information / Perusal'),
        ('For Compliance / Execution', 'For Compliance / Execution')
    ], default='Forwarded for Processing', validators=[DataRequired()])
    remarks = TextAreaField('Movement Remarks / Directive *', validators=[DataRequired(), Length(min=2)])
    dispatch_mode = SelectField('Movement Mode', choices=[
        ('Digital Workflow', 'Digital Workflow (Instant UFMS Transfer)'),
        ('Physical Peon Book', 'Physical Movement (Peon Dispatch Book)'),
        ('Hand Delivered', 'Hand Delivered by Section Assistant'),
        ('Speed Post / Registered', 'Speed Post / Courier')
    ], default='Digital Workflow')
    dispatch_number = StringField('Dispatch Register / Peon Book No. (Optional)', validators=[Optional()])
    submit = SubmitField('Forward File')


class FileReturnForm(FlaskForm):
    """Return File for Correction Form."""
    return_to_user_id = SelectField('Return To Officer *', coerce=int, validators=[DataRequired()])
    reason = StringField('Reason for Return *', validators=[DataRequired(), Length(min=3, max=255)])
    correction_instructions = TextAreaField('Detailed Correction Instructions *', validators=[DataRequired(), Length(min=5)])
    submit = SubmitField('Return File for Correction')


class FileApproveForm(FlaskForm):
    """Formal File Approval Form."""
    remarks = TextAreaField('Approval Minute / Sanction Remarks *', validators=[DataRequired(), Length(min=2)])
    conditions = TextAreaField('Specific Conditions / Directives (Optional)', validators=[Optional()])
    submit = SubmitField('Approve File')


class FileRejectForm(FlaskForm):
    """Formal File Rejection Form."""
    reason = StringField('Primary Rejection Reason *', validators=[DataRequired(), Length(min=5, max=255)])
    remarks = TextAreaField('Detailed Reason & Justification *', validators=[DataRequired(), Length(min=5)])
    submit = SubmitField('Reject File')


class FileCloseForm(FlaskForm):
    """File Closure Form."""
    remarks = TextAreaField('Closure Summary / Final Action Taken *', validators=[DataRequired(), Length(min=5)])
    submit = SubmitField('Close File')


class FileArchiveForm(FlaskForm):
    """File Archival Form."""
    archive_location = StringField('Archive Room / Rack / Shelf Location *', validators=[DataRequired(), Length(min=3, max=120)])
    remarks = TextAreaField('Archival Notes / Record Retention Details', validators=[Optional()])
    submit = SubmitField('Archive File Record')


class FileNoteForm(FlaskForm):
    """Green Sheet / Internal Noting Form."""
    note_type = SelectField('Note Type', choices=[
        ('Internal Note', 'Internal Note (Routine administrative noting)'),
        ('Formal Minute', 'Formal Minute (Official recommendation)'),
        ('Legal Opinion', 'Legal / Statutory Opinion'),
        ('Audit Remark', 'Audit & Accounts Remark')
    ], default='Internal Note', validators=[DataRequired()])
    content = TextAreaField('Noting Content *', validators=[DataRequired(), Length(min=2)])
    submit = SubmitField('Add Note to File')


class FileDocumentUploadForm(FlaskForm):
    """Document Upload Form for existing files."""
    title = StringField('Document Title / Reference *', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description / Notes', validators=[Optional()])
    document = FileField('Select File *', validators=[
        DataRequired(),
        FileAllowed(['pdf', 'docx', 'doc', 'xlsx', 'xls', 'jpg', 'jpeg', 'png'], 'Allowed formats: PDF, Word, Excel, Images')
    ])
    submit = SubmitField('Upload Document')


class FileFilterForm(FlaskForm):
    """Universal File Search & Filter Form."""
    search = StringField('Keyword Search (File No. or Subject)')
    department_id = SelectField('Department', coerce=int, validators=[Optional()])
    category = SelectField('Category', choices=[('', 'All Categories')], validators=[Optional()])
    status = SelectField('Status', choices=[('', 'All Statuses')], validators=[Optional()])
    priority = SelectField('Priority', choices=[('', 'All Priorities')], validators=[Optional()])
    confidentiality = SelectField('Confidentiality', choices=[('', 'All Levels')], validators=[Optional()])
    delay_filter = SelectField('Pending Duration', choices=[
        ('', 'All Durations'),
        ('today', 'Pending Today (≤ 1 day)'),
        ('gt3', 'Pending > 3 days'),
        ('gt7', 'Pending > 7 days'),
        ('gt15', 'Pending > 15 days'),
        ('overdue', 'Overdue Files Only')
    ], validators=[Optional()])
    submit = SubmitField('Apply Filters')
