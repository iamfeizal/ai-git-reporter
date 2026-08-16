from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.gitlab_service import GitLabService
from app.core.database import engine, get_db, Base
from app.core.workflow import app_workflow
from app.core.state import CommitData
from app.services.gdocs_service import GDocsService
from app.routers import config_router
from app.models.config_models import GitLabInstance
from app.schemas.config_schemas import GenerateReportRequest

# Create DB Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Report System API")
gitlab_service = GitLabService()
gdocs_service = GDocsService()

app.include_router(config_router.router)
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
    try:
        instance = db.query(GitLabInstance).filter(GitLabInstance.id == req.instance_id).first()
        if not instance:
            raise HTTPException(status_code=404, detail="GitLab instance not found")
            
        raw_gitlab_data = gitlab_service.get_commits(instance.gitlab_url, instance.token, req.project_id, req.start_date, req.end_date)
        
        commits_for_ai = [
            CommitData(
                id=c["short_id"], 
                message=f"{c['title']} - {c.get('message', '')}"
            ) 
            for c in raw_gitlab_data
        ]
        
        if not commits_for_ai:
            return {
                "status": "warning",
                "message": "Tidak ada commit ditemukan pada rentang tanggal tersebut.",
                "total_clusters": 0
            }
        
        initial_state = {
            "raw_commits": commits_for_ai,
            "classified_commits": [],
            "final_clusters": []
        }
        
        print(f"Menjalankan Pipeline untuk {len(commits_for_ai)} commit...")
        # invoke() akan menjalankan graph dari START sampai END
        result_state = app_workflow.invoke(initial_state)
        
        print("Mengekspor laporan ke Google Docs...")
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