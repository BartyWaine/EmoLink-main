FROM php:8.2-cli

RUN apt-get update && apt-get install -y \
    libzip-dev \
    unzip \
    && docker-php-ext-install pdo pdo_mysql zip

WORKDIR /app

# Copy all files
COPY . .

# Ensure public directory exists and has index
RUN if [ ! -d "public" ]; then mkdir public; fi

# Expose Railway's port
ENV PORT=8080
EXPOSE 8080

# Start PHP built-in server serving from public directory
CMD ["php", "-S", "0.0.0.0:${PORT:-8080}", "-t", "public"]
