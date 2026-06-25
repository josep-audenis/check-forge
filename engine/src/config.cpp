#include "checkforge/config.h"

#include <cctype>
#include <cstdio>
#include <stdexcept>
#include <string>

namespace checkforge {
namespace {

std::string read_file(const std::string& path) {
    FILE* input = std::fopen(path.c_str(), "rb");
    if (input == nullptr) {
        throw std::invalid_argument("could not open config: " + path);
    }

    std::string text;
    char buffer[4096];
    while (true) {
        const std::size_t count = std::fread(buffer, 1, sizeof(buffer), input);
        if (count > 0) {
            text.append(buffer, count);
        }
        if (count < sizeof(buffer)) {
            break;
        }
    }
    std::fclose(input);
    return text;
}

int parse_positive_int_after_key(const std::string& text, const std::string& key, int fallback) {
    const std::string quoted_key = "\"" + key + "\"";
    const std::size_t key_pos = text.find(quoted_key);
    if (key_pos == std::string::npos) {
        return fallback;
    }

    const std::size_t colon_pos = text.find(':', key_pos + quoted_key.size());
    if (colon_pos == std::string::npos) {
        throw std::invalid_argument("config key missing colon: " + key);
    }

    std::size_t value_pos = colon_pos + 1;
    while (value_pos < text.size() && std::isspace(static_cast<unsigned char>(text[value_pos]))) {
        ++value_pos;
    }

    if (value_pos >= text.size() || !std::isdigit(static_cast<unsigned char>(text[value_pos]))) {
        throw std::invalid_argument("config key must be positive integer: " + key);
    }

    std::size_t end_pos = value_pos;
    while (end_pos < text.size() && std::isdigit(static_cast<unsigned char>(text[end_pos]))) {
        ++end_pos;
    }

    const int value = std::stoi(text.substr(value_pos, end_pos - value_pos));
    if (value <= 0) {
        throw std::invalid_argument("config key must be positive integer: " + key);
    }
    return value;
}

}  // namespace

EngineConfig default_config() {
    return EngineConfig{};
}

EngineConfig load_config_file(const std::string& path) {
    const std::string text = read_file(path);
    EngineConfig config = default_config();

    config.pawn_value = parse_positive_int_after_key(text, "pawn", config.pawn_value);
    config.knight_value = parse_positive_int_after_key(text, "knight", config.knight_value);
    config.bishop_value = parse_positive_int_after_key(text, "bishop", config.bishop_value);
    config.rook_value = parse_positive_int_after_key(text, "rook", config.rook_value);
    config.queen_value = parse_positive_int_after_key(text, "queen", config.queen_value);
    config.default_depth = parse_positive_int_after_key(text, "default_depth", config.default_depth);
    config.quiescence_depth = parse_positive_int_after_key(text, "quiescence_depth", config.quiescence_depth);
    config.mob_knight = parse_positive_int_after_key(text, "mob_knight", config.mob_knight);
    config.mob_bishop = parse_positive_int_after_key(text, "mob_bishop", config.mob_bishop);
    config.mob_rook = parse_positive_int_after_key(text, "mob_rook", config.mob_rook);
    config.mob_queen = parse_positive_int_after_key(text, "mob_queen", config.mob_queen);

    return config;
}

std::string config_to_json(const EngineConfig& config) {
    char buffer[768];
    std::snprintf(
        buffer,
        sizeof(buffer),
        "{\"piece_values\":{\"pawn\":%d,\"knight\":%d,\"bishop\":%d,\"rook\":%d,\"queen\":%d},"
        "\"eval_weights\":{\"mob_knight\":%d,\"mob_bishop\":%d,\"mob_rook\":%d,\"mob_queen\":%d},"
        "\"search_params\":{\"default_depth\":%d,\"quiescence_depth\":%d}}",
        config.pawn_value,
        config.knight_value,
        config.bishop_value,
        config.rook_value,
        config.queen_value,
        config.mob_knight,
        config.mob_bishop,
        config.mob_rook,
        config.mob_queen,
        config.default_depth,
        config.quiescence_depth);
    return std::string(buffer);
}

}  // namespace checkforge
