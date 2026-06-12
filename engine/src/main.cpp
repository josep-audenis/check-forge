#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <stdexcept>
#include <vector>

#include "checkforge/board.h"
#include "checkforge/config.h"
#include "checkforge/eval.h"
#include "checkforge/movegen.h"
#include "checkforge/search.h"
#include "checkforge/uci.h"

namespace {

void print_usage() {
    std::puts("CheckForge engine");
    std::puts("Usage:");
    std::puts("  checkforge --version");
    std::puts("  checkforge --config <path> <command>");
    std::puts("  checkforge --fen <fen|startpos>");
    std::puts("  checkforge --moves <fen|startpos>");
    std::puts("  checkforge --perft <fen|startpos> <depth>");
    std::puts("  checkforge --eval <fen|startpos>");
    std::puts("  checkforge --bestmove <fen|startpos> --depth <n>");
    std::puts("  checkforge uci");
}

}  // namespace

int main(int argc, char* argv[]) {
    checkforge::EngineConfig config = checkforge::default_config();
    int first_arg = 1;

    if (argc >= 4 && std::strcmp(argv[1], "--config") == 0) {
        try {
            config = checkforge::load_config_file(argv[2]);
            first_arg = 3;
        } catch (const std::invalid_argument& error) {
            std::fprintf(stderr, "invalid config: %s\n", error.what());
            return 2;
        }
    }

    const int remaining = argc - first_arg;
    char** args = argv + first_arg;

    if (remaining == 1 && std::strcmp(args[0], "--version") == 0) {
        std::puts("CheckForge 0.1.0-phase4");
        return 0;
    }

    if (remaining == 1 && std::strcmp(args[0], "--print-config") == 0) {
        std::puts(checkforge::config_to_json(config).c_str());
        return 0;
    }

    if (remaining == 1 && std::strcmp(args[0], "uci") == 0) {
        return checkforge::run_uci_stdio(config);
    }

    if (remaining == 2 && std::strcmp(args[0], "--fen") == 0) {
        try {
            const checkforge::Board board = checkforge::Board::from_fen(args[1]);
            std::printf("%s\n", board.to_fen().c_str());
            return 0;
        } catch (const std::invalid_argument& error) {
            std::fprintf(stderr, "invalid FEN: %s\n", error.what());
            return 2;
        }
    }

    if (remaining == 2 && std::strcmp(args[0], "--moves") == 0) {
        try {
            const checkforge::Board board = checkforge::Board::from_fen(args[1]);
            const std::vector<checkforge::Move> moves = checkforge::generate_legal_moves(board);
            for (const checkforge::Move& move : moves) {
                std::printf("%s\n", checkforge::move_to_uci(move).c_str());
            }
            return 0;
        } catch (const std::invalid_argument& error) {
            std::fprintf(stderr, "invalid FEN: %s\n", error.what());
            return 2;
        }
    }

    if (remaining == 2 && std::strcmp(args[0], "--eval") == 0) {
        try {
            const checkforge::Board board = checkforge::Board::from_fen(args[1]);
            std::printf("%d\n", checkforge::evaluate_material(board, config));
            return 0;
        } catch (const std::invalid_argument& error) {
            std::fprintf(stderr, "invalid FEN: %s\n", error.what());
            return 2;
        }
    }

    if (remaining == 4 && std::strcmp(args[0], "--bestmove") == 0 && std::strcmp(args[2], "--depth") == 0) {
        try {
            const checkforge::Board board = checkforge::Board::from_fen(args[1]);
            const int depth = std::atoi(args[3]);
            if (depth < 1) {
                std::fprintf(stderr, "invalid depth: must be positive\n");
                return 2;
            }

            const checkforge::SearchResult result = checkforge::search_bestmove(board, depth, config);
            if (!result.has_move) {
                std::puts("bestmove 0000");
            } else {
                std::printf("bestmove %s score cp %d\n", checkforge::move_to_uci(result.best_move).c_str(), result.score);
            }
            return 0;
        } catch (const std::invalid_argument& error) {
            std::fprintf(stderr, "invalid FEN: %s\n", error.what());
            return 2;
        }
    }

    if (remaining == 3 && std::strcmp(args[0], "--perft") == 0) {
        int depth = 0;
        try {
            const checkforge::Board board = checkforge::Board::from_fen(args[1]);
            depth = std::atoi(args[2]);
            if (depth < 0) {
                std::fprintf(stderr, "invalid depth: must be non-negative\n");
                return 2;
            }

            const unsigned long long nodes =
                static_cast<unsigned long long>(checkforge::perft(board, depth));
            std::printf(
                "{\"fen\":\"%s\",\"depth\":%d,\"nodes\":%llu}\n",
                args[1],
                depth,
                nodes);
            return 0;
        } catch (const std::invalid_argument& error) {
            std::fprintf(stderr, "invalid FEN: %s\n", error.what());
            return 2;
        }
    }

    print_usage();
    return 0;
}
