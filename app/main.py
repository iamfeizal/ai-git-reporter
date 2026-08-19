from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from app.services.gitlab_service import GitLabService
from app.core.database import engine, get_db, Base, init_db
from app.core.workflow import app_workflow
from app.core.state import NormalizedCommit
from app.models.config_models import Base, LLMConfig, GitLabInstance
from app.models.embedding_models import CommitEmbedding
from app.routers import config_router, workflow_router
from app.core.logger import logger
from app.schemas.config_schemas import GenerateReportRequest

# Pastikan tabel terbuat (Note: Sebaiknya gunakan Alembic untuk production migration)
init_db()

app = FastAPI(title="AI Report System API")
gitlab_service = GitLabService()
gdocs_service = GDocsService()

# CORS middleware (needed for Vite dev server on different port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(config_router.router)
app.include_router(workflow_router.router)

# Serve static files (legacy Alpine.js frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/api/test-gitlab")
def test_gitlab(instance_id: int, project_id: str, start_date: str, end_date: str, db: Session = Depends(get_db)):
    try:
        instance = db.query(GitLabInstance).filter(GitLabInstance.id == instance_id).first()
        if not instance:
            raise HTTPException(status_code=404, detail="GitLab instance not found")
            
        commits = gitlab_service.get_commits(instance.gitlab_url, instance.token, project_id, start_date, end_date)
        sample_commits = [
            {
                "short_id": c.get("short_id"),
                "title": c.get("title"),
                "author_name": c.get("author_name"),
                "committed_date": c.get("committed_date") or c.get("created_at"),
            }
            for c in commits[:5]
        ]
        return {
            "status": "success",
            "total_commits": len(commits),
            "sample_commits": sample_commits
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/test-db")
def test_db():
    try:
        # Mencoba koneksi ke database
        with engine.connect() as connection:
            # Uji query sederhana
            connection.execute(text("SELECT 1;"))
            
            if engine.dialect.name == "postgresql":
                # Aktifkan ekstensi pgvector jika belum aktif
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                connection.commit()
                msg = "Berhasil terhubung ke Database PostgreSQL dan ekstensi pgvector aktif!"
            else:
                msg = f"Berhasil terhubung ke Database ({engine.dialect.name})!"
            
            return {
                "status": "success", 
                "message": msg
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

@app.post("/api/generate-report/full-pipeline")
def generate_report_full(req: GenerateReportRequest, db: Session = Depends(get_db)):
    """
    Legacy endpoint: runs the full pipeline without HITL pauses.
    Uses the simple compiled workflow (no checkpointer).
    
    For the HITL workflow, use POST /api/workflow/start instead.
    """
    try:
        instance = db.query(GitLabInstance).filter(GitLabInstance.id == req.instance_id).first()
        if not instance:
            raise HTTPException(status_code=404, detail="GitLab instance not found")
        
        # Use new normalized commit pipeline
        normalized_commits = gitlab_service.get_normalized_commits(
            url=instance.gitlab_url,
            token=instance.token,
            project_id=req.project_id,
            start_date=req.start_date,
            end_date=req.end_date,
            filter_noise=True,
        )
        
        if not normalized_commits:
            return {
                "status": "warning",
                "message": "Tidak ada commit ditemukan pada rentang tanggal tersebut.",
                "total_clusters": 0
            }
        
        initial_state = {
            "month_year": "",
            "raw_commits": normalized_commits,
            "classified_commits": [],
            "hitl_1_approved": False,
            "l2_classified": [],
            "clusters": [],
            "hitl_2_approved": False,
            "executive_summary": "",
            "final_clusters": [],
            "document_url": "",
        }
        
        logger.info(f"Menjalankan Pipeline untuk {len(normalized_commits)} commit...")
        # invoke() akan menjalankan graph dari START sampai END
        result_state = app_workflow.invoke(initial_state)
        
        logger.info("Mengekspor laporan ke Google Docs...")
        final_clusters = result_state["final_clusters"]
        if final_clusters:
            gdocs_service.write_report_to_docs(final_clusters, req.target_doc_id)
        
        return {
            "status": "success",
            "message": "Laporan berhasil di-generate dan ditulis ke Google Docs!",
            "total_clusters": len(final_clusters)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))