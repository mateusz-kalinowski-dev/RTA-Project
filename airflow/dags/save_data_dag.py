from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging
import sys
import os
import time

# Importing the include folder path to access the module.
scripts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../include/jobs'))
sys.path.insert(0, scripts_path)

import consumer_mongo as job

def run_dag():
    logging.info("Waiting for other services to stabilize...")
    time.sleep(40)
    job.process_messages()
    logging.info("Task completed")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='Consumer_DAG',
    description='Collects data from Kafka topics and saves it to MongoDB',
    default_args=default_args,
    max_active_runs=1,
    start_date=datetime(2025, 1, 1),
    schedule=None, 
    catchup=False,
    tags=["Kafka", "MongoDB", "Save"],
) as dag:

    save_data_task = PythonOperator(
        task_id='Consume_and_save_data',
        python_callable=run_dag
    )

    save_data_task