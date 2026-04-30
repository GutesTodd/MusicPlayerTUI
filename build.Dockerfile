FROM alpine:latest

# Установка системных зависимостей
RUN apk add --no-cache \
    curl \
    python3 \
    py3-pip \
    git \
    bash \
    tar

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
