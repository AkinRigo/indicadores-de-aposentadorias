from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "controle_carga",
        sa.Column("id_carga", sa.Integer(), primary_key=True),
        sa.Column("competencia", sa.CHAR(6), nullable=False, unique=True),
        sa.Column("arquivo", sa.Text(), nullable=False),
        sa.Column("etag", sa.Text(), nullable=False),
        sa.Column("tamanho_bytes", sa.BigInteger(), nullable=False),
        sa.Column("linhas_carregadas", sa.Integer(), nullable=False),
        sa.Column("carregado_em", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("controle_carga")
