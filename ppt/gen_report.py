# AAAI-2027 compliance check report (Korean) -> PDF via reportlab.
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable)
from reportlab.lib.styles import ParagraphStyle

pdfmetrics.registerFont(TTFont("Nanum", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"))
pdfmetrics.registerFont(TTFont("NanumB", "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"))

NAVY = colors.HexColor("#1E2761")
TEAL = colors.HexColor("#0B8A6B")
AMBER = colors.HexColor("#B5761B")
INK = colors.HexColor("#1F2A44")
MUTE = colors.HexColor("#5E6B85")
LINE = colors.HexColor("#D8E0EE")
GREENBG = colors.HexColor("#E8F7F1")
AMBERBG = colors.HexColor("#FBF1DF")
HEADBG = colors.HexColor("#1E2761")
ROWALT = colors.HexColor("#F4F7FC")

def P(txt, font="Nanum", size=9.2, color=INK, leading=13, align=TA_LEFT, space=0):
    return Paragraph(txt, ParagraphStyle("s", fontName=font, fontSize=size, textColor=color,
                     leading=leading, alignment=align, spaceAfter=space))

doc = SimpleDocTemplate("aaai2027_compliance_report.pdf", pagesize=A4,
                        leftMargin=16*mm, rightMargin=16*mm, topMargin=15*mm, bottomMargin=14*mm,
                        title="AAAI 2027 Compliance Check", author="Geunsik Lim")
story = []

# --- Header ---
story.append(P("AAAI&nbsp;2027 제출 준수사항 점검 결과", "NanumB", 19, NAVY, 24))
story.append(P("SemantOS: Safe and Explainable Kernel Tuning via Semantic Reasoning and Guardrailed LLMs",
               "Nanum", 9.5, MUTE, 13, space=2))
today = datetime.date.today().isoformat()
story.append(P(f"점검 대상: <font name='NanumB'>paper/main.pdf</font> · 소스 <font name='NanumB'>paper/main.tex</font> · 부록 zip &nbsp;|&nbsp; 점검일: {today}",
               "Nanum", 8.6, MUTE, 12))
story.append(Spacer(1, 6))
story.append(HRFlowable(width="100%", thickness=1, color=LINE))
story.append(Spacer(1, 8))

# --- Verdict box ---
verdict = Table([[P("종합 판정", "NanumB", 10.5, colors.white, 14),
                  P("파일에서 검증 가능한 모든 컴플라이언스 항목 <b>통과</b> — 수정이 필요한 위반 사항 없음. "
                    "저자 본인 확인 항목 3가지만 제출 시스템에서 확인 요망.", "Nanum", 9.2, colors.white, 13)]],
                 colWidths=[26*mm, 152*mm])
verdict.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), TEAL),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (0,0), (-1,-1), 8), ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ("LINEAFTER", (0,0), (0,0), 0.6, colors.white),
]))
story.append(verdict)
story.append(Spacer(1, 12))

# --- Main table ---
def badge(text, ok):
    c = TEAL if ok == "pass" else AMBER
    label = {"pass": "통과", "warn": "확인 필요", "part": "부분"}[ok]
    return P(f"<b>{label}</b>", "NanumB", 8.6, c, 12, align=TA_CENTER)

hdr = [P("#", "NanumB", 9, colors.white, 12, TA_CENTER),
       P("이메일 준수사항", "NanumB", 9, colors.white, 12),
       P("결과", "NanumB", 9, colors.white, 12, TA_CENTER),
       P("근거 / 검증 내용", "NanumB", 9, colors.white, 12)]

rows = [
 ("1", "저자당 본선 트랙 10편 이하", "warn",
   "제출 시스템에서 저자 본인 확인 필요 (파일로 판단 불가)."),
 ("2a", "익명성 — 현재형 자기인용 없음", "pass",
   "모든 인용이 3인칭(예: AdaptiveKernel~[Lee 2022]). \"our previous work\" 류 표현 0건."),
 ("2b", "익명성 — 부록 README 식별정보 없음", "pass",
   "부록 zip 21개 파일 전체 텍스트 스캔 — 이름·소속·이메일 0건."),
 ("2c", "익명성 — PDF 메타데이터", "pass",
   "Author/Title/Subject/Keywords 모두 비어 있음. Creator=TeX, Producer=pdfTeX (무해)."),
 ("2d", "익명성 — 저자 블록", "pass",
   "표지 \"Anonymous submission\", 소속·감사글 없음 (시각 확인 완료)."),
 ("3", "총 ≤ 9페이지 · 8–9p는 참고문헌만", "pass",
   "총 9페이지. 본문 1–7p, References는 8p부터 시작 → 8–9p 참고문헌 전용."),
 ("4", "여백·글꼴·줄간격 압축 없음 (템플릿 준수)", "pass",
   "공식 aaai2027.sty 무수정. geometry/setspace/linespread/fontsize/textheight 0건, "
   "음수 vspace(압축) 0건. 폰트=Times(TeXGyreTermes) 전부 임베드, US-Letter 여백."),
 ("5", "[올해 신규] 저자 자신의 웹자료 링크 금지 (본문·부록)", "pass",
   "github/gitlab/개인/anonymous.4open 링크 0건. PDF 링크 주석 0개. "
   "참고문헌 URL은 전부 제3자 출판사(ACM·NeurIPS·arXiv·IEEE·Nature·USENIX 등, 허용)."),
 ("6", "중복 제출 금지 (타 학회 동시 심사 금지)", "warn",
   "저자 본인 확인 필요 (파일로 판단 불가)."),
 ("7", "생성형 AI 사용 공개 / AAAI 윤리", "part",
   "윤리 섹션(IRB·least-privilege 등) 포함. 원고 작성에 GenAI를 사용했다면 별도 disclosure 필요."),
]

data = [hdr]
for num, item, ok, why in rows:
    data.append([P(num, "NanumB", 8.8, NAVY, 12, TA_CENTER),
                 P(item, "Nanum", 8.8, INK, 12),
                 badge(item, ok),
                 P(why, "Nanum", 8.4, INK, 11.5)])

tbl = Table(data, colWidths=[9*mm, 52*mm, 20*mm, 97*mm], repeatRows=1)
ts = [
    ("BACKGROUND", (0,0), (-1,0), HEADBG),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ("LINEBELOW", (0,0), (-1,-1), 0.5, LINE),
    ("LINEBEFORE", (2,1), (2,-1), 0.5, LINE),
    ("LINEBEFORE", (3,1), (3,-1), 0.5, LINE),
    ("BOX", (0,0), (-1,-1), 0.8, LINE),
]
for i, (num, item, ok, why) in enumerate(rows, start=1):
    if i % 2 == 0:
        ts.append(("BACKGROUND", (0,i), (-1,i), ROWALT))
    ts.append(("BACKGROUND", (2,i), (2,i), GREENBG if ok == "pass" else AMBERBG))
tbl.setStyle(TableStyle(ts))
story.append(tbl)
story.append(Spacer(1, 14))

# --- Action items ---
story.append(P("저자 본인이 제출 시스템에서 확인할 항목", "NanumB", 12, NAVY, 16))
story.append(Spacer(1, 3))
acts = [
    ("10편 제한", "본선 트랙에 제출한 논문 수가 10편을 넘지 않는지 확인."),
    ("중복 제출", "동일 원고가 타 학회/저널에서 심사 중이 아닌지 확인 (마감일부터 정책 시행)."),
    ("GenAI 공개", "원고 작성·아이디어 도출에 생성형 AI 도구를 사용했다면 정책에 따라 disclosure 추가. "
                   "(논문의 LLM은 '연구 방법'으로 이미 기술 — '작성 도구로서의 GenAI 사용 공개'와는 별개.)"),
]
adata = []
for i, (t, d) in enumerate(acts, 1):
    adata.append([P(f"{i}", "NanumB", 10, colors.white, 13, TA_CENTER),
                  P(f"<b>{t}</b> — {d}", "Nanum", 9, INK, 13)])
atbl = Table(adata, colWidths=[9*mm, 169*mm])
astyle = [("VALIGN",(0,0),(-1,-1),"MIDDLE"),
          ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
          ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
          ("LINEBELOW",(0,0),(-1,-1),0.5,LINE),("BOX",(0,0),(-1,-1),0.8,LINE)]
for i in range(len(acts)):
    astyle.append(("BACKGROUND",(0,i),(0,i),AMBER))
atbl.setStyle(TableStyle(astyle))
story.append(atbl)
story.append(Spacer(1, 12))

story.append(HRFlowable(width="100%", thickness=0.8, color=LINE))
story.append(Spacer(1, 5))
story.append(P("결론: 현재 paper/main.pdf 는 형식·익명성·링크·페이지·템플릿 규정 측면에서 문제가 없으며, "
               "그대로 업로드 가능합니다. 위 3가지 저자 확인 항목만 점검하시면 됩니다.",
               "Nanum", 8.8, MUTE, 12))
story.append(Spacer(1, 3))
story.append(P("AAAI-27 마감: 2026-07-28 23:59 UTC-12 · 보충자료는 2026-07-31까지 수정 가능.",
               "Nanum", 8.2, MUTE, 11))

doc.build(story)
print("wrote aaai2027_compliance_report.pdf")
