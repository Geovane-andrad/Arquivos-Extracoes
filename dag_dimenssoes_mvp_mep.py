import sys
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.task_group import TaskGroup
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta
from mvp_estabelecimentos import get_estabelecimentos_mvp
from mvp_dispositivosEC import get_dispositivos_ec_mvp
from mvp_dispositivosGeral import get_dispositivos_geral_mvp
from gsurf_dispositivos import get_dispositivos_gsurf
from mvp_taxas import get_mvp_taxas
from mvp_acordos_taxas import get_mvp_acordo_taxas
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
    'dag_dimenssoes_mvp_mep', 
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
    group_id="task_group_dimenssoes",
    default_args={"conn_id": "postgres_default"},
    tooltip="Roda a primeira camada de extração. Os dados passa pela extract e são salvos em tabelas no schema transform",
    dag=dag,
) as gr_tabelas_dimenssoes:
    
    tab_dim_mvp_estabelecimentos = PythonOperator(
        task_id="tb_dm_mvp_estabelecimentos", 
        python_callable=get_estabelecimentos_mvp, 
        dag=dag
    )

    tab_dim_mvp_dispositivos_ec = PythonOperator(
        task_id="tb_dm_mvp_dispositivos_ec", 
        python_callable=get_dispositivos_ec_mvp, 
        dag=dag
    )
  
    tab_dim_mvp_dispositivos_geral = PythonOperator(
        task_id="tb_dm_mvp_dispositivos_geral", 
        python_callable=get_dispositivos_geral_mvp, 
        dag=dag
    )

    tab_dim_gsurf_dispositivos = PythonOperator(
        task_id="tb_dm_gsurf_dispositivos", 
        python_callable=get_dispositivos_gsurf, 
        dag=dag
    )

    [tab_dim_mvp_estabelecimentos, tab_dim_mvp_dispositivos_ec, tab_dim_mvp_dispositivos_geral, tab_dim_gsurf_dispositivos]

with TaskGroup(
    group_id="task_group_taxas",
    default_args={"conn_id": "postgres_default"},
    tooltip="Roda a primeira camada de extração das taxas e dos planos de taxas. Os dados passa pela extract e são salvos em tabelas no schema transform",
    dag=dag,
) as gr_tabelas_dimenssoes_taxas:

    tab_dim_mvp_acordo_taxas = PythonOperator(
        task_id="tb_dm_mvp_acordo_taxas", 
        python_callable=get_mvp_acordo_taxas, 
        dag=dag
    )

    tab_dm_mvp_taxas = PythonOperator(
        task_id="tb_dm_mvp_taxas", 
        python_callable=get_mvp_taxas, 
        dag=dag
    )

    tab_dm_mvp_mcc = PythonOperator(
        task_id="tb_dm_mvp_mcc", 
        python_callable=get_mvp_mcc, 
        dag=dag
    )

    [tab_dim_mvp_acordo_taxas >> tab_dm_mvp_taxas >> tab_dm_mvp_mcc]

with TaskGroup(
    group_id="task_group_procedures",
    default_args={"conn_id": "postgres_default"},
    tooltip="Roda as procedures utilizadas na criação da tabelas do schema load.",
    dag=dag,
) as gr_procedures:

    sp_mvp_dm_estabelecimentos = PostgresOperator(
        task_id='sp_dm_mvp_atualizaEstabelecimentos',
        postgres_conn_id='postgresql_bi',
        sql='CALL load.sp_dm_mvp_estabelecimentos()', 
        autocommit=True,
        dag=dag
    )

    sp_mvp_dm_historico_estabelecimentos = PostgresOperator(
        task_id='sp_mvp_dm_historico_estabelecimentos',
        postgres_conn_id='postgresql_bi',
        sql='CALL load.sp_atualiza_mvp_historico_estabelecimento()', 
        autocommit=True,
        dag=dag
    )

    sp_mvp_dm_historico_dispositivos = PostgresOperator(
        task_id='sp_dm_gsurf_historico_dispositivos',
        postgres_conn_id='postgresql_bi',
        sql='call load.sp_atualiza_historico_dispositivos()', 
        autocommit=True,
        dag=dag
    )
    
    [sp_mvp_dm_estabelecimentos, sp_mvp_dm_historico_estabelecimentos, sp_mvp_dm_historico_dispositivos]

start_task >> gr_tabelas_dimenssoes >> gr_tabelas_dimenssoes_taxas >> gr_procedures >> done_task