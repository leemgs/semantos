// SemantOS — English single-slide conference poster (48in x 36in landscape).
// Build: node gen_poster.js -> semantos_poster_en.pptx  (then convert to .ppt)
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.defineLayout({ name: "POSTER", width: 48, height: 36 });
p.layout = "POSTER";
p.author = "Geunsik Lim";
p.title = "SemantOS Poster";

const DEEP = "0F1733", NAVY = "1E2761", TEAL = "02C39A", AMBER = "F4A261";
const ICE = "CADCFC", LIGHT = "EEF3FB", WHITE = "FFFFFF";
const TEXT = "1F2A44", MUTE = "5E6B85", LINE = "CFDAEC";
const SERIF = "Cambria", SANS = "Calibri";

const s = p.addSlide();
s.background = { color: LIGHT };

function shadow() { return { type: "outer", color: "1E2761", opacity: 0.20, blur: 14, offset: 5, angle: 90 }; }
function card(x, y, w, h, fill) {
  s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.22,
    fill: { color: fill || WHITE }, line: { color: LINE, width: 1.25 }, shadow: shadow() });
}
function secTitle(x, y, w, n, t) {
  s.addShape(p.ShapeType.ellipse, { x: x + 0.5, y: y + 0.25, w: 1.0, h: 1.0, fill: { color: TEAL }, line: { type: "none" } });
  s.addText(String(n), { x: x + 0.5, y: y + 0.25, w: 1.0, h: 1.0, align: "center", valign: "middle", fontFace: SERIF, fontSize: 30, bold: true, color: WHITE });
  s.addText(t, { x: x + 1.75, y: y + 0.2, w: w - 2.0, h: 1.1, valign: "middle", fontFace: SERIF, fontSize: 30, bold: true, color: NAVY, margin: 0 });
}

// ============================ HEADER =====================================
s.addShape(p.ShapeType.roundRect, { x: 1.0, y: 1.0, w: 46, h: 5.0, rectRadius: 0.22, fill: { color: DEEP }, line: { type: "none" }, shadow: shadow() });
s.addShape(p.ShapeType.ellipse, { x: 40.5, y: -3.5, w: 12, h: 12, fill: { color: NAVY }, line: { type: "none" } });
s.addText("SemantOS", { x: 2.0, y: 1.2, w: 30, h: 1.8, fontFace: SERIF, fontSize: 76, bold: true, color: WHITE, margin: 0 });
s.addText("Safe and Explainable Kernel Tuning via Semantic Reasoning and Guardrailed LLMs",
  { x: 2.05, y: 3.15, w: 38, h: 1.2, fontFace: SANS, fontSize: 30, bold: true, color: ICE, margin: 0 });
s.addText("Geunsik Lim  ·  leemgs@gmail.com          Submitted to AAAI-27 · Main Technical Track",
  { x: 2.05, y: 4.5, w: 38, h: 0.9, fontFace: SANS, fontSize: 20, italic: true, color: "8FA2CC", margin: 0 });
// headline chips (top-right of header)
[["23%", "P95 latency"], ["31%", "anomaly rate"], ["85%+", "operator effort"]].forEach((c, i) => {
  const x = 33.2 + i * 4.4;
  s.addShape(p.ShapeType.roundRect, { x, y: 1.5, w: 4.1, h: 3.0, rectRadius: 0.18, fill: { color: "16204a" }, line: { color: TEAL, width: 1.5 } });
  s.addText(c[0], { x, y: 1.75, w: 4.1, h: 1.5, align: "center", fontFace: SERIF, fontSize: 44, bold: true, color: TEAL });
  s.addText("↓ " + c[1], { x, y: 3.25, w: 4.1, h: 0.9, align: "center", fontFace: SANS, fontSize: 16, color: ICE });
});

// ============================ COLUMNS ====================================
const COLW = 14.7, GAP = 0.95;
const X1 = 1.0, X2 = X1 + COLW + GAP, X3 = X2 + COLW + GAP;
const TOP = 6.7;

// ---- Column 1 ----------------------------------------------------------
// 1. Motivation
card(X1, TOP, COLW, 8.6);
secTitle(X1, TOP, COLW, 1, "The Problem");
s.addText([
  { text: "Linux exposes hundreds of interdependent kernel knobs (scheduler / memory / I/O / IRQ / NUMA). Small mis-settings cause latency spikes and unstable tails.", options: { fontSize: 19, color: TEXT, breakLine: true, paraSpaceAfter: 12, lineSpacingMultiple: 1.12 } },
  { text: "Context sensitivity — best values differ per workload & phase.", options: { bullet: { code: "2022" }, fontSize: 19, color: TEXT, breakLine: true, paraSpaceAfter: 8 } },
  { text: "Strong inter-knob coupling — jointly tuning two scheduler knobs cuts tail latency >30% (non-additive).", options: { bullet: { code: "2022" }, fontSize: 19, color: TEXT, breakLine: true, paraSpaceAfter: 8 } },
  { text: "Multi-objective trade-offs — latency vs. fairness vs. throughput.", options: { bullet: { code: "2022" }, fontSize: 19, color: TEXT } },
], { x: X1 + 0.6, y: TOP + 1.7, w: COLW - 1.2, h: 6.6, valign: "top", margin: 0 });

// 2. Key idea
card(X1, TOP + 9.1, COLW, 6.2, NAVY);
s.addShape(p.ShapeType.ellipse, { x: X1 + 0.5, y: TOP + 9.35, w: 1.0, h: 1.0, fill: { color: TEAL }, line: { type: "none" } });
s.addText("2", { x: X1 + 0.5, y: TOP + 9.35, w: 1.0, h: 1.0, align: "center", valign: "middle", fontFace: SERIF, fontSize: 30, bold: true, color: WHITE });
s.addText("Key Idea", { x: X1 + 1.75, y: TOP + 9.3, w: COLW - 2, h: 1.1, valign: "middle", fontFace: SERIF, fontSize: 30, bold: true, color: WHITE, margin: 0 });
s.addText("Treat the kernel not as a black box but as a semantically grounded control loop:",
  { x: X1 + 0.6, y: TOP + 10.7, w: COLW - 1.2, h: 1.4, fontSize: 20, bold: true, color: ICE, margin: 0, lineSpacingMultiple: 1.1 });
s.addText("telemetry  →  KB + LLM reasoning  →  calibrated uncertainty  →  staged, auditable rollout",
  { x: X1 + 0.6, y: TOP + 12.2, w: COLW - 1.2, h: 2.4, fontSize: 20, italic: true, color: TEAL, margin: 0, lineSpacingMultiple: 1.2, valign: "top" });

// 3. Architecture
card(X1, TOP + 15.6, COLW, 12.0);
secTitle(X1, TOP + 15.6, COLW, 3, "Architecture");
const comps = [
  ["① Telemetry Agent", "eBPF + userspace, 5 s sampling (<1% CPU)"],
  ["② Knowledge Base", "typed/signed dep-graph + FAISS traces (γᵗ decay)"],
  ["③ Reasoner (LLM)", "RAG → knob, value, rationale, uncertainty u"],
  ["④ Safety Runtime", "conformal τ gate, canary→ramp→full, rollback"],
  ["⑤ Operator Console", "explanations, provenance, override/rollback"],
];
comps.forEach((c, i) => {
  const y = TOP + 17.2 + i * 2.02;
  s.addShape(p.ShapeType.roundRect, { x: X1 + 0.55, y, w: COLW - 1.1, h: 1.75, rectRadius: 0.12, fill: { color: LIGHT }, line: { color: LINE, width: 1 } });
  s.addText(c[0], { x: X1 + 0.8, y: y + 0.12, w: COLW - 1.6, h: 0.7, fontFace: SANS, fontSize: 19, bold: true, color: NAVY, margin: 0 });
  s.addText(c[1], { x: X1 + 0.8, y: y + 0.82, w: COLW - 1.6, h: 0.8, fontFace: SANS, fontSize: 15.5, color: TEXT, margin: 0 });
  if (i < 4) s.addShape(p.ShapeType.chevron, { x: X1 + COLW / 2 - 0.3, y: y + 1.75, w: 0.6, h: 0.22, fill: { color: TEAL }, line: { type: "none" }, rotate: 90 });
});

// ---- Column 2 ----------------------------------------------------------
// 4. Semantic KB
card(X2, TOP, COLW, 10.6);
secTitle(X2, TOP, COLW, 4, "Semantic KB");
const edges = [["SYNERGIZES-WITH", TEAL, "co-tune → super-additive gain"],
  ["CONFLICTS-WITH", AMBER, "joint change risks SLO regression"],
  ["DEPENDS-ON", NAVY, "safe range conditioned on another knob"]];
edges.forEach((e, i) => {
  const y = TOP + 1.75 + i * 1.75;
  s.addShape(p.ShapeType.roundRect, { x: X2 + 0.6, y, w: 6.4, h: 1.15, rectRadius: 0.12, fill: { color: e[1] }, line: { type: "none" } });
  s.addText(e[0], { x: X2 + 0.6, y, w: 6.4, h: 1.15, align: "center", valign: "middle", fontFace: SANS, fontSize: 17, bold: true, color: WHITE, margin: 0 });
  s.addText(e[2], { x: X2 + 7.2, y, w: COLW - 7.8, h: 1.15, valign: "middle", fontFace: SANS, fontSize: 16, color: TEXT, margin: 0, lineSpacingMultiple: 1.05 });
});
s.addText("Edges are induced offline from pairwise co-tuning sweeps and decayed online by γᵗ from deployment telemetry, so stale couplings fade. Every recommendation carries provenance to specific KB edges & traces.",
  { x: X2 + 0.6, y: TOP + 7.3, w: COLW - 1.2, h: 3.0, fontSize: 18, color: TEXT, margin: 0, lineSpacingMultiple: 1.15, valign: "top" });

// 5. Safety Runtime
card(X2, TOP + 11.1, COLW, 8.0);
secTitle(X2, TOP + 11.1, COLW, 5, "Safety Runtime");
["Canary 5%", "Ramp 25→50%", "Full 100%"].forEach((st, i) => {
  const w = 4.15, x = X2 + 0.6 + i * (w + 0.55), y = TOP + 12.8;
  s.addShape(p.ShapeType.roundRect, { x, y, w, h: 1.5, rectRadius: 0.12, fill: { color: NAVY }, line: { type: "none" } });
  s.addText(st, { x, y, w, h: 1.5, align: "center", valign: "middle", fontFace: SANS, fontSize: 17, bold: true, color: WHITE, margin: 0 });
  if (i < 2) s.addShape(p.ShapeType.chevron, { x: x + w + 0.06, y: y + 0.45, w: 0.45, h: 0.6, fill: { color: TEAL }, line: { type: "none" } });
});
s.addText([
  { text: "Conformal gate: split-conformal τ from log D_cal gives Pr[unsafe | u<τ] ≤ α;  u ≥ τ → veto.", options: { bullet: { code: "2022" }, fontSize: 18, color: TEXT, breakLine: true, paraSpaceAfter: 9, lineSpacingMultiple: 1.1 } },
  { text: "Cost-based τ*: minimize C(τ)=c_FN·miss + c_FP·over-veto + λ·ΔSLO. Default τ=0.55 (prec/rec ≈ 0.86/0.88).", options: { bullet: { code: "2022" }, fontSize: 18, color: TEXT, breakLine: true, paraSpaceAfter: 9, lineSpacingMultiple: 1.1 } },
  { text: "ADWIN drift detection → sliding-window recalibration restores coverage.", options: { bullet: { code: "2022" }, fontSize: 18, color: TEXT, lineSpacingMultiple: 1.1 } },
], { x: X2 + 0.6, y: TOP + 14.7, w: COLW - 1.2, h: 4.2, valign: "top", margin: 0 });

// 6. Theory
card(X2, TOP + 19.6, COLW, 8.0, DEEP);
s.addShape(p.ShapeType.ellipse, { x: X2 + 0.5, y: TOP + 19.85, w: 1.0, h: 1.0, fill: { color: TEAL }, line: { type: "none" } });
s.addText("6", { x: X2 + 0.5, y: TOP + 19.85, w: 1.0, h: 1.0, align: "center", valign: "middle", fontFace: SERIF, fontSize: 30, bold: true, color: WHITE });
s.addText("Guarantees", { x: X2 + 1.75, y: TOP + 19.8, w: COLW - 2, h: 1.1, valign: "middle", fontFace: SERIF, fontSize: 30, bold: true, color: WHITE, margin: 0 });
s.addText("Thm 1 — Expected-cost decomposition", { x: X2 + 0.6, y: TOP + 21.2, w: COLW - 1.2, h: 0.7, fontSize: 18, bold: true, color: TEAL, margin: 0 });
s.addText("E[C] ≤ c_FN·π·α + c_FP·(1−π)·β_FP + λ·E[ΔSLO]", { x: X2 + 0.6, y: TOP + 21.9, w: COLW - 1.2, h: 0.9, fontSize: 18, italic: true, bold: true, color: WHITE, align: "center", fontFace: SERIF, margin: 0 });
s.addText("Prop 1 — Recalibration coverage recovery under drift", { x: X2 + 0.6, y: TOP + 23.1, w: COLW - 1.2, h: 0.7, fontSize: 18, bold: true, color: TEAL, margin: 0 });
s.addText("α′  ≤  α + 1/(m+1) + ε", { x: X2 + 0.6, y: TOP + 23.8, w: COLW - 1.2, h: 1.0, fontSize: 26, italic: true, bold: true, color: WHITE, align: "center", fontFace: SERIF, margin: 0 });
s.addText("Names the three levers (α, β_FP, ΔSLO) a deployment tunes; coverage recovers to a finite-sample slack after each drift — validated in a 30-day study.",
  { x: X2 + 0.6, y: TOP + 25.0, w: COLW - 1.2, h: 2.4, fontSize: 16.5, color: ICE, margin: 0, lineSpacingMultiple: 1.15, valign: "top" });

// ---- Column 3 ----------------------------------------------------------
// 7. Results
card(X3, TOP, COLW, 10.6);
secTitle(X3, TOP, COLW, 7, "Results");
s.addText("6 workloads × 3 server classes, 10 runs (95% CI). vs. Baseline:", { x: X3 + 0.6, y: TOP + 1.7, w: COLW - 1.2, h: 0.9, fontSize: 17, color: TEXT, margin: 0 });
const stats = [["23%", "median latency ↓"], ["28%", "P95 latency ↓"], ["31%", "anomaly rate ↓"], ["85–92%", "operator effort ↓"]];
stats.forEach((st, i) => {
  const col = i % 2, row = (i / 2) | 0;
  const x = X3 + 0.6 + col * 6.85, y = TOP + 2.7 + row * 3.6;
  s.addShape(p.ShapeType.roundRect, { x, y, w: 6.4, h: 3.25, rectRadius: 0.14, fill: { color: LIGHT }, line: { color: LINE, width: 1 } });
  s.addText(st[0], { x, y: y + 0.4, w: 6.4, h: 1.6, align: "center", fontFace: SERIF, fontSize: 46, bold: true, color: TEAL, margin: 0 });
  s.addText(st[1], { x, y: y + 2.05, w: 6.4, h: 0.9, align: "center", fontFace: SANS, fontSize: 17, color: TEXT, margin: 0 });
});

// 8. Ablation + Pareto
card(X3, TOP + 11.1, COLW, 8.0);
secTitle(X3, TOP + 11.1, COLW, 8, "Ablation & Pareto");
s.addText([
  { text: "Anomaly rate by variant (stationary):", options: { fontSize: 17, bold: true, color: NAVY, breakLine: true, paraSpaceAfter: 8 } },
  { text: "Full 2.4%   ·   w/o Dep-Graph 4.1%   ·   w/o RAG 3.6%   ·   w/o Safety 4.9%   ·   KB-only 7.1%", options: { fontSize: 17, color: TEXT, breakLine: true, paraSpaceAfter: 12, lineSpacingMultiple: 1.15 } },
  { text: "Graph + RAG drive performance; Safety Runtime drives reliability — the combination is Pareto-best.", options: { bullet: { code: "2022" }, fontSize: 17, color: TEXT, breakLine: true, paraSpaceAfter: 8, lineSpacingMultiple: 1.12 } },
  { text: "vs. Expert on the frontier: up to 17% lower latency at equal anomaly budget; 23% lower anomaly at equal throughput.", options: { bullet: { code: "2022" }, fontSize: 17, color: TEXT, lineSpacingMultiple: 1.12 } },
], { x: X3 + 0.6, y: TOP + 12.8, w: COLW - 1.2, h: 6.0, valign: "top", margin: 0 });

// 9. User study + Conclusion
card(X3, TOP + 19.6, COLW, 8.0, NAVY);
s.addShape(p.ShapeType.ellipse, { x: X3 + 0.5, y: TOP + 19.85, w: 1.0, h: 1.0, fill: { color: TEAL }, line: { type: "none" } });
s.addText("9", { x: X3 + 0.5, y: TOP + 19.85, w: 1.0, h: 1.0, align: "center", valign: "middle", fontFace: SERIF, fontSize: 30, bold: true, color: WHITE });
s.addText("User Study & Takeaway", { x: X3 + 1.75, y: TOP + 19.8, w: COLW - 2, h: 1.1, valign: "middle", fontFace: SERIF, fontSize: 27, bold: true, color: WHITE, margin: 0 });
s.addText([
  { text: "N=32 SRE/DevOps, within-subjects, approved IRB, no PII.", options: { fontSize: 17, color: ICE, breakLine: true, paraSpaceAfter: 10 } },
  { text: "−28% decision time vs. BO/RL (p<0.01);  −24% cognitive load (NASA-TLX).  All p survive Holm–Bonferroni.", options: { fontSize: 17, color: WHITE, breakLine: true, paraSpaceAfter: 12, lineSpacingMultiple: 1.15 } },
  { text: "Explainability + safety cut operator burden beyond raw performance — provenance-grounded rationale is decisive.", options: { fontSize: 17, italic: true, color: TEAL, lineSpacingMultiple: 1.15 } },
], { x: X3 + 0.6, y: TOP + 21.2, w: COLW - 1.2, h: 6.2, valign: "top", margin: 0 });

// ============================ FOOTER =====================================
s.addShape(p.ShapeType.roundRect, { x: 1.0, y: 34.75, w: 46, h: 0.95, rectRadius: 0.12, fill: { color: DEEP }, line: { type: "none" } });
s.addText("Reproducibility: a seed-fixed offline harness regenerates every table, figure, and theory check (34/34 pass).      Geunsik Lim · leemgs@gmail.com",
  { x: 1.0, y: 34.75, w: 46, h: 0.95, align: "center", valign: "middle", fontFace: SANS, fontSize: 16, italic: true, color: ICE, margin: 0 });

p.writeFile({ fileName: "semantos_poster_en.pptx" }).then(f => console.log("wrote", f));
