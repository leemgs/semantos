# 리뷰 반영 점검 — 2026-09-27 (최신)

AAAI-27 Phase 1 결정(Reject)과 OpenReview 리뷰 3건(a8cr: 2 Strong reject, zBDs: 3 Clear
reject, AI Reviewer)을 원문 PDF에서 다시 추출해 현재 `main`의 논문·코드와 항목별로 대조했다.
아래 표가 최신 상태이며, 그 아래 2026-09-26 기록은 이력으로 남긴다.

**이번 점검에서 새로 발견·수정한 것:** KB 서비스의 trace 검색이 Python `hash()`로 seed한
**난수 벡터**를 임베딩으로 써서 유사도 검색이 아니었고, 프로세스가 바뀌면 저장된 벡터와 질의
벡터가 맞지도 않았다(a8cr가 지적한 "가짜 구현" 유형). `kb-service/embedding.py`의 결정적
토큰 feature-hashing 임베딩으로 교체하고, 기존 인덱스는 버전이 다르면 재임베딩하며, 테스트
3개를 추가했다. 논문은 "lexically matched trace text"로 실제 구현과 일치시켰다.

| 리뷰 | 지적 | 현재 상태 (근거) |
|---|---|---|
| a8cr | LLaMA-3.1-13B | 해결. 논문·활성 코드에 없음. 실제 사용 모델은 SHA-256이 공개 파일과 일치하는 GGUF 4종과 보고 모델 ID를 기록한 API 모델 6종 |
| a8cr | sched_wake_affinity | 해결. 거부 테스트(`tests/test_safety.py`)에만 존재 |
| a8cr | Moser 무관 인용 | 해결. 참고문헌 전부 제목·저자·출처 확인(신규 LLM 참고문헌 8건 포함) |
| a8cr | 표 수치+Gaussian noise 코드 | 해결. `code/legacy/`에 격리·경고, 빌드/평가 경로에서 미사용. 모든 보고 수치는 원시 로그에서 스크립트로 산출 |
| a8cr | 설명이 피상적 | 대부분 해결. 점수식·bundle 계약·결정 경로 그림·예시 trace. KB 검색 구현을 실제 유사도 검색으로 교정(이번) |
| zBDs | 같은 입력의 전통 optimizer 대비 LLM 가치 | **실증 완료(부정적 결과).** 동일 증거로 비-LLM 선택기와 LLM 10종 비교: 개선한 모델 없음, Llama-8B는 오히려 악화. BO/RL 동일 예산 비교는 미실시 |
| zBDs | 그래프가 전부를 설명할 가능성 | 해결. graph induction이 edge를 내지 않았고, no-graph ablation은 모든 모델에서 선택 불변 |
| zBDs | 실험 설정 불충분 | 해결. 호스트·커널·사전계획·seed·기간 분할·해시·모델 digest/ID·디코딩 설정 기록 |
| zBDs | anomaly 정의·순환 논리 | 해결. 사전 deadline 기반 정의, 독립 label과 veto/rollback 분리 |
| zBDs | unsafe/수락/거부 수 | 해결. 모든 분모와 TP/FP/FN/TN 공개(5/25, 4/24 unsafe 수락) |
| zBDs | real-world vs synthetic 모순 | 해결. 실측/replay/dry-run 구분, real-world·production 주장 없음 |
| AI | Theorem 1 조건부 확률 | 해결. 정확한 비용 항등식(q=P(accept|unsafe), r=P(veto|safe))으로 교체 |
| AI | Proposition 1 거짓 부등식 | 해결. 올바른 rank gate(j/(n+1)≤α)로 교체, drift recovery 주장 철회 |
| AI | CRC/NCRC 누락 | 해결. 인용 및 차이 기술 |
| AI | baseline/SOTA/Pareto | 철회. 명시적 control·paired 비교만 제시, 우위/frontier 주장 없음 |
| AI | KB-test 누출 | 해결(범위 한정). 기간 단위 역할 분리와 lineage 검증. 단일 호스트·단일 workload family |
| AI | 다중 knob vs 단일 API | 해결(dry-run). bundle 단위 검증·veto·stage. 실제 VM transaction은 미구현 |
| AI | 완전한 decision trace | 해결. 선택 artifact·점수·관측 ID와 적용/원복 기록, 모델 prompt/응답 전부 저장 |
| AI | 설명 faithfulness(ContextCite식 삭제) | **실증 완료.** 사전 계획한 인용/비인용 삭제를 10개 모델에 실행. Phi-4만 인용 특이적 반응(그러나 남은 증거와 반대 선택), 다수는 추정 불가 또는 무변화. 수치 주장 수동 감사: 로컬 16/28, API 25/69 오류·과장 |
| AI | fast/slow path 통합 | 철회+그림. 94%/6% 수치 철회, 실제 동기 경로 그림 |
| AI | causal/unconditional safety | 해결. empirical interaction, 가정하 위험 제어로 표현 |
| AI | checkpoint provenance | 해결. 로컬 가중치 해시, API는 보고 모델·라우팅 제공자 기록(재현성 한계 명시) |
| AI | OS-R1 분류, τ 방향, 이질적 ms 집계, delay 상태 | 해결. 비교표 삭제·TuneAgent로 정확히 서술, α sweep과 혼동행렬, workload/period 분리, delay 미주장 |

**남은 한계(논문에 명시됨):** 단일 호스트·단일 periodic workload·4개 설정의 작은 과제,
BO/RL 동일 예산 비교 없음, API 모델은 비트 단위 재현 불가, 실제 VM-sysctl 배포·트래픽 격리 없음.
OpenReview의 PDF·초록은 이 저장소 수정으로 갱신되지 않으며, 재제출은 새 원고로 해야 한다.

검증: 테스트 37개 통과, 논문 본문 7쪽 이내(참고문헌 8쪽부터), 제출용 PDF 링크 0개,
undefined/overfull 경고 없음.

---

# 리뷰 반영 및 추가 실험 — 2026-09-26

이 문서는 d471d40 이후 작업공간 수정본을 설명한다. 이전 작업 기록은
`archive/REVIEW_RESPONSE_before_followup_2026-09-26.md`에 보존했다.
OpenReview 답변 제출이나 외부 PDF 교체를 수행한 것은 아니다.

**판정:** 코드·문서 정정과 이 환경에서 실행 가능한 추가 실험을 완료했다.
모델 비교/설명 충실성의 실제 추론, 다중 호스트·워크로드 일반화, 저자 제공
하드웨어 집계의 원시 검증은 완료하지 못했다. 이를 완료로 표시하지 않는다.

## 이번 추가 작업

- `controlled_kernel.py`: 사전 계획, 기간별 역할 분리, 200개 grid 측정
  프로세스(8,000개 이벤트), 학습 score/선택 및 gate 사전 고정.
- graph/표 기반 비LLM 선택기, 기본 설정, seeded random을 동일 held-out
  관측에서 비교했다. 이는 offline replay이며 독립된 live LLM 실행이 아니다.
- 학습 40회 자료의 두 요인 interaction을 bootstrap 분석했다. 유의한 edge는
  없었고, 두 informed selector가 모두 control을 선택해 개선은 0이다.
- gate replay에서 proposal/accept/veto 및 TP/FP/FN/TN, unsafe와 accepted의
  서로 다른 분모를 산출했다. 5ms에서 unsafe 25개 중 5개를 수락했고,
  8ms에서는 24개 중 4개를 수락했다. 이 실패를 논문에 그대로 넣었다.
- 별도 staged adapter가 실제 자식 스레드의 timer slack/affinity를 적용하고
  readback 후 8/16/32개 이벤트를 관측한다. 80회 중 66회 조기 중단,
  14회 완료, 80회 모두 두 원래 설정으로 복원됐다. 1,696개 관측 이벤트와
  노출 시간을 기록했다. traffic canary 또는 REST VM actuator로 주장하지 않는다.
- `analyze_controlled.py`: 입력 해시, 실제 role/source 연결, freeze 순서,
  원시 event 산술, 적용/원복 readback, 조기 중단 조건을 검사하고 표를 생성한다.
- `model_audit.py`: full/no-graph/no-retrieval/model-only 및 cited/uncited
  context deletion을 고정 seed로 실행하는 도구를 추가했다. 전체 prompt,
  모델 manifest, raw response, citation 오류와 지연시간을 기록한다.
- 설치된 Llama 3.2의 manifest를 기록하고 실제 endpoint 호출을 시도했다.
  `PermissionError: Operation not permitted`로 추론 이전에 실패했고 유효 응답은
  0개이다. 외부 모델 credential도 구성돼 있지 않다. 기록을 실패 상태로 보존했다.
- reasoner는 서로 다른 sample의 knob들을 혼합하지 않고 실제 제안된 완전한
  bundle을 선택한다. backend 오류와 전체 context/prompt/sample을 반환하며,
  context가 예산을 넘으면 잘라서 전송하지 않고 abstain한다.
- CSV 분석기는 digest 컬럼/형식, NaN, 음수, quantile 순서를 검증한다.
  선택적 raw-log 디렉터리 검증은 실제 byte hash를 확인한다. 서버와 커널을
  섞어 집계하지 않으며 weighted anomaly에 잘못된 unweighted CI를 붙이지 않는다.
- Abstract/Evaluation/Discussion/Ethics/Conclusion을 새 결과와 실제 범위에
  맞춰 수정했다. 14% 외부 집계는 초록/결론의 증거에서 제외하되 기존 저자 보고
  부록은 provenance와 unresolved 사항을 유지했다. 전체 REST 경로 그림도 추가했다.

## 후속 정리 — 2026-09-26 (재제출 준비)

- **부록 삭제:** `paper/110-reported-results.tex`(원시 로그 없는 저자 보고 수치, 내부 불일치
  14.0% vs 11.8%)를 원고에서 제거하고 본문·초록·결론의 관련 언급도 삭제했다.
- **논문 어투 정리:** "earlier/withdrawn/this revision/prior 13B" 등 수정 이력 서술을 모두
  제거했다. 제목을 결과 범위에 맞게 변경했다
  ("SemantOS: Toward Auditable, Knowledge-Grounded Kernel Tuning with Bundle-Level Risk Gating").
  affiliations의 "Research revision" 문구를 제거하고, 절 번호가 없는 AAAI 양식에서 비어 보이던
  `Section~\ref{}`를 절 이름 참조로 바꿨다.
- **관련 연구 복원:** 참고문헌 9개 → 24개(모두 본문에서 인용). 각 항목의 제목·저자·학회·연도를
  출판사/학회 기록으로 확인했다. OS-R1은 현재 TuneAgent(arXiv:2508.12551)로 제목이 바뀌었고
  **Kconfig(빌드 타임) 튜닝**임을 확인해 정확히 서술했다.
- **저장소 정리:** 루트의 `semantos-main-integration.patch`, `semantos-review-revision.zip` 삭제
  및 `.gitignore` 추가. 패키지 스크립트가 `REVIEW_RESPONSE.md`를 더 이상 포함하지 않으며,
  보조자료로 들어가는 README 문서들의 수정 이력·리뷰 언급을 중립 문구로 바꿨다.
- 검증: 테스트 35개 통과, PDF 8쪽(본문 7쪽 이내), 제출용 PDF 링크 0개, undefined
  reference/citation·overfull 경고 없음.

## 리뷰별 현재 상태

| 지적 | 처리 | 실제로 남은 사항 |
|---|---|---|
| a8cr: Llama-3.1-13B | 명칭 정정, 명시적 모델 설정, 이번 모델 manifest 기록 | Llama 3.1 과거 실험 digest 없음; 이번 추론 차단 |
| a8cr: sched_wake_affinity | 활성 후보/seed에서 제거, 실제 인터페이스 구분 | 없음; 과거 보관본/거부 테스트는 보존 |
| a8cr: Moser 무관 인용 | 현 참고문헌에서 제거 | 없음 |
| a8cr: Gaussian-noise 재현 | legacy 격리, 새로운 raw-data pipeline 및 실측 | 원래 성능 수치의 검증으로 간주하지 않음 |
| a8cr: 방법 설명 부족 | 계약/식/전체 경로 그림/코드/실험 절차/한계 추가 | 실제 LLM 기반 end-to-end 결과 없음 |
| zBDs: LLM vs 동일 정보 optimizer | 동일 정보 비LLM selector replay 실행, 모델 ablation 코드 | LLM, BO/RL의 실제 동등 예산 비교 미완료 |
| zBDs: graph가 전부 설명할 가능성 | 측정 training sweep, offline 비용, graph와 table의 동등성 제시 | 유의 edge 및 LLM의 추가 효과 없음 |
| zBDs: 설정 명세 부족 | 새 실험의 사전 계획/환경/샘플/seed/clock/해시/분모 기록 | 외부 저자 보고의 hardware/실험 commit/설정 미제공 |
| zBDs: anomaly 정의/순환 | deadline event, action label, veto, rollback을 구분 | 외부 safety 백분율의 분자·분모 미제공 |
| zBDs: unsafe/수락/거부 수 | 80개 held-out bundle의 gate count와 별도 80회 적용 count | stage 조건 자체를 독립 label로 삼는 rollback precision은 계산하지 않음 |
| zBDs: 실측/synthetic 모순 | 실측/replay/dry-run/실제 별도 adapter를 구분, 잔여 docstring 수정 | 외부 실행본은 현재 코드와 연결되지 않음 |
| AI: 조건부 확률 오류 | 비용 항등식으로 정정, 올바른 분모 구현 | 비용 항등식의 novelty는 주장하지 않음 |
| AI: 거짓 drift 부등식 | 철회, 가정하의 rank 명제, held-out miss 수 공개 | 실제 drift recovery 효과/기한은 미입증 |
| AI: CRC/NCRC 누락 | 관련 연구 인용/차이 기술 | 없음 |
| AI: baseline/SOTA/Pareto | 명시적 control, paired 정규화, 기존 superiority/frontier 철회 | 다중 operating-point SOTA/Pareto 우위 미입증 |
| AI: KB/test leakage | 새 period-level split manifest와 실제 source/timestamp 검증 | 한 family/host이므로 family/hardware 독립 일반화는 아님 |
| AI: 공동 knob/단일 API | bundle 원자적 dry-run 검사 + coherent model bundle 선택 | 실제 host VM transaction/traffic staging 미구현 |
| AI: 완전한 decision trace | 선택 artifact/score/관측 ID와 원시 적용·원복, 모델 prompt/sample 기록 | 성공한 LLM→실제 actuator 연속 trace 없음 |
| AI: 설명 faithfulness | 고정 seed의 cited/동종 uncited 삭제 도구·검증 테스트 | 모델 호출 차단으로 실증 결과 없음 |
| AI: 전체 runtime 경로 | 새 그림, sync 경로/별도 calibration/KB 요구사항 연결 | 미구현 94/6%/비동기 수치는 철회 |
| AI: causal/unconditional safety | empirical interaction/가정하의 gate로 축소 | 새로운 측정도 universal safety로 주장하지 않음 |
| AI: checkpoint provenance | 잘못된 명칭 수정, 실제 시도한 manifest와 설정 저장 | 과거 Llama 3.1 실행 출처는 미제공 |
| AI: OS-R1 분류 | 잘못된 범주 비교표 삭제 | 새 OS-R1 비교 결과 없음 |
| AI: tau 방향 | 고정 후보/strict gate, 3개 alpha sweep와 혼동행렬 공개 | 동점으로 threshold가 같아 이 데이터에서 trade-off 곡선은 아님 |
| AI: 이질적 ms 집계 | workload/period/host 분리, paired 비율과 run-level CI | 외부 14% 집계는 아직 재현 불가 |
| AI: delay 불일치 | 현 runtime/algorithm에서는 delay 주장 제거 | 부록의 외부 delay 상태는 검증 불가로 표기 |

## 결과와 검증

- 회귀 테스트 **35개 통과**: 일반 suite 30개 + raw-run 검증기 5개.
  부분 적용 실패 시 원복, 원시 로그 변조 거부, source/freeze 재검증,
  context 삭제/citation 검증, backend 실패 보존, bundle 조합 일관성 포함.
- FastAPI 등 의존성이 설치된 `/tmp/semantos-review-venv`에서 실행했다.
- 새 실험 입력 해시, 측정 코드/지원 코드 해시, 재집계 및 논문 표 일치 확인.
- 두 PDF 빌드 성공, 일반 PDF URL annotation 0개, 최종 로그에 undefined
  reference/citation 및 overfull box 없음. 추가 실험 페이지를 렌더링해 확인했다.
- `git diff --check` 통과. 과거에 추적된 Python 캐시 두 개를 제거하고 무시 규칙 추가.
- 실험을 다시 실행하지 않고 원시 로그로 통계만 재계산할 수 있다. 테스트용
  모델 fixture는 실측/모델 결과 파일에 포함하지 않았다.

- [실측 요약](code/evaluation/results/controlled-2026-09-26/summary.md)
- [사전 계획](code/evaluation/results/controlled-2026-09-26/plan.json)
- [원시 기록](code/evaluation/results/controlled-2026-09-26/runs.jsonl)
- [모델 실행 상태](code/evaluation/results/model-audit-2026-09-26/status.json)
- [새 논문 절](paper/072-controlled-evaluation.tex)

해시/재집계 검증은 저장된 데이터의 내부 일관성을 보장한다. 그것만으로
과거 실행의 독립 인증, hidden-input 부재, production 일반화가 증명되지는 않는다.
단일 공유 호스트의 Student-t 구간은 block 간 의존성과 다중 비교를 보정하지 않는다.
새 측정은 과거 6-workload/3-server 실험의 재현이 아니다.

현재 초안은 참고문헌과 저자 보고 부록을 포함하여 9페이지이다. 학회 제출 가능성이나
형식 규정 전체 준수를 의미하지 않는다. OpenReview abstract/PDF/supplement는 별도
외부 산출물이며 이번 로컬 작업으로 자동 갱신되지 않는다.

실제 모델 접근과 외부 원시 자료가 확보되어야 남은 실증 항목을 완료할 수 있다.
관련 실행 도구와 실패 기록까지 준비했으며, 접근이 없다는 사실을 긍정적 실험 결과로
대체하지 않았다.
