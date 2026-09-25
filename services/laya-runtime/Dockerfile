FROM python:3.12.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HOME=/models
WORKDIR /app
# CPU wheels avoid bringing NVIDIA toolchains/libraries into a CPU PoC image.
RUN python -m pip install --no-cache-dir torch==2.10.0 --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt && mkdir /models && chown 10001:10001 /models
COPY runtime.py .
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "runtime:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
