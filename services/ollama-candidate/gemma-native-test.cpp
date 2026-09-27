#include "chat.h"

#include <algorithm>
#include <fstream>
#include <iostream>
#include <iterator>

int main(int argc, char ** argv) {
    if (argc != 2) return 1;
    std::ifstream file(argv[1]);
    const std::string text{std::istreambuf_iterator<char>(file), {}};
    const auto templates = common_chat_templates_init(nullptr, text);
    common_chat_templates_inputs inputs;
    common_chat_msg message;
    message.role = "user";
    message.content = "Find the example record.";
    inputs.messages.push_back(message);
    inputs.tools.push_back({"lookup_record", "Find a record",
        R"({"type":"object","properties":{"key":{"type":"string"}},"required":["key"]})"});
    const auto params = common_chat_templates_apply(templates.get(), inputs);
    if (params.format != COMMON_CHAT_FORMAT_PEG_GEMMA4 || params.grammar.empty()) {
        std::cerr << "Native Gemma tool grammar was not activated\n";
        return 1;
    }
    const auto contains = [&](const std::string & token) {
        return std::find(params.preserved_tokens.begin(), params.preserved_tokens.end(), token)
            != params.preserved_tokens.end();
    };
    if (!contains("<|\"|>")) {
        std::cerr << "Missing Gemma string delimiter in native preserved_tokens\n";
        return 2;
    }
    if (contains("<turn|>")) {
        std::cerr << "End-of-turn token would leak into ordinary content\n";
        return 1;
    }
    std::cout << "Native grammar and narrow delimiter preservation passed\n";
}
