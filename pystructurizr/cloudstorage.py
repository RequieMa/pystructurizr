from abc import ABC, abstractmethod
from enum import Enum
import boto3
import json
from typing import Dict


class CloudStorage(ABC):
    class Provider(Enum):
        GCS = "GCS"
        S3 = "S3"

    @abstractmethod
    def upload_file(self, file_path: str, bucket_name: str, object_name: str) -> str:
        pass
 

class GCS(CloudStorage):
    def __init__(self, gcs_credentials):
        self.gcs_credentials = gcs_credentials

    def upload_file(self, file_path: str, bucket_name: str, object_name: str) -> str:
        from google.cloud import storage
        gcs_client = storage.Client.from_service_account_json(self.gcs_credentials)
        gcs_bucket = gcs_client.get_bucket(bucket_name)
        gcs_blob = gcs_bucket.blob(object_name)
        gcs_blob.upload_from_filename(file_path)
        return f"https://storage.googleapis.com/{bucket_name}/{object_name}"


class S3(CloudStorage):
    def __init__(self, credentials_file: str):
        self.credentials = self._load_credentials(credentials_file)
        self.client = boto3.client(
            "s3",
            aws_access_key_id=self.credentials["access_key"],
            aws_secret_access_key=self.credentials["secret_key"],
            region_name=self.credentials["region"]
        )
    
    def _load_credentials(self, credentials_file: str) -> Dict[str, str]:
        with open(credentials_file, "r") as f:
            credentials = json.load(f)
        required_keys = ["access_key", "secret_key", "region"]
        if not all(key in credentials for key in required_keys):
            raise ValueError("Invalid credentials format")
        return credentials

    def upload_file(self, file_path: str, bucket_name: str, object_name: str) -> str:
        self.client.upload_file(file_path, bucket_name, object_name)
        url = f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
        return url


def create_cloud_storage(provider: CloudStorage.Provider, credentials_file: str) -> CloudStorage:
    if provider == CloudStorage.Provider.GCS:
        return GCS(credentials_file)
    elif provider == CloudStorage.Provider.S3:
        return S3(credentials_file)
    else:
        raise ValueError("Invalid cloud storage provider")
