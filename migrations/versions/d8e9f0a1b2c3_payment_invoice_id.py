"""Add invoice_id FK to payments

Revision ID: d8e9f0a1b2c3
Revises: caa715ba73c8
Create Date: 2026-06-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd8e9f0a1b2c3'
down_revision = 'caa715ba73c8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('payments', sa.Column('invoice_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_payments_invoice_id', 'payments', 'invoices',
        ['invoice_id'], ['id'], ondelete='SET NULL'
    )
    op.create_index('ix_payments_invoice_id', 'payments', ['invoice_id'])


def downgrade():
    op.drop_index('ix_payments_invoice_id', table_name='payments')
    op.drop_constraint('fk_payments_invoice_id', 'payments', type_='foreignkey')
    op.drop_column('payments', 'invoice_id')
