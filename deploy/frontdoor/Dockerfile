# Registry host supplied via --build-arg REGISTRY_HOST=<your-cr-host>.
ARG REGISTRY_HOST
FROM ${REGISTRY_HOST}/agentkit/agentkit-wizard:0.21.3
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /frontdoor
COPY app.py /frontdoor/app.py
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=3s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
