FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY safety_core.py /app/safety_core.py
COPY app.py /app/app.py
ENV CONFORMAL_ALPHA=0.10
ENV TAU=0.55
ENV CAL_WINDOW=400
ENV ROLLOUT_STEPS=5,25,50,100
ENV SLO_MAX_P95=35
ENV C_FN=4.0
ENV C_FP=6.0
ENV LAMBDA=0.5
ENV SLO_BUDGET_DELTA=0.5
ENV LOG_DIR=/app/outputs
ENV TRACE_PATH=/app/outputs/optimization_trace.jsonl
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
