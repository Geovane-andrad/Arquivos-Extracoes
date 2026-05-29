from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
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

# ── Wrappers com import lazy — evita conexão com banco no momento do import da DAG ──

def executar_usuarios():
    from bitrix_usuarios import get_bitrix_usuarios
    get_bitrix_usuarios()

def executar_usuarios_departamento():
    from bitrix_usuario_departamento import get_bitrix_usuarios_departamentos
    get_bitrix_usuarios_departamentos()

def executar_departamentos():
    from bitrix_departamentos import get_bitrix_departamentos
    get_bitrix_departamentos()

def executar_company():
    from bitrix_company import get_bitrix_company
    get_bitrix_company()

def executar_spa138():
    from bitrix_spa138_cadastro import get_bitrix_spa138_cadastro
    get_bitrix_spa138_cadastro()

def executar_spa183():
    from bitrix_spa183_monitoramento import get_bitrix_spa183_monitoramento
    get_bitrix_spa183_monitoramento()

def executar_etapas():
    from bitrix_spa_etapas import get_bitrix_spa_etapas
    get_bitrix_spa_etapas()

def executar_enum():
    from bitrix_spa_enum import get_bitrix_spa_enum
    get_bitrix_spa_enum([138, 183])

def executar_campos_personalizados():
    from bitrix_campos_personalizados import get_bitrix_campos_personalizados
    get_bitrix_campos_personalizados()


with DAG(
    'dag_bitrix',
    description="Dag - Processa os dados extraídos do CRM BITRIX",
    schedule_interval="0 8,18 * * 1-5",
    catchup=False,
    default_args=default_args,
    tags=["tabela", "valores", "dim", "bitrix"]
) as dag:

    start_task = EmptyOperator(task_id='start_task')
    done_task  = EmptyOperator(task_id='done_task')

    # ── FASE 1: extração paralela ──────────────────────────────────────────
    with TaskGroup(
        group_id="fase1_extracao_bitrix",
        tooltip="Extrai dimensões e fatos do Bitrix em paralelo"
    ) as fase1_extracao:

        t_usuarios = PythonOperator(
            task_id="usuarios",
            python_callable=executar_usuarios
        )
        t_usuarios_depto = PythonOperator(
            task_id="usuarios_departamento",
            python_callable=executar_usuarios_departamento
        )
        t_departamentos = PythonOperator(
            task_id="departamentos",
            python_callable=executar_departamentos
        )
        t_etapas = PythonOperator(
            task_id="etapas_spa",
            python_callable=executar_etapas
        )
        t_enum = PythonOperator(
            task_id="enum_spa",
            python_callable=executar_enum
        )
        t_campos = PythonOperator(
            task_id="campos_personalizados",
            python_callable=executar_campos_personalizados
        )
        t_spa138 = PythonOperator(
            task_id="spa138_cadastro",
            python_callable=executar_spa138
        )
        t_spa183 = PythonOperator(
            task_id="spa183_monitoramento",
            python_callable=executar_spa183
        )
        t_company = PythonOperator(
            task_id="company",
            python_callable=executar_company
        )

        # company depende de usuarios e departamentos
        [t_usuarios, t_usuarios_depto, t_departamentos] >> t_company

        # t_etapas, t_enum, t_campos, t_spa138, t_spa183 rodam em paralelo

    # ── FASE 2: união Bitrix × QProf ──────────────────────────────────────
    t_cadastro = PostgresOperator(
        task_id="sp_atualiza_load_bitrix_cadastro",
        postgres_conn_id='postgresql_bi',
        sql='CALL load.sp_atualiza_bitrix_cadastro()',
        autocommit=True
    )

    t_uniao = PostgresOperator(
        task_id="sp_atualiza_uniao_bitrix_qprof",
        postgres_conn_id='postgresql_bi',
        sql='CALL load.sp_atualiza_uniao_bitrix_qprof()',
        autocommit=True
    )

    # ── FASE 3: enriquecimento e refresh das MVs ───────────────────────────
    with TaskGroup(
        group_id="fase3_enriquecimento",
        tooltip="Enriquece tabelas load e refresha materialized views"
    ) as fase3_enriquecimento:

        t_monitoramento = PostgresOperator(
            task_id="sp_atualiza_bitrix_monitoramento",
            postgres_conn_id='postgresql_bi',
            sql='CALL load.sp_atualiza_bitrix_monitoramento()',
            autocommit=True
        )
        t_mv_cadastro = PostgresOperator(
            task_id="mv_tb_ft_cadastro_bitrix",
            postgres_conn_id='postgresql_bi',
            sql='REFRESH MATERIALIZED VIEW metabase.mv_tb_ft_cadastro_bitrix',
            autocommit=True,
            trigger_rule='all_done'
        )
        t_mv_monitoramento = PostgresOperator(
            task_id="mv_tb_ft_monitoramento_bitrix",
            postgres_conn_id='postgresql_bi',
            sql='REFRESH MATERIALIZED VIEW metabase.mv_tb_ft_monitoramento_bitrix',
            autocommit=True,
            trigger_rule='all_done'
        )

        t_monitoramento >> [t_mv_cadastro, t_mv_monitoramento]

    start_task >> fase1_extracao >> t_uniao >> t_cadastro >> fase3_enriquecimento >> done_task