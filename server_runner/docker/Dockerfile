# ==========================================
# CODEVIEW DEVELOPER ENVIRONMENT
# ==========================================

# Start with an official Go image based on Debian.
FROM golang:1.24-bookworm

# Install Python, Node.js, npm, Git, and Linux tools.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        nodejs \
        npm \
        git \
        bash \
        curl \
        ca-certificates \
        coreutils \
        procps \
        nano \
        && rm -rf /var/lib/apt/lists/*

# Create a regular Linux user for the developer.
RUN useradd \
    --create-home \
    --shell /bin/bash \
    --uid 10001 \
    developer

# Create the developer's workspace directory.
RUN mkdir -p /workspace && \
    chown developer:developer /workspace

# ==========================================
# PREPARE GO BUILD CACHE
# ==========================================

# Store precompiled Go dependencies in the image.
# This location remains readable when the container
# runs with a read-only filesystem.
ENV GOCACHE=/opt/codeview/go-cache

# Create the cache directory.
RUN mkdir -p /opt/codeview/go-cache && \
    chown -R developer:developer /opt/codeview/go-cache

# Switch to the unprivileged developer.
USER developer

# Compile a small Go program during image creation.
# This warms Go's build cache, including packages
# commonly required by simple Go programs.
RUN mkdir -p /tmp/codeview-go-warmup && \
    printf 'package main\nimport "fmt"\nfunc main() { fmt.Println("ready") }\n' \
        > /tmp/codeview-go-warmup/main.go && \
    cd /tmp/codeview-go-warmup && \
    go build -o /tmp/codeview-go-warmup/app main.go && \
    rm -rf /tmp/codeview-go-warmup

# Set the default working directory.
WORKDIR /workspace

# Start Bash when the container launches.
CMD ["/bin/bash"]