# Ultron-Proto-v1
A small, safe, offline-first assistant prototype inspired by a personal command center. It uses only Python's standard library and stores memory locally in .ultron_memory.json.

Run
python main.py --offline
Then try:

/help
/status
/remember project: build a voice interface
/recall
/calc (12 * 4) + 3
/quit
Natural-language shortcuts such as what time is it, show status, and remember that ... are supported. The prototype never executes arbitrary shell commands.

Test
python -m unittest discover -s tests -v
Layout
main.py - command-line entry point
ultron/assistant.py - routing and assistant behavior
ultron/memory.py - local JSON memory store
tests/ - standard-library unit tests
