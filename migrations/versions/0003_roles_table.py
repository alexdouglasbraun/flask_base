"""move user role to roles table

Revision ID: 0003_roles_table
Revises: 0002_rbac_scim
Create Date: 2026-06-29
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_roles_table"
down_revision = "0002_rbac_scim"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=False)

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    roles_table = sa.table(
        "roles",
        sa.column("name", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(
        roles_table,
        [
            {"name": "admin", "description": "Full administrative access."},
            {"name": "user", "description": "Standard application access."},
        ],
    )

    op.execute(
        """
        insert into user_roles (user_id, role_id)
        select users.id, roles.id
        from users
        join roles on roles.name = users.role
        """
    )

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("role")


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("role", sa.String(length=64), nullable=False, server_default="user"))

    op.execute(
        """
        update users
        set role = 'admin'
        where exists (
            select 1
            from user_roles
            join roles on roles.id = user_roles.role_id
            where user_roles.user_id = users.id
            and roles.name = 'admin'
        )
        """
    )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("role", server_default=None)

    op.drop_table("user_roles")
    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_table("roles")
