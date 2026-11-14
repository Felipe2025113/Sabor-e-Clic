FROM mysql:8.4
COPY database/01_modelo_fisico.sql /docker-entrypoint-initdb.d/01_modelo.sql
COPY database/20_triggers.sql /docker-entrypoint-initdb.d/02_triggers.sql
COPY database/02_insercoes_basicas.sql /docker-entrypoint-initdb.d/03_dados.sql
