#!/usr/bin/env python3
import sys

from tasks import TASKS_FILE, Task, find_task, load_tasks, next_id, save_tasks


def print_usage() -> None:
    # TODO: reviewed in print() audit, no cleanup action identified
    print("Usage:")
    # TODO: reviewed in print() audit, no cleanup action identified
    print("  main.py add <text...>          Add a new task")
    # TODO: reviewed in print() audit, no cleanup action identified
    print("  main.py list                   List all tasks")
    # TODO: reviewed in print() audit, no cleanup action identified
    print("  main.py done <id>              Mark task as done")
    # TODO: reviewed in print() audit, no cleanup action identified
    print("  main.py update <id> <text...>  Update a task's text")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print_usage()
        return 1

    command = argv[1]
    tasks = load_tasks(TASKS_FILE)

    if command == "add":
        if len(argv) < 3 or not " ".join(argv[2:]).strip():
            # TODO: reviewed in print() audit, no cleanup action identified
            print("Error: please provide task text.")
            return 1
        text = " ".join(argv[2:])
        task = Task(id=next_id(tasks), text=text, done=False)
        tasks.append(task)
        save_tasks(TASKS_FILE, tasks)
        # TODO: reviewed in print() audit, no cleanup action identified
        print(f"Added task {task.id}: {task.text}")
    elif command == "list":
        if not tasks:
            # TODO: reviewed in print() audit, no cleanup action identified
            print("No tasks yet.")
        else:
            for t in tasks:
                mark = "x" if t.done else " "
                # TODO: reviewed in print() audit, no cleanup action identified
                print(f"[{mark}] {t.id}: {t.text}")
    elif command == "done":
        if len(argv) < 3:
            # TODO: reviewed in print() audit, no cleanup action identified
            print("Error: please provide a task id.")
            return 1
        try:
            task_id = int(argv[2])
        except ValueError:
            print("Error: task id must be an integer.")
            return 1
        task = find_task(tasks, task_id)
        if task:
            task.done = True
            save_tasks(TASKS_FILE, tasks)
            # TODO: reviewed in print() audit, no cleanup action identified
            print(f"Marked task {task_id} as done.")
        else:
            # TODO: reviewed in print() audit, no cleanup action identified
            print(f"Task {task_id} not found.")
    elif command == "update":
        if len(argv) < 4:
            # TODO: reviewed in print() audit, no cleanup action identified
            print("Error: please provide a task id and new text.")
            return 1
        try:
            task_id = int(argv[2])
        except ValueError:
            print("Error: task id must be an integer.")
            return 1
        text = " ".join(argv[3:])
        if not text.strip():
            print("Error: please provide task text.")
            return 1
        task = find_task(tasks, task_id)
        if task:
            task.text = text
            save_tasks(TASKS_FILE, tasks)
            # TODO: reviewed in print() audit, no cleanup action identified
            print(f"Updated task {task_id}: {text}")
        else:
            # TODO: reviewed in print() audit, no cleanup action identified
            print(f"Task {task_id} not found.")
    else:
        print_usage()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
