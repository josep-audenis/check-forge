#pragma once

#include <cstdint>
#include <string>

namespace checkforge {

enum class Color {
    White,
    Black,
};

struct CastlingRights {
    bool white_kingside = false;
    bool white_queenside = false;
    bool black_kingside = false;
    bool black_queenside = false;
};

struct Board {
    char squares[64]{};
    Color side_to_move = Color::White;
    CastlingRights castling;
    int en_passant_square = -1;
    int halfmove_clock = 0;
    int fullmove_number = 1;
    std::uint64_t zobrist = 0;  // incrementally maintained in make/unmake (exp027)

    static Board startpos();
    static Board from_fen(const std::string& fen);

    std::string to_fen() const;
    char piece_at(int square) const;
};

int square_index(char file, char rank);
std::string square_name(int square);

}  // namespace checkforge
