# Lambda container image (matches aws-infrastructure §11.1 deployment contract).
FROM public.ecr.aws/lambda/python:3.12

# Runtime dependencies first (better layer caching).
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application package (src layout -> importable as `analyze_agent`).
COPY src/analyze_agent/ ${LAMBDA_TASK_ROOT}/analyze_agent/

# Single synchronous dispatcher: POST /analyze.
CMD ["analyze_agent.handler.handler"]
