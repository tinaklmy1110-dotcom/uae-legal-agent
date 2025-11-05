FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安装构建 pg/psycopg 所需的系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制后端源码与数据目录
COPY backend/ /app/backend
COPY data/ /app/data

WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app:/app/backend

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
