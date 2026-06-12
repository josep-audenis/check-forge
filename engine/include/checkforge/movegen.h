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

std::vector<Move> generate_legal_moves(const Board& board);
Board make_move(const Board& board, const Move& move);
bool is_in_check(const Board& board, Color color);
std::uint64_t perft(const Board& board, int depth);
std::string move_to_uci(const Move& move);
bool try_parse_uci_move(const Board& board, const std::string& text, Move* move);

}  // namespace checkforge
