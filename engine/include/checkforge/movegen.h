#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include "checkforge/board.h"

namespace checkforge {

struct Move {
    int from = -1;
    int to = -1;
    char promotion = '\0';
    bool is_en_passant = false;
    bool is_castling = false;
};

// Undo record for in-place make/unmake (the search hot path: avoids copying a whole
// Board per move). Holds everything needed to restore the position.
struct Undo {
    char moved = '\0';        // piece that was on move.from (pre-promotion)
    char captured = '\0';     // captured piece, or '\0'
    int captured_square = -1; // where the captured piece sat (to-square, or e.p. square)
    CastlingRights castling;
    int en_passant_square = -1;
    int halfmove_clock = 0;
    int fullmove_number = 1;
    std::uint64_t zobrist = 0;  // board hash before the move, restored on unmake
};

// Full Zobrist hash from scratch (use once at the search root; make/unmake then maintains
// board.zobrist incrementally).
std::uint64_t compute_zobrist(const Board& board);

std::vector<Move> generate_legal_moves(const Board& board);
Board make_move(const Board& board, const Move& move);
Undo make_move_inplace(Board& board, const Move& move);
void unmake_move(Board& board, const Move& move, const Undo& undo);
bool is_in_check(const Board& board, Color color);
std::uint64_t perft(const Board& board, int depth);
std::string move_to_uci(const Move& move);
bool try_parse_uci_move(const Board& board, const std::string& text, Move* move);

}  // namespace checkforge
