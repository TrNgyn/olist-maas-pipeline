provider "aws" {
  region = "us-east-1"
}

# Unique identifier for global bucket naming
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Landing Zone: The "Bronze" layer for raw data ingestion
resource "aws_s3_bucket" "olist_landing" {
  bucket = "olist-maas-landing-${random_id.bucket_suffix.hex}"
}

# Security: Prevent public access to the Landing Zone
resource "aws_s3_bucket_public_access_block" "landing_security" {
  bucket                  = aws_s3_bucket.olist_landing.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Ingestion Folders: Partitioning data by business domain
resource "aws_s3_object" "sales_folder" {
  bucket = aws_s3_bucket.olist_landing.id
  key    = "raw/sales/"
}

resource "aws_s3_object" "marketing_folder" {
  bucket = aws_s3_bucket.olist_landing.id
  key    = "raw/marketing/"
}

resource "aws_s3_object" "testing_folder" {
  bucket = aws_s3_bucket.olist_landing.id
  key    = "raw/testing/"
}

# The bucket name needed for data syncing
output "landing_bucket_name" {
  value = aws_s3_bucket.olist_landing.bucket
}