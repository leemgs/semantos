.PHONY: build.all run.services reproduce.all clean

# 서비스 정의
SERVICES = telemetry kb reasoner safety
DOCKER_COMPOSE_FILE = docker-compose.yml

# Docker Compose 파일 (가정)
# services:
#   kb: build: ./kb-service
#   reasoner: build: ./reasoner-engine
#   ...

# 모든 Docker 컨테이너 이미지 빌드
build.all:
	@echo "--- 1. Building all SemantOS Docker images ---"
	docker-compose -f $(DOCKER_COMPOSE_FILE) build

# 모든 백엔드 서비스 실행
run.services:
	@echo "--- 2. Starting all SemantOS services (KB, Reasoner, Safety) ---"
	docker-compose -f $(DOCKER_COMPOSE_FILE) up -d

# 논문 재현 스크립트 
reproduce.all: build.all run.services
	@echo "--- 3. Provisioning sample workloads and running SemantOS experiments ---"
	# 3.1. Workload provisioning (e.g., Web, OLTP, Streaming)
	./workloads/run_workload.sh --setup
	# 3.2. Start the continuous control loop and run for T hours
	docker-compose -f $(DOCKER_COMPOSE_FILE) exec safety-runtime ./safety-runtime --start-loop --duration 2h
	# 3.3. Export results to CSV
	docker-compose -f $(DOCKER_COMPOSE_FILE) exec kb cat /data/audit_log.csv > results/results_summary.csv
	@echo "--- Reproduction complete. Results saved in results/results_summary.csv ---"

clean:
	@echo "--- Cleaning up containers and images ---"
	docker-compose -f $(DOCKER_COMPOSE_FILE) down -v --rmi all
	rm -rf results/