add_executable(checkforge
    src/board.cpp
    src/config.cpp
    src/eval.cpp
    src/movegen.cpp
    src/search.cpp
    src/uci.cpp
    src/main.cpp
)

target_include_directories(checkforge PRIVATE include)

add_executable(checkforge_smoke_tests
    src/board.cpp
    src/config.cpp
    src/eval.cpp
    src/movegen.cpp
    src/search.cpp
    src/uci.cpp
    tests/smoke_tests.cpp
)

target_include_directories(checkforge_smoke_tests PRIVATE include)

add_test(NAME checkforge_smoke_tests COMMAND checkforge_smoke_tests)
