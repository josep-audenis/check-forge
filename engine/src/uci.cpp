#include "checkforge/uci.h"

#include <cstdio>
#include <stdexcept>
#include <string>
#include <vector>

#include "checkforge/movegen.h"
#include "checkforge/search.h"

namespace checkforge {
namespace {

std::vector<std::string> split(const std::string& line) {
    std::vector<std::string> tokens;
    std::string current;

    for (char ch : line) {
        if (ch == ' ' || ch == '\t' || ch == '\r' || ch == '\n') {
            if (!current.empty()) {
                tokens.push_back(current);
                current.clear();
            }
            continue;
        }
        current.push_back(ch);
    }

    if (!current.empty()) {
        tokens.push_back(current);
    }

    return tokens;
}

std::string join_tokens(const std::vector<std::string>& tokens, std::size_t first, std::size_t count) {
    std::string result;
    for (std::size_t i = 0; i < count; ++i) {
        if (i > 0) {
            result.push_back(' ');
        }
        result += tokens[first + i];
    }
    return result;
}

void add_output(std::vector<std::string>* output, const std::string& line) {
    output->push_back(line);
}

bool apply_moves(Board* board, const std::vector<std::string>& tokens, std::size_t moves_index, std::vector<std::string>* output) {
    for (std::size_t i = moves_index + 1; i < tokens.size(); ++i) {
        Move move;
        if (!try_parse_uci_move(*board, tokens[i], &move)) {
            add_output(output, "info string illegal move ignored: " + tokens[i]);
            return false;
        }
        *board = make_move(*board, move);
    }
    return true;
}

void handle_position(Board* board, const std::vector<std::string>& tokens, std::vector<std::string>* output) {
    if (tokens.size() < 2) {
        add_output(output, "info string position command missing arguments");
        return;
    }

    std::size_t moves_index = tokens.size();
    for (std::size_t i = 0; i < tokens.size(); ++i) {
        if (tokens[i] == "moves") {
            moves_index = i;
            break;
        }
    }

    try {
        if (tokens[1] == "startpos") {
            *board = Board::startpos();
        } else if (tokens[1] == "fen") {
            if (moves_index < 8 || tokens.size() < 8) {
                add_output(output, "info string position fen needs six FEN fields");
                return;
            }
            *board = Board::from_fen(join_tokens(tokens, 2, 6));
        } else {
            add_output(output, "info string unsupported position command");
            return;
        }
    } catch (const std::invalid_argument& error) {
        add_output(output, std::string("info string invalid position: ") + error.what());
        return;
    }

    if (moves_index < tokens.size()) {
        (void)apply_moves(board, tokens, moves_index, output);
    }
}

struct GoParams {
    bool has_depth = false;
    int depth = 0;
    bool has_movetime = false;
    long movetime = 0;
    long wtime = -1;
    long btime = -1;
    long winc = 0;
    long binc = 0;
};

long parse_long(const std::string& text) {
    return std::stol(text);
}

GoParams parse_go(const std::vector<std::string>& tokens) {
    GoParams params;
    for (std::size_t i = 1; i + 1 < tokens.size(); ++i) {
        const std::string& key = tokens[i];
        try {
            if (key == "depth") {
                params.has_depth = true;
                params.depth = static_cast<int>(parse_long(tokens[i + 1]));
            } else if (key == "movetime") {
                params.has_movetime = true;
                params.movetime = parse_long(tokens[i + 1]);
            } else if (key == "wtime") {
                params.wtime = parse_long(tokens[i + 1]);
            } else if (key == "btime") {
                params.btime = parse_long(tokens[i + 1]);
            } else if (key == "winc") {
                params.winc = parse_long(tokens[i + 1]);
            } else if (key == "binc") {
                params.binc = parse_long(tokens[i + 1]);
            }
        } catch (const std::exception&) {
            // Ignore malformed numeric arguments; fall back to defaults.
        }
    }
    return params;
}

// Turn the side-to-move clock into a per-move time budget in milliseconds.
long time_budget_ms(const Board& board, const GoParams& params) {
    const bool white = board.side_to_move == Color::White;
    const long remaining = white ? params.wtime : params.btime;
    const long increment = white ? params.winc : params.binc;

    // Spend a small fraction of the remaining time plus most of the increment,
    // leaving a safety margin so we never flag. Clamp to a sane minimum.
    // (A more aggressive remaining/20 + full increment was tried in exp012 and
    // rejected: it flagged at bullet TC and lost ~98 Elo.)
    long budget = remaining / 30 + (increment * 3) / 4;
    const long safety_cap = (remaining * 4) / 5;  // never commit more than 80%
    if (budget > safety_cap) {
        budget = safety_cap;
    }
    if (budget < 5) {
        budget = 5;
    }
    return budget;
}

void handle_go(const Board& board, const EngineConfig& config, const std::vector<std::string>& tokens, std::vector<std::string>* output) {
    const GoParams params = parse_go(tokens);

    SearchResult result;
    constexpr int kMaxTimedDepth = 64;
    if (params.has_depth) {
        // Explicit fixed-depth request (used by tactical tests and tooling).
        result = search_bestmove(board, params.depth < 1 ? 1 : params.depth, config);
    } else if (params.has_movetime) {
        result = search_bestmove_timed(board, kMaxTimedDepth, params.movetime, config);
    } else if (params.wtime >= 0 || params.btime >= 0) {
        // Clock-based search: deepen iteratively within the computed budget.
        result = search_bestmove_timed(board, kMaxTimedDepth, time_budget_ms(board, params), config);
    } else {
        // No limits given: fall back to the configured fixed depth.
        result = search_bestmove(board, config.default_depth, config);
    }

    if (!result.has_move) {
        add_output(output, "bestmove 0000");
        return;
    }

    add_output(output, "bestmove " + move_to_uci(result.best_move));
}

}  // namespace

UciSession::UciSession() : board(Board::startpos()), config(default_config()) {}

UciSession::UciSession(const EngineConfig& config) : board(Board::startpos()), config(config) {}

std::vector<std::string> UciSession::handle_line(const std::string& line) {
    std::vector<std::string> output;
    const std::vector<std::string> tokens = split(line);
    if (tokens.empty()) {
        return output;
    }

    const std::string& command = tokens[0];
    if (command == "uci") {
        add_output(&output, "id name CheckForge");
        add_output(&output, "id author Josep Audenis");
        add_output(&output, "uciok");
    } else if (command == "isready") {
        add_output(&output, "readyok");
    } else if (command == "ucinewgame") {
        board = Board::startpos();
    } else if (command == "position") {
        handle_position(&board, tokens, &output);
    } else if (command == "go") {
        handle_go(board, config, tokens, &output);
    } else if (command == "stop") {
    } else if (command == "quit") {
        add_output(&output, "__quit__");
    } else {
        add_output(&output, "info string unknown command: " + command);
    }

    return output;
}

int run_uci_stdio(const EngineConfig& config) {
    UciSession session(config);
    char buffer[4096];

    while (std::fgets(buffer, sizeof(buffer), stdin) != nullptr) {
        const std::vector<std::string> lines = session.handle_line(buffer);
        for (const std::string& line : lines) {
            if (line == "__quit__") {
                return 0;
            }
            std::printf("%s\n", line.c_str());
            std::fflush(stdout);
        }
    }

    return 0;
}

}  // namespace checkforge
