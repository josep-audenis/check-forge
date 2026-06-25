#pragma once

#include <cstdint>

namespace checkforge {

using Bitboard = std::uint64_t;

// Piece -> bitboard index (P N B R Q K p n b r q k). Matches the Zobrist ordering.
// Returns -1 for empty / invalid.
inline int bb_piece_index(char piece) {
    switch (piece) {
        case 'P': return 0;  case 'N': return 1;  case 'B': return 2;
        case 'R': return 3;  case 'Q': return 4;  case 'K': return 5;
        case 'p': return 6;  case 'n': return 7;  case 'b': return 8;
        case 'r': return 9;  case 'q': return 10; case 'k': return 11;
        default:  return -1;
    }
}

// Precomputed leaper attacks; slider attacks computed on the fly against an occupancy
// bitboard (classical ray loops — simple and correct; magics can come later).
extern Bitboard g_knight_attacks[64];
extern Bitboard g_king_attacks[64];
extern Bitboard g_pawn_attacks[2][64];  // [0]=white, [1]=black

Bitboard bishop_attacks(int square, Bitboard occupancy);
Bitboard rook_attacks(int square, Bitboard occupancy);
inline Bitboard queen_attacks(int square, Bitboard occupancy) {
    return bishop_attacks(square, occupancy) | rook_attacks(square, occupancy);
}

inline int bb_popcount(Bitboard b) { return __builtin_popcountll(b); }
inline int bb_lsb(Bitboard b) { return __builtin_ctzll(b); }
inline Bitboard bb_pop_lsb(Bitboard* b) {
    const Bitboard lsb = *b & (~*b + 1);
    *b &= *b - 1;
    return lsb;
}

}  // namespace checkforge
