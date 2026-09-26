// SemantOS — Korean research talk deck.
// Build: node gen_ko.js  ->  semantos_ko.pptx
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";              // 13.33 x 7.5 in
p.author = "Geunsik Lim";
p.title = "SemantOS (Korean)";

// ---- palette --------------------------------------------------------------
const DEEP = "0F1733", NAVY = "1E2761", TEAL = "02C39A", AMBER = "F4A261";
const ICE = "CADCFC", LIGHT = "F4F7FC", WHITE = "FFFFFF";
const TEXT = "1F2A44", MUTE = "5E6B85", LINE = "D8E0EE";
const HEAD = "Malgun Gothic", BODY = "Malgun Gothic";
const W = 13.33, H = 7.5;

const shadow = () => ({ type: "outer", color: "1E2761", opacity: 0.18, blur: 9, offset: 3, angle: 90 });

function bg(s, c) { s.background = { color: c }; }
function card(s, x, y, w, h, fill) {
  s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.10,
    fill: { color: fill || WHITE }, line: { color: LINE, width: 1 }, shadow: shadow() });
}
function numDot(s, x, y, n, c) {
  s.addShape(p.ShapeType.ellipse, { x, y, w: 0.5, h: 0.5, fill: { color: c || TEAL }, line: { type: "none" } });
  s.addText(String(n), { x, y, w: 0.5, h: 0.5, align: "center", valign: "middle",
    fontFace: HEAD, fontSize: 18, bold: true, color: WHITE });
}
// kicker + title header for light content slides
function header(s, kicker, title) {
  s.addText(kicker, { x: 0.6, y: 0.42, w: 8, h: 0.3, fontFace: HEAD, fontSize: 13, bold: true,
    color: TEAL, charSpacing: 2, margin: 0 });
  s.addText(title, { x: 0.6, y: 0.72, w: 12.1, h: 0.75, fontFace: HEAD, fontSize: 30, bold: true,
    color: NAVY, margin: 0 });
}
function pageNo(s, n) {
  s.addText(String(n).padStart(2, "0"), { x: 12.5, y: 6.95, w: 0.6, h: 0.3, align: "right",
    fontFace: BODY, fontSize: 11, color: MUTE });
  s.addText("SemantOS", { x: 0.6, y: 6.95, w: 3, h: 0.3, fontFace: BODY, fontSize: 11, color: MUTE });
}

// =========================================================================
// 1. Title (dark)
// =========================================================================
let s = p.addSlide(); bg(s, DEEP);
s.addShape(p.ShapeType.ellipse, { x: 9.7, y: -2.2, w: 6.2, h: 6.2, fill: { color: NAVY }, line: { type: "none" } });
s.addShape(p.ShapeType.ellipse, { x: 11.3, y: 3.6, w: 3.6, h: 3.6, fill: { color: "16204a" }, line: { type: "none" } });
s.addText("AAAI-27 · 시스템 · 인공지능", { x: 0.7, y: 0.85, w: 8, h: 0.4, fontFace: HEAD, fontSize: 14,
  bold: true, color: TEAL, charSpacing: 2 });
s.addText("SemantOS", { x: 0.65, y: 1.7, w: 11, h: 1.1, fontFace: HEAD, fontSize: 60, bold: true, color: WHITE });
s.addText("시맨틱 추론과 가드레일 LLM 기반\n안전하고 설명가능한 커널 튜닝", { x: 0.7, y: 2.95, w: 10.5, h: 1.3,
  fontFace: HEAD, fontSize: 26, bold: true, color: ICE, lineSpacingMultiple: 1.1 });
s.addText("Safe and Explainable Kernel Tuning via Semantic Reasoning and Guardrailed LLMs",
  { x: 0.72, y: 4.35, w: 11, h: 0.5, fontFace: BODY, fontSize: 15, italic: true, color: "9FB2D9" });
// three headline chips
const chips = [["23%", "테일 지연 P95 ↓"], ["31%", "이상 발생률 ↓"], ["85%+", "운영자 개입 ↓"]];
chips.forEach((c, i) => {
  const x = 0.72 + i * 3.15;
  s.addShape(p.ShapeType.roundRect, { x, y: 5.25, w: 2.9, h: 1.25, rectRadius: 0.1,
    fill: { color: "16204a" }, line: { color: TEAL, width: 1 } });
  s.addText(c[0], { x, y: 5.4, w: 2.9, h: 0.7, align: "center", fontFace: HEAD, fontSize: 34, bold: true, color: TEAL });
  s.addText(c[1], { x, y: 6.05, w: 2.9, h: 0.35, align: "center", fontFace: HEAD, fontSize: 13, color: ICE });
});
s.addText("Geunsik Lim  ·  leemgs@gmail.com", { x: 0.72, y: 6.9, w: 8, h: 0.35, fontFace: BODY, fontSize: 13, color: "8296C0" });

// =========================================================================
// 2. 배경 — 커널 튜닝의 어려움
// =========================================================================
s = p.addSlide(); bg(s, LIGHT);
header(s, "MOTIVATION · 배경", "커널 튜닝은 왜 어려운가");
s.addText("리눅스 커널은 스케줄링·메모리·I/O·IRQ·NUMA에 걸쳐 수백 개의 상호의존적 파라미터를 노출한다. 작은 설정 오류도 지연 급증과 꼬리 지연 불안정을 유발한다.",
  { x: 0.6, y: 1.55, w: 12.1, h: 0.7, fontFace: BODY, fontSize: 15, color: TEXT, lineSpacingMultiple: 1.15 });
const chal = [
  ["문맥 민감성", "동일 knob도 워크로드·단계마다 최적값이 달라진다. sched_latency_ns 축소는 web에서 P95 21% 개선하지만 mixed streaming에서 공정성 20% 저하."],
  ["강한 상호의존", "파라미터는 독립적이지 않다. sched_wake_affinity와 sched_min_granularity_ns를 동시에 조정하면 테일 지연을 30% 이상 낮추는 비선형 시너지."],
  ["다목적 트레이드오프", "지연을 낮추면 기아(starvation)가 늘고, 처리량을 높이면 공정성이 나빠진다. Pareto 최적 사이에서 명시적 선택이 필요하다."],
];
chal.forEach((c, i) => {
  const x = 0.6 + i * 4.07;
  card(s, x, 2.5, 3.85, 3.7);
  numDot(s, x + 0.3, 2.8, i + 1);
  s.addText(c[0], { x: x + 0.95, y: 2.83, w: 2.8, h: 0.5, fontFace: HEAD, fontSize: 18, bold: true, color: NAVY, valign: "middle", margin: 0 });
  s.addText(c[1], { x: x + 0.32, y: 3.55, w: 3.25, h: 2.5, fontFace: BODY, fontSize: 13.5, color: TEXT, lineSpacingMultiple: 1.2, margin: 0 });
});
pageNo(s, 2);

// =========================================================================
// 3. 기존 접근의 한계
// =========================================================================
s = p.addSlide(); bg(s, LIGHT);
header(s, "GAP · 기존 접근", "정적 프로파일과 블랙박스 최적화의 한계");
const rows = [
  ["정적 프로파일 / 휴리스틱", "워크로드 드리프트에 취약, 단일 파라미터 중심으로 상호작용 무시", "✗ 적응 불가"],
  ["BO / RL 블랙박스 튜너", "수백 회 시행 필요, 정상성 가정, 해석 불가, 위험한 구성 탐색으로 시스템 회귀 유발", "✗ 안전 보장 없음"],
  ["SemantOS (제안)", "지식 기반 추론 + 보정된 불확실성 + conformal 안전 런타임으로 온라인 sysctl을 안전하게 조정", "✓ 안전·설명·적응"],
];
rows.forEach((r, i) => {
  const y = 1.75 + i * 1.55;
  const hot = i === 2;
  card(s, 0.6, y, 12.1, 1.35, hot ? "EAF9F4" : WHITE);
  if (hot) s.addShape(p.ShapeType.roundRect, { x: 0.6, y, w: 12.1, h: 1.35, rectRadius: 0.10, fill: { type: "none" }, line: { color: TEAL, width: 2 } });
  s.addText(r[0], { x: 0.95, y: y + 0.16, w: 3.6, h: 1.0, fontFace: HEAD, fontSize: 17, bold: true, color: hot ? TEAL : NAVY, valign: "middle", margin: 0 });
  s.addText(r[1], { x: 4.7, y: y + 0.16, w: 5.7, h: 1.0, fontFace: BODY, fontSize: 13.5, color: TEXT, valign: "middle", lineSpacingMultiple: 1.12, margin: 0 });
  s.addText(r[2], { x: 10.5, y: y + 0.16, w: 2.0, h: 1.0, fontFace: HEAD, fontSize: 14, bold: true, align: "center", valign: "middle",
    color: hot ? TEAL : AMBER, margin: 0 });
});
pageNo(s, 3);

// =========================================================================
// 4. 핵심 아이디어 (dark section)
// =========================================================================
s = p.addSlide(); bg(s, NAVY);
s.addText("KEY IDEA", { x: 0.7, y: 0.7, w: 6, h: 0.4, fontFace: HEAD, fontSize: 14, bold: true, color: TEAL, charSpacing: 2 });
s.addText("커널을 블랙박스가 아닌\n시맨틱하게 근거화된 제어 루프로", { x: 0.7, y: 1.2, w: 12, h: 1.6,
  fontFace: HEAD, fontSize: 33, bold: true, color: WHITE, lineSpacingMultiple: 1.08 });
s.addText("관측(telemetry) → 지식 기반 추론(KB+LLM) → 보정된 불확실성 → 단계적·감사가능 배포",
  { x: 0.72, y: 3.0, w: 12, h: 0.5, fontFace: HEAD, fontSize: 16, italic: true, color: ICE });
const prin = [
  ["문맥 인지", "eBPF 텔레메트리로 실시간 시스템 상태 관측"],
  ["지식 중심 추론", "typed 의존성 그래프에 근거한 공동 튜닝"],
  ["안전 강제", "conformal τ 게이트 + 단계적 롤아웃/롤백"],
  ["지속 적응", "드리프트 감지와 재보정, KB 신선도 유지"],
];
prin.forEach((c, i) => {
  const x = 0.7 + i * 3.05;
  s.addShape(p.ShapeType.roundRect, { x, y: 3.9, w: 2.85, h: 2.6, rectRadius: 0.1, fill: { color: "16204a" }, line: { color: "2C3A6E", width: 1 } });
  numDot(s, x + 0.28, 4.18, i + 1, TEAL);
  s.addText(c[0], { x: x + 0.24, y: 4.9, w: 2.4, h: 0.5, fontFace: HEAD, fontSize: 16, bold: true, color: WHITE, margin: 0 });
  s.addText(c[1], { x: x + 0.24, y: 5.4, w: 2.45, h: 1.0, fontFace: BODY, fontSize: 12.5, color: ICE, lineSpacingMultiple: 1.15, margin: 0 });
});

// =========================================================================
// 5. 아키텍처
// =========================================================================
s = p.addSlide(); bg(s, LIGHT);
header(s, "ARCHITECTURE · 아키텍처", "5개 컴포넌트로 닫힌 제어 루프");
const comps = [
  ["① Telemetry Agent", "eBPF·유저스페이스 5초 주기 샘플링 (<1% CPU)"],
  ["② Knowledge Base", "typed/signed 의존성 그래프 + FAISS 트레이스 (γ 감쇠)"],
  ["③ Reasoner (LLM)", "RAG 프롬프트 → knob·value·rationale·uncertainty"],
  ["④ Safety Runtime", "conformal τ 게이트, canary→ramp→full, 자동 롤백"],
  ["⑤ Operator Console", "설명·프로비넌스·롤백 제어를 운영자에게 제시"],
];
comps.forEach((c, i) => {
  const y = 1.75 + i * 0.98;
  card(s, 0.6, y, 8.3, 0.82, WHITE);
  s.addText(c[0], { x: 0.9, y: y, w: 3.1, h: 0.82, fontFace: HEAD, fontSize: 15.5, bold: true, color: NAVY, valign: "middle", margin: 0 });
  s.addText(c[1], { x: 4.0, y: y, w: 4.8, h: 0.82, fontFace: BODY, fontSize: 12.5, color: TEXT, valign: "middle", lineSpacingMultiple: 1.1, margin: 0 });
  if (i < 4) s.addShape(p.ShapeType.chevron, { x: 4.35, y: y + 0.82, w: 0.5, h: 0.16, fill: { color: TEAL }, line: { type: "none" }, rotate: 90 });
});
// right side loop note
card(s, 9.15, 1.75, 3.55, 4.65, "0F1733");
s.addText("닫힌 루프", { x: 9.4, y: 1.95, w: 3.1, h: 0.4, fontFace: HEAD, fontSize: 16, bold: true, color: TEAL });
s.addText([
  { text: "telemetry → recommendation → deployment → feedback", options: { bullet: false, breakLine: true, fontSize: 13, color: WHITE, bold: true, paraSpaceAfter: 8 } },
  { text: "3개 핵심 JSON 엔드포인트가 루프를 닫는다:", options: { breakLine: true, fontSize: 12, color: ICE, paraSpaceAfter: 4 } },
  { text: "POST /get_recommendations", options: { breakLine: true, fontSize: 12, color: WHITE, fontFace: "Consolas" } },
  { text: "POST /apply", options: { breakLine: true, fontSize: 12, color: WHITE, fontFace: "Consolas" } },
  { text: "POST /log_outcome", options: { breakLine: true, fontSize: 12, color: WHITE, fontFace: "Consolas", paraSpaceAfter: 8 } },
  { text: "빠른 경로(≈94% 스냅샷)는 10ms 내, <3% CPU로 결정", options: { fontSize: 12, color: ICE, lineSpacingMultiple: 1.15 } },
], { x: 9.4, y: 2.45, w: 3.1, h: 3.8, valign: "top", margin: 0 });
pageNo(s, 5);

// =========================================================================
// 6. 지식 기반 추론
// =========================================================================
s = p.addSlide(); bg(s, LIGHT);
header(s, "SEMANTIC KB · 지식 기반", "typed 의존성 그래프에 근거한 공동 추론");
const edges = [
  ["SYNERGIZES-WITH", TEAL, "함께 바꾸면 초가산적 이득 — 반드시 공동 튜닝"],
  ["CONFLICTS-WITH", AMBER, "동시 변경 시 SLO 회귀 위험 — 상충 회피"],
  ["DEPENDS-ON", NAVY, "한 knob의 안전 범위가 다른 값에 조건부 — 순서 준수"],
];
edges.forEach((e, i) => {
  const y = 1.75 + i * 1.15;
  card(s, 0.6, y, 7.0, 0.98, WHITE);
  s.addShape(p.ShapeType.roundRect, { x: 0.85, y: y + 0.24, w: 2.55, h: 0.5, rectRadius: 0.08, fill: { color: e[1] }, line: { type: "none" } });
  s.addText(e[0], { x: 0.85, y: y + 0.24, w: 2.55, h: 0.5, align: "center", valign: "middle", fontFace: HEAD, fontSize: 12, bold: true, color: WHITE, margin: 0 });
  s.addText(e[2], { x: 3.65, y: y, w: 3.8, h: 0.98, valign: "middle", fontFace: BODY, fontSize: 12.5, color: TEXT, lineSpacingMultiple: 1.1, margin: 0 });
});
card(s, 7.85, 1.75, 4.85, 3.53, "0F1733");
s.addText("오프라인 유도 + 온라인 감쇠", { x: 8.1, y: 1.95, w: 4.4, h: 0.4, fontFace: HEAD, fontSize: 15, bold: true, color: TEAL });
s.addText([
  { text: "엣지는 pairwise 공동 튜닝 스윕에서 유도: 결합 효과가 단일 효과의 합에서 벗어난 정도(부트스트랩 유의)로 부호·가중치 결정.", options: { breakLine: true, fontSize: 12.5, color: WHITE, lineSpacingMultiple: 1.2, paraSpaceAfter: 8 } },
  { text: "가중치는 배포 텔레메트리로 γᵗ 감쇠·갱신 → 오래된 결합은 자연 소멸.", options: { fontSize: 12.5, color: ICE, lineSpacingMultiple: 1.2 } },
], { x: 8.1, y: 2.45, w: 4.4, h: 2.7, valign: "top", margin: 0 });
s.addText("각 추천은 특정 KB 엣지·트레이스로의 프로비넌스를 갖는다 — 왜 그렇게 튜닝했는지 감사 가능.",
  { x: 0.6, y: 5.5, w: 12.1, h: 0.8, fontFace: BODY, fontSize: 14, italic: true, color: NAVY, align: "center" });
pageNo(s, 6);

// =========================================================================
// 7. 안전 런타임
// =========================================================================
s = p.addSlide(); bg(s, LIGHT);
header(s, "SAFETY RUNTIME · 안전 런타임", "보정된 불확실성 게이트 + 단계적 롤아웃");
// stage flow
const stages = [["Canary", "5%"], ["Ramp", "25→50%"], ["Full", "100%"]];
stages.forEach((st, i) => {
  const x = 1.1 + i * 3.4;
  s.addShape(p.ShapeType.roundRect, { x, y: 1.9, w: 2.8, h: 1.2, rectRadius: 0.1, fill: { color: NAVY }, line: { type: "none" }, shadow: shadow() });
  s.addText(st[0], { x, y: 2.02, w: 2.8, h: 0.5, align: "center", fontFace: HEAD, fontSize: 20, bold: true, color: WHITE });
  s.addText(st[1] + " 트래픽", { x, y: 2.55, w: 2.8, h: 0.4, align: "center", fontFace: HEAD, fontSize: 13, color: TEAL });
  if (i < 2) s.addShape(p.ShapeType.chevron, { x: x + 2.85, y: 2.28, w: 0.45, h: 0.45, fill: { color: TEAL }, line: { type: "none" } });
});
s.addText("각 단계는 실시간 P95 SLO 가드로 감시 — 위반 시 즉시 자동 롤백하고 OptimizationTrace를 KB에 기록",
  { x: 1.1, y: 3.25, w: 11.1, h: 0.5, align: "center", fontFace: BODY, fontSize: 13.5, color: TEXT });
const sf = [
  ["conformal τ 게이트", "보정 로그 D_cal에서 분할 conformal로 τ 산출: Pr[unsafe | u<τ] ≤ α. u ≥ τ 이면 veto."],
  ["비용 기반 τ 선택", "C(τ)=c_FN·미탐 + c_FP·과탐 + λ·ΔSLO 최소화. 기본 τ=0.55 (정밀도/재현율 ≈0.86/0.88)."],
  ["드리프트 재보정", "ADWIN으로 드리프트 감지, 슬라이딩 윈도우 재보정으로 목표 커버리지 회복."],
];
sf.forEach((c, i) => {
  const x = 0.6 + i * 4.07;
  card(s, x, 4.0, 3.85, 2.35, WHITE);
  s.addText(c[0], { x: x + 0.28, y: 4.2, w: 3.3, h: 0.5, fontFace: HEAD, fontSize: 15, bold: true, color: TEAL, margin: 0 });
  s.addText(c[1], { x: x + 0.28, y: 4.72, w: 3.32, h: 1.5, fontFace: BODY, fontSize: 12.5, color: TEXT, lineSpacingMultiple: 1.18, margin: 0 });
});
pageNo(s, 7);

// =========================================================================
// 8. 이론적 보장
// =========================================================================
s = p.addSlide(); bg(s, LIGHT);
header(s, "THEORY · 이론적 보장", "기대비용 분해와 드리프트 커버리지 회복");
card(s, 0.6, 1.8, 6.0, 4.5, WHITE);
s.addText("정리 1 — 기대비용 분해", { x: 0.9, y: 2.0, w: 5.4, h: 0.5, fontFace: HEAD, fontSize: 18, bold: true, color: NAVY, margin: 0 });
s.addText("E[C] ≤ c_FN·π·α  +  c_FP·(1−π)·β_FP  +  λ·E[ΔSLO]",
  { x: 0.9, y: 2.6, w: 5.4, h: 0.6, fontFace: "Cambria", fontSize: 15, italic: true, bold: true, color: TEAL, align: "center" });
s.addText([
  { text: "안전 위험 (c_FN·π·α): conformal 미탐률 α가 통제", options: { bullet: { code: "2022" }, breakLine: true, fontSize: 13, color: TEXT, paraSpaceAfter: 6 } },
  { text: "효율 손실 (c_FP·(1−π)·β_FP): 불필요한 veto 비용", options: { bullet: { code: "2022" }, breakLine: true, fontSize: 13, color: TEXT, paraSpaceAfter: 6 } },
  { text: "성능 저하 (λ·ΔSLO): 롤백 전 노출 구간 상한", options: { bullet: { code: "2022" }, fontSize: 13, color: TEXT } },
], { x: 1.0, y: 3.4, w: 5.3, h: 2.0, valign: "top", margin: 0 });
s.addText("배포가 조정할 세 레버(α, β_FP, ΔSLO)를 명시한다.", { x: 0.9, y: 5.7, w: 5.4, h: 0.5, fontFace: BODY, fontSize: 12.5, italic: true, color: MUTE, margin: 0 });

card(s, 6.9, 1.8, 5.8, 4.5, "0F1733");
s.addText("명제 1 — 재보정 커버리지 회복", { x: 7.2, y: 2.0, w: 5.2, h: 0.5, fontFace: HEAD, fontSize: 18, bold: true, color: TEAL, margin: 0 });
s.addText("α′  ≤  α  +  1/(m+1)  +  ε", { x: 7.2, y: 2.65, w: 5.2, h: 0.7, fontFace: "Cambria", fontSize: 22, italic: true, bold: true, color: WHITE, align: "center" });
s.addText([
  { text: "드리프트(총변동 거리 ≤ ε) 후 크기 m 슬라이딩 윈도우가 채워지면 실현 미탐율 α′ 이 위 상한을 만족.", options: { breakLine: true, fontSize: 13.5, color: ICE, lineSpacingMultiple: 1.25, paraSpaceAfter: 8 } },
  { text: "ε→0 이면 α′ → α + 1/(m+1): 목표 커버리지가 유한표본 슬랙 내로 회복.", options: { fontSize: 13.5, color: WHITE, lineSpacingMultiple: 1.25 } },
], { x: 7.2, y: 3.5, w: 5.2, h: 2.4, valign: "top", margin: 0 });
s.addText("30일 드리프트 스터디에서 매 드리프트 후 커버리지 회복·롤백 정밀도 >0.85 로 실증.",
  { x: 0.6, y: 6.55, w: 12.1, h: 0.4, align: "center", fontFace: BODY, fontSize: 12.5, italic: true, color: NAVY });
pageNo(s, 8);

// =========================================================================
// 9. 평가 결과 (bar chart)
// =========================================================================
s = p.addSlide(); bg(s, LIGHT);
header(s, "RESULTS · 평가", "6개 워크로드 · 3개 서버 · 10회 반복 (95% CI)");
const cats = ["Median 지연↓", "P95 지연↓", "이상률↓"];
const chartData = [
  { name: "AdaptiveKernel", labels: cats, values: [12.5, 15, 18.5] },
  { name: "OS-R1", labels: cats, values: [15, 17.5, 21] },
  { name: "BO/RL", labels: cats, values: [18.5, 21, 23] },
  { name: "SemantOS", labels: cats, values: [23, 28, 31] },
];
s.addChart(p.ChartType.bar, chartData, {
  x: 0.6, y: 1.75, w: 8.1, h: 4.7, barDir: "col", barGrouping: "clustered",
  chartColors: [ICE, "9AB0DE", AMBER, TEAL],
  showLegend: true, legendPos: "b", legendFontFace: BODY, legendFontSize: 11, legendColor: TEXT,
  showValue: true, dataLabelPosition: "outEnd", dataLabelFontFace: BODY, dataLabelFontSize: 9, dataLabelColor: TEXT, dataLabelFormatCode: '0"%"',
  valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
  catAxisLabelFontFace: BODY, catAxisLabelFontSize: 12, catAxisLabelColor: NAVY,
  valAxisMaxVal: 38, valAxisMinVal: 0,
});
// stat callouts
const stats = [["23%", "Median 지연 감소 (최대)"], ["28%", "P95 지연 감소 (최대)"], ["31%", "이상률 감소 (최대)"], ["85–92%", "운영자 튜닝 노력 감소"]];
stats.forEach((st, i) => {
  const y = 1.75 + i * 1.2;
  card(s, 8.95, y, 3.75, 1.05, WHITE);
  s.addText(st[0], { x: 9.2, y: y + 0.06, w: 1.5, h: 0.9, fontFace: HEAD, fontSize: 26, bold: true, color: TEAL, valign: "middle", align: "left", margin: 0 });
  s.addText(st[1], { x: 10.5, y: y + 0.06, w: 2.05, h: 0.9, fontFace: BODY, fontSize: 12, color: TEXT, valign: "middle", lineSpacingMultiple: 1.05, margin: 0 });
});
s.addText("† AdaptiveKernel·OS-R1 은 문헌 보고치(설정 상이) — 맥락용. BO/RL·Expert 만 동일 조건 재현.",
  { x: 0.6, y: 6.55, w: 8.1, h: 0.4, fontFace: BODY, fontSize: 10.5, italic: true, color: MUTE });
pageNo(s, 9);

// =========================================================================
// 10. Ablation & Pareto (bar chart)
// =========================================================================
s = p.addSlide(); bg(s, LIGHT);
header(s, "ABLATION · 구성요소 분해", "그래프·RAG는 성능을, 안전 런타임은 신뢰성을 견인");
const av = [
  { name: "이상률(%)", labels: ["Full\n(KB+RAG+Safety)", "w/o Dep-Graph", "w/o RAG", "w/o Safety", "KB only"], values: [2.4, 4.1, 3.6, 4.9, 7.1] },
];
s.addChart(p.ChartType.bar, av, {
  x: 0.6, y: 1.8, w: 7.4, h: 4.5, barDir: "col",
  chartColors: [TEAL, "9AB0DE", "9AB0DE", AMBER, AMBER],
  chartColorsOpacity: [100, 100, 100, 100, 100],
  showLegend: false, showTitle: false,
  showValue: true, dataLabelPosition: "outEnd", dataLabelFontFace: BODY, dataLabelFontSize: 11, dataLabelColor: TEXT, dataLabelFormatCode: '0.0"%"',
  valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
  catAxisLabelFontFace: BODY, catAxisLabelFontSize: 10.5, catAxisLabelColor: NAVY,
  valAxisMaxVal: 8, valAxisMinVal: 0, barGapWidthPct: 40,
});
card(s, 8.25, 1.8, 4.45, 4.5, "0F1733");
s.addText("Pareto 우위", { x: 8.5, y: 2.0, w: 4.0, h: 0.45, fontFace: HEAD, fontSize: 17, bold: true, color: TEAL });
s.addText([
  { text: "동일 이상 예산에서 지연 최대 17%↓", options: { bullet: { code: "2022" }, breakLine: true, fontSize: 13.5, color: WHITE, paraSpaceAfter: 10, lineSpacingMultiple: 1.15 } },
  { text: "동일 처리량에서 이상률 23%↓", options: { bullet: { code: "2022" }, breakLine: true, fontSize: 13.5, color: WHITE, paraSpaceAfter: 10, lineSpacingMultiple: 1.15 } },
  { text: "의존성 그래프 제거 시 지연 19.5→21.4ms, 이상 2.4→4.1% — 시너지 손실", options: { bullet: { code: "2022" }, breakLine: true, fontSize: 13.5, color: ICE, paraSpaceAfter: 10, lineSpacingMultiple: 1.15 } },
  { text: "안전 제거 시 이상률 4.9%로 급등", options: { bullet: { code: "2022" }, fontSize: 13.5, color: ICE, lineSpacingMultiple: 1.15 } },
], { x: 8.5, y: 2.6, w: 3.95, h: 3.6, valign: "top", margin: 0 });
pageNo(s, 10);

// =========================================================================
// 11. 사용자 연구
// =========================================================================
s = p.addSlide(); bg(s, LIGHT);
header(s, "HUMAN FACTORS · 사용자 연구", "N=32 SRE/DevOps · within-subjects · 승인된 IRB");
const us = [["28%", "의사결정 시간 감소\n(vs BO/RL, p<0.01)"], ["24%", "인지부하 감소\n(NASA-TLX, vs BO/RL)"], ["0.42–0.58", "설명 유용성 우위\n(Cliff's δ)"]];
us.forEach((c, i) => {
  const x = 0.6 + i * 4.07;
  card(s, x, 1.85, 3.85, 2.2, WHITE);
  s.addText(c[0], { x: x + 0.2, y: 2.05, w: 3.45, h: 0.9, align: "center", fontFace: HEAD, fontSize: 40, bold: true, color: TEAL, margin: 0 });
  s.addText(c[1], { x: x + 0.2, y: 3.0, w: 3.45, h: 0.9, align: "center", fontFace: BODY, fontSize: 13, color: TEXT, lineSpacingMultiple: 1.15, margin: 0 });
});
card(s, 0.6, 4.35, 12.1, 1.95, "0F1733");
s.addText("설계 시사점", { x: 0.9, y: 4.55, w: 4, h: 0.4, fontFace: HEAD, fontSize: 16, bold: true, color: TEAL });
s.addText("32명 실무자(경력 5–15년)가 사고 분류·구성 선택·근거 판단 3개 과제를 baseline / expert / BO·RL / SemantOS 4개 조건에서 수행. 모든 p-값은 Holm–Bonferroni 보정 통과. 참가자들은 증거 추적과 프로비넌스 검증 설명을 결정적 요인으로 지목 — 설명가능성과 안전 설계가 원시 성능 이상의 인지 부담 경감을 준다.",
  { x: 0.9, y: 4.95, w: 11.5, h: 1.25, fontFace: BODY, fontSize: 13, color: ICE, lineSpacingMultiple: 1.2, margin: 0 });
pageNo(s, 11);

// =========================================================================
// 12. 결론 (dark closing)
// =========================================================================
s = p.addSlide(); bg(s, DEEP);
s.addShape(p.ShapeType.ellipse, { x: -2.0, y: 4.4, w: 5.5, h: 5.5, fill: { color: NAVY }, line: { type: "none" } });
s.addText("CONCLUSION", { x: 0.7, y: 0.7, w: 6, h: 0.4, fontFace: HEAD, fontSize: 14, bold: true, color: TEAL, charSpacing: 2 });
s.addText("SemantOS: 안전·설명·적응을 1급으로", { x: 0.7, y: 1.2, w: 12, h: 0.8, fontFace: HEAD, fontSize: 32, bold: true, color: WHITE });
const con = [
  ["지식 근거화된 순차 결정", "typed 의존성 그래프 + RAG LLM 추론으로 프로비넌스를 가진 설명가능 액션"],
  ["conformal 안전 런타임", "기대비용 분해(정리1)와 드리프트 커버리지 회복(명제1)을 갖춘 단계적 롤아웃"],
  ["광범위한 실증", "6 워크로드·3 서버, Pareto 우위 지연/이상 트레이드오프, 32명 사용자 연구"],
];
con.forEach((c, i) => {
  const y = 2.25 + i * 1.35;
  s.addShape(p.ShapeType.roundRect, { x: 0.7, y, w: 11.9, h: 1.15, rectRadius: 0.09, fill: { color: "16204a" }, line: { color: "2C3A6E", width: 1 } });
  numDot(s, 1.0, y + 0.32, i + 1, TEAL);
  s.addText(c[0], { x: 1.75, y: y + 0.12, w: 4.3, h: 0.9, valign: "middle", fontFace: HEAD, fontSize: 16, bold: true, color: WHITE, margin: 0 });
  s.addText(c[1], { x: 6.1, y: y + 0.12, w: 6.3, h: 0.9, valign: "middle", fontFace: BODY, fontSize: 13, color: ICE, lineSpacingMultiple: 1.12, margin: 0 });
});
s.addText("재현: seed 고정 오프라인 하니스로 모든 표·그림·이론 검증을 재생성 (34/34 PASS).   Geunsik Lim · leemgs@gmail.com",
  { x: 0.7, y: 6.55, w: 12, h: 0.5, fontFace: BODY, fontSize: 12.5, italic: true, color: "8296C0" });

p.writeFile({ fileName: "semantos_ko.pptx" }).then(f => console.log("wrote", f));
