-- dim_agencia sem uso na fato
SELECT a.codigo_aps, a.nome
FROM dim_agencia a
LEFT JOIN fato_concessao f ON f.codigo_aps = a.codigo_aps
WHERE f.codigo_aps IS NULL;

-- dim_municipio sem uso na fato
SELECT a.codigo_municipio, a.nome
FROM dim_municipio a
LEFT JOIN fato_concessao f ON f.codigo_municipio = a.codigo_municipio
WHERE f.codigo_municipio IS NULL;

-- dim_despacho sem uso na fato
SELECT a.codigo_despacho, a.nome
FROM dim_despacho a
LEFT JOIN fato_concessao f ON f.codigo_despacho = a.codigo_despacho
WHERE f.codigo_despacho IS NULL;

-- dim_forma_filiacao sem uso na fato
SELECT a.id, a.descricao
FROM dim_forma_filiacao a
LEFT JOIN fato_concessao f ON f.id_forma_filiacao = a.id
WHERE f.id_forma_filiacao IS NULL;

-- dim_ramo_atividade sem uso na fato
SELECT a.id, a.descricao
FROM dim_ramo_atividade a
LEFT JOIN fato_concessao f ON f.id_ramo_atividade = a.id
WHERE f.id_ramo_atividade IS NULL;

-- dim_grau_instrucao sem uso na fato
SELECT a.id, a.codigo, a.descricao
FROM dim_grau_instrucao a
LEFT JOIN fato_concessao f ON f.id_grau_instrucao = a.id
WHERE f.id_grau_instrucao IS NULL;
