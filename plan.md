# PetroStream: Serverless Real-Time Oil & Gas Data Lake

## 1. Executive Summary
**Project Name:** PetroStream
**Domain:** Energy / Oil & Gas
**Goal:** Build a production-grade, end-to-end **Serverless Data Lake** that ingests real-time sensor data from offshore rigs, detects critical failures, and enables historical analytics—all without managing a single server.

**Why this Project?**
*   **Industry Standard:** This exact architecture (Ingest $\rightarrow$ Buffer $\rightarrow$ Compute $\rightarrow$ Storage $\rightarrow$ Analyze) is used by Fortune 500 companies.
*   **Cost Efficiency:** Built entirely on **AWS Serverless** technologies. You pay only for what you use. With your $200 credit, this project is effectively **free**.
*   **"Big Data" Logic:** Even though we use small data for testing, the architecture scales to Petabytes automatically.

---

## 2. The Dataset: Real-World "Petrobras 3W"
We will use the **Petrobras 3W Dataset** (Publicly available on Kaggle/GitHub). This is a rare, high-quality dataset of real offshore oil well sensors.

### **What is inside each file?**
Each CSV file represents one "Event" (like a startup, normal operation, or failure) from a specific well.
*   **Rows:** Time-series data points (every second).
*   **Columns (Sensors):**
    1.  `P-PDG`: Pressure at the bottom of the well.
    2.  `P-TPT`: Pressure at the temperature transducer.
    3.  `T-TPT`: Temperature at the transducer.
    4.  `P-MON-CKP`: Pressure at the choke valve (upstream).
    5.  `T-JUS-CKP`: Temperature at the choke valve (downstream).
    6.  `class`: The label (0 = Normal, 1 = Fault).

### **Example Snippet (Gist)**
```csv
timestamp,          P-PDG,      P-TPT,      T-TPT,      P-MON-CKP,  T-JUS-CKP,  class
2017-01-01 00:00:01, 250.4,      180.2,      55.1,       80.5,       42.3,       0
2017-01-01 00:00:02, 250.5,      180.3,      55.1,       80.4,       42.3,       0
2017-01-01 00:00:03, 310.8,      210.1,      68.4,       95.2,       50.1,       1  <-- ANOMALY!
```
*Note: In the raw dataset, these are often normalized or anonymous, but they follow this physical structure.*

---

## 3. High-Level Architecture
We are building an **Event-Driven Pipeline**. Data flows through the system automatically as it is generated.

```mermaid
graph TD
    subgraph "Data Source (Local)"
        Producer[Python Script: Reads '3W' CSV] -->|PutRecords| Kinesis[AWS Kinesis Data Stream]
    end

    subgraph "Real-Time Layer (Speed)"
        Kinesis -->|Trigger| Lambda[AWS Lambda (Anomaly Detection)]
        Lambda -->|Alert| SNS[Amazon SNS (Email/SMS)]
    end

    subgraph "Storage Layer (Batch)"
        Kinesis -->|Buffer| Firehose[Kinesis Data Firehose]
        Firehose -->|Convert to Parquet| S3[Amazon S3 (Data Lake)]
    end

    subgraph "Analytics Layer (Serving)"
        Crawler[AWS Glue Crawler] -->|Catalog Protocol| GlueDB[Glue Data Catalog]
        GlueDB -->|Metadata| Athena[Amazon Athena (Serverless SQL)]
        Athena -->|Visualize| QuickSight[Amazon QuickSight (Dashboards)]
    end
```

---

## 4. Technology Stack & Data Flow

| Stage | Technology | Why we use it? |
| :--- | :--- | :--- |
| **Ingestion** | **Amazon Kinesis Data Streams** | Acts as a scalable buffer for high-velocity data. Decouples producers from consumers. |
| **Compute** | **AWS Lambda** (Python) | Serverless compute. Runs our business logic (anomaly detection) only when data arrives. |
| **Storage** | **Amazon S3** (Standard) | Infinite, durable object storage. usage: storing raw and processed data (Parquet). |
| **Transformation** | **Kinesis Data Firehose** | Automatically batches streaming data, converts JSON to Parquet, and writes to S3. |
| **Catalog** | **AWS Glue Crawler** | Automatically discovers schema changes (e.g., new sensor columns) and updates the metadata. |
| **Analytics** | **Amazon Athena** | Serverless SQL engine. Allows us to query S3 files as if they were a database table. |
| **Infrastructure** | **Terraform** | Infrastructure as Code (IaC). Spin up/down the entire stack with one command to save costs. |

---

## 5. Detailed Implementation Guide

### Phase 0: Prerequisites & Setup
1.  **AWS Account:** Ensure you have access and your $200 credits are active.
2.  **AWS CLI:** Install and configure `aws configure` on your local machine.
3.  **Terraform:** Install Terraform for infrastructure management.
4.  **Dataset:** Download the **Petrobras 3W dataset** (specifically the "Rare Events" subset like *Hydrate Formation*).

### Phase 1: Infrastructure as Code (IaC)
*   **Goal:** Define the "Skeleton" of our cloud.
*   **Action:** Create a `main.tf` file.
*   **Resources to Define:**
    *   `aws_s3_bucket`: For storing data (`petrostream-datalake`).
    *   `aws_kinesis_stream`: 1 Shard (Cost: ~$0.015/hr).
    *   `aws_glue_catalog_database`: Logical container for our tables.
    *   `aws_iam_role`: Permissions for Lambda to read Kinesis and write to SNS.

### Phase 2: The Data Producer (Replay)
*   **Goal:** Simulate a live offshore rig.
*   **Action:** Write a Python script (`producer.py`) using `boto3`.
*   **Logic:**
    1.  Read a CSV file from the dataset row-by-row.
    2.  Inject a "current timestamp" (so it looks live).
    3.  Send the record to Kinesis using `put_record`.
    4.  Sleep for 0.1 seconds between rows to mimic real-time generation.

### Phase 3: Real-Time Processing (Lambda)
*   **Goal:** Detect dangerous pressure spikes immediately.
*   **Action:** Write a Lambda function (`process_stream.py`).
*   **Logic:**
    1.  Triggered by Kinesis (Batch size: 100 records).
    2.  Loop through records.
    3.  Check: `if pressure > 300: send_sns_alert()`.
    4.  Log metrics to CloudWatch.

### Phase 4: The Storage Layer (Firehose)
*   **Goal:** Efficiently store data for history.
*   **Action:** Create a Delivery Stream in Kinesis Firehose.
*   **Configuration:**
    *   **Source:** Kinesis Data Stream.
    *   **Destination:** S3 Bucket.
    *   **Buffer:** 60 seconds or 5MB (whichever comes first).
    *   **Format Conversion:** Convert JSON $\rightarrow$ **Apache Parquet** (uses AWS Glue for schema definition). *Critical for performance.*

### Phase 5: Analytics & Serving (Athena)
*   **Goal:** Answer business questions.
*   **Action:**
    1.  Run the **Glue Crawler** to "discover" the Parquet files in S3.
    2.  Go to **Athena** console.
    3.  Run SQL Queries:
        ```sql
        -- Calculate average pressure during failure events
        SELECT event_type, AVG(pressure) as avg_pressure
        FROM "petrostream_db"."sensors"
        WHERE timestamp > run_date - interval '1' hour
        GROUP BY event_type;
        ```

### Phase 6: Visualization (Optional / Bonus)
*   **Goal:** Executive Dashboard.
*   **Action:** Connect **Amazon QuickSight** to Athena.
*   **Visualize:** Create a line chart showing Pressure vs. Time.

---

## 6. Cost Safety & Management
You have **$200 credits**, which is a huge buffer. However, follow these rules to keep the "Bill" at $0:

1.  **Terraform Destroy:** Always run `terraform destroy` when you finish a coding session. This deletes the Kinesis stream (the only "active" cost).
2.  **Retention:** Set Kinesis retention to **24 hours** (default) to avoid extra storage costs.
3.  **S3 Lifecycle:** Set a rule to expire/delete objects after **30 days** so you don't accumulate junk files.

---

## 7. What Makes This Resume-Worthy?
1.  **"End-to-End":** You built the whole thing, from raw CSV to SQL Dashboard.
2.  **"Serverless":** You demonstrated understanding of modern, scalable cloud architecture.
3.  **"Infrastructure as Code":** You didn't click buttons; you wrote code to build cloud resources.
4.  **"Real-Time":** You handled streaming data, not just batch files.
