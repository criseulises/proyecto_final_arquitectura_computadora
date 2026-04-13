/**
 * Simulador de Pipeline RISC - Frontend
 * Grupo: De blutus duais
 * Arquitectura de Computadores
 */

// ============================================================
// Estado Global
// ============================================================
const state = {
    snapshots: [],
    pipelineTable: [],
    stats: null,
    currentCycle: 0,
    isPlaying: false,
    playInterval: null,
    speed: 800,
    previousRegisters: new Array(32).fill(0),
};

// ============================================================
// Elementos del DOM
// ============================================================
const $ = (id) => document.getElementById(id);

const elements = {
    codeEditor: $("code-editor"),
    btnSimulate: $("btn-simulate"),
    btnPlay: $("btn-play"),
    btnStep: $("btn-step"),
    btnReset: $("btn-reset"),
    toggleForwarding: $("toggle-forwarding"),
    speedSlider: $("speed-slider"),
    speedValue: $("speed-value"),
    examplesList: $("examples-list"),
    pipelineEmpty: $("pipeline-empty"),
    pipelineView: $("pipeline-view"),
    tableEmpty: $("table-empty"),
    tableView: $("table-view"),
    statsEmpty: $("stats-empty"),
    statsView: $("stats-view"),
    cycleNumber: $("cycle-number"),
    hazardAlert: $("hazard-alert"),
    hazardTitle: $("hazard-title"),
    hazardDetail: $("hazard-detail"),
    branchAlert: $("branch-alert"),
    errorDisplay: $("error-display"),
    registersGrid: $("registers-grid"),
    memoryGrid: $("memory-grid"),
    pipelineTable: $("pipeline-table"),
    statsGrid: $("stats-grid"),
    loading: $("loading"),
};

// Nombres de registros MIPS
const REG_NAMES = [
    "$zero", "$at", "$v0", "$v1", "$a0", "$a1", "$a2", "$a3",
    "$t0", "$t1", "$t2", "$t3", "$t4", "$t5", "$t6", "$t7",
    "$s0", "$s1", "$s2", "$s3", "$s4", "$s5", "$s6", "$s7",
    "$t8", "$t9", "$k0", "$k1", "$gp", "$sp", "$fp", "$ra"
];

// ============================================================
// Inicializacion
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
    initRegistersGrid();
    loadExamples();
    setupEventListeners();
});

function initRegistersGrid() {
    let html = "";
    for (let i = 0; i < 32; i++) {
        html += `
            <div class="reg-item" id="reg-${i}">
                <div class="reg-name">${REG_NAMES[i]}</div>
                <div class="reg-value" id="reg-val-${i}">0</div>
            </div>
        `;
    }
    elements.registersGrid.innerHTML = html;
}

async function loadExamples() {
    try {
        const res = await fetch("/api/examples");
        const examples = await res.json();
        let html = "";
        examples.forEach((ex, idx) => {
            html += `
                <button class="example-btn" data-index="${idx}">
                    <div class="example-name">${ex.name}</div>
                    <div class="example-desc">${ex.description}</div>
                </button>
            `;
        });
        elements.examplesList.innerHTML = html;

        // Event listeners para ejemplos
        document.querySelectorAll(".example-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                const idx = parseInt(btn.dataset.index);
                elements.codeEditor.value = examples[idx].code;
                resetSimulation();
            });
        });

        // Cargar primer ejemplo por defecto
        if (examples.length > 0) {
            elements.codeEditor.value = examples[0].code;
        }
    } catch (err) {
        console.error("Error cargando ejemplos:", err);
    }
}

function setupEventListeners() {
    elements.btnSimulate.addEventListener("click", runSimulation);
    elements.btnPlay.addEventListener("click", togglePlay);
    elements.btnStep.addEventListener("click", stepForward);
    elements.btnReset.addEventListener("click", resetSimulation);

    elements.speedSlider.addEventListener("input", (e) => {
        state.speed = parseInt(e.target.value);
        elements.speedValue.textContent = state.speed + "ms";
        // Actualizar intervalo si esta reproduciendo
        if (state.isPlaying) {
            clearInterval(state.playInterval);
            state.playInterval = setInterval(stepForward, state.speed);
        }
    });

    // Tabs
    document.querySelectorAll(".tab").forEach((tab) => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
            document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));
            tab.classList.add("active");
            document.getElementById(tab.dataset.tab).classList.add("active");
        });
    });

    // Atajos de teclado
    document.addEventListener("keydown", (e) => {
        if (e.target.tagName === "TEXTAREA") return;
        if (e.key === " " || e.key === "Enter") {
            e.preventDefault();
            if (state.snapshots.length > 0) togglePlay();
        }
        if (e.key === "ArrowRight") {
            e.preventDefault();
            stepForward();
        }
        if (e.key === "ArrowLeft") {
            e.preventDefault();
            stepBackward();
        }
    });
}

// ============================================================
// Simulacion
// ============================================================
async function runSimulation() {
    const code = elements.codeEditor.value.trim();
    if (!code) return;

    elements.loading.classList.add("visible");
    elements.errorDisplay.classList.remove("visible");

    try {
        const res = await fetch("/api/simulate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                code: code,
                forwarding: elements.toggleForwarding.checked,
            }),
        });

        const data = await res.json();

        if (!res.ok) {
            showError(data.error || "Error desconocido");
            return;
        }

        state.snapshots = data.snapshots;
        state.pipelineTable = data.pipeline_table;
        state.stats = data.stats;
        state.currentCycle = 0;
        state.previousRegisters = new Array(32).fill(0);

        // Habilitar controles
        elements.btnPlay.disabled = false;
        elements.btnStep.disabled = false;
        elements.btnReset.disabled = false;

        // Mostrar vistas
        elements.pipelineEmpty.style.display = "none";
        elements.pipelineView.style.display = "block";
        elements.tableEmpty.style.display = "none";
        elements.tableView.style.display = "block";
        elements.statsEmpty.style.display = "none";
        elements.statsView.style.display = "block";

        // Renderizar
        renderPipelineTable();
        renderStats();
        displayCycle(0);

    } catch (err) {
        showError("Error de conexion con el servidor: " + err.message);
    } finally {
        elements.loading.classList.remove("visible");
    }
}

function showError(msg) {
    elements.errorDisplay.textContent = msg;
    elements.errorDisplay.classList.add("visible");
    elements.pipelineEmpty.style.display = "none";
    elements.pipelineView.style.display = "block";
}

function resetSimulation() {
    stopPlay();
    state.snapshots = [];
    state.pipelineTable = [];
    state.stats = null;
    state.currentCycle = 0;
    state.previousRegisters = new Array(32).fill(0);

    elements.btnPlay.disabled = true;
    elements.btnStep.disabled = true;
    elements.btnReset.disabled = true;

    elements.pipelineEmpty.style.display = "block";
    elements.pipelineView.style.display = "none";
    elements.tableEmpty.style.display = "block";
    elements.tableView.style.display = "none";
    elements.statsEmpty.style.display = "block";
    elements.statsView.style.display = "none";
    elements.errorDisplay.classList.remove("visible");

    initRegistersGrid();
}

// ============================================================
// Reproduccion
// ============================================================
function togglePlay() {
    if (state.isPlaying) {
        stopPlay();
    } else {
        startPlay();
    }
}

function startPlay() {
    if (state.currentCycle >= state.snapshots.length) {
        state.currentCycle = 0;
    }
    state.isPlaying = true;
    elements.btnPlay.textContent = "Pausa";
    elements.btnPlay.classList.remove("btn-success");
    elements.btnPlay.classList.add("btn-warning");
    state.playInterval = setInterval(() => {
        if (state.currentCycle >= state.snapshots.length - 1) {
            stopPlay();
            return;
        }
        stepForward();
    }, state.speed);
}

function stopPlay() {
    state.isPlaying = false;
    elements.btnPlay.textContent = "Play";
    elements.btnPlay.classList.remove("btn-warning");
    elements.btnPlay.classList.add("btn-success");
    if (state.playInterval) {
        clearInterval(state.playInterval);
        state.playInterval = null;
    }
}

function stepForward() {
    if (state.currentCycle < state.snapshots.length - 1) {
        state.previousRegisters = [...state.snapshots[state.currentCycle].registers];
        state.currentCycle++;
        displayCycle(state.currentCycle);
    }
}

function stepBackward() {
    if (state.currentCycle > 0) {
        state.currentCycle--;
        if (state.currentCycle > 0) {
            state.previousRegisters = [...state.snapshots[state.currentCycle - 1].registers];
        } else {
            state.previousRegisters = new Array(32).fill(0);
        }
        displayCycle(state.currentCycle);
    }
}

// ============================================================
// Renderizado del ciclo actual
// ============================================================
function displayCycle(cycleIndex) {
    const snap = state.snapshots[cycleIndex];
    if (!snap) return;

    // Numero de ciclo
    elements.cycleNumber.textContent = snap.cycle;

    // Etapas del pipeline
    const stageNames = ["FI", "DI", "EXE", "MEM", "WB"];
    const stageIds = ["fi", "di", "exe", "mem", "wb"];

    stageIds.forEach((id, i) => {
        const box = document.getElementById("stage-" + id);
        const instrEl = document.getElementById(id + "-instr");
        const stageData = snap.stages[stageNames[i]];

        box.classList.remove("has-bubble");

        if (stageData) {
            if (stageData.is_bubble) {
                instrEl.textContent = "BURBUJA";
                instrEl.className = "stage-instr";
                box.classList.add("has-bubble");
            } else {
                instrEl.textContent = stageData.instruction;
                instrEl.className = "stage-instr";
            }
        } else {
            instrEl.textContent = "---";
            instrEl.className = "stage-instr stage-empty";
        }
    });

    // Hazard alert
    if (snap.stall && snap.hazard) {
        elements.hazardAlert.classList.add("visible");
        elements.hazardTitle.textContent = `HAZARD ${snap.hazard.type} - Stall insertado`;
        elements.hazardDetail.innerHTML = `
            Registro <code>${snap.hazard.register}</code> en conflicto<br>
            Fuente: <code>${snap.hazard.instr_source}</code> (etapa ${snap.hazard.source_stage})<br>
            Espera: <code>${snap.hazard.instr_waiting}</code>
        `;
    } else {
        elements.hazardAlert.classList.remove("visible");
    }

    // Branch alert
    if (snap.branch_taken) {
        elements.branchAlert.classList.add("visible");
    } else {
        elements.branchAlert.classList.remove("visible");
    }

    // Registros
    for (let i = 0; i < 32; i++) {
        const regItem = document.getElementById("reg-" + i);
        const regVal = document.getElementById("reg-val-" + i);
        regVal.textContent = snap.registers[i];

        if (snap.registers[i] !== state.previousRegisters[i]) {
            regItem.classList.add("changed");
            setTimeout(() => regItem.classList.remove("changed"), 600);
        } else {
            regItem.classList.remove("changed");
        }
    }

    // Memoria
    const memEntries = Object.entries(snap.memory);
    if (memEntries.length > 0) {
        let memHtml = "";
        memEntries.forEach(([addr, val]) => {
            memHtml += `
                <div class="mem-item">
                    <div class="mem-addr">Mem[${addr}]</div>
                    <div class="mem-value">${val}</div>
                </div>
            `;
        });
        elements.memoryGrid.innerHTML = memHtml;
    } else {
        elements.memoryGrid.innerHTML = '<p class="memory-empty">Sin accesos a memoria</p>';
    }

    // Resaltar fila actual en tabla temporal
    highlightTableCycle(snap.cycle);
}

// ============================================================
// Tabla Temporal del Pipeline
// ============================================================
function renderPipelineTable() {
    if (!state.pipelineTable || state.pipelineTable.length === 0) return;

    const totalCycles = state.snapshots.length;

    let html = "<thead><tr><th>Instruccion</th>";
    for (let c = 1; c <= totalCycles; c++) {
        html += `<th>C${c}</th>`;
    }
    html += "</tr></thead><tbody>";

    state.pipelineTable.forEach((row) => {
        html += `<tr><th>${escapeHtml(row.instruction)}</th>`;
        for (let c = 1; c <= totalCycles; c++) {
            const stage = row.stages[String(c)];
            if (stage) {
                const cls = "stage-cell-" + stage.toLowerCase();
                html += `<td class="${cls}">${stage}</td>`;
            } else {
                html += `<td></td>`;
            }
        }
        html += "</tr>";
    });

    html += "</tbody>";
    elements.pipelineTable.innerHTML = html;
}

function highlightTableCycle(cycle) {
    // Resaltar columna del ciclo actual
    const table = elements.pipelineTable;
    const cells = table.querySelectorAll("th, td");
    cells.forEach((cell) => cell.style.opacity = "1");

    // Resaltar encabezado del ciclo
    const headerCells = table.querySelectorAll("thead th");
    headerCells.forEach((th, idx) => {
        if (idx === cycle) {
            th.style.color = "var(--accent-cyan)";
            th.style.fontWeight = "800";
        } else {
            th.style.color = "";
            th.style.fontWeight = "";
        }
    });
}

// ============================================================
// Estadisticas
// ============================================================
function renderStats() {
    if (!state.stats) return;

    const s = state.stats;
    elements.statsGrid.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${s.total_cycles}</div>
            <div class="stat-label">Ciclos Totales</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${s.total_instructions}</div>
            <div class="stat-label">Instrucciones</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${s.cpi}</div>
            <div class="stat-label">CPI (Ciclos/Instruccion)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${s.stalls}</div>
            <div class="stat-label">Stalls (Burbujas)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${s.branches_taken}</div>
            <div class="stat-label">Saltos Tomados</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${s.forwarding ? "SI" : "NO"}</div>
            <div class="stat-label">Forwarding Activo</div>
        </div>
    `;
}

// ============================================================
// Utilidades
// ============================================================
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
