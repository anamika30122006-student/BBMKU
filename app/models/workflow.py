from datetime import datetime, timezone
from app.extensions import db


class WorkflowDefinition(db.Model):
    """Configurable approval and processing route for university files."""
    __tablename__ = 'workflow_definitions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    code = db.Column(db.String(40), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Steps ordered by step_order
    steps = db.relationship('WorkflowStep', back_populates='workflow', order_by='WorkflowStep.step_order', cascade='all, delete-orphan')
    files = db.relationship('FileRecord', back_populates='workflow_definition', lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<WorkflowDefinition {self.name}>'


class WorkflowStep(db.Model):
    """A stage/level in a file workflow."""
    __tablename__ = 'workflow_steps'

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflow_definitions.id', ondelete='CASCADE'), nullable=False)
    step_order = db.Column(db.Integer, nullable=False) # 1, 2, 3...
    step_name = db.Column(db.String(120), nullable=False) # e.g. "Section Officer Verification", "Head Recommendation"
    
    # Target designation / role required to take action at this step
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    
    action_type = db.Column(db.String(64), default='Verify & Forward') # Verify & Forward, Endorse, Approve/Reject
    sla_days = db.Column(db.Integer, default=3) # Expected turnaround days for this step
    is_final_approval = db.Column(db.Boolean, default=False)

    # Relationships
    workflow = db.relationship('WorkflowDefinition', back_populates='steps')
    role = db.relationship('Role')
    department = db.relationship('Department')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<WorkflowStep {self.step_order}: {self.step_name}>'
