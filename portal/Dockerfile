# Project Atlas - CodeIgniter 3 Portal Dockerfile
FROM php:8.1-apache

# Enable Apache rewrite module
RUN a2enmod rewrite

# Install PHP extensions required by CI3 (mysqli, pdo_mysql, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcurl4-openssl-dev \
    curl \
    && docker-php-ext-install mysqli pdo_mysql curl \
    && rm -rf /var/lib/apt/lists/*

# Configure Apache DocumentRoot to /var/www/html
WORKDIR /var/www/html

# Copy portal source code
COPY portal/ /var/www/html/

# Ensure Apache file permissions
RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

CMD ["apache2-foreground"]
