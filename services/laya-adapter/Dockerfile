FROM python:3.12.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY laya_adapter ./laya_adapter
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "laya_adapter.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
