import sys
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta
from airflow.utils.task_group import TaskGroup
from mvp_antecipacoes import get_mvp_antecipacoes

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

dag = DAG(
    'dag_antecipacoes', 
    description="Dag - Processa os dados Mep",
    schedule_interval="0 2 * * *",  # Dias úteis às 2h
    catchup=False,
    default_args=default_args,
    tags=["tabela", "mep", "fato", "mvp"]
)

start_task = EmptyOperator(
    task_id='start_task', 
    dag=dag
)

done_task = EmptyOperator(
    task_id='done_task',
    dag=dag
)

    
tb_ft_mvp_antecipacoes = PythonOperator(
    task_id="tb_ft_mvp_antecipacoes", 
    python_callable=get_mvp_antecipacoes, 
    dag=dag
)

sp_atualiza_antecipacoes = PostgresOperator(
        task_id='sp_atualiza_antecipacoes_tb_ft_mep',
        postgres_conn_id='postgresql_bi',
        sql='CALL load.sp_dm_mvp_estabelecimentos()', 
        autocommit=True,
        dag=dag
)


start_task >> tb_ft_mvp_antecipacoes >> sp_atualiza_antecipacoes >> done_task  