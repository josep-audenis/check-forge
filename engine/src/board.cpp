#include "checkforge/board.h"

#include "checkforge/movegen.h"

#include <cctype>
#include <cstdlib>
#include <stdexcept>
#include <vector>

namespace checkforge {
namespace {

constexpr const char* kStartFen =
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

bool is_piece(char value) {
    switch (value) {
        case 'P':
        case 'N':
        case 'B':
        case 'R':
        case 'Q':
        case 'K':
        case 'p':
        case 'n':
        case 'b':
        case 'r':
        case 'q':
        case 'k':
            return true;
        default:
            return false;
    }
}

std::vector<std::string> split_spaces(const std::string& text) {
    std::vector<std::string> parts;
    std::string current;

    for (char ch : text) {
        if (ch == ' ') {
            if (!current.empty()) {
                parts.push_back(current);
                current.clear();
            }
            continue;
        }
        current.push_back(ch);
    }

    if (!current.empty()) {
        parts.push_back(current);
    }

    return parts;
}

int parse_non_negative_int(const std::string& value, const char* field) {
    if (value.empty()) {
        throw std::invalid_argument(std::string("missing ") + field);
    }

    for (char ch : value) {
        if (!std::isdigit(static_cast<unsigned char>(ch))) {
            throw std::invalid_argument(std::string("invalid ") + field);
        }
    }

    return std::atoi(value.c_str());
}

void parse_piece_placement(const std::string& placement, Board* board) {
    int rank = 7;
    int file = 0;
    int white_kings = 0;
    int black_kings = 0;

    for (char ch : placement) {
        if (ch == '/') {
            if (file != 8 || rank == 0) {
                throw std::invalid_argument("invalid FEN piece placement");
            }
            --rank;
            file = 0;
            continue;
        }

        if (std::isdigit(static_cast<unsigned char>(ch))) {
            int empty_count = ch - '0';
            if (empty_count < 1 || empty_count > 8 || file + empty_count > 8) {
                throw std::invalid_argument("invalid FEN empty square count");
            }
            file += empty_count;
            continue;
        }

        if (!is_piece(ch) || file >= 8) {
            throw std::invalid_argument("invalid FEN piece");
        }

        int index = (7 - rank) * 8 + file;
        board->squares[index] = ch;
        white_kings += ch == 'K' ? 1 : 0;
        black_kings += ch == 'k' ? 1 : 0;
        ++file;
    }

    if (rank != 0 || file != 8) {
        throw std::invalid_argument("invalid FEN board shape");
    }

    if (white_kings != 1 || black_kings != 1) {
        throw std::invalid_argument("FEN must contain one white king and one black king");
    }
}

CastlingRights parse_castling(const std::string& value) {
    CastlingRights rights;

    if (value == "-") {
        return rights;
    }

    for (char ch : value) {
        switch (ch) {
            case 'K':
                if (rights.white_kingside) {
                    throw std::invalid_argument("duplicate castling right");
                }
                rights.white_kingside = true;
                break;
            case 'Q':
                if (rights.white_queenside) {
                    throw std::invalid_argument("duplicate castling right");
                }
                rights.white_queenside = true;
                break;
            case 'k':
                if (rights.black_kingside) {
                    throw std::invalid_argument("duplicate castling right");
                }
                rights.black_kingside = true;
                break;
            case 'q':
                if (rights.black_queenside) {
                    throw std::invalid_argument("duplicate castling right");
                }
                rights.black_queenside = true;
                break;
            default:
                throw std::invalid_argument("invalid castling right");
        }
    }

    return rights;
}

int parse_en_passant(const std::string& value) {
    if (value == "-") {
        return -1;
    }

    if (value.size() != 2 || value[0] < 'a' || value[0] > 'h' ||
        (value[1] != '3' && value[1] != '6')) {
        throw std::invalid_argument("invalid en passant square");
    }

    return square_index(value[0], value[1]);
}

}  // namespace

Board Board::startpos() {
    return Board::from_fen(kStartFen);
}

Board Board::from_fen(const std::string& fen) {
    std::string normalized = fen == "startpos" ? kStartFen : fen;
    std::vector<std::string> parts = split_spaces(normalized);

    if (parts.size() != 6) {
        throw std::invalid_argument("FEN must contain six fields");
    }

    Board board;
    parse_piece_placement(parts[0], &board);

    if (parts[1] == "w") {
        board.side_to_move = Color::White;
    } else if (parts[1] == "b") {
        board.side_to_move = Color::Black;
    } else {
        throw std::invalid_argument("invalid side to move");
    }

    board.castling = parse_castling(parts[2]);
    board.en_passant_square = parse_en_passant(parts[3]);
    board.halfmove_clock = parse_non_negative_int(parts[4], "halfmove clock");
    board.fullmove_number = parse_non_negative_int(parts[5], "fullmove number");

    if (board.fullmove_number < 1) {
        throw std::invalid_argument("fullmove number must be positive");
    }

    board.zobrist = compute_zobrist(board);
    return board;
}

std::string Board::to_fen() const {
    std::string result;

    for (int rank = 7; rank >= 0; --rank) {
        int empty_count = 0;
        for (int file = 0; file < 8; ++file) {
            int index = (7 - rank) * 8 + file;
            char piece = squares[index];
            if (piece == '\0') {
                ++empty_count;
                continue;
            }

            if (empty_count > 0) {
                result.push_back(static_cast<char>('0' + empty_count));
                empty_count = 0;
            }
            result.push_back(piece);
        }

        if (empty_count > 0) {
            result.push_back(static_cast<char>('0' + empty_count));
        }

        if (rank > 0) {
            result.push_back('/');
        }
    }

    result += side_to_move == Color::White ? " w " : " b ";

    std::string castling_text;
    if (castling.white_kingside) {
        castling_text.push_back('K');
    }
    if (castling.white_queenside) {
        castling_text.push_back('Q');
    }
    if (castling.black_kingside) {
        castling_text.push_back('k');
    }
    if (castling.black_queenside) {
        castling_text.push_back('q');
    }
    result += castling_text.empty() ? "-" : castling_text;

    result.push_back(' ');
    result += en_passant_square == -1 ? "-" : square_name(en_passant_square);
    result.push_back(' ');
    result += std::to_string(halfmove_clock);
    result.push_back(' ');
    result += std::to_string(fullmove_number);

    return result;
}

char Board::piece_at(int square) const {
    if (square < 0 || square >= 64) {
        throw std::out_of_range("square index out of range");
    }

    return squares[square];
}

int square_index(char file, char rank) {
    if (file < 'a' || file > 'h' || rank < '1' || rank > '8') {
        throw std::invalid_argument("invalid square name");
    }

    int file_index = file - 'a';
    int rank_index = '8' - rank;
    return rank_index * 8 + file_index;
}

std::string square_name(int square) {
    if (square < 0 || square >= 64) {
        throw std::out_of_range("square index out of range");
    }

    int file = square % 8;
    int rank = 8 - (square / 8);
    std::string name;
    name.push_back(static_cast<char>('a' + file));
    name.push_back(static_cast<char>('0' + rank));
    return name;
}

}  // namespace checkforge
