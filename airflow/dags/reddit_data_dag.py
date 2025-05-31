from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta
import logging
import sys
import os
import time

# Importing the include folder path to access the module.
scripts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../include/jobs'))
sys.path.insert(0, scripts_path)

import scrapp_reddit_job as job

def run_dag():
    logging.info("Waiting for other services to stabilize...")
    time.sleep(30)
    job.collect_reddit_data()
    logging.info("Task completed")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='Scrapp_Reddit_DAG',
    description='Collects data from Reddit API and sends it to Kafka',
    default_args=default_args,
    max_active_runs=1,
    start_date=datetime(2025, 1, 1),
    schedule='@hourly', 
    catchup=False,
    tags=["Reddit", "Kafka", "Scrapper"],
) as dag:

    collect_task = PythonOperator(
        task_id='Collect_Reddit_data',
        python_callable=run_dag
    )
    trigger_analyzer = TriggerDagRunOperator(
        task_id='Trigger_Consumer_DAG',
        trigger_dag_id='Run_Analysis_Container_DAG',  
        wait_for_completion=False          
    )

    trigger_analyzer >> collect_task