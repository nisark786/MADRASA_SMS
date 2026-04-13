"""Add database backup management tables

Revision ID: 0006_add_database_backup
Revises: 0005_add_two_factor_auth
Create Date: 2026-04-13 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0006_add_database_backup'
down_revision: Union[str, None] = '0005_add_two_factor_auth'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Database Backups Table
    op.create_table(
        'database_backups',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('table_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('record_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('is_automated', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_by_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('backup_type', sa.String(length=20), nullable=False, server_default='full'),
        sa.Column('includes_data', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('includes_schema', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_compressed', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('compression_format', sa.String(length=20), nullable=True),
        sa.Column('is_encrypted', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('encryption_algorithm', sa.String(length=50), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_database_backups_created_at'), 'database_backups', ['created_at'], unique=False)
    op.create_index(op.f('ix_database_backups_created_by_id'), 'database_backups', ['created_by_id'], unique=False)
    
    # Backup Restores Table
    op.create_table(
        'backup_restores',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('backup_id', sa.String(), sa.ForeignKey('database_backups.id'), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('restore_mode', sa.String(length=20), nullable=False),
        sa.Column('started_by_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('target_database', sa.String(length=255), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('records_restored', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('tables_restored', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_backup_restores_backup_id'), 'backup_restores', ['backup_id'], unique=False)
    op.create_index(op.f('ix_backup_restores_created_at'), 'backup_restores', ['created_at'], unique=False)
    
    # Backup Schedules Table
    op.create_table(
        'backup_schedules',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('frequency', sa.String(length=20), nullable=False),
        sa.Column('time_of_day', sa.String(length=5), nullable=False),
        sa.Column('day_of_week', sa.String(length=20), nullable=True),
        sa.Column('day_of_month', sa.BigInteger(), nullable=True),
        sa.Column('backup_type', sa.String(length=20), nullable=False, server_default='full'),
        sa.Column('compression_enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('encryption_enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('retention_days', sa.BigInteger(), nullable=False, server_default='30'),
        sa.Column('max_backups', sa.BigInteger(), nullable=False, server_default='10'),
        sa.Column('created_by_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_backup_schedules_is_enabled'), 'backup_schedules', ['is_enabled'], unique=False)
    op.create_index(op.f('ix_backup_schedules_created_at'), 'backup_schedules', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_backup_schedules_created_at'), table_name='backup_schedules')
    op.drop_index(op.f('ix_backup_schedules_is_enabled'), table_name='backup_schedules')
    op.drop_table('backup_schedules')
    
    op.drop_index(op.f('ix_backup_restores_created_at'), table_name='backup_restores')
    op.drop_index(op.f('ix_backup_restores_backup_id'), table_name='backup_restores')
    op.drop_table('backup_restores')
    
    op.drop_index(op.f('ix_database_backups_created_by_id'), table_name='database_backups')
    op.drop_index(op.f('ix_database_backups_created_at'), table_name='database_backups')
    op.drop_table('database_backups')
