from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text
from app.services.gitlab_service import GitLabService
from app.core.database import engine
from app.core.workflow import app_workflow
from app.core.state import CommitData
from app.services.gdocs_service import GDocsService

app = FastAPI(title="AI Report System API")
gitlab_service = GitLabService()
gdocs_service = GDocsService()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/api/test-gitlab")
def test_gitlab(start_date: str, end_date: str):
    try:
        commits = gitlab_service.get_commits(start_date, end_date)
        return {
            "status": "success",
            "total_commits": len(commits),
            "sample_commit": commits[0] if commits else None
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
            
            # Aktifkan ekstensi pgvector jika belum aktif
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            connection.commit()
            
            return {
                "status": "success", 
                "message": "Berhasil terhubung ke Database dan ekstensi pgvector aktif!"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

@app.post("/api/generate-report/full-pipeline")
def generate_report_full(start_date: str, end_date: str):
    try:
        raw_gitlab_data = gitlab_service.get_commits(start_date, end_date)
        
        commits_for_ai = [
            CommitData(
                id=c["short_id"], 
                message=f"{c['title']} - {c.get('message', '')}"
            ) 
            for c in raw_gitlab_data
        ]
        
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
            gdocs_service.write_report_to_docs(final_clusters)
        
        return {
            "status": "success",
            "message": "Laporan berhasil di-generate dan ditulis ke Google Docs!",
            "total_clusters": len(final_clusters)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))