FROM ubuntu:22.04

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    python3.12 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Установка uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvbin/uv
ENV PATH="/uvbin:${PATH}"

# Установка nFPM
RUN curl -L https://github.com/goreleaser/nfpm/releases/download/v2.35.3/nfpm_2.35.3_Linux_x86_64.tar.gz | tar -xz \
    && mv nfpm /usr/local/bin/

WORKDIR /app
COPY . .

# Сборка будет запускаться через entrypoint или напрямую в CI
CMD ["bash"]
