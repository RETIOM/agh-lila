import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent


def lila_run(example: str, stdin: str = "") -> subprocess.CompletedProcess:
    path = ROOT / "examples" / example
    return subprocess.run(
        [sys.executable, "-m", "lila.cli", str(path), "--run"],
        cwd=str(ROOT), input=stdin, capture_output=True, text=True, timeout=10,
    )


def test_bubble_sort_outputs_sorted():
    r = lila_run("bubble_sort_test.lila")
    assert r.returncode == 0, r.stderr
    nums = [int(x) for x in r.stdout.strip().splitlines()]
    assert nums == sorted(nums)
    assert nums == [1, 2, 3, 4, 5, 7, 8, 9]


def test_stalin_sort_keeps_nondecreasing_elements():
    r = lila_run("stalin_sort.lila")
    assert r.returncode == 0, r.stderr
    nums = [int(x) for x in r.stdout.strip().splitlines()]
    assert nums == [3, 4, 5, 9]


def test_slow_sort_outputs_sorted_array():
    r = lila_run("slow_sort.lila")
    assert r.returncode == 0, r.stderr
    nums = [int(x) for x in r.stdout.strip().splitlines()]
    assert nums == [1, 2, 3, 4, 5, 6]


def test_caesar_shifts_lowercase_letters():
    r = lila_run("caesar.lila")
    assert r.returncode == 0, r.stderr
    assert r.stdout == "khoor!\n"
