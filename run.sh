#!/usr/bin/env bash

# 캐시 날리고 reasoner만 먼저 확인
docker compose -f docker-compose.yml build --no-cache reasoner-engine

# 전체 빌드
make build.all

# 서비스 기동
make run.services

# 재현 파이프라인
make reproduce.all
