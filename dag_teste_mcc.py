import sys
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.task_group import TaskGroup
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta
from mvp_mcc import get_mvp_mcc
import pendulum


local_tz = pendulum.timezone("America/Sao_Paulo")

default_args = {
    'owner': 'Airflow',
    'depends_on_past': False,
    'start_date': datetime(2025,2,8, tzinfo=local_tz),
    'email': ['guilherme.tenorio@valorem.com','geovane.andrade@valorem.com.br'],
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}


dag = DAG(
    'dag_dimenssoes_mvp_mep_V2', 
    description="Dag - Processa Dimensões Mep",
    schedule_interval= "15 6 * * 1-5",
    catchup=False,
    default_args=default_args,
    tags=["tabela","mep","dimensao","mvp"]
)

start_task = EmptyOperator(
    task_id='start_task', 
    dag=dag
)

done_task = EmptyOperator(
    task_id='done_task',
    dag=dag
)

with TaskGroup(
    group_id="task_group_dimenssoes_v2",
    default_args={"conn_id": "postgres_default"},
    tooltip="Roda a primeira camada de extração. Os dados passa pela extract e são salvos em tabelas no schema transform",
    dag=dag,
) as gr_tabelas_dimenssoes:
    
    tab_dm_mvp_mcc = PythonOperator(
        task_id="tb_dm_mvp_mcc", 
        python_callable=get_mvp_mcc, 
        dag=dag
    )
    [tab_dm_mvp_mcc]

start_task >> gr_tabelas_dimenssoes >> done_task