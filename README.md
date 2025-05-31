# RTA Project

## Overview

**RTA Project** is a modular data pipeline and analytics platform designed for collecting, processing, analyzing, and visualizing data (e.g., from Reddit). The system leverages modern technologies such as Apache Airflow, Kafka, MongoDB, and a full-stack web application (React + Flask) to provide a robust, scalable, and extensible solution.

## Project Structure

```
.
├── analyzer/         # Data analysis microservice (Python)
├── airflow/          # Workflow orchestration (Apache Airflow)
├── backend/          # REST API backend (Flask)
├── frontend/         # Web user interface (React + Tailwind)
├── docker-compose.yml
└── README.md
```

### Main Components

- **frontend/**: React-based web application for data visualization and user interaction. Uses Tailwind CSS for styling and Vite for development.
- **backend/**: Python Flask REST API serving data to the frontend, connecting to MongoDB.
- **analyzer/**: Python microservice for advanced data analysis, processing data from MongoDB.
- **airflow/**: Contains DAGs and jobs for orchestrating data collection, processing, and analysis workflows.
- **docker-compose.yml**: Orchestrates all services (including Kafka, MongoDB, Airflow, backend, analyzer, frontend) for local development and deployment.

## Technologies Used

- **Frontend**: React, Tailwind CSS, Vite, Nginx
- **Backend**: Python, Flask, MongoDB
- **Analyzer**: Python, ML models
- **Orchestration**: Apache Airflow
- **Messaging**: Kafka, Zookeeper
- **Database**: MongoDB
- **Other**: Redpanda Console (Kafka UI), PostgreSQL (for Airflow metadata)

## How It Works

1. **Data Collection**: Airflow DAGs trigger jobs (e.g., scraping Reddit) and push data to Kafka.
2. **Data Ingestion**: Kafka jobs consume and store data in MongoDB.
3. **Analysis**: The analyzer service processes data through ML model andsave data in MongoDB.
4. **API**: The backend exposes REST endpoints for the frontend.
5. **Visualization**: The frontend displays analytics and dashboards to the user.

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)
- (Optional) Node.js and Python for local development outside Docker

### Quick Start (Recommended)

1. **Clone the repository:**

   ```bash
   git clone <repo-url>
   cd RTA-Project
   ```
2. **Create a `.env` file** Copy or create a `.env` file in the root directory and Analyzer directory with necessary environment variables.
3. **Build and start all services:**

   ```bash
   docker-compose up --build
   ```
4. **Access the services:**

   - **Frontend**: [http://localhost:3000](http://localhost:3000)
   - **Backend API**: [http://localhost:5000](http://localhost:5000)
   - **Airflow UI**: [http://localhost:8081](http://localhost:8081)
   - **Redpanda Console (Kafka UI)**: [http://localhost:8080](http://localhost:8080)

### Stopping the Project

```bash
docker-compose down
```

## Customization

- **Add new data sources**: Implement new Airflow DAGs and in `airflow/dags/` and jobs in `airflow/include/jobs/`.
- **Extend analysis**: Add logic to `analyzer/analyzer.py`.
- **Expand API**: Add endpoints in `backend/app.py`.
- **Enhance UI**: Add React components in `frontend/src/components/`.
