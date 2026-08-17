#!/usr/bin/env python3
import sys

from tasks import TASKS_FILE, Task, load_tasks, next_id, save_tasks


def print_usage() -> None:
    print("Usage:")
    print("  main.py add <text...>          Add a new task")
    print("  main.py list                   List all tasks")
    print("  main.py done <id>              Mark task as done")
    print("  main.py update <id> <text...>  Update a task's text")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print_usage()
        return 1

    command = argv[1]
    tasks = load_tasks(TASKS_FILE)

    if command == "add":
        if len(argv) < 3:
            print("Error: please provide task text.")
            return 1
        text = " ".join(argv[2:])
        task = Task(id=next_id(tasks), text=text, done=False)
        tasks.append(task)
        save_tasks(TASKS_FILE, tasks)
        print(f"Added task {task.id}: {task.text}")
    elif command == "list":
        if not tasks:
            print("No tasks yet.")
        else:
            for t in tasks:
                mark = "x" if t.done else " "
                print(f"[{mark}] {t.id}: {t.text}")
    elif command == "done":
        if len(argv) < 3:
            print("Error: please provide a task id.")
            return 1
        task_id = int(argv[2])
        found = False
        for t in tasks:
            if t.id == task_id:
                t.done = True
                found = True
                break
        if found:
            save_tasks(TASKS_FILE, tasks)
            print(f"Marked task {task_id} as done.")
        else:
            print(f"Task {task_id} not found.")
    elif command == "update":
        if len(argv) < 4:
            print("Error: please provide a task id and new text.")
            return 1
        task_id = int(argv[2])
        text = " ".join(argv[3:])
        found = False
        for t in tasks:
            if t.id == task_id:
                t.text = text
                found = True
                break
        if found:
            save_tasks(TASKS_FILE, tasks)
            print(f"Updated task {task_id}: {text}")
        else:
            print(f"Task {task_id} not found.")
    else:
        print_usage()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
