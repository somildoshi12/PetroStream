# 🛢️ PetroStream: Serverless Oil & Gas Data Lake (AWS)

**A Real-Time Data Pipeline for Anomaly Detection in Offshore Wells.**

---

## 🏗️ Project Blueprint

**Detailed Architecture & Execution Plan**

This project simulates a real-time data stream from offshore oil wells, processes it for anomalies using Machine Learning (Isolation Forest), stores it in a Data Lake (S3), and visualizes it on a Unified Dashboard (Streamlit + Power BI).

### 🚀 Key Features

- **Serverless**: Uses AWS Kinesis, Lambda, Glue, and Athena.
- **Containerized**: ML Consumer and Streamlit App run on **AWS ECS Fargate**.
- **Cost-Optimized**: Uses **Spot Instances** and efficient resource tuning (<$5/month if managed).
- **Hybrid Visualization**: Real-time operational data in **Streamlit**, executive BI in **Power BI**.
- **One-Click Operations**: `project_up.sh` to deploy, `project_down.sh` to destroy.

---

## 🛠️ Technology Stack

| Component      | Technology          | Description                                          |
| :------------- | :------------------ | :--------------------------------------------------- |
| **Source**     | **Parquet**         | Petrobras 3W Dataset (Real & Simulated Well Data).   |
| **Ingestion**  | **AWS Kinesis**     | Real-time data streaming (Producer runs locally).    |
| **Processing** | **Python (Docker)** | ML Consumer app running Isolation Forest model.      |
| **Compute**    | **AWS ECS Fargate** | Serverless container orchestration (Spot Instances). |
| **Storage**    | **AWS S3**          | Raw data, Curated data, and Athena query results.    |
| **Catalog**    | **AWS Glue**        | Data Catalog for schema discovery.                   |
| **Query**      | **AWS Athena**      | SQL engine to query Parquet files in S3.             |
| **Frontend**   | **Streamlit**       | Real-time Operations Dashboard (Python).             |
| **BI**         | **Power BI**        | Executive Analytics Dashboard (Connects via ODBC).   |
| **IaC**        | **Terraform**       | Infrastructure as Code for all AWS resources.        |
| **CI/CD**      | **GitHub Actions**  | Automated testing and deployment.                    |

---

## 📐 Architecture Diagram

```mermaid
graph TD
    User((User/Producer)) -->|Stream Data| Kinesis[Kinesis Data Stream]
    Kinesis -->|Firehose| S3_Raw[(S3 Raw Data)]
    Kinesis -->|Consumer App| ECS[ECS Fargate (ML Consumer)]
    ECS -->|Anomalies| S3_Curated[(S3 Curated Data)]
    Glue[Glue Crawler] -->|Catalog| Athena[Amazon Athena]
    Athena -->|SQL| Streamlit[Streamlit Dashboard]
    Athena -->|ODBC| PowerBI[Power BI Dashboard]
    Streamlit -->|Unified View| User
```

---

## 💰 Cost Optimization Strategy (Budget: $120)

We have implemented strict cost controls to ensure the project stays within budget.

1.  **Spot Instances**: We use **Fargate Spot** capacity providers, saving ~70% on compute costs vs. On-Demand.
    - _Note_: Spot instances may be interrupted, but our data is safely stored in S3/Kinesis, so no data is lost.
2.  **Resource Tuning**:
    - **Kinesis**: 1 Shard (sufficient for demo volume).
    - **Lambda**: Minimal memory allocation (128MB - 256MB).
    - **Retention**: CloudWatch Logs expire after 1 day. S3 data is kept **indefinitely** (Standard Class).
3.  **Project Switch**: The `project_down.sh` script completely destroys all infrastructure when you are done working.

---

## 🚦 Project Controls: The "Switch"

We use shell scripts to manage the lifecycle of the project.

### 🟢 Start Project (`./scripts/project_up.sh`)

1.  Initializes Terraform.
2.  Applies Infrastructure (S3, Kinesis, ECS, ECR).
3.  Builds and Pushes Docker Images.
4.  Deploys ECS Services.

### 🔴 Stop Project (`./scripts/project_down.sh`)

1.  **Empty S3 Buckets**: Removes all files (Terraform cannot delete non-empty buckets).
2.  **Terraform Destroy**: Tears down all AWS resources.
3.  **Result**: $0 cost until you run `up` again.

---

## 📅 Execution Phases

### Phase 1: Infrastructure Setup (Terraform)

- Set up S3 buckets, Kinesis Streams, IAM Roles, and ECR Repositories.

### Phase 2: Machine Learning (Local)

- Train Isolation Forest model on `SIMULATED` data locally.
- Save model (`model.joblib`) and upload to S3 for the consumer to use.

### Phase 3: Stream Processing

- Develop Python Consumer App.
- Containerize with Docker.
- Deploy to ECS Fargate (Spot) with Auto-Scaling.

### Phase 4: Frontend (Streamlit)

- Develop Streamlit App for real-time visualization.
- Connect to Athena.
- Embed/Link to Power BI Dashboard.

### Phase 5: Business Intelligence (Power BI)

- Connect Power BI Desktop to Athena via ODBC.
- Build Executive Dashboard for historical trends.

### Phase 6: CI/CD Pipeline

- GitHub Actions workflow to automate Terraform planning and Docker builds.

### Phase 7: Data Producer

- Python script to replay local Parquet files into Kinesis.

---

## 📂 Project Structure

```
.
├── infra/                  # Terraform Infrastructure code
│   └── terraform/
├── ml/                     # Machine Learning scripts
│   └── train_model.py
├── producer/               # Data Producer script
│   └── producer.py
├── consumer/               # Stream Processing App
│   ├── app.py
│   └── Dockerfile
├── dashboard/              # Streamlit Frontend
│   ├── app.py
│   └── Dockerfile
├── scripts/                # Control Scripts
│   ├── project_up.sh
│   └── project_down.sh
├── .github/                # CI/CD Workflows
│   └── workflows/
├── Petrobras Data/         # Local Source Data
└── README.md               # You are here
```
