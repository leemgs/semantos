# 파이썬 기반 KB 서비스를 위한 기본 이미지
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 종속성 설치 (FAISS 및 Neo4j 드라이버에 필요할 수 있음)
# FAISS는 BLAS/LAPACK이 필요할 수 있으므로 빌드 시간을 최소화하기 위해 slim 이미지를 사용합니다.
RUN apt-get update && apt-get install -y \
    build-essential \
    libblas3 liblapack3 \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 종속성 설치
# neo4j는 그래프 DB 드라이버, faiss-cpu는 벡터 인덱싱 라이브러리입니다.
COPY requirements.txt .
# requirements.txt 내용:
# neo4j
# faiss-cpu
# grpcio
# grpcio-tools
# numpy
RUN pip install --no-cache-dir -r requirements.txt

# 소스코드 복사
COPY kb_service.py /app/
# gRPC proto 파일도 복사되어야 합니다. (별도의 빌드 단계 가정)

# Knowledge Base 서비스는 Reasoner Engine의 요청을 처리하기 위해 gRPC 포트를 열어야 합니다.
EXPOSE 50052 

# 서비스 실행 명령어 정의
# KB 서비스는 독립적으로 실행되거나, Neo4j 컨테이너와 함께 실행될 수 있습니다.
CMD ["python", "kb_service.py"]