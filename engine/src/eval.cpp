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

}  // namespace checkforge
