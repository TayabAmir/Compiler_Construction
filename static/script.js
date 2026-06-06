let currentModule = "lexer";
const OUTPUT_HEIGHT_KEY = "microjava.outputHeight";
const OUTPUT_COLLAPSED_KEY = "microjava.outputCollapsed";
const DEFAULT_OUTPUT_HEIGHT = 380;

const moduleNames = {
    lexer: "Lexical Analyzer",
    recursive: "Recursive Descent Parser",
    ll1: "LL(1) Predictive Parser",
    lr: "LR Parser (SLR(1))",
    symbol_table: "Symbol Table Manager",
    full: "Full Compilation Pipeline",
    grammar: "Grammar &amp; Parsing Tables",
};

document.querySelectorAll(".nav-item").forEach((item) => {
    item.addEventListener("click", function () {
        document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));
        this.classList.add("active");
        currentModule = this.dataset.module;
        document.getElementById("module-title").innerHTML = moduleNames[currentModule];
        document.getElementById("output-body").innerHTML = getPlaceholder(currentModule);
        setStatus("Ready", "info");
        if (currentModule === "grammar") {
            runModule();
        }
    });
});

document.addEventListener("DOMContentLoaded", initOutputPanelControls);

function initOutputPanelControls() {
    const panel = document.getElementById("output-panel");
    const handle = document.getElementById("output-resize-handle");
    const toggle = document.getElementById("output-toggle");

    if (!panel || !handle || !toggle) {
        return;
    }

    const savedHeight = parseInt(localStorage.getItem(OUTPUT_HEIGHT_KEY) || "", 10);
    const savedCollapsed = localStorage.getItem(OUTPUT_COLLAPSED_KEY) === "true";

    if (!Number.isNaN(savedHeight) && savedHeight > 0) {
        panel.style.setProperty("--output-panel-height", `${savedHeight}px`);
    } else {
        panel.style.setProperty("--output-panel-height", `${DEFAULT_OUTPUT_HEIGHT}px`);
    }

    setOutputCollapsed(savedCollapsed);

    toggle.addEventListener("click", () => {
        setOutputCollapsed(!panel.classList.contains("collapsed"));
    });

    handle.addEventListener("mousedown", startOutputResize);
}

function setOutputCollapsed(collapsed) {
    const panel = document.getElementById("output-panel");
    const handle = document.getElementById("output-resize-handle");
    const toggle = document.getElementById("output-toggle");

    if (!panel || !handle || !toggle) {
        return;
    }

    panel.classList.toggle("collapsed", collapsed);
    handle.style.display = collapsed ? "none" : "block";
    toggle.textContent = collapsed ? "▴" : "▾";
    toggle.title = collapsed ? "Expand output" : "Collapse output";
    localStorage.setItem(OUTPUT_COLLAPSED_KEY, String(collapsed));
}

function startOutputResize(event) {
    if (event.button !== 0) {
        return;
    }

    const panel = document.getElementById("output-panel");
    if (!panel || panel.classList.contains("collapsed")) {
        return;
    }

    const mainContent = document.querySelector(".main-content");
    const startY = event.clientY;
    const startHeight = panel.getBoundingClientRect().height;
    const minHeight = 44;
    const availableHeight = mainContent ? mainContent.clientHeight : window.innerHeight;
    const maxHeight = Math.max(minHeight, availableHeight - 180);

    document.body.classList.add("resizing-output");

    function onMove(moveEvent) {
        const nextHeight = startHeight + (startY - moveEvent.clientY);
        const clampedHeight = Math.max(minHeight, Math.min(maxHeight, nextHeight));
        panel.style.setProperty("--output-panel-height", `${clampedHeight}px`);
    }

    function onUp() {
        document.body.classList.remove("resizing-output");
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);

        const heightValue = parseInt(getComputedStyle(panel).getPropertyValue("--output-panel-height"), 10);
        if (!Number.isNaN(heightValue) && heightValue > 0) {
            localStorage.setItem(OUTPUT_HEIGHT_KEY, String(heightValue));
        }
    }

    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
}

function getPlaceholder(module) {
    const msgs = {
        lexer: "Tokenize source code into a stream of tokens.",
        recursive: "Parse using recursive descent parsing routines.",
        ll1: "Parse using LL(1) predictive parsing table.",
        lr: "Parse using SLR(1) shift-reduce parser.",
        symbol_table: "View symbol table with nested scopes.",
        full: "Execute the full compilation pipeline.",
        grammar: "View grammar, FIRST/FOLLOW sets, and parsing tables.",
    };
    return `<div class="placeholder"><div class="placeholder-icon">⚡</div><h3>Ready</h3><p>${msgs[module] || ""}</p></div>`;
}

function setStatus(text, type = "info") {
    const el = document.getElementById("output-status");
    el.textContent = text;
    el.className = "output-status " + type;
}

function showLoading() {
    document.getElementById("loading-overlay").classList.remove("hidden");
}

function hideLoading() {
    document.getElementById("loading-overlay").classList.add("hidden");
}

function loadSample() {
    const select = document.getElementById("sample-select");
    const options = select.options;
    if (options.length > 1) {
        const randomIdx = 1 + Math.floor(Math.random() * (options.length - 1));
        select.selectedIndex = randomIdx;
        loadSelectedSample();
    }
}

function loadSelectedSample() {
    const select = document.getElementById("sample-select");
    const fname = select.value;
    if (fname && testSources[fname]) {
        document.getElementById("source-editor").value = testSources[fname];
    }
}

function runModule() {
    const source = document.getElementById("source-editor").value;
    if (!source.trim()) {
        setStatus("No source code!", "error");
        return;
    }

    showLoading();

    const endpoints = {
        lexer: "/lexer",
        recursive: "/recursive_parser",
        ll1: "/ll1_parser",
        lr: "/lr_parser",
        symbol_table: "/symbol_table",
        full: "/full_compilation",
        grammar: "/grammar_info",
    };

    const endpoint = endpoints[currentModule];

    if (currentModule === "grammar") {
        fetch(endpoint)
            .then((r) => r.json())
            .then((data) => {
                hideLoading();
                renderGrammar(data);
            })
            .catch(() => {
                hideLoading();
                setStatus("Request failed", "error");
            });
        return;
    }

    fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source }),
    })
        .then((r) => r.json())
        .then((data) => {
            hideLoading();
            renderOutput(currentModule, data);
        })
        .catch(() => {
            hideLoading();
            setStatus("Request failed", "error");
            document.getElementById("output-body").innerHTML =
                '<div class="error-msg">Error communicating with server.</div>';
        });
}

function renderOutput(module, data) {
    const body = document.getElementById("output-body");
    setStatus("Complete", data.success !== false ? "success" : "error");

    switch (module) {
        case "lexer":
            renderLexerOutput(body, data);
            break;
        case "recursive":
            renderRecursiveOutput(body, data);
            break;
        case "ll1":
            renderLL1Output(body, data);
            break;
        case "lr":
            renderLROutput(body, data);
            break;
        case "symbol_table":
            renderSymbolTableOutput(body, data);
            break;
        case "full":
            renderFullOutput(body, data);
            break;
    }
}

function renderLexerOutput(body, data) {
    let html = `<div class="summary-card"><h4>Token Stream</h4>`;
    html += `<div style="font-size:12px;color:var(--text-muted);margin-bottom:8px;">Total tokens: ${data.total}</div>`;

    if (data.tokens.length === 0) {
        html += `<div class="info-msg">No tokens found.</div>`;
    } else {
        for (const t of data.tokens) {
            html += `<div class="token-line">
                <span class="token-pos">[L${t.line},C${t.col}]</span>
                <span class="token-type">${t.type}</span>
                <span class="token-lexeme">${t.lexeme ? `(${escHtml(t.lexeme)})` : ""}</span>
            </div>`;
        }
    }
    html += `</div>`;
    html += renderErrorSummary(data);
    body.innerHTML = html;
}

function renderRecursiveOutput(body, data) {
    let html = `<div class="summary-card">`;
    html += `<h4>Recursive Descent Parser Result</h4>`;
    html += `<div class="module-result ${data.success ? "pass" : "fail"}">
        ${data.success ? "✓" : "✗"} ${data.success ? "Parsing Successful!" : "Parsing Failed"}
    </div>`;
    html += `</div>`;
    html += renderSymbolTableHTML(data.symbol_table);
    html += renderErrorSummary(data);
    body.innerHTML = html;
}

function renderLL1Output(body, data) {
    let html = `<div class="summary-card"><h4>LL(1) Parsing Result</h4>`;
    html += `<div class="module-result ${data.success ? "pass" : "fail"}">
        ${data.success ? "✓" : "✗"} ${data.success ? "Parsing Successful!" : "Parsing Failed"}
    </div>`;
    html += `</div>`;

    html += `<div class="summary-card"><h4>FIRST Sets</h4>`;
    for (const [nt, set] of Object.entries(data.first_sets)) {
        html += `<div class="set-display"><span class="set-nt">FIRST(${nt})</span><span class="set-values">${set}</span></div>`;
    }
    html += `</div>`;

    html += `<div class="summary-card"><h4>FOLLOW Sets</h4>`;
    for (const [nt, set] of Object.entries(data.follow_sets)) {
        html += `<div class="set-display"><span class="set-nt">FOLLOW(${nt})</span><span class="set-values">${set}</span></div>`;
    }
    html += `</div>`;

    if (data.parse_table) {
        html += `<div class="summary-card"><h4>LL(1) Parsing Table</h4>`;
        html += `<table class="parse-table"><thead><tr><th>NT \\ T</th>`;
        for (const t of data.parse_table.terminals) {
            html += `<th>${t}</th>`;
        }
        html += `</tr></thead><tbody>`;
        for (const row of data.parse_table.rows) {
            html += `<tr><td><strong>${row.non_terminal}</strong></td>`;
            for (const t of data.parse_table.terminals) {
                html += `<td>${escHtml(row[t] || "--")}</td>`;
            }
            html += `</tr>`;
        }
        html += `</tbody></table></div>`;
    }

    if (data.trace && data.trace.length > 0) {
        html += `<div class="summary-card"><h4>Parsing Trace</h4>`;
        for (const step of data.trace) {
            html += `<div class="trace-step">
                <span style="min-width:200px;color:var(--accent-cyan)">${escHtml(step.stack)}</span>
                <span style="min-width:150px;color:var(--accent-yellow)">${escHtml(step.input)}</span>
                <span style="color:var(--text-secondary)">${escHtml(step.action)}</span>
            </div>`;
        }
        html += `</div>`;
    }

    html += renderErrorSummary(data);
    body.innerHTML = html;
}

function renderLROutput(body, data) {
    let html = `<div class="summary-card"><h4>LR Parsing Result</h4>`;
    html += `<div class="module-result ${data.success ? "pass" : "fail"}">
        ${data.success ? "✓" : "✗"} ${data.success ? "Parsing Successful!" : "Parsing Failed"}
    </div>`;
    html += `</div>`;

    if (data.states && data.states.length > 0) {
        html += `<div class="summary-card"><h4>LR(0) States (${data.states.length} total)</h4>`;
        for (const st of data.states) {
            html += `<div class="lr-state">
                <div class="state-id">State ${st.id}</div>`;
            for (const item of st.items) {
                html += `<div class="state-item">${escHtml(item)}</div>`;
            }
            for (const [sym, dest] of Object.entries(st.transitions)) {
                html += `<div class="state-trans">⟶ ${sym} → State ${dest}</div>`;
            }
            html += `</div>`;
        }
        html += `</div>`;
    }

    if (data.action_table) {
        html += `<div class="summary-card"><h4>ACTION Table</h4>`;
        html += `<table class="action-table"><thead><tr><th>State</th>`;
        for (const t of data.action_table.terminals) {
            html += `<th>${t}</th>`;
        }
        html += `</tr></thead><tbody>`;
        for (const row of data.action_table.rows) {
            html += `<tr><td><strong>${row.state}</strong></td>`;
            for (const t of data.action_table.terminals) {
                html += `<td>${row[t] || ""}</td>`;
            }
            html += `</tr>`;
        }
        html += `</tbody></table></div>`;
    }

    if (data.goto_table) {
        html += `<div class="summary-card"><h4>GOTO Table</h4>`;
        html += `<table class="action-table"><thead><tr><th>State</th>`;
        for (const nt of data.goto_table.non_terminals) {
            html += `<th>${nt}</th>`;
        }
        html += `</tr></thead><tbody>`;
        for (const row of data.goto_table.rows) {
            html += `<tr><td><strong>${row.state}</strong></td>`;
            for (const nt of data.goto_table.non_terminals) {
                html += `<td>${row[nt] || ""}</td>`;
            }
            html += `</tr>`;
        }
        html += `</tbody></table></div>`;
    }

    if (data.trace && data.trace.length > 0) {
        html += `<div class="summary-card"><h4>LR Parsing Trace</h4>`;
        for (const step of data.trace) {
            html += `<div class="trace-step">
                <span style="min-width:180px;color:var(--accent-cyan)">${escHtml(step.state_stack)}</span>
                <span style="min-width:120px;color:var(--accent-yellow)">${escHtml(step.sym_stack)}</span>
                <span style="min-width:150px;color:var(--text-secondary)">${escHtml(step.input)}</span>
                <span style="color:var(--text-primary)">${escHtml(step.action)}</span>
            </div>`;
        }
        html += `</div>`;
    }

    html += renderErrorSummary(data);
    body.innerHTML = html;
}

function renderSymbolTableOutput(body, data) {
    let html = `<div class="summary-card"><h4>Symbol Table (All Scopes)</h4>`;
    html += renderSymbolTableHTML(data.symbol_table);
    html += `</div>`;
    html += renderErrorSummary(data);
    body.innerHTML = html;
}

function renderFullOutput(body, data) {
    let html = `<div class="summary-card"><h4>Compilation Summary</h4>`;
    html += `<div class="error-summary">
        <div class="error-stat total"><div class="stat-value">${data.summary.total}</div><div class="stat-label">Total Errors</div></div>
        <div class="error-stat lexical"><div class="stat-value">${data.summary.lexical}</div><div class="stat-label">Lexical</div></div>
        <div class="error-stat syntax"><div class="stat-value">${data.summary.syntax}</div><div class="stat-label">Syntax</div></div>
        <div class="error-stat semantic"><div class="stat-value">${data.summary.semantic}</div><div class="stat-label">Semantic</div></div>
    </div>`;
    html += `</div>`;

    html += `<div class="compilation-grid">`;

    html += `<div class="compilation-card">
        <h4 style="color:var(--accent-cyan)">🔍 Lexical Analyzer</h4>
        <div class="module-result pass">✓ ${data.lexer.total} tokens</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">${data.lexer.errors.length} errors</div>
    </div>`;

    const rdStatus = data.recursive.success;
    html += `<div class="compilation-card">
        <h4 style="color:var(--accent-blue)">🔁 Recursive Descent</h4>
        <div class="module-result ${rdStatus ? 'pass' : 'fail'}">${rdStatus ? '✓ PASS' : '✗ FAIL'}</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">${data.recursive.errors.length} errors</div>
    </div>`;

    const ll1Status = data.ll1.success;
    html += `<div class="compilation-card">
        <h4 style="color:var(--accent-yellow)">📊 LL(1) Predictive</h4>
        <div class="module-result ${ll1Status ? 'pass' : 'fail'}">${ll1Status ? '✓ PASS' : '✗ FAIL'}</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">${data.ll1.errors.length} errors</div>
    </div>`;

    const lrStatus = data.lr.success;
    html += `<div class="compilation-card">
        <h4 style="color:var(--accent-green)">⚙️ LR Parser (SLR(1))</h4>
        <div class="module-result ${lrStatus ? 'pass' : 'fail'}">${lrStatus ? '✓ PASS' : '✗ FAIL'}</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">${data.lr.errors.length} errors</div>
    </div>`;

    html += `</div>`;

    html += `<div class="summary-card"><h4>Symbol Table</h4>`;
    html += renderSymbolTableHTML(data.recursive.symbol_table);
    html += `</div>`;

    html += `<div class="summary-card"><h4>LL(1) Parsing Trace</h4>`;
    const ll1Trace = data.ll1.trace || [];
    for (const step of ll1Trace.slice(0, 20)) {
        html += `<div class="trace-step">
            <span style="min-width:200px;color:var(--accent-cyan)">${escHtml(step.stack)}</span>
            <span style="min-width:150px;color:var(--accent-yellow)">${escHtml(step.input)}</span>
            <span style="color:var(--text-secondary)">${escHtml(step.action)}</span>
        </div>`;
    }
    if (ll1Trace.length > 20) {
        html += `<div class="info-msg">... and ${ll1Trace.length - 20} more steps</div>`;
    }
    html += `</div>`;

    body.innerHTML = html;
}

function renderGrammar(data) {
    const body = document.getElementById("output-body");
    setStatus("Grammar loaded", "info");

    let html = `<div class="summary-card"><h4>MicroJava Grammar</h4>`;
    html += `<div style="font-size:12px;color:var(--text-muted);margin-bottom:8px;">
        Non-terminals: ${data.non_terminals.length} | Terminals: ${data.terminals.length}</div>`;
    html += `</div>`;

    html += `<div class="summary-card"><h4>FIRST Sets</h4>`;
    for (const [nt, set] of Object.entries(data.first_sets)) {
        html += `<div class="set-display"><span class="set-nt">FIRST(${nt})</span><span class="set-values">${set}</span></div>`;
    }
    html += `</div>`;

    html += `<div class="summary-card"><h4>FOLLOW Sets</h4>`;
    for (const [nt, set] of Object.entries(data.follow_sets)) {
        html += `<div class="set-display"><span class="set-nt">FOLLOW(${nt})</span><span class="set-values">${set}</span></div>`;
    }
    html += `</div>`;

    if (data.parse_table) {
        html += `<div class="summary-card"><h4>LL(1) Parsing Table</h4>`;
        html += `<table class="parse-table"><thead><tr><th>NT \\ T</th>`;
        for (const t of data.parse_table.terminals) {
            html += `<th>${t}</th>`;
        }
        html += `</tr></thead><tbody>`;
        for (const row of data.parse_table.rows) {
            html += `<tr><td><strong>${row.non_terminal}</strong></td>`;
            for (const t of data.parse_table.terminals) {
                html += `<td style="font-size:10px;">${escHtml(row[t] || "--")}</td>`;
            }
            html += `</tr>`;
        }
        html += `</tbody></table></div>`;
    }

    body.innerHTML = html;

    fetch("/lr_tables")
        .then((r) => r.json())
        .then((lrData) => {
            let lrHtml = `<div class="summary-card"><h4>ACTION Table (SLR(1))</h4>`;
            if (lrData.action_table) {
                lrHtml += `<table class="action-table"><thead><tr><th>State</th>`;
                for (const t of lrData.action_table.terminals) {
                    lrHtml += `<th>${t}</th>`;
                }
                lrHtml += `</tr></thead><tbody>`;
                for (const row of lrData.action_table.rows) {
                    lrHtml += `<tr><td><strong>${row.state}</strong></td>`;
                    for (const t of lrData.action_table.terminals) {
                        lrHtml += `<td>${row[t] || ""}</td>`;
                    }
                    lrHtml += `</tr>`;
                }
                lrHtml += `</tbody></table>`;
            }
            lrHtml += `</div>`;

            lrHtml += `<div class="summary-card"><h4>GOTO Table (SLR(1))</h4>`;
            if (lrData.goto_table) {
                lrHtml += `<table class="action-table"><thead><tr><th>State</th>`;
                for (const nt of lrData.goto_table.non_terminals) {
                    lrHtml += `<th>${nt}</th>`;
                }
                lrHtml += `</tr></thead><tbody>`;
                for (const row of lrData.goto_table.rows) {
                    lrHtml += `<tr><td><strong>${row.state}</strong></td>`;
                    for (const nt of lrData.goto_table.non_terminals) {
                        lrHtml += `<td>${row[nt] || ""}</td>`;
                    }
                    lrHtml += `</tr>`;
                }
                lrHtml += `</tbody></table>`;
            }
            lrHtml += `</div>`;

            if (lrData.states) {
                lrHtml += `<div class="summary-card"><h4>LR(0) States (${lrData.states.length} total)</h4>`;
                for (const st of lrData.states) {
                    lrHtml += `<div class="lr-state">
                        <div class="state-id">State ${st.id}</div>`;
                    for (const item of st.items) {
                        lrHtml += `<div class="state-item">${escHtml(item)}</div>`;
                    }
                    for (const [sym, dest] of Object.entries(st.transitions)) {
                        lrHtml += `<div class="state-trans">⟶ ${sym} → State ${dest}</div>`;
                    }
                    lrHtml += `</div>`;
                }
                lrHtml += `</div>`;
            }

            body.innerHTML += lrHtml;
        });
}

function renderSymbolTableHTML(symbolTable) {
    if (!symbolTable || symbolTable.length === 0) {
        return `<div class="empty-scope">No symbols defined.</div>`;
    }

    let html = `<div class="sym-table-container">`;
    for (const scope of symbolTable) {
        html += `<div class="sym-scope">
            <div class="sym-scope-header">Scope ${scope.scope_level} (${scope.entry_count} entries)</div>
            <div class="sym-scope-body">`;
        if (scope.entries.length === 0) {
            html += `<div class="empty-scope">(empty)</div>`;
        } else {
            html += `<table class="sym-table">
                <thead><tr><th>#</th><th>Name</th><th>Kind</th><th>Type</th><th>Scope</th><th>Line</th></tr></thead>
                <tbody>`;
            for (const e of scope.entries) {
                html += `<tr>
                    <td>${e.id}</td>
                    <td><strong>${escHtml(e.name)}</strong></td>
                    <td>${e.kind}</td>
                    <td>${e.type}</td>
                    <td>${e.scope}</td>
                    <td>${e.line}</td>
                </tr>`;
            }
            html += `</tbody></table>`;
        }
        html += `</div></div>`;
    }
    html += `</div>`;
    return html;
}

function renderErrorSummary(data) {
    if (!data.error_summary) return "";
    const s = data.error_summary;
    let html = `<div class="summary-card"><h4>Error Summary</h4>
        <div class="error-summary">
            <div class="error-stat total"><div class="stat-value">${s.total}</div><div class="stat-label">Total</div></div>
            <div class="error-stat lexical"><div class="stat-value">${s.lexical}</div><div class="stat-label">Lexical</div></div>
            <div class="error-stat syntax"><div class="stat-value">${s.syntax}</div><div class="stat-label">Syntax</div></div>
            <div class="error-stat semantic"><div class="stat-value">${s.semantic}</div><div class="stat-label">Semantic</div></div>
        </div>`;

    if (data.errors && data.errors.length > 0) {
        for (const e of data.errors) {
            html += `<div class="error-msg">[${e.type}] Line ${e.line}, Col ${e.col}: ${escHtml(e.message)}</div>`;
        }
    }
    html += `</div>`;
    return html;
}

function escHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
