# Use a minimal Debian-based image
FROM debian:stable-slim

# Install essential packages, Git, Zsh, and dependencies for UV and Oh My Zsh
RUN apt-get update \
    && apt-get install -y curl git zsh \
    # && apt-get install -y curl git zsh \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# # Install Oh My Zsh
# RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

# # Set Zsh as the default shell
# RUN chsh -s /bin/zsh

# Add UV and other custom binaries to the PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Set the working directory in the container
WORKDIR /workspace

# Copy the project files into the container
COPY . /workspace
