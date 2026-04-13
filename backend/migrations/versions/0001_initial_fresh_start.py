"""Fresh start schema

Revision ID: 0001_initial_fresh_start
Revises: 
Create Date: 2026-04-11 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial_fresh_start'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users Table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)

    # 2. Roles Table
    op.create_table(
        'roles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system_role', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)
    op.create_index(op.f('ix_roles_created_at'), 'roles', ['created_at'], unique=False)

    # 3. User Roles Table
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', sa.String(), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('assigned_by', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # 4. Permissions Table
    op.create_table(
        'permissions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('module', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('module', 'action', name='uq_module_action')
    )
    op.create_index(op.f('ix_permissions_name'), 'permissions', ['name'], unique=True)

    # 5. Role Permissions Table
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.String(), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('permission_id', sa.String(), sa.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('granted_by', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    # 6. Students Table
    op.create_table(
        'students',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('class_name', sa.String(length=50), nullable=True),
        sa.Column('roll_no', sa.String(length=50), nullable=True),
        sa.Column('admission_no', sa.String(length=50), nullable=True),
        sa.Column('mobile_numbers', sa.JSON(), nullable=True),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('zip_code', sa.String(length=20), nullable=True),
        sa.Column('date_of_birth', sa.String(length=20), nullable=True),
        sa.Column('enrollment_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('submitted_via_form', sa.Boolean(), nullable=False),
        sa.Column('form_submission_code', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_students_email'), 'students', ['email'], unique=True)
    op.create_index(op.f('ix_students_first_name'), 'students', ['first_name'], unique=False)
    op.create_index(op.f('ix_students_is_active'), 'students', ['is_active'], unique=False)
    op.create_index(op.f('ix_students_form_submission_code'), 'students', ['form_submission_code'], unique=True)
    op.create_index(op.f('ix_students_created_at'), 'students', ['created_at'], unique=False)

    # 7. Widgets Table
    op.create_table(
        'widgets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('component_key', sa.String(length=100), nullable=False),
        sa.Column('widget_type', sa.String(length=50), nullable=False),
        sa.Column('default_config', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_widgets_name'), 'widgets', ['name'], unique=True)

    # 8. Widget Permissions Table
    op.create_table(
        'widget_permissions',
        sa.Column('widget_id', sa.String(), sa.ForeignKey('widgets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('permission_id', sa.String(), sa.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False),
        sa.PrimaryKeyConstraint('widget_id', 'permission_id')
    )

    # 9. User Widget Preferences Table
    op.create_table(
        'user_widget_preferences',
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('widget_id', sa.String(), sa.ForeignKey('widgets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_visible', sa.Boolean(), nullable=False),
        sa.Column('is_pinned', sa.Boolean(), nullable=False),
        sa.Column('position', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('user_id', 'widget_id')
    )

    # 10. Audit Logs Table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)

    # 11. Form Links Table
    op.create_table(
        'form_links',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('token', sa.String(length=50), nullable=False),
        sa.Column('allowed_fields', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_form_links_token'), 'form_links', ['token'], unique=True)
    op.create_index(op.f('ix_form_links_is_active'), 'form_links', ['is_active'], unique=False)

    # 12. Form Submissions Table
    op.create_table(
        'form_submissions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('form_link_id', sa.String(), sa.ForeignKey('form_links.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submitted_data', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_form_submissions_form_link_id'), 'form_submissions', ['form_link_id'], unique=False)
    op.create_index(op.f('ix_form_submissions_status'), 'form_submissions', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('form_submissions')
    op.drop_table('form_links')
    op.drop_table('audit_logs')
    op.drop_table('user_widget_preferences')
    op.drop_table('widget_permissions')
    op.drop_table('widgets')
    op.drop_table('students')
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('user_roles')
    op.drop_table('roles')
    op.drop_table('users')
