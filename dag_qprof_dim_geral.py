
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta
from airflow.utils.task_group import TaskGroup
import pendulum
from qprof_usuario import get_qprof_usuario
from qprof_usuario_sistema import get_qprof_usuario_sistema
from qprof_evento_nfe import get_qprof_evento_nfe


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

dag = DAG('dag_qprof_dim_geral', 
          description="Dag - Processa atualiza os dados das tabelas dimenssões extraídas do Qprof.",
          schedule_interval="10 13 * * 1-5",
          catchup=False,
          default_args=default_args,
          tags=["tabela","qprof","dimenssao"]
)

start_task = EmptyOperator(
        task_id='start_task', 
        dag=dag 
)

done_task = EmptyOperator(
    task_id='done_task',
    dag=dag
)

finish_extract = EmptyOperator(
    task_id='finish_extract',
    dag=dag
)

with TaskGroup(
    group_id="gr_extract_usuarios",
    default_args={"conn_id": "postgres_default"},
    tooltip="Extrai informações de usuarios e coloca até o Schema Transform",
    prefix_group_id=True,
    dag=dag,  
) as gr_extract_usuarios:
    
    tb_dm_usuario = PythonOperator(task_id="tb_dm_usuario", python_callable=get_qprof_usuario, dag=dag)
    tb_dm_usuarioSistema = PythonOperator(task_id="tb_dm_usuarioSistema", python_callable=get_qprof_usuario_sistema, dag=dag)

    [tb_dm_usuario, tb_dm_usuarioSistema] 

with TaskGroup(
    group_id="gr_extract_eventos_nfe",
    default_args={"conn_id": "postgres_default"},
    tooltip="Extrai informações dos eventos das notas fiscais e coloca até o Schema Transform",
    prefix_group_id=True,
    dag=dag,  
) as gr_extract_eventos_nfe:

    tb_dm_eventosNfe = PythonOperator(task_id="tb_dm_eventosNfe", python_callable=get_qprof_evento_nfe, dag=dag)

    [tb_dm_eventosNfe]

start_task >> [gr_extract_usuarios, gr_extract_eventos_nfe] >> finish_extract >>  done_task