# 리뷰 반영 독립 점검 — 2026-09-26

검수 기준: `d471d40` (`Add missing evaluation artifacts, tests, and paper sources`). 사용자가 제공한 a8cr, zBDs, AI Reviewer 원문을 논문·활성 코드·저장된 측정 자료와 대조했다. `REVIEW_RESPONSE.md`의 완료 표기를 그대로 인정하지 않고 실제 파일을 확인했다. OpenReview 업로드 상태나 제출 양식의 변경 여부는 검수하지 않았다.

**전체 판정: 모든 코멘트가 실질적으로 해결된 상태는 아니다.** 명칭·인용·확률식 오류는 수정됐고 과도한 기존 주장은 상당수 철회됐다. 그러나 LLM의 추가 효과, 동일 조건 비교, 안전성, 누출 없는 일반화, 설명 충실성은 아직 검증된 실험 결과가 부족하다. 주장 철회는 올바른 정정이지만 원래의 연구 기여를 입증한 것은 아니다.

판정 기준: **완료**는 해당 오류/설명 문제의 해결, **철회**는 근거 없는 주장 제거, **부분**은 방법·구현·일부 자료만 확보, **미완료**는 요구된 실증 결과 부재를 뜻한다. 부록의 저자 보고 수치는 허위로 단정하지 않으며, 원시 자료 없이 검증된 결과로 취급하지도 않는다.

| ID | 리뷰 지적 | 판정 | 확인 근거와 남은 사항 |
|---|---|---|---|
| A1 | 존재하지 않는 LLaMA-3.1-13B | 완료 / 실험 출처 부분 | `paper/015-background_related.tex`에서 오류 정정. `code/reasoner/app.py`의 Ollama 기본 모델 제거. `train/README.md`는 훈련 예시임을 명시. 실제 비교실험의 checkpoint digest·훈련 로그는 없음. |
| A2 | 존재하지 않는 sched_wake_affinity sysctl | 완료 | 활성 후보와 seed에서 제거. related work에서 WAKE_AFFINE과 sysctl 구분. 과거 자료와 거부 테스트에 문자열이 남은 것은 활성 사용이 아님. |
| A3 | 무관한 Moser 비즈니스 논문 인용 | 완료 | 현재 `paper/reference-data.bib`에서 제거. 과거 기록은 보관. |
| A4 | 논문 표에 Gaussian noise를 더한 재현 | 철회 / 대체 실증 부분 | `code/legacy/`로 격리하고 Introduction에 명시. 활성 재현기는 원시 CSV 분석. 새 로컬 로그는 재집계 가능하지만 원래 여섯 workload·세 서버 성능을 재현하지 않음. |
| A5 | 방법이 피상적이고 반복적 | 부분 | `040-design.tex`에 점수식·bundle 계약·알고리즘·예시 추적·실구현 경계 추가. 실제 모델 추론과 전체 배포 경로의 재현 자료는 없음. |
| Z1 | 동일 정보를 쓰는 전통 최적화 대비 LLM 가치 | 부분 | `070-evaluation.tex`에 matched-information/budget 비교 설계. 부록의 BO/RL+Graph 표는 정보·예산 일치와 run-level 불확실성 미제공. LLM 효과를 분리해 입증하지 못함. |
| Z2 | offline graph 탐색이 성능을 전부 설명할 가능성 | 부분 | 비용 분리와 shared-KB 비교 설계, `evaluation/induce_graph.py` 구현. seed graph는 비어 있음. 실제 graph 구축 비용 및 동일 graph를 쓰는 no-LLM 대조 결과 없음. timer/affinity 실험은 graph+LLM 검증이 아님. |
| Z3 | 실험 설정 부족 | 부분 | 로컬 실험은 환경·부하·반복·워밍업·deadline·해시 기술. 부록 실험은 hardware/kernel/checkpoint/commit/부하/예산/분할 manifest 부재. |
| Z4 | anomaly 미정의 및 rollback과 순환논리 | 본문 완료 / 부록 부분 | 로컬 anomaly는 실패 또는 사전 deadline 초과 / 전체 작업. gate label과 rollout 구분. 부록 3.2%→1.5%의 원시 분자·분모·측정 창은 없음. |
| Z5 | unsafe/accepted/rejected 개수 필요 | 부분 | `evaluation/safety_counts.py`에 독립 label·혼동행렬·미관측 label 처리. 실제 제어의 제안·수락·거부 count, exposure, 독립 label 자료 없음. 부록은 백분율뿐. |
| Z6 | real-world와 synthetic 범위 모순 | 본문 정정 / 일관성 부분 | Abstract·Discussion·Ethics는 로컬 측정과 dry-run을 명시하고 기존 인간연구/production 주장을 철회. 부록의 외부 실행 버전은 식별되지 않았으며 reasoner docstring에 자동 rollback 설명이 잔존. |
| I1 | Theorem 1의 조건부 확률 뒤바뀜 | 완료, 기여 축소 | `040-design.tex` 비용 항등식에서 q=P(accept|unsafe), r=P(veto|safe)로 정정. P(unsafe|accept)와 구분하고 novelty/safety bound가 아님을 명시. |
| I2 | Proposition 1 거짓 부등식과 drift 검증 부족 | 오류 철회 / drift 실증 미완료 | 거짓 recovery 주장 및 30일 확인을 철회. 고정 점수·unsafe-class 교환가능성 아래 strict rank gate로 대체. 실제 drift recovery 결과 없음. |
| I3 | CRC/NCRC 관련 연구 누락 | 완료 | `015-background_related.tex`, `reference-data.bib`에 두 연구 및 차이 추가. 제한된 rank 결과를 새 drift theorem으로 주장하지 않음. |
| I4 | Baseline/SOTA/Pareto 근거 부족 | 부분 | 기존 superiority 표/잘못된 frontier 철회, baseline과 비교 프로토콜 명시. 부록 Default 비교는 집계·예산·CI 미해결. 다중 operating point와 실제 Pareto 결과 없음. |
| I5 | graph/retrieval/calibration에 test leakage 가능성 | 부분 | `validate_split.py`가 선언된 group·digest·source lineage 중복을 검사. 실제 full-system 분할 manifest·frozen graph/index/calibrator 없음. 선언 검증만으로 숨은 입력이나 실제 수집 독립성을 입증하지 못함. |
| I6 | 단일 knob API와 공동 조정 불일치 | dry-run 완료 / 실제 적용 미완료 | runtime·OpenAPI·콘솔은 동일 bundle 전체 검증·veto·단계·취소를 지원. 실제 커널 transaction/readback/rollback은 요구사항으로만 기술. reasoner의 knob별 vote 조합은 실제 bundle 일관성 실험이 없음. |
| I7 | 완전한 decision trace | 부분 | 본문은 명시적 설명용 예시. 부록은 저자 보고 실행 발췌. 실제 snapshot→전체 graph/trace IDs→prompt/응답→목표 가중치→검증→설정 readback→결과의 일관된 기록 없음. |
| I8 | provenance faithfulness 평가 | 미완료, 계획 반영 | ContextCite 인용과 cited/uncited context 삭제 비교를 명시. 실제 context intervention 실험 결과 없음. |
| I9 | fast/slow path·목표·보정·KB 업데이트 통합 설명 | 부분 / 수치 철회 | 94%/6%/10ms 철회, 현재 동기 모델 호출과 향후 요구사항 기술. 전체 경로를 연결한 새 schematic 및 실제 비동기 경로·갱신 실증은 없음. |
| I10 | causal couplings / unconditional safety 과장 | 완료, 주장 축소 | empirical interaction과 가정하의 위험 제어로 수정. rollback이 피해를 모두 되돌릴 수 없음을 명시. |
| I11 | 정확한 base checkpoint와 인용 출처 | 부분 | 모델 계열 오류는 정정. 부록은 Llama-3.1-8B-Instruct라고 보고하나 실제 digest·토크나이저·실행 commit 등 미제공. |
| I12 | OS-R1의 BO+ML/RL 분류 모순 | 철회 | 근거 없는 범주 비교표를 제거하고 삭제 이유 기술. OS-R1와의 실제 비교는 추가되지 않음. |
| I13 | 작은 tau에서 anomaly 증가하는 모순 | 설명 완료 / 실증 미완료 | 고정 후보에서 수락 집합은 축소되나 수락자 중 unsafe 비율은 단조가 아닐 수 있음을 설명. precision에서 anomaly를 만드는 코드 격리. 실제 동일 후보 tau sweep 없음. |
| I14 | 이질적 workload raw latency 집계 불명 | 본문 완료 / 부록 미해결 | 로컬 표는 workload별 분리. 부록 표의 단순 평균은 23.375→20.625ms이며 aggregate 20.0→17.2ms와 불일치. 11.8%/11.5%와 14%를 연결할 집계 규칙 없음. |
| I15 | delay 상태 prose/algorithm 불일치 | 본문 철회 / 부록 미해결 | 현재 알고리즘은 delay를 주장하지 않음. 부록에는 canary/delay 0.57이 재등장하나 구현 상태·threshold가 없다고 명시. 외부 결과를 현 runtime 동작으로 해석할 수 없음. |

**우선 해결해야 할 사항**

1. **부록의 비교·안전성 결과에 원시 증거가 없다.** `paper/110-reported-results.tex:7`은 완전한 실험행렬이 서버당 560회임을 설명하지만 실제 run inventory가 없다. `:62`의 집계 불일치, `:66`의 safety 분모 부재, `:87`의 정의되지 않은 ± 및 20회 중 6개 값만 존재하는 문제는 리뷰의 핵심 비판과 직접 겹친다. Abstract도 14%를 다시 언급한다. 단서를 추가한 것은 투명성 개선이며 결과의 검증 완료는 아니다. 원시 로그·실험 commit·모델 digest·조건·집계 규칙을 확보하고 재계산해야 한다.
2. **LLM의 기여를 분리한 실험이 없다.** 동일 KB/검색자료/안전정책/예산의 optimizer·deterministic graph policy와 LLM 비교, no-graph/no-RAG/no-LLM ablation, graph 구축 비용이 필요하다. 새 baseline과 timer-slack 실험은 이 질문에 답하지 않는다.
3. **실제 closed-loop 안전성은 미검증이다.** `code/telemetry-agent/app.py:223`은 항상 end_to_end_latency_valid=False를 반환하고 `code/reasoner/app.py:203`은 이때 추천을 중단한다. 현재 제공 경로는 실제 workload telemetry로 모델을 구동하는 시스템이 아니다. runtime은 dry-run이며 rollback counter 코드만으로 안전성 증거가 되지 않는다.
4. **trace·일관성에 구체적인 잔여 문제가 있다.** `code/reasoner/app.py:227`의 설명은 여전히 SLO 기반 자동 rollback을 수행한다고 적는다. 실제 runtime에는 없다. backend 예외는 `sample_model`에서 소거되어 본문의 실패 기록 요구도 충분히 구현되지 않았다. 부록 trace는 dirty_ratio만 변경한다고 서술하지만 현 runtime은 dirty_background_ratio도 함께 전달해야 한다. 외부 버전을 식별하거나 완전한 요청을 제공해야 연결성을 검증할 수 있다.
5. **데이터 독립성과 설명 충실성은 계획 단계이다.** 검증기를 만들었다는 사실과 실제 실험자료가 검증을 통과했다는 사실은 다르다. full-system manifest와 frozen artifacts, held-out 결과, context deletion 실험이 필요하다.
6. **작업 기록 정리가 필요하다.** `REVIEW_RESPONSE.md:108`의 ‘현재 5페이지’는 최신 8페이지 PDF와 다르다. 앞부분의 21/23개 테스트 표기는 뒤의 24개 추가 기록과 시간순 관계를 명확히 해야 한다. 최신 커밋에는 Python `.pyc` 두 개도 포함되어 있다. 이는 핵심 실증 문제와 별개의 정리 사항이다.

**검증한 것과 검증하지 않은 것**

- 동일 커밋을 `git archive`로 추출한 임시 사본에서 앞선 검수 때 의존성이 설치된 `/tmp/semantos-review-venv`로 테스트 24개 통과, `make inventory` 통과, `make -B all`로 논문 PDF 두 종류 빌드 성공을 확인했다. 커밋이 같으므로 이번 점검에서 동일 테스트를 중복 실행하지 않았다. 시스템 기본 Python에는 FastAPI가 없어 그대로는 테스트가 실행되지 않았다.
- 이번 점검에서는 임시 사본의 분석 스크립트 두 개를 실행해 원시 해시를 검증하고 통계를 재계산했다. 3,000개 baseline operation의 summary JSON과 논문 표가 일치했다. baseline 측정 코드의 해시도 manifest와 일치했다.
- 120개 process run·9,600개 timer/affinity event의 해시, readback 기록, event 산술, 학습 선택과 집계가 분석기를 통과했고 summary JSON과 논문 표가 일치했다. 두 주기의 선택 설정은 baseline이므로 선택 정책 개선은 0이다.
- 해시 일치와 재집계는 저장된 자료의 내부 일관성 증거다. 과거 하드웨어 실행의 독립 인증이나 LLM/안전성 효과의 입증은 아니다. 이번 점검에서는 새로운 커널 실험·모델 추론·Docker 통합 실행을 수행하지 않았다.
- 사용자 제공 OpenReview 화면의 구버전 abstract/TL;DR 수치는 로컬 최신 abstract와 다르다. 저장소 수정만으로 OpenReview의 PDF·abstract·supplement가 갱신됐다고 볼 수 없다. 이번 점검은 해당 외부 상태를 확인하거나 변경하지 않았다.
- 관련 연구 링크를 직접 열어 제목과 범위를 교차 확인했다: [Conformal Risk Control](https://arxiv.org/abs/2208.02814), [Non-Exchangeable Conformal Risk Control](https://arxiv.org/abs/2310.01262), [ContextCite](https://arxiv.org/abs/2409.00729).

이 검수는 새로운 보고서만 추가하며 기존 논문·코드·측정값을 변경하지 않는다. ‘모든 코멘트를 다뤘다’는 문서상 대응은 상당 부분 성립하지만, ‘모든 코멘트가 해결됐다’거나 ‘원래 성능·안전성 기여가 입증됐다’는 판정은 할 수 없다.
