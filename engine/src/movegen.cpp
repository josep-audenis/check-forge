#include "checkforge/movegen.h"

#include <cctype>
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

bool attacks_by_pawn(const Board& board, int square, Color attacker) {
    const int rank = rank_of(square);
    const int file = file_of(square);
    const int pawn_rank = attacker == Color::White ? rank + 1 : rank - 1;
    const char pawn = attacker == Color::White ? 'P' : 'p';

    for (int pawn_file : {file - 1, file + 1}) {
        if (on_board(pawn_rank, pawn_file) && board.squares[index_of(pawn_rank, pawn_file)] == pawn) {
            return true;
        }
    }

    return false;
}

bool attacks_by_knight(const Board& board, int square, Color attacker) {
    const int offsets[8][2] = {
        {-2, -1}, {-2, 1}, {-1, -2}, {-1, 2},
        {1, -2},  {1, 2},  {2, -1},  {2, 1},
    };
    const int rank = rank_of(square);
    const int file = file_of(square);
    const char knight = attacker == Color::White ? 'N' : 'n';

    for (const auto& offset : offsets) {
        const int target_rank = rank + offset[0];
        const int target_file = file + offset[1];
        if (on_board(target_rank, target_file) && board.squares[index_of(target_rank, target_file)] == knight) {
            return true;
        }
    }

    return false;
}

bool attacks_by_king(const Board& board, int square, Color attacker) {
    const int rank = rank_of(square);
    const int file = file_of(square);
    const char king = attacker == Color::White ? 'K' : 'k';

    for (int rank_delta = -1; rank_delta <= 1; ++rank_delta) {
        for (int file_delta = -1; file_delta <= 1; ++file_delta) {
            if (rank_delta == 0 && file_delta == 0) {
                continue;
            }

            const int target_rank = rank + rank_delta;
            const int target_file = file + file_delta;
            if (on_board(target_rank, target_file) && board.squares[index_of(target_rank, target_file)] == king) {
                return true;
            }
        }
    }

    return false;
}

bool attacks_by_slider(const Board& board, int square, Color attacker, const int directions[][2], int direction_count, char piece_a, char piece_b) {
    const int start_rank = rank_of(square);
    const int start_file = file_of(square);
    const char attacker_a = attacker == Color::White ? piece_a : static_cast<char>(std::tolower(static_cast<unsigned char>(piece_a)));
    const char attacker_b = attacker == Color::White ? piece_b : static_cast<char>(std::tolower(static_cast<unsigned char>(piece_b)));

    for (int i = 0; i < direction_count; ++i) {
        int current_rank = start_rank + directions[i][0];
        int current_file = start_file + directions[i][1];

        while (on_board(current_rank, current_file)) {
            const char piece = board.squares[index_of(current_rank, current_file)];
            if (piece != '\0') {
                if (piece == attacker_a || piece == attacker_b) {
                    return true;
                }
                break;
            }

            current_rank += directions[i][0];
            current_file += directions[i][1];
        }
    }

    return false;
}

bool is_square_attacked(const Board& board, int square, Color attacker) {
    const int bishop_dirs[4][2] = {{-1, -1}, {-1, 1}, {1, -1}, {1, 1}};
    const int rook_dirs[4][2] = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};

    return attacks_by_pawn(board, square, attacker) ||
           attacks_by_knight(board, square, attacker) ||
           attacks_by_king(board, square, attacker) ||
           attacks_by_slider(board, square, attacker, bishop_dirs, 4, 'B', 'Q') ||
           attacks_by_slider(board, square, attacker, rook_dirs, 4, 'R', 'Q');
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

void generate_knight_moves(const Board& board, int square, std::vector<Move>* moves) {
    const int offsets[8][2] = {
        {-2, -1}, {-2, 1}, {-1, -2}, {-1, 2},
        {1, -2},  {1, 2},  {2, -1},  {2, 1},
    };
    const int rank = rank_of(square);
    const int file = file_of(square);

    for (const auto& offset : offsets) {
        const int target_rank = rank + offset[0];
        const int target_file = file + offset[1];
        if (!on_board(target_rank, target_file)) {
            continue;
        }

        const int target = index_of(target_rank, target_file);
        if (!is_color_piece(board.squares[target], board.side_to_move)) {
            add_move(moves, square, target);
        }
    }
}

void generate_sliding_moves(const Board& board, int square, const int directions[][2], int direction_count, std::vector<Move>* moves) {
    const int start_rank = rank_of(square);
    const int start_file = file_of(square);

    for (int i = 0; i < direction_count; ++i) {
        int current_rank = start_rank + directions[i][0];
        int current_file = start_file + directions[i][1];

        while (on_board(current_rank, current_file)) {
            const int target = index_of(current_rank, current_file);
            if (is_color_piece(board.squares[target], board.side_to_move)) {
                break;
            }

            add_move(moves, square, target);

            if (is_enemy_piece(board.squares[target], board.side_to_move)) {
                break;
            }

            current_rank += directions[i][0];
            current_file += directions[i][1];
        }
    }
}

void generate_king_moves(const Board& board, int square, std::vector<Move>* moves) {
    const int rank = rank_of(square);
    const int file = file_of(square);

    for (int rank_delta = -1; rank_delta <= 1; ++rank_delta) {
        for (int file_delta = -1; file_delta <= 1; ++file_delta) {
            if (rank_delta == 0 && file_delta == 0) {
                continue;
            }

            const int target_rank = rank + rank_delta;
            const int target_file = file + file_delta;
            if (!on_board(target_rank, target_file)) {
                continue;
            }

            const int target = index_of(target_rank, target_file);
            if (!is_color_piece(board.squares[target], board.side_to_move)) {
                add_move(moves, square, target);
            }
        }
    }

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
    const int bishop_dirs[4][2] = {{-1, -1}, {-1, 1}, {1, -1}, {1, 1}};
    const int rook_dirs[4][2] = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};
    const int queen_dirs[8][2] = {{-1, -1}, {-1, 1}, {1, -1}, {1, 1}, {-1, 0}, {1, 0}, {0, -1}, {0, 1}};

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
                generate_knight_moves(board, square, moves);
                break;
            case 'b':
                generate_sliding_moves(board, square, bishop_dirs, 4, moves);
                break;
            case 'r':
                generate_sliding_moves(board, square, rook_dirs, 4, moves);
                break;
            case 'q':
                generate_sliding_moves(board, square, queen_dirs, 8, moves);
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

}  // namespace

bool is_in_check(const Board& board, Color color) {
    return is_square_attacked(board, find_king(board, color), opposite(color));
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
    return next;
}

std::vector<Move> generate_legal_moves(const Board& board) {
    std::vector<Move> pseudo_moves;
    generate_pseudo_legal_moves(board, &pseudo_moves);

    std::vector<Move> legal_moves;
    for (const Move& move : pseudo_moves) {
        const Board next = make_move(board, move);
        if (!is_in_check(next, board.side_to_move)) {
            legal_moves.push_back(move);
        }
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
    for (const Move& move : moves) {
        nodes += perft(make_move(board, move), depth - 1);
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
