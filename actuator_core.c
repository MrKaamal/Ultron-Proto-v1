// src/spinal_cord/actuator_core.c
#include <stdio.h>
#include <math.h>

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

#define NUM_JOINTS 6
#define DT 0.001f          // 1,000 Hz deterministic step (1 ms)
#define MAX_CURRENT_A 35.0f // Peak GaN Inverter Phase Current (Amps)
#define KT_TORQUE 1.85f     // Quasi-Direct Drive Torque Constant (Nm/A)

typedef struct {
    int joint_id;
    char name[24];
    float q_actual;        // Current joint angle (rad)
    float dq_actual;       // Current joint velocity (rad/s)
    float q_desired;       // Target joint angle (rad)
    float dq_desired;      // Target joint velocity (rad/s)
    float kp;              // Virtual spring stiffness
    float kd;              // Virtual damper gain
    float iq_current;      // FOC quadrature current (Amps)
    float torque_nm;       // Applied mechanical torque (Nm)
    float temperature_c;   // Winding temperature (Celsius)
} JointState;

typedef struct {
    JointState joints[NUM_JOINTS];
    unsigned long long tick_count;
    int emergency_stop;
} CyberneticChassis;

// Initialize the 6-DoF Vision/Ultron Upper-Body Chassis
EXPORT void init_chassis(CyberneticChassis* chassis) {
    const char* names[NUM_JOINTS] = {
        "Neck_Yaw", "Neck_Pitch", "R_Shoulder_Pitch",
        "R_Elbow_Flex", "L_Shoulder_Pitch", "L_Elbow_Flex"
    };
    chassis->tick_count = 0;
    chassis->emergency_stop = 0;

    for (int i = 0; i < NUM_JOINTS; i++) {
        chassis->joints[i].joint_id = i;
        snprintf(chassis->joints[i].name, 24, "%s", names[i]);
        chassis->joints[i].q_actual = 0.0f;
        chassis->joints[i].dq_actual = 0.0f;
        chassis->joints[i].q_desired = 0.0f;
        chassis->joints[i].dq_desired = 0.0f;
        chassis->joints[i].kp = 65.0f;
        chassis->joints[i].kd = 6.5f;
        chassis->joints[i].iq_current = 0.0f;
        chassis->joints[i].torque_nm = 0.0f;
        chassis->joints[i].temperature_c = 32.0f;
    }
}

// Set target posture and impedance gains for a specific joint
EXPORT void set_joint_command(CyberneticChassis* chassis, int joint_id, float q_des, float kp, float kd) {
    if (joint_id < 0 || joint_id >= NUM_JOINTS) return;
    chassis->joints[joint_id].q_desired = q_des;
    chassis->joints[joint_id].kp = kp;
    chassis->joints[joint_id].kd = kd;
}

// Execute N ticks of the 1,000 Hz Real-Time Control & Physics Loop
EXPORT void step_control_loop(CyberneticChassis* chassis, int steps) {
    if (chassis->emergency_stop) return;

    const float link_inertia = 0.12f; // kg*m^2
    const float friction = 0.15f;

    for (int s = 0; s < steps; s++) {
        for (int i = 0; i < NUM_JOINTS; i++) {
            JointState* j = &chassis->joints[i];

            // 1. PD Impedance Law: tau = Kp*(q_d - q) + Kd*(dq_d - dq)
            float pos_error = j->q_desired - j->q_actual;
            float vel_error = j->dq_desired - j->dq_actual;
            float commanded_torque = (j->kp * pos_error) + (j->kd * vel_error);

            // 2. FOC Quadrature Current Calculation (I_q = tau / K_t) with Hardware Clamping
            float iq = commanded_torque / KT_TORQUE;
            if (iq > MAX_CURRENT_A) iq = MAX_CURRENT_A;
            if (iq < -MAX_CURRENT_A) iq = -MAX_CURRENT_A;
            j->iq_current = iq;

            // 3. Actual Mechanical Torque & Rigid-Body Dynamics Integration
            j->torque_nm = iq * KT_TORQUE;
            float angular_accel = (j->torque_nm - (friction * j->dq_actual)) / link_inertia;
            j->dq_actual += angular_accel * DT;
            j->q_actual += j->dq_actual * DT;

            // 4. Joule Heating Thermal Model (I^2 * R dissipation vs ambient cooling)
            float heat_rise = (iq * iq * 0.00008f) - ((j->temperature_c - 30.0f) * 0.0005f);
            j->temperature_c += heat_rise;

            // Fail-Stop Thermal Protection
            if (j->temperature_c > 85.0f) {
                chassis->emergency_stop = 1;
            }
        }
        chassis->tick_count++;
    }
}
