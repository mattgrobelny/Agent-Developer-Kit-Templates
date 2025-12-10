docker build -t mlflow-server:3.7.0 --build-arg MLFLOW_VERSION=3.7.0 -f Dockerfile.mlflow .


docker run -d \
    --name mlflow-tracing-server \
    -p 5000:5000 \
    -v $(pwd)/mlflow_data:/app \
    mlflow-server:3.7.0