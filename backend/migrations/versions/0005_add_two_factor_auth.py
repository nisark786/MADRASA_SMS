"""Add Two-Factor Authentication (2FA) tables

Revision ID: 0005_add_two_factor_auth
Revises: 0004_add_email_verification
Create Date: 2026-04-13 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0005_add_two_factor_auth'
down_revision: Union[str, None] = '0004_add_email_verification'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Two Factor Auth Table
    op.create_table(
        'two_factor_auth',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('totp_secret', sa.String(length=255), nullable=True),
        sa.Column('backup_codes', sa.Text(), nullable=True),
        sa.Column('setup_initiated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('setup_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_two_factor_auth_user_id'), 'two_factor_auth', ['user_id'], unique=True)
    op.create_index(op.f('ix_two_factor_auth_is_enabled'), 'two_factor_auth', ['is_enabled'], unique=False)
    op.create_index(op.f('ix_two_factor_auth_created_at'), 'two_factor_auth', ['created_at'], unique=False)
    
    # Two Factor Audit Log Table
    op.create_table(
        'two_factor_audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_two_factor_audit_logs_user_id'), 'two_factor_audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_two_factor_audit_logs_created_at'), 'two_factor_audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_two_factor_audit_logs_created_at'), table_name='two_factor_audit_logs')
    op.drop_index(op.f('ix_two_factor_audit_logs_user_id'), table_name='two_factor_audit_logs')
    op.drop_table('two_factor_audit_logs')
    
    op.drop_index(op.f('ix_two_factor_auth_created_at'), table_name='two_factor_auth')
    op.drop_index(op.f('ix_two_factor_auth_is_enabled'), table_name='two_factor_auth')
    op.drop_index(op.f('ix_two_factor_auth_user_id'), table_name='two_factor_auth')
    op.drop_table('two_factor_auth')
