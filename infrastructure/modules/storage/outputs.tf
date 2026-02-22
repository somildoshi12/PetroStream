output "raw_bucket_arn" {
  value = aws_s3_bucket.raw_data.arn
}

output "curated_bucket_arn" {
  value = aws_s3_bucket.curated_data.arn
}

output "athena_results_bucket_arn" {
  value = aws_s3_bucket.athena_results.arn
}
output "raw_bucket_id" {
  value = aws_s3_bucket.raw_data.id
}
output "curated_bucket_id" {
  value = aws_s3_bucket.curated_data.id
}
