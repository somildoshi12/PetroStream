# PetroStream - AWS Cloud Setup & Learning Log

This document serves as a comprehensive log of the steps taken to set up the cloud infrastructure for the PetroStream data pipeline. It is designed for learning purposes and future reference.

## 1. Environment Setup

### 1.1 Installed Tools

On macOS (M4), we installed the following command-line tools using Homebrew:

1.  **Terraform**: Create and manage infrastructure as code.
    ```bash
    brew install hashicorp/tap/terraform
    ```
2.  **AWS CLI**: Interact with AWS services from the terminal.
    ```bash
    brew install awscli
    ```

### 1.2 How to Get AWS Credentials (AWS Console Steps)

To configure the AWS CLI, you need an **Access Key ID** and a **Secret Access Key**. These are generated from the AWS Management Console.

1.  **Log in to the AWS Console**:
    - Go to [https://aws.amazon.com/console/](https://aws.amazon.com/console/) and sign in.

2.  **Navigate to IAM (Identity and Access Management)**:
    - In the top search bar, type `IAM` and select the service.

3.  **Create or Select a User**:
    - Click on **"Users"** in the left sidebar.
    - **Option A (New User)**: Click **"Create user"**. give it a name like `petrostream-admin`.
      - Attach policies directly -> search for and select **`AdministratorAccess`**. (This is easiest for a solo project; for production, you'd want tighter permissions).
    - **Option B (Existing User)**: Click on your existing username (make sure it has permissions like `AdministratorAccess` or at least access to S3, Kinesis, Glue, Athena, ECS, ECR, and IAM).

4.  **Create Access Keys**:
    - Click on the **"Security credentials"** tab for that user.
    - Scroll down to the **"Access keys"** section.
    - Click **"Create access key"**.
    - Select **"Command Line Interface (CLI)"**.
    - Check the confirmation box and click **"Next"**.
    - (Optional) Add a description tag like "MacBook Pro".
    - Click **"Create access key"**.

5.  **Copy the Keys**:
    - **Access key ID**: Copy this string (starts with `AKIA...`).
    - **Secret access key**: Copy this string (starts with a mix of characters). **Click "Show"** to see it.
    - _Important_: Download the `.csv` file or copy these now. You cannot see the Secret Key again after you leave this page.

### 1.3 AWS Configuration

After installing the AWS CLI, we configured it to connect to your AWS account.

**Command:**

```bash
aws configure
```

**What this does:**

- It asks for your **Access Key ID** and **Secret Access Key** (your "username" and "password" for the API).
- It sets your default **Region** (e.g., `us-east-1` for N. Virginia).
- It sets the output format to `json` (easier for scripts to read).

**Files Created:**

- `~/.aws/credentials`: Stores your keys securely.
- `~/.aws/config`: Stores your region and output preferences.

### 1.4 Verification

We verified the configuration by running:

```bash
aws sts get-caller-identity
```

**Output**:

- User: `petrostream-admin`
- Account: `439500389620`
- ARN: `arn:aws:iam::439500389620:user/petrostream-admin`

This confirms our local terminal is successfully authenticated to your AWS account.

## 2. Infrastructure as Code (Terraform) Concepts

We are using **Terraform** to build our "Phase 1" infrastructure.

- **Provider**: A plugin that tells Terraform which cloud to use (e.g., AWS, Azure, Google). We use the `aws` provider.
- **Resource**: A specific piece of infrastructure (e.g., an S3 bucket, a Kinesis stream).
- **State File**: A file (`terraform.tfstate`) that Terraform uses to remember what it has already built. **Never delete this file!**

## 3. Implementation Steps (Log)

### Phase 1: Infrastructure Setup

**Goal**: Create the "plumbing" for our data: storage (S3), streaming (Kinesis), and permissions (IAM).

#### Step 3.1: Project Directory Structure

We created a modular directory structure to keep our code clean:

```
infrastructure/
├── main.tf             # The "control center" connecting everything
├── providers.tf        # Configures AWS connection
├── variables.tf        # Defines project-wide settings (name, region)
└── modules/
    └── storage/
        └── main.tf     # Defines the actual S3 buckets
```

**Why Modules?**: Using modules allows us to group related resources (like "storage") together. If we want to add more buckets later, we just edit the storage module without touching the rest of the code.

#### Step 3.2: Terraform Commands Execution

1.  **Initialize**: We ran `terraform init` inside the `infrastructure` folder. This downloaded the AWS plugin needed to talk to the cloud.
2.  **Plan**: We ran `terraform plan` to double-check what would be built. It showed us 4 resources to add (3 buckets + 1 random ID).
3.  **Apply**: We ran `terraform apply` to create the resources.

**Outcome**:
Successfully created 3 S3 buckets in `us-east-1` with a unique suffix (`84f59e73`):

- `petrostream-raw-data-dev-84f59e73`
- `petrostream-curated-data-dev-84f59e73`
- `petrostream-athena-results-dev-84f59e73`

---

## 4. Troubleshooting & Notes

- **Exit Code 127**: This means "command not found". It happened when we tried to run `terraform` before installing it.
- **AWS CLI Version**: We are using version 2.x, which is the current standard.

---

### Step 3.3: Rethinking the Architecture (Removing Kinesis)

Due to AWS Academy/Student account restrictions, **Kinesis Data Streams** and **Kinesis Firehose** were unavailable. We pivoted to a more cost-effective and universally permitted architecture:

1.  **Direct S3 Uploads**: Instead of streaming one record at a time to Kinesis, our producer will batch data locally and upload the batches directly to the `raw-data` S3 bucket.
2.  **Amazon SQS**: We created a Simple Queue Service (SQS) queue named `petrostream-ingest-queue`.
3.  **S3 Event Notifications**: We configured the `raw-data` S3 bucket to automatically send a message to the SQS queue whenever a new file (`s3:ObjectCreated:*`) lands in it.

**Why this is better for learning and budget:**

- **Cost**: Eliminating Kinesis Data Streams removes hourly baseline costs. SQS is virtually free ($0.40 per 1 million requests), keeping us well under the $120 student budget.
- **Simplicity**: Batching is handled simply by the producer script, relying on event-driven architecture (S3 -> SQS -> ECS/Lambda).

We modified our Terraform code to delete the `streaming` module and create a `queue` module. After running `terraform apply`, SQS and S3 Event Notifications were successfully provisioned!

---

### Phase 2: Local ML Training

**Goal**: Extract operational features from the Petrobras dataset, train an Unsupervised Machine Learning model locally, and save it to the cloud for inference.

#### Step 4.1: ML Environment Setup

We created a `ml/` directory and initialized a `requirements.txt` file with essential data science libraries: `pandas`, `scikit-learn`, `fastparquet`, `boto3`, and `joblib`. These were installed locally on the Mac M4.

#### Step 4.2: Data Extraction & Preprocessing

We wrote `ml/train_model.py`. The script:

1. Searches the `Petrobras Data/` directory for `SIMULATED_*.parquet` files.
2. Loads a subset (the first 5 files) into a Pandas DataFrame to ensure lightning-fast training locally on the M4 chip.
3. Extracts exactly 5 focal features for anomaly detection:
   - `P-PDG` (Bottom-hole pressure)
   - `P-TPT` (Pressure at the Transducer)
   - `T-TPT` (Temperature at the Transducer)
   - `P-MON-CKP` (Pressure upstream of choke)
   - `T-JUS-CKP` (Temperature downstream of choke)
4. Cleans the data by dropping empty records (NaNs).

#### Step 4.3: Training the Isolation Forest

Since anomalies in oil & gas wells are rare, we used an **Isolation Forest**, an algorithm excellent at identifying outliers in multidimensional space.

- We set `contamination=0.01` (assuming ~1% of the data points represent anomalies).
- We set `n_jobs=-1` to utilize all available CPU cores on the Mac for instant training.

#### Step 4.4: Exporting the Model

The trained model was serialized using `joblib` into a file named `model.joblib`.
Finally, we used the AWS CLI to upload this asset directly to our newly created raw-data S3 bucket:

This model is now staged in the cloud. In the next phase, the live processing container will download this exact file to evaluate incoming data streams!

---

### Phase 3: Stream Processing via AWS Lambda

**Goal**: Create an event-driven compute layer in the cloud to process data hitting SQS, run inference using our trained model, and label the results into a final bucket.

#### Step 5.1: Pivoting from ECS to AWS Lambda

To maximize cost efficiency and simplify deployment tracking, we shifted our Phase 3 architecture from ECS Fargate (which incurs baseline container costs) to **AWS Lambda** (serverless, executing only when messages are in the SQS queue—virtually free at this scale).

#### Step 5.2: Writing the Inference Logic

We created `lambda/app.py`. The Python script implements a handler that:

1. Validates the event comes from SQS.
2. Identifies the `s3:ObjectCreated` event nested inside.
3. Caches the downloaded `model.joblib` to prevent redownloading it on warm starts.
4. Uses pandas to load the new Parquet data, drops invalid NaN records, and extracts our 5 features.
5. Invokes `model.predict()` to calculate outliers.
6. Maps the output array (-1 for outliers, 1 for inliers) into a clear database format: `anomaly_flag` (1 for true, 0 for false).
7. Writes the resulting dataframe to the `curated-data` S3 bucket in exactly the same partition structure as it was received.

#### Step 5.3: Containerizing Lambda (Addressing Size Limits)

AWS Lambda has a strict 250MB unzipped limit on deployments. Since `pandas` and `scikit-learn` are massive, we utilized Lambda's **Docker Image Support** (up to 10GB).

- Created a `Dockerfile` originating from `public.ecr.aws/lambda/python:3.12`.
- Since development is occurring on an M4 Mac, we explicitly built the target for `arm64` using `docker build --platform linux/arm64 -t ...`.

#### Step 5.4: Infrastructure Updates

We expanded Terraform by introducing a `compute` module. This module coordinates:

1. **AWS ECR Repository (`petrostream-lambda-repo-dev`)**: The container registry storing our `arm64` Docker image.
2. **IAM Roles & Policies**: We attached precise least-privilege permissions enabling Lambda to read from the Raw Bucket, write to the Curated Bucket, consume from SQS, and output CloudWatch Logs.
3. **AWS Lambda Function (`petrostream-inference-dev`)**: Bound to our ECR image and supplied with memory (1024MB) and timeout settings (120s) suitable for ML processing.
4. **Event Source Mapping**: Wired the SQS ingest queue to trigger this Lambda function, pulling batches of up to 10 files at a time.

We authorized Docker to communicate with AWS Elastic Container Registry, pushed the compiled image, and then ran `terraform apply` to materialize the pipeline. The entire streaming pipeline is now fully online.

---

### Phase 4: Frontend (Streamlit Dashboard)

**Goal**: Build a real-time visualization layer to monitor sensor data and detected anomalies by reading the output directly from the Curated S3 Bucket.

#### Step 6.1: Environment and Dependencies

We initialized a `dashboard/` directory and created a `requirements.txt` file including `streamlit`, `pandas`, `altair` (for interactive charting), `boto3`, and `awswrangler` (AWS Data Wrangler). We used constraints that matched exactly what we deployed in lambda to ensure consistency (e.g. `pandas==2.2.3`).

#### Step 6.2: Bypassing Athena for Real-Time Speed

Originally, we planned to query Athena to power the dashboard. However, since the lambda directly partitions the `model_output` into the Curated S3 Bucket in a well structured Parquet format, we opted to use `awswrangler.s3.read_parquet()`. This dramatically speeds up dashboard loads by directly reading the datasets from S3 into Pandas DataFrames, avoiding Athena's query execution time latency for real-time reads!

#### Step 6.3: Building the Streamlit Application (`app.py`)

We created the dashboard with the following features:

1. **Dynamic Configuration**: Resolves the target `CURATED_BUCKET_NAME` straight from the environment variables.
2. **Key Metric Indicators**: High-level KPIs showing total records processed, total anomalies detected, and an anomaly percentage rate using `st.metric`.
3. **Interactive Time-Series Charts**: We used Altair to overlay the `P-PDG` (Bottom-hole pressure) and `P-TPT` (Pressure at Transducer) lines. Crucially, we plotted bright red scatter-plot indicators EXACTLY where the `anomaly_flag == 1` so operators can instantly identify pressure spikes visually.
4. **Data Grid**: Included an `st.dataframe` to expose the raw sensor readings for the detected anomalies.

#### Step 6.4: Running Locally

We executed this locally using:

```bash
streamlit run dashboard/app.py --server.port=8502
```

This is fully running in the background and exposed. The real-time loop is completed: whenever files hit the "Raw S3 Bucket", Lambda scores them, writes them to the "Curated S3 Bucket", and hitting "Refresh" on the Streamlit dashboard immediately shows the new data and plotted anomalies!
