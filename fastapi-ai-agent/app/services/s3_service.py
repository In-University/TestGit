import boto3
from botocore.exceptions import ClientError
from app.core.config import S3_BUCKET_NAME, S3_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=S3_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )

    def upload_file(self, file_object, filename, content_type):
        """Uploads a file object to S3."""
        try:
            self.s3_client.upload_fileobj(
                file_object,
                S3_BUCKET_NAME,
                filename,
                ExtraArgs={'ContentType': content_type}
            )
            s3_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{filename}"
            return s3_url
        except ClientError as e:
            raise Exception(f"S3 upload failed: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred during S3 upload: {e}")

    def download_file(self, filename: str, local_path: str):
        try:
            self.s3_client.download_file(S3_BUCKET_NAME, filename, local_path)
            return local_path
        except ClientError as e:
            raise Exception(f"S3 download failed: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred during S3 download: {e}")
