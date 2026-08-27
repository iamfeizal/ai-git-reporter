Berikut adalah **Blueprint Arsitektur Teknis Detail** untuk **Sistem Pembuatan Laporan Bulanan Otomatis Berbasis AI/ML** dengan integrasi **GitLab API** dan **Google Docs API** yang dirancang khusus untuk arsitektur **Super App**.

Rancangan ini didesain menggunakan pendekatan **Stateful Multi-Agent Workflow** berbasis **LangGraph** dengan mekanisme **Human-in-the-Loop (HITL)** berkemampuan **CRUD Penuh**, **Granular Semantic Sub-Clustering**, **Penerjemahan Narasi Berimbang (Balanced Tech-to-Business)**, serta **Sinkronisasi Dokumen Google Docs Inkremental berbasis Looping Worker**.

---

# BLUEPRINT TEKNIS: AI-DRIVEN GITLAB TO GOOGLE DOCS REPORTING SYSTEM (SUPER APP EDITION)

```
+-----------------------------------------------------------------------------------------------------------------------+
|                                                FRONTEND WEB UI (HITL)                                                 |
|  [Pilih Bulan] ---> [HITL 1: Domain & Sub-Domain Layanan CRUD] ---> [HITL 2: Tree Clustering CRUD] ---> [Live Progress] |
+-----------------------------------------------------------------------------------------------------------------------+
       |                                      ^                                      ^                              |
       v                                      |                                      |                              v
+-----------------------------------------------------------------------------------------------------------------------+
|                                           ORCHESTRATION ENGINE (LangGraph)                                            |
|                                                                                                                       |
|  +---------------------+      +-----------------------------+      +-----------------------------------------------+  |
|  | GitLab Ingestion    | ---> | L1 Classification Node      | ---> | L2 Granular Semantic Sub-Clustering           |  |
|  | (REST API / Commit) |      | (Sistem Inti vs Sub-Layanan)|      | (Conventional Commit -> Context -> SubCluster)|  |
|  +---------------------+      +-----------------------------+      +-----------------------------------------------+  |
|                                                                                             |                         |
|                                                                                             v                         |
|  +-----------------------------------------------------------------------------------------------------------------+  |
|  |                              Executive Summary & Dynamic Heading Hierarchy Generator Node                       |  |
|  +-----------------------------------------------------------------------------------------------------------------+  |
|                                                     |                                                                 |
|                                                     v                                                                 |
|                               +--------------------------------------------+                                          |
|                               |    ITERATIVE SUB-CLUSTER WORKER (LOOP)     |                                          |
|                               |                                            |                                          |
|                               |   +------------------------------------+   |                                          |
|                               |   | Detail Narration Node              |   |                                          |
|                               |   | (Balanced Tech-to-Business +       |   |                                          |
|                               |   |  Preserve Function & Terms +       |   |                                          |
|                               |   |  Visual Placeholder Detector)      |   |                                          |
|                               |   +------------------------------------+   |                                          |
|                               |                      |                     |                                          |
|                               |                      v                     |                                          |
|                               |   +------------------------------------+   |                                          |
|                               |   | Google Docs API Incremental Append |   |                                          |
|                               |   | (batchUpdate IR + Monospace Styles)|   |                                          |
|                               |   +------------------------------------+   |                                          |
|                               |                      |                     |                                          |
|                               |                      v                     |                                          |
|                               |   +------------------------------------+   |                                          |
|                               |   | LangGraph State Checkpoint &       |   |                                          |
|                               |   | Real-time Progress Event (SSE/WS)  |   |                                          |
|                               |   +------------------------------------+   |                                          |
|                               +--------------------------------------------+                                          |
+-----------------------------------------------------------------------------------------------------------------------+
          ^                                                                                    ^
          |                                                                                    |
+-----------------------------------+                                       +-----------------------------------+
|    GOOGLE DOCS TEMPLATE REGISTRY  |                                       |     LLM & VECTOR INFRASTRUCTURE   |
|  - Named Styles (H1, H2, H3, H4)  |                                       |  - LLM (Gemini 2.5 / 3.5 Flash)   |
|  - Monospace Code Text Styling    |                                       |  - Embeddings (text-embedding-3)  |
|  - Dynamic Placeholder Rules      |                                       |  - LangGraph State Persistence    |
+-----------------------------------+                                       +-----------------------------------+
```

---

## 1. Strategi AI & Manajemen Template Document

### 1.1. Mengapa *Few-Shot In-Context Learning (ICL)* & *Structured Schema*, Bukan *Fine-Tuning*?

* Melakukan *supervised fine-tuning* pada LLM dengan sampel dokumen laporan tidak disarankan karena risiko *overfitting* yang tinggi, inflexibilitas terhadap perubahan struktur super app, serta kesulitan pemeliharaan tata letak (*formatting drift*).
* **Pendekatan Terbaik:** Menggunakan **Few-Shot In-Context Learning** untuk mempelajari *tone* bahasa (gaya penulisan dokumen formal korporat) dipadukan dengan **Structured Output Validation (Pydantic / JSON Schema)** untuk menjamin konsistensi keluaran dan validitas skema data di setiap langkah.

### 1.2. Transisi format `.docx` ke Google Docs (Document AST & Incremental Append Strategy)

* **Masalah:** Konversi langsung `.docx` ke Google Docs sering merusak margin, indentasi *unordered/ordered list*, dan hierarki Heading. Selain itu, mengirim seluruh isi laporan ratusan halaman dalam 1 kali panggilan API raksasa rentan *payload limit* dan kegagalan total (*all-or-nothing failure*).
* **Solusi (Template Standardization & Looping Append):**
  1. Buat **satu dokumen master Google Docs** sebagai *Template Resmi* dengan *Named Styles* permanen (`Heading 1`, `Heading 2`, `Heading 3`, `Heading 4`, `Normal Text`, bullet/list font, warna tabel, dan styling monospace untuk kode/fungsi).
  2. Dokumen template memuat variabel statis (pembuka, pengantar) dan **Dynamic Placeholders** awal (`{{MONTH_YEAR}}`, `{{EXEC_SUMMARY}}`).
  3. Dokumen baru diinisialisasi dari template, kemudian setiap sub-cluster hasil olahan AI disisipkan secara bertahap (*incremental append*) menggunakan perintah `batchUpdate` pada **Google Docs API** (mengisikan teks pada indeks akhir, menerapkan *style heading*, menyisipkan teks narasi berimbang, memformat nama fungsi dengan font monospace, dan menambahkan penanda visual berwarna).

---

## 2. Arsitektur & Spesifikasi Pipeline per Tahapan (Step-by-Step)

Sistem dibangun menggunakan stateful graph orchestrator (**LangGraph**) untuk mengelola alur kerja, penghentian sementara (*checkpoint pause*) pada tahap **Human-in-the-Loop (HITL)**, dan eksekusi perulangan (*looping worker*) yang tahan terhadap kegagalan.

### Tahap 1: Ingesti & Filter Data GitLab

* **Input User:** Rentang waktu (tanggal awal & akhir) atau pilihan Bulan/Tahun via Frontend Web UI.
* **Proses Integrasi:**
  * Sistem memanggil **GitLab REST API v4** (`/projects/:id/repository/commits?since=X&until=Y&with_stats=true`).
  * **Data Normalization & Cleaning:**
    * Menghapus *commit noise* (misal: commit *merge request default message*, *bump version*, bot commit `dependabot`, atau *typo fix* sederhana yang tidak relevan untuk laporan bisnis).
    * Ekstraksi metadata: `short_id`, `author_name`, `committed_date`, `title` (commit subject), `message` (commit body), path file yang dimodifikasi, dan statistik perubahan (`stats.additions`, `stats.deletions`).

---

### Tahap 2: Klasifikasi Level 1 — *Sistem Inti Aplikasi vs. Layanan Aplikasi (Super App Modules)*

* **Tujuan:** Memisahkan *commit* ke dalam 2 domain utama pada arsitektur Super App:
  1. **Sistem Inti Aplikasi (Core System):** Perubahan pada level fondasi arsitektur bersama, framework core, global state management, design system/shared UI kit, middleware global, sistem otentikasi sentral (SSO), atau optimasi kueri database inti.
  2. **Layanan Aplikasi (Super App Service Modules):** Seluruh fitur, modul, atau sub-aplikasi bisnis independen yang beroperasi di dalam ekosistem Super App.

* **Deteksi Otomatis Sub-Domain untuk "Layanan Aplikasi":**
  * AI secara otomatis mengekstraksi dan mengidentifikasi sub-domain (nama app/modul/layanan) berdasarkan *scope* pada conventional commit (misal: `feat(presensi): ...`, `fix(pembayaran): ...`) atau path direktori modul (misal: `apps/presensi/`, `modules/helpdesk/`).
  * **Contoh Sub-Domain Layanan Aplikasi:**
    * *Layanan Presensi & Kepegawaian*
    * *Layanan Pembayaran & Dompet Digital*
    * *Layanan Tiket & Helpdesk Layanan*
    * *Layanan Pengadaan & Logistik*
    * *Layanan Notifikasi & Komunikasi Pengguna*
    * *(Sub-domain lain yang terdeteksi secara dinamis sesuai repositori)*

* **Implementasi Teknis:**
  * Pemrosesan klasifikasi awal menggunakan LLM dengan **Structured Output**.
  * Setiap commit dipetakan ke: Domain (`SYSTEM_CORE` vs `APP_SERVICE`) dan jika masuk ke `APP_SERVICE`, secara otomatis dialokasikan ke salah satu `sub_domain_id` / `sub_domain_name`.

---

### Tahap 3: Human-in-the-Loop (HITL) Checkpoint 1

* **Alur:** Graph eksekusi LangGraph memasuki status *state pause* dan menyimpan snapshot state ke checkpointer (SQLite / PostgreSQL).
* **Antarmuka UI:** Web UI menampilkan panel interaktif dua tingkat:
  1. Tab/Kolom Utama: **Sistem Inti Aplikasi** vs **Layanan Aplikasi**.
  2. Panel Sub-Domain Layanan: Menampilkan daftar kartu/tab dari masing-masing sub-domain (app/modul) beserta commit yang dialokasikan di dalamnya.

* **Aksi User (Interaktivitas & Kapabilitas CRUD Lengkap):**
  * **Pemindahan Commit:** User dapat memindahkan (*drag-and-drop* / klik transfer) commit antara *Sistem Inti* dan *Layanan Aplikasi*, serta memindahkan commit antar sub-domain layanan.
  * **CRUD Penuh pada Sub-Domain Layanan Aplikasi:**
    * **Create (Tambah):** Menambahkan sub-domain/layanan baru (misal: membuat "Layanan Monitoring Kendaraan" jika ada fitur baru yang belum memiliki wadah modul).
    * **Read (Lihat):** Melihat rincian modul layanan, deskripsi, dan daftar commit terkait.
    * **Update (Ubah):** Mengedit judul/nama sub-domain layanan dan mengubah deskripsi singkat modul agar sesuai dengan nomenklatur resmi perusahaan.
    * **Delete (Hapus):** Menghapus sub-domain layanan tertentu (dengan dialog konfirmasi untuk memindahkan commit di dalamnya ke sub-domain lain atau ke penampung umum).
    * **Reorder / Organize:** Mengatur urutan prioritas sub-domain layanan untuk penyusunan laporan.
  * User menekan tombol **"Simpan & Lanjutkan ke Clustering (HITL 2)"** untuk melanjutkan graph.

---

### Tahap 4: Klasifikasi Level 2 & Granular Semantic Sub-Clustering

* **Tujuan:** Menghindari pengelompokan yang terlalu lebar/makro dengan membagi commit ke dalam struktur hirarki 4 tingkat yang detail, terstruktur, dan berakar pada **Conventional Commits** (`feat`, `fix`, `ui`, `refactor`, `perf`, `chore`, `docs`).

* **Struktur Hirarki 4-Level:**
  ```
  1. Domain / Sub-Domain Layanan (misal: Layanan Pembayaran)
     └── 2. Kategori Conventional Commits (misal: Pengembangan Fitur Baru / feat)
          └── 3. Cluster Konteks Fitur/Komponen (misal: Modul Integrasi Payment Gateway)
               └── 4. Sub-Cluster Fungsional Spesifik (Unit Cerita / Fungsionalitas Detail)
                    ├── Sub-Cluster A: Integrasi QRIS Dinamis & Penanganan Callback Webhook
                    └── Sub-Cluster B: Validasi Saldo Dompet Digital & Mekanisme Auto-Refund
  ```

* **Mengapa Sub-Clustering Granular Penting?**
  * Pengelompokan makro yang terlalu luas (misal: menggabungkan semua commit `feat` dalam 1 modul menjadi 1 narasi panjang) membuat laporan kehilangan konteks esensial.
  * Dengan membagi ke dalam **Sub-Cluster Fungsional Spesifik**, setiap narasi laporan fokus pada satu unit fungsionalitas/tujuan bisnis yang jelas, terukur, dan mudah dievaluasi progresnya.

* **Implementasi Teknis:**
  1. **Rule-Based Pre-parsing:** Regex untuk mengekstrak *type*, *scope*, dan *breaking changes* dari pesan conventional commit (`type(scope): subject`).
  2. **Vector Embedding & Granular Semantic Grouping:** Menggunakan model embedding (`text-embedding-3-small` / Gemini Embedding) dengan ambang batas *cosine similarity* ketat untuk mendeteksi kesamaan konteks fungsi/file yang dimodifikasi.
  3. **LLM Context Boundary Refiner:** LLM menyempurnakan batasan sub-cluster agar commit yang berada dalam 1 sub-cluster benar-benar membentuk satu alur fungsional yang utuh, serta memberikan judul sub-cluster yang spesifik dan tajam.

---

### Tahap 5: Human-in-the-Loop (HITL) Checkpoint 2

* **Alur:** Graph eksekusi LangGraph memasuki *state pause* kedua untuk verifikasi pengelompokan detail.
* **Antarmuka UI (Interactive Tree & CRUD Explorer):**
  * Menampilkan struktur pohon hierarki interaktif:
    `Domain / Sub-Domain Layanan` $\rightarrow$ `Kategori Conventional` $\rightarrow$ `Cluster Konteks` $\rightarrow$ `Sub-Cluster Fungsional` $\rightarrow$ `Daftar Commit`.

* **Aksi User (Fitur CRUD Lengkap pada Commit & Sub-Cluster):**
  * **Manajemen Commit (CRUD):**
    * **Edit:** Mengubah atau melengkapi pesan/konteks commit jika deskripsi git asli terlalu singkat/ambigu.
    * **Move:** Memindahkan commit ke sub-cluster atau cluster lain jika AI salah menempatkan konteks fungsional.
    * **Add (Manual Commit / Task):** Menambahkan commit manual atau item pekerjaan offline (misal: *“Hotfix migrasi data transaksi pembayaran”*) yang belum tercatat di git agar tetap masuk dalam laporan resmi.
    * **Delete / Exclude:** Menghapus atau mengecualikan commit tertentu agar tidak diikutsertakan dalam laporan akhir.
  * **Manajemen Cluster & Sub-Cluster (CRUD):**
    * **Create:** Membuat sub-cluster fungsional baru secara manual.
    * **Edit / Rename:** Mengubah nama cluster konteks atau judul sub-cluster fungsional agar selaras dengan bahasa program kerja perusahaan.
    * **Delete:** Menghapus sub-cluster yang tidak relevan.
    * **Split (Pecah):** Memecah sub-cluster yang dirasa masih terlalu padat menjadi dua sub-cluster terpisah.
    * **Merge (Gabung):** Menggabungkan dua sub-cluster serumpun menjadi satu kesatuan.
  * User menekan tombol **"Setujui & Mulai Generate Dokumen"** untuk memulai orkestrasi perulangan ke Google Docs.

---

### Tahap 6: Sintesis Executive Summary & Struktur Hierarki Heading

* **Tujuan:** Menghasilkan ringkasan tingkat tinggi (*high-level executive summary*) bulan berjalan dan menginisialisasi kerangka hierarki dokumen pada Google Docs.
* **Implementasi Teknis:**
  * LLM mengevaluasi seluruh ringkasan sub-cluster (total modul aktif, volume fitur baru, efisiensi sistem, dan resolusi masalah kritis).
  * LLM menyusun 2–3 paragraf narasi eksekutif formal untuk bagian pembuka laporan.
  * Dokumen Google Docs baru dibuat dari Template Master, dan kerangka Heading disusun sesuai hierarki standar:

#### Struktur Hierarki Heading Dokumen:
* `Heading 1`: **Laporan Aktivitas Pengembangan Super App - [Bulan Tahun]**
  * *[Paragraf Executive Summary]*
* `Heading 2`: **1. Perbaikan dan Pengembangan Sistem Inti Aplikasi**
  * `Heading 3`: **1.1. Pengembangan Fitur dan Antarmuka Baru (`feat`, `ui`)**
    * `Heading 4`: **1.1.1. [Nama Cluster Konteks Sistem Inti]**
      * *(Sub-cluster narasi detail + visual placeholder)*
  * `Heading 3`: **1.2. Resolusi Bug, Performa dan Refaktorisasi (`fix`, `perf`, `refactor`)**
    * `Heading 4`: **1.2.1. [Nama Cluster Konteks Sistem Inti]**
      * *(Sub-cluster narasi detail + visual placeholder)*
* `Heading 2`: **2. Pengembangan dan Pemeliharaan Layanan Aplikasi**
  * `Heading 3`: **2.1. Pengembangan Fitur dan Antarmuka Baru (`feat`, `ui`)**
    * `Heading 4`: **2.1.1. Layanan [Nama App/Modul] - [Cluster Konteks Fitur]**
      * *(Sub-cluster narasi detail + visual placeholder)*
  * `Heading 3`: **2.2. Resolusi Bug dan Pemeliharaan Layanan (`fix`, `perf`, `refactor`)**
    * `Heading 4`: **2.2.1. Layanan [Nama App/Modul] - [Cluster Konteks Bug/Perbaikan]**
      * *(Sub-cluster narasi detail + visual placeholder)*
  * `Heading 3`: **2.3. Pemeliharaan Infrastruktur dan Operasional Layanan (`chore`, `ops`)**
    * `Heading 4`: **2.3.1. Layanan [Nama App/Modul] - [Cluster Konteks Infra/Chore]**
      * *(Sub-cluster narasi detail + visual placeholder)*

---

### Tahap 7: Iterasi Narasi Detail (Balanced Tech-to-Business Translation) & Visual Placeholder

* **Filosofi Penulisan (Balanced Translation):**
  * Laporan harus mudah dipahami oleh manajemen eksekutif dan pemangku kepentingan non-teknis, **TETAPI TETAP MEMPERTAHANKAN** nama fungsi asli, endpoint API, dan istilah teknis penting secara presisi.
  * **Dilarang menerjemahkan secara mentah/harfiah** (misal: jangan menerjemahkan *webhook* menjadi *kait web*, *debounce* menjadi *pengurang pantulan*, atau menghilangkan nama fungsi yang krusial).
  * **Aturan Format Visual pada Google Docs:**
    * **Nama Fungsi Asli, Endpoint API & Variabel Teknis:** Wajib dipertahankan sesuai aslinya dan diformat menggunakan font **monospace / gaya inline code** (contoh: `handleStockLock()`, `/v1/orders/checkout`, `payload.userId`).
    * **Istilah Protokol / Teknologi / Infrastruktur Penting:** Dipertahankan dan diformat dengan **cetak tebal / bold** (contoh: **OAuth 2.0**, **Redis Cache**, **JWT Token**, **WebSocket**, **Docker Container**, **SSL/TLS Certificate**).
    * **Konteks & Dampak:** Dijelaskan dalam bahasa Indonesia naratif formal yang lugas, mengalir, dan menjelaskan *apa yang diubah*, *mengapa diubah*, dan *apa dampak positifnya bagi bisnis/pengguna*.

* **Visual Need Detector:**
  * LLM mengevaluasi apakah perubahan pada sub-cluster melibatkan perubahan alur antarmuka (UI), penambahan menu baru, atau perubahan alur data yang memerlukan bukti visual.
  * Jika bernilai `True`, LLM otomatis menyisipkan penanda kotak visual:
    `[TAMBAHKAN GAMBAR/DOKUMENTASI - Keterangan: ...]` dengan gaya latar belakang teks berwarna kuning/abu-abu agar mudah dilihat saat peninjauan dokumen.

#### Contoh Transformasi Narasi Seimbang (Input Commit vs Output Laporan):

* **Input Commit Sub-Cluster:**
  * `feat(checkout): implement debounce 500ms in handleCartQuantityUpdate() to prevent rapid clicks`
  * `fix(checkout): resolve race condition on stock reservation in POST /api/v1/cart/lock-stock using Redis distributed lock`

* **Output AI pada Laporan (Bahasa Bisnis Formal + Preservasi Istilah Teknis & Monospace):**
  > **Peningkatan Keandalan dan Validasi Stok pada Alur Checkout Transaksi**
  > Telah dilakukan penyempurnaan pada fungsi `handleCartQuantityUpdate()` di halaman keranjang belanja dengan menerapkan mekanisme *debounce* sebesar 500ms. Pembaruan ini memastikan sistem tidak memicu permintaan berulang saat pengguna menekan tombol penambahan jumlah barang secara cepat. 
  > 
  > Selain itu, pada endpoint `POST /api/v1/cart/lock-stock`, telah diimplementasikan mekanisme penguncian terdistribusi berbasis **Redis** (*distributed lock*) untuk mengeliminasi potensi *race condition*. Pembaruan ini menjamin kuantitas stok barang terkunci secara presisi selama proses pembayaran berlangsung, sehingga mencegah terjadinya penjualan barang melebihi stok yang tersedia (*overselling*).
  > 
  > `[TAMBAHKAN GAMBAR/DOKUMENTASI - Keterangan: Tangkapan layar antarmuka keranjang belanja saat kuantitas diperbarui dan notifikasi penguncian stok berhasil ditampilkan]`

---

### Tahap 8: Looping LLM Orchestration Worker & Incremental Google Docs Sync

Alih-alih memproses seluruh commit secara serentak dalam 1 prompt raksasa (yang berisiko terkena limit token, degradasi kualitas, dan kegagalan total), sistem menggunakan pola **Iterative Sub-Cluster Worker**:

```
+------------------------------------------------------------------------------------------------+
|                             LOOPING SUB-CLUSTER EXECUTION FLOW                                 |
|                                                                                                |
|   1. Inisialisasi Template Google Docs (Heading 1 & Executive Summary)                         |
|                                                                                                |
|   2. Perulangan (Loop) per Sub-Cluster:                                                        |
|      for each sub_cluster in report_plan.sub_clusters:                                         |
|         ├── a. LLM Orchestrator: Generate Balanced Narration + Visual Placeholder              |
|         ├── b. Backend Google Docs Service: Kirim batchUpdate langsung ke Google Docs          |
|         │      (Insert Heading, Paragraf Narasi, Monospace Function Style, Highlight Note)     |
|         ├── c. LangGraph State Checkpointer: Simpan progress status sub-cluster = "COMPLETED"  |
|         └── d. WebSocket / SSE Event: Emit update progress bar ke Web UI ("Sub-cluster i of N")|
|                                                                                                |
|   3. Finalisasi Dokumen & Notifikasi Selesai ke Frontend                                       |
+------------------------------------------------------------------------------------------------+
```

* **Keunggulan Pola Looping Worker:**
  1. **Kualitas Narasi Maksimal:** Setiap sub-cluster mendapatkan kapasitas *attention* dan token penuh dari LLM sehingga narasi lebih komprehensif dan mendalam.
  2. **Streaming & Feedback Real-time:** Pengguna dapat memantau progres pembuatan laporan secara langsung di antarmuka Web UI per sub-cluster yang berhasil ditulis.
  3. **Fault-Tolerance & Resume Capability:** Jika terjadi gangguan jaringan atau *rate-limit* pada sub-cluster ke-7 dari 20, state LangGraph tetap aman. Sistem cukup me-retry eksekusi mulai dari sub-cluster ke-7 tanpa perlu mengulang dari awal atau merusak bagian dokumen yang sudah tertulis.

---

## 3. Desain Skema Data (Structured Schema / Pydantic)

Untuk menjamin struktur data yang divalidasi ketat di setiap langkah LangGraph:

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class CommitItem(BaseModel):
    commit_id: str
    short_id: str
    original_message: str
    author_name: str
    files_changed: List[str] = Field(default_factory=list)
    custom_note: Optional[str] = Field(
        default=None, 
        description="Catatan tambahan dari hasil edit user pada HITL"
    )

class ServiceSubDomain(BaseModel):
    sub_domain_id: str
    sub_domain_name: str = Field(..., description="Nama App/Modul/Layanan dalam Super App")
    description: Optional[str] = None
    commit_ids: List[str] = Field(default_factory=list)

class SubClusterItem(BaseModel):
    sub_cluster_id: str
    sub_cluster_title: str = Field(..., description="Judul tema fungsional spesifik")
    functional_scope: str = Field(..., description="Deskripsi cakupan fungsi/masalah")
    commit_ids: List[str] = Field(default_factory=list)

class ContextCluster(BaseModel):
    cluster_id: str
    cluster_title: str = Field(..., description="Judul Cluster Konteks Modul")
    category_level_2: Literal["FEATURE_UI", "BUG_FIX", "REFACTOR_PERF", "INFRA_CHORE"]
    sub_clusters: List[SubClusterItem]

class SubClusterNarrationOutput(BaseModel):
    sub_cluster_id: str
    sub_cluster_title: str
    business_narrative: str = Field(
        ..., 
        description="Narasi detail bahasa Indonesia formal yang berimbang, mempertahankan nama fungsi asli dan istilah teknis kunci"
    )
    key_technical_terms_preserved: List[str] = Field(
        default_factory=list, 
        description="Daftar nama fungsi (misal: handleCartQuantityUpdate()) atau endpoint API yang dipertahankan"
    )
    requires_visual: bool = Field(default=False)
    visual_placeholder_note: Optional[str] = Field(
        default=None, 
        description="Instruksi spesifik screenshot visual jika requires_visual = True"
    )

class LangGraphReportState(BaseModel):
    report_id: str
    month_year: str
    google_doc_id: Optional[str] = None
    google_doc_url: Optional[str] = None
    executive_summary: Optional[str] = None
    service_sub_domains: List[ServiceSubDomain] = Field(default_factory=list)
    core_system_clusters: List[ContextCluster] = Field(default_factory=list)
    service_app_clusters: List[ContextCluster] = Field(default_factory=list)
    completed_sub_cluster_ids: List[str] = Field(default_factory=list)
    current_progress_percentage: float = 0.0
```

---

## 4. Desain System Prompt (Iterative Sub-Cluster Narrative Generator)

```text
Anda adalah Senior Technical Writer & Lead Business Analyst untuk ekosistem Super App enterprise.
Tugas Anda adalah menyusun narasi laporan progres bulanan mendalam dari kelompok git commit (Sub-Cluster Fungsional) untuk disajikan kepada pemangku kepentingan manajemen dan pimpinan teknis.

ATURAN PENULISAN (BALANCED TECH-TO-BUSINESS):
1. BAHASA FORMAL & KOMPREHENSIF:
   - Gunakan Bahasa Indonesia formal yang profesional, baku, runtut, dan jelas.
   - Tuliskan dalam paragraf naratif utuh (2-3 paragraf per sub-cluster). Jelaskan latar belakang/masalah, solusi teknis yang diterapkan, serta manfaat langsung bagi kestabilan sistem atau pengalaman pengguna.
   - DILARANG menulis sekadar ringkasan singkat atau poin-poin mentah.

2. PRESERVASI NAMA FUNGSI & ISTILAH TEKNIS KRUSIAL:
   - JANGAN menerjemahkan istilah teknis baku atau nama fungsi secara mentah (DILARANG: "kait web", "pengurang pantulan", dsb).
   - CANTUMKAN NAMA FUNGSI ASLI (contoh: `handleStockLock()`, `validateSessionToken()`) dan ENDPOINT API (contoh: `/api/v1/checkout`) dalam format tanda kutip backtick/code.
   - PERTAHANKAN istilah teknologi/protokol penting (contoh: OAuth 2.0, Redis, JWT, WebSocket, Docker, SSL/TLS, CI/CD Pipeline) dengan format cetak tebal (bold).

3. DETEKSI DOKUMENTASI VISUAL (VISUAL PLACEHOLDER):
   - Jika sub-cluster mencakup pembaruan antarmuka pengguna (UI), alur transaksi baru, dashboard, atau perubahan interaksi pengguna:
     - Set 'requires_visual' = true.
     - Isi 'visual_placeholder_note' dengan panduan screenshot spesifik (misal: "Tangkapan layar modal konfirmasi pembayaran saat validasi OTP berhasil").
   - Jika murni optimasi backend internal/kueri database yang tidak memiliki tampilan, set 'requires_visual' = false.
```

---

## 5. Rekomendasi Stack Teknologi (*Production-Ready*)

| Lapisan (Layer) | Teknologi Rekomendasi | Alasan Pemilihan & Penerapan |
| --- | --- | --- |
| **LLM Engine** | **Gemini 2.5 / 3.5 Flash** | Kecepatan tinggi untuk perulangan (*looping worker*), penalaran kontekstual superior, dan keandalan *Structured Outputs* (Pydantic). |
| **Orchestrator** | **LangGraph (Python)** | Mengelola *graph pipeline* kompleks dengan status persisten (*stateful persistence* via Postgres/SQLite) untuk interupsi **Human-in-the-Loop** dan mekanisme *resume loop*. |
| **API Backend** | **FastAPI + WebSockets / SSE** | Mengelola endpoint REST dan *streaming progress real-time* saat loop pembuatan narasi ke Google Docs sedang berjalan. |
| **Vector Engine** | **pgvector (PostgreSQL)** | Penyimpanan *embedding* pesan commit dan riwayat laporan bulan sebelumnya untuk clustering semantik berbobot tinggi. |
| **Frontend UI** | **Next.js (React) + TailwindCSS** | Antarmuka interaktif responsif untuk drag-and-drop commit, panel CRUD Sub-Domain Layanan, dan *Live Progress Bar*. |
| **Integration** | **Google-API-Python-Client (Docs API v1)** | Otomatisasi penulisan `.gdoc` inkremental via `batchUpdate` dengan Service Account / OAuth 2.0. |

---

## 6. Mitigasi Risiko & *Engineering Guardrails*

1. **Risiko: *Google Docs API Rate Limiting (429 Too Many Requests) pada Pola Looping***
   * *Mitigasi:* Google Docs API memiliki kuota tulis per menit. Setiap iterasi sub-cluster mengirimkan 1 paket `batchUpdate` ringkas yang mencakup penulisan teks, styling heading, monospace font, dan format highlight. Sistem menerapkan *pacing delay* adaptif (misal: 300–500ms antar sub-cluster) dan *exponential backoff with jitter* jika terdeteksi respon `429`.

2. **Risiko: *Noise & Overlapping Sub-Clusters***
   * *Mitigasi:* Commit bot otomatis diabaikan pada tahap ingesti. Pada tahap clustering, kemiripan kosinus dievaluasi bersamaan dengan analisis nama file/jalur direktori modul agar commit tidak terpecah ke sub-cluster yang tidak relevan.

3. **Risiko: *Tone Drift & Hilangnya Akurasi Teknis***
   * *Mitigasi:* Mengombinasikan *Few-Shot In-Context Learning* dari sampel laporan terbaik dengan instruksi eksplisit preservasi nama fungsi dan format monospace.

4. **Risiko: *Interupsi Jaringan saat Looping Worker Berjalan***
   * *Mitigasi:* Setiap sub-cluster yang selesai ditulis ke Google Docs langsung dicatat dalam *LangGraph Checkpoint State* (`completed_sub_cluster_ids`). Jika terjadi *crash* atau *network timeout*, sistem dapat melanjutkan (*resume*) tepat dari sub-cluster yang belum selesai tanpa membuat dokumen baru atau menimpa bagian yang sudah ada.

5. **Risiko: *Keamanan & Privasi Pesan Commit Super App***
   * *Mitigasi:* Gunakan enterprise SLA endpoint (misal: Google Cloud Vertex AI atau Azure OpenAI Service) yang menjamin *zero data retention* dan kepatuhan privasi data korporat.