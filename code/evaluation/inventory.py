"""Read-only inventory for a measured run; no hostnames, usernames or credentials."""
import hashlib
import json
import os
import platform
from pathlib import Path
import shutil

KNOBS = ['vm.dirty_ratio', 'vm.dirty_background_ratio', 'vm.swappiness']

def inventory():
    cpu = Path('/proc/cpuinfo').read_text()
    model = next((s.split(':',1)[1].strip() for s in cpu.splitlines() if s.startswith('model name')), 'unknown')
    knobs = {}
    for knob in KNOBS:
        path = Path('/proc/sys') / knob.replace('.', '/')
        knobs[knob] = {'present':path.exists(), 'value':path.read_text().strip() if path.exists() else None,
                       'os_write_access':os.access(path, os.W_OK)}
    return {'schema_version':1, 'kernel':platform.release(), 'machine':platform.machine(),
            'cpu_model':model, 'logical_cpus':os.cpu_count(), 'python':platform.python_version(),
            'memory_total_kib':int(Path('/proc/meminfo').read_text().splitlines()[0].split()[1]),
            'cpu_affinity':sorted(os.sched_getaffinity(0)), 'knobs':knobs,
            'tools':{n:bool(shutil.which(n)) for n in ['docker','stress-ng','perf','sysbench','fio','wrk','nvidia-smi']},
            'kernel_writes_performed':False}

if __name__ == '__main__':
    print(json.dumps(inventory(), indent=2))
