# Makefile for SafeBox convenience commands

.PHONY: build clean test test-cpp test-python test-integration help install

build:
	@mkdir -p build
	@cd build && cmake .. && make

test: test-cpp test-python
	@echo "✓ All tests completed"

test-cpp: build
	@cd build && ./safebox-host-tests

test-python:
	@python3 -m pytest tests/test_agent.py -v

test-integration:
	@bash tests/integration_test.sh

install: build
	@cd build && sudo make install
	@echo "✓ safebox-host installed to /usr/local/bin"

clean:
	@rm -rf build reports
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Cleaned build artifacts"

help:
	@echo "SafeBox Build Targets:"
	@echo "  make build            - Build the project"
	@echo "  make test             - Run all tests (C++ and Python)"
	@echo "  make test-cpp         - Run C++ unit tests only"
	@echo "  make test-python      - Run Python unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make install          - Build and install safebox-host"
	@echo "  make clean            - Clean build artifacts"
	@echo "  make help             - Show this help"
