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

int parse_go_depth(const std::vector<std::string>& tokens, const EngineConfig& config) {
    for (std::size_t i = 1; i + 1 < tokens.size(); ++i) {
        if (tokens[i] == "depth") {
            const int depth = std::stoi(tokens[i + 1]);
            return depth < 1 ? 1 : depth;
        }
        if (tokens[i] == "movetime") {
            return config.default_depth;
        }
    }

    return config.default_depth;
}

void handle_go(const Board& board, const EngineConfig& config, const std::vector<std::string>& tokens, std::vector<std::string>* output) {
    int depth = 3;
    try {
        depth = parse_go_depth(tokens, config);
    } catch (const std::exception&) {
        depth = config.default_depth;
    }

    const SearchResult result = search_bestmove(board, depth, config);
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
