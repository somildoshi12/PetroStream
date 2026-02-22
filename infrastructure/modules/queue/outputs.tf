output "ingest_queue_url" {
  value = aws_sqs_queue.ingest_queue.url
}

output "ingest_queue_arn" {
  value = aws_sqs_queue.ingest_queue.arn
}
