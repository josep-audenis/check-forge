#include "checkforge/bitboard.h"

#include <initializer_list>
#include <random>

namespace checkforge {

Bitboard g_knight_attacks[64];
Bitboard g_king_attacks[64];
Bitboard g_pawn_attacks[2][64];

namespace {

inline bool on_board(int rank, int file) {
    return rank >= 0 && rank < 8 && file >= 0 && file < 8;
}

const int kBishopDirs[4][2] = {{-1, -1}, {-1, 1}, {1, -1}, {1, 1}};
const int kRookDirs[4][2] = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};

// Full ray attacks against an occupancy (used to build the magic tables and as the source
// of truth). Blocker square is included (capturable).
Bitboard ray_attacks(int square, Bitboard occupancy, const int dirs[][2]) {
    Bitboard attacks = 0;
    const int r0 = square >> 3;
    const int f0 = square & 7;
    for (int i = 0; i < 4; ++i) {
        int r = r0 + dirs[i][0];
        int f = f0 + dirs[i][1];
        while (on_board(r, f)) {
            const int sq = r * 8 + f;
            attacks |= (Bitboard{1} << sq);
            if (occupancy & (Bitboard{1} << sq)) {
                break;
            }
            r += dirs[i][0];
            f += dirs[i][1];
        }
    }
    return attacks;
}

// "Relevant occupancy" mask for a slider on `square`: ray squares excluding the board
// edges (edge blockers never change the attack set).
Bitboard slider_mask(int square, const int dirs[][2]) {
    Bitboard mask = 0;
    const int r0 = square >> 3;
    const int f0 = square & 7;
    for (int i = 0; i < 4; ++i) {
        int r = r0 + dirs[i][0];
        int f = f0 + dirs[i][1];
        while (r >= 1 && r <= 6 && f >= 1 && f <= 6 ? true
               : (r >= 0 && r < 8 && f >= 0 && f < 8)) {
            // Include only interior squares: stop before the edge in this direction.
            const int nr = r + dirs[i][0];
            const int nf = f + dirs[i][1];
            if (nr < 0 || nr > 7 || nf < 0 || nf > 7) {
                break;  // `r,f` is the last square before the edge -> excluded
            }
            mask |= (Bitboard{1} << (r * 8 + f));
            r = nr;
            f = nf;
        }
    }
    return mask;
}

struct Magic {
    Bitboard mask = 0;
    Bitboard magic = 0;
    int shift = 0;
    Bitboard* table = nullptr;  // sized 1 << popcount(mask)
};

Magic g_rook_magic[64];
Magic g_bishop_magic[64];
Bitboard g_rook_table[64][4096];   // 2^12 max
Bitboard g_bishop_table[64][512];  // 2^9 max

inline unsigned magic_index(Bitboard occ, const Magic& m) {
    return static_cast<unsigned>(((occ & m.mask) * m.magic) >> m.shift);
}

// Enumerate the index-th subset of the set bits of `mask` (carry-rippler order).
Bitboard subset_from_index(int index, Bitboard mask) {
    Bitboard sub = 0;
    Bitboard m = mask;
    int bit = 0;
    while (m) {
        const int sq = __builtin_ctzll(m);
        m &= m - 1;
        if (index & (1 << bit)) {
            sub |= (Bitboard{1} << sq);
        }
        ++bit;
    }
    return sub;
}

void init_magics(std::mt19937_64& rng, const int dirs[][2], Magic magics[64],
                 Bitboard tables[64][4096], int max_entries) {
    std::uniform_int_distribution<Bitboard> dist;
    for (int sq = 0; sq < 64; ++sq) {
        const Bitboard mask = slider_mask(sq, dirs);
        const int bits = __builtin_popcountll(mask);
        const int count = 1 << bits;
        magics[sq].mask = mask;
        magics[sq].shift = 64 - bits;
        magics[sq].table = tables[sq];

        // Precompute (subset occupancy, attacks) pairs.
        static Bitboard occs[4096];
        static Bitboard atts[4096];
        for (int i = 0; i < count; ++i) {
            occs[i] = subset_from_index(i, mask);
            atts[i] = ray_attacks(sq, occs[i], dirs);
        }

        // Trial random sparse magics until one maps all subsets without collision.
        while (true) {
            const Bitboard candidate = dist(rng) & dist(rng) & dist(rng);  // few set bits
            magics[sq].magic = candidate;
            for (int i = 0; i < max_entries; ++i) {
                tables[sq][i] = 0;
            }
            bool ok = true;
            for (int i = 0; i < count && ok; ++i) {
                const unsigned idx = magic_index(occs[i], magics[sq]);
                if (tables[sq][idx] == 0) {
                    tables[sq][idx] = atts[i];
                } else if (tables[sq][idx] != atts[i]) {
                    ok = false;  // collision mapping to different attacks
                }
            }
            if (ok) {
                break;
            }
        }
    }
}

struct AttackInit {
    AttackInit() {
        const int knight[8][2] = {{-2, -1}, {-2, 1}, {-1, -2}, {-1, 2},
                                  {1, -2},  {1, 2},  {2, -1},  {2, 1}};
        for (int sq = 0; sq < 64; ++sq) {
            const int r = sq >> 3;
            const int f = sq & 7;
            Bitboard n = 0;
            for (const auto& o : knight) {
                if (on_board(r + o[0], f + o[1])) {
                    n |= Bitboard{1} << ((r + o[0]) * 8 + (f + o[1]));
                }
            }
            g_knight_attacks[sq] = n;

            Bitboard k = 0;
            for (int dr = -1; dr <= 1; ++dr) {
                for (int df = -1; df <= 1; ++df) {
                    if ((dr || df) && on_board(r + dr, f + df)) {
                        k |= Bitboard{1} << ((r + dr) * 8 + (f + df));
                    }
                }
            }
            g_king_attacks[sq] = k;

            Bitboard wp = 0, bp = 0;
            for (int df : {-1, 1}) {
                if (on_board(r - 1, f + df)) {
                    wp |= Bitboard{1} << ((r - 1) * 8 + (f + df));
                }
                if (on_board(r + 1, f + df)) {
                    bp |= Bitboard{1} << ((r + 1) * 8 + (f + df));
                }
            }
            g_pawn_attacks[0][sq] = wp;
            g_pawn_attacks[1][sq] = bp;
        }

        std::mt19937_64 rng(0x00C0FFEE12345678ull);  // fixed seed -> deterministic magics
        init_magics(rng, kRookDirs, g_rook_magic, g_rook_table, 4096);
        // Bishop tables are narrower; reuse the routine via a 4096-wide view is unsafe, so
        // build bishop magics with their own (512-wide) tables.
        std::uniform_int_distribution<Bitboard> dist;
        for (int sq = 0; sq < 64; ++sq) {
            const Bitboard mask = slider_mask(sq, kBishopDirs);
            const int bits = __builtin_popcountll(mask);
            const int count = 1 << bits;
            g_bishop_magic[sq].mask = mask;
            g_bishop_magic[sq].shift = 64 - bits;
            g_bishop_magic[sq].table = g_bishop_table[sq];
            static Bitboard occs[512];
            static Bitboard atts[512];
            for (int i = 0; i < count; ++i) {
                occs[i] = subset_from_index(i, mask);
                atts[i] = ray_attacks(sq, occs[i], kBishopDirs);
            }
            while (true) {
                const Bitboard candidate = dist(rng) & dist(rng) & dist(rng);
                g_bishop_magic[sq].magic = candidate;
                for (int i = 0; i < 512; ++i) {
                    g_bishop_table[sq][i] = 0;
                }
                bool ok = true;
                for (int i = 0; i < count && ok; ++i) {
                    const unsigned idx = magic_index(occs[i], g_bishop_magic[sq]);
                    if (g_bishop_table[sq][idx] == 0) {
                        g_bishop_table[sq][idx] = atts[i];
                    } else if (g_bishop_table[sq][idx] != atts[i]) {
                        ok = false;
                    }
                }
                if (ok) {
                    break;
                }
            }
        }
    }
};
const AttackInit g_attack_init;

}  // namespace

Bitboard bishop_attacks(int square, Bitboard occupancy) {
    const Magic& m = g_bishop_magic[square];
    return m.table[magic_index(occupancy, m)];
}

Bitboard rook_attacks(int square, Bitboard occupancy) {
    const Magic& m = g_rook_magic[square];
    return m.table[magic_index(occupancy, m)];
}

}  // namespace checkforge
