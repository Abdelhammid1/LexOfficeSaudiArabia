"""Add tenant.default_tax_rate

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-06-09 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e9f0a1b2c3d4'
down_revision = 'd8e9f0a1b2c3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tenants', sa.Column(
        'default_tax_rate', sa.Numeric(5, 2),
        nullable=False, server_default='0'
    ))


def downgrade():
    op.drop_column('tenants', 'default_tax_rate')
