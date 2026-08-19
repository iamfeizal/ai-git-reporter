# 🤖 AI Git Reporter (Commit-to-Docs AI Agent)

An enterprise-grade, stateful AI agent that automates the generation of monthly technical reports. It ingests raw commits from GitLab, categorizes them, groups them into semantic features, generates professional business narratives using Large Language Models (LLM) with Few-Shot In-Context Learning (ICL), and exports the final formatted report directly into Google Docs.

Built with **FastAPI**, **LangGraph**, **Google Gemini 3.5**, **Vite + React**, and **PostgreSQL (pgvector)**, and is fully containerized using **Docker**.

## 🌟 Key Features

- **Automated Data Ingestion & Filtering:** Fetches commit histories via the GitLab REST API, with built-in pagination, Conventional Commits parsing, and noise filtering (e.g., bot commits).
- **Human-in-the-Loop (HITL) Workflow:** A 6-step interactive React UI that allows you to review data at critical checkpoints:
  - **L1 Review:** Drag-and-drop dual-column interface to classify commits between `SYSTEM_APP` and `SERVICE_APP`.
  - **L2 Review:** Tree-view cluster editor to rename, merge, or delete AI-generated semantic clusters before narrative generation.
- **Stateful AI Pipeline (LangGraph):** Employs a multi-node LLM DAG pipeline running on a persistent state, using PostgresSaver to pause execution for human review and resume exactly where it left off.
- **Tech-to-Business Translation (Few-Shot ICL):** Translates raw, technical git commits into formal, easy-to-understand business narratives. The system uses extracted Golden Samples for Few-Shot In-Context Learning to perfectly mimic your preferred writing style.
- **Google Docs Rendering:** Uses the Google Docs and Drive APIs to dynamically create a master template (or copy an existing one), insert text with proper heading/bullet list formatting, and apply visual highlights for screenshot placeholders.
- **Premium User Interface:** A modern, dark-themed frontend built with Vite, React, and glassmorphism design principles.

## 🛠️ Tech Stack

- **Frontend:** React, Vite, Vanilla CSS
- **Backend:** Python 3.11, FastAPI
- **AI / Agentic Workflow:** Google Gemini, LangGraph, LangChain, Tenacity (Resiliency)
- **Database:** PostgreSQL with `pgvector` extension, SQLAlchemy
- **Integrations:** GitLab API v4, Google Docs API
- **Infrastructure:** Docker, Docker Compose, Makefile

---

## 🚀 Getting Started (Initial Setup)

Follow these steps to run the system on your local machine or server.

### 1. Prerequisites

Before you begin, ensure you have the following installed and ready:

- **Docker & Docker Compose** installed on your machine.
- **GitLab Personal Access Token (PAT)** with `read_api` and `read_repository` permissions.
- **Gemini API Key** from Google AI Studio.
- **Google Cloud Service Account** (with a downloaded JSON key) with Docs and Drive API enabled.
- **Node.js** (if running the frontend locally without Docker).

### 2. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-gitlab-reporter.git
cd ai-gitlab-reporter
```

### 3. Setup Environment Variables

Create a `.env` file in the root directory and configure it with your credentials:

```env
# Database Configuration (Docker)
DATABASE_URL=postgresql://user:password@vectordb:5432/vectordb

# Optional: Pre-configured API Keys (Can also be set in the UI)
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxx
GITLAB_TOKEN=glpat-xxxxxxxxx_xxxxxxxxxx
GITLAB_URL=https://gitlab.com

# Optional: Specific Template Document ID
GDOCS_TEMPLATE_ID=your_google_docs_template_id
```

### 4. Setup Google Docs Service Account

1. Rename your downloaded Google Cloud Service Account JSON file to `credentials.json`.
2. Place `credentials.json` in the root directory of this project.
3. If using an existing `GDOCS_TEMPLATE_ID`, open your template document, click **Share**, and invite the Service Account Email (e.g., `service-name@project.iam.gserviceaccount.com`) as an **Editor**.

### 5. Run the Application

You can use the provided `Makefile` to easily run the application.

#### Option A: Using Docker (Backend + DB) and Local Frontend (Recommended for Dev)

**Terminal 1 (Backend & Database):**
```bash
# Starts PostgreSQL (pgvector) and the FastAPI backend
make docker-up
```

**Terminal 2 (Frontend):**
```bash
# Starts the Vite + React frontend server
make frontend-dev
```

#### Option B: Running Entirely Locally (Without Docker)

You can run the application directly using Anaconda/Miniconda or a standard virtual environment. If `DATABASE_URL` is omitted, the system will fallback to an internal SQLite database (Note: `pgvector` embedding storage requires PostgreSQL).

**Terminal 1 (Backend):**
```bash
conda activate reporter_env
# Or standard venv: source venv/bin/activate

pip install -r requirements.txt
make run
```

**Terminal 2 (Frontend):**
```bash
make frontend-dev
```

### 6. Usage

Once the servers are running:

1. Open your web browser and navigate to: **`http://localhost:5173`**
2. **Setup Step**: Enter your GitLab credentials, Gemini API key, and select the target project.
3. **Data Check**: Choose the date range. The system will fetch, parse, and filter your commits.
4. **L1 Review**: Review the AI's classification of `SYSTEM_APP` vs `SERVICE_APP`. Drag and drop commits to correct any misclassifications.
5. **L2 Review**: Review the semantic clusters generated via `text-embedding-004`. Use the tree-view editor to rename or reorganize clusters.
6. **Generate**: The AI will generate the executive summary and business narratives using Few-Shot ICL.
7. **Result**: Click the generated Google Docs link to view your fully formatted monthly report!

## 🛑 Stopping the Application

To safely stop the application and database containers:

```bash
make docker-down
```

*(Your vector database data and system configurations are preserved safely in Docker volumes and local SQLite files).*
