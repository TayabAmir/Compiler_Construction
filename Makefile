PYTHON ?= python3
MAIN = main.py
TEST_DIR = test
OUTPUT_DIR = output

.PHONY: all help install test output clean web grammar

all: help

help:
	@echo "MicroJava Compiler - CS-471L"
	@echo "  make install    Install dependencies"
	@echo "  make test         Run full pipeline on all test files"
	@echo "  make test FILE=x  Run full pipeline on one file"
	@echo "  make output       Generate sample outputs"
	@echo "  make grammar      Print grammar and tables"
	@echo "  make web          Start Flask web UI"

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	@if [ -z "$(FILE)" ]; then \
		for f in $(TEST_DIR)/*.mj; do \
			echo "=== $$f ==="; \
			$(PYTHON) $(MAIN) full "$$f" || exit 1; \
		done; \
	else \
		$(PYTHON) $(MAIN) full "$(FILE)"; \
	fi

grammar:
	$(PYTHON) $(MAIN) grammar

output:
	@mkdir -p $(OUTPUT_DIR)/lexer $(OUTPUT_DIR)/recursive $(OUTPUT_DIR)/ll1 $(OUTPUT_DIR)/lr $(OUTPUT_DIR)/symbol_table $(OUTPUT_DIR)/full
	@for f in test_simple test1_valid test3_complex test_microjava_sample; do \
		$(PYTHON) $(MAIN) lexer test/$$f.mj > $(OUTPUT_DIR)/lexer/$$f.txt 2>&1; \
		$(PYTHON) $(MAIN) recursive test/$$f.mj > $(OUTPUT_DIR)/recursive/$$f.txt 2>&1; \
		$(PYTHON) $(MAIN) ll1 test/$$f.mj > $(OUTPUT_DIR)/ll1/$$f.txt 2>&1; \
		$(PYTHON) $(MAIN) lr test/$$f.mj > $(OUTPUT_DIR)/lr/$$f.txt 2>&1; \
		$(PYTHON) $(MAIN) symbol_table test/$$f.mj > $(OUTPUT_DIR)/symbol_table/$$f.txt 2>&1; \
		$(PYTHON) $(MAIN) full test/$$f.mj > $(OUTPUT_DIR)/full/$$f.txt 2>&1; \
	done
	$(PYTHON) $(MAIN) grammar > $(OUTPUT_DIR)/grammar_tables.txt 2>&1

web:
	$(PYTHON) app.py

clean:
	rm -rf $(OUTPUT_DIR)
