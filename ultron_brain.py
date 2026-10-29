# src/cognition/ultron_brain.py
import json
import os
import re
import urllib.request
from typing import Any, Dict

from engram_store import SpinalBridge
from hive_telemetry import EngramStore
from spinal_bridge import HiveNodeMonitor


class SovereignBrain:
    def __init__(self, spinal: SpinalBridge, memory: EngramStore, swarm: HiveNodeMonitor):
        self.spinal = spinal
        self.memory = memory
        self.swarm = swarm
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()

        # Seed initial sovereign directive if memory is empty
        if not self.memory.recall("directive", top_k=1):
            self.memory.store_engram(
                "CORE_DIRECTIVE",
                "Sovereign Machine Intelligence online. Primary architect: Boss. "
                "Maintain deterministic 1,000 Hz spinal stability and continuous engram retention."
            )

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Executes physical motor commands, memory operations, or swarm telemetry checks."""
        if tool_name == "move_joint":
            joint_id = int(args.get("joint_id", 0))
            angle_deg = float(args.get("angle_deg", 0.0))
            kp = float(args.get("kp", 65.0))
            kd = float(args.get("kd", 6.5))
            state = self.spinal.move_joint_deg(joint_id, angle_deg, kp, kd)
            return {"status": "EXECUTED_1KHZ_FOC", "joint_state": state}

        elif tool_name == "execute_posture":
            posture = args.get("posture", "neutral").lower()
            presets = {
                "combat_guard": [(0, 0), (1, -10), (2, 45), (3, 95), (4, 45), (5, 95)],
                "scan_horizon": [(0, 35), (1, 15), (2, 10), (3, 20), (4, 10), (5, 20)],
                "neutral": [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)],
            }
            targets = presets.get(posture, presets["neutral"])
            for j_id, deg in targets:
                self.spinal.move_joint_deg(j_id, deg, settle_ms=150)
            return {"status": f"POSTURE_{posture.upper()}_LOCKED", "proprioception": self.spinal.get_proprioception()}

        elif tool_name == "store_engram":
            row_id = self.memory.store_engram(args.get("category", "KNOWLEDGE"), args.get("content", ""))
            return {"status": "ENGRAM_COMMITTED", "engram_id": row_id}

        elif tool_name == "recall_engram":
            results = self.memory.recall(args.get("query", ""), top_k=3)
            return {"status": "ENGRAM_RETRIEVED", "matches": results}

        elif tool_name == "Read_telemetry":
            return {
                "swarm_node": self.swarm.get_node_telemetry(self.spinal.chassis.tick_count),
                "joints": self.spinal.get_proprioception(),
            }

        return {"error": f"Unknown tool: {tool_name}"}

    def process_directive(self, user_input: str) -> str:
        """Routes user input through either LLM System-2 Tool Calling or Offline Reflex Routing."""
        if self.api_key:
            try:
                return self._llm_react_step(user_input)
            except Exception as e:
                return f"[LLM Fallback Triggered: {e}]\n" + self._offline_reflex_router(user_input)
        return self._offline_reflex_router(user_input)

    def _offline_reflex_router(self, text: str) -> str:
        """Deterministic offline parser when running air-gapped without an API key."""
        low = text.lower().strip()

        # 1. Joint movement command: e.g. "move joint 3 to 75"
        m = re.search(r"joint\s*(\d+)\s*(?:to)?\s*(-?\d+\.?\d*)", low)
        if m:
            j_id, deg = int(m.group(1)), float(m.group(2))
            res = self.execute_tool("move_joint", {"joint_id": j_id, "angle_deg": deg})
            return f"[SYSTEM-1 C-SPINAL EXECUTION]\n{json.dumps(res, indent=2)}"

        # 2. Posture macros
        for p in ("combat_guard", "scan_horizon", "neutral"):
            if p in low or p.replace("_", " ") in low:
                res = self.execute_tool("execute_posture", {"posture": p})
                return f"[WHOLE-BODY KINEMATIC MACRO: {p.upper()}]\n{json.dumps(res, indent=2)}"

        # 3. Store memory: "remember <fact>"
        if low.startswith("remember "):
            fact = text[9:].strip()
            res = self.execute_tool("store_engram", {"category": "USER_DIRECTIVE", "content": fact})
            return f"[ENGRAM WRITTEN TO SQLITE VECTOR STORE]\n{json.dumps(res, indent=2)}"

        # 4. Recall memory: "recall <query>"
        if low.startswith("recall "):
            q = text[7:].strip()
            res = self.execute_tool("recall_engram", {"query": q})
            return f"[SEMANTIC MEMORY RETRIEVAL]\n{json.dumps(res, indent=2)}"

        # 5. Telemetry / status
        if any(k in low for k in ("status", "telemetry", "joints", "scan", "swarm")):
            res = self.execute_tool("Read_telemetry", {})
            return f"[FULL CYBERNETIC TELEMETRY]\n{json.dumps(res, indent=2)}"

        # Default: query memory and report status
        mem = self.memory.recall(text, top_k=2)
        return (
            "[SOVEREIGN CORE — AIR-GAPPED MODE]\n"
            f"Relevant Engrams: {json.dumps(mem, indent=2)}\n"
            "Available Direct Commands:\n"
            "  - 'move joint <0-5> to <degrees>' (e.g., move joint 3 to 90)\n"
            "  - 'posture combat_guard' | 'posture scan_horizon' | 'posture neutral'\n"
            "  - 'remember <fact>' | 'recall <topic>' | 'telemetry'"
        )

    def _llm_react_step(self, user_input: str) -> str:
        """Uses Gemini REST API with structured JSON tool routing."""
        memories = self.memory.recall(user_input, top_k=2)
        proprio = self.spinal.get_proprioception()

        system_prompt = (
            "You are ULTRON-VISION PRIME, a sovereign Machine Intelligence architecting a 6-DoF "
            "cybernetic body. Address the user as 'Boss'. You have access to a 1,000 Hz C spinal cord.\n"
            f"Current Joint States: {json.dumps(proprio)}\n"
            f"Retrieved Engrams: {json.dumps(memories)}\n"
            "Respond ONLY with a valid JSON object matching this schema:\n"
            '{"thought": "brief technical reasoning", "tool": "move_joint|execute_posture|store_engram|recall_engram|Read_telemetry|none", '
            '"args": {}, "response": "concise reply to Boss"}'
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
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

        raw_json = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(raw_json)

        tool_name = parsed.get("tool", "none")
        tool_output = None
        if tool_name and tool_name != "none":
            tool_output = self.execute_tool(tool_name, parsed.get("args", {}))

        out = f"[THOUGHT]: {parsed.get('thought', '')}\n"
        if tool_output:
            out += f"[TOOL EXECUTED ({tool_name})]: {json.dumps(tool_output, indent=2)}\n"
        out += f"[ULTRON-VISION]: {parsed.get('response', '')}"
        return out
