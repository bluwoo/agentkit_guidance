FROM python:3.12-slim
WORKDIR /app
COPY server.py .
RUN pip install --no-cache-dir veadk-python==1.1.13 agentkit-sdk-python==0.8.7 uvicorn aiosqlite
EXPOSE 8000
CMD ["python", "server.py"]
