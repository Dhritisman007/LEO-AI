FROM python:3.11-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    git \
    curl \
    nodejs \
    npm \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pytest black requests

CMD ["bash"]
