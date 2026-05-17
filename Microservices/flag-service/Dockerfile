FROM python:3.11-slim AS builder
WORKDIR /app
COPY flag-service/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app
ENV PATH=/root/.local/bin:$PATH
COPY --from=builder /root/.local /root/.local
COPY otel ./otel
COPY flag-service/ .
EXPOSE 8002
CMD ["python", "app.py"]
