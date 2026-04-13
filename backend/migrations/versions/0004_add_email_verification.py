"""Add email verification tokens table and email_verified field

Revision ID: 0004_add_email_verification
Revises: 0003_add_password_reset_tokens
Create Date: 2026-04-13 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0004_add_email_verification'
down_revision: Union[str, None] = '0003_add_password_reset_tokens'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add email_verified field to users table
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index(op.f('ix_users_email_verified'), 'users', ['email_verified'], unique=False)
    
    # Email Verification Tokens Table
    op.create_table(
        'email_verification_tokens',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_verification_tokens_user_id'), 'email_verification_tokens', ['user_id'], unique=True)
    op.create_index(op.f('ix_email_verification_tokens_token_hash'), 'email_verification_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_email_verification_tokens_is_used'), 'email_verification_tokens', ['is_used'], unique=False)
    op.create_index(op.f('ix_email_verification_tokens_created_at'), 'email_verification_tokens', ['created_at'], unique=False)
    op.create_index(op.f('ix_email_verification_tokens_expires_at'), 'email_verification_tokens', ['expires_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_email_verification_tokens_expires_at'), table_name='email_verification_tokens')
    op.drop_index(op.f('ix_email_verification_tokens_created_at'), table_name='email_verification_tokens')
    op.drop_index(op.f('ix_email_verification_tokens_is_used'), table_name='email_verification_tokens')
    op.drop_index(op.f('ix_email_verification_tokens_token_hash'), table_name='email_verification_tokens')
    op.drop_index(op.f('ix_email_verification_tokens_user_id'), table_name='email_verification_tokens')
    op.drop_table('email_verification_tokens')
    
    op.drop_index(op.f('ix_users_email_verified'), table_name='users')
    op.drop_column('users', 'email_verified')
