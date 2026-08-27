"""
LangGraph Workflow — Multi-Node Stateful Pipeline for Super App Reporting System.

Pipeline:
  START → classify_l1 → [HITL_1 interrupt] → classify_l2_and_subcluster
        → [HITL_2 interrupt] → generate_summary → generate_narratives_and_docs_loop → END

Features:
- Sub-domain auto-detection & CRUD for Super App
- 4-Level Granular Semantic Sub-Clustering
- Balanced Tech-to-Business Translation
- Incremental Looping Sub-Cluster Worker to Google Docs
"""
import os
import uuid
from typing import List, Dict, Any, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.core.state import (
    ReportState,
    NormalizedCommit,
    ClassifiedCommit,
    L1ClassificationResult,
    ServiceSubDomain,
    SubClusterItem,
    ContextCluster,
    SubClusterNarrationOutput,
    CommitCluster,
    ContentCluster,
)
from app.services.llm_service import get_llm
from app.services.embedding_service import cluster_commits_by_similarity
from app.services.gdocs_service import GDocsService
from app.core.logger import logger


# =====================================================================
# NODE 1: Klasifikasi Level 1 — SYSTEM_CORE vs APP_SERVICE & Sub-Domains
# =====================================================================
def classify_l1_node(state: ReportState) -> dict:
    """
    Classify each commit into SYSTEM_CORE or APP_SERVICE.
    Automatically extracts sub-domains (modules/apps in Super App) for APP_SERVICE commits.
    """
    commits = state.get("raw_commits", [])
    if not commits:
        return {"classified_commits": [], "service_sub_domains": []}

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Anda adalah Senior Software Architect untuk ekosistem Super App.
Tugas Anda adalah mengklasifikasikan daftar git commit ke dalam 2 domain utama:
1. 'SYSTEM_CORE': Perubahan fondasi sistem inti bersama, core framework, global state, base UI kit / design system, middleware sentral, atau keamanan platform global.
2. 'APP_SERVICE': Seluruh modul bisnis, aplikasi, atau layanan spesifik yang berjalan di dalam Super App (contoh: Presensi, Pembayaran, Tiket Helpdesk, Pengadaan, Notifikasi, dsb).

Jika sebuah commit masuk ke 'APP_SERVICE':
- Tentukan 'sub_domain_id' berupa slug pendek (contoh: 'presensi', 'pembayaran', 'helpdesk', 'pengadaan', 'auth').
- Tentukan 'sub_domain_name' dalam bahasa Indonesia formal (contoh: 'Layanan Presensi Online', 'Layanan Pembayaran & Dompet Digital').

Buat juga daftar 'detected_sub_domains' unik yang memuat sub_domain_id, sub_domain_name, dan daftar commit ID yang masuk ke modul tersebut."""),
        ("user", "Data git commit (ID | Scope | Subject | Message):\n{commits_text}")
    ])

    llm = get_llm()
    structured_llm = llm.with_structured_output(L1ClassificationResult)
    chain = prompt | structured_llm

    commits_text = "\n".join([
        f"[{c.short_id}] (scope: {c.cc_scope or '-'}) {c.title}" + (f" | {c.message[:100]}" if c.message and c.message != c.title else "")
        for c in commits
    ])

    logger.info(f"[Node: classify_l1] Mengklasifikasikan {len(commits)} commit dan mendeteksi sub-domain...")
    try:
        response = chain.invoke({"commits_text": commits_text})
        results = response.results
        sub_domains = response.detected_sub_domains

        # If sub_domains list was empty or incomplete, aggregate from results
        if not sub_domains:
            sd_map: Dict[str, ServiceSubDomain] = {}
            for r in results:
                if r.category == "APP_SERVICE" and r.sub_domain_id:
                    sid = r.sub_domain_id.lower().strip()
                    sname = r.sub_domain_name or f"Layanan {sid.title()}"
                    if sid not in sd_map:
                        sd_map[sid] = ServiceSubDomain(sub_domain_id=sid, sub_domain_name=sname, commit_ids=[])
                    sd_map[sid].commit_ids.append(r.id)
            sub_domains = list(sd_map.values())

        return {
            "classified_commits": results,
            "service_sub_domains": sub_domains
        }
    except Exception as e:
        logger.error(f"[Node: classify_l1] Error during classification: {e}")
        # Fallback simple classification
        fallback_results = [
            ClassifiedCommit(
                id=c.short_id,
                category="APP_SERVICE" if c.cc_scope else "SYSTEM_CORE",
                sub_domain_id=c.cc_scope.lower() if c.cc_scope else None,
                sub_domain_name=f"Layanan {c.cc_scope.title()}" if c.cc_scope else None,
                reason="Auto fallback rule"
            )
            for c in commits
        ]
        return {"classified_commits": fallback_results, "service_sub_domains": []}


# =====================================================================
# NODE 2: HITL Checkpoint 1 — User reviews & CRUD on Sub-Domains
# =====================================================================
def hitl_checkpoint_1_node(state: ReportState) -> dict:
    """
    Human-in-the-Loop Checkpoint 1.
    Pauses execution and presents L1 classification & sub-domains for user review.
    Supports full CRUD on sub-domains and moving commits between domains.
    """
    classified = state.get("classified_commits", [])
    sub_domains = state.get("service_sub_domains", [])
    raw_commits = {c.short_id: c for c in state.get("raw_commits", [])}

    system_core = [c for c in classified if c.category in ("SYSTEM_CORE", "SYSTEM_APP")]
    service_app = [c for c in classified if c.category in ("APP_SERVICE", "SERVICE_APP")]

    user_response = interrupt({
        "type": "hitl_l1_review",
        "message": f"Review L1 & Sub-Domain Layanan: {len(system_core)} Sistem Inti, {len(service_app)} Layanan Aplikasi ({len(sub_domains)} sub-domain)",
        "system_core_commits": [
            {**c.model_dump(), "title": raw_commits.get(c.id, NormalizedCommit(short_id=c.id, title=c.id)).title}
            for c in system_core
        ],
        "service_app_commits": [
            {**c.model_dump(), "title": raw_commits.get(c.id, NormalizedCommit(short_id=c.id, title=c.id)).title}
            for c in service_app
        ],
        "service_sub_domains": [sd.model_dump() for sd in sub_domains],
    })

    if user_response and isinstance(user_response, dict):
        new_commits = user_response.get("corrected_commits")
        new_sub_domains = user_response.get("corrected_sub_domains")

        updates = {"hitl_1_approved": True}
        if new_commits is not None:
            updates["classified_commits"] = [ClassifiedCommit(**c) for c in new_commits]
        if new_sub_domains is not None:
            updates["service_sub_domains"] = [ServiceSubDomain(**sd) for sd in new_sub_domains]

        return updates

    return {"hitl_1_approved": True}


# =====================================================================
# NODE 3: Klasifikasi Level 2 & Granular Semantic Sub-Clustering
# =====================================================================
class GranularClusterOutput(BaseModel):
    clusters: List[ContextCluster]


def classify_l2_and_cluster_node(state: ReportState) -> dict:
    """
    4-Level Granular Semantic Sub-Clustering:
    1. Group commits by Domain/Sub-Domain & Conventional Category (FEATURE_UI, BUG_FIX, etc.)
    2. Group into ContextCluster (module/feature area)
    3. Break down into SubClusterItem (specific user stories / functional units)
    """
    raw_commits = state.get("raw_commits", [])
    classified = state.get("classified_commits", [])
    sub_domains = state.get("service_sub_domains", [])

    if not classified:
        return {"core_system_clusters": [], "service_app_clusters": [], "clusters": []}

    commit_dict = {c.short_id: c for c in raw_commits}
    classified_dict = {c.id: c for c in classified}

    # Group commits by Domain -> Sub-domain -> Conventional Type
    system_core_commits: List[NormalizedCommit] = []
    service_app_commits_by_subdomain: Dict[str, List[NormalizedCommit]] = {}

    for c in classified:
        nc = commit_dict.get(c.id)
        if not nc:
            continue
        if c.category in ("SYSTEM_CORE", "SYSTEM_APP"):
            system_core_commits.append(nc)
        else:
            sid = c.sub_domain_id or "general"
            service_app_commits_by_subdomain.setdefault(sid, []).append(nc)

    llm = get_llm()
    structured_llm = llm.with_structured_output(GranularClusterOutput)

    cluster_prompt_template = ChatPromptTemplate.from_messages([
        ("system", """Anda adalah Lead System Architect & Technical Writer.
Tugas Anda adalah mengelompokkan commit berikut ke dalam struktur **Granular Semantic Clustering**:
1. Tentukan sub-kategori Conventional Commits:
   - 'FEATURE_UI': Fitur baru, antarmuka, fungsionalitas pengguna.
   - 'BUG_FIX': Resolusi bug, penanganan error, perbaikan cacat sistem.
   - 'REFACTOR_PERF': Optimasi performa, refaktorisasi, restrukturisasi kode.
   - 'INFRA_CHORE': Infrastruktur, CI/CD, maintenance, script.
2. Kelompokkan ke dalam 'ContextCluster' (Area Konteks Modul).
3. PENTING: JANGAN buat pengelompokan yang terlalu lebar. Di dalam setiap 'ContextCluster', pecah commit menjadi 'sub_clusters' (SubClusterItem) fungsional spesifik (maksimal 3-5 commit per sub-cluster).
4. Berikan judul sub-cluster yang spesifik dan jelas (contoh: "Integrasi QRIS Dinamis & Penanganan Callback Webhook")."""),
        ("user", "Domain: {domain_context}\nDaftar Commit:\n{commits_list}\n\nHasilkan ContextCluster dan SubClusterItem:")
    ])

    chain = cluster_prompt_template | structured_llm

    core_clusters: List[ContextCluster] = []
    service_clusters: List[ContextCluster] = []

    # Process System Core commits
    if system_core_commits:
        commits_text = "\n".join([
            f"[{c.short_id}] (type: {c.cc_type or 'feat'}) {c.title}" + (f" | {c.message[:80]}" if c.message else "")
            for c in system_core_commits
        ])
        logger.info(f"[Node: classify_l2] Clustering {len(system_core_commits)} commit Sistem Inti...")
        try:
            res = chain.invoke({"domain_context": "Sistem Inti Aplikasi (Core Platform)", "commits_list": commits_text})
            for cl in res.clusters:
                cl.category_level_1 = "SYSTEM_CORE"
                core_clusters.append(cl)
        except Exception as e:
            logger.warning(f"Clustering error for core system: {e}")
            # Fallback single cluster
            core_clusters.append(ContextCluster(
                cluster_id=f"core-{uuid.uuid4().hex[:6]}",
                cluster_title="Pembaruan Fondasi Sistem Inti",
                category_level_1="SYSTEM_CORE",
                category_level_2="FEATURE_UI",
                sub_clusters=[SubClusterItem(
                    sub_cluster_id=f"sub-{uuid.uuid4().hex[:6]}",
                    sub_cluster_title="Pembaruan Komponen dan Fungsionalitas Inti",
                    commit_ids=[c.short_id for c in system_core_commits]
                )]
            ))

    # Process Service App commits per sub-domain
    for sid, scommits in service_app_commits_by_subdomain.items():
        sd_obj = next((s for s in sub_domains if s.sub_domain_id == sid), None)
        sd_name = sd_obj.sub_domain_name if sd_obj else f"Layanan {sid.title()}"

        commits_text = "\n".join([
            f"[{c.short_id}] (type: {c.cc_type or 'feat'}) {c.title}" + (f" | {c.message[:80]}" if c.message else "")
            for c in scommits
        ])
        logger.info(f"[Node: classify_l2] Clustering {len(scommits)} commit untuk {sd_name}...")
        try:
            res = chain.invoke({"domain_context": f"Layanan Aplikasi: {sd_name}", "commits_list": commits_text})
            for cl in res.clusters:
                cl.category_level_1 = "APP_SERVICE"
                cl.sub_domain_id = sid
                service_clusters.append(cl)
        except Exception as e:
            logger.warning(f"Clustering error for {sd_name}: {e}")
            service_clusters.append(ContextCluster(
                cluster_id=f"serv-{sid}-{uuid.uuid4().hex[:6]}",
                cluster_title=f"Aktivitas Pengembangan {sd_name}",
                category_level_1="APP_SERVICE",
                sub_domain_id=sid,
                category_level_2="FEATURE_UI",
                sub_clusters=[SubClusterItem(
                    sub_cluster_id=f"sub-{uuid.uuid4().hex[:6]}",
                    sub_cluster_title=f"Penyempurnaan Fitur pada {sd_name}",
                    commit_ids=[c.short_id for c in scommits]
                )]
            ))

    # Backward-compat clusters list
    legacy_clusters: List[CommitCluster] = []
    for c in core_clusters + service_clusters:
        for sc in c.sub_clusters:
            legacy_clusters.append(CommitCluster(
                cluster_title=sc.sub_cluster_title,
                commit_ids=sc.commit_ids,
                category_level_1=c.category_level_1,
                category_level_2=c.category_level_2
            ))

    return {
        "core_system_clusters": core_clusters,
        "service_app_clusters": service_clusters,
        "clusters": legacy_clusters
    }


# =====================================================================
# NODE 4: HITL Checkpoint 2 — User reviews & CRUD on Sub-Clusters
# =====================================================================
def hitl_checkpoint_2_node(state: ReportState) -> dict:
    """
    Human-in-the-Loop Checkpoint 2.
    Pauses execution and presents full 4-level tree for user review.
    Supports full CRUD on Commits and Sub-Clusters.
    """
    core_clusters = state.get("core_system_clusters", [])
    service_clusters = state.get("service_app_clusters", [])
    sub_domains = state.get("service_sub_domains", [])
    raw_commits = {c.short_id: c for c in state.get("raw_commits", [])}

    total_subclusters = sum(len(c.sub_clusters) for c in core_clusters + service_clusters)

    user_response = interrupt({
        "type": "hitl_l2_review",
        "message": f"Review Hierarki Sub-Cluster: {len(core_clusters)} Cluster Inti, {len(service_clusters)} Cluster Layanan ({total_subclusters} sub-cluster fungsional)",
        "core_system_clusters": [c.model_dump() for c in core_clusters],
        "service_app_clusters": [c.model_dump() for c in service_clusters],
        "service_sub_domains": [sd.model_dump() for sd in sub_domains],
        "raw_commits": {k: v.model_dump() for k, v in raw_commits.items()},
    })

    if user_response and isinstance(user_response, dict):
        new_core = user_response.get("corrected_core_clusters")
        new_service = user_response.get("corrected_service_clusters")

        updates = {"hitl_2_approved": True}
        if new_core is not None:
            updates["core_system_clusters"] = [ContextCluster(**c) for c in new_core]
        if new_service is not None:
            updates["service_app_clusters"] = [ContextCluster(**c) for c in new_service]

        return updates

    return {"hitl_2_approved": True}


# =====================================================================
# NODE 5: Executive Summary Generation
# =====================================================================
def generate_summary_node(state: ReportState) -> dict:
    """Generate a formal 2-3 paragraph executive summary of the Super App progress."""
    core_clusters = state.get("core_system_clusters", [])
    service_clusters = state.get("service_app_clusters", [])
    sub_domains = state.get("service_sub_domains", [])
    month_year = state.get("month_year", "")

    all_clusters = core_clusters + service_clusters
    if not all_clusters:
        return {"executive_summary": "Laporan aktivitas bulanan telah selesai disusun."}

    summary_items = []
    for c in core_clusters:
        for sc in c.sub_clusters:
            summary_items.append(f"- [Sistem Inti / {c.category_level_2}] {sc.sub_cluster_title} ({len(sc.commit_ids)} commit)")

    for c in service_clusters:
        sd = next((s for s in sub_domains if s.sub_domain_id == c.sub_domain_id), None)
        sd_name = sd.sub_domain_name if sd else c.sub_domain_id or "Layanan"
        for sc in c.sub_clusters:
            summary_items.append(f"- [{sd_name} / {c.category_level_2}] {sc.sub_cluster_title} ({len(sc.commit_ids)} commit)")

    cluster_overview = "\n".join(summary_items[:25])

    from app.data.style_guide import get_few_shot_prompt
    few_shot_examples = get_few_shot_prompt()

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""Anda adalah Senior Technical Writer dan Product Manager Super App.
Tugas Anda adalah menyusun Executive Summary dalam Bahasa Indonesia yang formal, elegan, dan komprehensif (2-3 paragraf) untuk direksi/manajemen eksekutif.

ATURAN PENULISAN:
1. Mulai langsung ke inti perkembangan Super App pada bulan bersangkutan.
2. Paparkan capaian utama pada fondasi Sistem Inti dan modul-modul Layanan Aplikasi.
3. Format paragraf yang utuh dan mengalir secara formal, BUKAN bullet point.
4. Jangan gunakan kata marketing berlebihan.

{few_shot_examples}"""),
        ("user", """Bulan: {month_year}
Daftar Sub-Cluster Aktivitas:
{cluster_overview}

Tuliskan Ringkasan Eksekutif:""")
    ])

    llm = get_llm()
    chain = prompt | llm

    logger.info("[Node: generate_summary] Menyusun Executive Summary Super App...")
    response = chain.invoke({"month_year": month_year, "cluster_overview": cluster_overview})

    content = response.content
    if isinstance(content, list):
        exec_summary_text = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])
    else:
        exec_summary_text = str(content)

    return {"executive_summary": exec_summary_text}


# =====================================================================
# NODE 6: Iterative Sub-Cluster Worker & Incremental Google Docs Sync
# =====================================================================
def generate_narratives_and_docs_loop_node(state: ReportState) -> dict:
    """
    Looping Sub-Cluster Worker:
    For each sub-cluster:
      1. LLM generates Balanced Tech-to-Business narration + visual placeholder
      2. Backend sends batchUpdate directly to Google Docs API
      3. Updates checkpoint state and progress
    """
    raw_commits = state.get("raw_commits", [])
    core_clusters = state.get("core_system_clusters", [])
    service_clusters = state.get("service_app_clusters", [])
    sub_domains = state.get("service_sub_domains", [])
    month_year = state.get("month_year", "")
    exec_summary = state.get("executive_summary", "")
    gdocs_mode = state.get("gdocs_mode", "direct")
    target_doc_id = state.get("gdocs_document_id") or os.getenv("TARGET_DOC_ID") or os.getenv("GDOCS_TEMPLATE_ID")

    commit_dict = {c.short_id: c for c in raw_commits}
    gdocs_service = GDocsService()

    # Step 1: Initialize Google Docs document
    doc_id = None
    doc_url = ""
    if gdocs_service.docs_service:
        try:
            doc_id, doc_url = gdocs_service.init_report_document(
                template_id=target_doc_id,
                month_year=month_year,
                exec_summary=exec_summary,
                mode=gdocs_mode
            )
            logger.info(f"[Node: loop_worker] Google Docs diinisialisasi: {doc_url}")
        except Exception as e:
            logger.warning(f"Failed to init Google Docs: {e}")

    # Prepare system prompt for balanced narration
    system_prompt = """Anda adalah Senior Technical Writer & Lead Business Analyst untuk ekosistem Super App.
Tugas Anda adalah menyusun narasi laporan progres mendalam dari kelompok commit (Sub-Cluster Fungsional).

ATURAN PENULISAN (BALANCED TECH-TO-BUSINESS):
1. BAHASA FORMAL & MENGALIR:
   - Gunakan Bahasa Indonesia formal, baku, dan jelas (2-3 paragraf per sub-cluster).
   - Jelaskan latar belakang masalah, implementasi solusi, dan dampak operasional/bisnisnya.
2. PRESERVASI NAMA FUNGSI & ISTILAH TEKNIS PENTING:
   - JANGAN menerjemahkan istilah baku secara mentah (contoh: JANGAN terjemahkan 'webhook' jadi 'kait web', 'debounce' jadi 'pengurang pantulan').
   - CANTUMKAN NAMA FUNGSI ASLI (misal: `handleStockLock()`, `validateSession()`) dan ENDPOINT API (misal: `/v1/orders`) dalam tanda petik kode backtick.
   - PERTAHANKAN istilah teknologi/protokol (misal: **OAuth 2.0**, **Redis**, **JWT**, **WebSocket**, **Docker**) dalam cetak tebal.
3. VISUAL PLACEHOLDER:
   - Jika perubahan menyangkut UI/UX, menu baru, atau alur transaksi yang butuh bukti visual, set 'requires_visual' = true dan berikan keterangan screenshot di 'visual_placeholder_note'."""

    llm = get_llm()
    structured_llm = llm.with_structured_output(SubClusterNarrationOutput)

    narrative_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", """Konteks Domain: {domain_context}
Kategori: {category_level_2}
Judul Cluster: {cluster_title}
Judul Sub-Cluster: {sub_cluster_title}

Daftar Commit Terkait:
{commits_details}

Buat narasi detail berimbang untuk sub-cluster ini:""")
    ])

    chain = narrative_prompt | structured_llm

    final_narratives: List[SubClusterNarrationOutput] = []
    completed_ids: List[str] = []

    # Flatten sub-clusters with hierarchy metadata
    tasks = []

    # 1. Core System
    for cl in core_clusters:
        for sc in cl.sub_clusters:
            tasks.append({
                "type": "CORE",
                "h2": "1. Perbaikan dan Pengembangan Sistem Inti Aplikasi",
                "h3": f"1.{'1' if cl.category_level_2 == 'FEATURE_UI' else '2'}. {cl.category_level_2}",
                "h4": f"1.{'1' if cl.category_level_2 == 'FEATURE_UI' else '2'}.1. {cl.cluster_title}",
                "domain_context": "Sistem Inti Aplikasi (Core Platform)",
                "cluster": cl,
                "sub_cluster": sc,
            })

    # 2. Service Apps
    for cl in service_clusters:
        sd = next((s for s in sub_domains if s.sub_domain_id == cl.sub_domain_id), None)
        sd_name = sd.sub_domain_name if sd else cl.sub_domain_id or "Layanan Aplikasi"
        for sc in cl.sub_clusters:
            tasks.append({
                "type": "SERVICE",
                "h2": "2. Pengembangan dan Pemeliharaan Layanan Aplikasi",
                "h3": f"2.{'1' if cl.category_level_2 == 'FEATURE_UI' else '2'}. {cl.category_level_2}",
                "h4": f"{sd_name} — {cl.cluster_title}",
                "domain_context": f"Layanan Aplikasi: {sd_name}",
                "cluster": cl,
                "sub_cluster": sc,
            })

    total_tasks = len(tasks)
    logger.info(f"[Node: loop_worker] Memulai Looping Sub-Cluster Worker untuk {total_tasks} sub-cluster...")

    # Looping execution per sub-cluster
    for idx, t in enumerate(tasks):
        cl: ContextCluster = t["cluster"]
        sc: SubClusterItem = t["sub_cluster"]

        # Gather commit details
        commit_lines = []
        for cid in sc.commit_ids:
            c = commit_dict.get(cid)
            if c:
                commit_lines.append(f"- [{c.short_id}] {c.title}" + (f"\n  Body: {c.message[:150]}" if c.message else ""))

        commits_details = "\n".join(commit_lines) if commit_lines else "- (Commit manual / general task)"

        logger.info(f"[Node: loop_worker] ({idx + 1}/{total_tasks}) Generating narasi untuk: {sc.sub_cluster_title}...")
        try:
            narration: SubClusterNarrationOutput = chain.invoke({
                "domain_context": t["domain_context"],
                "category_level_2": cl.category_level_2,
                "cluster_title": cl.cluster_title,
                "sub_cluster_title": sc.sub_cluster_title,
                "commits_details": commits_details,
            })
            narration.sub_cluster_id = sc.sub_cluster_id
            narration.cluster_id = cl.cluster_id
            narration.cluster_title = cl.cluster_title
            narration.category_level_1 = cl.category_level_1
            narration.sub_domain_id = cl.sub_domain_id
            narration.category_level_2 = cl.category_level_2
            narration.commit_ids = sc.commit_ids

            final_narratives.append(narration)
            completed_ids.append(sc.sub_cluster_id)

            # Append incrementally to Google Docs
            if doc_id and gdocs_service.docs_service:
                try:
                    gdocs_service.append_subcluster_section(
                        doc_id=doc_id,
                        h2_title=t["h2"] if idx == 0 or tasks[idx - 1]["h2"] != t["h2"] else None,
                        h3_title=t["h3"] if idx == 0 or tasks[idx - 1]["h3"] != t["h3"] else None,
                        h4_title=t["h4"] if idx == 0 or tasks[idx - 1]["h4"] != t["h4"] else None,
                        narration_output=narration
                    )
                except Exception as doc_err:
                    logger.warning(f"GDocs append failed for subcluster {sc.sub_cluster_id}: {doc_err}")

        except Exception as err:
            logger.error(f"Error generating narrative for {sc.sub_cluster_id}: {err}")

    # Convert to legacy ContentCluster for backward compat
    legacy_final = [
        ContentCluster(
            cluster_title=n.sub_cluster_title,
            commit_ids=n.commit_ids,
            category_level_1=n.category_level_1 or "SYSTEM_CORE",
            category_level_2=n.category_level_2 or "FEATURE_UI",
            business_narrative=n.business_narrative,
            requires_visual=n.requires_visual,
            visual_placeholder_note=n.visual_placeholder_note
        )
        for n in final_narratives
    ]

    return {
        "final_narratives": final_narratives,
        "final_clusters": legacy_final,
        "completed_sub_cluster_ids": completed_ids,
        "document_url": doc_url,
    }


# =====================================================================
# BUILD GRAPH
# =====================================================================
def build_workflow() -> StateGraph:
    """Build the full LangGraph workflow with all nodes and HITL interrupts."""
    workflow = StateGraph(ReportState)

    # Add nodes
    workflow.add_node("classify_l1", classify_l1_node)
    workflow.add_node("hitl_checkpoint_1", hitl_checkpoint_1_node)
    workflow.add_node("classify_l2_and_subcluster", classify_l2_and_cluster_node)
    workflow.add_node("hitl_checkpoint_2", hitl_checkpoint_2_node)
    workflow.add_node("generate_summary", generate_summary_node)
    workflow.add_node("generate_narratives_and_docs_loop", generate_narratives_and_docs_loop_node)

    # Define edges
    workflow.add_edge(START, "classify_l1")
    workflow.add_edge("classify_l1", "hitl_checkpoint_1")
    workflow.add_edge("hitl_checkpoint_1", "classify_l2_and_subcluster")
    workflow.add_edge("classify_l2_and_subcluster", "hitl_checkpoint_2")
    workflow.add_edge("hitl_checkpoint_2", "generate_summary")
    workflow.add_edge("generate_summary", "generate_narratives_and_docs_loop")
    workflow.add_edge("generate_narratives_and_docs_loop", END)

    return workflow


def compile_workflow(checkpointer=None):
    """Compile the workflow graph, optionally with a checkpointer for HITL persistence."""
    workflow = build_workflow()
    return workflow.compile(checkpointer=checkpointer)


# Legacy: simple compiled graph without checkpointer (for testing)
app_workflow = compile_workflow()