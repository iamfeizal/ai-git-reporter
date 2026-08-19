from src.gitlab_client import get_monthly_commits

# Kita uji coba untuk mengambil data bulan lalu atau bulan ini
# Sesuaikan tanggal ini dengan aktivitas gitlab Anda
START_DATE = "2026-07-01" 
END_DATE = "2026-07-31"

if __name__ == "__main__":
    # Jalankan fungsi
    hasil_commits = get_monthly_commits(START_DATE, END_DATE)

    # Tampilkan 1 commit pertama sebagai contoh uji coba
    if hasil_commits:
        print("\n--- CONTOH 1 DATA COMMIT ---")
        contoh = hasil_commits[0]
        print(f"ID: {contoh.get('short_id')}")
        print(f"Author: {contoh.get('author_name')}")
        print(f"Judul: {contoh.get('title')}")
        print(f"Tanggal: {contoh.get('created_at')}")
    else:
        print("\nTidak ada data yang bisa ditampilkan. Pastikan Token dan Project ID benar.")