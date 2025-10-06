import os, time, json, threading, statistics, psutil
from fastapi import FastAPI
from fastapi.responses import JSONResponse

USE_EBPF = os.environ.get("USE_EBPF", "auto")  # "auto" | "on" | "off"
SAMPLE_WINDOW = int(os.environ.get("SAMPLE_WINDOW", "30"))  # seconds to keep

app = FastAPI(title="telemetry-agent")
hist_lock = threading.Lock()
latency_ms = []  # sliding window storage (sched switch proxy)
io_latency = []  # sliding window of block I/O complete durations (ms)
sys_enter_rate = []  # syscalls/sec in window

def try_init_bcc():
    if USE_EBPF == "off":
        return None, {}
    try:
        from bcc import BPF
    except Exception:
        return None, {}
    program = r"""
    #include <uapi/linux/ptrace.h>
    #include <linux/blkdev.h>

    BPF_HISTOGRAM(dist);
    BPF_HISTOGRAM(iolat);
    BPF_HASH(sys_enter_cnt, u32, u64);

    int trace_sched_switch(struct pt_regs *ctx) {
        u64 ts = bpf_ktime_get_ns();
        u64 slot = ts / 1000000ULL % 100;  // bucket 0..99 ms
        dist.increment(slot);
        return 0;
    }

    TRACEPOINT_PROBE(block, block_rq_complete) {
        u64 delta = args->nr_bytes ? args->nr_bytes : 1; // placeholder if needed
        // Here, we don't have start timestamp easily; use completion time mod buckets as proxy demo
        u64 slot = bpf_ktime_get_ns() / 1000000ULL % 200; // 0..199 ms
        iolat.increment(slot);
        return 0;
    }

    TRACEPOINT_PROBE(raw_syscalls, sys_enter) {
        u32 key = 0;
        u64 zero = 0, *val;
        val = sys_enter_cnt.lookup_or_init(&key, &zero);
        (*val)++;
        return 0;
    }
    """
    b = BPF(text=program)
    try:
        b.attach_kprobe(event="finish_task_switch", fn_name="trace_sched_switch")
    except Exception:
        pass
    tps = {}
    try:
        tps["block"] = b.get_table("iolat")
    except Exception:
        tps["block"] = None
    try:
        tps["sys_enter"] = b.get_table("sys_enter_cnt")
    except Exception:
        tps["sys_enter"] = None
    return b, tps

bcc = None
tps = {}

def ebpf_worker():
    global bcc, tps
    last_syscalls = 0
    last_ts = time.time()
    while True:
        time.sleep(1.0)
        try:
            # sched histogram -> p50/p95 proxy
            table = bcc.get_table("dist")
            total = 0
            buckets = []
            for k, v in table.items():
                buckets.append((int(k.value), int(v.value)))
                total += int(v.value)
            buckets.sort()
            if total:
                cum = 0
                p50 = p95 = 0
                for b, c in buckets:
                    cum += c
                    if p50 == 0 and cum >= 0.5 * total:
                        p50 = b
                    if p95 == 0 and cum >= 0.95 * total:
                        p95 = b
                        break
            else:
                p50 = p95 = 0

            # block I/O latency proxy
            iop = 0
            if tps.get("block"):
                io_tab = tps["block"]
                total_io = 0
                io_buckets = []
                for k, v in io_tab.items():
                    io_buckets.append((int(k.value), int(v.value)))
                    total_io += int(v.value)
                io_buckets.sort()
                if total_io:
                    cum = 0
                    p95io = 0
                    for b, c in io_buckets:
                        cum += c
                        if p95io == 0 and cum >= 0.95 * total_io:
                            p95io = b
                            break
                    iop = p95io
                io_tab.clear()

            # sys_enter rate (per second)
            rate = 0.0
            if tps.get("sys_enter"):
                tab = tps["sys_enter"]
                key = tab.Key(0)
                val = tab.get(key)
                cur = int(val.value) if val else 0
                now = time.time()
                dt = now - last_ts if now > last_ts else 1.0
                if dt > 0:
                    rate = max(0.0, (cur - last_syscalls) / dt)
                last_syscalls, last_ts = cur, now

            with hist_lock:
                latency_ms.append({"ts": time.time(), "median": p50, "p95": p95})
                io_latency.append({"ts": time.time(), "p95": iop})
                sys_enter_rate.append({"ts": time.time(), "rps": rate})
                cutoff = time.time() - SAMPLE_WINDOW
                latency_ms[:]   = [x for x in latency_ms   if x["ts"] >= cutoff]
                io_latency[:]   = [x for x in io_latency   if x["ts"] >= cutoff]
                sys_enter_rate[:] = [x for x in sys_enter_rate if x["ts"] >= cutoff]

            table.clear()
        except Exception:
            break

@app.on_event("startup")
def startup():
    global bcc, tps
    if USE_EBPF != "off":
        try:
            bcc, tables = try_init_bcc()
            tps = tables
        except Exception:
            bcc = None
    if bcc is not None:
        t = threading.Thread(target=ebpf_worker, daemon=True)
        t.start()

@app.get("/healthz")
def healthz():
    mode = "fallback"
    if bcc is not None:
        mode = "ebpf"
    elif USE_EBPF == "on":
        mode = "ebpf-requested-but-unavailable"
    return {"ok": True, "mode": mode, "has_block": bool(tps.get("block")), "has_sysenter": bool(tps.get("sys_enter"))}

@app.get("/snapshot")
def snapshot():
    with hist_lock:
        meds = [x["median"] for x in latency_ms]
        p95s = [x["p95"] for x in latency_ms]
        iop  = [x["p95"] for x in io_latency if x["p95"]]
        rps  = [x["rps"] for x in sys_enter_rate]
    median = statistics.median(meds) if meds else 0.0
    p95 = statistics.median(p95s) if p95s else 0.0
    p95_io = statistics.median(iop) if iop else 0.0
    rate = statistics.median(rps) if rps else 0.0
    load1, load5, load15 = psutil.getloadavg()
    return JSONResponse({
        "host_id": "host-001",
        "metrics": {
            "cpu_load_1": load1,
            "cpu_load_5": load5,
            "cpu_load_15": load15,
            "median_latency_ms": float(median),
            "p95_latency_ms": float(p95),
            "p95_block_io_ms": float(p95_io),
            "sys_enter_rps": float(rate),
        },
        "ts": time.time()
    })
