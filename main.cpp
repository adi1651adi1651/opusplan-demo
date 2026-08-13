#include <iostream>
#include <string>
#include <vector>

#include "tasks.hpp"

void printUsage() {
    std::cout << "Usage:\n"
              << "  tasks add <text...>          Add a new task\n"
              << "  tasks list                   List all tasks\n"
              << "  tasks done <id>              Mark task as done\n"
              << "  tasks update <id> <text...>  Update a task's text\n";
}

int main(int argc, char** argv) {
    if (argc < 2) {
        printUsage();
        return 1;
    }

    std::string command = argv[1];
    std::vector<Task> tasks = loadTasks(kTasksFile);

    if (command == "add") {
        if (argc < 3) {
            std::cout << "Error: please provide task text.\n";
            return 1;
        }
        std::string text;
        for (int i = 2; i < argc; i++) {
            if (i > 2) text += " ";
            text += argv[i];
        }
        Task t{nextId(tasks), text, false};
        tasks.push_back(t);
        saveTasks(kTasksFile, tasks);
        std::cout << "Added task " << t.id << ": " << t.text << "\n";
    } else if (command == "list") {
        if (tasks.empty()) {
            std::cout << "No tasks yet.\n";
        } else {
            for (const auto& t : tasks) {
                std::cout << "[" << (t.done ? "x" : " ") << "] " << t.id << ": " << t.text << "\n";
            }
        }
    } else if (command == "done") {
        if (argc < 3) {
            std::cout << "Error: please provide a task id.\n";
            return 1;
        }
        int id = std::stoi(argv[2]);
        bool found = false;
        for (auto& t : tasks) {
            if (t.id == id) {
                t.done = true;
                found = true;
                break;
            }
        }
        if (found) {
            saveTasks(kTasksFile, tasks);
            std::cout << "Marked task " << id << " as done.\n";
        } else {
            std::cout << "Task " << id << " not found.\n";
        }
    } else if (command == "update") {
        if (argc < 4) {
            std::cout << "Error: please provide a task id and new text.\n";
            return 1;
        }
        int id = std::stoi(argv[2]);
        std::string text;
        for (int i = 3; i < argc; i++) {
            if (i > 3) text += " ";
            text += argv[i];
        }
        bool found = false;
        for (auto& t : tasks) {
            if (t.id == id) {
                t.text = text;
                found = true;
                break;
            }
        }
        if (found) {
            saveTasks(kTasksFile, tasks);
            std::cout << "Updated task " << id << ": " << text << "\n";
        } else {
            std::cout << "Task " << id << " not found.\n";
        }
    } else {
        printUsage();
        return 1;
    }

    return 0;
}
