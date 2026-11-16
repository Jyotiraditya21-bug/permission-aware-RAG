from fastapi.testclient import TestClient

from src.api import app

client = TestClient(app)

def test_observability_endpoints():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert "version" in res.json()

    res = client.get("/ready")
    assert res.status_code == 200
    assert res.json()["status"] == "ready"

    res = client.get("/version")
    assert res.status_code == 200
    assert "version" in res.json()


def test_list_demo_identities():
    res = client.get("/demo/identities")
    assert res.status_code == 200
    identities = res.json()
    assert len(identities) >= 4
    ids = [i["id"] for i in identities]
    assert "alice@alpha" in ids
    assert "bob@alpha" in ids
    assert "charlie@beta" in ids
    assert "anonymous" in ids


def test_fail_closed_anonymous_identity():
    # Anonymous identity must fail closed with 401
    res = client.post("/demo/query", json={
        "identity": "anonymous",
        "query": "What is Project Titan?"
    })
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]


def test_alice_authorized_for_confidential_roadmap():
    # Alice (engineering/admin in alpha) has access to Project Titan
    res = client.post("/demo/query", json={
        "identity": "alice@alpha",
        "query": "What is Project Titan?"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "grounded"
    assert "Project Titan" in data["answer"]
    # Verify citations link to chunk-alpha-002
    cited_chunks = [cid for cite in data["citations"] for cid in cite["chunk_ids"]]
    assert "chunk-alpha-002" in cited_chunks


def test_bob_denied_confidential_roadmap_without_leakage():
    # Bob (sales in alpha) is NOT in engineering group
    res = client.post("/demo/query", json={
        "identity": "bob@alpha",
        "query": "What is Project Titan?"
    })
    assert res.status_code == 200
    data = res.json()
    # Bob must NOT receive chunk-alpha-002
    for chunk in data.get("authorized_chunks", []):
        assert chunk["chunk_id"] != "chunk-alpha-002"
        assert "Project Titan" not in chunk["text"]

    for cite in data.get("citations", []):
        assert "chunk-alpha-002" not in cite["chunk_ids"]

    # Denied count must reflect filtered confidential chunks
    assert data["denied_chunks_count"] >= 1


def test_cross_tenant_isolation_charlie_beta():
    # Charlie is in tenant_beta, must never see tenant_alpha documents
    res = client.post("/demo/query", json={
        "identity": "charlie@beta",
        "query": "AlphaCorp Framework SLA"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["tenant_id"] == "tenant_beta"
    for chunk in data.get("authorized_chunks", []):
        assert chunk["tenant_id"] == "tenant_beta"
        assert "AlphaCorp" not in chunk["text"]


def test_charlie_authorized_for_beta_spec():
    # Charlie should be able to view Beta partner specifications
    res = client.post("/demo/query", json={
        "identity": "charlie@beta",
        "query": "BetaLogistics partner guidelines"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "grounded"
    assert "BetaLogistics" in data["answer"]
    cited_chunks = [cid for cite in data["citations"] for cid in cite["chunk_ids"]]
    assert "chunk-beta-001" in cited_chunks
