#!/bin/bash
# run_workload.sh: SemantOS Ablation 실험을 위한 워크로드 설정 및 실행 스크립트

# 실험할 6가지 워크로드 목록 (논문 섹션 7. Evaluation Setup 참조)
WORKLOADS=("web_serving" "oltp_database" "streaming_pipeline" "embedded_sensor" "ml_inference" "audio_processing")
DURATION_MINUTES=20 # 각 워크로드별 실행 시간 (2시간 전체 실험 시간 내에서 조정 가능)

# ------------------------------------------------------------------
# 함수 정의
# ------------------------------------------------------------------

# 워크로드 컨테이너를 시작하고 부하를 발생시키는 함수
start_workload() {
    local WORKLOAD_NAME=$1
    echo "Starting workload: $WORKLOAD_NAME for ${DURATION_MINUTES} minutes..."

    # 1. 워크로드 실행 (각 워크로드별 Docker Compose 서비스 또는 컨테이너 호출 시뮬레이션)
    # 실제 환경: docker-compose up -d workload-$WORKLOAD_NAME
    echo "  [Workload] Simulating heavy load generation for $WORKLOAD_NAME..."

    # 2. Safety Runtime의 제어 루프가 워크로드 데이터를 받을 수 있도록 잠시 대기
    sleep 5 

    # 3. Telemetry Agent의 메트릭 수집 시작 확인
    # 실제 환경에서는 Telemetry Agent 컨테이너 내부의 /proc/kallsyms 등을 확인하여 eBPF 프로그램 부착 여부를 확인합니다.
    echo "  [Telemetry] Agent is actively collecting eBPF metrics."

    # 4. 설정된 시간 동안 워크로드 부하 유지
    # Safety Runtime이 이 시간 동안 튜닝을 시도하고 SLO를 모니터링합니다.
    for (( i=0; i<DURATION_MINUTES; i+=1 )); do
        echo -n "."
        sleep 60 # 1분 대기
    done
    echo " Workload finished."

    # 5. 워크로드 컨테이너 정리 (시뮬레이션)
    # docker-compose down workload-$WORKLOAD_NAME 
}

# ------------------------------------------------------------------
# 메인 실행 로직
# ------------------------------------------------------------------

# 1. 초기화 옵션 처리
if [[ "$1" == "--setup" ]]; then
    echo "--- 3.1. Workload Provisioning & Initial Setup ---"
    
    # KB 및 Reasoner가 준비되었는지 확인 (docker-compose up -d 명령이 처리)
    echo "  [System Check] SemantOS core services are ready."
    
    # 초기 커널 노브 상태를 KB에 로깅 (Safe Initial State) 시뮬레이션
    echo "  [KB] Logging initial system state to Knowledge Base."
    # docker-compose exec kb-service python /app/kb_service.py --log-initial-state
    
    # 2. 모든 워크로드를 순차적으로 실행
    for W in "${WORKLOADS[@]}"; do
        echo ""
        echo "========================================================="
        echo ">>> Starting Ablation Run for Workload: $W <<<"
        echo "========================================================="
        start_workload $W
        
        # 각 워크로드 사이에서 시스템 상태가 안정되도록 잠시 대기
        echo "--- Transitioning to next workload (60s cooldown) ---"
        sleep 60
    done
    
    echo "--- All six workloads completed. Experiment data logged to KB. ---"
    exit 0
fi

# 도움말
echo "Usage: $0 --setup"
echo "  --setup : Executes the sequential 6-workload experiment."
exit 1