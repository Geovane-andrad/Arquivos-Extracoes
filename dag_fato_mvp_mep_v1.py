import sys
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta
from airflow.utils.task_group import TaskGroup
from mvp_transacoes import get_mvp_transacoes
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
    'dag_fato_mvp_mep_v1', 
    description="Dag - Processa os dados Mep",
    schedule_interval="15 6,16 * * 1-5",  # Dias úteis às 2h
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

with TaskGroup(
    group_id="task_group_transacoes",
    default_args={"conn_id": "postgres_default"},
    tooltip="Busca as Informações de transações por empresa e gera tabelas",
    dag=dag,
) as grupo_transacoes:
    
    tb_ft_mvp_transacoes = PythonOperator(
        task_id="tb_ft_mvp_transacoes", 
        python_callable=get_mvp_transacoes, 
        dag=dag
    )

    mvp_agragacao_transacoes = PostgresOperator(
        task_id='sp_atualiza_tb_ft_mep_tra',
        postgres_conn_id='postgresql_bi',
        sql='CALL load.sp_atualiza_tb_ft_mep_tra()', 
        autocommit=True,
        dag=dag
    )

    tb_ft_mvp_transacoes >> mvp_agragacao_transacoes

with TaskGroup(
    group_id="task_group_antecipacoes",
    default_args={"conn_id": "postgres_default"},
    tooltip="Busca as antecipações por empresa e gera as tabelas",
    dag=dag,
) as grupo_antecipacoes:
    
    tb_ft_mvp_antecipacoes = PythonOperator(
        task_id="tb_ft_mvp_antecipacoes", 
        python_callable=get_mvp_antecipacoes, 
        dag=dag
    )

    mvp_agragacao_antecipacoes = PostgresOperator(
        task_id='sp_atualiza_tb_ft_mep_ant',
        postgres_conn_id='postgresql_bi',
        sql='CALL load.sp_atualiza_tb_ft_mep_ant()', 
        autocommit=True,
        dag=dag
    )

    tb_ft_mvp_antecipacoes >> mvp_agragacao_antecipacoes

start_task >> grupo_transacoes >> grupo_antecipacoes >> done_task  