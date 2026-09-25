FROM python:3.12.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY bootstrap.py .
USER 10001:10001
CMD ["python", "bootstrap.py"]
