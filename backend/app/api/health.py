from __future__ import annotations

from flask import Blueprint, current_app
from minio import Minio
import psycopg2
health_bp = Blueprint("health", __name__, url_prefix="/api/health")


@health_bp.get("")
def healthcheck() -> dict[str, object]:
    services = {}
    #在这里需要加数据库、MinIO等服务的健康检查
    #检查MinIO服务
    
    #API
    services["api"] = "ok"
    #MinIO对象存储
    try:
        minio_client = Minio(
            current_app.config["MINIO_ENDPOINT"],
            access_key=current_app.config["MINIO_ACCESS_KEY"],
            secret_key=current_app.config["MINIO_SECRET_KEY"],
            secure=current_app.config["MINIO_USE_SSL"],
        )
        minio_client.list_buckets()  # 尝试列出桶以检查连接
        services["minio"] = "ok"
    except Exception as e:
       return {
            "status": "error",
            "error": str(e)
        }

    # PostgreSQL
    try:
        conn = psycopg2.connect(
            host = current_app.config["POSTGRES_HOST"],
            port = current_app.config["POSTGRES_PORT"],
            database = current_app.config["POSTGRES_DB"],
            user = current_app.config["POSTGRES_USER"],
            password = current_app.config["POSTGRES_PASSWORD"]
        )
        conn.close()
        services["postgresql"] = "ok"
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
    # LLM
    try:
        import requests
        reponse = requests.post(
            current_app.config["OPENAI_BASE_URL"],
            headers={
                "Authorization": f"Bearer {current_app.config['OPENAI_API_KEY']}",
                "Content-Type": "application/json"
            },
            json={
                "model": current_app.config["CHAT_MODEL"],
                "messages": [{"role": "user", "content": "Hello, how are you?"}]
            }
        )
        if reponse.status_code == 200:
            services["llm"] = "ok"
        else:
            services["llm"] = f"error: {reponse.status_code}"
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
    return {
        "service": current_app.config["APP_NAME"],
        "status": "ok",
        "env": "development" if current_app.config["DEBUG"] else "production",
    }
