#include "checkforge/search.h"

#include <algorithm>
#include <cctype>
#include <limits>
#include <vector>

#include "checkforge/eval.h"

namespace checkforge {
namespace {

constexpr int kMateScore = 100000;
constexpr int kInfinity = 1000000;

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
        case 'k':
            return 20000;
        default:
            return 0;
    }
}

void order_moves(const Board& board, const EngineConfig& config, std::vector<Move>* moves) {
    std::stable_sort(moves->begin(), moves->end(), [&board, &config](const Move& left, const Move& right) {
        const int left_capture = piece_value(board.squares[left.to], config);
        const int right_capture = piece_value(board.squares[right.to], config);
        const int left_promotion = piece_value(left.promotion, config);
        const int right_promotion = piece_value(right.promotion, config);
        return (left_capture + left_promotion) > (right_capture + right_promotion);
    });
}

bool is_capture_or_promotion(const Board& board, const Move& move) {
    return board.squares[move.to] != '\0' || move.is_en_passant || move.promotion != '\0';
}

int quiescence(const Board& board, int alpha, int beta, int remaining_depth, const EngineConfig& config) {
    const int stand_pat = evaluate_static_for_side_to_move(board, config);
    if (stand_pat >= beta) {
        return beta;
    }
    if (stand_pat > alpha) {
        alpha = stand_pat;
    }

    if (remaining_depth <= 0) {
        return stand_pat;
    }

    std::vector<Move> moves = generate_legal_moves(board);
    order_moves(board, config, &moves);

    for (const Move& move : moves) {
        if (!is_capture_or_promotion(board, move)) {
            continue;
        }

        const Board next = make_move(board, move);
        const int score = -quiescence(next, -beta, -alpha, remaining_depth - 1, config);
        if (score >= beta) {
            return beta;
        }
        if (score > alpha) {
            alpha = score;
        }
    }

    return alpha;
}

int negamax(const Board& board, int depth, int alpha, int beta, int ply, const EngineConfig& config) {
    std::vector<Move> moves = generate_legal_moves(board);

    if (moves.empty()) {
        if (is_in_check(board, board.side_to_move)) {
            return -kMateScore + ply;
        }
        return 0;
    }

    if (depth == 0 && is_in_check(board, board.side_to_move)) {
        depth = 1;
    }

    if (depth == 0) {
        return quiescence(board, alpha, beta, config.quiescence_depth, config);
    }

    order_moves(board, config, &moves);

    int best_score = -kInfinity;
    for (const Move& move : moves) {
        const Board next = make_move(board, move);
        const int score = -negamax(next, depth - 1, -beta, -alpha, ply + 1, config);
        best_score = std::max(best_score, score);
        alpha = std::max(alpha, score);
        if (alpha >= beta) {
            break;
        }
    }

    return best_score;
}

}  // namespace

SearchResult search_bestmove(const Board& board, int depth) {
    return search_bestmove(board, depth, default_config());
}

SearchResult search_bestmove(const Board& board, int depth, const EngineConfig& config) {
    if (depth < 1) {
        depth = 1;
    }

    std::vector<Move> moves = generate_legal_moves(board);
    SearchResult result;
    result.depth = depth;

    if (moves.empty()) {
        result.score = is_in_check(board, board.side_to_move) ? -kMateScore : 0;
        return result;
    }

    order_moves(board, config, &moves);

    int alpha = -kInfinity;
    const int beta = kInfinity;
    for (const Move& move : moves) {
        const Board next = make_move(board, move);
        const int score = -negamax(next, depth - 1, -beta, -alpha, 1, config);
        if (!result.has_move || score > result.score) {
            result.best_move = move;
            result.score = score;
            result.has_move = true;
        }
        alpha = std::max(alpha, score);
    }

    return result;
}

}  // namespace checkforge
