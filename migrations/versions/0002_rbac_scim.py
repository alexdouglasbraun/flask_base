"""add rbac and scim user fields

Revision ID: 0002_rbac_scim
Revises: 0001_initial
Create Date: 2026-06-29
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_rbac_scim"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("role", sa.String(length=64), nullable=False, server_default="user"))
        batch_op.add_column(sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column("scim_external_id", sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint("uq_users_scim_external_id", ["scim_external_id"])
        batch_op.create_index("ix_users_scim_external_id", ["scim_external_id"], unique=False)

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("role", server_default=None)
        batch_op.alter_column("active", server_default=None)


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_scim_external_id")
        batch_op.drop_constraint("uq_users_scim_external_id", type_="unique")
        batch_op.drop_column("scim_external_id")
        batch_op.drop_column("active")
        batch_op.drop_column("role")
