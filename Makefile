.PHONY: build test perft tactics speed match benchmark cutechess clean

BUILD_DIR := build
ENGINE := $(BUILD_DIR)/engine/checkforge.exe

build:
	cmake -S . -B $(BUILD_DIR)
	cmake --build $(BUILD_DIR)

test: build
	ctest --test-dir $(BUILD_DIR) --output-on-failure

perft: build
	python research/run_perft.py --engine "$(ENGINE)"

tactics: build
	python research/run_tactics.py --engine "$(ENGINE)"

speed: build
	python research/run_speed.py --engine "$(ENGINE)"

match: build
	python research/run_match.py --engine "$(ENGINE)"

benchmark: build
	python research/run_benchmark.py --engine "$(ENGINE)"
	python research/evaluate_result.py results/latest.json

cutechess: build
	python research/run_cutechess.py --engine "$(ENGINE)" --opponent-engine "$(ENGINE)"

clean:
	cmake --build $(BUILD_DIR) --target clean
