variable "project_name" {}
variable "environment" {}

resource "aws_s3_bucket" "raw_data" {
  bucket = "${var.project_name}-raw-data-${var.environment}-${random_id.bucket_suffix.hex}"
  force_destroy = true 

  tags = {
    Name        = "Raw Data Bucket"
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "curated_data" {
  bucket = "${var.project_name}-curated-data-${var.environment}-${random_id.bucket_suffix.hex}"
  force_destroy = true

  tags = {
    Name        = "Curated Data Bucket"
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "athena_results" {
  bucket = "${var.project_name}-athena-results-${var.environment}-${random_id.bucket_suffix.hex}"
  force_destroy = true

  tags = {
    Name        = "Athena Results Bucket"
    Environment = var.environment
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}
