from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

def print_hello():
    print("Hello, World!")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),  # Stała data zamiast timedelta
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'reddit_data_pipeline',
    default_args=default_args,
    description='Hourly Reddit data collection and processing',
    schedule='@hourly',  # Zmienione z schedule_interval na schedule
    catchup=False,
    tags=['reddit', 'kafka', 'ml'],
) as dag:

    run_hello_world = PythonOperator(
        task_id='run_hello_world',
        python_callable=print_hello,
    )
