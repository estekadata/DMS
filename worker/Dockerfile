FROM python:3.12-slim

# Installe mdbtools + libs minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    mdbtools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installe les dépendances Python
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie le script de sync ET le worker
# (NB: le build context Railway est la racine du repo Script/)
COPY sync_access.py /app/sync_access.py
COPY worker/main.py /app/main.py

# Variables d'env par défaut
ENV PYTHON_BIN=/usr/local/bin/python
ENV SYNC_SCRIPT=/app/sync_access.py
ENV UPLOAD_DIR=/tmp/uploads
ENV PORT=8080

EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
