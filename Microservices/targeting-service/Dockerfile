FROM python:3.11-slim AS builder
WORKDIR /app
COPY targeting-service/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app
ENV PATH=/root/.local/bin:$PATH
COPY --from=builder /root/.local /root/.local
COPY otel ./otel
COPY targeting-service/ .
EXPOSE 8003
CMD ["python", "app.py"]
