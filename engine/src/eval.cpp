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

int evaluate_static(const Board& board, const EngineConfig& config) {
    int score = evaluate_material(board, config);
    for (int square = 0; square < 64; ++square) {
        const char piece = board.squares[square];
        if (piece != '\0') {
            score += positional_value(piece, square);
        }
    }
    return score;
}

int evaluate_static_for_side_to_move(const Board& board, const EngineConfig& config) {
    const int score = evaluate_static(board, config);
    return board.side_to_move == Color::White ? score : -score;
}

}  // namespace checkforge
