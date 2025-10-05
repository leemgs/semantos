# Telemetry Agent Dockerfile (eBPF 기반)

# 1. 기본 이미지 사용 (Python 3.10)
FROM python:3.10

# 2. bcc 설치를 위한 시스템 종속성 설치 (가장 중요한 부분)
# clang, llvm, build-essential, cmake, kernel headers 등 eBPF 프로그램 컴파일에 필요한 도구 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    clang \
    llvm \
    build-essential \
    cmake \
    libelf-dev \
    linux-headers-$(uname -r) \
    libncurses5-dev \
    bison \
    flex \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# 3. 컨테이너 작업 디렉토리 설정
WORKDIR /app

# 4. 의존성 파일 복사 및 설치
# telemetry-agent 폴더 내에 있는 'requirements.txt'를 복사합니다.
COPY telemetry-agent/requirements.txt .

# 의존성 설치 (bcc, grpcio 설치)
RUN pip install --no-cache-dir -r requirements.txt

# 5. 애플리케이션 파일 및 eBPF C 코드 복사 (경로 주의)
# 프로젝트 루트(컨텍스트) 기준으로 파일들을 복사합니다.
COPY telemetry-agent/src/agent.py .
COPY telemetry-agent/src/bpf/trace_metrics.c ./bpf/

# gRPC 통신에 필요한 파일 복사 (프로토콜 파일 및 컴파일된 스텁 파일)
COPY proto/semantos.proto .
COPY semantos_pb2.py .
COPY semantos_pb2_grpc.py .

# 6. 서비스 실행 명령
# 주의: eBPF를 사용하려면 --privileged 또는 cap_add: SYS_ADMIN 권한으로 실행되어야 합니다.
CMD ["python", "agent.py"]