# Lambda container image (matches aws-infrastructure §11.1 deployment contract).
FROM public.ecr.aws/lambda/python:3.12

# Runtime dependencies first (better layer caching).
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application package (src layout -> importable as `ingest_agent`).
COPY src/ingest_agent/ ${LAMBDA_TASK_ROOT}/ingest_agent/

# Single dispatcher: handles `api` (POST /ingest, GET /status) and `worker`.
CMD ["ingest_agent.handler.handler"]
