#pragma once

#include "checkforge/board.h"
#include "checkforge/config.h"

namespace checkforge {

int evaluate_material(const Board& board);
int evaluate_for_side_to_move(const Board& board);
int evaluate_material(const Board& board, const EngineConfig& config);
int evaluate_for_side_to_move(const Board& board, const EngineConfig& config);

}  // namespace checkforge
