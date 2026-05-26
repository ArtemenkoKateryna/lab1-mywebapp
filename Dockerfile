FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY mywebapp ./mywebapp
COPY scripts ./scripts
COPY docker/web-entrypoint.sh /usr/local/bin/web-entrypoint.sh

RUN chmod +x /usr/local/bin/web-entrypoint.sh

EXPOSE 3000

ENTRYPOINT ["web-entrypoint.sh"]
