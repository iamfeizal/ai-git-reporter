from typing import TypedDict, List, Optional, Literal, Annotated
from pydantic import BaseModel, Field

# -------------------------------------------------------------------
# 1. Normalized Commit Data (from GitLab ingestion, post-filter)
# -------------------------------------------------------------------
class NormalizedCommit(BaseModel):
    """Full normalized commit data from GitLab, after noise filtering."""
    short_id: str
    title: str = Field(description="First line of commit message (subject)")
    message: str = Field(default="", description="Full commit message body")
    author_name: str = Field(default="")
    committed_date: str = Field(default="")
    stats_additions: int = Field(default=0)
    stats_deletions: int = Field(default=0)
    # Parsed Conventional Commit fields (pre-parsed in ingestion)
    cc_type: Optional[str] = Field(None, description="Conventional Commit type (feat, fix, chore, etc.)")
    cc_scope: Optional[str] = Field(None, description="Conventional Commit scope")
    cc_subject: Optional[str] = Field(None, description="Conventional Commit subject")
    cc_is_conventional: bool = Field(default=False)


# -------------------------------------------------------------------
# 2. Backward-compat alias for existing workflow code
# -------------------------------------------------------------------
class CommitData(BaseModel):
    """Simplified commit data for LLM processing (backward compat)."""
    id: str
    message: str


# -------------------------------------------------------------------
# 3. Klasifikasi Level 1
# -------------------------------------------------------------------
class ClassifiedCommit(BaseModel):
    id: str
    category: str = Field(description="Harus bernilai 'SYSTEM_APP' atau 'SERVICE_APP'")
    reason: str = Field(description="Alasan singkat 1 kalimat kenapa masuk kategori tersebut")


class L1ClassificationResult(BaseModel):
    results: List[ClassifiedCommit]


# -------------------------------------------------------------------
# 4. Klasifikasi Level 2 & Clustering
# -------------------------------------------------------------------
class L2ClassifiedCommit(BaseModel):
    """Commit with both L1 and L2 classification."""
    id: str
    category_level_1: Literal["SYSTEM_APP", "SERVICE_APP"]
    category_level_2: Literal["FEATURE_UI", "BUG_FIX", "REFACTOR_PERF", "INFRA_CHORE"]
    reason: str = Field(description="Alasan sub-kategorisasi")


class L2ClassificationResult(BaseModel):
    results: List[L2ClassifiedCommit]


class CommitCluster(BaseModel):
    """A semantic cluster of related commits (before narration)."""
    cluster_title: str = Field(..., description="Judul tema cluster pendek (maks 5 kata)")
    commit_ids: List[str]
    category_level_1: Literal["SYSTEM_APP", "SERVICE_APP"]
    category_level_2: Literal["FEATURE_UI", "BUG_FIX", "REFACTOR_PERF", "INFRA_CHORE"]


class ClusteringResult(BaseModel):
    clusters: List[CommitCluster]


# -------------------------------------------------------------------
# 5. Content Cluster (post-narration, final output per cluster)
# -------------------------------------------------------------------
class ContentCluster(BaseModel):
    cluster_title: str = Field(..., description="Judul tema cluster pendek (maks 5 kata), misal: 'Pembaruan Modul Pembayaran'")
    commit_ids: List[str] = Field(..., description="Daftar ID commit yang masuk ke cluster ini")
    category_level_1: Literal["SYSTEM_APP", "SERVICE_APP"]
    category_level_2: Literal["FEATURE_UI", "BUG_FIX", "REFACTOR_PERF", "INFRA_CHORE"]
    business_narrative: str = Field(..., description="Narasi detail bahasa formal non-teknis, minimal 3 kalimat. Hindari jargon teknis mentah.")
    requires_visual: bool = Field(default=False)
    visual_placeholder_note: Optional[str] = Field(default=None, description="Instruksi gambar jika requires_visual = True")


class ClusterResult(BaseModel):
    """Legacy wrapper for backward compat."""
    clusters: List[ContentCluster]


# -------------------------------------------------------------------
# 6. Monthly Report Schema (full output, matches GUIDELINES §3)
# -------------------------------------------------------------------
class MonthlyReportSchema(BaseModel):
    month_year: str
    executive_summary: str = Field(..., description="Ringkasan eksekutif 2-3 paragraf")
    system_app_narratives: List[ContentCluster] = Field(default_factory=list)
    service_app_narratives: List[ContentCluster] = Field(default_factory=list)


# -------------------------------------------------------------------
# 7. LangGraph State — Full Pipeline State
# -------------------------------------------------------------------
class ReportState(TypedDict):
    # Input
    month_year: str
    raw_commits: List[NormalizedCommit]
    
    # Tahap 2: L1 Classification
    classified_commits: List[ClassifiedCommit]
    
    # HITL 1: User corrections applied
    hitl_1_approved: bool
    
    # Tahap 4: L2 Classification + Clustering
    l2_classified: List[L2ClassifiedCommit]
    clusters: List[CommitCluster]
    
    # HITL 2: User corrections applied
    hitl_2_approved: bool
    
    # Tahap 6: Executive Summary
    executive_summary: str
    
    # Tahap 7: Final narrated clusters
    final_clusters: List[ContentCluster]
    
    # Tahap 8: Document IR / Output
    document_url: str