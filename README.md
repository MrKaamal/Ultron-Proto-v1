# Ultron-Proto-v1

Offline Ultron-inspired prototype with:
- Python command core (`main.py`, `ultron_brain.py`)
- C motor/spinal simulation (`actuator_core.c`)
- Local SQLite engram memory

## Run
```bash
python main.py
```

On first boot, the app auto-compiles `actuator_core.c` into `build/actuator_core.so` (or `.dll` on Windows) using `gcc`.

## Example commands
- `telemetry`
- `move joint 3 to 85`
- `posture combat_guard`
- `remember Vibranium chassis nominal`
- `recall chassis`
- `exit`
