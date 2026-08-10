import os
import requests
from dotenv import load_dotenv

# Memuat konfigurasi dari file .env
load_dotenv()

GITLAB_TOKEN = os.getenv("GITLAB_ACCESS_TOKEN")
BASE_URL = os.getenv("GITLAB_BASE_URL")
PROJECT_ID = os.getenv("GITLAB_PROJECT_ID")

def get_monthly_commits(start_date: str, end_date: str):
    """
    Fungsi untuk mengambil data commit dari GitLab berdasarkan rentang tanggal.
    Format tanggal: YYYY-MM-DD (contoh: 2026-08-01)
    """
    print(f"Mengambil data commit dari {start_date} hingga {end_date}...")

    # Endpoint API GitLab untuk mengambil commits
    url = f"{BASE_URL}/api/v4/projects/{PROJECT_ID}/repository/commits"

    headers = {
        "PRIVATE-TOKEN": GITLAB_TOKEN
    }

    # Parameter query
    params = {
        "since": f"{start_date}T00:00:00Z",
        "until": f"{end_date}T23:59:59Z",
        "with_stats": "true", # Untuk melihat jumlah baris kode yang ditambah/dihapus
        "per_page": 100       # Mengambil maksimal 100 commit per halaman
    }

    response = requests.get(url, headers=headers, params=params)

    # Cek apakah permintaan berhasil (Status Code 200 = OK)
    if response.status_code == 200:
        commits = response.json()
        print(f"Berhasil! Ditemukan {len(commits)} commit.")
        return commits
    else:
        print(f"Gagal mengambil data. Status Code: {response.status_code}")
        print(response.text)
        return []