# Use a minimal Debian-based image
FROM debian:stable-slim

# Install essential packages, Git, Bash, and dependencies for UV
RUN apt-get update \
    && apt-get install -y curl git bash \
    && curl -LsSf https://astral.sh/uv/install.sh | bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add UV and other custom binaries to the PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Set the working directory in the container
WORKDIR /workspace

# Copy the project files into the container
COPY . /workspace
