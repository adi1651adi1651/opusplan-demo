"""Task persistence: the Task record, tasks.json load/save, and id assignment."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

TASKS_FILE = "tasks.json"


@dataclass
class Task:
    id: int
    text: str
    done: bool


def load_tasks(path: str) -> list[Task]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return [Task(id=item["id"], text=item["text"], done=item["done"]) for item in data]


def save_tasks(path: str, tasks: list[Task]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([asdict(t) for t in tasks], f, indent=2)
        f.write("\n")


def next_id(tasks: list[Task]) -> int:
    return max((t.id for t in tasks), default=0) + 1
