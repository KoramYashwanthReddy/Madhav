#!/bin/sh
# MinIO Client Bucket Initialization Script
set -e

echo "Waiting for MinIO server to start..."
until curl -s http://minio:9000/minio/health/ready; do
    sleep 2
done

echo "MinIO server is ready. Initializing storage buckets..."

mc alias set maxminio http://minio:9000 ${MINIO_ROOT_USER:-minioadmin} ${MINIO_ROOT_PASSWORD:-minioadmin}

# Create required private object buckets
mc mb --ignore-existing maxminio/max-artifacts
mc mb --ignore-existing maxminio/max-documents
mc mb --ignore-existing maxminio/max-backups

# Enforce private policy on all buckets
mc anonymous set private maxminio/max-artifacts
mc anonymous set private maxminio/max-documents
mc anonymous set private maxminio/max-backups

echo "MinIO buckets initialized successfully."
