# 리뷰 반영 및 실측 작업 기록

대상: 사용자가 제공한 AAAI-27 submission 4088의 a8cr, zBDs, AI Reviewer 의견.
기준 원본: Git `25ec0ca`. 이 문서는 **로컬 수정 기록**이며 OpenReview에 제출한 답변이 아니다.
제공된 결정문은 Reject / final decision이다. 재심이나 재제출 가능성을 주장하지 않는다.

## 이번 작업에서 실제로 한 일

- 논문 수치를 넣고 노이즈를 더하던 코드·데이터를 `code/legacy/`로 격리했다.
  과거 PDF/ZIP/발표자료/형식 점검 보고서는 `archive/rejected-2026-09-25/`에 보존했다.
  원래 기록을 새로운 실측인 것처럼 고쳐 쓰지 않았다.
- 현재 호스트에서 SQLite 커밋, 파일 fsync, 압축/검증을 직접 실행했다.
  각 10회 × 100개 측정 작업, 총 **3,000건**의 원시 시간을 기록했다.
  워밍업은 회당 10건으로 통계에서 제외했다. 측정 스크립트, 원시 CSV,
  환경, 원시 파일 SHA-256, 반복별 통계가 모두 `code/evaluation/`에 있다.
- 새 측정표를 논문에 반영했다. 이것은 **로컬 무변경 기준 성능**이다.
  SemantOS 개선율, 원래 여섯 워크로드·세 서버의 재현으로 주장하지 않는다.
- 이론, 모델 명칭, 실제 커널 인터페이스, API/묶음 처리, 점수 의미,
  데이터 출처 및 실험 범위를 수정했다. 현재 런타임의 실제 기능은 dry-run이다.

## 리뷰별 처리

| 지적 | 반영 내용과 위치 | 상태 / 남은 증거 |
|---|---|---|
| a8cr: Llama-3.1-13B는 존재하지 않음 | `reasoner/app.py`의 잘못된 기본값 제거, `train/`을 제안 설정으로 표시, 논문 모델 출처 수정 | 수정 완료. 실제 사용 모델을 다른 모델로 사후 치환하지 않음; 새 모델 실험은 미실시 |
| a8cr/AI: sched_wake_affinity | 활성 후보·시드에서 제거, Linux WAKE_AFFINE 기능과 sysctl 구분 | 수정 완료. 다른 파라미터로 바꿔 과거 효과를 유지하지 않음 |
| a8cr: Moser 등 부적절한 인용 | 해당 인용 및 확인되지 않은 비교표 제거, 현재 주장에 필요한 6개 1차 출처로 참고문헌 재구성 | 수정 완료; 원래 참고문헌은 Git/과거 ZIP 보존 |
| a8cr: 표 수치에 Gaussian noise를 더하는 재현 | 코드·산출물 격리, 기존 재현 명령은 오류로 중단, 실측 경로 분리 | 수정 완료. 이전 34/34 PASS는 성능 증거로 철회 |
| a8cr: 방법 설명 부족 | 점수 식, 묶음 정책, 단계, 구현/설계 경계와 예시 추적 추가 | 현재 구현에 맞춰 수정 |
| zBDs: LLM vs 같은 정보의 전통 최적화 | 동일 KB/검색자료/정책/예산의 최적화 비교와 no-LLM 실험 명시 | 프로토콜 작성 완료; 비교실험 결과는 아직 없음 |
| zBDs: 오프라인 탐색이 성능을 전부 설명할 가능성 | 비용 분리, cold/shared-KB 비교, `evaluation/induce_graph.py`에 원시 sweep 기반 상호작용 계산 구현 | 코드·방법 작성 완료; 프로세스별 timer/affinity sweep 추가 완료; 원래 VM knob/graph 실험은 별도 환경 필요 |
| zBDs: 실험 설정 불충분 | 실제 로컬 CPU/커널/버전·워크로드 명령·워밍업·반복수·deadline·시계·해시 기록 | 로컬 실측 완료. 기존 S1/S2/S3 설정을 측정했다고 주장하지 않음 |
| zBDs: anomaly 정의 및 순환논리 | 오류 또는 사전 deadline 초과 / 전체 요청으로 정의; unsafe label과 veto/rollback 분리 | 원고·실측 분석·카운터 수정 |
| zBDs: unsafe/accepted/rejected 개수 | `safety_counts.py`에 혼동행렬·분모·미관측 라벨·rollback 별도 카운트 구현 | 코드 검증 완료; 실제 제어 실험 로그는 없음 |
| zBDs: real-world vs synthetic 모순 | 기존 성능/인간연구 결과 주장 제거; 새 실측 범위와 시뮬레이션 범위를 일관되게 기술 | 수정 완료 |
| AI: 정리의 조건부 확률 뒤바뀜 | 비용 **항등식**으로 정정, q=P(accept\|unsafe), r=P(veto\|safe), 선택위험과 구별 | 증명·코드·분모 테스트 수정 |
| AI: drift 회복 부등식 오류 | 거짓 회복 정리 삭제, 고정 점수·unsafe-class 교환가능성의 순위 명제로 대체 | 정확한 순위 열거 테스트 통과; drift 회복은 주장하지 않음 |
| AI: 관련 conformal 연구 누락 | CRC / Non-Exchangeable CRC 인용 및 차이 기술 | 수정 완료 |
| AI: baseline/비교/Pareto 근거 부족 | 기존 SOTA 수치/전선 그림 철회, 명시적 baseline·공통 예산·다중 operating point 프로토콜 | 원고 수정 완료; 비교효과 증거는 미완료 |
| AI: KB/검색/보정 test leakage | 전 단계 분리 규칙, `validate_split.py`의 group/hash/source-lineage 검증 | 코드·테스트 완료; 실제 새로운 데이터 분할 필요 |
| AI: 개별 knob API와 공동 조정 불일치 | `proposed` 필드 통일, 동일 bundle 검증/거부/단계/취소, 콘솔도 전체 bundle 전달 | API·콘솔 회귀검사 완료; 실제 kernel transaction은 구현된 것으로 주장하지 않음 |
| AI: 완전한 decision trace | 식과 출처·정책·임계값·묶음 결정을 연결한 예시, JSONL gate 기록 | 예시는 명시적으로 예시; 실제 LLM 추적 결과는 아님 |
| AI: provenance faithfulness | ContextCite 관련 연구 및 cited/uncited context 제거 실험 정의 | 프로토콜 완료; 모델 접근 후 실행 필요 |
| AI: fast/slow path, 목표·보정·KB 업데이트 | 미구현 94%/6%·비동기·10 ms 수치 삭제, 현재 동기 경로와 향후 요건 구분 | 수정 완료 |
| AI: causal couplings / unconditional safety | empirical interaction / assumption-dependent risk로 축소 | 수정 완료 |
| AI: OS-R1 분류 모순 | 근거가 불충분한 범주 비교표 자체 제거 | 수정 완료 |
| AI: tau 방향/이상률 모순 | 작은 tau=더 적게 수락, min(rank,cost,cap); 이상률을 precision에서 만드는 코드 격리 | 코드·테스트 완료; 새 tau 실측 비교는 미실시 |
| AI: 이질적 latency ms 집계 | 새 표는 워크로드별 분리, 이후 비교는 baseline 정규화 | 수정 완료 |
| AI: delay 상태 불일치 | 미구현 delay 및 가짜 immutable logging 주장 삭제 | 수정 완료 |

## 직접 수행한 실측 결과

환경: i5-3570, 4 logical CPUs, Linux 6.17.0-23-generic, RAM 32,739,220 KiB.
각 지표는 10회 실행 통계의 평균; CI는 반복 간 Student-t 95% 구간 반폭이다.

| 워크로드 | median ms | P95 ms | 50 ms 초과 또는 오류 |
|---|---:|---:|---:|
| 파일 fsync | 1.9030 ± 0.0115 | 2.0353 ± 0.0432 | 0 / 1,000 |
| SQLite commit | 1.8703 ± 0.0186 | 2.1871 ± 0.2728 | 0 / 1,000 |
| zlib 압축+검증 | 1.4743 ± 0.0084 | 2.0375 ± 0.3555 | 0 / 1,000 |

데이터: [summary](code/evaluation/results/local-2026-09-26/summary.md),
[원시 CSV](code/evaluation/results/local-2026-09-26/operations.csv),
[환경·측정 설정](code/evaluation/results/local-2026-09-26/manifest.json).
단일 공유 호스트·짧은 직렬 부하이므로 실행 간 완전한 독립성, 큐잉 부하,
production 일반화, zero risk 또는 커널 튜닝 성능을 주장하지 않는다.

## 현재 세션에서 후속 비교실험이 막힌 구체적 이유

- 세 개 VM sysctl 모두 `os_write_access=false`; 세션 파일시스템 정책도
  작업 디렉터리와 `/tmp` 외 쓰기를 허용하지 않는다. 이 제한을 우회하지 않았다.
- Docker CLI는 있으나 `/var/run/docker.sock` 연결은 permission denied.
- 외부 pip 다운로드는 DNS/network 제한으로 실패. 코드 검증에 필요한 FastAPI
  0.115.0/Pydantic 2.8.2는 로컬 캐시에서 격리 venv에 설치해 검증을 계속했다.
- 이 대화·저장소에는 기존에 설명한 측정 절차의 문서나 별도 실험 서버 접속
  대상이 없다. workload 스크립트는 고정 숫자 출력기였으며, 현행 진입점은 실제
  로컬 측정기로 바꿨다. 실제 커널 actuator와 원래 여섯 workload adapter도 없다.

**사용자가 측정을 대신 돌릴 필요는 없다.** 다음 단계에 필요한 것은 기존 측정
절차가 있는 위치와, 내가 실행할 수 있는 격리 실험 호스트/권한/모델 접근이다.
접근이 생겨도 아직 구현되지 않은 실제 actuator·workload adapter와 비교 제어기를
먼저 만들고 검증해야 하므로, 숫자만 실행하면 원래 주장 전체가 자동으로 복구되는
상태라고 말하지 않는다. 이 후속 구현·측정·분석 작업도 에이전트가 수행할 작업이다.

사용자만 확인할 부분은 실제 모델/외부 실험자료가 존재한다면 그 위치, 그리고
인간연구를 유지하려는 경우 실제 참여·동의·기관 심의 기록이다. 현 수정본은
인간연구 주장을 제거했으므로 새 IRB 절차를 진행해야만 수정본을 볼 수 있는 것은 아니다.

## 확인한 1차 자료

- [Meta: Llama 3.1 release](https://ai.meta.com/blog/meta-llama-3-1/)
- [Linux v6.4 scheduler features](https://raw.githubusercontent.com/torvalds/linux/v6.4/kernel/sched/features.h)
- [Linux VM sysctl documentation](https://kernel.org/doc/html/v6.7/admin-guide/sysctl/vm.html)
- [Conformal Risk Control](https://arxiv.org/abs/2208.02814)
- [Non-Exchangeable Conformal Risk Control](https://arxiv.org/abs/2310.01262)
- [ContextCite](https://proceedings.neurips.cc/paper_files/paper/2024/hash/adbea136219b64db96a9941e4249a857-Abstract-Conference.html)

## 최종 검증

- 회귀검사 **21/21 통과**: 순위 보장의 정확 열거, 작은 표본/동점/NaN,
  cost cap 방향, drift detector 합계, 묶음 전체 거부·취소, 잘못된 보정 요청의
  원자적 거부, 빈 요청에서 추천 재생성 방지, 실패 샘플의 신뢰도 부풀림 방지,
  콘솔의 전체 묶음 전달, 데이터 누출·상호작용·미관측 라벨 처리.
- FastAPI 0.115.0, Pydantic 2.8.2, httpx 0.28.1, AnyIO 4.11.0에서 검사.
  sandbox에서 worker-thread의 selector wakeup이 지연되어 HTTP 검사는 실제
  ASGI 경로에 짧은 event-loop timer와 timeout을 두었다. endpoint를 mock하여
  통과시킨 검사가 아니며, 소켓 기반 다중 서비스 배포 검증과는 다르다.
- 논문 일반 PDF와 참고문헌 링크 PDF 빌드 성공. 현재 5페이지이며 일반 PDF의
  링크 주석은 0개. 새 측정표 값과 이론/표 배치 확인. 전체 학회 규정 준수나
  현재 제출 가능 여부를 이 검사로 보장하지 않는다.
- 활성 Python 구문 검사 및 `git diff --check` 통과.
- 실제 호스트 sysctl 변경, Docker 통합 실행, LLM 추론, 비교 성능실험은 미실시.

## 원격 main 통합

원격 `4f85c63`의 원시 run-level CSV 검증기, 스키마, 테스트를 보존했다.
`make reproduce RAW_RUNS=...`는 이 검증기를 실행하며 과거 수치 생성기를
실행하지 않는다. 기존의 재현 명령 중단 설명은 과거 합성 경로에 해당한다.
통합 후 검사는 기존 21개와 원격 검증기 2개, 총 23개이다.

## 추가 실행: 실제 프로세스별 커널 설정 비교

사용자 요청에 따라 호스트 전체 sysctl 권한 없이 실행 가능한 독립 측정기를
구현하고 실험을 완료했다. 새 자식 프로세스마다 timer slack 50us/1ms와
CPU affinity 전체/CPU 0의 네 조합을 실제 적용하고 커널 readback을 검증했다.
2ms/5ms 주기, 학습 5블록 + 이후 평가 10블록, 각 80개 이벤트로
**120개 프로세스·9,600개 원시 이벤트**를 기록했다. 설정 선택은 평가 전에
파일로 고정했다. 기존 dry-run runtime을 실제 actuator로 바꿨다는 의미는 아니다.

두 주기 모두 학습 선택은 기본 대조 설정(50us, 전체 CPU)이었다. 평가 P95는
각각 89.5±9.2us, 94.2±6.9us였다. 따라서 선택 정책의 기본값 대비 개선은
0이며, 이를 성능 향상으로 포장하지 않았다. 네 설정 전체 결과, 블록별 paired
차이, 200us deadline 초과 분모, 원시 타임스탬프·설정 readback·해시를 보관하고
논문 표와 본문에 반영했다. 호스트·워크로드 독립 평가나 LLM 효과는 아니다.

- [측정 코드](code/evaluation/measure_kernel_local.py)
- [분석 코드](code/evaluation/analyze_kernel_local.py)
- [실측 결과](code/evaluation/results/kernel-local-2026-09-26/summary.md)

로컬 Ollama에 모델 manifest가 존재하는 것을 확인했으나, CLI가 필요한
127.0.0.1:11434 연결은 `socket: operation not permitted`로 차단된다.
따라서 모델 추론을 실행했다고 보고하지 않는다. GitHub 쓰기는 이미
`MCP tool call requires approval, but approval policy is never`로 거부되었고,
작업공간 .git도 읽기 전용이다. 이 제한은 사용자에게 측정을 떠넘길 사유가
아니며, 가능한 실험·분석·PDF 생성·병합용 패치 준비는 직접 완료한다.

최종 추가 검증: 회귀 테스트 24개 통과(기존 23개 + 새 실측 해시 검증/변조 거부 테스트 1개).

## 사용자 제공 실측 보고서 반영 및 정정

사용자가 reference result라는 표기는 오타이며 실제 측정 결과라고 정정했다. 이에 `paper/110-reported-results.tex`에 사용자 보고 실측 결과로 수록하고, Evaluation과 Conclusion에도 출처와 한계를 명시했다. 가상 데이터로 분류하지 않는다. 단, 이 환경에서 직접 실행한 실측과는 별도이며 원시 로그·run CSV·해시·실험 commit은 제공되지 않았다.

성능·method·workload·safety 표와 실행 trace를 반영했다. workload 평균은 Default 23.375ms, Full 20.625ms로 aggregate 20.0/17.2ms와 다르다. 평균의 비율 개선은 11.8%, workload별 개선의 평균은 11.5%다. 집계 가중치가 없어 원인을 단정하지 않고 두 표를 보존했다. Rules+Graph 대비 8.4%는 정책 간 차이이며 단독으로 LLM의 인과적 기여를 입증하지 않는다. BO/RL 대비 차이는 4.4%/3.3%다. Safety 분모, 20회 원시 기록, ±의 정의를 임의 생성하지 않았다.
