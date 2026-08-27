# 🤖 AI Git Reporter (Super App Edition)

An enterprise-grade, stateful AI agent that automates the generation of monthly technical reports from GitLab repository activity to Google Docs. Designed specifically for **Super App** and multi-module architectures, it leverages **LangGraph**, **Gemini 2.5/3.5**, **4-Level Granular Semantic Sub-Clustering**, and **Human-in-the-Loop (HITL) Checkpoints with full CRUD capabilities**.

Built with **FastAPI**, **LangGraph**, **Google Gemini**, **Vite + React**, and **PostgreSQL (pgvector)**, containerized with **Docker**.

---

## 🌟 Key Features

- **Automated Ingestion & Noise Filtering:** Fetches commit histories via GitLab REST API v4, with built-in Conventional Commits parsing, scope extraction, and automated noise filtering (e.g., bot commits, merge requests, version bumps).
- **Super App Sub-Domain Auto-Detection:** Automatically extracts sub-domains (e.g., *Layanan Presensi*, *Layanan Pembayaran*, *Layanan Helpdesk*) from commit scopes and directory paths.
- **HITL Checkpoint 1 (L1 Domain & Sub-Domain CRUD):**
  - Interactive dual-column interface to classify commits between **Sistem Inti Aplikasi (Core Platform)** and **Layanan Aplikasi (Super App Modules)**.
  - **Full CRUD on Sub-Domains:** Create new service modules, rename modules, delete modules with commit reassignment, and reorder priority.
- **4-Level Granular Semantic Sub-Clustering:**
  - Prevents broad/macro clustering by enforcing a strict 4-level hierarchy:
    `Domain / Sub-Domain` $\rightarrow$ `Conventional Category (feat, fix, refactor, chore)` $\rightarrow$ `Context Cluster (Modul)` $\rightarrow$ `Sub-Cluster Fungsional Spesifik (Feature Unit)` $\rightarrow$ `Commit Items`.
- **HITL Checkpoint 2 (L2 Tree Explorer & CRUD):**
  - **Commit CRUD:** Edit commit context/notes, move commits between sub-clusters, add manual tasks/offline hotfixes, and exclude commits.
  - **Sub-Cluster CRUD:** Add new sub-clusters, rename titles, split overcrowded sub-clusters into two, merge related sub-clusters, and delete.
- **Balanced Tech-to-Business Translation:**
  - Generates formal, professional Indonesian narratives suitable for executive management.
  - **Preserves Critical Technical Identifiers:** Retains original function names (e.g., `handleStockLock()`) and API endpoints (`/v1/orders`) formatted with **monospace code styling**, and important technologies/protocols (**OAuth 2.0**, **Redis**, **JWT**) in **bold**.
  - Automatically inserts highlight-styled visual placeholders `[TAMBAHKAN GAMBAR/DOKUMENTASI - Keterangan: ...]`.
- **Iterative Sub-Cluster Worker Loop & Google Docs Sync:**
  - Avoids single giant batch prompts by looping through sub-clusters individually.
  - Appends each sub-cluster section directly into Google Docs via `batchUpdate`, updates LangGraph checkpoints, and streams real-time progress events.
  - Full **fault-tolerance & resume capability** if network interruptions occur.

---

## 🛠️ Tech Stack

- **Frontend:** React, Vite, Vanilla CSS (Premium Dark Theme with Glassmorphism)
- **Backend:** Python 3.11, FastAPI, Uvicorn
- **Orchestration & AI:** LangGraph, LangChain Core, Google Gemini (2.5 / 3.5 Flash)
- **State Persistence:** PostgreSQL with `pgvector` & `PostgresSaver` (SQLite fallback for dev)
- **Integrations:** GitLab REST API v4, Google Docs API v1, Google Drive API v3
- **Infrastructure:** Docker, Docker Compose, Makefile

---

## 🚀 Getting Started

### 1. Prerequisites

- **Docker & Docker Compose** (or Python 3.11 with Conda/venv + Node.js 18+).
- **GitLab Personal Access Token (PAT)** with `read_api` and `read_repository` scopes.
- **Gemini API Key** from Google AI Studio.
- **Google Cloud Service Account (`credentials.json`)** with Docs and Drive API enabled.

### 2. Setup Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration (Docker)
DATABASE_URL=postgresql://user:password@localhost:5432/vectordb

# API Keys & Defaults
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxx
GITLAB_TOKEN=glpat-xxxxxxxxx_xxxxxxxxxx
GITLAB_URL=https://gitlab.com

# Optional: Master Google Docs Template ID
TARGET_DOC_ID=your_google_docs_template_id
```

### 3. Setup Google Docs Service Account

1. Place your Google Cloud Service Account JSON file as `credentials.json` in the root directory.
2. If using a master template doc (`TARGET_DOC_ID`), share the document with the `client_email` listed in `credentials.json` with **Editor** permissions.

### 4. Running the Application

#### Option A: Running with Conda Environment (`reporter_env`)

**Terminal 1 (Backend):**
```bash
conda activate reporter_env
pip install -r requirements.txt
make run
```

**Terminal 2 (Frontend):**
```bash
make frontend-dev
```

#### Option B: Running with Docker (Backend & Database)

```bash
make docker-up
```

---

## 📖 Step-by-Step Workflow

1. **Setup & Config (`http://localhost:5173`)**: Input GitLab token, select project, and set the target report month.
2. **Data Ingestion**: System fetches git commits, strips bot noise, and pre-parses Conventional Commits (`type`, `scope`, `subject`).
3. **HITL Checkpoint 1 (Domain & Sub-Domain Review)**:
   - Review AI classification: **Sistem Inti Aplikasi** vs **Layanan Aplikasi**.
   - Manage Super App modules (Add new sub-domain, rename, or reassign commits).
4. **HITL Checkpoint 2 (4-Level Tree & Sub-Cluster Review)**:
   - Review granular sub-clusters under each conventional commit category.
   - Perform CRUD: Edit/rename titles, split overcrowded sub-clusters, add manual tasks, or move commits.
5. **Executive Summary & Looping Generation**:
   - AI generates a high-level 2-3 paragraph executive summary.
   - Looping worker generates balanced narratives per sub-cluster and streams updates directly to Google Docs.
6. **Final Result**: Open the generated Google Docs report URL with all headings, monospace code identifiers, and visual placeholders pre-rendered!

---

## 🧪 Developer Utilities & Scratch Scripts (`scratch/`)

The [`scratch/`](file:///Users/imamaf/Development/Personal/ai-reporter/scratch) folder contains standalone utility scripts for verification, smoke testing, and sample analysis:

```
scratch/
├── test_workflow_graph.py   # StateGraph & Pydantic model integrity verification
├── test_gdocs_copy.py       # Google Drive API & template cloning smoke test
└── inspect_docx.py          # Reference .docx sample reader & formatting inspector
```

### 1. Test LangGraph Workflow & State Models
Verifies that all Pydantic state models (`ServiceSubDomain`, `ContextCluster`, `SubClusterItem`, `SubClusterNarrationOutput`) and LangGraph StateGraph DAG compile correctly:

```bash
conda run -n reporter_env python scratch/test_workflow_graph.py
```
*Output:*
```
Testing models...
Models verified successfully!
Testing graph compilation...
LangGraph workflow compiled successfully!
All checks passed!
```

### 2. Test Google Drive & Docs Integration
Smoke tests authentication using `credentials.json` and verifies permissions to copy/modify the template document:

```bash
conda run -n reporter_env python scratch/test_gdocs_copy.py
```

### 3. Inspect Reference Sample Documents
Reads and inspects paragraph hierarchies and styles from sample `.docx` golden files in `sample_data/`:

```bash
conda run -n reporter_env python scratch/inspect_docx.py
```

---

## 🛑 Stopping the Application

To stop all background services and containers:

```bash
make docker-down
```
