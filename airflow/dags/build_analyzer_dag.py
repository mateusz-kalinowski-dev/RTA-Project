from airflow.decorators import dag, task
from airflow import DAG
from datetime import datetime, timedelta
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='Run_Analysis_Container_DAG',
    description='Runs analysis on streamed data from Kafka using a Docker container',
    default_args=default_args,
    max_active_runs=1,
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["Kafka", "Analysis", "Docker"]
) as dag:

    run_analysis = DockerOperator(
        task_id='run_analysis',
        image='analyzer:latest',
        container_name='analyzer_airflow_triggered',
        api_version="auto",
        command='python /analyzer/analyzer.py',
        auto_remove='success',
        docker_url='unix://var/run/docker.sock',
        network_mode='rta-project_rta-network',
        mount_tmp_dir=False,
        working_dir="/analyzer",
    )
    trigger_consumer = TriggerDagRunOperator(
        task_id='Trigger_Consumer_DAG',
        trigger_dag_id='Consumer_DAG',  
        wait_for_completion=False          
    )
    trigger_consumer >> run_analysis