# MicroJava Compiler

**CS-471L Compiler Construction Lab**  
**Spring 2026 — University of Engineering and Technology, Lahore**  
**Department of Computer Science**

---

## Project Overview

A complete mini compiler for the MicroJava language, integrating all lab modules built during the semester: 

- Lexical Analyzer
- Recursive Descent Parser
- LL(1) Predictive Parser
- LR Parser (SLR(1))
- Operator Precedence Parser (two-stack expression parsing)
- Symbol Table Manager (with nested scopes)
- Error Handler (with panic-mode recovery)
- Full Compilation Pipeline

Two interfaces are provided:
1. **Web UI** — Flask-based browser interface
2. **Command-Line Interface** — Direct terminal usage

---

## Project Structure

```
python_compiler/
├── main.py                 # CLI entry point
├── app.py                  # Flask web server
├── Makefile                # Build and run (cross-platform)
├── run.bat                 # Single-command launcher (Windows)
├── requirements.txt        # Python dependencies
├── README.md               # This file
│
├── src/
│   ├── __init__.py         # Package exports
│   ├── token.py            # Token type definitions
│   ├── lexer.py            # Lexical analyzer
│   ├── error_handler.py    # Error tracking and handling
│   ├── symbol_table.py     # Symbol table with hash-based scopes
│   ├── recursive_parser.py # Recursive descent parser
│   ├── ll1_parser.py       # LL(1) predictive parser
│   └── lr_parser.py        # LR/SLR(1) parser
│
├── static/
│   ├── script.js           # Frontend JS logic
│   └── style.css           # Frontend styling
│
├── templates/
│   └── index.html          # Web UI template
│
├── test/
│   ├── test_simple.mj      # Simple valid program
│   ├── test1_valid.mj      # Full valid program with all features
│   ├── test2_errors.mj     # Program with error handling
│   ├── test3_complex.mj    # Complex program with arrays/classes
│   └── test_lr.mj          # LR parser test
│
└── output/                 # (output files directory)
```

---

## Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Windows (for `run.bat`; other OS use `python main.py` directly)

### Step 1: Install Dependencies

```bash
# Option A: Using run.bat menu
run.bat              # then choose option 11 (Install dependencies)

# Option B: Direct pip
pip install -r requirements.txt

# Option C: Install Flask manually
pip install flask>=3.0.0
```

### Step 2: Verify Installation

```bash
python main.py grammar
```

This prints the grammar, FIRST/FOLLOW sets, and both LL(1) and LR parsing tables. If this works, everything is set up correctly.

---

## Usage — Command Line

### Single Command — Interactive Menu

```bash
run.bat
```

This launches an interactive menu where you can:
- Select a module (1-6)
- Show grammar and tables (7)
- Interactive mode (8)
- Launch Web UI (9)
- Run ALL tests through ALL modules (10)

### Single Command — Direct Module

```bash
run.bat <module> [source_file]
```

**Examples:**
```bash
run.bat lexer test_simple.mj           # Run lexer on a test file
run.bat recursive test1_valid.mj       # Run recursive descent parser
run.bat ll1 test3_complex.mj           # Run LL(1) parser
run.bat lr test_lr.mj                  # Run LR parser
run.bat symbol_table test1_valid.mj    # Run symbol table manager
run.bat full test_simple.mj            # Run full compilation pipeline
run.bat grammar                        # Show grammar, FIRST/FOLLOW, tables
run.bat interactive                     # Interactive mode (manual input)
```

Files are automatically searched in the `test/` folder. You can also provide a full path:
```bash
run.bat lexer C:\path\to\program.mj
```

### Using Python Directly (cross-platform)

```bash
python main.py <module> [source_file]
```

**Examples:**
```bash
python main.py lexer test\test_simple.mj
python main.py full test\test1_valid.mj
python main.py grammar
python main.py interactive
```

---

## Usage — Web UI

### Launching the Web Server

```bash
# From run.bat menu, choose option 9
# OR directly:
python app.py
```

### Accessing the Web UI

Open your browser and navigate to: **http://127.0.0.1:5000**

The web interface provides:
- Source code editor with test file selector
- Module selector sidebar with 7 modules:
  - **Lexical Analyzer** — Tokenizes source code
  - **Recursive Descent** — Parses using recursive routines
  - **LL(1) Predictive** — Parses using LL(1) table
  - **LR Parser (SLR(1))** — Parses using shift-reduce
  - **Symbol Table** — Views nested symbol scopes
  - **Full Compilation** — Runs all modules at once
  - **Grammar & Tables** — Shows grammar, FIRST/FOLLOW, parsing tables
- Real-time error reporting

---

## Compiler Modules

### 1. Lexical Analyzer (`src/lexer.py`)
- Reads source character by character using **double buffering** (Lab 2)
- Produces tokens with (type, lexeme, line, col) attributes
- Recognizes: identifiers, keywords (`program`, `class`, `if`, `else`, `while`, `read`, `print`, `return`, `void`, `final`, `new`), numbers, character constants, operators (`+`, `-`, `*`, `/`, `%`, `==`, `!=`, `>`, `<`, `>=`, `<=`, `=`), punctuation (`(`, `)`, `{`, `}`, `[`, `]`, `;`, `,`, `.`)
- Skips whitespace and `//`-style comments
- Tracks line and column numbers for every token

### 2. Recursive Descent Parser (`src/recursive_parser.py`)
- One parsing method per non-terminal
- Top-down parsing with lookahead
- Integrates with symbol table (inserts/checks symbols during parsing)
- Reports syntax errors with line/column info
- Implements panic-mode error recovery (syncs on `;`, `}`, `program`, EOF)

### 3. LL(1) Predictive Parser (`src/ll1_parser.py`)
- Grammar transformed to be left-factored and free of left recursion
- FIRST and FOLLOW sets computed iteratively
- LL(1) parsing table built from FIRST/FOLLOW
- Uses explicit stack (non-recursive)
- Shows parsing trace with stack, input, and action at each step

### 4. LR Parser — SLR(1) (`src/lr_parser.py`)
- Augmented grammar with start symbol `S'`
- LR(0) items with closure and goto operations
- LR(0) states (canonical collection)
- SLR(1) action and goto tables
- Shift-reduce algorithm with state stack and symbol stack
- Uses FOLLOW sets to determine reduce actions
- Prints complete parsing trace

### 5. Operator Precedence Parser (`src/operator_precedence_parser.py`)
- Hybrid parser: recursive descent for program structure, operator-precedence for expressions
- Two stacks: operator stack and operand stack
- Precedence table: unary `-` (4) > `*` `/` `%` (3) > `+` `-` (2), all left-associative except unary minus
- SHIFT/REDUCE actions with full expression parsing trace
- CLI: `python main.py opp test_opp.mj` · Web UI: **Operator Precedence** module

### 6. Symbol Table Manager (`src/symbol_table.py`)
- Hash table implementation (size 211, with chaining)
- Supports insert, lookup, and delete by name
- Stores: name, kind (variable/constant/function/array/class/parameter), type (int/char/void), scope level, line number
- Nested scopes via linked parent chain
- ScopeManager with `begin_scope()` / `end_scope()` for block nesting
- Dumps all scope levels with their entries

### 7. Error Handler (`src/error_handler.py`)
- Three error categories: Lexical, Syntax, Semantic
- Each error stores: type, message, line, column
- Summary statistics (total / lexical / syntax / semantic)
- Panic mode support for parsers
- Synchronization sets for error recovery in predictive parser

---

## Building and Submission

### File Naming for Submission

```
CS471L_Project_Group#_RollNo.zip
```

### Folder Layout for Submission

```
submission/
├── src/               (all source code files from src/)
│   ├── __init__.py
│   ├── token.py
│   ├── lexer.py
│   ├── error_handler.py
│   ├── symbol_table.py
│   ├── recursive_parser.py
│   ├── ll1_parser.py
│   └── lr_parser.py
├── main.py            (CLI entry point)
├── app.py             (Flask web server)
├── run.bat            (Windows launcher)
├── requirements.txt   (dependencies)
├── docs/              (project report and grammar)
├── test/              (sample MicroJava programs)
├── output/            (sample outputs for each module)
└── README.md          (build and run instructions)
```

### Building Single Command

Everything runs from either:
```bash
make test FILE=test_simple.mj   # Cross-platform (Makefile)
run.bat <module> <file>         # Windows
python main.py <module> <file>  # Cross-platform
```

---

## Test Programs

| File | Description |
|------|-------------|
| `test_simple.mj` | Minimal valid program: variable declaration, assignment, print, return |
| `test1_valid.mj` | Full valid program with constants, classes, if/else, while, read/print |
| `test2_errors.mj` | Valid program with variables, if/while, read/print |
| `test3_complex.mj` | Complex valid program with constants, classes, methods, parameters, nested blocks, arrays |
| `test_lr.mj` | Simple program with arithmetic expression (`a + 10`) |
| `test_microjava_sample.mj` | Official MicroJava sample from the language specification |

---

## Quick Reference — All Commands

```bash
# Setup
pip install -r requirements.txt

# Grammar Info
python main.py grammar

# Run Individual Modules
python main.py lexer test\test_simple.mj
python main.py recursive test\test_simple.mj
python main.py ll1 test\test_simple.mj
python main.py lr test\test_lr.mj
python main.py symbol_table test\test1_valid.mj

# Full Pipeline
python main.py full test\test3_complex.mj

# Interactive
python main.py interactive

# Web UI
python app.py

# Windows Launcher (replaces all of the above with a menu)
run.bat
```

---

## Academic Integrity

- Code sharing between groups is **not allowed**.
- Code from previous semesters or public repositories is **not allowed**.
- AI tools may be used **to understand concepts only**, not to generate source code.
- All submissions will be checked with MOSS (Measure of Software Similarity).
- Plagiarism penalties as per course policy apply.

---

## License

This project is created for academic purposes as part of CS-471L Compiler Construction Lab at UET Lahore, Spring 2026.
