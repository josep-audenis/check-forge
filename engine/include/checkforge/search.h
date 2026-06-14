#pragma once

#include <string>

#include "checkforge/board.h"
#include "checkforge/config.h"
#include "checkforge/movegen.h"

namespace checkforge {

struct SearchResult {
    Move best_move;
    int score = 0;
    int depth = 0;
    bool has_move = false;
};

SearchResult search_bestmove(const Board& board, int depth);
SearchResult search_bestmove(const Board& board, int depth, const EngineConfig& config);

// Iterative-deepening search bounded by a wall-clock budget in milliseconds.
// Searches depth 1, 2, ... up to max_depth, returning the best move from the
// last fully completed depth before the budget runs out. Always returns a legal
// move when one exists (depth 1 always completes).
SearchResult search_bestmove_timed(const Board& board, int max_depth, long budget_ms, const EngineConfig& config);

}  // namespace checkforge
