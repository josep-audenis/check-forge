#include <cstdlib>
#include <cstdio>
#include <stdexcept>
#include <string>

#include "checkforge/board.h"
#include "checkforge/config.h"
#include "checkforge/eval.h"
#include "checkforge/movegen.h"
#include "checkforge/search.h"
#include "checkforge/uci.h"

namespace {

int failures = 0;

void expect(bool condition, const char* message) {
    if (!condition) {
        std::printf("FAIL: %s\n", message);
        ++failures;
    }
}

void expect_equal(const std::string& actual, const std::string& expected, const char* message) {
    if (actual != expected) {
        std::printf("FAIL: %s\n  expected: %s\n  actual:   %s\n", message, expected.c_str(), actual.c_str());
        ++failures;
    }
}

void expect_invalid(const std::string& fen, const char* message) {
    try {
        (void)checkforge::Board::from_fen(fen);
        std::printf("FAIL: %s\n  FEN accepted: %s\n", message, fen.c_str());
        ++failures;
    } catch (const std::invalid_argument&) {
    }
}

void test_startpos() {
    const checkforge::Board board = checkforge::Board::from_fen("startpos");

    expect(board.side_to_move == checkforge::Color::White, "startpos side to move");
    expect(board.castling.white_kingside, "startpos white kingside castling");
    expect(board.castling.white_queenside, "startpos white queenside castling");
    expect(board.castling.black_kingside, "startpos black kingside castling");
    expect(board.castling.black_queenside, "startpos black queenside castling");
    expect(board.en_passant_square == -1, "startpos has no en passant square");
    expect(board.halfmove_clock == 0, "startpos halfmove clock");
    expect(board.fullmove_number == 1, "startpos fullmove number");
    expect(board.piece_at(checkforge::square_index('e', '1')) == 'K', "white king on e1");
    expect(board.piece_at(checkforge::square_index('e', '8')) == 'k', "black king on e8");
}

void test_round_trip() {
    const std::string fen = "r3k2r/ppp2ppp/2n5/3pp3/3PP3/2N5/PPP2PPP/R3K2R b KQkq e3 7 12";
    const checkforge::Board board = checkforge::Board::from_fen(fen);

    expect_equal(board.to_fen(), fen, "custom FEN round-trip");
    expect(board.side_to_move == checkforge::Color::Black, "custom side to move");
    expect(board.en_passant_square == checkforge::square_index('e', '3'), "custom en passant square");
    expect(board.halfmove_clock == 7, "custom halfmove clock");
    expect(board.fullmove_number == 12, "custom fullmove number");
}

void test_invalid_fens() {
    expect_invalid("", "empty FEN");
    expect_invalid("8/8/8/8/8/8/8/8 w - - 0 1", "missing kings");
    expect_invalid("8/8/8/8/8/8/8/4K2k x - - 0 1", "invalid side");
    expect_invalid("8/8/8/8/8/8/8/4K2k w KZ - 0 1", "invalid castling");
    expect_invalid("8/8/8/8/8/8/8/4K2k w - e4 0 1", "invalid en passant rank");
    expect_invalid("8/8/8/8/8/8/8/4K2k w - - -1 1", "negative halfmove");
    expect_invalid("8/8/8/8/8/8/8/4K2k w - - 0 0", "zero fullmove");
    expect_invalid("9/8/8/8/8/8/8/4K2k w - - 0 1", "rank too wide");
}

void test_startpos_perft() {
    const checkforge::Board board = checkforge::Board::from_fen("startpos");

    expect(checkforge::perft(board, 0) == 1, "startpos perft depth 0");
    expect(checkforge::perft(board, 1) == 20, "startpos perft depth 1");
    expect(checkforge::perft(board, 2) == 400, "startpos perft depth 2");
    expect(checkforge::perft(board, 3) == 8902, "startpos perft depth 3");
}

void test_kiwipete_perft() {
    const checkforge::Board board = checkforge::Board::from_fen(
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");

    expect(checkforge::perft(board, 1) == 48, "kiwipete perft depth 1");
    expect(checkforge::perft(board, 2) == 2039, "kiwipete perft depth 2");
}

void test_material_eval() {
    const checkforge::Board equal = checkforge::Board::from_fen("startpos");
    const checkforge::Board white_up_queen =
        checkforge::Board::from_fen("4k3/8/8/8/8/8/8/4KQ2 w - - 0 1");
    const checkforge::Board black_up_rook =
        checkforge::Board::from_fen("4kr2/8/8/8/8/8/8/4K3 b - - 0 1");

    expect(checkforge::evaluate_material(equal) == 0, "startpos material eval");
    expect(checkforge::evaluate_material(white_up_queen) == 900, "white queen material eval");
    expect(checkforge::evaluate_material(black_up_rook) == -500, "black rook material eval");
    expect(checkforge::evaluate_for_side_to_move(black_up_rook) == 500, "side-to-move eval perspective");
}

void test_configurable_eval() {
    const checkforge::Board white_up_queen =
        checkforge::Board::from_fen("4k3/8/8/8/8/8/8/4KQ2 w - - 0 1");
    checkforge::EngineConfig config = checkforge::default_config();
    config.queen_value = 1000;

    expect(checkforge::evaluate_material(white_up_queen, config) == 1000, "configurable queen material eval");
}

void test_bestmove_is_legal() {
    const checkforge::Board board = checkforge::Board::from_fen("startpos");
    const checkforge::SearchResult result = checkforge::search_bestmove(board, 2);
    const std::vector<checkforge::Move> moves = checkforge::generate_legal_moves(board);
    bool found = false;

    for (const checkforge::Move& move : moves) {
        if (checkforge::move_to_uci(move) == checkforge::move_to_uci(result.best_move)) {
            found = true;
            break;
        }
    }

    expect(result.has_move, "bestmove exists");
    expect(found, "bestmove is legal");
}

void test_bestmove_wins_free_queen() {
    const checkforge::Board board =
        checkforge::Board::from_fen("4k3/8/8/8/4q3/8/4R3/4K3 w - - 0 1");
    const checkforge::SearchResult result = checkforge::search_bestmove(board, 1);

    expect_equal(checkforge::move_to_uci(result.best_move), "e2e4", "bestmove captures free queen");
}

void test_full_game_smoke() {
    checkforge::Board board = checkforge::Board::from_fen("startpos");

    for (int ply = 0; ply < 300; ++ply) {
        const checkforge::SearchResult result = checkforge::search_bestmove(board, 1);
        if (!result.has_move) {
            return;
        }
        board = checkforge::make_move(board, result.best_move);
    }

    expect(true, "full game smoke reached ply limit without crashing");
}

void test_uci_handshake() {
    checkforge::UciSession session;

    const std::vector<std::string> uci = session.handle_line("uci");
    const std::vector<std::string> ready = session.handle_line("isready");

    expect(uci.size() == 3, "uci outputs three lines");
    expect(uci.size() > 0 && uci[0] == "id name CheckForge", "uci name output");
    expect(uci.size() > 1 && uci[1] == "id author Josep Audenis", "uci author output");
    expect(uci.size() > 2 && uci[2] == "uciok", "uciok output");
    expect(ready.size() == 1 && ready[0] == "readyok", "readyok output");
}

void test_uci_go_depth() {
    checkforge::UciSession session;

    (void)session.handle_line("position startpos");
    const std::vector<std::string> output = session.handle_line("go depth 1");

    expect(output.size() == 1 && output[0].find("bestmove ") == 0, "uci go depth bestmove output");
}

void test_uci_position_fen_and_moves() {
    checkforge::UciSession session;

    (void)session.handle_line("position fen 4k3/8/8/8/4q3/8/4R3/4K3 w - - 0 1");
    const std::vector<std::string> capture_output = session.handle_line("go depth 1");
    (void)session.handle_line("position startpos moves e2e4 e7e5");
    const std::vector<std::string> moves_output = session.handle_line("go depth 1");

    expect(capture_output.size() == 1 && capture_output[0] == "bestmove e2e4", "uci FEN bestmove captures queen");
    expect(moves_output.size() == 1 && moves_output[0].find("bestmove ") == 0, "uci position moves bestmove output");
}

}  // namespace

int main() {
    test_startpos();
    test_round_trip();
    test_invalid_fens();
    test_startpos_perft();
    test_kiwipete_perft();
    test_material_eval();
    test_configurable_eval();
    test_bestmove_is_legal();
    test_bestmove_wins_free_queen();
    test_full_game_smoke();
    test_uci_handshake();
    test_uci_go_depth();
    test_uci_position_fen_and_moves();

    if (failures > 0) {
        std::printf("%d checkforge tests failed\n", failures);
        return EXIT_FAILURE;
    }

    std::puts("checkforge tests passed");
    return EXIT_SUCCESS;
}
