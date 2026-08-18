"""
LangGraph Workflow — Multi-Node Stateful Pipeline with HITL Interrupts.

Pipeline:
  START → classify_l1 → [HITL_1 interrupt] → classify_l2_and_cluster
        → [HITL_2 interrupt] → generate_summary → generate_narratives → END

Uses PostgresSaver for checkpoint persistence (HITL pause/resume).
"""
import os
from typing import List

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langchain_core.prompts import ChatPromptTemplate

from app.core.state import (
    ReportState,
    NormalizedCommit,
    ClassifiedCommit,
    L1ClassificationResult,
    L2ClassifiedCommit,
    L2ClassificationResult,
    CommitCluster,
    ClusteringResult,
    ContentCluster,
    ClusterResult,
)
from app.services.llm_service import get_llm
from app.services.embedding_service import cluster_commits_by_similarity


# =====================================================================
# NODE 1: Klasifikasi Level 1 — SYSTEM_APP vs SERVICE_APP
# =====================================================================
def classify_l1_node(state: ReportState) -> dict:
    """Classify each commit into SYSTEM_APP or SERVICE_APP using LLM structured output."""
    commits = state["raw_commits"]
    if not commits:
        return {"classified_commits": []}

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Anda adalah AI Architect Senior. Tugas Anda mengklasifikasikan daftar git commit ke dalam 2 kategori:
1. 'SYSTEM_APP': Perubahan pada aplikasi, fitur baru, antarmuka (UI/UX), perbaikan bug kode, optimalisasi kueri database, atau business logic.
2. 'SERVICE_APP': Perubahan pada infrastruktur, Docker, CI/CD pipeline, konfigurasi server, SSL/kredensial, deployment script, atau konfigurasi web server/proxy.

Klasifikasikan SETIAP commit. Berikan alasan singkat (1 kalimat) kenapa commit tersebut masuk ke kategori yang dipilih."""),
        ("user", "Data git commit (ID | Title | Message):\n{commits_text}")
    ])

    llm = get_llm()
    structured_llm = llm.with_structured_output(L1ClassificationResult)
    chain = prompt | structured_llm

    commits_text = "\n".join([
        f"[{c.short_id}] {c.title}" + (f" — {c.message[:100]}" if c.message and c.message != c.title else "")
        for c in commits
    ])

    print(f"[Node: classify_l1] Mengklasifikasikan {len(commits)} commit...")
    response = chain.invoke({"commits_text": commits_text})
    return {"classified_commits": response.results}


# =====================================================================
# NODE 2: HITL Checkpoint 1 — User reviews L1 classification
# =====================================================================
def hitl_checkpoint_1_node(state: ReportState) -> dict:
    """
    Human-in-the-Loop Checkpoint 1.
    Pauses execution and presents L1 classification for user review.
    User can re-classify commits before continuing.
    """
    classified = state["classified_commits"]
    
    # Prepare review data for the frontend
    system_app = [c for c in classified if c.category == "SYSTEM_APP"]
    service_app = [c for c in classified if c.category == "SERVICE_APP"]
    
    # Dynamic interrupt — pauses graph and sends data to the user
    user_response = interrupt({
        "type": "hitl_l1_review",
        "message": f"Review klasifikasi L1: {len(system_app)} SYSTEM_APP, {len(service_app)} SERVICE_APP",
        "system_app_commits": [c.model_dump() for c in system_app],
        "service_app_commits": [c.model_dump() for c in service_app],
    })
    
    # user_response contains the corrected classifications from the frontend
    if user_response and isinstance(user_response, dict):
        corrected = user_response.get("corrected_commits", None)
        if corrected:
            # Rebuild classified commits from user corrections
            new_classified = [ClassifiedCommit(**c) for c in corrected]
            return {"classified_commits": new_classified, "hitl_1_approved": True}
    
    # If user approved without changes
    return {"hitl_1_approved": True}


# =====================================================================
# NODE 3: Klasifikasi Level 2 & Semantic Clustering
# =====================================================================
def classify_l2_and_cluster_node(state: ReportState) -> dict:
    """
    Two-step process:
    1. LLM classifies each commit into L2 sub-categories (FEATURE_UI, BUG_FIX, etc.)
    2. Semantic embedding + clustering groups related commits together
    """
    raw_commits = state["raw_commits"]
    classified = state["classified_commits"]

    if not classified:
        return {"l2_classified": [], "clusters": []}

    commit_dict = {c.short_id: c for c in raw_commits}

    # --- Step 1: L2 Classification via LLM ---
    combined_text = "\n".join([
        f"[{c.id}] ({c.category}) {commit_dict[c.id].title if c.id in commit_dict else ''}"
        for c in classified
    ])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Anda adalah AI Architect. Tentukan sub-kategori Level 2 untuk setiap commit.
Sub-kategori yang tersedia:
- 'FEATURE_UI': Fitur baru, pengembangan antarmuka, penambahan fungsionalitas, UI/UX.
- 'BUG_FIX': Perbaikan bug, resolusi error, fixing crash atau kesalahan.
- 'REFACTOR_PERF': Refactoring kode, optimalisasi performa, peningkatan kualitas kode.
- 'INFRA_CHORE': Konfigurasi infrastruktur, CI/CD, Docker, maintenance, dependency update.

Klasifikasikan setiap commit berdasarkan ID-nya. Pertahankan kategori L1 (SYSTEM_APP/SERVICE_APP) yang sudah ada."""),
        ("user", "Daftar commit:\n{combined_text}")
    ])

    llm = get_llm()
    structured_llm = llm.with_structured_output(L2ClassificationResult)
    chain = prompt | structured_llm

    print(f"[Node: classify_l2] Mengklasifikasikan {len(classified)} commit ke Level 2...")
    l2_response = chain.invoke({"combined_text": combined_text})
    l2_classified = l2_response.results

    # --- Step 2: Semantic Clustering ---
    # Group commits by (L1 category, L2 category), then cluster within each group
    groups: dict[tuple[str, str], List[NormalizedCommit]] = {}
    l2_lookup = {c.id: c for c in l2_classified}

    for l2c in l2_classified:
        key = (l2c.category_level_1, l2c.category_level_2)
        commit = commit_dict.get(l2c.id)
        if commit:
            groups.setdefault(key, []).append(commit)

    all_clusters: List[CommitCluster] = []

    for (l1_cat, l2_cat), group_commits in groups.items():
        try:
            # Attempt semantic clustering
            semantic_groups = cluster_commits_by_similarity(group_commits)
        except Exception as e:
            print(f"[Warning] Embedding clustering failed for {l1_cat}/{l2_cat}: {e}. Falling back to single cluster.")
            semantic_groups = [group_commits]

        for cluster_group in semantic_groups:
            # Generate a cluster title from the first commit's subject
            first = cluster_group[0]
            title = first.cc_subject or first.title
            if len(title) > 40:
                title = title[:37] + "..."

            all_clusters.append(CommitCluster(
                cluster_title=title,
                commit_ids=[c.short_id for c in cluster_group],
                category_level_1=l1_cat,
                category_level_2=l2_cat,
            ))

    print(f"[Node: classify_l2] Dihasilkan {len(all_clusters)} cluster dari {len(l2_classified)} commit.")
    return {"l2_classified": l2_classified, "clusters": all_clusters}


# =====================================================================
# NODE 4: HITL Checkpoint 2 — User reviews L2 + Clusters
# =====================================================================
def hitl_checkpoint_2_node(state: ReportState) -> dict:
    """
    Human-in-the-Loop Checkpoint 2.
    Pauses execution and presents clusters for user review.
    User can rename, merge, or split clusters.
    """
    clusters = state["clusters"]

    user_response = interrupt({
        "type": "hitl_l2_review",
        "message": f"Review {len(clusters)} cluster semantik.",
        "clusters": [c.model_dump() for c in clusters],
    })

    if user_response and isinstance(user_response, dict):
        corrected_clusters = user_response.get("corrected_clusters", None)
        if corrected_clusters:
            new_clusters = [CommitCluster(**c) for c in corrected_clusters]
            return {"clusters": new_clusters, "hitl_2_approved": True}

    return {"hitl_2_approved": True}


# =====================================================================
# NODE 5: Executive Summary Generation
# =====================================================================
def generate_summary_node(state: ReportState) -> dict:
    """Generate a 2-3 paragraph executive summary of the month's work."""
    clusters = state["clusters"]
    month_year = state.get("month_year", "")

    if not clusters:
        return {"executive_summary": ""}

    # Prepare cluster overview for the LLM
    cluster_overview = "\n".join([
        f"- [{c.category_level_1}/{c.category_level_2}] {c.cluster_title} ({len(c.commit_ids)} commit)"
        for c in clusters
    ])

    # Count statistics
    system_count = sum(1 for c in clusters if c.category_level_1 == "SYSTEM_APP")
    service_count = sum(1 for c in clusters if c.category_level_1 == "SERVICE_APP")
    feature_count = sum(1 for c in clusters if c.category_level_2 == "FEATURE_UI")
    bugfix_count = sum(1 for c in clusters if c.category_level_2 == "BUG_FIX")

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Anda adalah Technical Writer Senior. Tugas Anda menulis Executive Summary (ringkasan eksekutif) 
untuk laporan progres pengembangan bulanan IT.

ATURAN:
1. Tulis dalam Bahasa Indonesia formal dan profesional.
2. Tulis dalam 2-3 paragraf naratif (BUKAN bullet points).
3. Jelaskan gambaran besar aktivitas bulan ini: berapa fitur baru, berapa bug fix, area utama pengembangan.
4. JANGAN menyebut nama file, fungsi, atau jargon teknis mentah.
5. Fokus pada dampak bisnis dan nilai yang dihasilkan."""),
        ("user", """Bulan: {month_year}
Statistik: {system_count} cluster Sistem Aplikasi, {service_count} cluster Layanan/Infrastruktur, {feature_count} fitur baru, {bugfix_count} perbaikan bug.

Daftar Cluster:
{cluster_overview}

Tuliskan Executive Summary:""")
    ])

    llm = get_llm()
    chain = prompt | llm

    print("[Node: generate_summary] Menyusun Executive Summary...")
    response = chain.invoke({
        "month_year": month_year,
        "system_count": system_count,
        "service_count": service_count,
        "feature_count": feature_count,
        "bugfix_count": bugfix_count,
        "cluster_overview": cluster_overview,
    })

    return {"executive_summary": response.content}


# =====================================================================
# NODE 6: Narrative Generation (Tech → Business Translation)
# =====================================================================
def generate_narratives_node(state: ReportState) -> dict:
    """
    Generate business narratives for each cluster.
    Processes clusters individually or in small batches.
    Transforms technical git commits into formal business language.
    """
    raw_commits = state["raw_commits"]
    clusters = state["clusters"]

    if not clusters:
        return {"final_clusters": []}

    commit_dict = {c.short_id: c for c in raw_commits}

    # System prompt matching GUIDELINES §4
    system_prompt = """Anda adalah Technical Writer & Business Analyst Senior di perusahaan enterprise.
Tugas Anda adalah menerjemahkan kelompok pesan git commit (Conventional Commits) 
menjadi laporan progres teknis yang mudah dipahami oleh manajemen eksekutif non-teknis.

ATURAN PENULISAN:
1. Gunakan Bahasa Indonesia formal yang profesional, baku, dan jelas.
2. DILARANG KERING / TERLALU SINGKAT: Jangan menulis seperti changelog atau bullet point pendek.
   Tuliskan dalam paragraf naratif utuh atau deskripsi mendalam yang menjelaskan konteks masalah,
   solusi yang diimplementasikan, serta manfaat operasionalnya.
3. HINDARI JARGON TEKNIS MENTAH:
   - Jangan gunakan: "Refactor function get_user_token()", "Fix null pointer exception di table orders", "Bump axios to v1.6".
   - Gunakan kalimat bisnis: "Pembaruan arsitektur keamanan pada sistem autentikasi pengguna...",
     "Perbaikan kesalahan pembacaan data pada tabel pesanan...", "Pembaruan komponen pustaka jaringan...".
4. VISUAL PLACEHOLDER:
   Jika perubahan melibatkan antarmuka pengguna (UI), alur transaksi baru, atau perubahan arsitektur kompleks,
   set variabel requires_visual = true dan berikan panduan screenshot yang tepat pada 'visual_placeholder_note'.
5. MINIMAL 3 kalimat per narasi. Narasi harus menjelaskan APA yang diubah, MENGAPA diubah, dan APA dampaknya."""

    llm = get_llm()
    structured_llm = llm.with_structured_output(ClusterResult)

    final_clusters: List[ContentCluster] = []

    # Process clusters in small batches (max 5 per LLM call) to maintain quality
    batch_size = 5
    for i in range(0, len(clusters), batch_size):
        batch = clusters[i:i + batch_size]

        batch_text_parts = []
        for cluster in batch:
            commit_details = []
            for cid in cluster.commit_ids:
                c = commit_dict.get(cid)
                if c:
                    commit_details.append(f"  - [{c.short_id}] {c.title}")
            
            batch_text_parts.append(
                f"CLUSTER: \"{cluster.cluster_title}\"\n"
                f"Kategori: {cluster.category_level_1} / {cluster.category_level_2}\n"
                f"Commit:\n" + "\n".join(commit_details)
            )

        combined_text = "\n\n".join(batch_text_parts)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", """Berikut adalah cluster-cluster commit yang perlu Anda terjemahkan menjadi narasi bisnis.
Untuk setiap cluster, pertahankan cluster_title, commit_ids, category_level_1, dan category_level_2 yang sudah ada.
Tuliskan business_narrative yang mendalam dan profesional.

{combined_text}""")
        ])

        chain = prompt | structured_llm

        batch_num = (i // batch_size) + 1
        total_batches = (len(clusters) + batch_size - 1) // batch_size
        print(f"[Node: generate_narratives] Batch {batch_num}/{total_batches} ({len(batch)} cluster)...")

        response = chain.invoke({"combined_text": combined_text})
        final_clusters.extend(response.clusters)

    return {"final_clusters": final_clusters}


# =====================================================================
# BUILD GRAPH
# =====================================================================
def build_workflow() -> StateGraph:
    """Build the full LangGraph workflow with all nodes and HITL interrupts."""
    workflow = StateGraph(ReportState)

    # Add nodes
    workflow.add_node("classify_l1", classify_l1_node)
    workflow.add_node("hitl_checkpoint_1", hitl_checkpoint_1_node)
    workflow.add_node("classify_l2_and_cluster", classify_l2_and_cluster_node)
    workflow.add_node("hitl_checkpoint_2", hitl_checkpoint_2_node)
    workflow.add_node("generate_summary", generate_summary_node)
    workflow.add_node("generate_narratives", generate_narratives_node)

    # Define edges
    workflow.add_edge(START, "classify_l1")
    workflow.add_edge("classify_l1", "hitl_checkpoint_1")
    workflow.add_edge("hitl_checkpoint_1", "classify_l2_and_cluster")
    workflow.add_edge("classify_l2_and_cluster", "hitl_checkpoint_2")
    workflow.add_edge("hitl_checkpoint_2", "generate_summary")
    workflow.add_edge("generate_summary", "generate_narratives")
    workflow.add_edge("generate_narratives", END)

    return workflow


def compile_workflow(checkpointer=None):
    """Compile the workflow graph, optionally with a checkpointer for HITL persistence."""
    workflow = build_workflow()
    return workflow.compile(checkpointer=checkpointer)


# Legacy: simple compiled graph without checkpointer (for backward compat / testing)
app_workflow = compile_workflow()