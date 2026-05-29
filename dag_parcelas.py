import sys
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta
from airflow.utils.task_group import TaskGroup
from mvp_parcelas import get_mvp_parcelas

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
    'dag_parcelas', 
    description="Dag - Processa os dados Mep",
    schedule_interval="0 2 * * 1-5",  # Dias úteis às 2h
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

    
tb_ft_mvp_parcelas = PythonOperator(
    task_id="tb_ft_mvp_parcelas", 
    python_callable=get_mvp_parcelas, 
    dag=dag
)


start_task >> tb_ft_mvp_parcelas >> done_task  