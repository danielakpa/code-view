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

# Run as a non-root user.
USER developer

# Set the default working directory.
WORKDIR /workspace

# Start Bash when the container launches.
CMD ["/bin/bash"]