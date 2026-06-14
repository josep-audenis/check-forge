#include "checkforge/eval.h"

#include <cctype>

namespace checkforge {
namespace {

int piece_value(char piece, const EngineConfig& config) {
    switch (static_cast<char>(std::tolower(static_cast<unsigned char>(piece)))) {
        case 'p':
            return config.pawn_value;
        case 'n':
            return config.knight_value;
        case 'b':
            return config.bishop_value;
        case 'r':
            return config.rook_value;
        case 'q':
            return config.queen_value;
        default:
            return 0;
    }
}

bool is_white_piece(char piece) {
    return piece >= 'A' && piece <= 'Z';
}

int file_of(int square) {
    return square % 8;
}

int rank_of(int square) {
    return square / 8;
}

int central_bonus(int square) {
    const int file = file_of(square);
    const int rank = rank_of(square);
    const int file_distance = std::min(std::abs((2 * file) - 7), 7);
    const int rank_distance = std::min(std::abs((2 * rank) - 7), 7);
    return 14 - file_distance - rank_distance;
}

int positional_value(char piece, int square) {
    const bool white = is_white_piece(piece);
    const char lower = static_cast<char>(std::tolower(static_cast<unsigned char>(piece)));
    const int rank = rank_of(square);
    const int file = file_of(square);
    const int advance = white ? 6 - rank : rank - 1;
    const bool back_rank = white ? rank == 7 : rank == 0;
    int value = 0;

    switch (lower) {
        case 'p':
            value += std::max(0, advance) * 2;
            if (file >= 2 && file <= 5) {
                value += 3;
            }
            if (file == 0 || file == 7) {
                value -= 4;
            }
            break;
        case 'n':
            value += central_bonus(square) * 4;
            if (!back_rank) {
                value += 10;
            }
            break;
        case 'b':
            value += central_bonus(square) * 2;
            if (!back_rank) {
                value += 8;
            }
            break;
        case 'r':
            if (!back_rank) {
                value += 3;
            }
            break;
        case 'q':
            value += central_bonus(square);
            break;
        default:
            break;
    }

    return white ? value : -value;
}

// Pawn-structure weights (centipawns). Hardcoded like kBishopPairBonus; expose in
// config later for tuning. Board orientation: rank 0 == 8th rank, rank 7 == white's
// back rank, so white pawns advance toward rank 0 and black toward rank 7.
constexpr int kDoubledPenalty = 15;   // per extra pawn on a file
constexpr int kIsolatedPenalty = 12;  // pawn with no friendly pawn on adjacent files
// Passed-pawn bonus indexed by rank distance advanced (0 = home rank .. 5 = about to promote).
constexpr int kPassedBonus[6] = {10, 17, 25, 40, 65, 100};

// White-perspective pawn-structure score (positive favors White).
int evaluate_pawn_structure(const Board& board) {
    int white_files[8] = {0, 0, 0, 0, 0, 0, 0, 0};
    int black_files[8] = {0, 0, 0, 0, 0, 0, 0, 0};
    // Most-advanced white pawn rank per file (smallest rank), and least-advanced black
    // pawn rank per file (largest rank), for passed-pawn tests.
    int white_min_rank[8];
    int black_max_rank[8];
    for (int f = 0; f < 8; ++f) {
        white_min_rank[f] = 8;   // none
        black_max_rank[f] = -1;  // none
    }

    for (int square = 0; square < 64; ++square) {
        const char piece = board.squares[square];
        if (piece != 'P' && piece != 'p') {
            continue;
        }
        const int f = file_of(square);
        const int r = rank_of(square);
        if (piece == 'P') {
            ++white_files[f];
            if (r < white_min_rank[f]) {
                white_min_rank[f] = r;
            }
        } else {
            ++black_files[f];
            if (r > black_max_rank[f]) {
                black_max_rank[f] = r;
            }
        }
    }

    int score = 0;

    // Doubled and isolated.
    for (int f = 0; f < 8; ++f) {
        if (white_files[f] > 1) {
            score -= (white_files[f] - 1) * kDoubledPenalty;
        }
        if (black_files[f] > 1) {
            score += (black_files[f] - 1) * kDoubledPenalty;
        }
        const bool white_adj = (f > 0 && white_files[f - 1] > 0) || (f < 7 && white_files[f + 1] > 0);
        const bool black_adj = (f > 0 && black_files[f - 1] > 0) || (f < 7 && black_files[f + 1] > 0);
        if (white_files[f] > 0 && !white_adj) {
            score -= kIsolatedPenalty;
        }
        if (black_files[f] > 0 && !black_adj) {
            score += kIsolatedPenalty;
        }
    }

    // Passed pawns. A pawn is passed if no enemy pawn stands on the same or adjacent
    // files anywhere ahead of it.
    for (int square = 0; square < 64; ++square) {
        const char piece = board.squares[square];
        if (piece != 'P' && piece != 'p') {
            continue;
        }
        const int f = file_of(square);
        const int r = rank_of(square);
        if (piece == 'P') {
            bool blocked = false;
            for (int af = f - 1; af <= f + 1 && !blocked; ++af) {
                if (af < 0 || af > 7) {
                    continue;
                }
                // Black pawn ahead of white means a smaller rank index.
                if (black_max_rank[af] != -1 && black_max_rank[af] < r) {
                    blocked = true;
                }
            }
            if (!blocked) {
                score += kPassedBonus[6 - r > 5 ? 5 : (6 - r < 0 ? 0 : 6 - r)];
            }
        } else {
            bool blocked = false;
            for (int af = f - 1; af <= f + 1 && !blocked; ++af) {
                if (af < 0 || af > 7) {
                    continue;
                }
                // White pawn ahead of black means a larger rank index.
                if (white_min_rank[af] != 8 && white_min_rank[af] > r) {
                    blocked = true;
                }
            }
            if (!blocked) {
                score -= kPassedBonus[r - 1 > 5 ? 5 : (r - 1 < 0 ? 0 : r - 1)];
            }
        }
    }

    return score;
}

}  // namespace

int evaluate_material(const Board& board) {
    return evaluate_material(board, default_config());
}

int evaluate_for_side_to_move(const Board& board) {
    return evaluate_for_side_to_move(board, default_config());
}

int evaluate_material(const Board& board, const EngineConfig& config) {
    int score = 0;

    for (char piece : board.squares) {
        if (piece == '\0') {
            continue;
        }

        const int value = piece_value(piece, config);
        score += is_white_piece(piece) ? value : -value;
    }

    return score;
}

int evaluate_for_side_to_move(const Board& board, const EngineConfig& config) {
    const int material = evaluate_material(board, config);
    return board.side_to_move == Color::White ? material : -material;
}

constexpr int kBishopPairBonus = 30;

int evaluate_static(const Board& board, const EngineConfig& config) {
    int score = evaluate_material(board, config);
    int white_bishops = 0;
    int black_bishops = 0;
    for (int square = 0; square < 64; ++square) {
        const char piece = board.squares[square];
        if (piece == '\0') {
            continue;
        }
        score += positional_value(piece, square);
        if (piece == 'B') {
            ++white_bishops;
        } else if (piece == 'b') {
            ++black_bishops;
        }
    }
    if (white_bishops >= 2) {
        score += kBishopPairBonus;
    }
    if (black_bishops >= 2) {
        score -= kBishopPairBonus;
    }
    score += evaluate_pawn_structure(board);
    return score;
}

int evaluate_static_for_side_to_move(const Board& board, const EngineConfig& config) {
    const int score = evaluate_static(board, config);
    return board.side_to_move == Color::White ? score : -score;
}

}  // namespace checkforge
