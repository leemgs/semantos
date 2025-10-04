#include <uapi/linux/ptrace.h>
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

char LICENSE[] SEC("license") = "GPL";

// BPF Map: 수집된 메트릭을 사용자 공간으로 전달하기 위한 맵 정의
// Key: 메트릭 ID (enum), Value: 카운터 또는 타이밍 값
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 128);
    __type(key, u64);
    __type(value, u66);
} metrics_map SEC(".maps");

// 메트릭 ID 정의
enum metric_id {
    METRIC_RUN_QUEUE_LATENCY,
    METRIC_SCHED_MIGRATIONS,
    METRIC_PAGE_FAULTS_MAJOR,
    // ... 기타 커널 메트릭
};

// Tracepoint: 스케줄러 스위치 이벤트 처리
// 이 함수는 스케줄러가 한 태스크에서 다른 태스크로 전환될 때 호출됩니다.
SEC("tracepoint/sched/sched_switch")
int trace_sched_switch(struct trace_event_raw_sched_switch *ctx) {
    u64 latency_ns = bpf_ktime_get_ns();
    u64 zero = 0;
    
    // 이 예제에서는 단순한 카운트 및 가상의 레이턴시만 시뮬레이션
    
    // 1. 스케줄링 마이그레이션 횟수 카운트
    u64 metric_key = METRIC_SCHED_MIGRATIONS;
    u64 *value = bpf_map_lookup_elem(&metrics_map, &metric_key);
    
    if (value) {
        // 기존 값에 1을 더합니다.
        __sync_fetch_and_add(value, 1);
    } else {
        // 맵에 처음 삽입합니다.
        u64 init_value = 1;
        bpf_map_update_elem(&metrics_map, &metric_key, &init_value, BPF_ANY);
    }

    // 2. 가상의 Run Queue Latency 기록 (실제 계산 로직은 더 복잡함)
    metric_key = METRIC_RUN_QUEUE_LATENCY;
    bpf_map_update_elem(&metrics_map, &metric_key, &latency_ns, BPF_ANY);

    return 0;
}

// Tracepoint: 페이지 폴트 이벤트 처리 (시뮬레이션)
SEC("tracepoint/mm/mm_page_alloc")
int trace_page_alloc(void *ctx) {
    u64 metric_key = METRIC_PAGE_FAULTS_MAJOR;
    u64 *value = bpf_map_lookup_elem(&metrics_map, &metric_key);
    
    if (value) {
        __sync_fetch_and_add(value, 1);
    } else {
        u64 init_value = 1;
        bpf_map_update_elem(&metrics_map, &metric_key, &init_value, BPF_ANY);
    }
    
    return 0;
}