from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fato_concessao",
        sa.Column("id_concessao", sa.Integer(), primary_key=True),
        sa.Column("id_carga", sa.Integer(), sa.ForeignKey("controle_carga.id_carga"), nullable=False),
        sa.Column("competencia", sa.CHAR(6), nullable=False),
        sa.Column("codigo_aps", sa.CHAR(8), sa.ForeignKey("dim_agencia.codigo_aps"), nullable=False),
        sa.Column("codigo_municipio", sa.CHAR(5), sa.ForeignKey("dim_municipio.codigo_municipio"), nullable=False),
        sa.Column("codigo_despacho", sa.Text(), sa.ForeignKey("dim_despacho.codigo_despacho"), nullable=False),
        sa.Column("id_forma_filiacao", sa.Integer(), sa.ForeignKey("dim_forma_filiacao.id"), nullable=False),
        sa.Column("id_ramo_atividade", sa.Integer(), sa.ForeignKey("dim_ramo_atividade.id"), nullable=False),
        sa.Column("id_grau_instrucao", sa.Integer(), sa.ForeignKey("dim_grau_instrucao.id"), nullable=False),
        sa.Column("sexo", sa.Text(), nullable=False),
        sa.Column("clientela", sa.Text(), nullable=False),
        sa.Column("ano_nascimento", sa.SmallInteger(), nullable=False),
        sa.Column("idade_na_dib", sa.SmallInteger(), nullable=False),
        sa.Column("dib", sa.Date(), nullable=False),
        sa.Column("ddb", sa.Date(), nullable=False),
        sa.Column("dcb", sa.Date(), nullable=True),
        sa.Column("qtd_salarios_minimos", sa.Numeric(5, 2), nullable=False),
        sa.Column("qt_anos_contribuicao", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("sexo IN ('FEMININO', 'MASCULINO')", name="ck_fato_sexo"),
        sa.CheckConstraint("clientela IN ('URBANA', 'RURAL')", name="ck_fato_clientela"),
        sa.CheckConstraint("dcb IS NULL OR dcb >= dib", name="ck_fato_dcb_dib"),
        sa.CheckConstraint("qtd_salarios_minimos > 0", name="ck_fato_rmi"),
        sa.CheckConstraint("qt_anos_contribuicao BETWEEN 0 AND 90", name="ck_fato_anos_contribuicao"),
    )


def downgrade():
    op.drop_table("fato_concessao")
