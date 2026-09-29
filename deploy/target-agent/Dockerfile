# Registry host supplied via --build-arg REGISTRY_HOST=<your-cr-host>.
ARG REGISTRY_HOST
FROM ${REGISTRY_HOST}/agentkit/agentkit-wizard:0.21.3
ENV PYTHONUNBUFFERED=1
WORKDIR /target-agent
RUN pip install --no-cache-dir \
    agentkit-sdk-python==0.8.7 \
    veadk-python==1.1.13 \
    opentelemetry-exporter-otlp-proto-grpc==1.37.0
RUN pip check
COPY app.py /target-agent/app.py
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=3s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
