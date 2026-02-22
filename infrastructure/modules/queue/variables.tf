variable "project_name" {}
variable "environment" {}
variable "raw_bucket_arn" {
  description = "ARN of the raw data bucket"
  type        = string
}

variable "raw_bucket_id" {
  description = "ID of the raw data bucket"
  type        = string
}
