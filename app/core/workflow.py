from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from app.core.state import ReportState, L1ClassificationResult, ClusterResult
from app.services.llm_service import get_llm

# --- NODE 1: Klasifikasi Level 1 ---
def classify_l1_node(state: ReportState):
    commits = state["raw_commits"]
    if not commits:
        return {"classified_commits": []}

    # 1. Merangkai system prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Anda adalah AI Architect. Tugas Anda mengklasifikasikan daftar git commit ke dalam 2 kategori:
        1. 'SYSTEM_APP': Perubahan pada aplikasi, fitur, antarmuka, perbaikan bug kode, atau business logic.
        2. 'SERVICE_APP': Perubahan pada infrastruktur, Docker, CI/CD pipeline, konfigurasi server, atau SSL.
        """),
        ("user", "Data git commit (ID | Message):\n{commits_text}")
    ])

    llm = get_llm()
    structured_llm = llm.with_structured_output(L1ClassificationResult)
    chain = prompt | structured_llm
    commits_text = "\n".join([f"[{c.id}] {c.message}" for c in commits])
    
    response = chain.invoke({"commits_text": commits_text})
    return {"classified_commits": response.results}

def generate_narrative_node(state: ReportState):
    raw_commits = state["raw_commits"]
    classified_commits = state["classified_commits"]

    if not classified_commits:
        return {"final_clusters": []}

    # Buat kamus untuk mencocokkan ID dengan pesan aslinya
    commit_dict = {c.id: c.message for c in raw_commits}

    # Format data untuk LLM: "[ID] (Kategori) Pesan Commit"
    combined_text = "\n".join([
        f"[{c.id}] ({c.category}) {commit_dict.get(c.id, '')}" 
        for c in classified_commits
    ])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Anda adalah Technical Writer & Business Analyst Senior.
        Tugas Anda:
        1. Kelompokkan commit yang saling berkaitan ke dalam SATU fitur/cluster.
        2. Tentukan category_level_2 (FEATURE_UI, BUG_FIX, REFACTOR_PERF, atau INFRA_CHORE).
        3. Tuliskan 'business_narrative' menggunakan Bahasa Indonesia formal. 
           JELASKAN apa yang diubah dan manfaatnya untuk bisnis. HINDARI nama file/fungsi/jargon teknis mentah.
        4. Jika fitur kompleks (misal: antarmuka baru), set 'requires_visual' = true dan berikan instruksinya.
        """),
        ("user", "Daftar Commit yang sudah diklasifikasi:\n{combined_text}")
    ])

    # Memaksa output LLM sesuai skema ClusterResult
    llm = get_llm()
    structured_llm = llm.with_structured_output(ClusterResult)
    chain = prompt | structured_llm
    
    print("AI sedang menyusun narasi bisnis...")
    response = chain.invoke({"combined_text": combined_text})
    
    return {"final_clusters": response.clusters}

# --- BUILD GRAPH ---
workflow = StateGraph(ReportState)

# Tambahkan Node
workflow.add_node("classify_l1", classify_l1_node)
workflow.add_node("generate_narrative", generate_narrative_node)

# Tentukan Alur (Start -> Classify -> End)
workflow.add_edge(START, "classify_l1")
workflow.add_edge("classify_l1", "generate_narrative")
workflow.add_edge("generate_narrative", END)

# Compile Graph
app_workflow = workflow.compile()