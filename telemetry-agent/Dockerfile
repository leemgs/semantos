# eBPF 개발 및 실행을 위해 Ubuntu Bionic을 기반으로 합니다.
FROM ubuntu:20.04

# 환경 변수 설정
ENV DEBIAN_FRONTEND=noninteractive

# 필수 도구 및 eBPF 빌드 종속성 설치
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    clang llvm \
    libelf-dev \
    linux-headers-$(uname -r) || apt-get install -y linux-headers-generic \
    build-essential \
    git \
    libbpfcc-dev  # BCC 라이브러리 개발 파일
    
# bcc Python 라이브러리 설치
RUN pip3 install psutil bcc-tools grpcio grpcio-tools

# 작업 디렉토리 설정
WORKDIR /app

# gRPC proto 파일 컴파일 (실제 환경에서는 별도의 빌드 단계에서 수행될 수 있음)
# RUN python3 -m grpc_tools.protoc -I../proto --python_out=. --grpc_python_out=. ../proto/semantos.proto

# 소스코드 복사
COPY src/ /app/src/
COPY Dockerfile /app/

# 에이전트 실행 명령어 정의
# 호스트 커널에 접근해야 하므로 privileged 모드와 함께 실행되어야 합니다.
CMD ["python3", "src/agent.py"]