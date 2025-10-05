package main

import (
	"log"
	"time"
	// TODO: gRPC 사용 시 아래를 해제하고 실제 구현에 맞춰 사용하세요.
	// "context"
	// "fmt"
	// "net"
	// "os"
	// "google.golang.org/grpc"
	// pb "semantos/proto"
)

const (
	// Safety Runtime의 gRPC 리스닝 포트
	port = ":50051"
	// 예시: P95 지연 시간의 최대 허용치 (ms)
	sloMaxP95Latency = 50.0 
	// 연속적인 SLO 위반이 감지될 때 자동 롤백을 트리거하는 임계값
	rollbackThreshold = 3 
)

// SafetyRuntimeServer는 SemantosControl gRPC 서비스를 구현합니다.
// type SafetyRuntimeServer struct {
// 	pb.UnimplementedSemantosControlServer
// 	// ... 시스템 상태 및 이전 값 저장을 위한 맵 또는 구조체
// }

// ApplyConfiguration은 튜닝 권장 사항을 받아 시스템에 적용하고 SLO 모니터링을 시작합니다.
// func (s *SafetyRuntimeServer) ApplyConfiguration(ctx context.Context, req *pb.TuningRecommendation) (*pb.ApplyResponse, error) {
func ApplyConfiguration(knob, value string) bool {
	// 1. Staged Rollout (단계적 롤아웃) 로직 시작 (예: Canary 그룹에만 적용)
	log.Printf("[SafetyRuntime] Applying staged configuration change: %s = %s", knob, value)
	
	// 2. Kernel Knob 적용 시뮬레이션
	// 실제 환경: /proc/sys 파일을 덮어쓰거나 sysctl 명령을 사용합니다.
	// if err := os.WriteFile(fmt.Sprintf("/proc/sys/%s", knob), []byte(value), 0644); err != nil {
	// 	log.Printf("Error applying knob %s: %v", knob, err)
	// 	return false
	// }
	
	// 3. 이전 안전한 값(Safe Previous Value)을 저장하여 롤백에 대비
	savePreviousValue(knob, "40") // "40"은 이전 값을 시뮬레이션

	// 4. SLO 모니터링 루프를 별도의 고루틴(goroutine)으로 시작
	go monitorSLO(knob, value)

	return true
	
	// return &pb.ApplyResponse{Success: true, StatusMessage: "Configuration applied and monitoring started.", AuditLogId: "12345"}, nil
}

// SLO(Service Level Objective) 모니터링 및 자동 롤백 루프입니다.
func monitorSLO(knob, value string) {
	var violationCount int
	log.Printf("[SLO Monitor] Starting monitoring for %s=%s...", knob, value)

	// 30초마다 메트릭을 확인하는 타이머
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		// Telemetry Agent로부터 최신 P95 Latency 메트릭 수집 시뮬레이션
		currentP95 := getTelemetryMetric("p95_latency_ms") 

		if currentP95 > sloMaxP95Latency {
			// SLO 위반 감지: P95 지연 시간이 허용치를 초과했습니다.
			violationCount++
			log.Printf("[SLO Violation] Detected! P95: %.2f ms (Limit: %.2f ms). Count: %d", 
				currentP95, sloMaxP95Latency, violationCount)
			
			if violationCount >= rollbackThreshold {
				// 롤백 임계값 도달: 자동 롤백 트리거
				log.Printf("[CRITICAL] %d consecutive violations. Triggering automatic rollback for %s.", violationCount, knob)
				rollbackConfiguration(knob)
				return // 모니터링 중지
			}
		} else {
			// SLO 준수: 카운트 초기화
			violationCount = 0 
			log.Printf("[SLO Pass] P95 check passed. P95: %.2f ms", currentP95)
		}
	}
}

// 롤백 로직: 이전의 안전한 설정으로 되돌립니다.
func rollbackConfiguration(knob string) {
	// Audit Log/KB에서 이전 안전 값 검색 시뮬레이션
	revertValue := getSafePreviousValue(knob) 
	
	log.Printf("[ROLLBACK] Reverting %s to previous safe value: %s", knob, revertValue)
	
	// 실제 롤백 명령 실행 시뮬레이션
	// if err := os.WriteFile(fmt.Sprintf("/proc/sys/%s", knob), []byte(revertValue), 0644); err != nil {
	// 	log.Printf("FATAL: Failed to rollback knob %s: %v", knob, err)
	// }
	
	// 롤백 결과를 Knowledge Base에 로깅하여 재학습에 활용
	// logRollbackOutcome(knob, revertValue)
}

// getTelemetryMetric: Telemetry Agent로부터 메트릭을 가져오는 것을 시뮬레이션합니다.
func getTelemetryMetric(metric string) float64 {
	// 테스트를 위해 15초마다 임계값을 초과하도록 시뮬레이션합니다.
	if time.Now().Second() % 15 == 0 {
		return sloMaxP95Latency + 20.0 // 위반 (70.0 ms)
	}
	return sloMaxP95Latency - 15.0 // 정상 (35.0 ms)
}

// 이전 값을 저장하는 시뮬레이션 함수
func savePreviousValue(knob, value string) {
	// 실제 환경에서는 영구적인 Knowledge Base에 저장됩니다.
	log.Printf("KB: Saved previous safe value for %s: %s", knob, value)
}

// 이전 안전한 값을 가져오는 시뮬레이션 함수
func getSafePreviousValue(knob string) string {
	// 실제 환경에서는 Knowledge Base에서 검색합니다.
	return "40" // 시뮬레이션된 이전 값
}


func main() {
	// gRPC 서버 설정 및 시작 시뮬레이션
	log.Println("Starting SemantOS Safety Runtime...")
	
	// lis, err := net.Listen("tcp", port)
	// if err != nil {
	// 	log.Fatalf("Failed to listen: %v", err)
	// }
	// grpcServer := grpc.NewServer()
	// pb.RegisterSemantosControlServer(grpcServer, &SafetyRuntimeServer{})
	
	// log.Printf("Server listening at %v", lis.Addr())
	// if err := grpcServer.Serve(lis); err != nil {
	// 	log.Fatalf("Failed to serve: %v", err)
	// }
	
	// 간단한 실행 테스트
	log.Println("Safety Runtime is running in simulation mode.")
	// Reasoner이 권장 사항을 보냈다고 가정하고 적용을 시작합니다.
	ApplyConfiguration("vm.swappiness", "1")
	
	// 서버가 종료되지 않도록 무한 루프 유지 (실제 서버에서는 grpcServer.Serve가 루프를 담당)
	select {}
}