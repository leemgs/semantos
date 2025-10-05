# KB Service (Knowledge Base) Dockerfile

# 1. 기본 이미지 사용 (파이썬 3.10 버전의 최소화된 이미지)
FROM python:3.10-slim

# 2. 시스템 라이브러리 설치
# FAISS 및 NumPy 기반 라이브러리 설치에 필요한 build-essential, BLAS/LAPACK 라이브러리 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libblas3 \
    liblapack3 \
    && rm -rf /var/lib/apt/lists/*

# 3. 컨테이너 작업 디렉토리 설정
WORKDIR /app

# 4. 의존성 파일 복사 및 설치 (수정된 부분)
# 프로젝트 루트에 있는 'base_requirements.txt'를 복사합니다.
COPY base_requirements.txt .

# 의존성 설치
# (변경) gRPC 스텁 생성을 위해 grpcio-tools도 함께 설치합니다.
RUN pip install --no-cache-dir -r base_requirements.txt && \
    pip install --no-cache-dir grpcio-tools

# 5. 애플리케이션 파일 복사 (경로 주의)
# 프로젝트 루트(컨텍스트) 기준으로 kb-service 폴더 내의 파일을 복사합니다.
COPY kb-service/kb_service.py .

# 6. gRPC 통신에 필요한 파일 복사 (프로토콜 파일 및 컴파일된 스텁 파일)
# proto 파일을 컴파일하면 생성되는 파일들(루트 디렉토리에 생성됨을 가정)
# (변경) 기존에는 semantos_pb2*.py를 COPY 했지만, 빌드 시 자동 생성하도록 변경합니다.
COPY proto/ ./proto/
RUN python -m grpc_tools.protoc -I./proto \
    --python_out=. --grpc_python_out=. \
    ./proto/semantos.proto

# 7. 서비스 실행 명령
CMD ["python", "kb_service.py"]
