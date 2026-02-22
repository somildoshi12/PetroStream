output "ingest_queue_url" {
  value = module.queue.ingest_queue_url
}
output "ecr_repository_url" {
  value = module.compute.ecr_repository_url
}
