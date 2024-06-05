# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Install necessary packages including Git, Zsh, and dependencies for Oh My Zsh
RUN apt-get update \
    && apt-get install -y curl git zsh \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Oh My Zsh
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

# Set Zsh as the default shell
RUN chsh -s /bin/zsh

# Add Poetry to the PATH
ENV PATH="/root/.local/bin:$PATH"

# Set the working directory in the container
WORKDIR /workspace

# Copy the project files into the container
COPY . /workspace
