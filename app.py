"""
Servidor Flask para el Simulador de Pipeline RISC.
Grupo: De blutus duais
Materia: Arquitectura de Computadores
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from simulator.assembler import parse
from simulator.pipeline import simulate

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    data = request.get_json()
    if not data or "code" not in data:
        return jsonify({"error": "Se requiere el campo 'code' con el codigo ensamblador."}), 400

    code = data["code"]
    forwarding = data.get("forwarding", False)

    try:
        instructions, labels = parse(code)
    except ValueError as e:
        return jsonify({"error": f"Error de ensamblado: {str(e)}"}), 400

    if not instructions:
        return jsonify({"error": "No se encontraron instrucciones validas."}), 400

    snapshots = simulate(instructions, forwarding_enabled=forwarding)

    # Construir tabla del pipeline (instruccion x ciclo)
    pipeline_table = []
    for instr in instructions:
        pipeline_table.append({
            "instruction": instr["raw"],
            "index": instr["index"],
            "stages": {},
        })

    for snap in snapshots:
        for stage_name, stage_data in snap["stages"].items():
            if stage_data and not stage_data.get("is_bubble") and stage_data["index"] >= 0:
                idx = stage_data["index"]
                if idx < len(pipeline_table):
                    pipeline_table[idx]["stages"][str(snap["cycle"])] = stage_name

    # Estadisticas
    total_cycles = len(snapshots)
    total_instructions = len(instructions)
    stalls = sum(1 for s in snapshots if s["stall"])
    branches = sum(1 for s in snapshots if s["branch_taken"])
    cpi = total_cycles / total_instructions if total_instructions > 0 else 0

    return jsonify({
        "snapshots": snapshots,
        "pipeline_table": pipeline_table,
        "stats": {
            "total_cycles": total_cycles,
            "total_instructions": total_instructions,
            "stalls": stalls,
            "branches_taken": branches,
            "cpi": round(cpi, 2),
            "forwarding": forwarding,
        },
        "labels": labels,
    })


@app.route("/api/examples", methods=["GET"])
def api_examples():
    examples = [
        {
            "name": "Suma Basica",
            "description": "Operaciones aritmeticas simples sin hazards",
            "code": (
                "# Suma Basica - Sin hazards\n"
                "ADDI $t0, $zero, 10    # $t0 = 10\n"
                "ADDI $t1, $zero, 20    # $t1 = 20\n"
                "NOP\n"
                "NOP\n"
                "ADD $t2, $t0, $t1     # $t2 = $t0 + $t1 = 30\n"
                "NOP\n"
                "NOP\n"
                "SUB $t3, $t2, $t0     # $t3 = $t2 - $t0 = 20\n"
                "HALT\n"
            ),
        },
        {
            "name": "Hazard de Datos (RAW)",
            "description": "Dependencia Read After Write - el pipeline inserta burbujas",
            "code": (
                "# Hazard de Datos RAW\n"
                "ADDI $t0, $zero, 5     # $t0 = 5\n"
                "ADD $t1, $t0, $t0      # $t1 = $t0 + $t0 (HAZARD: $t0 aun en pipeline)\n"
                "SUB $t2, $t1, $t0      # $t2 = $t1 - $t0 (HAZARD: $t1 aun en pipeline)\n"
                "HALT\n"
            ),
        },
        {
            "name": "Memoria (LW/SW)",
            "description": "Carga y almacenamiento en memoria con hazard Load-Use",
            "code": (
                "# Operaciones de Memoria\n"
                "ADDI $t0, $zero, 100   # $t0 = 100 (direccion)\n"
                "ADDI $t1, $zero, 42    # $t1 = 42 (valor)\n"
                "NOP\n"
                "NOP\n"
                "SW $t1, 0($t0)         # Mem[100] = 42\n"
                "LW $t2, 0($t0)         # $t2 = Mem[100] = 42\n"
                "ADD $t3, $t2, $t1      # HAZARD Load-Use: $t2 aun no disponible\n"
                "HALT\n"
            ),
        },
        {
            "name": "Salto Condicional (BEQ)",
            "description": "Salto con flush del pipeline cuando se toma la rama",
            "code": (
                "# Salto Condicional\n"
                "ADDI $t0, $zero, 5     # $t0 = 5\n"
                "ADDI $t1, $zero, 5     # $t1 = 5\n"
                "NOP\n"
                "NOP\n"
                "BEQ $t0, $t1, salto    # Si $t0 == $t1, saltar\n"
                "ADDI $t2, $zero, 99    # NO se ejecuta (flush)\n"
                "ADDI $t3, $zero, 99    # NO se ejecuta (flush)\n"
                "salto: ADDI $t4, $zero, 1  # Se ejecuta aqui\n"
                "HALT\n"
            ),
        },
        {
            "name": "Bucle (Loop)",
            "description": "Bucle que suma numeros del 1 al 5",
            "code": (
                "# Bucle: Suma de 1 a 5\n"
                "ADDI $t0, $zero, 0     # $t0 = suma = 0\n"
                "ADDI $t1, $zero, 1     # $t1 = contador = 1\n"
                "ADDI $t2, $zero, 6     # $t2 = limite = 6\n"
                "NOP\n"
                "NOP\n"
                "loop: ADD $t0, $t0, $t1  # suma += contador\n"
                "ADDI $t1, $t1, 1        # contador++\n"
                "NOP\n"
                "NOP\n"
                "BNE $t1, $t2, loop      # Si contador != limite, repetir\n"
                "NOP\n"
                "NOP\n"
                "HALT\n"
            ),
        },
    ]
    return jsonify(examples)


if __name__ == "__main__":
    app.run(debug=True, port=5050)
