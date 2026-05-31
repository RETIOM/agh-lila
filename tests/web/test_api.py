from fastapi.testclient import TestClient

from web.server.app import app

client = TestClient(app)


def test_highlight_endpoint():
    r = client.post("/api/highlight", json={"source": "int x;"})
    assert r.status_code == 200
    spans = r.json()["spans"]
    assert any(s["type"] == "TYPE_INT" for s in spans)


def test_compile_endpoint_valid():
    r = client.post("/api/compile", json={"source": "fn main() -> int { return 0; }"})
    assert r.status_code == 200
    body = r.json()
    assert body["diagnostics"] == []
    assert "define i32 @main" in body["ir"]


def test_compile_endpoint_semantic_error():
    r = client.post("/api/compile", json={"source": "fn main() -> int { break; }"})
    assert r.status_code == 200
    assert any(d["stage"] == "semantic" for d in r.json()["diagnostics"])


def test_run_endpoint_compile_error_returns_diagnostics():
    r = client.post("/api/run", json={"source": "fn main() -> int { break; }", "stdin": ""})
    assert r.status_code == 200
    body = r.json()
    assert body["diagnostics"]
    assert body["exit_code"] is None


def test_list_examples_grouped():
    r = client.get("/api/examples")
    assert r.status_code == 200
    items = r.json()
    assert any(i["category"] == "algo" and i["name"] == "caesar" for i in items)
    assert any(i["id"] == "trivial/hello_world" for i in items)


def test_get_example_source():
    r = client.get("/api/examples/trivial/hello_world")
    assert r.status_code == 200
    assert "Hello" in r.json()["source"]


def test_get_example_rejects_traversal():
    r = client.get("/api/examples/..%2Fpyproject")
    assert r.status_code == 404


def test_api_routes_work_without_built_client():
    # mounting static files is conditional on dist existing; the API must work regardless
    r = client.post("/api/highlight", json={"source": "int x;"})
    assert r.status_code == 200
