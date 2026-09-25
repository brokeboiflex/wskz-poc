FROM python:3.12.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /workspace
COPY services/router/requirements.txt /tmp/router.txt
COPY tests/requirements.txt /tmp/tests.txt
RUN python -m pip install --no-cache-dir -r /tmp/router.txt -r /tmp/tests.txt
COPY pyproject.toml .
COPY services ./services
COPY tests ./tests
CMD ["pytest", "-q", "-p", "no:cacheprovider"]
