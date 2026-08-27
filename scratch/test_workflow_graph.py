import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.state import (
    NormalizedCommit,
    ServiceSubDomain,
    ClassifiedCommit,
    ContextCluster,
    SubClusterItem,
    SubClusterNarrationOutput,
    ReportState
)
from app.core.workflow import build_workflow, compile_workflow

def test_models():
    print("Testing models...")
    nc = NormalizedCommit(
        short_id="a1b2c3d",
        title="feat(presensi): add face recognition validation in handleVerification()",
        message="Full details",
        author_name="Developer",
        cc_type="feat",
        cc_scope="presensi",
        cc_subject="add face recognition validation in handleVerification()",
        cc_is_conventional=True
    )
    assert nc.short_id == "a1b2c3d"

    sd = ServiceSubDomain(
        sub_domain_id="presensi",
        sub_domain_name="Layanan Presensi Online",
        commit_ids=["a1b2c3d"]
    )
    assert sd.sub_domain_id == "presensi"

    sc = SubClusterItem(
        sub_cluster_id="sub-1",
        sub_cluster_title="Validasi Pengenalan Wajah",
        commit_ids=["a1b2c3d"]
    )

    cc = ContextCluster(
        cluster_id="cl-1",
        cluster_title="Modul Kehadiran",
        category_level_1="APP_SERVICE",
        sub_domain_id="presensi",
        category_level_2="FEATURE_UI",
        sub_clusters=[sc]
    )
    assert len(cc.sub_clusters) == 1
    print("Models verified successfully!")

def test_graph_compilation():
    print("Testing graph compilation...")
    workflow = build_workflow()
    compiled = workflow.compile()
    assert compiled is not None
    print("LangGraph workflow compiled successfully!")

if __name__ == "__main__":
    test_models()
    test_graph_compilation()
    print("All checks passed!")
