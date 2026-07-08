FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    # Python
    python3 \
    python3-pip \
    # Node
    nodejs \
    npm \
    # Java
    default-jdk \
    # C / C++
    gcc \
    g++ \
    # Rust
    rustc \
    cargo \
    # Go
    golang \
    # Utilities
    git \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Python packages
RUN pip3 install pytest black requests numpy pandas

CMD ["bash"]
