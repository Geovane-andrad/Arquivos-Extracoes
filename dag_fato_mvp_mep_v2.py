import sys
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta
from airflow.utils.task_group import TaskGroup
from mvp_lancamentos import get_mvp_lancamentos
from mvp_parcelas import get_mvp_parcelas
from mvp_chargeback import get_mvp_chargeback
from mvp_cancelamentos import get_mvp_cancelamentos
import pendulum


local_tz = pendulum.timezone("America/Sao_Paulo")

default_args = {
    'owner': 'Airflow',
    'depends_on_past': False,
    'start_date': datetime(2025,2,11, tzinfo=local_tz),
    'email': ['guilherme.tenorio@valorem.com','geovane.andrade@valorem.com.br'],
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}


dag = DAG('dag_fato_mvp_mep_v2', 
          description="Dag - Processa dados Mep",
          schedule_interval= "15 6,16 * * 1-5",
          catchup=False,
          default_args=default_args,
          tags=["tabela","mep","fato","mvp"]
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
    group_id="grupo_1",
    default_args={"conn_id": "postgres_default"},
    tooltip="Primeiro grupo de carga; atualiza as informações de cancelamento e preenche a tabela de agregação.",
    prefix_group_id=True,
    dag=dag,
) as grupo_1:
    
   tb_ft_mvp_cancelamentos = PythonOperator(
        task_id="tb_ft_mvp_cancelamentos", 
        python_callable=get_mvp_cancelamentos, 
        dag=dag
    )
   mvp_agregacao_cancelamento = PostgresOperator(
        task_id='sp_atualiza_tb_ft_mep_can',
        postgres_conn_id='postgresql_bi',
        sql='CALL load.sp_atualiza_tb_ft_mep_can()', 
        autocommit=True,
        dag=dag
    )
   
   tb_ft_mvp_cancelamentos >> mvp_agregacao_cancelamento

with TaskGroup(
    group_id="grupo_2",
    default_args={"conn_id": "postgres_default"},
    tooltip="Segundo grupo de carga; atualiza as informações de chargeback e preenche a tabela de agregação.",
    prefix_group_id=True,
    dag=dag,
) as grupo_2:
    
   tb_ft_mvp_chargeback = PythonOperator(
        task_id="tb_ft_mvp_chargeback", 
        python_callable=get_mvp_chargeback, 
        dag=dag
    )
   mvp_agregacao_chargeback = PostgresOperator(
        task_id='sp_atualiza_tb_ft_mep_cha',
        postgres_conn_id='postgresql_bi',
        sql='CALL load.sp_atualiza_tb_ft_mep_cha()', 
        autocommit=True,
        dag=dag
    )
   
   tb_ft_mvp_chargeback >> mvp_agregacao_chargeback

with TaskGroup(
    group_id="grupo_3",
    default_args={"conn_id": "postgres_default"},
    tooltip="Terceiro grupo de carga; atualiza as informações de lançamento.",
    prefix_group_id=True,
    dag=dag,
) as grupo_3:
    
   tb_ft_mvp_lancamentos = PythonOperator(
        task_id="tb_ft_mvp_lancamento", 
        python_callable=get_mvp_lancamentos, 
        dag=dag
    )
   
   mvp_load_lancamentos = PostgresOperator(
        task_id='sp_atualiza_load_tb_ft_lancamentos',
        postgres_conn_id='postgresql_bi',
        sql='CALL load.sp_atualiza_mvp_lancamentos()', 
        autocommit=True,
        dag=dag
    )
   
   tb_ft_mvp_lancamentos >> mvp_load_lancamentos


start_task >> [grupo_1, grupo_2, grupo_3] >> done_task
