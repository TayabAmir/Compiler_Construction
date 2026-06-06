from __future__ import annotations

import os
from flask import Flask, render_template, request, jsonify

from src.token import Token, TokenType
from src.lexer import Lexer
from src.error_handler import ErrorHandler, ErrorType
from src.symbol_table import ScopeManager, IdentifierKind, DataType
from src.recursive_parser import RecursiveParser
from src.ll1_parser import LL1Parser
from src.lr_parser import LRParser

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "test"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def get_source_text(filename: str) -> str:
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(filepath):
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


@app.route("/")
def index():
    test_files = [f for f in os.listdir(app.config["UPLOAD_FOLDER"]) if f.endswith(".mj")]
    test_sources = {}
    for tf in test_files:
        test_sources[tf] = get_source_text(tf)
    return render_template("index.html", test_files=test_files, test_sources=test_sources)


@app.route("/lexer", methods=["POST"])
def run_lexer():
    data = request.get_json()
    source = data.get("source", "")

    errors = ErrorHandler()
    lexer = Lexer(source, errors)
    tokens = lexer.tokenize_all()

    token_list = []
    for t in tokens:
        token_list.append({
            "type": t.type_to_string(),
            "lexeme": t.lexeme,
            "line": t.line,
            "col": t.col,
        })

    return jsonify({
        "tokens": token_list,
        "error_summary": errors.get_summary(),
        "errors": [e.to_dict() for e in errors.get_errors()],
        "total": len(tokens),
    })


@app.route("/recursive_parser", methods=["POST"])
def run_recursive_parser():
    data = request.get_json()
    source = data.get("source", "")

    errors = ErrorHandler()
    lexer = Lexer(source, errors)
    sym_table = ScopeManager()
    parser = RecursiveParser(lexer, sym_table, errors)

    success = parser.parse()

    return jsonify({
        "success": success,
        "error_summary": errors.get_summary(),
        "errors": [e.to_dict() for e in errors.get_errors()],
        "symbol_table": sym_table.get_all_scopes_data(),
    })


@app.route("/ll1_parser", methods=["POST"])
def run_ll1_parser():
    data = request.get_json()
    source = data.get("source", "")

    errors_tokenize = ErrorHandler()
    lexer = Lexer(source, errors_tokenize)
    tokens = lexer.tokenize_all()

    errors = ErrorHandler()
    parser = LL1Parser(errors)
    parser.initialize_microjava_grammar()
    parser.compute_sets()

    result = parser.parse(tokens)

    return jsonify({
        "success": result["success"],
        "trace": result["trace"],
        "first_sets": parser.get_first_sets(),
        "follow_sets": parser.get_follow_sets(),
        "parse_table": parser.get_parse_table_data(),
        "error_summary": errors.get_summary(),
        "errors": [e.to_dict() for e in errors.get_errors()],
        "total_tokens": len(tokens),
    })


@app.route("/lr_parser", methods=["POST"])
def run_lr_parser():
    data = request.get_json()
    source = data.get("source", "")

    errors_tokenize = ErrorHandler()
    lexer = Lexer(source, errors_tokenize)
    tokens = lexer.tokenize_all()

    errors = ErrorHandler()
    parser = LRParser(errors)
    parser.initialize_microjava_grammar()
    parser.build_parsing_tables()

    result = parser.parse(tokens)

    return jsonify({
        "success": result["success"],
        "trace": result["trace"],
        "states": parser.get_states_info(),
        "action_table": parser.get_action_table_data(),
        "goto_table": parser.get_goto_table_data(),
        "error_summary": errors.get_summary(),
        "errors": [e.to_dict() for e in errors.get_errors()],
        "total_tokens": len(tokens),
    })


@app.route("/symbol_table", methods=["POST"])
def run_symbol_table():
    data = request.get_json()
    source = data.get("source", "")

    errors = ErrorHandler()
    lexer = Lexer(source, errors)
    sym_table = ScopeManager()
    parser = RecursiveParser(lexer, sym_table, errors)
    parser.parse()

    return jsonify({
        "symbol_table": sym_table.get_all_scopes_data(),
        "error_summary": errors.get_summary(),
        "errors": [e.to_dict() for e in errors.get_errors()],
    })


@app.route("/full_compilation", methods=["POST"])
def run_full_compilation():
    data = request.get_json()
    source = data.get("source", "")

    results = {}

    errors = ErrorHandler()
    lexer = Lexer(source, errors)
    tokens = lexer.tokenize_all()
    token_list = []
    for t in tokens:
        token_list.append({
            "type": t.type_to_string(),
            "lexeme": t.lexeme,
            "line": t.line,
            "col": t.col,
        })
    results["lexer"] = {
        "tokens": token_list,
        "total": len(tokens),
        "errors": [e.to_dict() for e in errors.get_errors() if e.type == ErrorType.LEXICAL],
    }

    errors2 = ErrorHandler()
    lexer2 = Lexer(source, errors2)
    sym_table = ScopeManager()
    parser_rd = RecursiveParser(lexer2, sym_table, errors2)
    rd_success = parser_rd.parse()
    results["recursive"] = {
        "success": rd_success,
        "errors": [e.to_dict() for e in errors2.get_errors()],
        "symbol_table": sym_table.get_all_scopes_data(),
    }

    errors3 = ErrorHandler()
    lexer3 = Lexer(source, ErrorHandler())
    tokens3 = lexer3.tokenize_all()
    parser_ll1 = LL1Parser(errors3)
    parser_ll1.initialize_microjava_grammar()
    parser_ll1.compute_sets()
    ll1_result = parser_ll1.parse(tokens3)
    results["ll1"] = {
        "success": ll1_result["success"],
        "trace": ll1_result["trace"],
        "errors": [e.to_dict() for e in errors3.get_errors()],
    }

    errors4 = ErrorHandler()
    lexer4 = Lexer(source, ErrorHandler())
    tokens4 = lexer4.tokenize_all()
    parser_lr = LRParser(errors4)
    parser_lr.initialize_microjava_grammar()
    parser_lr.build_parsing_tables()
    lr_result = parser_lr.parse(tokens4)
    results["lr"] = {
        "success": lr_result["success"],
        "trace": lr_result["trace"],
        "errors": [e.to_dict() for e in errors4.get_errors()],
    }

    all_errors = []
    all_errors.extend(errors.get_errors())
    all_errors.extend(errors2.get_errors())
    all_errors.extend(errors3.get_errors())
    all_errors.extend(errors4.get_errors())

    all_summary = {
        "total": len(all_errors),
        "lexical": sum(1 for e in all_errors if e.type == ErrorType.LEXICAL),
        "syntax": sum(1 for e in all_errors if e.type == ErrorType.SYNTAX),
        "semantic": sum(1 for e in all_errors if e.type == ErrorType.SEMANTIC),
    }

    results["summary"] = all_summary

    return jsonify(results)


@app.route("/grammar_info", methods=["GET"])
def grammar_info():
    errors = ErrorHandler()
    parser = LL1Parser(errors)
    parser.initialize_microjava_grammar()
    parser.compute_sets()

    return jsonify({
        "non_terminals": sorted(parser.non_terminals),
        "terminals": sorted(parser.terminals),
        "first_sets": parser.get_first_sets(),
        "follow_sets": parser.get_follow_sets(),
        "parse_table": parser.get_parse_table_data(),
    })


@app.route("/lr_tables", methods=["GET"])
def lr_tables():
    errors = ErrorHandler()
    parser = LRParser(errors)
    parser.initialize_microjava_grammar()
    parser.build_parsing_tables()

    return jsonify({
        "states": parser.get_states_info(),
        "action_table": parser.get_action_table_data(),
        "goto_table": parser.get_goto_table_data(),
    })



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
