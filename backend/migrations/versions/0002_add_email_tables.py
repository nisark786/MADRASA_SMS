"""Add email tables

Revision ID: 0002_add_email_tables
Revises: 0001_initial_fresh_start
Create Date: 2026-04-13 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0002_add_email_tables'
down_revision: Union[str, None] = '0001_initial_fresh_start'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Email Templates Table
    op.create_table(
        'email_templates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body_html', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_templates_name'), 'email_templates', ['name'], unique=True)
    op.create_index(op.f('ix_email_templates_is_active'), 'email_templates', ['is_active'], unique=False)

    # 2. Emails Table
    op.create_table(
        'emails',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.Column('recipient_name', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body_html', sa.Text(), nullable=False),
        sa.Column('template_id', sa.String(), sa.ForeignKey('email_templates.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_emails_recipient_email'), 'emails', ['recipient_email'], unique=False)
    op.create_index(op.f('ix_emails_status'), 'emails', ['status'], unique=False)
    op.create_index(op.f('ix_emails_created_at'), 'emails', ['created_at'], unique=False)
    op.create_index(op.f('ix_emails_sent_at'), 'emails', ['sent_at'], unique=False)


def downgrade() -> None:
    op.drop_table('emails')
    op.drop_table('email_templates')
