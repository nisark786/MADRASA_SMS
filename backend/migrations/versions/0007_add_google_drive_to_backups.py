"""Add Google Drive fields to database_backups table

Revision ID: 0007_add_google_drive_to_backups
Revises: 0006_add_database_backup
Create Date: 2026-04-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0007_add_google_drive_to_backups'
down_revision = '0006_add_database_backup'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add Google Drive integration columns to database_backups
    op.add_column('database_backups', sa.Column('google_drive_file_id', sa.String(255), nullable=True))
    op.add_column('database_backups', sa.Column('google_drive_link', sa.String(500), nullable=True))
    op.add_column('database_backups', sa.Column('uploaded_to_drive', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('database_backups', sa.Column('uploaded_to_drive_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove Google Drive integration columns
    op.drop_column('database_backups', 'uploaded_to_drive_at')
    op.drop_column('database_backups', 'uploaded_to_drive')
    op.drop_column('database_backups', 'google_drive_link')
    op.drop_column('database_backups', 'google_drive_file_id')
