
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta
from airflow.utils.task_group import TaskGroup
from qprof_ocorrencia_titulo import get_qprof_ocorrenciaTitulo
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

dag = DAG('dag_qprof_ocorrencia_titulo', 
          description="Dag - Processa ocorrencia Titulos",
          schedule_interval="10 13 * * 1-5",
          catchup=False,
          default_args=default_args,
          tags=["tabela","qprof","fato"]
)



start_task = EmptyOperator(
        task_id='start_task', 
        dag=dag 
)

done_task = EmptyOperator(
    task_id='done_task',
    dag=dag
)

tab_fat_ocorrenciaFundo = PythonOperator(task_id="tb_ft_qprof_ocorrencia_titulos", python_callable=get_qprof_ocorrenciaTitulo, dag=dag)


start_task >> tab_fat_ocorrenciaFundo >> done_task 