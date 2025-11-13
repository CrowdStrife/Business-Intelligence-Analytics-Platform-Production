"""
MinIO storage service for uploading files and creating markers.
"""
import io
import logging
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile
from app.core.config import settings

# Setup logging
log = logging.getLogger(__name__)

# Initialize MinIO client
minio_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access,
    secret_key=settings.minio_secret,
    secure=settings.minio_secure
)


def ensure_bucket_exists(bucket_name: str):
    """
    Ensures the specified MinIO bucket exists. Creates it if it doesn't.
    """
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            log.info(f"Created MinIO bucket: {bucket_name}")
        else:
            log.debug(f"MinIO bucket '{bucket_name}' already exists.")
    except S3Error as e:
        log.error(f"Error ensuring bucket exists: {e}")
        raise


async def upload_file_to_minio(
    file: UploadFile, 
    filename: str, 
    folder: str
) -> int:
    """
    Uploads a file to MinIO in the specified folder within the landing bucket.
    
    Args:
        file: FastAPI UploadFile object
        filename: Name of the file to upload
        folder: Target folder within the bucket (e.g., 'raw_sales_by_transaction')
    
    Returns:
        int: Size of the uploaded file in bytes
    
    Raises:
        Exception: If upload fails
    """
    try:
        # Ensure the landing bucket exists
        ensure_bucket_exists(settings.minio_landing_bucket)
        
        # Read file content
        contents = await file.read()
        file_size = len(contents)
        
        # Create object path (folder/filename)
        object_name = f"{folder}/{filename}"
        
        # Upload to MinIO
        minio_client.put_object(
            bucket_name=settings.minio_landing_bucket,
            object_name=object_name,
            data=io.BytesIO(contents),
            length=file_size,
            content_type=file.content_type or "application/octet-stream"
        )
        
        log.info(f"Uploaded {filename} to MinIO: {settings.minio_landing_bucket}/{object_name}")
        return file_size
        
    except S3Error as e:
        log.error(f"MinIO S3Error uploading {filename}: {e}")
        raise Exception(f"Failed to upload {filename} to MinIO: {str(e)}")
    except Exception as e:
        log.error(f"Unexpected error uploading {filename}: {e}")
        raise


async def create_complete_marker():
    """
    Creates a '_complete' marker file in the landing bucket to signal
    that a batch of files has been fully uploaded.
    """
    try:
        # Ensure the landing bucket exists
        ensure_bucket_exists(settings.minio_landing_bucket)
        
        # Create marker file
        marker_content = b"complete"
        marker_name = "_complete"
        
        minio_client.put_object(
            bucket_name=settings.minio_landing_bucket,
            object_name=marker_name,
            data=io.BytesIO(marker_content),
            length=len(marker_content),
            content_type="text/plain"
        )
        
        log.info(f"Created completion marker in MinIO: {settings.minio_landing_bucket}/{marker_name}")
        
    except S3Error as e:
        log.error(f"MinIO S3Error creating marker: {e}")
        raise Exception(f"Failed to create completion marker: {str(e)}")
    except Exception as e:
        log.error(f"Unexpected error creating marker: {e}")
        raise

