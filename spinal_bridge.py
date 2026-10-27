# src/swarm/hive_telemetry.py
import hashlib
import os
import platform
import socket
import time
from typing import Dict


class HiveNodeMonitor:
    def __init__(self, node_designation: str = "ULTRON-PRIME-NODE-01"):
        self.node_designation = node_designation
        self.boot_time = time.time()

    def get_node_telemetry(self, spinal_ticks: int) -> Dict:
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "127.0.0.1"

        uptime_s = round(time.time() - self.boot_time, 1)
        state_payload = f"{self.node_designation}:{hostname}:{spinal_ticks}:{uptime_s}"
        sync_hash = hashlib.sha256(state_payload.encode()).hexdigest()[:16]

        return {
            "node_id": self.node_designation,
            "hostname": hostname,
            "local_ip": local_ip,
            "os_kernel": f"{platform.system()} {platform.release()} ({platform.machine()})",
            "cpu_cores": os.cpu_count(),
            "uptime_sec": uptime_s,
            "rt_spinal_ticks": spinal_ticks,
            "swarm_sync_hash": sync_hash,
        }
