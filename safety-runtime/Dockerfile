FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY app.py /app/app.py
ENV TAU=0.55
ENV ROLLOUT_STEPS=5,25,50,100
ENV SLO_MAX_P95=35
ENV LOG_DIR=/app/outputs
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
