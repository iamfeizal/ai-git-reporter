"""
State Models for AI Report System (Super App & LangGraph Stateful Workflow).
"""
from typing import TypedDict, List, Optional, Literal
from pydantic import BaseModel, Field


# -------------------------------------------------------------------
# 1. Normalized Commit Data
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
    # Parsed Conventional Commit fields
    cc_type: Optional[str] = Field(None, description="Conventional Commit type (feat, fix, chore, etc.)")
    cc_scope: Optional[str] = Field(None, description="Conventional Commit scope")
    cc_subject: Optional[str] = Field(None, description="Conventional Commit subject")
    cc_is_conventional: bool = Field(default=False)
    custom_note: Optional[str] = Field(default=None, description="Catatan modifikasi dari user")


# -------------------------------------------------------------------
# 2. Sub-Domain Layanan Aplikasi (Super App Modules)
# -------------------------------------------------------------------
class ServiceSubDomain(BaseModel):
    """Sub-domain representing an app/module/service within the Super App."""
    sub_domain_id: str = Field(..., description="Unique slug or identifier, e.g. 'presensi', 'pembayaran'")
    sub_domain_name: str = Field(..., description="Nama Layanan/Modul, e.g. 'Layanan Presensi Online'")
    description: Optional[str] = Field(default=None, description="Deskripsi singkat modul layanan")
    commit_ids: List[str] = Field(default_factory=list, description="List short_id commit yang masuk")


# -------------------------------------------------------------------
# 3. Klasifikasi Level 1
# -------------------------------------------------------------------
class ClassifiedCommit(BaseModel):
    id: str
    category: Literal["SYSTEM_CORE", "APP_SERVICE", "SYSTEM_APP", "SERVICE_APP"] = Field(
        default="SYSTEM_CORE",
        description="SYSTEM_CORE (Inti Sistem) atau APP_SERVICE (Layanan Aplikasi)"
    )
    sub_domain_id: Optional[str] = Field(default=None, description="ID sub-domain jika APP_SERVICE")
    sub_domain_name: Optional[str] = Field(default=None, description="Nama sub-domain jika APP_SERVICE")
    reason: str = Field(default="", description="Alasan singkat 1 kalimat")


class L1ClassificationResult(BaseModel):
    results: List[ClassifiedCommit]
    detected_sub_domains: List[ServiceSubDomain] = Field(default_factory=list)


# -------------------------------------------------------------------
# 4. Granular Semantic Sub-Clustering (4-Level Hierarchy)
# -------------------------------------------------------------------
class SubClusterItem(BaseModel):
    """Granular functional sub-cluster (specific user story / feature unit)."""
    sub_cluster_id: str = Field(..., description="ID unik sub-cluster")
    sub_cluster_title: str = Field(..., description="Judul tema fungsional spesifik (maks 8 kata)")
    functional_scope: str = Field(default="", description="Cakupan fungsi atau masalah spesifik")
    commit_ids: List[str] = Field(default_factory=list, description="Daftar commit short_id dalam sub-cluster")


class ContextCluster(BaseModel):
    """Cluster of related context/module under Conventional Commit categories."""
    cluster_id: str = Field(..., description="ID unik cluster konteks")
    cluster_title: str = Field(..., description="Judul Cluster Konteks Modul")
    category_level_1: Literal["SYSTEM_CORE", "APP_SERVICE", "SYSTEM_APP", "SERVICE_APP"] = "SYSTEM_CORE"
    sub_domain_id: Optional[str] = Field(default=None, description="ID sub-domain jika APP_SERVICE")
    category_level_2: Literal["FEATURE_UI", "BUG_FIX", "REFACTOR_PERF", "INFRA_CHORE"] = "FEATURE_UI"
    sub_clusters: List[SubClusterItem] = Field(default_factory=list)


# Backward-compat classes for legacy / test wrappers
class CommitCluster(BaseModel):
    cluster_title: str
    commit_ids: List[str]
    category_level_1: str = "SYSTEM_CORE"
    category_level_2: str = "FEATURE_UI"


class ContentCluster(BaseModel):
    cluster_title: str
    commit_ids: List[str]
    category_level_1: str = "SYSTEM_CORE"
    category_level_2: str = "FEATURE_UI"
    business_narrative: str
    requires_visual: bool = False
    visual_placeholder_note: Optional[str] = None


class ClusterResult(BaseModel):
    clusters: List[ContentCluster]


# -------------------------------------------------------------------
# 5. Narasi Detail Sub-Cluster (Balanced Tech-to-Business)
# -------------------------------------------------------------------
class SubClusterNarrationOutput(BaseModel):
    """Output generated for each sub-cluster during looping generation."""
    sub_cluster_id: str
    sub_cluster_title: str
    cluster_id: Optional[str] = None
    cluster_title: Optional[str] = None
    category_level_1: Optional[str] = None
    sub_domain_id: Optional[str] = None
    category_level_2: Optional[str] = None
    business_narrative: str = Field(
        ...,
        description="Narasi detail bahasa formal Indonesia yang seimbang, mempertahankan nama fungsi asli dan istilah kunci"
    )
    key_technical_terms_preserved: List[str] = Field(
        default_factory=list,
        description="Nama fungsi asli atau endpoint API yang dipertahankan dalam narasi"
    )
    requires_visual: bool = Field(default=False)
    visual_placeholder_note: Optional[str] = Field(default=None)
    commit_ids: List[str] = Field(default_factory=list)


# -------------------------------------------------------------------
# 6. LangGraph State — Full Pipeline State
# -------------------------------------------------------------------
class ReportState(TypedDict, total=False):
    # Input
    month_year: str
    gdocs_mode: str
    gdocs_document_id: str
    raw_commits: List[NormalizedCommit]

    # Tahap 2: L1 Classification & Sub-Domains
    service_sub_domains: List[ServiceSubDomain]
    classified_commits: List[ClassifiedCommit]

    # HITL 1: User corrections
    hitl_1_approved: bool

    # Tahap 4: Granular Sub-Clustering
    core_system_clusters: List[ContextCluster]
    service_app_clusters: List[ContextCluster]
    # Legacy alias for backward compat
    clusters: List[CommitCluster]

    # HITL 2: User corrections
    hitl_2_approved: bool

    # Tahap 6: Executive Summary
    executive_summary: str

    # Tahap 7 & 8: Looping Narratives & Docs Progress
    final_narratives: List[SubClusterNarrationOutput]
    # Legacy alias
    final_clusters: List[ContentCluster]
    completed_sub_cluster_ids: List[str]
    document_url: str
    progress_message: str