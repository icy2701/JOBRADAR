import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import HTTPException, status
from src.config import settings
import uuid

# S3 client - boto3 is the official AWS SDK for Python
s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name="ap-south-1"
)

BUCKET_NAME = settings.AWS_BUCKET_NAME

# Only allow PDF uploads — resume must be a PDF
ALLOWED_TYPES = ["application/pdf"]
# 5MB max file size — prevents abuse
MAX_FILE_SIZE = 5 * 1024 * 1024


def upload_resume(file_bytes: bytes, filename: str,
                  content_type: str, user_id: int) -> str:
    # Validate file type — only PDFs allowed
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed for resumes"
        )

    # Validate file size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 5MB"
        )

    # Build unique S3 key (path inside the bucket)
    # Format: resumes/42/a1b2c3d4_Aisiri_Resume.pdf
    unique_id = str(uuid.uuid4())[:8]
    s3_key = f"resumes/{user_id}/{unique_id}_{filename}"

    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type,
            ACL="public-read"
        )

        # Build and return the public URL
        # Format: https://{bucket}.s3.{region}.amazonaws.com/{key}
        url = (
            f"https://{BUCKET_NAME}.s3.ap-south-1.amazonaws.com/{s3_key}"
        )
        return url

    except NoCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AWS credentials not configured"
        )
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"S3 upload failed: {str(e)}"
        )


def delete_resume(resume_url: str) -> bool:
    try:
        # Extract key from URL
        # URL format: https://bucket.s3.region.amazonaws.com/key
        prefix = f"https://{BUCKET_NAME}.s3.ap-south-1.amazonaws.com/"
        if not resume_url.startswith(prefix):
            return False

        s3_key = resume_url.replace(prefix, "")
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
        return True

    except Exception:
        return False