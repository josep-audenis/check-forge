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

}  // namespace checkforge
