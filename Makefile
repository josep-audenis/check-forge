.PHONY: build test measurement-test measurement perft tactics speed match benchmark cutechess clean

BUILD_DIR := build
ENGINE := $(BUILD_DIR)/engine/checkforge.exe

build:
	cmake -S . -B $(BUILD_DIR)
	cmake --build $(BUILD_DIR)

test: build
	ctest --test-dir $(BUILD_DIR) --output-on-failure
	python -m unittest discover -s research/tests -p "test_*.py"

measurement-test:
	python -m unittest discover -s research/tests -p "test_*.py"

measurement: build
	python research/run_measurement.py --engine "$(ENGINE)" --baseline-engine "$(ENGINE)" --profile smoke

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
