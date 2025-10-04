# SemantOS: Semantic Reasoning for Continual, Explainable, and Safe Kernel Auto-Tuning

본 저장소는 ICJAI '25에 발표된 "SemantOS" 논문의 재현 코드입니다. SemantOS는 eBPF 텔레메트리, 시맨틱 지식 기반(Knowledge Base), 그리고 미세 조정된 대규모 언어 모델(LLM)을 결합하여 설명 가능하고 안전한 커널 설정 자동 튜닝을 제공하는 프레임워크입니다.


# 아키텍처 개요

[cite_start]SemantOS는 gRPC로 통신하는 5개의 모듈형 구성 요소로 이루어진 지속적인 제어 루프입니다[cite: 929, 953].

| 구성 요소 | 기술 스택 | 주요 기능 |
| :--- | :--- | :--- |
| **Telemetry Agent** | Python, C/eBPF | [cite_start]커널 및 워크로드 메트릭을 초당 1% 미만의 CPU 오버헤드로 수집[cite: 953, 1003]. |
| **Semantic Knowledge Base (KB)** | Python, Neo4j, FAISS | [cite_start]튜닝 설정의 메타데이터, 의존성 그래프, 역사적 결과를 저장합니다[cite: 946, 1007]. |
| **Reasoner Engine** | Python, FastAPI, LLaMA-3.1-13B | [cite_start]KB 및 실시간 텔레메트리를 기반으로 설정 변경 사항과 자연어 설명을 생성합니다. |
| **Safety Runtime** | Go | [cite_start]단계별 롤아웃(staged rollouts), SLO(Service Level Objective) 모니터링 및 회귀 감지 시 자동 롤백을 수행합니다. |
| **Developer Interface** | TypeScript, Vue.js (시뮬레이션됨) | [cite_start]CLI/웹 대시보드를 통해 운영자가 설명을 검토하고 결정을 승인/거부할 수 있도록 합니다[cite: 964, 1017]. |

* 프로젝트 파일 구조 (semantos/)
'''bash
semantos/
├── LICENSE.md              # Apache-2.0 라이센스
├── README.md               # 프로젝트 문서화
├── Makefile                # 빌드 및 재현 스크립트 (make reproduce.all)
├── proto/
│   └── semantos.proto      # gRPC 서비스 정의
├── telemetry-agent/        # eBPF 기반 커널 메트릭 수집
│   ├── src/
│   │   ├── bpf/
│   │   │   └── trace_metrics.c  # eBPF C 코드 (골격)
│   │   └── agent.py             # Python Telemetry Agent (gRPC 클라이언트/서버)
│   └── Dockerfile
├── kb-service/             # Semantic Knowledge Base (Neo4j + FAISS 시뮬레이션)
│   ├── kb_service.py
│   └── Dockerfile
├── reasoner-engine/        # LLM Reasoning Engine (Fine-tuned LLaMA 시뮬레이션)
│   ├── reasoner_api.py     # FastAPI 기반 LLM 서비스
│   └── Dockerfile
└── safety-runtime/         # Go 기반 Safety Runtime
    ├── cmd/
    │   └── safety-runtime.go  # SLO 감시 및 자동 롤백 로직
    └── Dockerfile

'''

-----

# Getting Started

이 문서는 **SemantOS** 프로젝트를 설정하고 논문에서 제시된 **커널 자동 튜닝 실험**을 재현하는 방법을 안내합니다. SemantOS는 eBPF, Semantic Knowledge Base, 그리고 LLM 기반 Reasoner Engine으로 구성된 전체 스택 프레임워크입니다.

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

SemantOS는 **Telemetry Agent**, **Knowledge Base (KB)**, **Reasoner Engine (LLM)**, **Safety Runtime**의 네 가지 핵심 서비스로 구성됩니다.

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

## 🧹 Cleanup (정리)

실행이 완료되면 다음 명령을 사용하여 생성된 모든 컨테이너와 이미지를 정리할 수 있습니다.

```bash
# 모든 컨테이너 중지 및 제거, 빌드된 이미지 제거, 로컬 결과 파일(results/) 제거
$ make clean
```

-----