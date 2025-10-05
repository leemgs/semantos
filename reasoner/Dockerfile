# Reasoner (LLM Inference/API) Dockerfile

# 1. 기본 이미지 사용 (파이썬 3.10 버전의 최소화된 이미지)
FROM python:3.10-slim

# 2. 시스템 라이브러리 설치
# LLM 프레임워크 또는 데이터 과학 라이브러리(FAISS 등)에 필요한 필수 빌드 도구 설치
# 만약 LLaMA-3.1-13B가 GPU 가속이 필요하다면, 이 기본 이미지 대신 CUDA 기반 이미지를 사용해야 합니다.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libblas3 \
    liblapack3 \
    && rm -rf /var/lib/apt/lists/*

# 3. 컨테이너 작업 디렉토리 설정
WORKDIR /app

# 4. 의존성 파일 복사 및 설치
# 프로젝트 루트에 있는 'base_requirements.txt'를 복사합니다.
COPY base_requirements.txt .

# 의존성 설치 (Faiss, FastAPI, Uvicorn 등 설치)
RUN pip install --no-cache-dir -r base_requirements.txt

# 5. 애플리케이션 파일 복사 (경로 주의)
# 프로젝트 루트(컨텍스트) 기준으로 reasoner 폴더 내의 파일을 복사합니다.
COPY reasoner/reasoner_api.py .

# 6. gRPC 통신에 필요한 파일 복사 (프로토콜 파일 및 컴파일된 스텁 파일)
# proto 파일을 컴파일하면 생성되는 파일들(루트 디렉토리에 생성됨을 가정)
COPY proto/semantos.proto .
# gRPC 컴파일 결과 파일:
COPY semantos_pb2.py .
COPY semantos_pb2_grpc.py .

# 7. 서비스 실행 명령
# FastAPI 애플리케이션을 Uvicorn을 이용해 실행합니다.
# 호스트 0.0.0.0, 포트 8000, reasoner_api.py 파일의 'app' 객체를 실행한다고 가정
CMD ["uvicorn", "reasoner_api:app", "--host", "0.0.0.0", "--port", "8000"]