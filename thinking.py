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

