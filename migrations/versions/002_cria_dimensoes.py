from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dim_agencia",
        sa.Column("codigo_aps", sa.CHAR(8), primary_key=True),
        sa.Column("nome", sa.Text(), nullable=False),
        sa.Column("uf", sa.Text(), nullable=False),
    )
    op.create_table(
        "dim_municipio",
        sa.Column("codigo_municipio", sa.CHAR(5), primary_key=True),
        sa.Column("nome", sa.Text(), nullable=False),
    )
    op.create_table(
        "dim_despacho",
        sa.Column("codigo_despacho", sa.Text(), primary_key=True),
        sa.Column("nome", sa.Text(), nullable=False),
    )
    op.create_table(
        "dim_forma_filiacao",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("descricao", sa.Text(), nullable=False, unique=True),
    )
    op.create_table(
        "dim_ramo_atividade",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("descricao", sa.Text(), nullable=False, unique=True),
    )
    op.create_table(
        "dim_grau_instrucao",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo", sa.CHAR(2), nullable=False, unique=True),
        sa.Column("descricao", sa.Text(), nullable=False),
    )


def downgrade():
    op.drop_table("dim_grau_instrucao")
    op.drop_table("dim_ramo_atividade")
    op.drop_table("dim_forma_filiacao")
    op.drop_table("dim_despacho")
    op.drop_table("dim_municipio")
    op.drop_table("dim_agencia")
