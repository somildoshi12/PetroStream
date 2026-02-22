# Amazon SQS Queue for Ingestion Events
resource "aws_sqs_queue" "ingest_queue" {
  name                      = "${var.project_name}-ingest-queue-${var.environment}"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 345600 # 4 days
  receive_wait_time_seconds = 0
  visibility_timeout_seconds= 120    # Must match or exceed Lambda timeout

  tags = {
    Environment = var.environment
  }
}

# Policy to allow S3 to send messages to this SQS Queue
resource "aws_sqs_queue_policy" "sqs_policy" {
  queue_url = aws_sqs_queue.ingest_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "sqspolicy"
    Statement = [
      {
        Sid       = "First"
        Effect    = "Allow"
        Principal = "*"
        Action    = "sqs:SendMessage"
        Resource  = aws_sqs_queue.ingest_queue.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = var.raw_bucket_arn
          }
        }
      }
    ]
  })
}

# S3 Event Notification: Trigger SQS when a new file lands in raw-data
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = var.raw_bucket_id

  queue {
    queue_arn     = aws_sqs_queue.ingest_queue.arn
    events        = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_sqs_queue_policy.sqs_policy]
}
