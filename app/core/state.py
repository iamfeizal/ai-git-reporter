from typing import TypedDict, List, Optional, Literal
from pydantic import BaseModel, Field

# 1. Struktur data untuk input commit
class CommitData(BaseModel):
    id: str
    message: str

# 2. Struktur data untuk hasil klasifikasi per commit
class ClassifiedCommit(BaseModel):
    id: str
    category: str = Field(description="Harus bernilai 'SYSTEM_APP' atau 'SERVICE_APP'")
    reason: str = Field(description="Alasan singkat 1 kalimat kenapa masuk kategori tersebut")

# 3. Struktur data balikan (output) dari AI
class L1ClassificationResult(BaseModel):
    results: List[ClassifiedCommit]

# 4. State keseluruhan graph LangGraph
class ContentCluster(BaseModel):
    cluster_title: str = Field(..., description="Judul tema cluster pendek (maks 5 kata), misal: 'Pembaruan Modul Pembayaran'")
    commit_ids: List[str] = Field(..., description="Daftar ID commit yang masuk ke cluster ini")
    category_level_1: Literal["SYSTEM_APP", "SERVICE_APP"]
    category_level_2: Literal["FEATURE_UI", "BUG_FIX", "REFACTOR_PERF", "INFRA_CHORE"]
    business_narrative: str = Field(..., description="Narasi detail bahasa formal non-teknis, minimal 3 kalimat. Hindari jargon teknis mentah.")
    requires_visual: bool = Field(default=False)
    visual_placeholder_note: Optional[str] = Field(default=None, description="Instruksi gambar jika requires_visual = True")

class ClusterResult(BaseModel):
    clusters: List[ContentCluster]

class ReportState(TypedDict):
    raw_commits: List[CommitData]
    classified_commits: List[ClassifiedCommit]
    final_clusters: List[ContentCluster]