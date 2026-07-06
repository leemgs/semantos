"""
kb-service — SemantOS Knowledge Base.

Two coupled stores (paper Sec. 4.2):
  1. A *typed, signed, weighted* inter-knob dependency graph in Neo4j.
     Edge types: SYNERGIZES_WITH, CONFLICTS_WITH, DEPENDS_ON.  Each edge carries
     a sign (+1 reinforcing / -1 opposing), a weight w in [0,1] (evidence
     strength), an evidence count, and an `updated_at` epoch used for
     gamma-decay so stale co-tuning evidence is down-weighted over time.
  2. A FAISS trace index for retrieval-augmented grounding (RAG) of past
     (context, action, outcome) tuples.

The typed neighborhood the reasoner queries is the object the ablation calls the
"dep-graph"; removing it corresponds to the `wo_depgraph` row of Table 3.
"""
import os
import json
import time
import math
from pathlib import Path

import numpy as np
from fastapi import FastAPI, Body, Query
from fastapi.responses import JSONResponse
from neo4j import GraphDatabase

# --------------------------------------------------------------------------- #
# Connections.
# --------------------------------------------------------------------------- #
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASS = os.environ.get("NEO4J_PASS", "password")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

import faiss  # noqa: E402
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = DATA_DIR / "faiss.index"
META_PATH = DATA_DIR / "faiss_meta.json"
SEED_PATH = Path(os.environ.get("SEED_EDGES", "/app/kb/seed_edges.json"))

DIM = 128
if INDEX_PATH.exists():
    index = faiss.read_index(str(INDEX_PATH))
    meta = json.loads(META_PATH.read_text())
else:
    index = faiss.IndexFlatIP(DIM)
    meta = {"ids": [], "texts": []}

# Typed edge vocabulary and gamma-decay half-life (paper defaults).
EDGE_TYPES = {"synergizes_with": "SYNERGIZES_WITH",
              "conflicts_with": "CONFLICTS_WITH",
              "depends_on": "DEPENDS_ON"}
GAMMA = float(os.environ.get("KB_GAMMA", "0.98"))          # per-day decay
DECAY_UNIT_S = float(os.environ.get("KB_DECAY_UNIT_S", "86400"))


def persist_index():
    faiss.write_index(index, str(INDEX_PATH))
    META_PATH.write_text(json.dumps(meta))


app = FastAPI(title="kb-service", version="1.0.0")


@app.get("/healthz")
def healthz():
    with driver.session() as s:
        s.run("RETURN 1").consume()
    return {"ok": True, "neo4j": True, "faiss_ntotal": int(index.ntotal),
            "gamma": GAMMA}


# --------------------------------------------------------------------------- #
# Tunables (knobs).
# --------------------------------------------------------------------------- #
@app.post("/kb/upsert_tunable")
def upsert_tunable(name: str = Body(...), rng: list = Body(default=None),
                   unit: str = Body(default=None),
                   subsystem: str = Body(default=None),
                   direction: str = Body(default=None)):
    """direction: 'higher_faster' | 'lower_faster' | 'nonmonotone' (optional)."""
    cy = """
    MERGE (t:Tunable {name:$name})
    SET t.unit=$unit, t.range=$rng, t.subsystem=$subsystem, t.direction=$direction
    RETURN t
    """
    with driver.session() as s:
        rec = s.run(cy, name=name, unit=unit, rng=rng,
                    subsystem=subsystem, direction=direction).single()
    return JSONResponse(rec["t"])


# --------------------------------------------------------------------------- #
# Typed / signed / weighted dependency edges.
# --------------------------------------------------------------------------- #
def _rel_label(edge_type: str) -> str:
    key = edge_type.lower()
    if key not in EDGE_TYPES:
        raise ValueError(f"unknown edge_type '{edge_type}'; "
                         f"expected one of {list(EDGE_TYPES)}")
    return EDGE_TYPES[key]


@app.post("/kb/dep_edge")
def dep_edge(frm: str = Body(...), to: str = Body(...),
             edge_type: str = Body(...), sign: int = Body(default=1),
             weight: float = Body(default=0.5), evidence: int = Body(default=1)):
    """Upsert a typed edge.  Repeated evidence does a weighted running update of
    the edge weight and increments the evidence counter."""
    label = _rel_label(edge_type)
    now = time.time()
    cy = f"""
    MATCH (a:Tunable {{name:$frm}}), (b:Tunable {{name:$to}})
    MERGE (a)-[r:{label}]->(b)
    ON CREATE SET r.weight=$weight, r.sign=$sign, r.evidence=$evidence,
                  r.created_at=$now, r.updated_at=$now
    ON MATCH  SET r.weight = (r.weight*r.evidence + $weight*$evidence)
                              / (r.evidence + $evidence),
                  r.sign=$sign,
                  r.evidence = r.evidence + $evidence,
                  r.updated_at=$now
    RETURN type(r) AS edge_type, a.name AS from, b.name AS to,
           r.sign AS sign, r.weight AS weight, r.evidence AS evidence
    """
    with driver.session() as s:
        rec = s.run(cy, frm=frm, to=to, weight=float(weight), sign=int(sign),
                    evidence=int(evidence), now=now).single()
    if rec is None:
        return JSONResponse({"error": "both tunables must exist"}, status_code=404)
    return JSONResponse(rec.data())


@app.get("/kb/typed_neighborhood")
def typed_neighborhood(knob: str = Query(...), edge_type: str = Query(None),
                       min_weight: float = Query(0.0), decayed: bool = Query(True)):
    """Return the typed/signed/weighted neighborhood the reasoner grounds on.

    If `decayed`, weights are reported after gamma-decay: w * gamma^(age_days),
    so stale evidence is discounted at query time without mutating the store.
    """
    rel = _rel_label(edge_type) if edge_type else None
    pattern = f"[r:{rel}]" if rel else "[r]"
    cy = f"""
    MATCH (a:Tunable {{name:$knob}})-{pattern}->(b:Tunable)
    RETURN type(r) AS edge_type, b.name AS neighbor, r.sign AS sign,
           r.weight AS weight, r.evidence AS evidence, r.updated_at AS updated_at
    """
    now = time.time()
    out = []
    with driver.session() as s:
        for rec in s.run(cy, knob=knob):
            w = float(rec["weight"])
            if decayed and rec["updated_at"] is not None:
                age_days = max(0.0, (now - float(rec["updated_at"])) / DECAY_UNIT_S)
                w = w * (GAMMA ** age_days)
            if w < min_weight:
                continue
            out.append({"edge_type": rec["edge_type"].lower(),
                        "neighbor": rec["neighbor"], "sign": int(rec["sign"]),
                        "weight": round(w, 4), "evidence": int(rec["evidence"])})
    out.sort(key=lambda e: -e["weight"])
    return {"knob": knob, "edges": out}


@app.post("/kb/decay")
def decay():
    """Persist gamma-decay into stored weights (batch maintenance job).
    w <- w * gamma^(age_days); updated_at reset to now."""
    now = time.time()
    cy = """
    MATCH ()-[r]->()
    WHERE r.updated_at IS NOT NULL AND r.weight IS NOT NULL
    RETURN id(r) AS rid, r.weight AS w, r.updated_at AS ts
    """
    updates = []
    with driver.session() as s:
        for rec in s.run(cy):
            age_days = max(0.0, (now - float(rec["ts"])) / DECAY_UNIT_S)
            updates.append((rec["rid"], float(rec["w"]) * (GAMMA ** age_days)))
        for rid, w in updates:
            s.run("MATCH ()-[r]->() WHERE id(r)=$rid "
                  "SET r.weight=$w, r.updated_at=$now",
                  rid=rid, w=w, now=now).consume()
    return {"decayed_edges": len(updates), "gamma": GAMMA}


@app.post("/kb/induce_from_seed")
def induce_from_seed(path: str = Body(default=None)):
    """Bulk-load the induced typed edges produced offline by kb/induce_edges.py.
    Expects a JSON list of {from,to,edge_type,sign,weight,evidence}."""
    p = Path(path) if path else SEED_PATH
    if not p.exists():
        return JSONResponse({"error": f"seed file not found: {p}"}, status_code=404)
    edges = json.loads(p.read_text())
    loaded = 0
    for e in edges:
        try:
            dep_edge(frm=e["from"], to=e["to"], edge_type=e["edge_type"],
                     sign=int(e.get("sign", 1)), weight=float(e.get("weight", 0.5)),
                     evidence=int(e.get("evidence", 1)))
            loaded += 1
        except Exception:
            continue
    return {"loaded": loaded, "source": str(p)}


# --------------------------------------------------------------------------- #
# Traces + RAG (FAISS).
# --------------------------------------------------------------------------- #
@app.post("/kb/upsert_trace")
def upsert_trace(context: dict = Body(...), action: dict = Body(...),
                 outcome: dict = Body(...)):
    cy = """
    MERGE (c:Context {key:$ckey}) SET c += $context
    MERGE (a:Action {key:$akey}) SET a += $action
    MERGE (o:Outcome {key:$okey}) SET o += $outcome
    MERGE (c)-[:LED_TO]->(a)-[:RESULTED_IN]->(o)
    RETURN c,a,o
    """
    key = f"{context.get('workload','unknown')}::{action.get('knob','?')}"
    with driver.session() as s:
        s.run(cy, ckey=key, akey=key, okey=key, context=context,
              action=action, outcome=outcome).consume()
    # index a textual view of the trace for RAG
    text = (f"workload={context.get('workload')} server={context.get('server')} "
            f"knob={action.get('knob')} value={action.get('proposed_value')} "
            f"delta_p95={outcome.get('delta_p95')} anomaly={outcome.get('anomaly')}")
    nn_upsert(text=text)
    return {"ok": True}


def _embed(text: str) -> np.ndarray:
    np.random.seed(abs(hash(text)) % (2 ** 32))
    v = np.random.normal(0, 1, size=(DIM,)).astype("float32")
    v /= np.linalg.norm(v) + 1e-8
    return v


@app.post("/kb/nn_upsert")
def nn_upsert(text: str = Body(...)):
    v = _embed(text)
    index.add(v.reshape(1, -1))
    meta["ids"].append(int(index.ntotal) - 1)
    meta["texts"].append(text)
    persist_index()
    return {"ok": True, "id": int(index.ntotal) - 1}


@app.post("/kb/nn_search")
def nn_search(query: str = Body(...), k: int = Body(default=5)):
    if index.ntotal == 0:
        return {"items": []}
    v = _embed(query)
    D, I = index.search(v.reshape(1, -1), min(k, index.ntotal))
    items = []
    for score, idx in zip(D[0].tolist(), I[0].tolist()):
        if idx < 0 or idx >= len(meta["texts"]):
            continue
        items.append({"id": idx, "text": meta["texts"][idx], "score": float(score)})
    return {"items": items}


# --------------------------------------------------------------------------- #
# Path / neighborhood over any typed edge (kept for operator introspection).
# --------------------------------------------------------------------------- #
@app.get("/kb/dependency_path")
def dependency_path(start: str = Query(...), end: str = Query(None)):
    with driver.session() as s:
        if end:
            cy = """
            MATCH p = shortestPath((a:Tunable {name:$start})-[*1..4]->(b:Tunable {name:$end}))
            RETURN [n IN nodes(p) | n.name] AS nodes,
                   [r IN relationships(p) | type(r)] AS rels
            """
            rec = s.run(cy, start=start, end=end).single()
            if not rec:
                return {"nodes": [], "rels": []}
            return {"nodes": rec["nodes"], "rels": [r.lower() for r in rec["rels"]]}
        cy = """
        MATCH (a:Tunable {name:$start})-[*1..2]->(b:Tunable)
        RETURN collect(distinct b.name) AS nbrs
        """
        rec = s.run(cy, start=start).single()
        return {"neighbors": rec["nbrs"] if rec else []}
