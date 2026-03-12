from __future__ import annotations

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

#extensions.py 负责初始化 db、migrate 和 cors 这三个 Flask 扩展，并提供一个 init_extensions 函数来绑定它们到 Flask app 上。
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
cors = CORS()


def init_extensions(app: Flask) -> None:
    #这一步是把 Flask app 和数据库扩展绑定起来。
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )
