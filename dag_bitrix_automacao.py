from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta
import pendulum

local_tz = pendulum.timezone("America/Sao_Paulo")

default_args = {
    'owner': 'Airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 2, 11, tzinfo=local_tz),
    'email': ['guilherme.tenorio@valorem.com', 'geovane.andrade@valorem.com.br'],
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

# Wrapper com import lazy — evita conexão com banco no momento do import da DAG
def executar_update_card():
    from bitrix_automacao_update_card import get_automacao_update_card_bitrix
    get_automacao_update_card_bitrix()

with DAG(
    'dag_bitrix_automacao',
    description="Atualiza os cards no Bitrix com dados do QProf — todo sábado",
    schedule_interval="30 9 * * 6",
    catchup=False,
    default_args=default_args,
    tags=["tabela", "valores", "dim", "bitrix"]
) as dag:

    start_task = EmptyOperator(task_id='start_task')
    done_task  = EmptyOperator(task_id='done_task')

    t_refresh_mv = PostgresOperator(
        task_id='mv_ft_atualiza_card_bitrix',
        sql='REFRESH MATERIALIZED VIEW load.mv_ft_atualiza_card_bitrix;',
        postgres_conn_id='postgresql_bi',
        autocommit=True
    )

    t_update_card = PythonOperator(
        task_id='automacao_update_card_bitrix',
        python_callable=executar_update_card
    )

    start_task >> t_refresh_mv >> t_update_card >> done_task