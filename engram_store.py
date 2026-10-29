# src/bridge/spinal_bridge.py
import ctypes
import math
import os
import platform
import subprocess
from typing import Dict, List


class JointState(ctypes.Structure):
    _fields_ = [
        ("joint_id", ctypes.c_int),
        ("name", ctypes.c_char * 24),
        ("q_actual", ctypes.c_float),
        ("dq_actual", ctypes.c_float),
        ("q_desired", ctypes.c_float),
        ("dq_desired", ctypes.c_float),
        ("kp", ctypes.c_float),
        ("kd", ctypes.c_float),
        ("iq_current", ctypes.c_float),
        ("torque_nm", ctypes.c_float),
        ("temperature_c", ctypes.c_float),
    ]


class CyberneticChassis(ctypes.Structure):
    _fields_ = [
        ("joints", JointState * 6),
        ("tick_count", ctypes.c_ulonglong),
        ("emergency_stop", ctypes.c_int),
    ]


class SpinalBridge:
    def __init__(self, lib_dir: str = "build"):
        ext = ".dll" if platform.system() == "Windows" else ".so"
        lib_path = os.path.abspath(os.path.join(lib_dir, f"actuator_core{ext}"))

        if not os.path.exists(lib_path):
            self._compile_library(lib_path)

        self.lib = ctypes.CDLL(lib_path)

        # Configure C function signatures
        self.lib.init_chassis.argtypes = [ctypes.POINTER(CyberneticChassis)]
        self.lib.set_joint_command.argtypes = [
            ctypes.POINTER(CyberneticChassis),
            ctypes.c_int,
            ctypes.c_float,
            ctypes.c_float,
            ctypes.c_float,
        ]
        self.lib.step_control_loop.argtypes = [
            ctypes.POINTER(CyberneticChassis),
            ctypes.c_int,
        ]

        self.chassis = CyberneticChassis()
        self.lib.init_chassis(ctypes.byref(self.chassis))

    def _compile_library(self, lib_path: str) -> None:
        source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "actuator_core.c"))
        if not os.path.exists(source_path):
            raise FileNotFoundError(
                f"C spinal source file missing at {source_path}. "
                "Restore actuator_core.c before starting Ultron."
            )

        os.makedirs(os.path.dirname(lib_path), exist_ok=True)
        compile_cmd = ["gcc", "-shared", "-O3", source_path, "-o", lib_path]
        if platform.system() != "Windows":
            compile_cmd.insert(1, "-fPIC")

        try:
            result = subprocess.run(compile_cmd, capture_output=True, text=True, check=False)
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                "GCC compiler was not found in PATH, so the C spinal library could not be built."
            ) from exc

        if result.returncode != 0:
            err = result.stderr.strip() or result.stdout.strip() or "Unknown compiler error."
            raise FileNotFoundError(
                f"Failed to compile C spinal library at {lib_path}. Compiler output: {err}"
            )

    def move_joint_deg(
        self, joint_id: int, angle_deg: float, kp: float = 65.0, kd: float = 6.5, settle_ms: int = 350
    ) -> Dict:
        """Commands a joint in degrees and steps the 1,000 Hz C loop for `settle_ms` ticks."""
        angle_rad = math.radians(angle_deg)
        self.lib.set_joint_command(
            ctypes.byref(self.chassis), joint_id, angle_rad, kp, kd
        )
        self.lib.step_control_loop(ctypes.byref(self.chassis), settle_ms)
        return self.get_proprioception()[joint_id]

    def get_proprioception(self) -> List[Dict]:
        """Reads real-time proprioceptive state (q_t, dq_t, current, temp) from C memory."""
        states = []
        for i in range(6):
            j = self.chassis.joints[i]
            states.append({
                "joint_id": j.joint_id,
                "name": j.name.decode("utf-8"),
                "angle_deg": round(math.degrees(j.q_actual), 2),
                "target_deg": round(math.degrees(j.q_desired), 2),
                "velocity_deg_s": round(math.degrees(j.dq_actual), 2),
                "iq_current_a": round(j.iq_current, 2),
                "torque_nm": round(j.torque_nm, 2),
                "temp_c": round(j.temperature_c, 2),
            })
        return states
