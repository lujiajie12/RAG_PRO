from __future__ import annotations

from minio import Minio


class ObjectStorage:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool) -> None:
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    def ensure_bucket(self, bucket_name: str) -> None:
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
