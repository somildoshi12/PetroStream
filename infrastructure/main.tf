module "s3_storage" {
  source = "./modules/storage"
  project_name = var.project_name
  environment  = var.environment
}

module "queue" {
  source           = "./modules/queue"
  project_name     = var.project_name
  environment      = var.environment
  raw_bucket_arn   = module.s3_storage.raw_bucket_arn
  raw_bucket_id    = module.s3_storage.raw_bucket_id
}

module "compute" {
  source             = "./modules/compute"
  project_name       = var.project_name
  environment        = var.environment
  raw_bucket_arn     = module.s3_storage.raw_bucket_arn
  raw_bucket_id      = module.s3_storage.raw_bucket_id
  curated_bucket_arn = module.s3_storage.curated_bucket_arn
  curated_bucket_id  = module.s3_storage.curated_bucket_id
  ingest_queue_arn   = module.queue.ingest_queue_arn
}
