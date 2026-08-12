#include <algorithm>
#include <cctype>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

struct Task {
    int id;
    std::string text;
    bool done;
};

const std::string kTasksFile = "tasks.json";

std::string escapeJson(const std::string& s) {
    std::string out;
    for (char c : s) {
        switch (c) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\t': out += "\\t"; break;
            default: out += c;
        }
    }
    return out;
}

// Minimal parser tailored to the array-of-{id,text,done} format this program writes.
class JsonParser {
public:
    explicit JsonParser(const std::string& s) : s_(s), pos_(0) {}

    std::vector<Task> parseTasks() {
        std::vector<Task> tasks;
        skipWs();
        if (pos_ >= s_.size() || s_[pos_] != '[') return tasks;
        pos_++;
        skipWs();
        if (pos_ < s_.size() && s_[pos_] == ']') { pos_++; return tasks; }
        while (true) {
            skipWs();
            tasks.push_back(parseTask());
            skipWs();
            if (pos_ < s_.size() && s_[pos_] == ',') { pos_++; continue; }
            break;
        }
        skipWs();
        if (pos_ < s_.size() && s_[pos_] == ']') pos_++;
        return tasks;
    }

private:
    const std::string& s_;
    size_t pos_;

    void skipWs() {
        while (pos_ < s_.size() && std::isspace(static_cast<unsigned char>(s_[pos_]))) pos_++;
    }

    void expect(char c) {
        if (pos_ < s_.size() && s_[pos_] == c) pos_++;
    }

    Task parseTask() {
        Task t{0, "", false};
        expect('{');
        skipWs();
        if (pos_ < s_.size() && s_[pos_] == '}') { pos_++; return t; }
        while (true) {
            skipWs();
            std::string key = parseString();
            skipWs();
            expect(':');
            skipWs();
            if (key == "id") t.id = parseInt();
            else if (key == "text") t.text = parseString();
            else if (key == "done") t.done = parseBool();
            else skipValue();
            skipWs();
            if (pos_ < s_.size() && s_[pos_] == ',') { pos_++; continue; }
            break;
        }
        skipWs();
        expect('}');
        return t;
    }

    std::string parseString() {
        std::string out;
        if (pos_ >= s_.size() || s_[pos_] != '"') return out;
        pos_++;
        while (pos_ < s_.size() && s_[pos_] != '"') {
            char c = s_[pos_];
            if (c == '\\' && pos_ + 1 < s_.size()) {
                pos_++;
                char e = s_[pos_];
                switch (e) {
                    case 'n': out += '\n'; break;
                    case 't': out += '\t'; break;
                    case '"': out += '"'; break;
                    case '\\': out += '\\'; break;
                    default: out += e;
                }
            } else {
                out += c;
            }
            pos_++;
        }
        if (pos_ < s_.size()) pos_++;
        return out;
    }

    int parseInt() {
        size_t start = pos_;
        if (pos_ < s_.size() && (s_[pos_] == '-' || s_[pos_] == '+')) pos_++;
        while (pos_ < s_.size() && std::isdigit(static_cast<unsigned char>(s_[pos_]))) pos_++;
        if (start == pos_) return 0;
        return std::stoi(s_.substr(start, pos_ - start));
    }

    bool parseBool() {
        if (s_.compare(pos_, 4, "true") == 0) { pos_ += 4; return true; }
        if (s_.compare(pos_, 5, "false") == 0) { pos_ += 5; return false; }
        return false;
    }

    void skipValue() {
        skipWs();
        if (pos_ >= s_.size()) return;
        char c = s_[pos_];
        if (c == '"') {
            parseString();
        } else if (c == '{' || c == '[') {
            char open = c, close = (c == '{') ? '}' : ']';
            int depth = 0;
            do {
                if (s_[pos_] == open) depth++;
                else if (s_[pos_] == close) depth--;
                pos_++;
            } while (pos_ < s_.size() && depth > 0);
        } else {
            while (pos_ < s_.size() && s_[pos_] != ',' && s_[pos_] != '}' && s_[pos_] != ']') pos_++;
        }
    }
};

std::vector<Task> loadTasks(const std::string& path) {
    std::ifstream in(path);
    if (!in) return {};
    std::stringstream buffer;
    buffer << in.rdbuf();
    return JsonParser(buffer.str()).parseTasks();
}

void saveTasks(const std::string& path, const std::vector<Task>& tasks) {
    std::ofstream out(path);
    out << "[\n";
    for (size_t i = 0; i < tasks.size(); i++) {
        const Task& t = tasks[i];
        out << "  {\"id\": " << t.id << ", \"text\": \"" << escapeJson(t.text)
            << "\", \"done\": " << (t.done ? "true" : "false") << "}";
        if (i + 1 < tasks.size()) out << ",";
        out << "\n";
    }
    out << "]\n";
}

int nextId(const std::vector<Task>& tasks) {
    int maxId = 0;
    for (const auto& t : tasks) maxId = std::max(maxId, t.id);
    return maxId + 1;
}

void printUsage() {
    std::cout << "Usage:\n"
              << "  tasks add <text...>   Add a new task\n"
              << "  tasks list            List all tasks\n"
              << "  tasks done <id>       Mark task as done\n";
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
    } else {
        printUsage();
        return 1;
    }

    return 0;
}
