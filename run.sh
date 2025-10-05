# 캐시 없이 새로 빌드 권장
docker compose -f docker-compose.yml build --no-cache kb-service

# 전체 빌드 (Makefile 대상 그대로 사용)
make build.all

# 서비스 기동
make run.services

# 재현 파이프라인
make reproduce.all