# Telemetry Agent Dockerfile (eBPF 기반, 호스트 헤더 마운트, bcc는 apt로 설치)

FROM python:3.10

# 1) eBPF/빌드 도구 설치 (커널 헤더는 호스트에서 마운트해 사용)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      clang \
      llvm \
      build-essential \
      cmake \
      libelf-dev \
      pkg-config \
      bpfcc-tools \
      python3-bpfcc \
      libbpfcc-dev \
    && rm -rf /var/lib/apt/lists/*

# 2) 작업 디렉토리
WORKDIR /app

# 3) Python 의존성
#    - requirements.txt에서 bcc 항목만 제거하여 pip 설치
COPY telemetry-agent/requirements.txt ./requirements.txt
RUN awk 'tolower($0) !~ /^bcc(==.*)?$/ {print}' requirements.txt > requirements.nobcc.txt && \
    python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.nobcc.txt && \
    pip install --no-cache-dir grpcio-tools

# 4) 소스 복사
COPY telemetry-agent/src/agent.py ./agent.py
RUN mkdir -p ./bpf
COPY telemetry-agent/src/bpf/trace_metrics.c ./bpf/trace_metrics.c

# 5) proto 복사 및 gRPC 스텁 생성
COPY proto/ ./proto/
RUN python -m grpc_tools.protoc -I./proto \
    --python_out=. --grpc_python_out=. \
    ./proto/semantos.proto

# 6) 실행
#    eBPF 사용을 위해 컨테이너는 privileged 권한 및 호스트 헤더/모듈 마운트가 필요
CMD ["python", "agent.py"]

