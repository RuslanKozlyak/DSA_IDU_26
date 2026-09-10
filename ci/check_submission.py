"""Проверка одного student-ноутбука в Pull Request."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


LABS = {
    "lab1_complexity/lab1_student.ipynb": "SEARCHES =",
    "lab2_sorting/lab2_student.ipynb": "INT_SORTS =",
    "lab3_structures/lab3_student.ipynb": "LISTS =",
    "lab4_strings/lab4_student.ipynb": "SEARCHES =",
}
FORBIDDEN_NAMES = {
    "reference.py",
    "lab1_reference.ipynb",
    "lab2_reference.ipynb",
    "lab3_reference.ipynb",
    "lab4_reference.ipynb",
}
FORBIDDEN_PARTS = {"_tools", "_to_delete", "graphify-out", ".ipynb_checkpoints"}


def fail(message: str) -> None:
    print(f"ОШИБКА: {message}", file=sys.stderr)
    raise SystemExit(1)


def changed_files(base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def audit_tree(root: Path) -> None:
    leaked = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if path.name in FORBIDDEN_NAMES or FORBIDDEN_PARTS.intersection(relative.parts):
            leaked.append(relative.as_posix())
    if leaked:
        fail("в публичном репозитории найдены закрытые файлы: " + ", ".join(leaked))


def execute(notebook: Path, boundary: str) -> None:
    document = json.loads(notebook.read_text(encoding="utf-8"))
    namespace = {"__name__": "__main__"}
    found_boundary = False
    previous_directory = Path.cwd()
    os.chdir(notebook.parent)
    try:
        for index, cell in enumerate(document.get("cells", [])):
            if cell.get("cell_type") != "code":
                continue
            source = "".join(cell.get("source", []))
            if boundary in source:
                found_boundary = True
                break
            if source.strip():
                exec(compile(source, f"{notebook.name}:cell-{index}", "exec"), namespace)
    finally:
        os.chdir(previous_directory)
    if not found_boundary:
        fail(f"в {notebook} не найдена граница экспериментальной части {boundary!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()

    root = Path.cwd()
    audit_tree(root)
    changed = changed_files(args.base, args.head)
    print("Изменённые файлы:")
    for path in changed:
        print(f"  {path}")

    notebooks = [path for path in changed if path in LABS]
    if len(notebooks) != 1:
        fail("PR должен изменять ровно один student-ноутбук")
    if changed != notebooks:
        fail("в PR разрешено изменять только notebook текущей лабораторной работы")

    relative = notebooks[0]
    notebook = root / relative
    if not notebook.is_file():
        fail(f"не найден {relative}")

    print(f"\nВыполняю короткие проверки: {relative}")
    try:
        execute(notebook, LABS[relative])
    except Exception as error:
        print(f"\nПроверка ноутбука завершилась ошибкой: {error}", file=sys.stderr)
        raise
    print("Короткие проверки пройдены.")


if __name__ == "__main__":
    main()
