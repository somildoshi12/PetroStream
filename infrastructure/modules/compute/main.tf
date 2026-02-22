# 1. AWS ECR Repository for the Lambda Image
resource "aws_ecr_repository" "lambda_repo" {
  name                 = "${var.project_name}-lambda-repo-${var.environment}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# 2. IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-exec-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# 3. IAM Policy for Lambda to access SQS, S3, and CloudWatch
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy-${var.environment}"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.raw_bucket_arn,
          "${var.raw_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = [
          var.curated_bucket_arn,
          "${var.curated_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.ingest_queue_arn
      }
    ]
  })
}

# Note: The Lambda Function resource itself should ideally be created AFTER the Docker image is pushed to ECR.
# However, Terraform will fail if we deploy the function without an image. We will instruct the user to deploy
# an initial dummy image using a bash script, and then apply terraform to create this below function.
resource "aws_lambda_function" "ml_inference_lambda" {
  function_name = "${var.project_name}-inference-${var.environment}"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda_repo.repository_url}:latest"
  
  # IMPORTANT: Since it's built on Mac M4, architecture MUST be arm64 to run
  architectures = ["arm64"]

  # Generous timeout and memory since we are loading pandas, sklearn, and model files
  timeout       = 120
  memory_size   = 1024

  environment {
    variables = {
      RAW_BUCKET_NAME     = var.raw_bucket_id
      CURATED_BUCKET_NAME = var.curated_bucket_id
    }
  }
}

# 5. SQS Event Source Mapping to Trigger the Lambda
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = var.ingest_queue_arn
  function_name    = aws_lambda_function.ml_inference_lambda.arn
  batch_size       = 10 # Process up to 10 incoming S3 uploads at a time
}

output "ecr_repository_url" {
  value = aws_ecr_repository.lambda_repo.repository_url
}

output "lambda_function_name" {
  value = aws_lambda_function.ml_inference_lambda.function_name
}
