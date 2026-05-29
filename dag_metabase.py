from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.task_group import TaskGroup
from datetime import datetime, timedelta
import pendulum

# Fuso horário
local_tz = pendulum.timezone("America/Sao_Paulo")

# Argumentos padrão
default_args = {
    "owner": "Airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 2, 11, tzinfo=local_tz),
    "email": [
        "guilherme.tenorio@valorem.com",
        "geovane.andrade@valorem.com.br",
    ],
    "email_on_failure": True,
    "email_on_retry": True,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="dag_metabase_materialized_view",
    description="Dag - Atualiza as Views Materializadas do Metabase",
    schedule="30 8,13 * * 1-5",
    catchup=False,
    default_args=default_args,
    tags=["Metabase", "Prisma"],
) as dag:

    start_task = EmptyOperator(task_id="start_task")

    mv_ccb_nc_rendaFixa = PostgresOperator(
        task_id="mv_ccb_nc_rendaFixa",
        sql='REFRESH MATERIALIZED VIEW metabase."mv_ccb_nc_rendaFixa";',
        postgres_conn_id="postgresql_bi",
        autocommit=True,
    )

    mv_ft_recibos_efetivados = PostgresOperator(
        task_id="mv_ft_recibos_efetivados",
        sql='REFRESH MATERIALIZED VIEW metabase."mv_ft_recibos_efetivados";',
        postgres_conn_id="postgresql_bi",
        autocommit=True,
    )

    mv_ft_conciliacao = PostgresOperator(
        task_id="mv_ft_conciliacao",
        sql='REFRESH MATERIALIZED VIEW metabase."mv_ft_conciliacao";',
        postgres_conn_id="postgresql_bi",
        autocommit=True,
    )

    mv_ft_aplicacoes = PostgresOperator(
        task_id="mv_ft_aplicacoes",
        sql='REFRESH MATERIALIZED VIEW metabase."mv_ft_aplicacoes";',
        postgres_conn_id="postgresql_bi",
        autocommit=True,
    )


    mv_consolidada_ri = PostgresOperator(
        task_id="mv_consolidada_ri",
        sql="REFRESH MATERIALIZED VIEW metabase.mv_consolidada_ri;",
        postgres_conn_id="postgresql_bi",
        autocommit=True,
    )



    with TaskGroup(
        group_id="task_group_cubo_prisma",
        tooltip=(
            "Atualiza as materializadas que têm como base "
            "as informações do banco Vertica do Prisma."
        ),
    ) as grupo_cubo_prisma:

        PostgresOperator(
            task_id="mv_ft_prisma_rec_aplicacao_amortizada",
            sql="REFRESH MATERIALIZED VIEW metabase.mv_ft_prisma_rec_aplicacao_amortizada;",
            postgres_conn_id="postgresql_bi",
            autocommit=True,
        )

        PostgresOperator(
            task_id="mv_ft_prisma_rec_aplicacao_fato",
            sql="REFRESH MATERIALIZED VIEW metabase.mv_ft_prisma_rec_aplicacao_fato;",
            postgres_conn_id="postgresql_bi",
            autocommit=True,
        )

        PostgresOperator(
            task_id="mv_ft_prisma_rec_aplicacao_rendimento",
            sql="REFRESH MATERIALIZED VIEW metabase.mv_ft_prisma_rec_aplicacao_rendimento;",
            postgres_conn_id="postgresql_bi",
            autocommit=True,
        )

        PostgresOperator(
            task_id="mv_ft_prisma_rec_aplicacao_resgate",
            sql="REFRESH MATERIALIZED VIEW metabase.mv_ft_prisma_rec_aplicacao_resgate;",
            postgres_conn_id="postgresql_bi",
            autocommit=True,
        )

        PostgresOperator(
            task_id="mv_ft_prisma_rec_tipo_aplicacao",
            sql="REFRESH MATERIALIZED VIEW metabase.mv_ft_prisma_rec_tipo_aplicacao;",
            postgres_conn_id="postgresql_bi",
            autocommit=True,
        )

    with TaskGroup(
        group_id="task_group_info_ri",
        tooltip=(
            "Atualiza as materializadas que gera a base "
            "para os relatórios do RI."
        ),
    ) as grupo_cubo_info_ri:
        
        mv_acompanhamento_carteira_cedente =  PostgresOperator(
            task_id="mv_acompanhamento_carteira_cedente",
            sql="REFRESH MATERIALIZED VIEW metabase.mv_acompanhamento_carteira_cedente;",
            postgres_conn_id="postgresql_bi",
            autocommit=True,
        )

        mv_acompanhamento_carteira_sacado = PostgresOperator(
                task_id="mv_acompanhamento_carteira_sacado",
                sql="REFRESH MATERIALIZED VIEW metabase.mv_acompanhamento_carteira_sacado;",
                postgres_conn_id="postgresql_bi",
                autocommit=True,
            )


    done_task = EmptyOperator(task_id="done_task")

    start_task >> mv_ccb_nc_rendaFixa >> [mv_ft_recibos_efetivados, mv_ft_aplicacoes, mv_ft_conciliacao, mv_consolidada_ri] >> grupo_cubo_prisma >> grupo_cubo_info_ri >> done_task
