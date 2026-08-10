# 🤖 AI Git Reporter (Commit-to-Docs AI Agent)

An enterprise-grade, stateful AI agent that automates the generation of monthly technical reports. It ingests raw commits from GitLab, categorizes them, groups them into semantic features, generates professional business narratives using Large Language Models (LLM), and exports the final formatted report directly into Google Docs.

Built with **FastAPI**, **LangGraph**, **Google Gemini 3.5 Flash**, and **PostgreSQL (pgvector)**, fully containerized using **Docker**.

## 🌟 Key Features

- **Automated Data Ingestion:** Fetches commit histories seamlessly via the GitLab REST API.
- **Stateful AI Workflow (LangGraph):** Employs a multi-node LLM pipeline to filter out noise, classify commits (`SYSTEM_APP` vs `SERVICE_APP`), and cluster them semantically.
- **Tech-to-Business Translation:** Translates raw, technical git commits into formal, easy-to-understand business narratives tailored for stakeholders.
- **Google Docs Integration:** Uses Google Docs API (Batch Updates) to dynamically insert text, apply heading styles, and inject visual placeholders natively into a template document.
- **Dockerized Environment:** Hassle-free deployment with a pre-configured FastAPI backend and pgvector database.

## 🛠️ Tech Stack

- **Backend:** Python 3.11, FastAPI
- **AI / LLM:** Google Gemini 3.5 Flash, LangGraph, LangChain
- **Database:** PostgreSQL with `pgvector` extension
- **Integrations:** GitLab API v4, Google Docs API
- **Infrastructure:** Docker & Docker Compose

---

## 🚀 Getting Started (Initial Setup)

Follow these steps to run the system on your local machine or server.

### 1. Prerequisites

Before you begin, ensure you have the following installed and ready:

- **Docker & Docker Compose** installed on your machine.
- **GitLab Personal Access Token (PAT)** with `read_api` and `read_repository` permissions.
- **Gemini API Key** from Google AI Studio.
- **Google Cloud Service Account** (with a downloaded JSON key).

### 2. Clone the Repository

```bash
git clone [https://github.com/yourusername/ai-gitlab-reporter.git](https://github.com/yourusername/ai-gitlab-reporter.git)
cd ai-gitlab-reporter
```

### 3. Setup Environment Variables

Create a `.env` file in the root directory and configure it with your credentials:

```env
# GitLab Configuration
GITLAB_TOKEN=glpat-xxxxxxxxx_xxxxxxxxxx
GITLAB_URL=[https://gitlab.com](https://gitlab.com)
GITLAB_PROJECT_ID=1234567

# Gemini Configuration
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxx

# Google Docs Configuration
TARGET_DOC_ID=your_google_docs_document_id

# Database Configuration (Docker)
DATABASE_URL=postgresql://user:password@vectordb:5432/vectordb

```

### 4. Setup Google Docs Service Account

1. Rename your downloaded Google Cloud Service Account JSON file to `credentials.json`.
2. Place `credentials.json` in the root directory of this project.
3. Open your target Google Docs document in your browser.
4. Click **Share** and invite the Service Account Email (e.g., `service-name@project.iam.gserviceaccount.com`) as an **Editor**.
5. Copy the Document ID from the URL and paste it into the `TARGET_DOC_ID` in your `.env` file.

### 5. Run the Application (Docker)

Build and spin up the containers using Docker Compose:

```bash
docker compose up -d --build

```

_Note: This will download the necessary PostgreSQL and Python images, install dependencies, and start the FastAPI server._

### 6. Usage

Once the containers are running:

1. Open your web browser and navigate to: **`http://localhost:8000`**
2. You will see the AI Report Generator web interface.
3. Select your desired `Start Date` and `End Date`.
4. Click **Generate**. The AI will process the commits and automatically write the summarized business report directly into your Google Docs document!

## 🛑 Stopping the Application

To safely stop the application and database containers:

```bash
docker compose down

```

_(Your vector database data is preserved safely in Docker volumes)._
