FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV ANALYSIS_ENGINE_PORT=8090
EXPOSE 8090
CMD ["sh", "-c", "python -m analysis_engine.app.api"]