#pragma once

#include <string>

namespace checkforge {

struct EngineConfig {
    int pawn_value = 100;
    int knight_value = 320;
    int bishop_value = 330;
    int rook_value = 500;
    int queen_value = 900;
    int default_depth = 3;
    int quiescence_depth = 4;
};

EngineConfig default_config();
EngineConfig load_config_file(const std::string& path);
std::string config_to_json(const EngineConfig& config);

}  // namespace checkforge
