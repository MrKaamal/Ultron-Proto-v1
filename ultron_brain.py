# src/cognition/ultron_brain.py
import json
import os
import time
import urllib.request
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable, Deque, Dict, List, Tuple

from hive_telemetry import EngramStore
from spinal_bridge import HiveNodeMonitor


class Guardrails:
    def __init__(self) -> None:
        self.kill_switch = False
        self.allowed_tools = {"time_now", "sum_values", "fabric_status", "fabric_scale"}

    def validate(self, tool_name: str, args: Dict[str, Any]) -> Tuple[bool, str]:
        if self.kill_switch and tool_name != "fabric_status":
            return False, "Kill switch active. Only status reads are allowed."
        if tool_name not in self.allowed_tools:
            return False, f"Tool '{tool_name}' is not allowed by policy."
        if tool_name == "fabric_scale":
            replicas = int(args.get("replicas", 1))
            if replicas < 1 or replicas > 64:
                return False, "Replicas out of policy range (1-64)."
        return True, "ok"


class UltronFabric:
    def __init__(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.services = {
            "model_serving": {"replicas": 2, "health": "green", "last_event": now},
            "vector_db": {"replicas": 2, "health": "green", "last_event": now},
            "message_bus": {"replicas": 3, "health": "green", "last_event": now},
            "telemetry": {"replicas": 2, "health": "green", "last_event": now},
            "object_store": {"replicas": 2, "health": "green", "last_event": now},
        }

    def status(self) -> Dict[str, Any]:
        healthy = all(s["health"] == "green" for s in self.services.values())
        return {
            "fabric_state": "healthy" if healthy else "degraded",
            "services": self.services,
        }

    def scale(self, service: str, replicas: int) -> Dict[str, Any]:
        if service not in self.services:
            return {"error": f"Unknown service: {service}"}
        self.services[service]["replicas"] = replicas
        self.services[service]["last_event"] = datetime.now(timezone.utc).isoformat()
        return {"status": "scaled", "service": service, "replicas": replicas}


class SovereignBrain:
    def __init__(self, memory: EngramStore, swarm: HiveNodeMonitor):
        self.memory = memory
        self.swarm = swarm
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.guardrails = Guardrails()
        self.fabric = UltronFabric()
        self.short_term: Deque[Dict[str, Any]] = deque(maxlen=24)
        self.audit_log: Deque[Dict[str, Any]] = deque(maxlen=200)
        self.tool_registry: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "time_now": self._tool_time_now,
            "sum_values": self._tool_sum_values,
            "fabric_status": self._tool_fabric_status,
            "fabric_scale": self._tool_fabric_scale,
        }

        if not self.memory.recall("platform_directive", top_k=1):
            self.memory.store_engram(
                "PLATFORM_DIRECTIVE",
                "Ultron platform operates offline-first, enforces guardrails, and logs all tool actions."
            )

    def process_directive(self, user_input: str) -> str:
        text = user_input.strip()
        if not text:
            return "No input received."

        self._remember_turn("user", text)
        plan = self._plan(text)
        response = self._execute_plan(plan, text)
        self._remember_turn("assistant", response)
        return response

    def _plan(self, text: str) -> Dict[str, Any]:
        low = text.lower()
        if low in {"help", "/help"}:
            return {"intent": "help"}
        if low in {"status", "platform status", "telemetry"}:
            return {"intent": "status"}
        if low.startswith("remember "):
            return {"intent": "remember", "content": text[9:].strip()}
        if low.startswith("recall "):
            return {"intent": "recall", "query": text[7:].strip()}
        if low.startswith("kill switch on"):
            return {"intent": "kill_on"}
        if low.startswith("kill switch off"):
            return {"intent": "kill_off"}
        if low.startswith("scale "):
            parts = low.split()
            if len(parts) == 3 and parts[2].isdigit():
                return {"intent": "tool", "tool": "fabric_scale", "args": {"service": parts[1], "replicas": int(parts[2])}}
        if low.startswith("sum "):
            values = [v.strip() for v in text[4:].split(",") if v.strip()]
            return {"intent": "tool", "tool": "sum_values", "args": {"values": values}}
        if "time" in low:
            return {"intent": "tool", "tool": "time_now", "args": {}}
        if any(key in low for key in ("fabric", "cluster", "datacenter", "data centre")):
            return {"intent": "tool", "tool": "fabric_status", "args": {}}
        return {"intent": "model_route", "text": text}

    def _execute_plan(self, plan: Dict[str, Any], original_text: str) -> str:
        intent = plan["intent"]

        if intent == "help":
            return (
                "ULTRON AI Platform Commands:\n"
                "  - status | telemetry\n"
                "  - remember <fact>\n"
                "  - recall <query>\n"
                "  - scale <service> <replicas>\n"
                "  - sum <n1,n2,...>\n"
                "  - kill switch on|off\n"
                "  - fabric status"
            )

        if intent == "status":
            return json.dumps(self._platform_status(), indent=2)

        if intent == "remember":
            item = plan.get("content", "").strip()
            if not item:
                return "Nothing to remember."
            row_id = self.memory.store_engram("USER_MEMORY", item)
            return f"Stored memory entry #{row_id}."

        if intent == "recall":
            query = plan.get("query", "").strip()
            rows = self.memory.recall(query, top_k=5)
            return json.dumps({"query": query, "matches": rows}, indent=2)

        if intent == "kill_on":
            self.guardrails.kill_switch = True
            return "Kill switch enabled."

        if intent == "kill_off":
            self.guardrails.kill_switch = False
            return "Kill switch disabled."

        if intent == "tool":
            result = self._run_tool(plan["tool"], plan.get("args", {}))
            return json.dumps(result, indent=2)

        model_response = self._route_model(original_text)
        return model_response

    def _route_model(self, text: str) -> str:
        if not self.api_key:
            return self._offline_answer(text)
        try:
            return self._gemini_answer(text)
        except Exception as exc:
            return f"[Model fallback: {exc}] {self._offline_answer(text)}"

    def _offline_answer(self, text: str) -> str:
        related = self.memory.recall(text, top_k=2)
        return (
            "Offline reasoning mode active. "
            "I can run platform commands, memory operations, and fabric management.\n"
            f"Closest memories: {json.dumps(related)}"
        )

    def _gemini_answer(self, text: str) -> str:
        prompt = (
            "You are Ultron Platform Core. Provide concise operational guidance "
            "for an AI platform running with strict guardrails and audit logging.\n"
            f"Current status: {json.dumps(self._platform_status())}\n"
            f"User input: {text}"
        )
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _run_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        allowed, reason = self.guardrails.validate(tool_name, args)
        if not allowed:
            event = {"time": time.time(), "tool": tool_name, "args": args, "status": "blocked", "reason": reason}
            self.audit_log.append(event)
            return {"status": "blocked", "reason": reason}

        fn = self.tool_registry.get(tool_name)
        if not fn:
            return {"status": "error", "reason": f"Tool not registered: {tool_name}"}

        out = fn(args)
        event = {"time": time.time(), "tool": tool_name, "args": args, "status": "ok", "result": out}
        self.audit_log.append(event)
        return {"status": "ok", "result": out}

    def _tool_time_now(self, _: Dict[str, Any]) -> Dict[str, Any]:
        return {"utc": datetime.now(timezone.utc).isoformat()}

    def _tool_sum_values(self, args: Dict[str, Any]) -> Dict[str, Any]:
        numbers = [float(v) for v in args.get("values", [])]
        return {"count": len(numbers), "sum": sum(numbers)}

    def _tool_fabric_status(self, _: Dict[str, Any]) -> Dict[str, Any]:
        return self._platform_status()

    def _tool_fabric_scale(self, args: Dict[str, Any]) -> Dict[str, Any]:
        service = str(args.get("service", ""))
        replicas = int(args.get("replicas", 1))
        return self.fabric.scale(service, replicas)

    def _platform_status(self) -> Dict[str, Any]:
        telemetry = self.swarm.get_node_telemetry(spinal_ticks=len(self.short_term))
        return {
            "node": telemetry,
            "fabric": self.fabric.status(),
            "guardrails": {"kill_switch": self.guardrails.kill_switch, "allowed_tools": sorted(self.guardrails.allowed_tools)},
            "memory": {"short_term_items": len(self.short_term), "audit_events": len(self.audit_log)},
        }

    def _remember_turn(self, role: str, content: str) -> None:
        self.short_term.append({"role": role, "content": content, "ts": time.time()})
