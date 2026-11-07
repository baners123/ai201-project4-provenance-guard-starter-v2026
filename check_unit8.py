#!/usr/bin/env python3
from pathlib import Path

required = [
    "criteria.md",
    "README.md",
    "scenarios.py",
    "run_eval.py",
    "logs/audit.jsonl",
    "results",
]

print("Unit 8 submission check")
print("-" * 50)

for name in required:
    p = Path(name)
    print(f"[{'PASS' if p.exists() else 'MISSING'}] {name}")

my_writing = Path("data/my_writing.txt")
if my_writing.exists():
    pieces = [
        p.strip()
        for p in my_writing.read_text(encoding="utf-8").split("\n---\n")
        if p.strip()
    ]
    placeholders = sum("PASTE YOUR" in p for p in pieces)
    print(f"\nMy-writing pieces: {len(pieces)}")
    print(f"Placeholder pieces: {placeholders}")
else:
    print("\n[MISSING] data/my_writing.txt")

results = Path("results")
if results.exists():
    names = sorted(p.name for p in results.iterdir() if p.is_file())
    print("\nResult files:")
    for name in names:
        print(" -", name)
