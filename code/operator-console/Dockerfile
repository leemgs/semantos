# Operator Console: FastAPI
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
# Copy outputs as a volume mount location; at runtime, docker-compose will mount ./outputs:/app/outputs
EXPOSE 9988
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9988"]
