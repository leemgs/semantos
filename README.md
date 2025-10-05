# SemantOS: Semantic Reasoning for Continual, Explainable, and Safe Kernel Auto-Tuning

본 저장소는 "SemantOS" 논문의 재현 코드입니다. SemantOS는 eBPF 텔레메트리, 시맨틱 지식 기반(Knowledge Base), 그리고 미세 조정된 대규모 언어 모델(LLM)을 결합하여 설명 가능하고 안전한 커널 설정 자동 튜닝을 제공하는 프레임워크입니다.

## 아키텍처 개요
SemantOS는 gRPC로 통신하는 5개의 모듈형 구성 요소로 이루어진 지속적인 제어 루프입니다.
  
| 구성 요소 | 기술 스택 | 주요 기능 |
| :--- | :--- | :--- |
| **Telemetry Agent** | Python, C/eBPF | 커널 및 워크로드 메트릭을 초당 1% 미만의 CPU 오버헤드로 수집. |
| **Knowledge Base (KB)** | Python, Neo4j, FAISS | 튜닝 설정의 메타데이터, 의존성 그래프, 역사적 결과를 저장합니다. |
| **Reasoner** | Python, FastAPI, LLaMA-3.1-13B | KB 및 실시간 텔레메트리를 기반으로 설정 변경 사항과 자연어 설명을 생성합니다. |
| **Safety Runtime** | Go | 단계별 롤아웃(staged rollouts), SLO(Service Level Objective) 모니터링 및 회귀 감지 시 자동 롤백을 수행합니다. |
| **Operator Console** | TypeScript, Vue.js (시뮬레이션됨) | CLI/웹 대시보드를 통해 운영자가 설명을 검토하고 결정을 승인/거부할 수 있도록 합니다. |

## SemantOS 프로젝트 파일 구조
요청하신 형식에 맞춰 SemantOS 프로젝트의 모든 생성 파일 및 폴더를 포함한 최종 구조를 출력합니다.

semantos/
├── LICENSE.md                   # 프로젝트 라이선스 (Apache-2.0)
├── README.md                    # 프로젝트 개요, 아키텍처 및 사용 방법 문서
├── Makefile                     # 빌드 및 재현 자동화 스크립트 (예: make reproduce.all)
├── base_requirements.txt        # 공통 Python 패키지 의존성 정의
├── docker-compose.yml           # 전체 마이크로서비스 오케스트레이션 설정
├── run.sh                       # 빌드 및 서비스 전체 실행용 스크립트
│
├── proto/                       # gRPC 서비스 인터페이스 정의 디렉토리
│   ├── semantos.proto           # 서비스 간 메시지 및 API 인터페이스 정의
│   ├── semantos_pb2.py          # Python용 gRPC 메시지 스텁 (자동 생성)
│   └── semantos_pb2_grpc.py     # Python용 gRPC 서비스 스텁 (자동 생성)
│
├── kb-service/                  # Knowledge Base 서비스 (Neo4j/FAISS 시뮬레이션)
│   ├── kb_service.py            # 트레이스 로깅 및 RAG 기반 컨텍스트 검색 로직
│   └── Dockerfile               # KB 서비스 컨테이너 빌드 설정
│
├── reasoner/                    # LLM Reasoner 서비스 (추론 및 설명 생성)
│   ├── reasoner_api.py          # FastAPI 기반 LLM 추론 API 서버
│   └── Dockerfile               # Reasoner 컨테이너 빌드 설정
│
├── safety-runtime/              # Go 기반 Safety Runtime (SLO 감시 및 자동 제어)
│   ├── cmd/
│   │   └── safety-runtime.go    # SLO 모니터링, 롤백, 커널 튜닝 제어 루프 로직
│   └── Dockerfile               # Safety Runtime 컨테이너 빌드 설정
│
├── telemetry-agent/             # eBPF 기반 커널 메트릭 수집 및 전송 모듈
│   ├── requirements.txt         # Telemetry Agent 전용 Python 의존성
│   ├── Dockerfile               # Telemetry Agent 컨테이너 빌드 설정
│   └── src/
│       ├── agent.py             # 커널 메트릭 수집 및 gRPC 전송 Python 에이전트
│       └── bpf/
│           └── trace_metrics.c  # eBPF C 코드 (커널 트레이스 수집)
│
├── operator-console/            # 운영자 대시보드 (Vue.js + gRPC-Web)
│   ├── nginx.conf               # Nginx 설정 (정적 파일 서빙 및 gRPC-Web 프록시)
│   ├── Dockerfile               # Operator Console 컨테이너 빌드 설정
│   └── src/                     # Vue.js 프론트엔드 애플리케이션
│       ├── App.vue              # 루트 컴포넌트
│       ├── main.ts              # Vue 애플리케이션 진입점
│       ├── components/
│       │   └── TuningApproval.vue  # 튜닝 권장사항 승인/거부 UI 컴포넌트
│       └── proto/
│           ├── semantos_grpc_web_pb.d.ts  # gRPC-Web 클라이언트 서비스 타입 정의
│           └── semantos_pb.d.ts           # gRPC 메시지 타입 정의
│
└── workloads/                   # 벤치마크 및 실험 워크로드 실행 스크립트
    └── run_workload.sh          # 실험 워크로드 자동화 실행 스크립트

-----

# Getting Started
이 문서는 **SemantOS** 프로젝트를 설정하고 논문에서 제시된 **커널 자동 튜닝 실험**을 재현하는 방법을 안내합니다. SemantOS는 eBPF, Knowledge Base, 그리고 LLM 기반 Reasoner으로 구성된 전체 스택 프레임워크입니다.

## 📋 Prerequisites (선행 조건)

실험 재현을 위해서는 다음 소프트웨어 및 하드웨어 조건이 필요합니다.

1.  **운영 체제:** **Linux Kernel 5.x 이상**을 실행하는 시스템. (eBPF 기능 지원 필수)
2.  **컨테이너 도구:** **Docker** 및 **Docker Compose** (또는 Docker CLI)
3.  **빌드 도구:** `make` 유틸리티
4.  **Go:** Safety Runtime 컴파일을 위한 **Go 1.20+** (Docker 사용 시 내부적으로 처리됨)

## 💾 Installation & Setup (설치 및 설정)

모든 서비스는 Docker 컨테이너로 격리되어 실행되며, gRPC 프로토콜을 사용하여 통신합니다.

### 1\. Repository Clone

먼저, 프로젝트 저장소를 로컬 시스템에 복제합니다.

```bash
git clone https://github.com/your-username/semantos.git
cd semantos
```

### 2\. gRPC Protobuf Compilation

각 서비스가 통신할 수 있도록 `semantos.proto` 파일을 각 언어(Python, Go)의 스텁 코드로 컴파일해야 합니다.

```bash
# 필요한 경우 grpcio-tools 설치
pip install grpcio grpcio-tools

# Python 코드 생성 (Telemetry, KB, Reasoner)
python3 -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/semantos.proto

# Go 코드 생성 (Safety Runtime)
# Go 환경 설정이 필요하며, 외부 라이브러리(protoc-gen-go)가 필요합니다.
# go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
# go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
# protoc -I proto --go_out=safety-runtime --go-grpc_out=safety-runtime proto/semantos.proto
```

> ⚠️ **참고:** `make reproduce.all` 명령은 대부분의 빌드 과정을 Docker 내에서 처리하지만, 로컬에서 개발할 때는 위 과정이 필요할 수 있습니다.

## ⚙️ Running the Services (서비스 실행)

SemantOS는 **Telemetry Agent**, **Knowledge Base (KB)**, **Reasoner (LLM)**, **Safety Runtime**의 네 가지 핵심 서비스로 구성됩니다.

### 1\. Single Command Reproduction (논문 재현)

논문의 모든 핵심 실험을 단일 명령으로 재현할 수 있습니다. 이 명령은 모든 Docker 이미지를 빌드하고, 컨테이너를 시작하며, 실험 워크로드를 실행하고, 최종 결과를 CSV 파일로 내보냅니다.

```bash
# 모든 구성 요소를 빌드하고 실험을 2시간 동안 실행하는 것을 시뮬레이션합니다.
$ make reproduce.all
```

### 2\. Manual Startup (수동 실행)

개별 서비스의 디버깅이나 테스트를 위해 수동으로 시작할 수 있습니다.

**A. 모든 컨테이너 이미지 빌드**

```bash
$ make build.all
```

**B. 백엔드 서비스 실행 (KB, Reasoner, Safety Runtime)**

```bash
# Knowledge Base와 Reasoner, Safety Runtime을 백그라운드에서 실행합니다.
$ make run.services 
```

**C. Telemetry Agent 실행**

Telemetry Agent는 **eBPF** 접근이 필요하므로, 호스트의 **`--privileged`** 모드로 실행해야 합니다.

```bash
# Telemetry Agent를 시작하여 커널 메트릭 수집 루프를 시작합니다.
docker-compose up -d telemetry-agent
```

**D. Operator Console 실행**

```bash
docker-compose up -d
```
웹 브라우저에서 **http://localhost:8080**으로 접속하여 Operator Console에 접근합니다. 
(이때, gRPC-Web 통신은 Nginx Proxy를 통해 Safety Runtime으로 전달됩니다.)
이 화면은 SemantOS의 Human-in-the-Loop 메커니즘을 시각화하며, Safety Runtime이 운영자의 최종 승인을 기다리는 동안 표시됩니다.
 아래의 테이블은 Vue.js/TypeScript 컴포넌트인 TuningApproval.vue의 실행 결과를 보여주며, 논문의 핵심 요구 사항인 **설명 가능성(Explainability)**과 **안전성(Safety)**을 반영합니다.


## SemantOS Operator Console 실행 화면 (시뮬레이션)

제가 코드로 구현한 **Operator Console (Vue.js/TypeScript)**를 실제로 빌드하고 실행했을 때, 사용자에게 보이게 될 웹 화면의 모습을 Markdown 형식으로 시뮬레이션하여 보여드립니다. 이 화면은 **SemantOS** 아키텍처의 핵심인 **Human-in-the-Loop** 제어 메커니즘을 나타냅니다.

---


### 1. 화면 구성 요소

이 데모 화면은 Vue.js/TypeScript 컴포넌트인 `TuningApproval.vue`의 실행 결과를 보여주며, 논문의 핵심 요구 사항인 **설명 가능성(Explainability)**과 **안전성(Safety)**을 반영합니다.

| 영역 | 설명 | 연관 백엔드 모듈 |
| :--- | :--- | :--- |
| **Pending Action** | 현재 시스템에 적용 대기 중인 커널 튜닝 매개변수를 표시합니다. 이 예시에서는 메모리 관리 노브인 `vm.swappiness`의 값을 낮추는 것을 제안합니다. | **Reasoner**이 생성한 `TuningRecommendation` |
| **Uncertainty Score** | **LLM**이 이 특정 추론에 대해 느끼는 불확실성을 백분율로 표시합니다. 운영자는 이 점수를 통해 위험도를 직관적으로 평가할 수 있습니다. (예: 8.00%는 낮은 불확실성) | **Reasoner** |
| **LLM Rationale (Explainability)** | **Knowledge Base (KB)**에서 검색된 과거 트레이스(Vector Retrieval)를 근거로 하여, 왜 이 변경이 필요한지 자연어로 설명합니다. 이 부분이 SemantOS의 핵심 강점입니다. | **Reasoner** & **Knowledge Base** |
| **Approve & Apply** | 운영자가 튜닝을 승인할 경우, **Safety Runtime**의 `ApplyConfiguration` gRPC 엔드포인트가 호출되어 설정이 적용되고 SLO 모니터링이 시작됩니다. | **Safety Runtime** |
| **Reject & Log Fail** | 운영자가 튜닝을 거부할 경우, **Safety Runtime**을 통해 거부 트레이스가 **Knowledge Base**의 `LogOutcome`에 기록됩니다. 이는 LLM이 **실패 경험**으로부터 학습하여 다음 권장 사항의 정확도를 높이는 데 사용됩니다. | **Safety Runtime** & **Knowledge Base** |

이 인터페이스를 통해 SemantOS는 완전 자동화와 수동 제어 사이의 균형을 유지하며, 최종 결정권은 항상 숙련된 시스템 운영자에게 부여됩니다.

### 2. 화면 시뮬레이션 

| 요소 | 설명 |
| :--- | :--- |
| **타이틀** | **SemantOS Operator Console: Critical Action Pending** |
| **상태** | **Pending Action: Kernel Knob Tuning** |
| **Knob Name** | `vm.swappiness` |
| **Proposed Value** | `1` (기존 값: `60`) |
| **Uncertainty Score** | **8.00%** (낮은 불확실성/높은 신뢰도) |
| **Predicted Impact** | P95 Latency: **-15%** / Throughput: **+5%** |
| **LLM Rationale (Explainability)** | **"Knowledge Base의 벡터 트레이스 검색 결과 및 현재 높은 I/O 대기열 상태 분석에 따르면, 메모리 집약적인 OLTP 워크로드에서 `vm.swappiness`를 1로 설정하는 것이 P95 지연 시간을 15% 감소시키며 SLO 위반 위험이 낮음을 입증했습니다."** |
| **제어 버튼** | **✅ Approve & Apply** (녹색) |
| **제어 버튼** | **❌ Reject & Log Fail** (빨간색) |

---

### 3. 화면 구성 요소별 역할

이 인터페이스는 운영자가 LLM의 결정에 대해 **최종적인 안전 점검**을 수행할 수 있도록 설계되었습니다.

#### 설명 가능성 (Explainability) 제공
* **Rationale** 필드가 핵심입니다. **Reasoner (LLM)**은 **Knowledge Base (KB)**에서 가져온 **과거 경험**을 근거로 제시하므로, 운영자는 단순히 '왜?'라는 질문에 대한 답변을 넘어, **'어떤 증거'**에 기반한 결정인지 이해할 수 있습니다.

#### 안전성 (Safety) 확보
* **Uncertainty Score**와 **Predicted Impact**를 통해 LLM의 자신감과 예상되는 결과를 사전에 알 수 있습니다.
* **Approve & Apply** 버튼은 **Safety Runtime**의 `ApplyConfiguration` gRPC API를 호출하여 설정 적용을 시작합니다.
* **Reject & Log Fail** 버튼은 거부 결정을 KB에 **'실패 트레이스'**로 기록하여, LLM이 다음 번 추론 시 이 부정적인 경험을 학습에 반영하도록 합니다.


### 4. 실행 및 운영 중 생성/수정되는 파일 목록
SemantOS의 5개 컴포넌트(`telemetry-agent`, `kb-service`, `reasoner-engine`, `safety-runtime`, `developer-interface`)를 실행하고 운영하는 과정에서 **지속적인 학습(Continual Learning) 결과**, **운영 로그**, **실험 결과** 등의 파일들을 생성합니다. 

| 컴포넌트 | 생성/수정 파일 | 설명 | 연관성 |
| :--- | :--- | :--- | :--- |
| **Knowledge Base (`kb-service`)** | `kb/data/optimization_traces.db` (또는 `.jsonl`) | **Safety Runtime**이 `LogOutcome` gRPC를 호출할 때마다 기록되는 **과거 튜닝 경험(트레이스)** 데이터베이스 파일입니다. LLM의 재학습(Continual Learning)에 사용됩니다. | **지속적 학습 데이터** |
| | `kb/data/faiss_index.bin` | KB 서비스가 튜닝 트레이스의 임베딩 벡터를 저장하는 **FAISS 벡터 인덱스 파일**입니다. | **RAG 검색 인덱스** |
| | `kb/data/audit_log.csv` | 시스템의 모든 튜닝 시도, 롤백, SLO 위반 여부 등이 기록되는 **감사 로그 파일**입니다. | **운영/감사 로그** |
| **Safety Runtime** | `/proc/sys/vm/swappiness` 등 커널 파일 | `ApplyConfiguration` gRPC가 승인될 때 **실제로 값이 변경되는** 커널 매개변수 파일입니다. | **시스템 설정 변경** |
| **Telemetry Agent** | `/tmp/semantos_ebpf_metrics` (pipe/socket) | eBPF 프로그램(`trace_metrics.c`)이 수집한 커널 레벨 메트릭을 사용자 공간의 `agent.py`로 전달하기 위해 사용하는 **임시 통신 파일** (파이프 또는 소켓)입니다. | **실시간 데이터** |
| **Reasoner** | `reasoner/models/llama_ft_latest.gguf` | 지속적인 학습을 통해 KB에 새로 기록된 트레이스 데이터로 **LLM이 미세 조정(Fine-tuning)될 경우** 업데이트되는 모델 파일입니다. | **업데이트된 LLM** |
| **Makefile/실험** | `results/results_summary.csv` | `make reproduce.all` 명령을 실행했을 때, 모든 컴포넌트의 제어 루프가 종료된 후 , per_workload_results와 같은 **실험 결과들을 집계**하여 저장하는 최종 파일입니다. (논문의 **Table 2** 해당) | **최종 실험 결과** |

* **Telemetry Agent**: 데이터를 생성하여 메모리/네트워크를 통해 전송하며, 영구적인 파일을 생성하지 않습니다 (임시 파이프/소켓 사용).
* **Safety Runtime**: 시스템 파일(`proc/sys/`)을 직접 수정하고, 그 결과를 **KB 서비스**를 통해 로깅합니다.
* **Operator Console**: 브라우저에서 실행되는 프론트엔드이므로, 서버 측에 영구적인 파일을 생성하지 않습니다.
* **Knowledge Base**: 시스템의 영구적인 기억 장치로서 **데이터 파일**을 주로 생성하고 관리합니다.



## 🧹 Cleanup (정리)

실행이 완료되면 다음 명령을 사용하여 생성된 모든 컨테이너와 이미지를 정리할 수 있습니다.

```bash
# 모든 컨테이너 중지 및 제거, 빌드된 이미지 제거, 로컬 결과 파일(results/) 제거
$ make clean
```

-----
