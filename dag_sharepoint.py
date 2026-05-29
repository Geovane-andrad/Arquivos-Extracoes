import uuid
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
from airflow.utils.task_group import TaskGroup
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


# ── Wrappers com import lazy — evita conexão com banco no parse da DAG ─────────
# Os quatro módulos importam sys_conexaoBanco no nível do módulo; importar no
# topo da DAG abriria conexão a cada heartbeat do scheduler.

def gerar_id_grupo(**context):
    """Gera o UUID do lote e o empurra para XCom.
    As tasks B3, CERC e BMP puxam esse valor para gravar o mesmo
    id_grupo_arquivo em todos os registros do dia.
    """
    id_grupo = str(uuid.uuid4())
    context['ti'].xcom_push(key='id_grupo_arquivo', value=id_grupo)
    print(f"🔑 id_grupo_arquivo gerado: {id_grupo}")
    return id_grupo


def executar_cnpj_agenda(**context):
    from sharepoint_importar_cnpj_agenda import executar_etl
    executar_etl()


def executar_b3_agenda(**context):
    id_grupo = context['ti'].xcom_pull(
        task_ids='gerar_id_grupo', key='id_grupo_arquivo'
    )
    from sharepoint_importar_b3_agenda import executar_etl
    executar_etl(id_grupo_externo=id_grupo)


def executar_cerc_agenda(**context):
    id_grupo = context['ti'].xcom_pull(
        task_ids='gerar_id_grupo', key='id_grupo_arquivo'
    )
    from sharepoint_importar_cerc_agenda import executar_etl
    executar_etl(id_grupo_externo=id_grupo)


def executar_bmp_agenda(**context):
    id_grupo = context['ti'].xcom_pull(
        task_ids='gerar_id_grupo', key='id_grupo_arquivo'
    )
    from sharepoint_importar_bmp_agenda import executar_etl
    executar_etl(id_grupo_externo=id_grupo)


with DAG(
    'dag_sharepoint',
    description="Dag - Processa os arquivos de consulta de agenda do SharePoint.",
    schedule_interval="0 14 * * 1-5",  # Segunda a sexta às 14h (horário de Brasília)
    catchup=False,
    default_args=default_args,
    tags=["sharepoint", "Consulta_Agenda"]
) as dag:

    start_task = EmptyOperator(task_id='start_task')

    # trigger_rule padrão 'all_success': done_task só fecha verde se todas as
    # tasks upstream tiverem sucesso — qualquer falha propaga o vermelho.
    done_task = EmptyOperator(task_id='done_task')

    # ── Gera o UUID compartilhado do lote ──────────────────────────────────────
    t_gerar_id = PythonOperator(
        task_id='gerar_id_grupo',
        python_callable=gerar_id_grupo,
        provide_context=True
    )

    # ── CNPJ: dimensão independente, roda em paralelo com a geração do ID ──────
    t_cnpj = PythonOperator(
        task_id='importar_cnpj_agenda',
        python_callable=executar_cnpj_agenda,
        provide_context=True
    )

    # ── Cadeia sequencial das agendas: B3 → CERC → BMP ────────────────────────
    # Sequencial para garantir o mesmo id_grupo_arquivo no lote do dia.
    # CERC (~100k linhas) tem timeout estendido.
    with TaskGroup(
        group_id='agendas',
        tooltip='Importa B3, CERC e BMP em sequência com o mesmo id_grupo_arquivo'
    ) as agendas:

        t_b3 = PythonOperator(
            task_id='importar_b3_agenda',
            python_callable=executar_b3_agenda,
            provide_context=True
        )
        t_cerc = PythonOperator(
            task_id='importar_cerc_agenda',
            python_callable=executar_cerc_agenda,
            provide_context=True,
            execution_timeout=timedelta(minutes=30)
        )
        t_bmp = PythonOperator(
            task_id='importar_bmp_agenda',
            python_callable=executar_bmp_agenda,
            provide_context=True
        )

        t_b3 >> t_cerc >> t_bmp

    # ── Fluxo principal ────────────────────────────────────────────────────────
    #
    #   start ──┬── gerar_id ── [ B3 → CERC → BMP ] ──┐
    #           │                                       ├── done
    #           └── importar_cnpj ─────────────────────┘
    #
    start_task >> [t_gerar_id, t_cnpj]
    t_gerar_id >> agendas
    [agendas, t_cnpj] >> done_task