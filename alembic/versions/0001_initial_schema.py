"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-10 10:59:31.900121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'outbox',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.Uuid(), nullable=False),
        sa.Column('aggregate_id', sa.Uuid(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'PUBLISHED', 'FAILED', name='outboxstatus'), nullable=False),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('aggregate_id'),
        sa.UniqueConstraint('message_id'),
    )
    op.create_table(
        'payments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.Enum('RUB', 'USD', 'EUR', name='currency'), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'SUCCEEDED', 'FAILED', name='paymentstatus'), nullable=False),
        sa.Column('idempotency_key', sa.String(length=255), nullable=False),
        sa.Column('webhook_url', sa.String(length=2048), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_payments_idempotency_key'), 'payments', ['idempotency_key'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_payments_idempotency_key'), table_name='payments')
    op.drop_table('payments')
    op.drop_table('outbox')
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    op.execute('DROP TYPE IF EXISTS outboxstatus')
    op.execute('DROP TYPE IF EXISTS currency')
