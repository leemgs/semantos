import time
import socket
import psutil
# from bcc import BPF  # 실제 eBPF 프로그램 로드 라이브러리 (bcc 또는 libbpf-python)
# import grpc
# import semantos_pb2
# import semantos_pb2_grpc

# 메트릭 이름과 BPF 맵 키 매핑 (trace_metrics.c와 일치해야 함)
METRIC_MAPPING = {
    0: "sched_migrations_count",
    1: "run_queue_latency_ns",
    2: "major_page_faults_count",
}

class TelemetryAgent:
    def __init__(self, grpc_target_host):
        self.host_id = socket.gethostname()
        self.grpc_target = grpc_target_host
        # self.channel = grpc.insecure_channel(self.grpc_target)
        # self.stub = semantos_pb2_grpc.SemantosControlStub(self.channel)
        
        # eBPF 프로그램 초기화 시뮬레이션
        # with open("src/bpf/trace_metrics.c", "r") as f:
        #     self.b = BPF(text=f.read())
        # self.metrics_map = self.b["metrics_map"]
        print(f"Telemetry Agent initialized on host: {self.host_id}")

    def get_user_space_metrics(self):
        """psutil 등을 사용하여 사용자 공간 및 시스템 메트릭 수집"""
        metrics = {}
        # CPU 사용률
        metrics["cpu_utilization_percent"] = psutil.cpu_percent(interval=None)
        # 메모리 사용량 (MiB)
        metrics["memory_available_mib"] = psutil.virtual_memory().available / (1024 * 1024)
        # 디스크 I/O (초당 읽기/쓰기 바이트)
        metrics["disk_read_bytes_per_sec"] = psutil.disk_io_counters().read_bytes
        # 현재 커널 설정 읽기 (예: vm.swappiness)
        knobs = {}
        try:
            with open("/proc/sys/vm/swappiness", "r") as f:
                knobs["vm_swappiness"] = f.read().strip()
        except FileNotFoundError:
            knobs["vm_swappiness"] = "60" # 기본값 시뮬레이션
            
        return metrics, knobs

    def get_ebpf_metrics(self):
        """eBPF 맵에서 커널 메트릭 읽기"""
        ebpf_metrics = {}
        # 실제 환경에서는 self.metrics_map.items() 등을 사용
        
        # eBPF 메트릭 수집 시뮬레이션
        ebpf_metrics[METRIC_MAPPING[0]] = 42 # sched_migrations_count
        ebpf_metrics[METRIC_MAPPING[1]] = 150000000.0 # run_queue_latency_ns (150ms)
        
        # 맵에서 데이터를 읽은 후, 일부 카운터는 재설정을 위해 Clear 해야 함 (eBPF 모범 사례)
        # self.metrics_map.clear()

        return ebpf_metrics

    def collect_and_send_snapshot(self):
        """모든 메트릭을 수집하고 gRPC를 통해 전송"""
        user_metrics, current_knobs = self.get_user_space_metrics()
        ebpf_metrics = self.get_ebpf_metrics()
        
        # 메트릭 통합
        full_metrics = {**user_metrics, **ebpf_metrics}
        
        # gRPC 요청 객체 생성 시뮬레이션
        # snapshot = semantos_pb2.TelemetrySnapshot(
        #     host_id=self.host_id,
        #     metrics=full_metrics,
        #     current_knobs=current_knobs
        # )

        # Reasoner Engine에 전송 및 권장 사항 수신 시뮬레이션
        # response = self.stub.GetRecommendations(snapshot)
        print(f"[{time.strftime('%H:%M:%S')}] Collected {len(full_metrics)} metrics and sent to Reasoner.")
        # print(f"Received recommendations: {response}")

    def run(self):
        """에이전트 메인 루프"""
        # 논문에서 언급된 텔레메트리 주기 (예: 5초)
        COLLECTION_INTERVAL = 5 
        
        while True:
            self.collect_and_send_snapshot()
            time.sleep(COLLECTION_INTERVAL)

if __name__ == "__main__":
    # gRPC 서버 타겟 (Reasoner Engine)
    AGENT = TelemetryAgent(grpc_target_host="reasoner-engine:50051")
    AGENT.run()