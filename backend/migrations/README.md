# Alembic Migrations

该目录预留给 Alembic 迁移脚本。

建议初始化方式：

```bash
cd backend
flask --app run.py db init
flask --app run.py db migrate -m "init schema"
flask --app run.py db upgrade
```
