#include "checkforge/search.h"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cstdlib>
#include <limits>
#include <vector>

#include "checkforge/eval.h"

// Use the Win32 millisecond tick counter directly. The libstdc++ <chrono>
// backend on this msys2/ucrt toolchain transitively includes sys/timeb.h ->
// features.h, which is absent here. Declaring GetTickCount64 extern avoids
// pulling in <windows.h> (and its min/max macros).
extern "C" __declspec(dllimport) unsigned long long __stdcall GetTickCount64(void);

namespace checkforge {
namespace {

using ms_t = unsigned long long;

ms_t now_ms() {
    return GetTickCount64();
}

constexpr int kMateScore = 100000;
constexpr int kInfinity = 1000000;
constexpr int kMateZone = kMateScore - 1000;  // scores above this are mate distances

// Transposition table: cache the search result of positions so iterative
// deepening can reuse shallower work and reach greater depth in the same time.
constexpr std::uint64_t kTTSize = 1u << 20;  // power of two for masking
constexpr std::uint64_t kTTMask = kTTSize - 1;

enum TTFlag : std::int16_t { kTTExact = 0, kTTLower = 1, kTTUpper = 2 };

struct TTEntry {
    std::uint64_t key = 0;
    std::int32_t score = 0;
    std::int16_t depth = -1;
    std::int16_t flag = kTTExact;
    Move best{};  // best move found here, used as a search-ordering hint
};

thread_local std::vector<TTEntry> g_tt;

void tt_reset() {
    if (g_tt.size() != kTTSize) {
        g_tt.assign(kTTSize, TTEntry{});
    } else {
        std::fill(g_tt.begin(), g_tt.end(), TTEntry{});
    }
}

std::uint64_t hash_board(const Board& board) {
    std::uint64_t h = 1469598103934665603ull;  // FNV-1a
    for (char c : board.squares) {
        h ^= static_cast<unsigned char>(c);
        h *= 1099511628211ull;
    }
    if (board.side_to_move == Color::Black) {
        h ^= 0x9e3779b97f4a7c15ull;
    }
    h ^= static_cast<std::uint64_t>(board.en_passant_square + 1) * 0x100000001b3ull;
    const std::uint64_t cr =
        (board.castling.white_kingside ? 1u : 0u) | (board.castling.white_queenside ? 2u : 0u) |
        (board.castling.black_kingside ? 4u : 0u) | (board.castling.black_queenside ? 8u : 0u);
    h ^= cr * 0xff51afd7ed558ccdull;
    return h;
}

// State threaded through the recursive search. For fixed-depth search
// time_limited is false, so the deadline checks are inert and traversal is
// identical to a plain alpha-beta. For timed search the deadline aborts the
// current iteration; partial results from an aborted depth are discarded.
struct SearchContext {
    const EngineConfig& config;
    bool time_limited = false;
    ms_t deadline = 0;
    long nodes = 0;
    bool aborted = false;
};

bool out_of_time(SearchContext* ctx) {
    if (!ctx->time_limited) {
        return false;
    }
    // Once aborted, stay aborted so the signal propagates up immediately
    // instead of only on the next poll tick.
    if (ctx->aborted) {
        return true;
    }
    // Only read the clock periodically to keep the hot path cheap.
    if ((ctx->nodes++ & 2047) == 0 && now_ms() >= ctx->deadline) {
        ctx->aborted = true;
    }
    return ctx->aborted;
}

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

// Side has at least one knight/bishop/rook/queen — used to gate null-move pruning,
// which is unsound in (near-)zugzwang king-and-pawn positions.
bool has_non_pawn_material(const Board& board, Color color) {
    for (char piece : board.squares) {
        if (piece == '\0') {
            continue;
        }
        const bool white = piece >= 'A' && piece <= 'Z';
        if ((color == Color::White) != white) {
            continue;
        }
        switch (static_cast<char>(std::tolower(static_cast<unsigned char>(piece)))) {
            case 'n': case 'b': case 'r': case 'q':
                return true;
            default:
                break;
        }
    }
    return false;
}

int move_order_key(const Board& board, const EngineConfig& config, const Move& move) {
    const int victim = piece_value(board.squares[move.to], config);
    const int promotion = piece_value(move.promotion, config);
    if (victim == 0 && promotion == 0) {
        return 0;  // quiet move
    }
    // MVV-LVA: most valuable victim first, least valuable attacker breaks ties.
    const int attacker = piece_value(board.squares[move.from], config);
    return ((victim + promotion) * 100) - attacker;
}

void order_moves(const Board& board, const EngineConfig& config, std::vector<Move>* moves) {
    std::stable_sort(moves->begin(), moves->end(), [&board, &config](const Move& left, const Move& right) {
        return move_order_key(board, config, left) > move_order_key(board, config, right);
    });
}

bool is_capture_or_promotion(const Board& board, const Move& move) {
    return board.squares[move.to] != '\0' || move.is_en_passant || move.promotion != '\0';
}

bool same_move(const Move& a, const Move& b) {
    return a.from == b.from && a.to == b.to && a.promotion == b.promotion;
}

// Move a known-good move to the front of an already-ordered list.
void promote_move_to_front(const Move& hint, std::vector<Move>* moves) {
    if (hint.from < 0) {
        return;
    }
    const auto it = std::find_if(moves->begin(), moves->end(),
                                 [&hint](const Move& m) { return same_move(m, hint); });
    if (it != moves->end()) {
        std::rotate(moves->begin(), it, it + 1);
    }
}

int quiescence(const Board& board, int alpha, int beta, int remaining_depth, SearchContext* ctx) {
    const int stand_pat = evaluate_static_for_side_to_move(board, ctx->config);
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
    order_moves(board, ctx->config, &moves);

    for (const Move& move : moves) {
        if (!is_capture_or_promotion(board, move)) {
            continue;
        }
        if (out_of_time(ctx)) {
            return alpha;
        }

        const Board next = make_move(board, move);
        const int score = -quiescence(next, -beta, -alpha, remaining_depth - 1, ctx);
        if (score >= beta) {
            return beta;
        }
        if (score > alpha) {
            alpha = score;
        }
    }

    return alpha;
}

int negamax(const Board& board, int depth, int alpha, int beta, int ply, SearchContext* ctx) {
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
        return quiescence(board, alpha, beta, ctx->config.quiescence_depth, ctx);
    }

    // Transposition table probe. Reuse a stored result only when it was searched
    // at least as deep and its bound is usable against the current window.
    const std::uint64_t key = hash_board(board);
    const int alpha_orig = alpha;
    TTEntry& entry = g_tt[key & kTTMask];
    Move tt_move{};
    if (entry.key == key) {
        tt_move = entry.best;  // ordering hint even when the bound is unusable
        if (entry.depth >= depth) {
            if (entry.flag == kTTExact) {
                return entry.score;
            }
            if (entry.flag == kTTLower && entry.score >= beta) {
                return entry.score;
            }
            if (entry.flag == kTTUpper && entry.score <= alpha) {
                return entry.score;
            }
        }
    }

    // Null-move pruning: if passing the move (a free tempo for the opponent) still fails
    // high, the position is so good that a real move surely does too — prune. Skipped at
    // PV/full-window nodes (beta is a mate/infinity bound there), when in check, at low
    // depth, and without non-pawn material (zugzwang).
    constexpr int kNullReduction = 2;
    if (depth >= 3 && beta < kMateZone &&
        has_non_pawn_material(board, board.side_to_move) &&
        !is_in_check(board, board.side_to_move)) {
        Board null_board = board;
        null_board.side_to_move = board.side_to_move == Color::White ? Color::Black : Color::White;
        null_board.en_passant_square = -1;
        const int null_score = -negamax(null_board, depth - 1 - kNullReduction,
                                        -beta, -beta + 1, ply + 1, ctx);
        if (!ctx->aborted && null_score >= beta) {
            return beta;
        }
    }

    order_moves(board, ctx->config, &moves);
    promote_move_to_front(tt_move, &moves);

    int best_score = -kInfinity;
    Move best_move{};
    for (const Move& move : moves) {
        if (out_of_time(ctx)) {
            break;
        }
        const Board next = make_move(board, move);
        const int score = -negamax(next, depth - 1, -beta, -alpha, ply + 1, ctx);
        if (score > best_score) {
            best_score = score;
            best_move = move;
        }
        alpha = std::max(alpha, score);
        if (alpha >= beta) {
            break;
        }
    }

    // Store, unless aborted (partial) or the score is a mate distance (those need
    // ply-relative correction this simple table does not track).
    if (!ctx->aborted && std::abs(best_score) < kMateZone) {
        const std::int16_t flag = best_score <= alpha_orig ? kTTUpper
                                  : best_score >= beta     ? kTTLower
                                                           : kTTExact;
        if (entry.key != key || depth >= entry.depth) {
            entry = TTEntry{key, static_cast<std::int32_t>(best_score),
                            static_cast<std::int16_t>(depth), flag, best_move};
        }
    }

    return best_score;
}

// Run a full-width root search at a single depth using the given context.
SearchResult search_root(const Board& board, int depth, SearchContext* ctx) {
    SearchResult result;
    result.depth = depth;

    std::vector<Move> moves = generate_legal_moves(board);
    if (moves.empty()) {
        result.score = is_in_check(board, board.side_to_move) ? -kMateScore : 0;
        return result;
    }

    order_moves(board, ctx->config, &moves);

    const std::uint64_t key = hash_board(board);
    const TTEntry& entry = g_tt[key & kTTMask];
    if (entry.key == key) {
        promote_move_to_front(entry.best, &moves);
    }

    int alpha = -kInfinity;
    const int beta = kInfinity;
    for (const Move& move : moves) {
        if (out_of_time(ctx)) {
            break;
        }
        const Board next = make_move(board, move);
        const int score = -negamax(next, depth - 1, -beta, -alpha, 1, ctx);
        if (!result.has_move || score > result.score) {
            result.best_move = move;
            result.score = score;
            result.has_move = true;
        }
        alpha = std::max(alpha, score);
    }

    return result;
}

}  // namespace

SearchResult search_bestmove(const Board& board, int depth) {
    return search_bestmove(board, depth, default_config());
}

SearchResult search_bestmove(const Board& board, int depth, const EngineConfig& config) {
    if (depth < 1) {
        depth = 1;
    }
    tt_reset();
    SearchContext ctx{config};
    return search_root(board, depth, &ctx);
}

SearchResult search_bestmove_timed(const Board& board, int max_depth, long budget_ms, const EngineConfig& config) {
    if (max_depth < 1) {
        max_depth = 1;
    }
    if (budget_ms < 1) {
        budget_ms = 1;
    }

    tt_reset();
    SearchContext ctx{config};
    ctx.time_limited = true;
    ctx.deadline = now_ms() + static_cast<ms_t>(budget_ms);

    // Depth 1 is cheap and always completes, guaranteeing a legal move.
    SearchResult best = search_root(board, 1, &ctx);

    for (int depth = 2; depth <= max_depth; ++depth) {
        const SearchResult candidate = search_root(board, depth, &ctx);
        if (ctx.aborted) {
            break;  // discard partial iteration, keep last completed depth
        }
        best = candidate;
        // A forced mate this side cannot be improved by searching deeper.
        if (best.score >= kMateScore - 1000 || best.score <= -kMateScore + 1000) {
            break;
        }
        // If we have already spent most of the budget, another full depth is
        // unlikely to finish, so stop instead of starting a doomed iteration.
        if (now_ms() >= ctx.deadline) {
            break;
        }
    }

    return best;
}

}  // namespace checkforge
