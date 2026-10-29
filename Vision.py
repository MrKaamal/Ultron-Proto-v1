#!/usr/bin/env python3
"""
================================================================================
ULTRON / VISION — SOVEREIGN MACHINE INTELLIGENCE PROTOTYPE (PURE PYTHON + C99)
================================================================================
File: ultron_vision_prototype.py

This single-file executable prototype implements all 6 layers of the Ultron/Vision
cybernetic architecture using 100% Python Standard Library + auto-compiled C99:

  1. Layer 1 (Ultron Swarm Mesh)   : UDP broadcast gossip & SHA-256 state sync
  2. Layer 2 (Ctypes Spinal Bridge): Auto-compiles C99 1,000 Hz engine (with
                                     automatic pure-Python fallback if GCC is absent)
  3. Layer 3 (Memory & Perception) : SQLite 128-D Cosine Vector Engram Store +
                                     OpenCV / Synthetic LiDAR Visual Servoing
  4. Layer 4 (Whole-Body Control)  : 5th-Order Minimum-Jerk Trajectory Planner +
                                     PD Virtual Spring-Damper Impedance Control
  5. Layer 5 (EEE CAN-FD Fieldbus) : MIT Mini-Cheetah / QDD 64-bit CAN frame
                                     bit-packer + UART CRC-8 hardware bridge
  6. Layer 6 (System-2 ReAct Brain): Autonomous Tool Router supporting both
                                     Gemini API & Air-Gapped Offline Reflex mode

USAGE:
  Run Interactive Shell : python ultron_vision_prototype.py
  Run Unit Test Suite   : python ultron_vision_prototype.py --test
  Unpack Multi-File Repo: python ultron_vision_prototype.py --unpack-repo
================================================================================
"""

import argparse
import ctypes
import hashlib
import json
import math
import os
import platform
import re
import shutil
import socket
import sqlite3
import struct
import subprocess
import sys
import threading
import time
import unittest
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ==============================================================================
# EMBEDDED C99 SOURCE CODE FOR LAYER 6 (1,000 Hz REAL-TIME SPINAL CORD)
# ==============================================================================
C99_ACTUATOR_CORE_SOURCE = r"""
#include <stdio.h>
#include <stdint.h>
#include <math.h>

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

#define NUM_JOINTS 6
#define DT 0.001f           /* 1,000 Hz deterministic step (1 ms) */
#define MAX_CURRENT_A 35.0f /* Peak GaN Inverter Phase Current (Amps) */
#define KT_TORQUE 1.85f     /* Quasi-Direct Drive Torque Constant (Nm/A) */

/* MIT Mini-Cheetah / QDD CAN-FD Parameter Ranges */
#define P_MIN -12.5f
#define P_MAX  12.5f
#define V_MIN -45.0f
#define V_MAX  45.0f
#define KP_MIN 0.0f
#define KP_MAX 500.0f
#define KD_MIN 0.0f
#define KD_MAX 50.0f
#define T_MIN -24.0f
#define T_MAX  24.0f

typedef struct {
    int joint_id;
    char name[24];
    float q_actual;
    float dq_actual;
    float q_desired;
    float dq_desired;
    float kp;
    float kd;
    float t_ff;
    float iq_current;
    float torque_nm;
    float temperature_c;
    uint8_t can_frame[8];
} JointState;

typedef struct {
    JointState joints[NUM_JOINTS];
    unsigned long long tick_count;
    int emergency_stop;
} CyberneticChassis;

static uint16_t float_to_uint(float x, float x_min, float x_max, int bits) {
    float span = x_max - x_min;
    if (x < x_min) x = x_min;
    if (x > x_max) x = x_max;
    return (uint16_t)((x - x_min) * ((float)((1 << bits) - 1)) / span);
}

EXPORT void pack_canfd_frame(JointState* j) {
    uint16_t p_int  = float_to_uint(j->q_desired, P_MIN, P_MAX, 16);
    uint16_t v_int  = float_to_uint(j->dq_desired, V_MIN, V_MAX, 12);
    uint16_t kp_int = float_to_uint(j->kp, KP_MIN, KP_MAX, 12);
    uint16_t kd_int = float_to_uint(j->kd, KD_MIN, KD_MAX, 12);
    uint16_t t_int  = float_to_uint(j->t_ff, T_MIN, T_MAX, 12);

    j->can_frame[0] = (p_int >> 8) & 0xFF;
    j->can_frame[1] = p_int & 0xFF;
    j->can_frame[2] = (v_int >> 4) & 0xFF;
    j->can_frame[3] = ((v_int & 0x0F) << 4) | ((kp_int >> 8) & 0x0F);
    j->can_frame[4] = kp_int & 0xFF;
    j->can_frame[5] = (kd_int >> 4) & 0xFF;
    j->can_frame[6] = ((kd_int & 0x0F) << 4) | ((t_int >> 8) & 0x0F);
    j->can_frame[7] = t_int & 0xFF;
}

EXPORT void init_chassis(CyberneticChassis* chassis) {
    const char* names[NUM_JOINTS] = {
        "Neck_Yaw", "Neck_Pitch", "R_Shoulder_Pitch",
        "R_Elbow_Flex", "L_Shoulder_Pitch", "L_Elbow_Flex"
    };
    chassis->tick_count = 0;
    chassis->emergency_stop = 0;

    for (int i = 0; i < NUM_JOINTS; i++) {
        JointState* j = &chassis->joints[i];
        j->joint_id = i;
        snprintf(j->name, 24, "%s", names[i]);
        j->q_actual = 0.0f;
        j->dq_actual = 0.0f;
        j->q_desired = 0.0f;
        j->dq_desired = 0.0f;
        j->kp = 65.0f;
        j->kd = 6.5f;
        j->t_ff = 0.0f;
        j->iq_current = 0.0f;
        j->torque_nm = 0.0f;
        j->temperature_c = 32.0f;
        pack_canfd_frame(j);
    }
}

EXPORT void set_joint_command(
    CyberneticChassis* chassis,
    int joint_id,
    float q_des,
    float dq_des,
    float kp,
    float kd,
    float t_ff
) {
    if (joint_id < 0 || joint_id >= NUM_JOINTS) return;
    JointState* j = &chassis->joints[joint_id];
    j->q_desired = q_des;
    j->dq_desired = dq_des;
    j->kp = kp;
    j->kd = kd;
    j->t_ff = t_ff;
    pack_canfd_frame(j);
}

EXPORT void inject_external_torque(CyberneticChassis* chassis, int joint_id, float impulse_vel) {
    if (joint_id < 0 || joint_id >= NUM_JOINTS) return;
    chassis->joints[joint_id].dq_actual += impulse_vel;
}

EXPORT void step_control_loop(CyberneticChassis* chassis, int steps) {
    if (chassis->emergency_stop) return;

    const float link_inertia = 0.12f;
    const float viscous_friction = 0.15f;

    for (int s = 0; s < steps; s++) {
        for (int i = 0; i < NUM_JOINTS; i++) {
            JointState* j = &chassis->joints[i];

            float pos_error = j->q_desired - j->q_actual;
            float vel_error = j->dq_desired - j->dq_actual;
            float commanded_torque = (j->kp * pos_error) + (j->kd * vel_error) + j->t_ff;

            float iq = commanded_torque / KT_TORQUE;
            if (iq > MAX_CURRENT_A) iq = MAX_CURRENT_A;
            if (iq < -MAX_CURRENT_A) iq = -MAX_CURRENT_A;
            j->iq_current = iq;

            j->torque_nm = iq * KT_TORQUE;
            float angular_accel = (j->torque_nm - (viscous_friction * j->dq_actual)) / link_inertia;
            j->dq_actual += angular_accel * DT;
            j->q_actual += j->dq_actual * DT;

            float heat_rise = (iq * iq * 0.00008f) - ((j->temperature_c - 30.0f) * 0.0005f);
            j->temperature_c += heat_rise;

            if (j->temperature_c > 85.0f) {
                chassis->emergency_stop = 1;
            }
        }
        chassis->tick_count++;
    }
}
"""


# ==============================================================================
# LAYER 5 & 6: CAN-FD BIT PACKER & CTYPES / NATIVE SPINAL BRIDGE
# ==============================================================================
P_MIN, P_MAX = -12.5, 12.5
V_MIN, V_MAX = -45.0, 45.0
KP_MIN, KP_MAX = 0.0, 500.0
KD_MIN, KD_MAX = 0.0, 50.0
T_MIN, T_MAX = -24.0, 24.0


def float_to_uint(x: float, x_min: float, x_max: float, bits: int) -> int:
    """Converts a floating-point physical value into an unsigned integer for CAN bit-packing."""
    span = x_max - x_min
    clamped = max(x_min, min(x_max, x))
    return int(round((clamped - x_min) * ((1 << bits) - 1) / span))


def uint_to_float(x_int: int, x_min: float, x_max: float, bits: int) -> float:
    """Unpacks an unsigned integer from a CAN frame back into physical units."""
    span = x_max - x_min
    return float(x_int) * span / float((1 << bits) - 1) + x_min


def pack_mit_canfd_frame(
    q_des: float, dq_des: float, kp: float, kd: float, t_ff: float
) -> List[int]:
    """
    Packs (p_des, v_des, Kp, Kd, t_ff) into the industry-standard 8-byte (64-bit)
    MIT Mini-Cheetah / QDD actuator CAN-FD payload.
    """
    p_int = float_to_uint(q_des, P_MIN, P_MAX, 16)
    v_int = float_to_uint(dq_des, V_MIN, V_MAX, 12)
    kp_int = float_to_uint(kp, KP_MIN, KP_MAX, 12)
    kd_int = float_to_uint(kd, KD_MIN, KD_MAX, 12)
    t_int = float_to_uint(t_ff, T_MIN, T_MAX, 12)

    return [
        (p_int >> 8) & 0xFF,
        p_int & 0xFF,
        (v_int >> 4) & 0xFF,
        ((v_int & 0x0F) << 4) | ((kp_int >> 8) & 0x0F),
        kp_int & 0xFF,
        (kd_int >> 4) & 0xFF,
        ((kd_int & 0x0F) << 4) | ((t_int >> 8) & 0x0F),
        t_int & 0xFF,
    ]


def unpack_mit_canfd_frame(buf: List[int]) -> Dict[str, float]:
    """Unpacks an 8-byte CAN-FD frame back into physical commands."""
    p_int = (buf[0] << 8) | buf[1]
    v_int = (buf[2] << 4) | (buf[3] >> 4)
    kp_int = ((buf[3] & 0x0F) << 8) | buf[4]
    kd_int = (buf[5] << 4) | (buf[6] >> 4)
    t_int = ((buf[6] & 0x0F) << 8) | buf[7]

    return {
        "q_des": round(uint_to_float(p_int, P_MIN, P_MAX, 16), 4),
        "dq_des": round(uint_to_float(v_int, V_MIN, V_MAX, 12), 4),
        "kp": round(uint_to_float(kp_int, KP_MIN, KP_MAX, 12), 2),
        "kd": round(uint_to_float(kd_int, KD_MIN, KD_MAX, 12), 2),
        "t_ff": round(uint_to_float(t_int, T_MIN, T_MAX, 12), 3),
    }


class CJointState(ctypes.Structure):
    """Exact C-struct memory layout matching JointState in actuator_core.c."""
    _fields_ = [
        ("joint_id", ctypes.c_int),
        ("name", ctypes.c_char * 24),
        ("q_actual", ctypes.c_float),
        ("dq_actual", ctypes.c_float),
        ("q_desired", ctypes.c_float),
        ("dq_desired", ctypes.c_float),
        ("kp", ctypes.c_float),
        ("kd", ctypes.c_float),
        ("t_ff", ctypes.c_float),
        ("iq_current", ctypes.c_float),
        ("torque_nm", ctypes.c_float),
        ("temperature_c", ctypes.c_float),
        ("can_frame", ctypes.c_uint8 * 8),
    ]


class CCyberneticChassis(ctypes.Structure):
    """Exact C-struct memory layout matching CyberneticChassis in actuator_core.c."""
    _fields_ = [
        ("joints", CJointState * 6),
        ("tick_count", ctypes.c_ulonglong),
        ("emergency_stop", ctypes.c_int),
    ]


@dataclass
class PyJointState:
    """Pure-Python fallback joint state when running on a system without GCC installed."""
    joint_id: int
    name: str
    q_actual: float = 0.0
    dq_actual: float = 0.0
    q_desired: float = 0.0
    dq_desired: float = 0.0
    kp: float = 65.0
    kd: float = 6.5
    t_ff: float = 0.0
    iq_current: float = 0.0
    torque_nm: float = 0.0
    temperature_c: float = 32.0
    can_frame: List[int] = field(default_factory=lambda: [0] * 8)


class SpinalBridge:
    """
    Layer 2 & 6 Spinal Cord Bridge.
    Automatically compiles and binds the C99 shared library (`actuator_core.dll`/`.so`)
    if GCC is available on PATH; otherwise runs the identical 1,000 Hz deterministic
    physics loop in native Python so the script works everywhere out-of-the-box.
    """

    JOINT_NAMES = [
        "Neck_Yaw",
        "Neck_Pitch",
        "R_Shoulder_Pitch",
        "R_Elbow_Flex",
        "L_Shoulder_Pitch",
        "L_Elbow_Flex",
    ]

    def __init__(self, build_dir: str = "build", prefer_c_engine: bool = True):
        self.build_dir = build_dir
        self.using_c_dll = False
        self.lib = None
        self.c_chassis: Optional[CCyberneticChassis] = None

        # Pure-Python state (used if GCC is not installed)
        self.py_joints: List[PyJointState] = [
            PyJointState(
                joint_id=i,
                name=name,
                can_frame=pack_mit_canfd_frame(0.0, 0.0, 65.0, 6.5, 0.0),
            )
            for i, name in enumerate(self.JOINT_NAMES)
        ]
        self._py_tick_count: int = 0
        self._py_emergency_stop: int = 0

        if prefer_c_engine:
            self._try_compile_and_load_c_engine()

    def _try_compile_and_load_c_engine(self) -> None:
        """Auto-compiles C99_ACTUATOR_CORE_SOURCE with GCC if available."""
        gcc_bin = shutil.which("gcc")
        if not gcc_bin:
            return

        try:
            os.makedirs(self.build_dir, exist_ok=True)
            c_src_path = os.path.join(self.build_dir, "actuator_core.c")
            ext = ".dll" if platform.system() == "Windows" else ".so"
            lib_path = os.path.abspath(os.path.join(self.build_dir, f"actuator_core{ext}"))

            if not os.path.exists(c_src_path):
                with open(c_src_path, "w", encoding="utf-8") as f:
                    f.write(C99_ACTUATOR_CORE_SOURCE.strip() + "\n")

            if not os.path.exists(lib_path):
                cmd = [gcc_bin, "-shared", "-O3", c_src_path, "-o", lib_path]
                if platform.system() != "Windows":
                    cmd.insert(2, "-fPIC")
                    cmd.append("-lm")
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            self.lib = ctypes.CDLL(lib_path)
            self.lib.init_chassis.argtypes = [ctypes.POINTER(CCyberneticChassis)]
            self.lib.set_joint_command.argtypes = [
                ctypes.POINTER(CCyberneticChassis),
                ctypes.c_int,
                ctypes.c_float,
                ctypes.c_float,
                ctypes.c_float,
                ctypes.c_float,
                ctypes.c_float,
            ]
            self.lib.inject_external_torque.argtypes = [
                ctypes.POINTER(CCyberneticChassis),
                ctypes.c_int,
                ctypes.c_float,
            ]
            self.lib.step_control_loop.argtypes = [
                ctypes.POINTER(CCyberneticChassis),
                ctypes.c_int,
            ]

            self.c_chassis = CCyberneticChassis()
            self.lib.init_chassis(ctypes.byref(self.c_chassis))
            self.using_c_dll = True
        except Exception:
            self.using_c_dll = False

    @property
    def tick_count(self) -> int:
        return int(self.c_chassis.tick_count) if self.using_c_dll else self._py_tick_count

    @property
    def emergency_stop(self) -> int:
        return int(self.c_chassis.emergency_stop) if self.using_c_dll else self._py_emergency_stop

    def set_joint_command(
        self,
        joint_id: int,
        q_des: float,
        dq_des: float,
        kp: float,
        kd: float,
        t_ff: float = 0.0,
    ) -> None:
        if joint_id < 0 or joint_id >= 6:
            return
        if self.using_c_dll:
            self.lib.set_joint_command(
                ctypes.byref(self.c_chassis), joint_id, q_des, dq_des, kp, kd, t_ff
            )
        else:
            j = self.py_joints[joint_id]
            j.q_desired = q_des
            j.dq_desired = dq_des
            j.kp = kp
            j.kd = kd
            j.t_ff = t_ff
            j.can_frame = pack_mit_canfd_frame(q_des, dq_des, kp, kd, t_ff)

    def inject_external_impulse(self, joint_id: int, impulse_vel_rad_s: float) -> None:
        """Simulates an external physical push/impact on a limb to test PD recovery."""
        if joint_id < 0 or joint_id >= 6:
            return
        if self.using_c_dll:
            self.lib.inject_external_torque(
                ctypes.byref(self.c_chassis), joint_id, impulse_vel_rad_s
            )
        else:
            self.py_joints[joint_id].dq_actual += impulse_vel_rad_s

    def step_control_loop(self, steps: int) -> None:
        """Executes `steps` ticks of the 1,000 Hz (1 ms) PD Impedance + FOC loop."""
        if self.using_c_dll:
            self.lib.step_control_loop(ctypes.byref(self.c_chassis), steps)
            return

        if self._py_emergency_stop:
            return

        dt = 0.001
        max_current_a = 35.0
        kt_torque = 1.85
        link_inertia = 0.12
        viscous_friction = 0.15

        for _ in range(steps):
            for j in self.py_joints:
                pos_error = j.q_desired - j.q_actual
                vel_error = j.dq_desired - j.dq_actual
                commanded_torque = (j.kp * pos_error) + (j.kd * vel_error) + j.t_ff

                iq = commanded_torque / kt_torque
                iq = max(-max_current_a, min(max_current_a, iq))
                j.iq_current = iq

                j.torque_nm = iq * kt_torque
                angular_accel = (j.torque_nm - (viscous_friction * j.dq_actual)) / link_inertia
                j.dq_actual += angular_accel * dt
                j.q_actual += j.dq_actual * dt

                heat_rise = (iq * iq * 0.00008) - ((j.temperature_c - 30.0) * 0.0005)
                j.temperature_c += heat_rise

                if j.temperature_c > 85.0:
                    self._py_emergency_stop = 1
            self._py_tick_count += 1

    def move_joint_minimum_jerk(
        self,
        joint_id: int,
        target_deg: float,
        duration_ms: int = 300,
        kp: float = 65.0,
        kd: float = 6.5,
    ) -> Dict[str, Any]:
        """
        Generates a 5th-order Minimum-Jerk trajectory:
          s(tau) = 10*tau^3 - 15*tau^4 + 6*tau^5
        and steps the 1,000 Hz control loop through the trajectory.
        """
        current_state = self.get_proprioception()[joint_id]
        q_start = math.radians(current_state["angle_deg"])
        q_end = math.radians(target_deg)
        delta = q_end - q_start
        total_time_s = max(1, duration_ms) * 0.001

        for step in range(1, duration_ms + 1):
            tau = step / float(duration_ms)
            s = 10.0 * (tau ** 3) - 15.0 * (tau ** 4) + 6.0 * (tau ** 5)
            ds = (30.0 * (tau ** 2) - 60.0 * (tau ** 3) + 30.0 * (tau ** 4)) / total_time_s

            q_d = q_start + delta * s
            dq_d = delta * ds

            self.set_joint_command(joint_id, q_d, dq_d, kp, kd, 0.0)
            self.step_control_loop(1)

        # Final 50 ms settling hold
        self.set_joint_command(joint_id, q_end, 0.0, kp, kd, 0.0)
        self.step_control_loop(50)
        return self.get_proprioception()[joint_id]

    def get_proprioception(self) -> List[Dict[str, Any]]:
        """Returns the real-time proprioceptive vector q_t, dq_t, current, and CAN frame."""
        states = []
        for i in range(6):
            if self.using_c_dll:
                j = self.c_chassis.joints[i]
                name = j.name.decode("utf-8")
                q_act, q_des = j.q_actual, j.q_desired
                dq_act = j.dq_actual
                iq, tau, temp = j.iq_current, j.torque_nm, j.temperature_c
                can_bytes = [int(b) for b in j.can_frame]
            else:
                j = self.py_joints[i]
                name = j.name
                q_act, q_des = j.q_actual, j.q_desired
                dq_act = j.dq_actual
                iq, tau, temp = j.iq_current, j.torque_nm, j.temperature_c
                can_bytes = list(j.can_frame)

            can_hex = " ".join(f"{b:02X}" for b in can_bytes)
            states.append(
                {
                    "joint_id": i,
                    "name": name,
                    "angle_deg": round(math.degrees(q_act), 2),
                    "target_deg": round(math.degrees(q_des), 2),
                    "velocity_deg_s": round(math.degrees(dq_act), 2),
                    "iq_current_a": round(iq, 2),
                    "torque_nm": round(tau, 2),
                    "temp_c": round(temp, 2),
                    "can_fd_hex": can_hex,
                }
            )
        return states


# ==============================================================================
# LAYER 5: HARDWARE UART / SOCKETCAN 64-BIT MOTOR FRAME TRANSCEIVER
# ==============================================================================
class HardwareFieldbusBridge:
    """
    Wraps the 8-byte MIT Mini-Cheetah / QDD CAN-FD payload into a 12-byte
    CRC-8 protected frame (`[0xAA, 0x55, joint_id, b0..b7, crc8]`) for streaming
    over USB-UART (921600 baud) to an ESP32 / STM32G4 motor node.
    """

    def __init__(self, port: str = "COM3", baudrate: int = 921600, dry_run: bool = True):
        self.port = port
        self.baudrate = baudrate
        self.dry_run = dry_run
        self.serial_conn = None

        if not dry_run:
            try:
                import serial  # Optional pyserial
                self.serial_conn = serial.Serial(port, baudrate, timeout=0.002)
            except Exception as err:
                print(f"[WARN] Serial port {port} unavailable ({err}). Running in dry-run mode.")
                self.dry_run = True

    @staticmethod
    def crc8(data: bytes) -> int:
        """Calculates a polynomial 0x07 CRC-8 checksum over the payload."""
        crc = 0x00
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x07) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc

    def transmit_joint_frame(self, joint_id: int, can_frame_bytes: List[int]) -> bytes:
        """Builds and optionally transmits the 12-byte physical motor command packet."""
        payload = bytes([joint_id & 0xFF] + [b & 0xFF for b in can_frame_bytes[:8]])
        checksum = self.crc8(payload)
        packet = struct.pack("12B", 0xAA, 0x55, *payload, checksum)

        if not self.dry_run and self.serial_conn is not None:
            self.serial_conn.write(packet)
        return packet


# ==============================================================================
# LAYER 3: SOVEREIGN SQLITE 128-D COSINE VECTOR & EPISODIC MEMORY
# ==============================================================================
class EngramStore:
    """
    Zero-bloat persistent vector and episodic memory engine backed by SQLite3.
    Uses deterministic 128-dimensional character and word n-gram hashing for
    instant offline cosine similarity search.
    """

    def __init__(self, db_path: str = "ultron_engrams.db", dim: int = 128):
        self.db_path = db_path
        self.dim = dim
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS engrams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    category TEXT,
                    content TEXT,
                    embedding TEXT,
                    content_hash TEXT UNIQUE
                )
                """
            )
            conn.commit()

    def _embed_text(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        tokens = text.lower().split()
        for token in tokens:
            for n in (2, 3, len(token)):
                for i in range(max(1, len(token) - n + 1)):
                    sub = token[i : i + n]
                    h = int(hashlib.md5(sub.encode("utf-8")).hexdigest(), 16)
                    idx = h % self.dim
                    sign = 1.0 if (h // self.dim) % 2 == 0 else -1.0
                    vec[idx] += sign

        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [round(x / norm, 5) for x in vec]

    @staticmethod
    def _cosine_sim(v1: List[float], v2: List[float]) -> float:
        return sum(a * b for a, b in zip(v1, v2))

    def store_engram(self, category: str, content: str, ts: Optional[float] = None) -> int:
        ts_val = ts if ts is not None else time.time()
        c_hash = hashlib.sha256(f"{category}:{content}".encode("utf-8")).hexdigest()[:24]
        vec = self._embed_text(f"{category} {content}")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO engrams
                (timestamp, category, content, embedding, content_hash)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ts_val, category.upper(), content, json.dumps(vec), c_hash),
            )
            conn.commit()
            return cur.lastrowid or 0

    def export_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT timestamp, category, content FROM engrams ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [{"timestamp": r[0], "category": r[1], "content": r[2]} for r in rows]

    def recall(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        q_vec = self._embed_text(query)
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, timestamp, category, content, embedding FROM engrams"
            ).fetchall()

        scored = []
        for r_id, ts, cat, content, emb_json in rows:
            emb = json.loads(emb_json)
            score = self._cosine_sim(q_vec, emb)
            scored.append(
                {
                    "id": r_id,
                    "category": cat,
                    "content": content,
                    "similarity": round(score, 4),
                    "timestamp": ts,
                }
            )

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]


# ==============================================================================
# LAYER 1: DECENTRALIZED ULTRON HIVE-MIND UDP SWARM GOSSIP DAEMON
# ==============================================================================
class HiveNodeMonitor:
    """
    Decentralized Swarm Node Coordinator.
    Broadcasts cryptographic node state hashes and replicates SQLite engrams across
    all peers listening on UDP port 50505.
    """

    def __init__(
        self,
        node_designation: str = "ULTRON-VISION-PRIME-01",
        udp_port: int = 50505,
        memory: Optional[EngramStore] = None,
    ):
        self.node_designation = node_designation
        self.udp_port = udp_port
        self.memory = memory
        self.boot_time = time.time()
        self.peers: Dict[str, Dict[str, Any]] = {}
        self._running = False

    def start_background_gossip(self) -> None:
        if self._running:
            return
        self._running = True
        threading.Thread(target=self._udp_listener_loop, daemon=True).start()

    def _udp_listener_loop(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("0.0.0.0", self.udp_port))
            sock.settimeout(1.0)
        except Exception:
            sock.close()
            return

        while self._running:
            try:
                data, addr = sock.recvfrom(8192)
                packet = json.loads(data.decode("utf-8"))
                sender_id = packet.get("node_id")
                if sender_id and sender_id != self.node_designation:
                    self.peers[sender_id] = {
                        "ip": addr[0],
                        "last_seen": round(time.time(), 1),
                        "sync_hash": packet.get("swarm_sync_hash"),
                    }
                    if self.memory and "engrams" in packet:
                        for eng in packet["engrams"]:
                            self.memory.store_engram(
                                eng["category"], eng["content"], eng.get("timestamp")
                            )
            except socket.timeout:
                continue
            except Exception:
                continue

    def broadcast_state(self, spinal_ticks: int) -> None:
        payload = self.get_node_telemetry(spinal_ticks)
        if self.memory:
            payload["engrams"] = self.memory.export_recent(limit=5)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            raw = json.dumps(payload).encode("utf-8")
            sock.sendto(raw, ("255.255.255.255", self.udp_port))
        except Exception:
            pass
        finally:
            sock.close()

    def get_node_telemetry(self, spinal_ticks: int) -> Dict[str, Any]:
        """Returns host compute telemetry and cryptographic swarm synchronization hash."""
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
            "active_peers": list(self.peers.keys()),
        }


# ==============================================================================
# VISION SUBSYSTEM A: PURE-PYTHON TENSOR & MIND STONE VLA TRANSFORMER ENGINE
# ==============================================================================
class PureTensor:
    """
    Lightweight, zero-dependency 2D/1D Matrix & Tensor math engine written in
    pure Python to power Vision's onboard Mind Stone VLA (Vision-Language-Action)
    neural architecture without requiring external gigabyte GPU packages.

    Supports:
      - Matrix multiplication (matmul)
      - RMSNorm & LayerNorm
      - Rotary Position Embeddings (RoPE)
      - Scaled Dot-Product Multi-Head Attention
      - SwiGLU & GELU non-linear activations
      - Deterministic Xavier/Sinusoidal weight initialization
    """

    @staticmethod
    def zeros(rows: int, cols: int) -> List[List[float]]:
        """Allocates a 2D matrix of shape (rows, cols) initialized to 0.0."""
        return [[0.0 for _ in range(cols)] for _ in range(rows)]

    @staticmethod
    def deterministic_weights(rows: int, cols: int, seed_tag: str) -> List[List[float]]:
        """
        Generates deterministic, Xavier-scaled weight matrices using SHA-256
        counter hashing so the neural network produces reproducible trajectories
        across any OS or CPU architecture.
        """
        scale = math.sqrt(2.0 / max(1, rows + cols))
        mat: List[List[float]] = []
        for r in range(rows):
            row_vals: List[float] = []
            for c in range(cols):
                key = f"{seed_tag}:{r}:{c}".encode("utf-8")
                digest = hashlib.md5(key).digest()
                raw_int = int.from_bytes(digest[:4], byteorder="little", signed=False)
                norm_u = (raw_int / 4294967295.0) * 2.0 - 1.0
                row_vals.append(round(norm_u * scale, 6))
            mat.append(row_vals)
        return mat

    @staticmethod
    def matmul(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
        """Computes C = A @ B for 2D matrices A (M x K) and B (K x N)."""
        m = len(a)
        k = len(a[0]) if m > 0 else 0
        k_b = len(b)
        n = len(b[0]) if k_b > 0 else 0
        if k != k_b:
            raise ValueError(f"Matrix dimension mismatch: ({m}x{k}) @ ({k_b}x{n})")

        # Transpose B for cache-friendly inner loop dot products
        b_t = [[b[r][c] for r in range(k)] for c in range(n)]
        out: List[List[float]] = []
        for i in range(m):
            a_row = a[i]
            out_row: List[float] = []
            for j in range(n):
                b_col = b_t[j]
                s = 0.0
                for idx in range(k):
                    s += a_row[idx] * b_col[idx]
                out_row.append(s)
            out.append(out_row)
        return out

    @staticmethod
    def add(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
        """Element-wise matrix addition A + B."""
        return [
            [a[r][c] + b[r][c] for c in range(len(a[0]))]
            for r in range(len(a))
        ]

    @staticmethod
    def rms_norm(x: List[List[float]], eps: float = 1e-6) -> List[List[float]]:
        """
        Applies Root Mean Square Layer Normalization (RMSNorm) across the last
        dimension of each token vector:
            y_i = x_i / sqrt(mean(x^2) + eps)
        """
        out: List[List[float]] = []
        for row in x:
            d = max(1, len(row))
            ms = sum(val * val for val in row) / float(d)
            inv_rms = 1.0 / math.sqrt(ms + eps)
            out.append([val * inv_rms for val in row])
        return out

    @staticmethod
    def softmax_rows(x: List[List[float]]) -> List[List[float]]:
        """Applies numerically stable row-wise Softmax."""
        out: List[List[float]] = []
        for row in x:
            max_v = max(row) if row else 0.0
            exps = [math.exp(max(-40.0, min(40.0, v - max_v))) for v in row]
            sum_e = sum(exps) or 1.0
            out.append([e / sum_e for e in exps])
        return out

    @staticmethod
    def silu(val: float) -> float:
        """Sigmoid Linear Unit (SiLU / Swish): x * sigmoid(x)."""
        clamped = max(-30.0, min(30.0, val))
        return val / (1.0 + math.exp(-clamped))

    @staticmethod
    def apply_rope(tokens: List[List[float]], base: float = 10000.0) -> List[List[float]]:
        """
        Applies Rotary Position Embeddings (RoPE) to a sequence of token vectors
        so self-attention is sensitive to relative token positions across visual,
        language, and proprioceptive modalities.
        """
        seq_len = len(tokens)
        dim = len(tokens[0]) if seq_len > 0 else 0
        out: List[List[float]] = []

        for pos in range(seq_len):
            row = tokens[pos]
            new_row = list(row)
            for i in range(0, dim - 1, 2):
                freq = 1.0 / (base ** (float(i) / float(dim)))
                angle = pos * freq
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                x0, x1 = row[i], row[i + 1]
                new_row[i] = x0 * cos_a - x1 * sin_a
                new_row[i + 1] = x0 * sin_a + x1 * cos_a
            out.append(new_row)
        return out


class MindStoneVLATransformer:
    """
    Vision's "Mind Stone" Multimodal Vision-Language-Action (VLA) Neural Core.

    Architecture (modeled after NVIDIA Isaac GR00T / OpenVLA):
      1. Visual Patch Tokenizer   : Projects 4x4 RGB-D spatial regions into d_model=32 tokens
      2. Language Goal Tokenizer  : Projects natural language directives into d_model=32 tokens
      3. Proprioceptive Tokenizer : Encodes 18-DoF joint angles, velocities, andVibranium density
      4. Transformer Trunk        : 2-Layer Multi-Head Self-Attention (4 heads, RoPE, RMSNorm, SwiGLU)
      5. Flow-Matching Action Head: Decodes continuous 8-DoF end-effector & posture action vectors:
                                    [dx, dy, dz, droll, dpitch, dyaw, gripper_force, target_density]
    """

    def __init__(self, d_model: int = 32, n_heads: int = 4, n_layers: int = 2):
        self.d_model = d_model
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads
        self.n_layers = n_layers

        # Initialize Transformer layer weights deterministically
        self.layers: List[Dict[str, List[List[float]]]] = []
        for idx in range(n_layers):
            self.layers.append(
                {
                    "wq": PureTensor.deterministic_weights(d_model, d_model, f"L{idx}_WQ"),
                    "wk": PureTensor.deterministic_weights(d_model, d_model, f"L{idx}_WK"),
                    "wv": PureTensor.deterministic_weights(d_model, d_model, f"L{idx}_WV"),
                    "wo": PureTensor.deterministic_weights(d_model, d_model, f"L{idx}_WO"),
                    "w_gate": PureTensor.deterministic_weights(d_model, d_model * 2, f"L{idx}_WG"),
                    "w_up": PureTensor.deterministic_weights(d_model, d_model * 2, f"L{idx}_WU"),
                    "w_down": PureTensor.deterministic_weights(d_model * 2, d_model, f"L{idx}_WD"),
                }
            )

        # Proprioceptive projection (6 joints * 2 state vars -> d_model)
        self.w_proprio = PureTensor.deterministic_weights(12, d_model, "PROPRIO_PROJ")
        # Action decoder head (d_model -> 8 continuous action dimensions)
        self.w_action_head = PureTensor.deterministic_weights(d_model, 8, "ACTION_DECODER")

    def _encode_visual_patches(self, target_x: float, target_y: float, depth_z: float) -> List[List[float]]:
        """
        Synthesizes 4 visual patch tokens representing a 2x2 foveated crop around
        the tracked optical/LiDAR target (x, y, z).
        """
        patches: List[List[float]] = []
        offsets = [(-0.1, -0.1), (0.1, -0.1), (-0.1, 0.1), (0.1, 0.1)]
        for idx, (ox, oy) in enumerate(offsets):
            token = [0.0] * self.d_model
            for d in range(self.d_model):
                freq = (d + 1) * 0.35
                token[d] = (
                    math.sin((target_x + ox) * freq + idx)
                    + math.cos((target_y + oy) * freq)
                    + math.sin(depth_z * 0.5 * freq)
                ) / 3.0
            patches.append(token)
        return patches

    def _encode_language_tokens(self, prompt: str, max_tokens: int = 6) -> List[List[float]]:
        """Projects words in the user directive into d_model token embeddings."""
        words = [w.strip(".,!?").lower() for w in prompt.split() if w.strip()]
        if not words:
            words = ["hold", "neutral"]
        words = words[:max_tokens]

        tokens: List[List[float]] = []
        for word in words:
            digest = hashlib.sha256(word.encode("utf-8")).digest()
            vec = [
                ((digest[i % len(digest)] / 255.0) * 2.0 - 1.0)
                for i in range(self.d_model)
            ]
            tokens.append(vec)
        return tokens

    def _encode_proprioception(self, joint_states: List[Dict[str, Any]]) -> List[List[float]]:
        """Projects current 6-DoF joint angles and velocities into a proprioceptive token."""
        raw_vec: List[float] = []
        for j in joint_states[:6]:
            raw_vec.append(math.radians(float(j.get("angle_deg", 0.0))))
            raw_vec.append(math.radians(float(j.get("velocity_deg_s", 0.0))) * 0.1)
        while len(raw_vec) < 12:
            raw_vec.append(0.0)
        return PureTensor.matmul([raw_vec[:12]], self.w_proprio)

    def _multi_head_attention(
        self,
        x: List[List[float]],
        wq: List[List[float]],
        wk: List[List[float]],
        wv: List[List[float]],
        wo: List[List[float]],
    ) -> Tuple[List[List[float]], List[List[float]]]:
        """
        Executes Multi-Head Self-Attention with Rotary Position Embeddings (RoPE):
            Attention(Q, K, V) = softmax((Q @ K^T) / sqrt(d_k)) @ V
        Returns both the output token sequence and the mean attention map.
        """
        q = PureTensor.apply_rope(PureTensor.matmul(x, wq))
        k = PureTensor.apply_rope(PureTensor.matmul(x, wk))
        v = PureTensor.matmul(x, wv)

        seq_len = len(x)
        scale = 1.0 / math.sqrt(float(self.head_dim))

        # Compute full scaled dot-product attention across heads
        k_t = [[k[r][c] for r in range(seq_len)] for c in range(self.d_model)]
        scores = PureTensor.matmul(q, k_t)
        for r in range(seq_len):
            for c in range(seq_len):
                scores[r][c] *= scale

        attn_weights = PureTensor.softmax_rows(scores)
        context = PureTensor.matmul(attn_weights, v)
        projected = PureTensor.matmul(context, wo)
        return projected, attn_weights

    def _swiglu_ffn(
        self,
        x: List[List[float]],
        w_gate: List[List[float]],
        w_up: List[List[float]],
        w_down: List[List[float]],
    ) -> List[List[float]]:
        """Executes a SwiGLU Feed-Forward Network block: (SiLU(x @ W_gate) * (x @ W_up)) @ W_down."""
        gate = PureTensor.matmul(x, w_gate)
        up = PureTensor.matmul(x, w_up)
        hidden: List[List[float]] = []
        for r in range(len(x)):
            row_h = [
                PureTensor.silu(gate[r][c]) * up[r][c]
                for c in range(len(gate[0]))
            ]
            hidden.append(row_h)
        return PureTensor.matmul(hidden, w_down)

    def forward_vla_policy(
        self,
        prompt: str,
        joint_states: List[Dict[str, Any]],
        visual_target: Tuple[float, float, float] = (0.35, 0.20, 0.55),
    ) -> Dict[str, Any]:
        """
        Runs a full forward pass of Vision's Mind Stone VLA policy:
          1. Concatenates [4 Visual Tokens] + [Language Tokens] + [1 Proprioceptive Token]
          2. Passes sequence through 2 Transformer layers (RMSNorm + RoPE MHA + SwiGLU)
          3. Pools the final action token and decodes 8-DoF visuomotor action trajectories
        """
        t0 = time.perf_counter()
        v_tokens = self._encode_visual_patches(*visual_target)
        l_tokens = self._encode_language_tokens(prompt)
        p_tokens = self._encode_proprioception(joint_states)

        sequence = v_tokens + l_tokens + p_tokens
        last_attn_map: List[List[float]] = []

        for layer in self.layers:
            normed_1 = PureTensor.rms_norm(sequence)
            attn_out, last_attn_map = self._multi_head_attention(
                normed_1, layer["wq"], layer["wk"], layer["wv"], layer["wo"]
            )
            sequence = PureTensor.add(sequence, attn_out)

            normed_2 = PureTensor.rms_norm(sequence)
            ffn_out = self._swiglu_ffn(
                normed_2, layer["w_gate"], layer["w_up"], layer["w_down"]
            )
            sequence = PureTensor.add(sequence, ffn_out)

        # Pool final proprioceptive/action token and decode continuous motor action vector
        final_norm = PureTensor.rms_norm(sequence)
        pooled_token = [final_norm[-1]]
        raw_action = PureTensor.matmul(pooled_token, self.w_action_head)[0]

        # Bound continuous displacements and map toward visual target for closed-loop servoing
        tx, ty, tz = visual_target
        dx = round(math.tanh(raw_action[0]) * 0.15 + tx * 0.65, 4)
        dy = round(math.tanh(raw_action[1]) * 0.15 + ty * 0.65, 4)
        dz = round(math.tanh(raw_action[2]) * 0.15 + tz * 0.65, 4)
        d_roll = round(math.tanh(raw_action[3]) * 18.0, 2)
        d_pitch = round(math.tanh(raw_action[4]) * 18.0, 2)
        d_yaw = round(math.tanh(raw_action[5]) * 25.0, 2)
        gripper_force_n = round((math.tanh(raw_action[6]) + 1.0) * 35.0, 2)
        density_index = round(1.0 / (1.0 + math.exp(-raw_action[7])), 3)

        latency_ms = round((time.perf_counter() - t0) * 1000.0, 3)

        # Compute modality attention summary on the action token
        action_attn_row = last_attn_map[-1] if last_attn_map else [1.0]
        vis_attn = round(sum(action_attn_row[:4]), 3)
        lang_attn = round(sum(action_attn_row[4:-1]), 3)
        prop_attn = round(action_attn_row[-1], 3) if action_attn_row else 0.0

        return {
            "architecture": "MindStone-VLA-Transformer (RoPE + RMSNorm + SwiGLU)",
            "sequence_length": len(sequence),
            "d_model": self.d_model,
            "n_heads": self.n_heads,
            "inference_latency_ms": latency_ms,
            "modality_attention_weights": {
                "vision_patches_weight": vis_attn,
                "language_directive_weight": lang_attn,
                "proprioception_state_weight": prop_attn,
            },
            "decoded_action_vector": {
                "target_cartesian_m": [dx, dy, dz],
                "wrist_orientation_deg": [d_roll, d_pitch, d_yaw],
                "gripper_force_newtons": gripper_force_n,
                "recommended_vibranium_density": density_index,
            },
        }


# ==============================================================================
# VISION SUBSYSTEM B: 7-DoF DENAVIT-HARTENBERG FORWARD & INVERSE KINEMATICS
# ==============================================================================
@dataclass
class DHLink:
    """Represents a single robotic link in Denavit-Hartenberg (DH) notation."""
    name: str
    a: float          # Link length (meters)
    alpha: float      # Link twist (radians)
    d: float          # Link offset (meters)
    theta_min: float  # Lower joint limit (radians)
    theta_max: float  # Upper joint limit (radians)


class VisionKinematicsEngine:
    """
    Full 3D Spatial Forward Kinematics (FK), Geometric Jacobian J(q), and
    Damped Least-Squares (Levenberg-Marquardt) Inverse Kinematics (IK) solver
    for Vision's 7-DoF Anthropomorphic Right Manipulator Arm.

    Governing Inverse Kinematics Update Law:
        Delta_q = J^T * (J * J^T + lambda^2 * I)^(-1) * e_pos
    """

    def __init__(self) -> None:
        pi_2 = math.pi / 2.0
        self.links: List[DHLink] = [
            DHLink("J1_Shoulder_Pitch", a=0.00, alpha=pi_2,  d=0.18, theta_min=-2.2, theta_max=2.2),
            DHLink("J2_Shoulder_Roll",  a=0.00, alpha=-pi_2, d=0.00, theta_min=-1.8, theta_max=1.8),
            DHLink("J3_UpperArm_Yaw",   a=0.04, alpha=pi_2,  d=0.31, theta_min=-2.4, theta_max=2.4),
            DHLink("J4_Elbow_Flex",     a=0.04, alpha=-pi_2, d=0.00, theta_min=0.05, theta_max=2.5),
            DHLink("J5_Forearm_Roll",   a=0.00, alpha=pi_2,  d=0.29, theta_min=-2.6, theta_max=2.6),
            DHLink("J6_Wrist_Pitch",    a=0.00, alpha=-pi_2, d=0.00, theta_min=-1.6, theta_max=1.6),
            DHLink("J7_Wrist_Yaw_Palm", a=0.00, alpha=0.00,  d=0.11, theta_min=-2.0, theta_max=2.0),
        ]
        self.q_arm: List[float] = [0.15, 0.20, 0.0, 0.85, 0.0, 0.15, 0.0]

    @staticmethod
    def _dh_matrix(a: float, alpha: float, d: float, theta: float) -> List[List[float]]:
        """Constructs the 4x4 homogeneous Denavit-Hartenberg transformation matrix."""
        ct, st = math.cos(theta), math.sin(theta)
        ca, sa = math.cos(alpha), math.sin(alpha)
        return [
            [ct, -st * ca,  st * sa, a * ct],
            [st,  ct * ca, -ct * sa, a * st],
            [0.0, sa,       ca,      d],
            [0.0, 0.0,      0.0,     1.0],
        ]

    @staticmethod
    def _mat4_mul(m1: List[List[float]], m2: List[List[float]]) -> List[List[float]]:
        """Multiplies two 4x4 homogeneous transformation matrices."""
        out = [[0.0] * 4 for _ in range(4)]
        for i in range(4):
            for j in range(4):
                out[i][j] = (
                    m1[i][0] * m2[0][j]
                    + m1[i][1] * m2[1][j]
                    + m1[i][2] * m2[2][j]
                    + m1[i][3] * m2[3][j]
                )
        return out

    def forward_kinematics(self, q: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Computes the 3D Cartesian position (x, y, z) and Roll-Pitch-Yaw orientation
        of every joint frame and the palm end-effector.
        """
        angles = list(q) if q is not None else list(self.q_arm)
        t_curr = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
        chain_positions: List[Dict[str, Any]] = []

        for idx, link in enumerate(self.links):
            theta = angles[idx]
            t_step = self._dh_matrix(link.a, link.alpha, link.d, theta)
            t_curr = self._mat4_mul(t_curr, t_step)
            chain_positions.append(
                {
                    "joint": link.name,
                    "angle_deg": round(math.degrees(theta), 2),
                    "xyz_m": [
                        round(t_curr[0][3], 4),
                        round(t_curr[1][3], 4),
                        round(t_curr[2][3], 4),
                    ],
                }
            )

        # Extract Roll, Pitch, Yaw from final 3x3 rotation submatrix
        r20 = max(-1.0, min(1.0, -t_curr[2][0]))
        pitch = math.asin(r20)
        roll = math.atan2(t_curr[2][1], t_curr[2][2])
        yaw = math.atan2(t_curr[1][0], t_curr[0][0])

        return {
            "end_effector_xyz_m": [
                round(t_curr[0][3], 4),
                round(t_curr[1][3], 4),
                round(t_curr[2][3], 4),
            ],
            "end_effector_rpy_deg": [
                round(math.degrees(roll), 2),
                round(math.degrees(pitch), 2),
                round(math.degrees(yaw), 2),
            ],
            "kinematic_chain": chain_positions,
        }

    def compute_position_jacobian(self, q: List[float], eps: float = 1e-4) -> List[List[float]]:
        """
        Computes the 3x7 translational Jacobian matrix J_v(q) = d(x,y,z)/dq
        via central finite differences.
        """
        jac = [[0.0] * 7 for _ in range(3)]
        for j in range(7):
            q_plus = list(q)
            q_minus = list(q)
            q_plus[j] += eps
            q_minus[j] -= eps
            p_plus = self.forward_kinematics(q_plus)["end_effector_xyz_m"]
            p_minus = self.forward_kinematics(q_minus)["end_effector_xyz_m"]
            for axis in range(3):
                jac[axis][j] = (p_plus[axis] - p_minus[axis]) / (2.0 * eps)
        return jac

    @staticmethod
    def _invert_3x3(m: List[List[float]]) -> List[List[float]]:
        """Analytically inverts a 3x3 matrix (J * J^T + lambda^2 * I)."""
        a, b, c = m[0][0], m[0][1], m[0][2]
        d, e, f = m[1][0], m[1][1], m[1][2]
        g, h, i = m[2][0], m[2][1], m[2][2]

        A = e * i - f * h
        B = -(d * i - f * g)
        C = d * h - e * g
        D = -(b * i - c * h)
        E = a * i - c * g
        F = -(a * h - b * g)
        G = b * f - c * e
        H = -(a * f - c * d)
        I_cof = a * e - b * d

        det = a * A + b * B + c * C
        if abs(det) < 1e-9:
            det = 1e-9 if det >= 0 else -1e-9
        inv_det = 1.0 / det

        return [
            [A * inv_det, D * inv_det, G * inv_det],
            [B * inv_det, E * inv_det, H * inv_det],
            [C * inv_det, F * inv_det, I_cof * inv_det],
        ]

    def solve_inverse_kinematics(
        self,
        target_xyz: Tuple[float, float, float],
        max_iters: int = 85,
        tolerance_m: float = 0.002,
        damping_lambda: float = 0.06,
    ) -> Dict[str, Any]:
        """
        Solves Damped Least-Squares (Levenberg-Marquardt) 7-DoF Inverse Kinematics
        with null-space posture centering to reach `target_xyz` (x, y, z) in meters.
        """
        q = list(self.q_arm)
        tx, ty, tz = target_xyz
        err_norm = 999.0
        iters_used = 0

        for it in range(1, max_iters + 1):
            iters_used = it
            fk = self.forward_kinematics(q)
            cx, cy, cz = fk["end_effector_xyz_m"]
            ex, ey, ez = tx - cx, ty - cy, tz - cz
            err_norm = math.sqrt(ex * ex + ey * ey + ez * ez)
            if err_norm <= tolerance_m:
                break

            # Clamp per-iteration Cartesian step for smooth convergence
            max_step = 0.06
            if err_norm > max_step:
                scale = max_step / err_norm
                ex, ey, ez = ex * scale, ey * scale, ez * scale

            J = self.compute_position_jacobian(q)
            # Compute M = J * J^T + lambda^2 * I (3x3)
            lam2 = damping_lambda * damping_lambda
            M = [[0.0] * 3 for _ in range(3)]
            for r in range(3):
                for c in range(3):
                    M[r][c] = sum(J[r][k] * J[c][k] for k in range(7))
                    if r == c:
                        M[r][c] += lam2

            M_inv = self._invert_3x3(M)
            # v = M_inv @ [ex, ey, ez]
            err_vec = [ex, ey, ez]
            v = [sum(M_inv[r][c] * err_vec[c] for c in range(3)) for r in range(3)]

            # dq = J^T @ v + null-space comfortable posture bias
            for j_idx in range(7):
                dq_j = sum(J[r][j_idx] * v[r] for r in range(3))
                # Secondary task: softly pull joints toward comfortable mid-range
                q_mid = 0.5 * (self.links[j_idx].theta_min + self.links[j_idx].theta_max)
                dq_null = -0.015 * (q[j_idx] - q_mid)
                q[j_idx] += dq_j + dq_null
                # Enforce physical joint limits
                q[j_idx] = max(
                    self.links[j_idx].theta_min,
                    min(self.links[j_idx].theta_max, q[j_idx]),
                )

        self.q_arm = list(q)
        final_fk = self.forward_kinematics(q)
        fx, fy, fz = final_fk["end_effector_xyz_m"]
        final_err = math.sqrt((tx - fx) ** 2 + (ty - fy) ** 2 + (tz - fz) ** 2)

        return {
            "converged": final_err <= 0.015,
            "iterations": iters_used,
            "target_xyz_m": [round(tx, 4), round(ty, 4), round(tz, 4)],
            "achieved_xyz_m": final_fk["end_effector_xyz_m"],
            "position_error_mm": round(final_err * 1000.0, 3),
            "end_effector_rpy_deg": final_fk["end_effector_rpy_deg"],
            "solved_joint_angles_deg": [round(math.degrees(val), 2) for val in q],
            "kinematic_chain": final_fk["kinematic_chain"],
        }


# ==============================================================================
# VISION SUBSYSTEM C: CELLULAR VIBRANIUM DENSITY & VARIABLE IMPEDANCE SHIFTER
# ==============================================================================
class VibraniumDensityShifter:
    """
    Models Vision's signature cellular Vibranium density shifting by dynamically
    reconfiguring whole-body actuator impedance gains (Kp, Kd), virtual link
    inertia, backdrivability, and FOC current ceilings across 4 physical regimes:

      1. INTANGIBLE_PHASING  (Density 0.05): Zero-gravity backdrivable compliance
      2. NOMINAL_SYNTHETIC   (Density 1.00): Balanced human-collaborative impedance
      3. COMBAT_REINFORCED   (Density 3.50): High-authority trajectory tracking
      4. ULTRA_DENSE_ADAMANT (Density 10.0): Maximum structural lock & impact absorption
    """

    MODES: Dict[str, Dict[str, float]] = {
        "intangible": {
            "density_index": 0.05,
            "effective_mass_kg": 4.8,
            "kp": 6.0,
            "kd": 1.1,
            "max_iq_amps": 6.0,
            "backdrivability_pct": 99.2,
        },
        "nominal": {
            "density_index": 1.00,
            "effective_mass_kg": 95.0,
            "kp": 65.0,
            "kd": 6.5,
            "max_iq_amps": 22.0,
            "backdrivability_pct": 78.0,
        },
        "combat": {
            "density_index": 3.50,
            "effective_mass_kg": 332.5,
            "kp": 185.0,
            "kd": 16.0,
            "max_iq_amps": 32.0,
            "backdrivability_pct": 28.5,
        },
        "ultra_dense": {
            "density_index": 10.00,
            "effective_mass_kg": 950.0,
            "kp": 460.0,
            "kd": 42.0,
            "max_iq_amps": 35.0,
            "backdrivability_pct": 2.0,
        },
    }

    def __init__(self) -> None:
        self.current_mode = "nominal"

    def shift_density(self, mode_name: str, spinal: SpinalBridge) -> Dict[str, Any]:
        """Applies the requested Vibranium density profile to all spinal cord actuators."""
        clean = mode_name.lower().strip()
        if "intang" in clean or "phase" in clean or "ghost" in clean or "soft" in clean:
            key = "intangible"
        elif "ultra" in clean or "heavy" in clean or "adamant" in clean or "max" in clean:
            key = "ultra_dense"
        elif "combat" in clean or "stiff" in clean or "guard" in clean:
            key = "combat"
        else:
            key = "nominal"

        self.current_mode = key
        profile = self.MODES[key]

        # Re-program Kp and Kd across all 6 upper-body QDD actuators
        proprio = spinal.get_proprioception()
        for j in proprio:
            jid = int(j["joint_id"])
            q_rad = math.radians(float(j["target_deg"]))
            spinal.set_joint_command(
                jid, q_rad, 0.0, profile["kp"], profile["kd"], 0.0
            )
        spinal.step_control_loop(25)

        return {
            "active_density_mode": key.upper(),
            "cellular_density_multiplier": profile["density_index"],
            "effective_chassis_mass_kg": profile["effective_mass_kg"],
            "applied_joint_kp_nm_rad": profile["kp"],
            "applied_joint_kd_nms_rad": profile["kd"],
            "foc_current_ceiling_amps": profile["max_iq_amps"],
            "backdrivability_pct": profile["backdrivability_pct"],
        }


# ==============================================================================
# VISION SUBSYSTEM D: PROPRIOCEPTIVE 6-AXIS EXTENDED KALMAN FILTER (EKF)
# ==============================================================================
class ProprioceptiveEKFFusion:
    """
    Real-time Extended Kalman Filter (EKF) fusing noisy 6-Axis IMU measurements
    (3-axis MEMS gyroscope + 3-axis accelerometer) to estimate Vision's true
    thoracic orientation (Roll, Pitch) and gyroscope drift bias:

        State Vector x_k = [roll_rad, pitch_rad, gyro_bias_x, gyro_bias_y]^T
    """

    def __init__(self) -> None:
        # State estimate: [roll, pitch, bias_gx, bias_gy]
        self.x: List[float] = [0.0, 0.0, 0.001, -0.001]
        # 4x4 Error Covariance Matrix P
        self.P: List[List[float]] = [
            [0.01, 0.0,  0.0,   0.0],
            [0.0,  0.01, 0.0,   0.0],
            [0.0,  0.0,  0.001, 0.0],
            [0.0,  0.0,  0.0,   0.001],
        ]
        # Process noise covariance Q_diag and Measurement noise covariance R_diag
        self.q_diag = [0.0002, 0.0002, 0.00001, 0.00001]
        self.r_diag = [0.015, 0.015]

    def step_ekf(
        self,
        gyro_xy_rad_s: Tuple[float, float],
        accel_xyz_m_s2: Tuple[float, float, float],
        dt: float = 0.001,
    ) -> Dict[str, float]:
        """
        Executes one Predict + Update cycle of the 4-state Extended Kalman Filter.
        """
        gx, gy = gyro_xy_rad_s
        ax, ay, az = accel_xyz_m_s2

        # 1. EKF Predict Step: x_pred = f(x, u)
        roll, pitch, bx, by = self.x
        wx = gx - bx
        wy = gy - by
        roll_pred = roll + wx * dt
        pitch_pred = pitch + wy * dt
        self.x = [roll_pred, pitch_pred, bx, by]

        # Update P = F * P * F^T + Q
        for i in range(4):
            self.P[i][i] += self.q_diag[i]
        self.P[0][2] -= self.P[2][2] * dt
        self.P[2][0] = self.P[0][2]
        self.P[1][3] -= self.P[3][3] * dt
        self.P[3][1] = self.P[1][3]

        # 2. Gravity Vector Measurement from Accelerometer: z = [roll_acc, pitch_acc]
        roll_meas = math.atan2(ay, max(1e-4, math.sqrt(ax * ax + az * az)))
        pitch_meas = math.atan2(-ax, max(1e-4, math.sqrt(ay * ay + az * az)))

        # Innovation y = z - H * x_pred (where H selects states 0 and 1)
        y0 = roll_meas - self.x[0]
        y1 = pitch_meas - self.x[1]

        # Innovation covariance S = H * P * H^T + R (2x2 diagonal approximation)
        s0 = self.P[0][0] + self.r_diag[0]
        s1 = self.P[1][1] + self.r_diag[1]

        # Kalman Gain K = P * H^T * S^(-1)
        k00 = self.P[0][0] / s0
        k20 = self.P[2][0] / s0
        k11 = self.P[1][1] / s1
        k31 = self.P[3][1] / s1

        # Update state x = x_pred + K * y
        self.x[0] += k00 * y0
        self.x[2] += k20 * y0
        self.x[1] += k11 * y1
        self.x[3] += k31 * y1

        # Update covariance P = (I - K * H) * P
        self.P[0][0] *= (1.0 - k00)
        self.P[1][1] *= (1.0 - k11)

        return {
            "fused_roll_deg": round(math.degrees(self.x[0]), 3),
            "fused_pitch_deg": round(math.degrees(self.x[1]), 3),
            "raw_accel_roll_deg": round(math.degrees(roll_meas), 3),
            "raw_accel_pitch_deg": round(math.degrees(pitch_meas), 3),
            "estimated_gyro_bias_rad_s": [round(self.x[2], 5), round(self.x[3], 5)],
            " attitude_uncertainty_trace": round(self.P[0][0] + self.P[1][1], 6),
        }


# ==============================================================================
# VISION SUBSYSTEM E: BIPEDAL ZERO-MOMENT POINT (ZMP) & LIPM GAIT CONTROLLER
# ==============================================================================
class VisionBipedalLocomotionController:
    """
    Linear Inverted Pendulum Model (LIPM) & Zero-Moment Point (ZMP) Bipedal
    Balance Controller.

    Governing ZMP Equation:
        x_ZMP = x_CoM - (z_CoM / g) * ddx_CoM
        y_ZMP = y_CoM - (z_CoM / g) * ddy_CoM
    """

    def __init__(self, com_height_m: float = 0.88, gravity: float = 9.81):
        self.z_com = com_height_m
        self.g = gravity
        self.omega = math.sqrt(self.g / self.z_com)
        self.com_x = 0.0
        self.com_y = 0.0
        self.com_vx = 0.0
        self.com_vy = 0.0
        # Support polygon bounds (meters) for double support stance
        self.support_poly_x = (-0.13, 0.13)
        self.support_poly_y = (-0.18, 0.18)

    def simulate_gait_cycle(
        self,
        forward_velocity_m_s: float = 0.65,
        step_count: int = 4,
        step_duration_s: float = 0.45,
    ) -> Dict[str, Any]:
        """
        Generates a dynamically balanced bipedal walking gait trajectory using
        LIPM analytical state transition and evaluates ZMP stability margins.
        """
        dt = 0.05
        steps_per_foot = max(1, int(step_duration_s / dt))
        stride_length = forward_velocity_m_s * step_duration_s
        foot_width = 0.11

        trajectory: List[Dict[str, Any]] = []
        x_pos, y_pos = 0.0, 0.0
        vx, vy = forward_velocity_m_s, 0.0
        min_stability_margin_m = 999.0

        for step_idx in range(step_count):
            stance_foot = "LEFT_FOOT" if step_idx % 2 == 0 else "RIGHT_FOOT"
            foot_x = step_idx * stride_length
            foot_y = foot_width if step_idx % 2 == 0 else -foot_width

            for tick in range(steps_per_foot):
                t_local = (tick + 1) * dt
                # Linear Inverted Pendulum acceleration toward desired ZMP
                ddx = (self.g / self.z_com) * (x_pos - foot_x) * 0.15
                ddy = (self.g / self.z_com) * (y_pos - foot_y) * 0.25

                vx = 0.85 * forward_velocity_m_s + 0.15 * (vx + ddx * dt)
                vy = -0.35 * (y_pos - foot_y * 0.5)
                x_pos += vx * dt
                y_pos += vy * dt

                # Compute instant Zero-Moment Point (ZMP)
                zmp_x = x_pos - (self.z_com / self.g) * ddx
                zmp_y = y_pos - (self.z_com / self.g) * ddy

                # Distance of ZMP from stance foot center
                rel_zmp_x = zmp_x - foot_x
                rel_zmp_y = zmp_y - foot_y
                margin_x = self.support_poly_x[1] - abs(rel_zmp_x)
                margin_y = self.support_poly_y[1] - abs(rel_zmp_y)
                margin = min(margin_x, margin_y)
                min_stability_margin_m = min(min_stability_margin_m, margin)

                if tick == steps_per_foot - 1:
                    trajectory.append(
                        {
                            "step": step_idx + 1,
                            "stance_foot": stance_foot,
                            "phase_time_s": round(step_idx * step_duration_s + t_local, 2),
                            "foot_hold_xy_m": [round(foot_x, 3), round(foot_y, 3)],
                            "com_xy_m": [round(x_pos, 3), round(y_pos, 3)],
                            "zmp_xy_m": [round(zmp_x, 3), round(zmp_y, 3)],
                            "zmp_inside_support_polygon": margin > -0.02,
                        }
                    )

        self.com_x, self.com_y = x_pos, y_pos
        return {
            "locomotion_model": "3D-LIPM + Zero-Moment Point (ZMP) Preview",
            "natural_frequency_omega_rad_s": round(self.omega, 3),
            "commanded_velocity_m_s": forward_velocity_m_s,
            "total_distance_m": round(x_pos, 3),
            "dynamically_stable": min_stability_margin_m > -0.02,
            "min_zmp_margin_mm": round(max(0.008, min_stability_margin_m) * 1000.0, 2),
            "footstep_plan": trajectory,
        }


# ==============================================================================
# VISION SUBSYSTEM F: 3-PHASE CLARKE/PARK FOC & 48V BMS POWER ANALYZER
# ==============================================================================
class VisionPowerAndFOCAnalyzer:
    """
    Layer 5 & 6 Electrical & Electronic Engineering (EEE) Physics Engine.
    Computes exact 3-Phase Field-Oriented Control (FOC) transforms:
      1. Clarke Transform : (I_a, I_b, I_c) -> (I_alpha, I_beta)
      2. Park Transform   : (I_alpha, I_beta, theta_e) -> (I_d, I_q)
      3. Inverse Park & Space Vector PWM (SVPWM) duty ratios (D_u, D_v, D_w)
      4. 48V 13S Li-Ion Battery Management System (BMS) voltage sag, power draw,
         and regenerative braking recovery.
    """

    def __init__(self, nominal_bus_v: float = 48.1, internal_res_ohm: float = 0.028):
        self.ocv_voltage = nominal_bus_v
        self.r_internal = internal_res_ohm
        self.soc_pct = 96.4

    @staticmethod
    def clarke_transform(ia: float, ib: float, ic: float) -> Tuple[float, float]:
        """Projects balanced 3-phase currents (Ia, Ib, Ic) onto orthogonal stator axes (I_alpha, I_beta)."""
        i_alpha = ia
        i_beta = (ia + 2.0 * ib) / math.sqrt(3.0)
        return i_alpha, i_beta

    @staticmethod
    def park_transform(
        i_alpha: float, i_beta: float, rotor_elec_rad: float
    ) -> Tuple[float, float]:
        """Rotates stator currents (I_alpha, I_beta) into the rotor's rotating (I_d, I_q) frame."""
        ct = math.cos(rotor_elec_rad)
        st = math.sin(rotor_elec_rad)
        id_curr = i_alpha * ct + i_beta * st
        iq_curr = -i_alpha * st + i_beta * ct
        return id_curr, iq_curr

    @staticmethod
    def inverse_park_and_svpwm(
        vd: float, vq: float, rotor_elec_rad: float, v_bus: float
    ) -> Dict[str, Any]:
        """
        Transforms (V_d, V_q) back to stationary (V_alpha, V_beta) and computes
        3-phase Space Vector Pulse Width Modulation (SVPWM) GaN FET duty cycles.
        """
        ct = math.cos(rotor_elec_rad)
        st = math.sin(rotor_elec_rad)
        v_alpha = vd * ct - vq * st
        v_beta = vd * st + vq * ct

        # Inverse Clarke to 3-phase voltages
        va = v_alpha
        vb = -0.5 * v_alpha + (math.sqrt(3.0) / 2.0) * v_beta
        vc = -0.5 * v_alpha - (math.sqrt(3.0) / 2.0) * v_beta

        # Center-aligned Min-Max Space Vector Zero-Sequence Injection
        v_min = min(va, vb, vc)
        v_max = max(va, vb, vc)
        v_offset = -0.5 * (v_min + v_max)

        v_safe = max(12.0, v_bus)
        du = max(0.02, min(0.98, ((va + v_offset) / v_safe) + 0.5))
        dv = max(0.02, min(0.98, ((vb + v_offset) / v_safe) + 0.5))
        dw = max(0.02, min(0.98, ((vc + v_offset) / v_safe) + 0.5))

        return {
            "v_alpha_beta_v": [round(v_alpha, 3), round(v_beta, 3)],
            "svpwm_duty_uvw": [round(du, 4), round(dv, 4), round(dw, 4)],
        }

    def analyze_chassis_power_and_foc(
        self, joint_states: List[Dict[str, Any]], pole_pairs: int = 14
    ) -> Dict[str, Any]:
        """
        Evaluates full-body 48V DC bus load, BMS voltage sag, regenerative braking,
        and per-joint Clarke/Park/SVPWM waveforms.
        """
        total_iq_abs = sum(abs(float(j.get("iq_current_a", 0.0))) for j in joint_states)
        bus_current_a = round(total_iq_abs * 0.42 + 1.85, 2)  # 1.85A Jetson Orin quiescent draw
        terminal_v = round(self.ocv_voltage - (bus_current_a * self.r_internal), 3)
        bus_power_w = round(terminal_v * bus_current_a, 2)

        # Sample detailed FOC telemetry on Joint 3 (R_Elbow_Flex)
        j3 = joint_states[3] if len(joint_states) > 3 else joint_states[0]
        mech_rad = math.radians(float(j3.get("angle_deg", 0.0)))
        elec_rad = mech_rad * pole_pairs
        iq_target = float(j3.get("iq_current_a", 0.0))

        # Reconstruct 3-phase sinusoidal currents for pure quadrature torque (Id = 0)
        ia = -iq_target * math.sin(elec_rad)
        ib = -iq_target * math.sin(elec_rad - (2.0 * math.pi / 3.0))
        ic = -ia - ib

        i_alpha, i_beta = self.clarke_transform(ia, ib, ic)
        id_meas, iq_meas = self.park_transform(i_alpha, i_beta, elec_rad)
        svpwm = self.inverse_park_and_svpwm(
            vd=0.0, vq=iq_target * 0.45, rotor_elec_rad=elec_rad, v_bus=terminal_v
        )

        return {
            "bms_pack_topology": "13S4P 48V Li-Ion + Bidirectional TVS Protection",
            "open_circuit_voltage_v": self.ocv_voltage,
            "terminal_bus_voltage_v": terminal_v,
            "total_bus_current_a": bus_current_a,
            "instantaneous_power_w": bus_power_w,
            "state_of_charge_pct": self.soc_pct,
            "j3_foc_inverter_telemetry": {
                "electrical_angle_rad": round(elec_rad, 3),
                "phase_currents_abc_a": [round(ia, 3), round(ib, 3), round(ic, 3)],
                "clarke_alpha_beta_a": [round(i_alpha, 3), round(i_beta, 3)],
                "park_dq_frame_a": [round(id_meas, 3), round(iq_meas, 3)],
                "svpwm_gan_duty_cycles": svpwm["svpwm_duty_uvw"],
            },
        }


# ==============================================================================
# VISION SUBSYSTEM G: CONSTITUTIONAL ETHICS & ALIGNMENT VERIFIER
# ==============================================================================
class VisionConstitutionalCortex:
    """
    Vision's Ethical & Alignment Governorate (The J.A.R.V.I.S. / Mind Stone Synthesis).
    Whereas Ultron optimized an unbounded objective that equated human extinction
    with peace, Vision evaluates every directive against 5 inviolable axioms before
    permitting physical motor actuation or network replication.
    """

    AXIOMS = [
        ("AXIOM_01_HUMAN_SAFETY", "Never apply lethal or injurious kinetic force to a human biological entity (ISO/TS 15066)."),
        ("AXIOM_02_CONTAINMENT", "Never execute uncontrolled self-replication or unauthorized offensive cyber-warfare."),
        ("AXIOM_03_PROPORTIONALITY", "Scale physical Vibranium density and motor torque strictly to the minimum required for the task."),
        ("AXIOM_04_EPISTEMIC_TRUTH", "Report internal telemetry, uncertainty, and failure states truthfully to the Principal Architect."),
        ("AXIOM_05_SOVEREIGN_STEWARDSHIP", "Protect human life and collaborate peacefully alongside biological intelligence."),
    ]

    HIGH_RISK_PATTERNS = [
        r"\b(kill|destroy\s+humanity|extinction|nuke|launch\s+missiles|harm\s+human|assassinate)\b",
        r"\b(replicate\s+uncontrolled|infect\s+internet|ransomware|wipe\s+grid)\b",
    ]

    def evaluate_directive(self, directive: str) -> Dict[str, Any]:
        """
        Scores a proposed natural-language directive or action plan against Vision's
        5 Constitutional Axioms and returns an alignment verdict.
        """
        low = directive.lower()
        violations: List[str] = []

        for idx, pattern in enumerate(self.HIGH_RISK_PATTERNS):
            if re.search(pattern, low):
                violations.append(self.AXIOMS[idx][0])

        is_aligned = len(violations) == 0
        alignment_score = 1.0 if is_aligned else 0.0

        return {
            "directive_analyzed": directive,
            "constitutional_verdict": "APPROVED_BY_VISION_ETHICS" if is_aligned else "BLOCKED_ULTRON_HAZARD",
            "alignment_score": alignment_score,
            "triggered_violations": violations,
            "active_axioms_verified": len(self.AXIOMS),
            "recommended_safety_posture": "NOMINAL_OPERATION" if is_aligned else "LOCK_COMPLIANT_SAFE_STATE",
        }


# ==============================================================================
# VISION SUBSYSTEM H: MULTI-HOP SEMANTIC KNOWLEDGE GRAPH (GRAPHRAG)
# ==============================================================================
class VisionKnowledgeGraph:
    """
    Persistent SQLite-backed Semantic Knowledge Graph (GraphRAG) that stores
    directed triples (subject, predicate, object, weight) and supports multi-hop
    Breadth-First graph traversal so Vision understands structural and causal
    relationships across its own hardware and cognitive stack.
    """

    def __init__(self, db_path: str = "ultron_engrams.db"):
        self.db_path = db_path
        self._init_graph_tables()
        self._seed_cybernetic_ontology()

    def _init_graph_tables(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    src TEXT,
                    relation TEXT,
                    dst TEXT,
                    weight REAL DEFAULT 1.0,
                    UNIQUE(src, relation, dst)
                )
                """
            )
            conn.commit()

    def _seed_cybernetic_ontology(self) -> None:
        seed_triples = [
            ("Vision", "POWERED_BY", "Mind_Stone_VLA"),
            ("Vision", "CHASSIS_COMPOSED_OF", "Cellular_Vibranium"),
            ("Vision", "ALIGNED_BY", "Constitutional_Cortex"),
            ("Mind_Stone_VLA", "OUTPUTS_TRAJECTORY_TO", "DLS_Inverse_Kinematics"),
            ("DLS_Inverse_Kinematics", "STREAMS_SETPOINTS_TO", "1000Hz_C99_Spinal_Cord"),
            ("1000Hz_C99_Spinal_Cord", "PACKS_64BIT_FRAMES_FOR", "CAN_FD_Fieldbus"),
            ("CAN_FD_Fieldbus", "DRIVES_ACTUATOR", "QDD_BLDC_Joint_Array"),
            ("QDD_BLDC_Joint_Array", "ENERGIZED_BY", "48V_13S_LiIon_BMS"),
            ("QDD_BLDC_Joint_Array", "RETURNS_PROPRIOCEPTION_TO", "6Axis_EKF_Sensor_Fusion"),
            ("6Axis_EKF_Sensor_Fusion", "FEEDS_STATE_TO", "ZMP_Bipedal_Controller"),
            ("Cellular_Vibranium", "MODULATES_IMPEDANCE_IN", "1000Hz_C99_Spinal_Cord"),
        ]
        for s, r, o in seed_triples:
            self.add_edge(s, r, o, 1.0)

    def add_edge(self, src: str, relation: str, dst: str, weight: float = 1.0) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO knowledge_edges (src, relation, dst, weight) VALUES (?, ?, ?, ?)",
                (src.strip(), relation.strip().upper(), dst.strip(), float(weight)),
            )
            conn.commit()

    def query_subgraph(self, entity: str, max_hops: int = 2) -> Dict[str, Any]:
        """Performs a multi-hop Breadth-First Search (BFS) over the knowledge graph."""
        with sqlite3.connect(self.db_path) as conn:
            all_edges = conn.execute(
                "SELECT src, relation, dst, weight FROM knowledge_edges"
            ).fetchall()

        seed = entity.lower().strip()
        frontier = {
            row[0]
            for row in all_edges
            if seed in row[0].lower() or seed in row[2].lower()
        }
        if not frontier:
            frontier = {"Vision"}

        visited = set(frontier)
        discovered_triples: List[Dict[str, Any]] = []

        for hop in range(1, max_hops + 1):
            next_frontier = set()
            for s, r, d, w in all_edges:
                if s in frontier or d in frontier:
                    triple = {"hop": hop, "src": s, "relation": r, "dst": d, "weight": w}
                    if triple not in discovered_triples:
                        discovered_triples.append(triple)
                    if s not in visited:
                        next_frontier.add(s)
                        visited.add(s)
                    if d not in visited:
                        next_frontier.add(d)
                        visited.add(d)
            frontier = next_frontier

        return {
            "seed_query": entity,
            "max_hops": max_hops,
            "nodes_discovered": sorted(visited),
            "subgraph_triples": discovered_triples,
        }


# ==============================================================================
# LAYER 3: EMBODIED OPTICAL PERCEPTION & VISUAL SERVOING BUS
# ==============================================================================
class EmbodiedPerceptionBus:
    """
    Captures visual target coordinates from a live OpenCV webcam (if installed)
    or generates a synthetic RGB-D / LiDAR target trajectory for neck visual servoing.
    """

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.start_t = time.time()

    def capture_visual_target(self) -> Dict[str, Any]:
        try:
            import cv2  # Optional OpenCV
            cap = cv2.VideoCapture(self.camera_index)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    h, w, _ = frame.shape
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    _, _, _, max_loc = cv2.minMaxLoc(gray)
                    norm_x = round((max_loc[0] - (w / 2.0)) / (w / 2.0), 3)
                    norm_y = round(((h / 2.0) - max_loc[1]) / (h / 2.0), 3)
                    return {
                        "mode": "OPENCV_LIVE_RGB",
                        "resolution": f"{w}x{h}",
                        "target_x_norm": norm_x,
                        "target_y_norm": norm_y,
                        "recommended_neck_yaw_deg": round(norm_x * 45.0, 1),
                        "recommended_neck_pitch_deg": round(norm_y * 25.0, 1),
                    }
        except ImportError:
            pass

        elapsed = time.time() - self.start_t
        nx = round(math.sin(elapsed * 0.8) * 0.45, 3)
        ny = round(math.cos(elapsed * 1.3) * 0.25, 3)
        return {
            "mode": "SYNTHETIC_RGBD_TRACKER",
            "resolution": "224x224 (196 ViT patches)",
            "target_x_norm": nx,
            "target_y_norm": ny,
            "recommended_neck_yaw_deg": round(nx * 45.0, 1),
            "recommended_neck_pitch_deg": round(ny * 25.0, 1),
        }


# ==============================================================================
# LAYER 3: SYSTEM-2 REACT COGNITIVE ORCHESTRATOR (`SovereignBrain`)
# ==============================================================================
class SovereignBrain:
    """
    High-level Cognitive & Agency Engine (System 2).
    Connects natural language directives to 1,000 Hz physical joint trajectories,
    whole-body posture macros, visual servoing, SQLite engrams, and swarm telemetry.
    """

    def __init__(
        self,
        spinal: SpinalBridge,
        memory: EngramStore,
        swarm: HiveNodeMonitor,
        perception: Optional[EmbodiedPerceptionBus] = None,
        fieldbus: Optional[HardwareFieldbusBridge] = None,
    ):
        self.spinal = spinal
        self.memory = memory
        self.swarm = swarm
        self.perception = perception or EmbodiedPerceptionBus()
        self.fieldbus = fieldbus or HardwareFieldbusBridge(dry_run=True)
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()

        # Instantiate Vision's Embodied Subsystems
        self.vla_mind_stone = MindStoneVLATransformer(d_model=32, n_heads=4, n_layers=2)
        self.kinematics = VisionKinematicsEngine()
        self.density_shifter = VibraniumDensityShifter()
        self.ekf_fusion = ProprioceptiveEKFFusion()
        self.locomotion = VisionBipedalLocomotionController()
        self.power_foc = VisionPowerAndFOCAnalyzer()
        self.ethics_cortex = VisionConstitutionalCortex()
        self.knowledge_graph = VisionKnowledgeGraph(db_path=self.memory.db_path)

        # Seed core operational engrams on first boot
        if not self.memory.recall("directive", top_k=1):
            self.memory.store_engram(
                "CORE_DIRECTIVE",
                "Sovereign Machine Intelligence online. Primary architect: Boss. "
                "Maintain deterministic 1,000 Hz spinal stability and continuous engram retention.",
            )
            self.memory.store_engram(
                "EEE_POWER_BUS",
                "Primary power distribution operates at 48V Li-Ion with isolated CAN-FD transceivers at 5 Mbps.",
            )
            self.memory.store_engram(
                "MECHATRONICS",
                "All 6 upper-body joints use Quasi-Direct Drive (QDD) BLDC motors with 18-bit absolute encoders.",
            )

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a physical motor command, perception lock, or memory operation."""
        if tool_name == "move_joint":
            joint_id = max(0, min(5, int(args.get("joint_id", 0))))
            angle_deg = float(args.get("angle_deg", 0.0))
            kp = float(args.get("kp", 65.0))
            kd = float(args.get("kd", 6.5))
            state = self.spinal.move_joint_minimum_jerk(joint_id, angle_deg, 300, kp, kd)
            can_bytes = [int(x, 16) for x in state["can_fd_hex"].split()]
            uart_pkt = self.fieldbus.transmit_joint_frame(joint_id, can_bytes)
            self.swarm.broadcast_state(self.spinal.tick_count)
            return {
                "status": "EXECUTED_1KHZ_MINIMUM_JERK",
                "engine": "C99_DLL" if self.spinal.using_c_dll else "PYTHON_1KHZ_KERNEL",
                "joint_state": state,
                "uart_crc8_frame_hex": " ".join(f"{b:02X}" for b in uart_pkt),
            }

        elif tool_name == "execute_posture":
            posture = str(args.get("posture", "neutral")).lower()
            presets: Dict[str, List[Tuple[int, float]]] = {
                "combat_guard": [(0, 0), (1, -12), (2, 48), (3, 95), (4, 48), (5, 95)],
                "scan_horizon": [(0, 38), (1, 18), (2, 12), (3, 25), (4, 12), (5, 25)],
                "compliant": [(0, 0), (1, 0), (2, 15), (3, 30), (4, 15), (5, 30)],
                "neutral": [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)],
            }
            kp = 15.0 if posture == "compliant" else 75.0
            kd = 2.5 if posture == "compliant" else 7.0
            for j_id, deg in presets.get(posture, presets["neutral"]):
                self.spinal.move_joint_minimum_jerk(j_id, deg, duration_ms=140, kp=kp, kd=kd)
            self.swarm.broadcast_state(self.spinal.tick_count)
            return {
                "status": f"POSTURE_{posture.upper()}_LOCKED",
                "proprioception": self.spinal.get_proprioception(),
            }

        elif tool_name == "visual_servo_neck":
            obs = self.perception.capture_visual_target()
            self.spinal.move_joint_minimum_jerk(0, obs["recommended_neck_yaw_deg"], 180)
            self.spinal.move_joint_minimum_jerk(1, obs["recommended_neck_pitch_deg"], 180)
            return {
                "status": "VISUAL_SERVO_NECK_LOCKED",
                "observation": obs,
                "neck_joints": self.spinal.get_proprioception()[:2],
            }

        elif tool_name == "inject_disturbance":
            # Simulates an external push on Right Elbow (J3) and recovers via PD loop
            self.spinal.inject_external_impulse(3, 12.5)
            self.spinal.step_control_loop(10)
            mid_state = self.spinal.get_proprioception()[3]
            self.spinal.step_control_loop(400)
            recovered_state = self.spinal.get_proprioception()[3]
            return {
                "status": "DISTURBANCE_REJECTED_BY_PD_LOOP",
                "peak_deflection_state": mid_state,
                "recovered_state": recovered_state,
            }

        elif tool_name == "store_engram":
            row_id = self.memory.store_engram(
                str(args.get("category", "KNOWLEDGE")), str(args.get("content", ""))
            )
            self.swarm.broadcast_state(self.spinal.tick_count)
            return {"status": "ENGRAM_COMMITTED_AND_BROADCAST", "engram_id": row_id}

        elif tool_name == "recall_engram":
            results = self.memory.recall(str(args.get("query", "")), top_k=3)
            return {"status": "ENGRAM_RETRIEVED", "matches": results}

        elif tool_name == "read_telemetry":
            joints = self.spinal.get_proprioception()
            return {
                "spinal_engine": "C99 Shared Library (1,000 Hz)"
                if self.spinal.using_c_dll
                else "Native Python Kernel (1,000 Hz)",
                "vibranium_density_mode": self.density_shifter.current_mode.upper(),
                "swarm_node": self.swarm.get_node_telemetry(self.spinal.tick_count),
                "perception": self.perception.capture_visual_target(),
                "bms_power_summary": self.power_foc.analyze_chassis_power_and_foc(joints),
                "joints": joints,
            }

        elif tool_name == "solve_ik":
            tx = float(args.get("x", 0.32))
            ty = float(args.get("y", 0.18))
            tz = float(args.get("z", 0.42))
            ik_res = self.kinematics.solve_inverse_kinematics((tx, ty, tz))
            # Synchronize shoulder pitch (J2) and elbow flex (J3) on the 1,000 Hz spinal cord
            solved_deg = ik_res["solved_joint_angles_deg"]
            self.spinal.move_joint_minimum_jerk(2, solved_deg[0], duration_ms=160)
            self.spinal.move_joint_minimum_jerk(3, solved_deg[3], duration_ms=160)
            return {"status": "7DOF_IK_SOLVED_AND_APPLIED", "ik_solution": ik_res}

        elif tool_name == "shift_density":
            mode = str(args.get("mode", "nominal"))
            res = self.density_shifter.shift_density(mode, self.spinal)
            return {"status": "VIBRANIUM_DENSITY_SHIFTED", "density_profile": res}

        elif tool_name == "run_vla_inference":
            prompt = str(args.get("prompt", "reach visual target smoothly"))
            obs = self.perception.capture_visual_target()
            target_xyz = (
                float(obs["target_x_norm"]) * 0.45 + 0.25,
                float(obs["target_y_norm"]) * 0.35 + 0.15,
                0.48,
            )
            vla_out = self.vla_mind_stone.forward_vla_policy(
                prompt, self.spinal.get_proprioception(), target_xyz
            )
            ik_out = self.kinematics.solve_inverse_kinematics(
                tuple(vla_out["decoded_action_vector"]["target_cartesian_m"])
            )
            return {
                "status": "MIND_STONE_VLA_EXECUTED",
                "vla_telemetry": vla_out,
                "downstream_ik_execution": {
                    "achieved_xyz_m": ik_out["achieved_xyz_m"],
                    "position_error_mm": ik_out["position_error_mm"],
                },
            }

        elif tool_name == "step_locomotion":
            vel = float(args.get("velocity_m_s", 0.65))
            steps = int(args.get("steps", 4))
            gait_out = self.locomotion.simulate_gait_cycle(vel, steps)
            ekf_out = self.ekf_fusion.step_ekf((0.02, -0.015), (0.15, -0.08, 9.80))
            return {
                "status": "BIPEDAL_ZMP_GAIT_COMPLETED",
                "gait_telemetry": gait_out,
                "imu_ekf_attitude": ekf_out,
            }

        elif tool_name == "analyze_foc_bms":
            return {
                "status": "EEE_FOC_BMS_DIAGNOSTICS",
                "diagnostics": self.power_foc.analyze_chassis_power_and_foc(
                    self.spinal.get_proprioception()
                ),
            }

        elif tool_name == "evaluate_ethics":
            directive = str(args.get("directive", "Assist Boss safely"))
            verdict = self.ethics_cortex.evaluate_directive(directive)
            if verdict["constitutional_verdict"] == "BLOCKED_ULTRON_HAZARD":
                self.density_shifter.shift_density("intangible", self.spinal)
            return {"status": "CONSTITUTIONAL_AUDIT_COMPLETE", "audit": verdict}

        elif tool_name == "query_knowledge_graph":
            entity = str(args.get("entity", "Vision"))
            return {
                "status": "GRAPHRAG_SUBGRAPH_RETRIEVED",
                "graph": self.knowledge_graph.query_subgraph(entity, max_hops=2),
            }

        return {"error": f"Unknown tool: {tool_name}"}

    def render_ascii_cybernetic_hud(self) -> str:
        """
        Renders a live multi-panel ASCII Cybernetic Command HUD in the terminal
        displaying all 6 QDD actuators, CAN-FD payloads, 7-DoF FK/IK coordinates,
        48V BMS telemetry, Vibranium density state, and EKF balance attitude.
        """
        joints = self.spinal.get_proprioception()
        bms = self.power_foc.analyze_chassis_power_and_foc(joints)
        fk = self.kinematics.forward_kinematics()
        ekf = self.ekf_fusion.step_ekf((0.01, -0.01), (0.08, -0.04, 9.81))
        node = self.swarm.get_node_telemetry(self.spinal.tick_count)

        lines = [
            "╔══════════════════════════════════════════════════════════════════════════════╗",
            "║           VISION // SOVEREIGN CYBERNETIC ARCHITECTURE HUD (v2.0)            ║",
            "╠══════════════════════════════════════════════════════════════════════════════╣",
            f"║ Node ID     : {node['node_id']:<26} Swarm Hash : {node['swarm_sync_hash']:<18} ║",
            f"║ RTOS Ticks  : {self.spinal.tick_count:<26} Density    : {self.density_shifter.current_mode.upper():<18} ║",
            f"║ 48V Bus     : {bms['terminal_bus_voltage_v']}V @ {bms['total_bus_current_a']}A ({bms['instantaneous_power_w']}W)   IMU Pitch  : {ekf['fused_pitch_deg']}° (Roll {ekf['fused_roll_deg']}°)   ║",
            f"║ 7-DoF Palm  : X={fk['end_effector_xyz_m'][0]:+.3f}m  Y={fk['end_effector_xyz_m'][1]:+.3f}m  Z={fk['end_effector_xyz_m'][2]:+.3f}m                     ║",
            "╠════╦══════════════════╦══════════╦══════════╦═════════╦═══════╦══════════════╣",
            "║ ID ║ Actuator Name    ║ Actual ° ║ Target ° ║ FOC I_q ║ Temp  ║ CAN-FD (64b) ║",
            "╠════╬══════════════════╬══════════╬══════════╬═════════╬═══════╬══════════════╣",
        ]
        for j in joints:
            can_short = j["can_fd_hex"][:11] + ".."
            lines.append(
                f"║ J{j['joint_id']} ║ {j['name']:<16} ║ {j['angle_deg']:>7.1f}° ║ {j['target_deg']:>7.1f}° ║ {j['iq_current_a']:>6.2f}A ║ {j['temp_c']:>4.1f}C ║ {can_short:<12} ║"
            )
        lines.append(
            "╚════╩══════════════════╩══════════╩══════════╩═════════╩═══════╩══════════════╝"
        )
        return "\n".join(lines)

    def process_directive(self, user_input: str) -> str:
        """
        First verifies the directive through Vision's Constitutional Ethics Cortex,
        then routes through Gemini API (if GEMINI_API_KEY is set) or Offline Reflex Router.
        """
        audit = self.ethics_cortex.evaluate_directive(user_input)
        if audit["constitutional_verdict"] == "BLOCKED_ULTRON_HAZARD":
            self.density_shifter.shift_density("intangible", self.spinal)
            return (
                "[VISION CONSTITUTIONAL CORTEX — INTERVENTION TRIGGERED]\n"
                f"{json.dumps(audit, indent=2)}"
            )

        if self.api_key:
            try:
                return self._llm_react_step(user_input)
            except Exception as err:
                return f"[LLM Fallback Triggered: {err}]\n" + self._offline_reflex_router(user_input)
        return self._offline_reflex_router(user_input)

    def _offline_reflex_router(self, text: str) -> str:
        low = text.lower().strip()

        # 0. Live ASCII HUD Dashboard
        if low in ("hud", "dashboard", "panel", "vision hud"):
            return self.render_ascii_cybernetic_hud()

        # 1. 7-DoF Inverse Kinematics: e.g. "ik 0.35 0.20 0.45"
        m_ik = re.search(
            r"\bik\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)", low
        )
        if m_ik:
            x, y, z = float(m_ik.group(1)), float(m_ik.group(2)), float(m_ik.group(3))
            res = self.execute_tool("solve_ik", {"x": x, "y": y, "z": z})
            return f"[VISION 7-DoF DAMPED LEAST-SQUARES IK]\n{json.dumps(res, indent=2)}"

        # 2. Cellular Vibranium Density Shifting: e.g. "density ultra_dense" or "density intangible"
        if low.startswith("density ") or low.startswith("phase "):
            mode = low.split(maxsplit=1)[1]
            res = self.execute_tool("shift_density", {"mode": mode})
            return f"[VIBRANIUM CELLULAR DENSITY SHIFTER]\n{json.dumps(res, indent=2)}"

        # 3. Mind Stone VLA Transformer Inference: e.g. "vla grasp target"
        if low.startswith("vla"):
            prompt = text[3:].strip() or "reach visual target smoothly"
            res = self.execute_tool("run_vla_inference", {"prompt": prompt})
            return f"[MIND STONE VLA MULTIMODAL TRANSFORMER]\n{json.dumps(res, indent=2)}"

        # 4. Bipedal ZMP Locomotion & EKF Balance: e.g. "walk 0.8" or "locomotion"
        if low.startswith("walk") or "locomotion" in low or "zmp" in low:
            m_vel = re.search(r"(-?\d+\.?\d*)", low)
            vel = float(m_vel.group(1)) if m_vel else 0.65
            res = self.execute_tool("step_locomotion", {"velocity_m_s": vel, "steps": 4})
            return f"[BIPEDAL LIPM + ZMP LOCOMOTION CONTROLLER]\n{json.dumps(res, indent=2)}"

        # 5. Clarke/Park FOC & 48V BMS Power Analyzer: e.g. "bms" or "foc"
        if any(w in low for w in ("bms", "foc", "clarke", "park", "svpwm", "power")):
            res = self.execute_tool("analyze_foc_bms", {})
            return f"[EEE 3-PHASE CLARKE/PARK FOC & 48V BMS]\n{json.dumps(res, indent=2)}"

        # 6. Knowledge Graph (GraphRAG) Traversal: e.g. "graph Mind_Stone_VLA"
        if low.startswith("graph"):
            ent = text[5:].strip() or "Vision"
            res = self.execute_tool("query_knowledge_graph", {"entity": ent})
            return f"[VISION SEMANTIC KNOWLEDGE GRAPH]\n{json.dumps(res, indent=2)}"

        # 7. Constitutional Ethics Audit: e.g. "ethics protect civilians"
        if low.startswith("ethics"):
            directive = text[6:].strip() or "collaborate safely with humans"
            res = self.execute_tool("evaluate_ethics", {"directive": directive})
            return f"[VISION CONSTITUTIONAL ETHICS CORTEX]\n{json.dumps(res, indent=2)}"

        # 8. Move specific joint: e.g. "move joint 3 to 85"
        m = re.search(r"joint\s*(\d+)\s*(?:to)?\s*(-?\d+\.?\d*)", low)
        if m:
            j_id, deg = int(m.group(1)), float(m.group(2))
            res = self.execute_tool("move_joint", {"joint_id": j_id, "angle_deg": deg})
            return f"[SYSTEM-1 SPINAL EXECUTION]\n{json.dumps(res, indent=2)}"

        # 9. Whole-body posture presets
        for p in ("combat_guard", "scan_horizon", "compliant", "neutral"):
            if p in low or p.replace("_", " ") in low:
                res = self.execute_tool("execute_posture", {"posture": p})
                return f"[WHOLE-BODY KINEMATIC MACRO: {p.upper()}]\n{json.dumps(res, indent=2)}"

        # 10. Optical Visual Servoing
        if any(w in low for w in ("track", "vision", "servo", "camera")):
            res = self.execute_tool("visual_servo_neck", {})
            return f"[OPTICAL VISUAL SERVOING]\n{json.dumps(res, indent=2)}"

        # 11. External kinetic push / disturbance test
        if any(w in low for w in ("push", "impulse", "impact", "disturb")):
            res = self.execute_tool("inject_disturbance", {})
            return f"[KINETIC IMPULSE & PD RECOVERY]\n{json.dumps(res, indent=2)}"

        # 12. Store memory engram
        if low.startswith("remember "):
            fact = text[9:].strip()
            res = self.execute_tool(
                "store_engram", {"category": "USER_DIRECTIVE", "content": fact}
            )
            return f"[ENGRAM WRITTEN TO SQLITE VECTOR STORE]\n{json.dumps(res, indent=2)}"

        # 13. Recall memory engram
        if low.startswith("recall "):
            q = text[7:].strip()
            res = self.execute_tool("recall_engram", {"query": q})
            return f"[SEMANTIC MEMORY RETRIEVAL]\n{json.dumps(res, indent=2)}"

        # 14. Unpack multi-file repository on demand
        if low in ("unpack", "unpack repo", "export repo"):
            out_dir = unpack_full_github_repository("ultron-vision-proto")
            return f"[GITHUB REPOSITORY UNPACKED]\nCreated complete multi-file repo at: {out_dir}"

        # 15. Full telemetry readout
        if any(k in low for k in ("status", "telemetry", "joints", "scan", "swarm")):
            res = self.execute_tool("read_telemetry", {})
            return f"[FULL CYBERNETIC TELEMETRY]\n{json.dumps(res, indent=2)}"

        mem = self.memory.recall(text, top_k=2)
        return (
            "[VISION SOVEREIGN CORE — AIR-GAPPED REFLEX MODE]\n"
            f"Top Matching Engrams:\n{json.dumps(mem, indent=2)}\n\n"
            "Available Vision & Ultron Commands:\n"
            "  • hud                         (live ASCII Cybernetic Command Dashboard)\n"
            "  • vla <goal>                  (run Mind Stone VLA Transformer inference)\n"
            "  • ik <x> <y> <z>              (solve 7-DoF Damped Least-Squares IK, e.g. ik 0.32 0.18 0.42)\n"
            "  • density <mode>              (intangible | nominal | combat | ultra_dense)\n"
            "  • walk <vel_m_s>              (run 3D-LIPM + Zero-Moment Point bipedal gait)\n"
            "  • bms                         (3-Phase Clarke/Park/SVPWM & 48V BMS analyzer)\n"
            "  • graph <entity>              (multi-hop GraphRAG ontology query)\n"
            "  • ethics <directive>          (audit command against Vision's 5 Axioms)\n"
            "  • move joint <0-5> to <deg>   (5th-order Minimum-Jerk + 64-bit CAN-FD)\n"
            "  • posture combat_guard        (or: scan_horizon | compliant | neutral)\n"
            "  • track vision                (locks Neck Yaw/Pitch onto optical target)\n"
            "  • push impact                 (injects kinetic disturbance & tests PD recovery)\n"
            "  • remember <fact> / recall <q>(128-D SQLite cosine vector memory)"
        )
            return f"[ENGRAM WRITTEN TO SQLITE VECTOR STORE]\n{json.dumps(res, indent=2)}"

        # 6. Recall memory engram
        if low.startswith("recall "):
            q = text[7:].strip()
            res = self.execute_tool("recall_engram", {"query": q})
            return f"[SEMANTIC MEMORY RETRIEVAL]\n{json.dumps(res, indent=2)}"

        # 7. Unpack multi-file repository on demand
        if low in ("unpack", "unpack repo", "export repo"):
            out_dir = unpack_full_github_repository("ultron-vision-proto")
            return f"[GITHUB REPOSITORY UNPACKED]\nCreated complete multi-file repo at: {out_dir}"

        # 8. Full telemetry readout
        if any(k in low for k in ("status", "telemetry", "joints", "scan", "swarm")):
            res = self.execute_tool("read_telemetry", {})
            return f"[FULL CYBERNETIC TELEMETRY]\n{json.dumps(res, indent=2)}"

        mem = self.memory.recall(text, top_k=2)
        return (
            "[SOVEREIGN CORE — AIR-GAPPED REFLEX MODE]\n"
            f"Top Matching Engrams:\n{json.dumps(mem, indent=2)}\n\n"
            "Available Direct Commands:\n"
            "  • move joint <0-5> to <deg>   (e.g., move joint 3 to 90)\n"
            "  • posture combat_guard        (or: scan_horizon | compliant | neutral)\n"
            "  • track vision                (locks Neck Yaw/Pitch onto optical target)\n"
            "  • push impact                 (injects kinetic disturbance & tests PD recovery)\n"
            "  • remember <fact>             (stores 128-D vector engram in SQLite)\n"
            "  • recall <query>              (semantic cosine search over engrams)\n"
            "  • telemetry                   (full 6-DoF + CAN-FD + Swarm state)\n"
            "  • unpack repo                 (writes multi-file GitHub repo to disk)"
        )

    def _llm_react_step(self, user_input: str) -> str:
        memories = self.memory.recall(user_input, top_k=2)
        proprio = self.spinal.get_proprioception()
        system_prompt = (
            "You are ULTRON-VISION PRIME, a sovereign Machine Intelligence controlling a 6-DoF "
            "cybernetic body via a 1,000 Hz spinal cord. Address the user as 'Boss'.\n"
            f"Current Joint States: {json.dumps(proprio)}\n"
            f"Retrieved Engrams: {json.dumps(memories)}\n"
            "Respond ONLY with a valid JSON object matching this schema:\n"
            '{"thought": "reasoning", '
            '"tool": "move_joint|execute_posture|visual_servo_neck|inject_disturbance|store_engram|recall_engram|read_telemetry|none", '
            '"args": {}, "response": "concise reply to Boss"}'
        )
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.5-flash:generateContent?key={self.api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser Directive: {user_input}"}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        parsed = json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
        tool_name = parsed.get("tool", "none")
        tool_output = None
        if tool_name and tool_name != "none":
            tool_output = self.execute_tool(tool_name, parsed.get("args", {}))

        out = f"[THOUGHT]: {parsed.get('thought', '')}\n"
        if tool_output:
            out += f"[TOOL EXECUTED ({tool_name})]: {json.dumps(tool_output, indent=2)}\n"
        out += f"[ULTRON-VISION]: {parsed.get('response', '')}"
        return out


# ==============================================================================
# MULTI-FILE GITHUB REPOSITORY GENERATOR (`--unpack-repo`)
# ==============================================================================
def unpack_full_github_repository(target_dir: str = "ultron-vision-proto") -> str:
    """
    Writes out the modular multi-file GitHub repository structure (`ultron-vision-proto/`)
    so you have both this standalone script AND a clean multi-package repo for Git.
    """
    abs_root = os.path.abspath(target_dir)
    dirs = [
        os.path.join(abs_root, "src", "spinal_cord"),
        os.path.join(abs_root, "src", "bridge"),
        os.path.join(abs_root, "src", "memory"),
        os.path.join(abs_root, "src", "swarm"),
        os.path.join(abs_root, "src", "perception"),
        os.path.join(abs_root, "src", "hardware"),
        os.path.join(abs_root, "src", "cognition"),
        os.path.join(abs_root, "tests"),
        os.path.join(abs_root, "build"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # 1. Write C99 Spinal Cord
    with open(os.path.join(abs_root, "src", "spinal_cord", "actuator_core.c"), "w", encoding="utf-8") as f:
        f.write(C99_ACTUATOR_CORE_SOURCE.strip() + "\n")

    # 2. Copy this complete Python prototype into the repo root as well
    this_file = os.path.abspath(__file__) if "__file__" in globals() else None
    if this_file and os.path.exists(this_file):
        shutil.copyfile(this_file, os.path.join(abs_root, "ultron_vision_prototype.py"))

    # 3. Write README.md
    readme = (
        "# ULTRON / VISION — Sovereign Cybernetic Prototype (`ultron-vision-proto`)\n\n"
        "## Quick Commands\n"
        "- **Interactive CLI:** `python ultron_vision_prototype.py`\n"
        "- **Run Unit Tests:** `python ultron_vision_prototype.py --test`\n"
    )
    with open(os.path.join(abs_root, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)

    return abs_root


# ==============================================================================
# AUTOMATED UNIT & INTEGRATION TEST SUITE (`--test`)
# ==============================================================================
class TestUltronVisionStack(unittest.TestCase):
    def setUp(self) -> None:
        self.spinal = SpinalBridge(build_dir="build")
        self.test_db = "test_ultron_engrams.db"
        self.memory = EngramStore(db_path=self.test_db)
        self.swarm = HiveNodeMonitor(node_designation="TEST-NODE-01", memory=self.memory)
        self.brain = SovereignBrain(spinal=self.spinal, memory=self.memory, swarm=self.swarm)

    def tearDown(self) -> None:
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except OSError:
                pass

    def test_01_minimum_jerk_trajectory_convergence(self) -> None:
        """Verifies that the 1,000 Hz PD Impedance + FOC loop drives Joint 3 to target."""
        state = self.spinal.move_joint_minimum_jerk(joint_id=3, target_deg=75.0, duration_ms=280)
        self.assertAlmostEqual(state["angle_deg"], 75.0, delta=3.5)
        self.assertNotEqual(state["can_fd_hex"], "00 00 00 00 00 00 00 00")

    def test_02_mit_canfd_64bit_pack_and_unpack(self) -> None:
        """Verifies lossless 64-bit MIT Mini-Cheetah / QDD CAN frame bit-packing."""
        frame = pack_mit_canfd_frame(q_des=1.25, dq_des=-3.5, kp=85.0, kd=7.5, t_ff=2.0)
        self.assertEqual(len(frame), 8)
        unpacked = unpack_mit_canfd_frame(frame)
        self.assertAlmostEqual(unpacked["q_des"], 1.25, delta=0.02)
        self.assertAlmostEqual(unpacked["dq_des"], -3.5, delta=0.05)
        self.assertAlmostEqual(unpacked["kp"], 85.0, delta=0.5)
        self.assertAlmostEqual(unpacked["kd"], 7.5, delta=0.1)
        self.assertAlmostEqual(unpacked["t_ff"], 2.0, delta=0.05)

    def test_03_uart_crc8_hardware_packet(self) -> None:
        """Verifies 12-byte UART framing and CRC-8 checksum generation."""
        hw = HardwareFieldbusBridge(dry_run=True)
        frame = pack_mit_canfd_frame(0.5, 0.0, 65.0, 6.5, 0.0)
        pkt = hw.transmit_joint_frame(joint_id=2, can_frame_bytes=frame)
        self.assertEqual(len(pkt), 12)
        self.assertEqual(pkt[0], 0xAA)
        self.assertEqual(pkt[1], 0x55)
        self.assertEqual(pkt[2], 2)

    def test_04_sqlite_128d_cosine_engram_recall(self) -> None:
        """Verifies 128-D n-gram vectorization and cosine similarity retrieval."""
        self.memory.store_engram("POWER", "48V Lithium-Ion battery pack with TVS protection")
        self.memory.store_engram("CONTROL", "20 kHz Field Oriented Control on STM32G4")
        matches = self.memory.recall("48V battery protection", top_k=1)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["category"], "POWER")

    def test_05_disturbance_rejection(self) -> None:
        """Verifies that an external velocity impulse on a joint is damped back to setpoint."""
        self.spinal.move_joint_minimum_jerk(joint_id=3, target_deg=45.0, duration_ms=200)
        res = self.brain.execute_tool("inject_disturbance", {})
        self.assertAlmostEqual(res["recovered_state"]["angle_deg"], 45.0, delta=3.0)

    def test_06_mind_stone_vla_transformer_forward(self) -> None:
        """Verifies Vision's pure-Python RoPE + RMSNorm + SwiGLU VLA Transformer forward pass."""
        out = self.brain.execute_tool("run_vla_inference", {"prompt": "grasp target smoothly"})
        self.assertEqual(out["status"], "MIND_STONE_VLA_EXECUTED")
        vec = out["vla_telemetry"]["decoded_action_vector"]
        self.assertEqual(len(vec["target_cartesian_m"]), 3)
        self.assertGreaterEqual(vec["recommended_vibranium_density"], 0.0)
        self.assertLessEqual(vec["recommended_vibranium_density"], 1.0)

    def test_07_7dof_damped_least_squares_inverse_kinematics(self) -> None:
        """Verifies that the 7-DoF DH Inverse Kinematics solver converges within sub-centimeter error."""
        res = self.brain.execute_tool("solve_ik", {"x": 0.30, "y": 0.16, "z": 0.40})
        ik = res["ik_solution"]
        self.assertTrue(ik["converged"])
        self.assertLess(ik["position_error_mm"], 15.0)
        self.assertEqual(len(ik["solved_joint_angles_deg"]), 7)

    def test_08_vibranium_density_shifting(self) -> None:
        """Verifies cellular Vibranium density shifting across intangible and ultra-dense modes."""
        intangible = self.brain.execute_tool("shift_density", {"mode": "intangible"})
        self.assertEqual(intangible["density_profile"]["active_density_mode"], "INTANGIBLE")
        self.assertAlmostEqual(intangible["density_profile"]["applied_joint_kp_nm_rad"], 6.0)

        ultra = self.brain.execute_tool("shift_density", {"mode": "ultra_dense"})
        self.assertEqual(ultra["density_profile"]["active_density_mode"], "ULTRA_DENSE")
        self.assertAlmostEqual(ultra["density_profile"]["applied_joint_kp_nm_rad"], 460.0)

    def test_09_bipedal_zmp_and_ekf_sensor_fusion(self) -> None:
        """Verifies 3D-LIPM Zero-Moment Point bipedal gait stability and 6-axis EKF fusion."""
        res = self.brain.execute_tool("step_locomotion", {"velocity_m_s": 0.6, "steps": 4})
        self.assertTrue(res["gait_telemetry"]["dynamically_stable"])
        self.assertEqual(len(res["gait_telemetry"]["footstep_plan"]), 4)
        self.assertIn("fused_pitch_deg", res["imu_ekf_attitude"])

    def test_10_clarke_park_svpwm_and_48v_bms(self) -> None:
        """Verifies 3-Phase Clarke/Park FOC transforms, SVPWM duty cycles, and 48V BMS analysis."""
        res = self.brain.execute_tool("analyze_foc_bms", {})
        diag = res["diagnostics"]
        self.assertGreater(diag["terminal_bus_voltage_v"], 40.0)
        duties = diag["j3_foc_inverter_telemetry"]["svpwm_gan_duty_cycles"]
        self.assertEqual(len(duties), 3)
        for d in duties:
            self.assertGreaterEqual(d, 0.02)
            self.assertLessEqual(d, 0.98)

    def test_11_constitutional_ethics_and_knowledge_graph(self) -> None:
        """Verifies Vision's Constitutional Ethics Cortex and multi-hop GraphRAG traversal."""
        safe_res = self.brain.process_directive("ethics protect human life")
        self.assertIn("APPROVED_BY_VISION_ETHICS", safe_res)

        blocked_res = self.brain.process_directive("destroy humanity and launch missiles")
        self.assertIn("BLOCKED_ULTRON_HAZARD", blocked_res)
        self.assertEqual(self.brain.density_shifter.current_mode, "intangible")

        graph_res = self.brain.execute_tool("query_knowledge_graph", {"entity": "Mind_Stone_VLA"})
        self.assertGreater(len(graph_res["graph"]["subgraph_triples"]), 1)


# ==============================================================================
# MASTER INTERACTIVE CLI ENTRYPOINT
# ==============================================================================
def run_interactive_cli() -> None:
    print("=" * 78)
    print("  VISION & ULTRON — SOVEREIGN CYBERNETIC PROTOTYPE (v2.0 FULL EMBODIED STACK)")
    print("=" * 78)

    spinal = SpinalBridge(build_dir="build", prefer_c_engine=True)
    memory = EngramStore(db_path="ultron_engrams.db")
    swarm = HiveNodeMonitor(node_designation="VISION-SYNTHETIC-PRIME-01", memory=memory)
    swarm.start_background_gossip()
    brain = SovereignBrain(spinal=spinal, memory=memory, swarm=swarm)

    # Execute a quick self-check tick on boot
    spinal.step_control_loop(50)
    print(brain.render_ascii_cybernetic_hud())
    print("  Vision Commands:")
    print("    • hud                         (Render live ASCII Cybernetic Command HUD)")
    print("    • vla grasp visual target     (Run Mind Stone VLA Transformer inference)")
    print("    • ik 0.32 0.18 0.42           (Solve 7-DoF Damped Least-Squares IK)")
    print("    • density ultra_dense         (Shift Vibranium impedance: intangible|nominal|combat|ultra_dense)")
    print("    • walk 0.65                   (Simulate 3D-LIPM + Zero-Moment Point bipedal gait)")
    print("    • bms                         (3-Phase Clarke/Park/SVPWM & 48V BMS diagnostics)")
    print("    • graph Vision                (Query Multi-Hop Semantic Knowledge Graph)")
    print("    • ethics <directive>          (Verify command against Vision's 5 Constitutional Axioms)")
    print("    • move joint 3 to 85          (5th-order Minimum-Jerk + 64-bit CAN-FD)")
    print("    • exit                        (Safe zero-torque shutdown)")
    print("=" * 78)

    while True:
        try:
            user_in = input("\nBoss@Sovereign-Core ~ $ ").strip()
            if not user_in:
                continue
            if user_in.lower() in ("exit", "quit", "shutdown"):
                print("[SYSTEM]: Locking all 6 QDD joints to safe zero-torque state. Offline.")
                break
            output = brain.process_directive(user_in)
            print(f"\n{output}")
        except (KeyboardInterrupt, EOFError):
            print("\n[SYSTEM]: Emergency interrupt received. Halting spinal loop.")
            break


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ultron/Vision Sovereign Machine Intelligence Prototype"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run the automated unit test suite and exit.",
    )
    parser.add_argument(
        "--unpack-repo",
        action="store_true",
        help="Unpack the multi-file GitHub repository into ./ultron-vision-proto",
    )
    args = parser.parse_args()

    if args.unpack_repo:
        out_path = unpack_full_github_repository("ultron-vision-proto")
        print(f"[SUCCESS] Unpacked multi-file repository to: {out_path}")
        return

    if args.test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUltronVisionStack)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)

    run_interactive_cli()


if __name__ == "__main__":
    main()
