from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None

REGRAS = {
    "ck_controle_competencia": "competencia ~ '^[0-9]{4}(0[1-9]|1[0-2])$'",
    "ck_controle_arquivo": "length(trim(arquivo)) > 0",
    "ck_controle_etag": "length(trim(etag)) > 0",
    "ck_controle_tamanho": "tamanho_bytes > 0",
    "ck_controle_linhas": "linhas_carregadas > 0",
}


def upgrade():
    for nome, regra in REGRAS.items():
        op.create_check_constraint(nome, "controle_carga", regra)


def downgrade():
    for nome in reversed(list(REGRAS)):
        op.drop_constraint(nome, "controle_carga", type_="check")
