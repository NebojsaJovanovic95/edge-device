from __future__ import annotations
from pathlib import Path
from typing import BinaryIO
import shutil
import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from io import BytesIO
from src.util import logger
from src.config import settings

class ImageStorage:
    """
    Handles saving, loading, and deleting image files.
    """
    def __init__(
        self,
        base_dir: str,
        use_minio: bool,
        minio_endpoint: str = "",
        minio_access_key: str = "",
        minio_secret_key: str = "",
        minio_bucket: str = "",
    ) -> None:
        self.base_dir: Path = Path(base_dir)
        self.use_minio = use_minio

        if self.use_minio:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=minio_endpoint,
                aws_access_key_id=minio_access_key,
                aws_secret_access_key=minio_secret_key,
                region_name='us-east-1'
            )
            self.bucket_name = minio_bucket
            self._ensure_bucket_exists()
        else:
            self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _ensure_bucket_exists(self) -> None:
        """Create the bucket if it doesnt exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(F"[{self.NAME}]: Bucket '{self.bucket_name}' exists")
        except ClientError as e:
            if e.response["Error"]["Code"] in ('404', 'NoSuchBucket'):
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"[{self.NAME}]: Created bucket '{self.bucket_name}'")
            else:
                logger.error(f"[{self.NAME}]: Error checking buckets: {e}")

    def save_image(
        self,
        file_obj: BinaryIO,
        filename: str
    ) -> Path:
        """Save an uploaded image file to disk"""
        if self.use_minio:
            try:
                file_obj.seek(0)
                self.s3_client.upload_fileobj(
                    file_obj,
                    self.bucket_name,
                    filename
                )
                logger.info(f"[{self.NAME}]: Uploaded {filename} to MinIO bucket {self.bucket_name}")
            except NoCredentialError:
                logger.error(f"[{self.NAME}]: Credentials not available for MinIO")
            except Exception as e:
                logger.error(f"[{self.NAME}]: Error uploading image to MinIO: {e}")
            finally:
                return filename
        else:
            save_path: Path = self.base_dir / filename
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as out_file:
                shutil.copyfileobj(file_obj, out_file)
            return str(save_path.relative_to(self.base_dir))
    
    def load_image(self, image_path: str) -> BinaryIO:
        """Load an image file from disk for streaming."""
        if self.use_minio:
            try:
                response = self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=image_path
                )
                return BytesIO(response['Body'].read())
            except self.s3_client.exceptions.NoSuchKey:
                logger.error(f"[{self.NAME}]: Image not found in MinIO: {image_path}")
                return BytesIO()
            except Exception as e:
                logger.error(f"[{self.NAME}]: Error laoding image from MinIO: {e}")
                return BytesIO()
        else:
            path = self.base_dir / image_path
            if not path.exists():
                logger.error(
                    f"[{self.NAME}]: Image not found: {image_path}"
                )
            return open(path, "rb")
    
    def delete_image(self, image_path: str) -> None:
        """Delete an image file from local storage or MinIO."""
        if self.use_minio:
            try:
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=image_path
                )
                logger.info(f"[{self.NAME}]: Deleted {image_path} from MinIO bucket {self.bucket_name}")
            except Exception as e:
                logger.error(f"[{self.NAME}]: Error deleting image from MinIO: {e}")
        else:
            try:
                os.remove(image_path)
            except FileNotFoundError:
                logger.error(f"[{self.NAME}]: File not found")


minio_storage: ImageStorage = ImageStorage(
    base_dir=settings.IMAGE_DIR,
    use_minio=settings.USE_MINIO,
    minio_endpoint=settings.MINIO_ENDPOINT,
    minio_access_key=settings.MINIO_ROOT_USER,
    minio_secret_key=settings.MINIO_ROOT_PASSWORD,
    minio_bucket=settings.MINIO_BUCKET
)

local_storage: ImageStorage = ImageStorage(
    base_dir=settings.IMAGE_DIR,
    use_minio=False
)
