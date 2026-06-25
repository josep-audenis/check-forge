#include "checkforge/movegen.h"

#include "checkforge/bitboard.h"

#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>

namespace checkforge {
namespace {

bool is_white_piece(char piece) {
    return piece >= 'A' && piece <= 'Z';
}

bool is_black_piece(char piece) {
    return piece >= 'a' && piece <= 'z';
}

bool is_color_piece(char piece, Color color) {
    return color == Color::White ? is_white_piece(piece) : is_black_piece(piece);
}

bool is_enemy_piece(char piece, Color color) {
    return piece != '\0' && !is_color_piece(piece, color);
}

Color opposite(Color color) {
    return color == Color::White ? Color::Black : Color::White;
}

int file_of(int square) {
    return square % 8;
}

int rank_of(int square) {
    return square / 8;
}

bool on_board(int rank, int file) {
    return rank >= 0 && rank < 8 && file >= 0 && file < 8;
}

int index_of(int rank, int file) {
    return rank * 8 + file;
}

char promotion_piece(Color color, char piece) {
    return color == Color::White ? piece : static_cast<char>(std::tolower(static_cast<unsigned char>(piece)));
}

void add_move(std::vector<Move>* moves, int from, int to) {
    Move move;
    move.from = from;
    move.to = to;
    moves->push_back(move);
}

void add_promotion_moves(std::vector<Move>* moves, int from, int to, Color color) {
    const char pieces[] = {'Q', 'R', 'B', 'N'};
    for (char piece : pieces) {
        Move move;
        move.from = from;
        move.to = to;
        move.promotion = promotion_piece(color, piece);
        moves->push_back(move);
    }
}

int find_king(const Board& board, Color color) {
    const char king = color == Color::White ? 'K' : 'k';
    for (int square = 0; square < 64; ++square) {
        if (board.squares[square] == king) {
            return square;
        }
    }
    throw std::invalid_argument("board has no king");
}

// Bitboard attack detection (exp031): uses the piece bitboards maintained on the Board.
// A square is attacked by `attacker` if any of its pieces hits it.
Bitboard color_occupancy(const Board& board, Color color) {
    Bitboard occ = 0;
    const int base = color == Color::White ? 0 : 6;
    for (int i = 0; i < 6; ++i) {
        occ |= board.bb[base + i];
    }
    return occ;
}

Bitboard total_occupancy(const Board& board) {
    Bitboard occ = 0;
    for (int i = 0; i < 12; ++i) {
        occ |= board.bb[i];
    }
    return occ;
}

// Emit a quiet/capture move to every set bit of `targets`.
void emit_targets(int from, Bitboard targets, std::vector<Move>* moves) {
    while (targets) {
        const int to = bb_lsb(targets);
        targets &= targets - 1;
        add_move(moves, from, to);
    }
}

bool is_square_attacked(const Board& board, int square, Color attacker) {
    Bitboard occ = 0;
    for (int i = 0; i < 12; ++i) {
        occ |= board.bb[i];
    }
    const int base = attacker == Color::White ? 0 : 6;  // bb index of this color's pawns
    const Bitboard pawns = board.bb[base + 0];
    const Bitboard knights = board.bb[base + 1];
    const Bitboard bishops = board.bb[base + 2];
    const Bitboard rooks = board.bb[base + 3];
    const Bitboard queens = board.bb[base + 4];
    const Bitboard king = board.bb[base + 5];

    // A white pawn attacks `square` iff it stands on one of the squares that a *black*
    // pawn on `square` would attack (and vice-versa) — so index the opposite table.
    const Bitboard pawn_from = attacker == Color::White ? g_pawn_attacks[1][square]
                                                        : g_pawn_attacks[0][square];
    if (pawn_from & pawns) {
        return true;
    }
    if (g_knight_attacks[square] & knights) {
        return true;
    }
    if (g_king_attacks[square] & king) {
        return true;
    }
    if (bishop_attacks(square, occ) & (bishops | queens)) {
        return true;
    }
    if (rook_attacks(square, occ) & (rooks | queens)) {
        return true;
    }
    return false;
}

void generate_pawn_moves(const Board& board, int square, std::vector<Move>* moves) {
    const Color color = board.side_to_move;
    const int direction = color == Color::White ? -1 : 1;
    const int start_rank = color == Color::White ? 6 : 1;
    const int promotion_rank = color == Color::White ? 0 : 7;
    const int rank = rank_of(square);
    const int file = file_of(square);
    const int one_rank = rank + direction;

    if (on_board(one_rank, file)) {
        const int one_step = index_of(one_rank, file);
        if (board.squares[one_step] == '\0') {
            if (one_rank == promotion_rank) {
                add_promotion_moves(moves, square, one_step, color);
            } else {
                add_move(moves, square, one_step);
            }

            const int two_rank = rank + (2 * direction);
            if (rank == start_rank && on_board(two_rank, file)) {
                const int two_step = index_of(two_rank, file);
                if (board.squares[two_step] == '\0') {
                    add_move(moves, square, two_step);
                }
            }
        }
    }

    for (int capture_file : {file - 1, file + 1}) {
        if (!on_board(one_rank, capture_file)) {
            continue;
        }

        const int target = index_of(one_rank, capture_file);
        if (is_enemy_piece(board.squares[target], color)) {
            if (one_rank == promotion_rank) {
                add_promotion_moves(moves, square, target, color);
            } else {
                add_move(moves, square, target);
            }
        }

        if (target == board.en_passant_square) {
            Move move;
            move.from = square;
            move.to = target;
            move.is_en_passant = true;
            moves->push_back(move);
        }
    }
}

void generate_king_moves(const Board& board, int square, std::vector<Move>* moves) {
    const Bitboard own = color_occupancy(board, board.side_to_move);
    emit_targets(square, g_king_attacks[square] & ~own, moves);

    const Color enemy = opposite(board.side_to_move);
    if (is_in_check(board, board.side_to_move)) {
        return;
    }

    if (board.side_to_move == Color::White && square == square_index('e', '1')) {
        if (board.castling.white_kingside && board.squares[square_index('f', '1')] == '\0' &&
            board.squares[square_index('g', '1')] == '\0' &&
            !is_square_attacked(board, square_index('f', '1'), enemy) &&
            !is_square_attacked(board, square_index('g', '1'), enemy)) {
            Move move;
            move.from = square;
            move.to = square_index('g', '1');
            move.is_castling = true;
            moves->push_back(move);
        }

        if (board.castling.white_queenside && board.squares[square_index('d', '1')] == '\0' &&
            board.squares[square_index('c', '1')] == '\0' && board.squares[square_index('b', '1')] == '\0' &&
            !is_square_attacked(board, square_index('d', '1'), enemy) &&
            !is_square_attacked(board, square_index('c', '1'), enemy)) {
            Move move;
            move.from = square;
            move.to = square_index('c', '1');
            move.is_castling = true;
            moves->push_back(move);
        }
    }

    if (board.side_to_move == Color::Black && square == square_index('e', '8')) {
        if (board.castling.black_kingside && board.squares[square_index('f', '8')] == '\0' &&
            board.squares[square_index('g', '8')] == '\0' &&
            !is_square_attacked(board, square_index('f', '8'), enemy) &&
            !is_square_attacked(board, square_index('g', '8'), enemy)) {
            Move move;
            move.from = square;
            move.to = square_index('g', '8');
            move.is_castling = true;
            moves->push_back(move);
        }

        if (board.castling.black_queenside && board.squares[square_index('d', '8')] == '\0' &&
            board.squares[square_index('c', '8')] == '\0' && board.squares[square_index('b', '8')] == '\0' &&
            !is_square_attacked(board, square_index('d', '8'), enemy) &&
            !is_square_attacked(board, square_index('c', '8'), enemy)) {
            Move move;
            move.from = square;
            move.to = square_index('c', '8');
            move.is_castling = true;
            moves->push_back(move);
        }
    }
}

void generate_pseudo_legal_moves(const Board& board, std::vector<Move>* moves) {
    const Bitboard own = color_occupancy(board, board.side_to_move);
    const Bitboard occ = total_occupancy(board);

    for (int square = 0; square < 64; ++square) {
        const char piece = board.squares[square];
        if (!is_color_piece(piece, board.side_to_move)) {
            continue;
        }

        switch (static_cast<char>(std::tolower(static_cast<unsigned char>(piece)))) {
            case 'p':
                generate_pawn_moves(board, square, moves);
                break;
            case 'n':
                emit_targets(square, g_knight_attacks[square] & ~own, moves);
                break;
            case 'b':
                emit_targets(square, bishop_attacks(square, occ) & ~own, moves);
                break;
            case 'r':
                emit_targets(square, rook_attacks(square, occ) & ~own, moves);
                break;
            case 'q':
                emit_targets(square, queen_attacks(square, occ) & ~own, moves);
                break;
            case 'k':
                generate_king_moves(board, square, moves);
                break;
            default:
                break;
        }
    }
}

void clear_castling_for_square(Board* board, int square) {
    if (square == square_index('e', '1')) {
        board->castling.white_kingside = false;
        board->castling.white_queenside = false;
    } else if (square == square_index('h', '1')) {
        board->castling.white_kingside = false;
    } else if (square == square_index('a', '1')) {
        board->castling.white_queenside = false;
    } else if (square == square_index('e', '8')) {
        board->castling.black_kingside = false;
        board->castling.black_queenside = false;
    } else if (square == square_index('h', '8')) {
        board->castling.black_kingside = false;
    } else if (square == square_index('a', '8')) {
        board->castling.black_queenside = false;
    }
}

// ---- Zobrist hashing (exp027) ----------------------------------------------------
// 12 piece types x 64 squares, side-to-move, 16 castling masks, 8 e.p. files.
std::uint64_t z_piece[12][64];
std::uint64_t z_side;
std::uint64_t z_castle[16];
std::uint64_t z_ep[8];

int piece_index(char piece) {
    switch (piece) {
        case 'P': return 0;  case 'N': return 1;  case 'B': return 2;
        case 'R': return 3;  case 'Q': return 4;  case 'K': return 5;
        case 'p': return 6;  case 'n': return 7;  case 'b': return 8;
        case 'r': return 9;  case 'q': return 10; case 'k': return 11;
        default:  return -1;
    }
}

int castle_mask(const CastlingRights& c) {
    return (c.white_kingside ? 1 : 0) | (c.white_queenside ? 2 : 0) |
           (c.black_kingside ? 4 : 0) | (c.black_queenside ? 8 : 0);
}

struct ZobristInit {
    ZobristInit() {
        std::uint64_t s = 0x9e3779b97f4a7c15ull;  // deterministic splitmix64 seed
        auto next = [&s]() {
            s += 0x9e3779b97f4a7c15ull;
            std::uint64_t z = s;
            z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ull;
            z = (z ^ (z >> 27)) * 0x94d049bb133111ebull;
            return z ^ (z >> 31);
        };
        for (auto& row : z_piece) {
            for (auto& v : row) {
                v = next();
            }
        }
        z_side = next();
        for (auto& v : z_castle) {
            v = next();
        }
        for (auto& v : z_ep) {
            v = next();
        }
    }
};
const ZobristInit g_zobrist_init;

}  // namespace

void rebuild_bitboards(Board& board) {
    for (int i = 0; i < 12; ++i) {
        board.bb[i] = 0;
    }
    for (int sq = 0; sq < 64; ++sq) {
        const int idx = bb_piece_index(board.squares[sq]);
        if (idx >= 0) {
            board.bb[idx] |= (Bitboard{1} << sq);
        }
    }
}

std::uint64_t compute_zobrist(const Board& board) {
    std::uint64_t h = 0;
    for (int sq = 0; sq < 64; ++sq) {
        const int idx = piece_index(board.squares[sq]);
        if (idx >= 0) {
            h ^= z_piece[idx][sq];
        }
    }
    if (board.side_to_move == Color::Black) {
        h ^= z_side;
    }
    h ^= z_castle[castle_mask(board.castling)];
    if (board.en_passant_square >= 0) {
        h ^= z_ep[board.en_passant_square % 8];
    }
    return h;
}

bool is_in_check(const Board& board, Color color) {
    return is_square_attacked(board, find_king(board, color), opposite(color));
}

namespace {

// All pieces (both colors) attacking `sq` given occupancy `occ` (recomputed each SEE
// swap so slider x-rays are handled). Restricted to currently-present pieces.
Bitboard attackers_to(const Board& board, int sq, Bitboard occ) {
    Bitboard att = 0;
    att |= g_pawn_attacks[1][sq] & board.bb[0];                       // white pawns
    att |= g_pawn_attacks[0][sq] & board.bb[6];                       // black pawns
    att |= g_knight_attacks[sq] & (board.bb[1] | board.bb[7]);
    att |= g_king_attacks[sq] & (board.bb[5] | board.bb[11]);
    const Bitboard ba = bishop_attacks(sq, occ);
    att |= ba & (board.bb[2] | board.bb[8] | board.bb[4] | board.bb[10]);
    const Bitboard ra = rook_attacks(sq, occ);
    att |= ra & (board.bb[3] | board.bb[9] | board.bb[4] | board.bb[10]);
    return att & occ;
}

int piece_type_value(char piece, const int vals[6]) {
    switch (std::tolower(static_cast<unsigned char>(piece))) {
        case 'p': return vals[0];
        case 'n': return vals[1];
        case 'b': return vals[2];
        case 'r': return vals[3];
        case 'q': return vals[4];
        case 'k': return vals[5];
        default:  return 0;
    }
}

}  // namespace

int see_capture(const Board& board, const Move& move,
                int pawn, int knight, int bishop, int rook, int queen) {
    const int vals[6] = {pawn, knight, bishop, rook, queen, 100000};
    const int to = move.to;
    const Color mover = board.side_to_move;

    Bitboard occ = 0;
    for (int i = 0; i < 12; ++i) {
        occ |= board.bb[i];
    }

    int captured_val;
    if (move.is_en_passant) {
        captured_val = pawn;
        const int ep_sq = mover == Color::White ? to + 8 : to - 8;
        occ ^= (Bitboard{1} << ep_sq);  // remove the e.p.-captured pawn
    } else {
        captured_val = piece_type_value(board.squares[to], vals);
    }

    occ ^= (Bitboard{1} << move.from);  // the mover leaves 'from', now sits on 'to'
    int on_square_val = piece_type_value(
        move.promotion != '\0' ? move.promotion : board.squares[move.from], vals);

    Bitboard attackers = attackers_to(board, to, occ);
    int gain[32];
    int d = 0;
    gain[0] = captured_val;
    Color side = mover == Color::White ? Color::Black : Color::White;

    while (true) {
        ++d;
        gain[d] = on_square_val - gain[d - 1];
        // Least valuable attacker for `side`.
        const int base = side == Color::White ? 0 : 6;
        Bitboard from_bb = 0;
        int t = -1;
        for (int pt = 0; pt < 6; ++pt) {
            const Bitboard cand = board.bb[base + pt] & attackers;
            if (cand) {
                from_bb = cand & (~cand + 1);  // pick one bit
                t = pt;
                break;
            }
        }
        if (t < 0) {
            break;  // no attacker -> sequence ends
        }
        on_square_val = vals[t];
        occ ^= from_bb;                       // that attacker captures on 'to'
        attackers = attackers_to(board, to, occ);
        side = side == Color::White ? Color::Black : Color::White;
        if (d >= 31) {
            break;
        }
    }

    while (--d > 0) {
        gain[d - 1] = -((-gain[d - 1] > gain[d]) ? -gain[d - 1] : gain[d]);
    }
    return gain[0];
}

Board make_move(const Board& board, const Move& move) {
    Board next = board;
    const char piece = board.squares[move.from];
    const char captured = board.squares[move.to];
    const Color moving_color = board.side_to_move;

    next.squares[move.from] = '\0';
    next.squares[move.to] = move.promotion != '\0' ? move.promotion : piece;

    if (move.is_en_passant) {
        const int capture_square = moving_color == Color::White ? move.to + 8 : move.to - 8;
        next.squares[capture_square] = '\0';
    }

    if (move.is_castling) {
        if (move.to == square_index('g', '1')) {
            next.squares[square_index('h', '1')] = '\0';
            next.squares[square_index('f', '1')] = 'R';
        } else if (move.to == square_index('c', '1')) {
            next.squares[square_index('a', '1')] = '\0';
            next.squares[square_index('d', '1')] = 'R';
        } else if (move.to == square_index('g', '8')) {
            next.squares[square_index('h', '8')] = '\0';
            next.squares[square_index('f', '8')] = 'r';
        } else if (move.to == square_index('c', '8')) {
            next.squares[square_index('a', '8')] = '\0';
            next.squares[square_index('d', '8')] = 'r';
        }
    }

    clear_castling_for_square(&next, move.from);
    clear_castling_for_square(&next, move.to);

    next.en_passant_square = -1;
    if (piece == 'P' && move.from - move.to == 16) {
        next.en_passant_square = move.from - 8;
    } else if (piece == 'p' && move.to - move.from == 16) {
        next.en_passant_square = move.from + 8;
    }

    if (piece == 'P' || piece == 'p' || captured != '\0' || move.is_en_passant) {
        next.halfmove_clock = 0;
    } else {
        ++next.halfmove_clock;
    }

    if (moving_color == Color::Black) {
        ++next.fullmove_number;
    }

    next.side_to_move = opposite(moving_color);
    next.zobrist = compute_zobrist(next);  // copy path is not hot; recompute for validity
    rebuild_bitboards(next);
    return next;
}

Undo make_move_inplace(Board& board, const Move& move) {
    Undo undo;
    undo.castling = board.castling;
    undo.en_passant_square = board.en_passant_square;
    undo.halfmove_clock = board.halfmove_clock;
    undo.fullmove_number = board.fullmove_number;
    undo.zobrist = board.zobrist;

    const char piece = board.squares[move.from];
    undo.moved = piece;
    const Color moving_color = board.side_to_move;

    // Incrementally update the Zobrist key: start from the current key, remove the old
    // castling/e.p. state, then XOR each piece move as it happens, flip side, and add the
    // new castling/e.p. state at the end.
    std::uint64_t h = board.zobrist;
    h ^= z_castle[castle_mask(board.castling)];
    if (board.en_passant_square >= 0) {
        h ^= z_ep[board.en_passant_square % 8];
    }

    char captured = '\0';
    int captured_square = -1;
    if (move.is_en_passant) {
        captured_square = moving_color == Color::White ? move.to + 8 : move.to - 8;
        captured = board.squares[captured_square];
        board.squares[captured_square] = '\0';
    } else if (board.squares[move.to] != '\0') {
        captured = board.squares[move.to];
        captured_square = move.to;
    }
    undo.captured = captured;
    undo.captured_square = captured_square;
    if (captured != '\0') {
        h ^= z_piece[piece_index(captured)][captured_square];
        board.bb[bb_piece_index(captured)] &= ~(Bitboard{1} << captured_square);
    }

    const char placed = move.promotion != '\0' ? move.promotion : piece;
    h ^= z_piece[piece_index(piece)][move.from];  // lift moving piece off 'from'
    h ^= z_piece[piece_index(placed)][move.to];   // place (possibly promoted) on 'to'
    board.bb[bb_piece_index(piece)] &= ~(Bitboard{1} << move.from);
    board.bb[bb_piece_index(placed)] |= (Bitboard{1} << move.to);
    board.squares[move.from] = '\0';
    board.squares[move.to] = placed;

    if (move.is_castling) {
        int rook_from = -1;
        int rook_to = -1;
        char rook = 'R';
        if (move.to == square_index('g', '1')) {
            rook_from = square_index('h', '1'); rook_to = square_index('f', '1'); rook = 'R';
        } else if (move.to == square_index('c', '1')) {
            rook_from = square_index('a', '1'); rook_to = square_index('d', '1'); rook = 'R';
        } else if (move.to == square_index('g', '8')) {
            rook_from = square_index('h', '8'); rook_to = square_index('f', '8'); rook = 'r';
        } else if (move.to == square_index('c', '8')) {
            rook_from = square_index('a', '8'); rook_to = square_index('d', '8'); rook = 'r';
        }
        board.squares[rook_from] = '\0';
        board.squares[rook_to] = rook;
        h ^= z_piece[piece_index(rook)][rook_from];
        h ^= z_piece[piece_index(rook)][rook_to];
        board.bb[bb_piece_index(rook)] &= ~(Bitboard{1} << rook_from);
        board.bb[bb_piece_index(rook)] |= (Bitboard{1} << rook_to);
    }

    clear_castling_for_square(&board, move.from);
    clear_castling_for_square(&board, move.to);

    board.en_passant_square = -1;
    if (piece == 'P' && move.from - move.to == 16) {
        board.en_passant_square = move.from - 8;
    } else if (piece == 'p' && move.to - move.from == 16) {
        board.en_passant_square = move.from + 8;
    }

    if (piece == 'P' || piece == 'p' || captured != '\0') {
        board.halfmove_clock = 0;
    } else {
        ++board.halfmove_clock;
    }

    if (moving_color == Color::Black) {
        ++board.fullmove_number;
    }

    board.side_to_move = opposite(moving_color);

    // Add new castling/e.p. state and the side-to-move flip.
    h ^= z_castle[castle_mask(board.castling)];
    if (board.en_passant_square >= 0) {
        h ^= z_ep[board.en_passant_square % 8];
    }
    h ^= z_side;
    board.zobrist = h;
    return undo;
}

void unmake_move(Board& board, const Move& move, const Undo& undo) {
    const Color moved_color = opposite(board.side_to_move);  // side that made the move
    board.side_to_move = moved_color;
    board.castling = undo.castling;
    board.en_passant_square = undo.en_passant_square;
    board.halfmove_clock = undo.halfmove_clock;
    board.fullmove_number = undo.fullmove_number;
    board.zobrist = undo.zobrist;

    // Restore bitboards: lift the placed piece off 'to', put the original mover back on
    // 'from', and restore any captured piece.
    const char placed = move.promotion != '\0' ? move.promotion : undo.moved;
    board.bb[bb_piece_index(placed)] &= ~(Bitboard{1} << move.to);
    board.bb[bb_piece_index(undo.moved)] |= (Bitboard{1} << move.from);
    if (undo.captured != '\0') {
        board.bb[bb_piece_index(undo.captured)] |= (Bitboard{1} << undo.captured_square);
    }

    board.squares[move.from] = undo.moved;
    board.squares[move.to] = '\0';
    if (undo.captured != '\0') {
        board.squares[undo.captured_square] = undo.captured;
    }

    if (move.is_castling) {
        int rook_from = -1;
        int rook_to = -1;
        char rook = 'R';
        if (move.to == square_index('g', '1')) {
            rook_from = square_index('h', '1'); rook_to = square_index('f', '1'); rook = 'R';
        } else if (move.to == square_index('c', '1')) {
            rook_from = square_index('a', '1'); rook_to = square_index('d', '1'); rook = 'R';
        } else if (move.to == square_index('g', '8')) {
            rook_from = square_index('h', '8'); rook_to = square_index('f', '8'); rook = 'r';
        } else if (move.to == square_index('c', '8')) {
            rook_from = square_index('a', '8'); rook_to = square_index('d', '8'); rook = 'r';
        }
        board.squares[rook_to] = '\0';
        board.squares[rook_from] = rook;
        board.bb[bb_piece_index(rook)] &= ~(Bitboard{1} << rook_to);
        board.bb[bb_piece_index(rook)] |= (Bitboard{1} << rook_from);
    }
}

std::vector<Move> generate_legal_moves(const Board& board) {
    std::vector<Move> pseudo_moves;
    pseudo_moves.reserve(64);
    generate_pseudo_legal_moves(board, &pseudo_moves);

    // Legality = our king not attacked after the move. Find our king once; it only
    // moves when the king itself moves, so the post-move king square is O(1). One
    // mutable copy of the board is made/unmade per pseudo move (no per-move copy).
    const Color us = board.side_to_move;
    const Color enemy = opposite(us);
    const int king_square = find_king(board, us);

    std::vector<Move> legal_moves;
    legal_moves.reserve(pseudo_moves.size());
    Board work = board;
    for (const Move& move : pseudo_moves) {
        const Undo undo = make_move_inplace(work, move);
        const int king_sq = (move.from == king_square) ? move.to : king_square;
        if (!is_square_attacked(work, king_sq, enemy)) {
            legal_moves.push_back(move);
        }
        unmake_move(work, move, undo);
    }

    return legal_moves;
}

std::uint64_t perft(const Board& board, int depth) {
    if (depth < 0) {
        throw std::invalid_argument("perft depth must be non-negative");
    }

    if (depth == 0) {
        return 1;
    }

    const std::vector<Move> moves = generate_legal_moves(board);
    if (depth == 1) {
        return moves.size();
    }

    std::uint64_t nodes = 0;
    Board work = board;
    for (const Move& move : moves) {
        const Undo undo = make_move_inplace(work, move);
        nodes += perft(work, depth - 1);
        unmake_move(work, move, undo);
    }

    return nodes;
}

std::string move_to_uci(const Move& move) {
    std::string text = square_name(move.from) + square_name(move.to);
    if (move.promotion != '\0') {
        text.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(move.promotion))));
    }
    return text;
}

bool try_parse_uci_move(const Board& board, const std::string& text, Move* move) {
    const std::vector<Move> legal_moves = generate_legal_moves(board);

    for (const Move& legal_move : legal_moves) {
        if (move_to_uci(legal_move) == text) {
            if (move != nullptr) {
                *move = legal_move;
            }
            return true;
        }
    }

    return false;
}

}  // namespace checkforge
