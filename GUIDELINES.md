Berikut adalah **Blueprint Arsitektur Teknis Detail** untuk **Sistem Pembuatan Laporan Bulanan Otomatis Berbasis AI/ML** dengan integrasi **GitLab API** dan **Google Docs API**.

Rancangan ini didesain menggunakan pendekatan **Stateful Multi-Agent Workflow** dengan mekanisme **Human-in-the-Loop (HITL)** dan **Structured Output Verification** agar *production-ready*, bebas halusinasi struktur, serta menghasilkan narasi ramah non-teknis.

---

# BLUEPRINT TEKNIS: AI-DRIVEN GITLAB TO GOOGLE DOCS REPORTING SYSTEM

```
+---------------------------------------------------------------------------------------------------+
|                                      FRONTEND WEB UI (HITL)                                       |
|  [Pilih Bulan] ---> [Review Level 1: System vs Service] ---> [Review Level 2: Sub-Kategori]      |
+---------------------------------------------------------------------------------------------------+
       |                    ^                              ^                              |
       v                    |                              |                              v
+---------------------------------------------------------------------------------------------------+
|                                ORCHESTRATION ENGINE (LangGraph)                                   |
|                                                                                                   |
|  +-------------------+     +-------------------------+     +-----------------------------------+  |
|  |  GitLab Ingestion | --> |  L1 Classification Node | --> |  L2 Classification & Clustering   |  |
|  |  (REST API / Git) |     |  (LLM Structured JSON)  |     |  (Semantic Embedding + LLM)       |  |
|  +-------------------+     +-------------------------+     +-----------------------------------+  |
|                                                                              |                    |
|                                                                              v                    |
|  +-------------------+     +-------------------------+     +-----------------------------------+  |
|  |  Google Docs API  | <-- |  Detail Narration Node  | <-- |  Executive Summary & Subheading   |  |
|  |  (batchUpdate IR) |     |  (Tech -> Business +    |     |  Generation Node                  |  |
|  |                   |     |   Image Placeholder)    |     |                                   |  |
|  +-------------------+     +-------------------------+     +-----------------------------------+  |
+---------------------------------------------------------------------------------------------------+
          ^                                                                        ^
          |                                                                        |
+-----------------------------------+                           +-----------------------------------+
|  GOOGLE DOCS TEMPLATE REGISTRY    |                           |     LLM & VECTOR INFRASTRUCTURE   |
|  - Named Styles (H1, H2, Body)    |                           |  - LLM (Gemini 1.5 Pro / GPT-4o)  |
|  - Dynamic Placeholder Rules      |                           |  - Embeddings (text-embedding-3)  |
+-----------------------------------+                           +-----------------------------------+

```

---

## 1. Strategi AI & Manajemen Template Document

### 1.1. Mengapa *Few-Shot In-Context Learning (ICL)* & *Structured Schema*, Bukan *Fine-Tuning*?

* Dengan **7 sampel laporan `.docx**`, melakukan *supervised fine-tuning* pada LLM tidak disarankan karena risiko *overfitting* yang tinggi dan kesulitan pemeliharaan format tata letak (*formatting drift*).
* **Pendekatan Terbaik:** Menggunakan **Few-Shot In-Context Learning** untuk mempelajari *tone* bahasa (gaya penulisan dokumen formal perusahaan) dipadukan dengan **Structured Output Validation (Pydantic / JSON Schema)** untuk menjamin konsistensi keluaran.

### 1.2. Transisi format `.docx` ke Google Docs (Document AST Strategy)

* **Masalah:** Konversi langsung `.docx` ke Google Docs sering merusak margin, indentasi *unordered/ordered list*, dan hierarki Heading.
* **Solusi (Template Standardization):**
1. Buat **satu dokumen master Google Docs** sebagai *Template Resmi* dengan *Named Styles* yang sudah dikonfigurasi permanen (`Heading 1`, `Heading 2`, `Heading 3`, `Normal Text`, bullet/list font, warna tabel).
2. Dokumen template memuat variabel statis (pembuka, pengantar, penutup) dan **Dynamic Placeholders** (contoh: `{{MONTH_YEAR}}`, `{{EXEC_SUMMARY}}`, `{{SECTION_SYSTEM_APP}}`, `{{SECTION_SERVICE_APP}}`).
3. AI tidak menghasilkan teks *raw formatting*; AI menghasilkan **Intermediate Representation (IR) berbasis JSON**, yang kemudian diterjemahkan oleh *backend* menjadi perintah `batchUpdate` pada **Google Docs API** (mengisikan teks pada indeks yang tepat, menerapkan *style heading*, dan memasukkan *bullet points* secara natif).



---

## 2. Arsitektur & Spesifikasi Pipeline per Tahapan (Step-by-Step)

Sistem dibangun menggunakan stateful graph orchestrator (**LangGraph**) untuk mengelola alur kerja dan penghentian sementara (*checkpoint pause*) saat tahap **Human-in-the-Loop (HITL)**.

### Tahap 1: Ingesti & Filter Data GitLab

* **Input User:** Rentang waktu (tanggal awal & akhir) atau pilihan Bulan/Tahun via Frontend.
* **Proses Integrasi:**
* Sistem memanggil **GitLab REST API v4** (`/projects/:id/repository/commits?since=X&until=Y&with_stats=true`).
* **Data Normalization & Cleaning:**
* Menghapus *commit noise* (misal: commit *merge request default message*, *bump version*, atau *typo fix* sederhana yang tidak relevan untuk laporan bisnis).
* Ekstraksi metadata: `short_id`, `author_name`, `committed_date`, `title` (commit subject), `message` (commit body), dan statistik file yang berubah (`stats.additions`, `stats.deletions`).





### Tahap 2: Klasifikasi Level 1 — *Sistem Aplikasi vs. Layanan Aplikasi*

* **Tujuan:** Memisahkan *commit* ke dalam 2 domain utama.
* **Sistem Aplikasi (Application System):** Perubahan fitur, UI/UX, *business logic*, perbaikan *bug* aplikasi, optimalisasi kueri DB.
* **Layanan Aplikasi (Application Service / Ops / Infra):** Deployment script, konfigurasi Docker/CI-CD, perubahan SSL/kredensial, *infrastructure scaling*, konfigurasi *web server/proxy*.


* **Implementasi Teknis:**
* Batch pemrosesan menggunakan LLM dengan **Structured Output / Function Calling**.
* Keluaran dijamin dalam skema JSON berindeks *commit ID*.



### Tahap 3: Human-in-the-Loop (HITL) Checkpoint 1

* **Alur:** Graph eksekusi LangGraph memasuki *state pause*.
* **Antarmuka UI:** Web UI menampilkan daftar *commit* dalam 2 kolom/tab (Sistem vs Layanan).
* **Aksi User:** User dapat menggeser (*drag-and-drop*) atau mengklik tombol pindah jika ada *commit* yang salah klasifikasi oleh AI, lalu menekan **"Approve & Continue"**.

### Tahap 4: Klasifikasi Level 2 & Semantic Clustering

* **Tujuan:** Mengelompokkan *commit* berdasarkan **Conventional Commits** (`feat`, `fix`, `ui`, `chore`, `refactor`, `perf`, `docs`) **DAN** mengelompokkan *commit-commit* yang relevan menjadi satu kesatuan fitur (*Semantic Clustering*).
* **Mengapa Clustering Penting?** 5 commit seperti *“feat(auth): add login button”*, *“fix(auth): fix padding on login”*, dan *“feat(auth): connect login API”* harus digabungkan menjadi **satu item narasi laporan**, bukan 3 baris terpisah.
* **Implementasi Teknis:**
1. **Rule-Based Pre-parsing:** Regex untuk menangkap *type* dan *scope* pada *Conventional Commits* (`type(scope): subject`).
2. **Vector Embedding & Clustering:** Menggunakan *Embedding Model* (`text-embedding-3-small` / Gemini Embedding) untuk mengukur *cosine similarity* antar pesan commit di bawah *scope/type* yang sama, digabungkan ke dalam **Commit Clusters**.



### Tahap 5: Human-in-the-Loop (HITL) Checkpoint 2

* **Alur:** Graph eksekusi pause kembali.
* **Antarmuka UI:** Menampilkan *tree-view*:
* Kategori Utama -> Sub-kategori (Fitur, Bug Fix, UI, Refactor) -> Cluster Fitur -> Anggota *commit*.


* **Aksi User:** User dapat memodifikasi nama cluster, menggabungkan (*merge*), atau memisahkan (*unmerge*) commit dari kelompoknya, kemudian klik **"Approve & Generate Content"**.

### Tahap 6: Sintesis Executive Summary & Sub-Judul

* **Tujuan:** Menghasilkan gambaran umum (*high-level executive summary*) bulan berjalan dan menentukan struktur **Heading 2 / Heading 3** secara dinamis.
* **Implementasi Teknis:**
* LLM menerima metadata keseluruhan cluster (jumlah fitur baru, bug kritis yang diselesaikan, peningkatan performa).
* LLM menyusun narasi 2–3 paragraf eksekutif untuk bagian awal sebelum masuk ke rincian per kategori.
* Struktur Sub-judul dihasilkan sesuai hierarki:
* `Heading 1`: Laporan Aktivitas Pengembangan - [Bulan Tahun]
* `Heading 2`: 1. Perbaikan dan Pengembangan Sistem Aplikasi
* `Heading 3`: 1.1. Pengembangan Fitur dan Antarmuka Baru (`feat`, `ui`)
* `Heading 3`: 1.2. Resolusi Bug dan Pemeliharaan (`fix`, `refactor`)
* `Heading 2`: 2. Pemeliharaan Layanan dan Infrastruktur Aplikasi (`chore`, `ops`)





### Tahap 7: Iterasi Narasi Detail (Tech-to-Business Translation) & Visual Placeholder

* **Tujuan:** Mengubah jargon teknis *git commit* menjadi bahasa bisnis formal yang dimengerti oleh pemangku kepentingan non-teknis, serta menandai kebutuhan dokumentasi visual.
* **Implementasi Teknis (Iterative Graph Node):**
* LLM memproses tiap **Commit Cluster** secara individual/batch kecil dengan instruksi (*System Prompt*):
* *Dilarang* menggunakan nama fungsi, variabel, atau parameter teknis mentah kecuali istilah bisnis standar.
* *Fokus* pada **apa yang diubah**, **mengapa diubah**, dan **apa dampaknya bagi pengguna/sistem**.


* **Visual Need Detector:** LLM mengevaluasi apakah perubahan fitur/UI/alur sistem cukup kompleks. Jika "Ya", LLM secara otomatis menyisipkan objek penanda gambar.



#### Contoh Transformasi Narasi (Input vs Output):

* **Input Commit Cluster:**
* `feat(checkout): add debounce 500ms on qty increment`
* `fix(checkout): prevent race condition on stock lock API`


* **Output AI (Bahasa Non-Teknis + Placeholder):**
> **Peningkatan Stabilitas Proses Checkout dan Pemesanan**
> Telah dilakukan penyempurnaan pada halaman keranjang belanja untuk mencegah pemrosesan ganda akibat klik yang terlalu cepat oleh pengguna. Selain itu, sistem manajemen stok barang kini telah diperbarui agar lebih akurat dalam mengunci jumlah item saat proses transaksi berlangsung, sehingga menghilangkan risiko barang terjual melebihi stok yang tersedia (*overselling*).
> `[TAMBAHKAN GAMBAR/CODE - Keterangan: Tangkapan layar antarmuka keranjang belanja saat pengguna memperbarui jumlah barang]`



### Tahap 8: Google Docs Document Composition & Rendering

* **Proses Backend:**
1. Backend menyalin (*make a copy*) Template Master Google Docs menjadi dokumen baru: `"Laporan Bulanan IT - <Bulan> <Tahun>"`.
2. Backend memetakan skema JSON hasil keluaran LLM menjadi urutan instruksi `batchUpdate` Google Docs API:
* `replaceAllText`: Untuk mengganti placeholder statis (`{{MONTH_YEAR}}`, `{{EXEC_SUMMARY}}`).
* `insertText` + `updateTextStyle` + `updateParagraphStyle`: Untuk menyisipkan Sub-judul (menerapkan *style* `HEADING_2`, `HEADING_3`).
* `createParagraphBullets`: Untuk menyisipkan rincian *item* pesanan/daftar secara *bulleted list* (counted/uncounted order).
* `updateTextStyle` (Highlight/Color): Untuk memberi warna latar belakang abu-abu muda atau kuning pada teks `[TAMBAHKAN GAMBAR/CODE - Keterangan: ...]` agar mudah terlihat oleh *user* saat review akhir di Google Docs.


3. Backend mengembalikan URL Google Docs yang sudah siap diedit kepada user.



---

## 3. Desain Skema Data (Structured Schema / Pydantic)

Untuk menjamin AI tidak halusinasi format, node klasifikasi dan pembuatan narasi **wajib** menggunakan validasi skema JSON berikut:

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class CommitItem(BaseModel):
    commit_id: str
    short_id: str
    original_message: str

class ContentCluster(BaseModel):
    cluster_title: str = Field(..., description="Judul tema cluster pendek (maks 5 kata)")
    commit_ids: List[str]
    category_level_1: Literal["SYSTEM_APP", "SERVICE_APP"]
    category_level_2: Literal["FEATURE_UI", "BUG_FIX", "REFACTOR_PERF", "INFRA_CHORE"]
    business_narrative: str = Field(..., description="Narasi detail bahasa formal non-teknis")
    requires_visual: bool = Field(default=False)
    visual_placeholder_note: Optional[str] = Field(
        default=None, 
        description="Instruksi untuk gambar jika requires_visual = True"
    )

class MonthlyReportSchema(BaseModel):
    month_year: str
    executive_summary: str
    system_app_narratives: List[ContentCluster]
    service_app_narratives: List[ContentCluster]

```

---

## 4. Desain System Prompt (Tahap 7: Narrative Translator)

```text
Anda adalah Technical Writer & Business Analyst Senior di perusahaan enterprise.
Tugas Anda adalah menerjemahkan kelompok pesan git commit (Conventional Commits) 
menjadi laporan progres teknis yang mudah dipahami oleh manajemen eksekutif non-teknis.

ATURAN PENULISAN:
1. Gunakan Bahasa Indonesia formal yang profesional, baku, dan jelas.
2. DILARANG KERING / TERLALU SINGKAT: Jangan menulis seperti changelog atau bullet point pendek. 
   Tuliskan dalam paragraf naratif utuh atau deskripsi mendalam yang menjelaskan konteks masalah, 
   solusi yang diimplementasikan, serta manfaat operasionalnya.
3. HINDARI JARGON TEKNIS MENTAH:
   - Jangan gunakan: "Refactor function get_user_token()", "Fix null pointer exception di table orders", "Bump axios to v1.6".
   - Gunakan kalimat bisnis: "Pembaruan arsitektur keamanan pada sistem autentikasi pengguna...", 
     "Perbaikan kesalahan pembacaan data pada tabel pesanan...", "Pembaruan komponen pustaka jaringan...".
4. VISUAL PLACEHOLDER:
   Jika perubahan melibatkan antarmuka pengguna (UI), alur transaksi baru, atau perubahan arsitektur kompleks,
   set variabel requires_visual = true dan berikan panduan screenshot yang tepat pada 'visual_placeholder_note'.

```

---

## 5. Rekomendasi Stack Teknologi (*Production-Ready*)

| Lapisan (Layer) | Teknologi Rekomendasi | Alasan Pemilihan |
| --- | --- | --- |
| **LLM Engine** | **gemini-3.5-flash** | Kualitas penalaran tertinggi untuk *text-rewriting*, instruksi kompleks, dan *Structured Outputs* yang sangat diandalkan. |
| **Orchestrator** | **LangGraph (Python)** | Mengelola *graph pipeline* kompleks dengan status persisten (*stateful persistence* / checkpoint SQLite/Postgres) untuk interupsi **Human-in-the-Loop**. |
| **API Backend** | **FastAPI** | Asinkronus; ekstraksi ratusan git commit dan agregasi LLM dapat memakan waktu 15–40 detik, harus dijalankan di *background task*. |
| **Vector Engine** | **pgvector (Postgres)** | Penyimpanan *embedding default* apabila ingin mengelompokkan commit berulang atau mencari referensi riwayat laporan bulan sebelumnya. |
| **Frontend UI** | **Next.js (React) + TailwindCSS** | Mudah untuk membangun *table UI* drag-and-drop / review HITL sebelum menembak generator dokumen. |
| **Integration** | **Google-API-Python-Client (Docs API v1)** | Autentikasi menggunakan **Google Cloud Service Account** atau **OAuth 2.0 User Token** untuk otomatisasi penulisan `.gdoc`. |

---

## 6. Mitigasi Risiko & *Engineering Guardrails*

1. **Risiko: *Google Docs Quota Limit / Rate Limiting***
* *Mitigasi:* Jika sistem mengirim 100 commit dalam 100 request `batchUpdate` terpisah, API akan terkena *limit* (`429 Too Many Requests`). Sistem harus merangkum seluruh perubahan hierarki dokumen ke dalam **satu *array* *payload* `batchUpdate` besar** (1 kali HTTP request ke Google API).


2. **Risiko: *Noise & Over-clustering***
* *Mitigasi:* Commit dari *author* dengan nama mesin/bot (misal: `gitlab-ci[bot]`, `dependabot`) secara otomatis didrop di level *ingestion filter* agar tidak mengonsumsi token LLM.


3. **Risiko: *Tone drift* (Gaya bahasa berubah-ubah antar bulan)**
* *Mitigasi:* Sistem menyimpan *style guide dictionary* kecil dan contoh narasi terbaik (*golden sample*) dari 7 dokumen MS Word acuan sebelumnya di dalam *system prompt* sebagai demonstrasi *few-shot*.


4. **Risiko: Keamanan Data Codebase (GitLab Commit Messages)**
* *Mitigasi:* Jika kebijakan kantor melarang commit message dikirim ke API publik, gunakan konfigurasi **Azure OpenAI Service** (enterprise SLA - no data retention) atau deploy LLM *open-weight* berskala besar secara lokal (contoh: **Llama 3.3 70B Instruct** menggunakan vLLM/Ollama pada server *on-premise*).



---