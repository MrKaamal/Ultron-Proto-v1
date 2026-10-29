# Ultron-Proto-v1

Ultron AI platform MVP focused on:
- Agent runtime loop with deterministic planning + tool execution
- Short-term + long-term memory (`sqlite` engram store)
- Model router (offline-first with Gemini fallback)
- Guardrails (tool policy + kill switch + audit log)
- Software-defined data-centre layer ("Ultron Fabric")

## Run
```bash
python main.py
```

## Example commands
- `status`
- `fabric status`
- `scale model_serving 4`
- `remember deploy autoscaling after telemetry burn-in`
- `recall autoscaling`
- `kill switch on`
- `kill switch off`
- `sum 2,4,6.5`
- `exit`
