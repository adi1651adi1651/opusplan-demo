#include <cstdio>
#include <iostream>
#include <string>
#include <vector>

#include "../tasks.hpp"

int g_pass = 0;
int g_fail = 0;

void check(bool cond, const std::string& name) {
    if (cond) {
        g_pass++;
    } else {
        g_fail++;
        std::cout << "[FAIL] " << name << "\n";
    }
}

template <typename T>
void checkEq(const T& actual, const T& expected, const std::string& name) {
    if (actual == expected) {
        g_pass++;
        return;
    }
    g_fail++;
    std::cout << "[FAIL] " << name << " -- expected [" << expected << "] got [" << actual << "]\n";
}

bool taskEq(const Task& a, const Task& b) {
    return a.id == b.id && a.text == b.text && a.done == b.done;
}

void testEscapeJson() {
    checkEq(escapeJson("hello"), std::string("hello"), "escapeJson: plain text unchanged");
    checkEq(escapeJson("\""), std::string("\\\""), "escapeJson: lone quote");
    checkEq(escapeJson("\\"), std::string("\\\\"), "escapeJson: lone backslash");
    checkEq(escapeJson("\n"), std::string("\\n"), "escapeJson: lone newline");
    checkEq(escapeJson("\t"), std::string("\\t"), "escapeJson: lone tab");
    checkEq(escapeJson(""), std::string(""), "escapeJson: empty string");
    checkEq(escapeJson("\"\\\n\t"), std::string("\\\"\\\\\\n\\t"), "escapeJson: combined special chars");
    checkEq(escapeJson("say \"hi\""), std::string("say \\\"hi\\\""), "escapeJson: quote embedded mid-word");
}

void testJsonParser() {
    checkEq(JsonParser("[]").parseTasks().size(), std::size_t{0}, "JsonParser: empty array");
    checkEq(JsonParser("  [   ]  ").parseTasks().size(), std::size_t{0}, "JsonParser: whitespace-padded empty array");

    {
        auto tasks = JsonParser(R"([{"id":1,"text":"buy milk","done":false}])").parseTasks();
        checkEq(tasks.size(), std::size_t{1}, "JsonParser: single task count");
        if (tasks.size() == 1) {
            check(taskEq(tasks[0], Task{1, "buy milk", false}), "JsonParser: single task contents");
        }
    }

    {
        auto tasks = JsonParser(
            R"([{"id":1,"text":"a","done":false},{"id":2,"text":"b","done":true},{"id":3,"text":"c","done":false}])")
            .parseTasks();
        checkEq(tasks.size(), std::size_t{3}, "JsonParser: multiple tasks count");
        if (tasks.size() == 3) {
            check(taskEq(tasks[0], Task{1, "a", false}), "JsonParser: multiple tasks order[0]");
            check(taskEq(tasks[1], Task{2, "b", true}), "JsonParser: multiple tasks order[1]");
            check(taskEq(tasks[2], Task{3, "c", false}), "JsonParser: multiple tasks order[2]");
        }
    }

    {
        auto tasks = JsonParser(R"([{"id":1,"text":"say \"hi\"\nbye","done":true}])").parseTasks();
        checkEq(tasks.size(), std::size_t{1}, "JsonParser: escaped chars round-trip count");
        if (tasks.size() == 1) {
            checkEq(tasks[0].text, std::string("say \"hi\"\nbye"), "JsonParser: escaped chars round-trip text");
        }
    }

    {
        auto tasks = JsonParser(R"([{"priority":3,"id":1,"text":"x","done":false}])").parseTasks();
        checkEq(tasks.size(), std::size_t{1}, "JsonParser: unknown scalar key skipped count");
        if (tasks.size() == 1) {
            check(taskEq(tasks[0], Task{1, "x", false}), "JsonParser: unknown scalar key skipped contents");
        }
    }

    {
        auto tasks = JsonParser(R"([{"meta":{"a":1},"id":1,"text":"x","done":false}])").parseTasks();
        checkEq(tasks.size(), std::size_t{1}, "JsonParser: unknown nested object key skipped count");
        if (tasks.size() == 1) {
            check(taskEq(tasks[0], Task{1, "x", false}), "JsonParser: unknown nested object key skipped contents");
        }
    }

    {
        auto tasks = JsonParser(R"([{"tags":["x","y"],"id":1,"text":"x","done":false}])").parseTasks();
        checkEq(tasks.size(), std::size_t{1}, "JsonParser: unknown nested array key skipped count");
        if (tasks.size() == 1) {
            check(taskEq(tasks[0], Task{1, "x", false}), "JsonParser: unknown nested array key skipped contents");
        }
    }

    {
        auto tasks = JsonParser(R"([{"done":true,"text":"x","id":5}])").parseTasks();
        checkEq(tasks.size(), std::size_t{1}, "JsonParser: keys out of order count");
        if (tasks.size() == 1) {
            check(taskEq(tasks[0], Task{5, "x", true}), "JsonParser: keys out of order contents");
        }
    }

    {
        auto tasks = JsonParser(R"([{"id":1,"text":"x","done":false})").parseTasks();
        checkEq(tasks.size(), std::size_t{1}, "JsonParser: missing trailing ] tolerated");
        if (tasks.size() == 1) {
            check(taskEq(tasks[0], Task{1, "x", false}), "JsonParser: missing trailing ] contents");
        }
    }

    {
        auto tasks = JsonParser(R"([{"id":1,"text":"x","done":false)").parseTasks();
        checkEq(tasks.size(), std::size_t{1}, "JsonParser: missing trailing } tolerated");
        if (tasks.size() == 1) {
            check(taskEq(tasks[0], Task{1, "x", false}), "JsonParser: missing trailing } contents");
        }
    }

    {
        auto tasks = JsonParser("[\n  {\n    \"id\" : 1,\n    \"text\":   \"x\"  ,\n    \"done\": false\n  }\n]\n")
                         .parseTasks();
        checkEq(tasks.size(), std::size_t{1}, "JsonParser: irregular whitespace count");
        if (tasks.size() == 1) {
            check(taskEq(tasks[0], Task{1, "x", false}), "JsonParser: irregular whitespace contents");
        }
    }
}

void testLoadSaveTasksRoundtrip() {
    const std::string kTmp = "test_tmp_tasks.json";
    std::remove(kTmp.c_str());

    std::vector<Task> original = {
        {1, "buy milk", false},
        {2, "say \"hi\"\nbye\tthere", true},
        {3, "walk the dog", false},
    };
    saveTasks(kTmp, original);
    auto loaded = loadTasks(kTmp);
    checkEq(loaded.size(), original.size(), "loadSaveTasks: roundtrip count");
    if (loaded.size() == original.size()) {
        for (std::size_t i = 0; i < original.size(); i++) {
            check(taskEq(loaded[i], original[i]), "loadSaveTasks: roundtrip element " + std::to_string(i));
        }
    }

    saveTasks(kTmp, {});
    checkEq(loadTasks(kTmp).size(), std::size_t{0}, "loadSaveTasks: empty vector roundtrip");

    checkEq(loadTasks("does_not_exist_12345.json").size(), std::size_t{0}, "loadSaveTasks: nonexistent path returns empty");

    std::remove(kTmp.c_str());
}

void testNextId() {
    checkEq(nextId({}), 1, "nextId: empty vector");
    checkEq(nextId({{1, "a", false}, {2, "b", false}, {3, "c", false}}), 4, "nextId: contiguous ids");
    checkEq(nextId({{1, "a", false}, {5, "b", false}, {3, "c", false}}), 6, "nextId: non-contiguous ids");
    checkEq(nextId({{7, "a", false}}), 8, "nextId: single id");
    checkEq(nextId({{2, "a", false}, {4, "b", false}}), 5, "nextId: gap case (no gap-filling)");
}

int main() {
    testEscapeJson();
    testJsonParser();
    testLoadSaveTasksRoundtrip();
    testNextId();
    std::cout << g_pass << " passed, " << g_fail << " failed\n";
    return g_fail == 0 ? 0 : 1;
}
