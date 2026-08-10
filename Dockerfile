# Gunakan image Python 3.11 yang ringan
FROM python:3.11-slim

# Set direktori kerja di dalam container
WORKDIR /app

# Install dependencies sistem yang mungkin dibutuhkan oleh psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Salin file requirements.txt dan install pustaka
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode proyek (termasuk folder app, static, dan credentials)
COPY . .

# Ekspos port 8000 yang digunakan FastAPI
EXPOSE 8000

# Perintah default saat container dijalankan
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]