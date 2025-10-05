# Telemetry Agent Dockerfile (eBPF 기반)

# 1) Python 베이스 이미지
FROM python:3.10

# 2) eBPF/BCC 빌드에 필요한 패키지 설치
#    - 커널 헤더는 호스트 의존성이 있어 런타임에 마운트/호스트 제공이 필요할 수 있음
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      clang \
      llvm \
      build-essential \
      cmake \
      libelf-dev \
      linux-headers-$(uname -r) && \
    rm -rf /var/lib/apt/lists/*

# 3) 작업 디렉토리
WORKDIR /app

# 4) Python 의존성 설치 (+ gRPC 스텁 생성을 위한 grpcio-tools)
COPY telemetry-agent/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir grpcio-tools

# 5) 애플리케이션 및 eBPF 소스 복사
COPY telemetry-agent/src/agent.py ./agent.py
RUN mkdir -p ./bpf
COPY telemetry-agent/src/bpf/trace_metrics.c ./bpf/trace_metrics.c

# 6) 프로토 파일 복사 및 gRPC 스텁 생성
#    => semantos_pb2.py / semantos_pb2_grpc.py 를 빌드 시 생성
COPY proto/ ./proto/
RUN python -m grpc_tools.protoc -I./proto \
    --python_out=. --grpc_python_out=. \
    ./proto/semantos.proto

# 7) 실행
#    주의: eBPF 사용 시 컨테이너는 --privileged 또는 적절한 cap_add 권한 필요
CMD ["python", "agent.py"]

