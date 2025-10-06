import os, json, numpy as np
from pathlib import Path
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from neo4j import GraphDatabase

# Neo4j connection
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASS = os.environ.get("NEO4J_PASS", "password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

# FAISS index
import faiss
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = DATA_DIR / "faiss.index"
META_PATH = DATA_DIR / "faiss_meta.json"

DIM = 128  # vector dim
if INDEX_PATH.exists():
    index = faiss.read_index(str(INDEX_PATH))
    meta = json.loads(META_PATH.read_text())
else:
    index = faiss.IndexFlatIP(DIM)
    meta = {"ids": [], "texts": []}

def persist_index():
    faiss.write_index(index, str(INDEX_PATH))
    META_PATH.write_text(json.dumps(meta))

app = FastAPI(title="kb-service", version="0.2.0")

@app.get("/healthz")
def healthz():
    with driver.session() as s:
        s.run("RETURN 1").consume()
    return {"ok": True, "neo4j": True, "faiss_ntotal": int(index.ntotal)}

@app.post("/kb/upsert_tunable")
def upsert_tunable(name: str = Body(...), rng: list = Body(default=None), unit: str = Body(default=None)):
    cy = """
    MERGE (t:Tunable {name:$name})
    SET t.unit=$unit, t.range=$rng
    RETURN t
    """
    with driver.session() as s:
        rec = s.run(cy, name=name, unit=unit, rng=rng).single()
    return JSONResponse(rec["t"])

@app.post("/kb/dep_edge")
def dep_edge(frm: str = Body(...), to: str = Body(...), rel: str = Body(default="rel")):
    cy = """
    MATCH (a:Tunable {name:$frm}), (b:Tunable {name:$to})
    MERGE (a)-[r:DEP {rel:$rel}]->(b)
    RETURN type(r) AS type, a.name AS from, b.name AS to, r.rel AS rel
    """
    with driver.session() as s:
        rec = s.run(cy, frm=frm, to=to, rel=rel).single()
    return JSONResponse(rec.data())

@app.post("/kb/upsert_trace")
def upsert_trace(context: dict = Body(...), action: dict = Body(...), outcome: dict = Body(...)):
    cy = """
    MERGE (c:Context {key:$ckey}) SET c += $context
    MERGE (a:Action {key:$akey}) SET a += $action
    MERGE (o:Outcome {key:$okey}) SET o += $outcome
    MERGE (c)-[:LED_TO]->(a)-[:RESULTED_IN]->(o)
    RETURN c,a,o
    """
    key = f"{context.get('workload','unknown')}::{action.get('knob','?')}"
    with driver.session() as s:
        s.run(cy, ckey=key, akey=key, okey=key, context=context, action=action, outcome=outcome).consume()
    return {"ok": True}

def _embed(text: str) -> np.ndarray:
    # Simple deterministic toy embedding (hash-based) to keep demo self-contained
    np.random.seed(abs(hash(text)) % (2**32))
    v = np.random.normal(0, 1, size=(DIM,)).astype("float32")
    v /= np.linalg.norm(v) + 1e-8
    return v

@app.post("/kb/nn_upsert")
def nn_upsert(text: str = Body(...)):
    v = _embed(text)
    index.add(v.reshape(1, -1))
    meta["ids"].append(int(index.ntotal)-1)
    meta["texts"].append(text)
    persist_index()
    return {"ok": True, "id": int(index.ntotal)-1}

@app.post("/kb/nn_search")
def nn_search(query: str = Body(...), k: int = Body(default=5)):
    v = _embed(query)
    D, I = index.search(v.reshape(1,-1), k)
    items = []
    for score, idx in zip(D[0].tolist(), I[0].tolist()):
        if idx < 0 or idx >= len(meta["texts"]): 
            continue
        items.append({"id": idx, "text": meta["texts"][idx], "score": float(score)})
    return {"items": items}


from fastapi import Query

@app.get("/kb/dependency_path")
def dependency_path(start: str = Query(...), end: str = Query(None)):
    """
    If `end` is provided, returns one shortest DEP path from start->end (depth ≤ 4).
    Otherwise, returns outward neighborhood (depth ≤ 2) from start.
    """
    with driver.session() as s:
        if end:
            cy = """
            MATCH p = shortestPath((a:Tunable {name:$start})-[:DEP*1..4]->(b:Tunable {name:$end}))
            RETURN [n IN nodes(p) | n.name] AS nodes, [r IN relationships(p) | r.rel] AS rels
            """
            rec = s.run(cy, start=start, end=end).single()
            if not rec:
                return {"nodes": [], "rels": []}
            return {"nodes": rec["nodes"], "rels": rec["rels"]}
        else:
            cy = """
            MATCH (a:Tunable {name:$start})- [r:DEP*1..2] -> (b:Tunable)
            WITH collect(distinct b.name) AS nbrs
            RETURN nbrs
            """
            rec = s.run(cy, start=start).single()
            return {"neighbors": rec["nbrs"] if rec else []}
