FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 系统依赖（编译 pg/psycopg 等）
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制后端与数据（保持目录结构）
WORKDIR /app
COPY backend/ /app/backend
COPY data/ /app/data

# 安装后端依赖
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

# 让 Python 能按包路径 import（/app 在 sys.path）
ENV PYTHONPATH=/app

# 以包路径启动（backend 就是包名）
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
