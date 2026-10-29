# main.py
from hive_telemetry import EngramStore
from spinal_bridge import HiveNodeMonitor
from ultron_brain import SovereignBrain


def main():
    print("=" * 68)
    print("  ULTRON AI PLATFORM CORE (v1.0-MVP)")
    print("  [Agent Runtime] [Memory Plane] [Model Router] [Ultron Fabric]")
    print("  [Guardrails] [Audit Log] [Offline-First Operations]")
    print("=" * 68)

    memory = EngramStore(db_path="ultron_engrams.db")
    swarm = HiveNodeMonitor(node_designation="ULTRON-PLATFORM-PRIME-01")
    brain = SovereignBrain(memory=memory, swarm=swarm)

    telemetry = swarm.get_node_telemetry(0)
    print(f"Node ID      : {telemetry['node_id']} ({telemetry['os_kernel']})")
    print(f"Swarm Hash   : {telemetry['swarm_sync_hash']}")
    print("LLM API Mode : " + ("ENABLED (Gemini)" if brain.api_key else "OFFLINE-FIRST MODE"))
    print("-" * 68)
    print("Try commands: 'status', 'fabric status', 'scale model_serving 4',")
    print("              'remember <fact>', 'recall <query>', 'kill switch on', or 'exit'")
    print("-" * 68)

    while True:
        try:
            user_in = input("\nBoss@Sovereign-Core ~ $ ").strip()
            if not user_in:
                continue
            if user_in.lower() in ("exit", "quit", "shutdown"):
                print("[SYSTEM]: Persisting state and shutting down platform core.")
                break
            output = brain.process_directive(user_in)
            print(f"\n{output}")
        except KeyboardInterrupt:
            print("\n[SYSTEM]: Emergency interrupt received. Halting.")
            break


if __name__ == "__main__":
    main()
