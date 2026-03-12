from __future__ import annotations

from io import BytesIO

from minio import Minio


class ObjectStorage:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool) -> None:
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    def ensure_bucket(self, bucket_name: str) -> None:
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    def upload_bytes(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        self.ensure_bucket(bucket_name)
        self.client.put_object(
            bucket_name,
            object_name,
            BytesIO(data),
            len(data),
            content_type=content_type,
        )

    def download_bytes(self, bucket_name: str, object_name: str) -> bytes:
        response = self.client.get_object(bucket_name, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete_object(self, bucket_name: str, object_name: str) -> None:
        self.client.remove_object(bucket_name, object_name)
