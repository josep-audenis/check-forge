#pragma once

#include <string>
#include <vector>

#include "checkforge/board.h"
#include "checkforge/config.h"

namespace checkforge {

struct UciSession {
    Board board;
    EngineConfig config;

    UciSession();
    explicit UciSession(const EngineConfig& config);
    std::vector<std::string> handle_line(const std::string& line);
};

int run_uci_stdio(const EngineConfig& config = default_config());

}  // namespace checkforge
