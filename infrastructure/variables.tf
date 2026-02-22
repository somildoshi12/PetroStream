variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "The name of the project"
  type        = string
  default     = "petrostream"
}

variable "environment" {
  description = "The deployment environment (e.g., dev, prod)"
  type        = string
  default     = "dev"
}
