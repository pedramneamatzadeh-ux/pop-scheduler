#!/usr/bin/env python3
"""
Run all tests for Pop Scheduler Bot.
"""
import sys
import os
import subprocess

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)

# Use venv python if available
venv_python = os.path.join(PROJECT_ROOT, ".venv", "bin", "python")
python = venv_python if os.path.exists(venv_python) else sys.executable

test_files = sorted([
    f for f in os.listdir(TESTS_DIR)
    if f.startswith("test_") and f.endswith(".py")
])

total_passed = 0
total_failed = 0
failed_files = []

for tf in test_files:
    path = os.path.join(TESTS_DIR, tf)
    print(f"\n{'='*50}")
    print(f"📄 Running: {tf}")
    print(f"{'='*50}")

    result = subprocess.run([python, path], capture_output=False)

    if result.returncode == 0:
        total_passed += 1
    else:
        total_failed += 1
        failed_files.append(tf)

print(f"\n{'='*50}")
print(f"📊 SUMMARY")
print(f"{'='*50}")
print(f"  Test files passed: {total_passed}")
print(f"  Test files failed: {total_failed}")
if failed_files:
    print(f"  Failed files: {', '.join(failed_files)}")
print(f"{'='*50}")

sys.exit(1 if total_failed else 0)
