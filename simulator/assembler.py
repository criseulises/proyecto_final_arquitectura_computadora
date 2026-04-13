"""
Ensamblador: Parsea código ensamblador MIPS simplificado a instrucciones.

Instrucciones soportadas:
  R-type: ADD, SUB, AND, OR, SLT
  I-type: ADDI, LW, SW, BEQ, BNE
  J-type: J
  Especiales: NOP, HALT
"""

import re


REGISTER_ALIASES = {
    "$zero": 0, "$at": 1, "$v0": 2, "$v1": 3,
    "$a0": 4, "$a1": 5, "$a2": 6, "$a3": 7,
    "$t0": 8, "$t1": 9, "$t2": 10, "$t3": 11,
    "$t4": 12, "$t5": 13, "$t6": 14, "$t7": 15,
    "$s0": 16, "$s1": 17, "$s2": 18, "$s3": 19,
    "$s4": 20, "$s5": 21, "$s6": 22, "$s7": 23,
    "$t8": 24, "$t9": 25, "$k0": 26, "$k1": 27,
    "$gp": 28, "$sp": 29, "$fp": 30, "$ra": 31,
}

R_TYPE_OPS = {"ADD", "SUB", "AND", "OR", "SLT"}
I_TYPE_OPS = {"ADDI", "BEQ", "BNE"}
MEM_OPS = {"LW", "SW"}
J_TYPE_OPS = {"J"}


def _parse_register(token):
    token = token.strip().rstrip(",")
    if token in REGISTER_ALIASES:
        return REGISTER_ALIASES[token]
    match = re.match(r"\$(\d+)", token)
    if match:
        num = int(match.group(1))
        if 0 <= num <= 31:
            return num
    raise ValueError(f"Registro invalido: {token}")


def _parse_mem_operand(token):
    """Parsea operandos tipo offset($reg) -> (offset, reg_num)"""
    match = re.match(r"(-?\d+)\((\$\w+)\)", token.strip())
    if not match:
        raise ValueError(f"Operando de memoria invalido: {token}")
    offset = int(match.group(1))
    reg = _parse_register(match.group(2))
    return offset, reg


def parse(assembly_text):
    """
    Parsea texto ensamblador y retorna lista de instrucciones.
    Soporta etiquetas (labels) para saltos.
    """
    lines = assembly_text.strip().split("\n")
    labels = {}
    clean_lines = []

    # Primera pasada: resolver etiquetas
    for line in lines:
        line = line.split("#")[0].strip()  # Remover comentarios
        if not line:
            continue
        if ":" in line:
            parts = line.split(":", 1)
            label = parts[0].strip()
            labels[label] = len(clean_lines)
            rest = parts[1].strip()
            if rest:
                clean_lines.append(rest)
        else:
            clean_lines.append(line)

    # Segunda pasada: parsear instrucciones
    instructions = []
    for idx, line in enumerate(clean_lines):
        tokens = line.replace(",", " ").split()
        op = tokens[0].upper()

        instr = {
            "op": op,
            "rd": None,
            "rs": None,
            "rt": None,
            "imm": None,
            "raw": line.strip(),
            "index": idx,
            "writes_reg": None,
            "reads_regs": [],
        }

        if op == "NOP":
            instr["writes_reg"] = None
            instr["reads_regs"] = []

        elif op == "HALT":
            instr["writes_reg"] = None
            instr["reads_regs"] = []

        elif op in R_TYPE_OPS:
            # ADD $rd, $rs, $rt
            instr["rd"] = _parse_register(tokens[1])
            instr["rs"] = _parse_register(tokens[2])
            instr["rt"] = _parse_register(tokens[3])
            instr["writes_reg"] = instr["rd"]
            instr["reads_regs"] = [instr["rs"], instr["rt"]]

        elif op == "ADDI":
            # ADDI $rt, $rs, imm
            instr["rt"] = _parse_register(tokens[1])
            instr["rs"] = _parse_register(tokens[2])
            instr["imm"] = int(tokens[3])
            instr["writes_reg"] = instr["rt"]
            instr["reads_regs"] = [instr["rs"]]

        elif op == "LW":
            # LW $rt, offset($rs)
            instr["rt"] = _parse_register(tokens[1])
            offset, rs = _parse_mem_operand(tokens[2])
            instr["rs"] = rs
            instr["imm"] = offset
            instr["writes_reg"] = instr["rt"]
            instr["reads_regs"] = [instr["rs"]]

        elif op == "SW":
            # SW $rt, offset($rs)
            instr["rt"] = _parse_register(tokens[1])
            offset, rs = _parse_mem_operand(tokens[2])
            instr["rs"] = rs
            instr["imm"] = offset
            instr["writes_reg"] = None
            instr["reads_regs"] = [instr["rt"], instr["rs"]]

        elif op in ("BEQ", "BNE"):
            # BEQ $rs, $rt, label/offset
            instr["rs"] = _parse_register(tokens[1])
            instr["rt"] = _parse_register(tokens[2])
            target = tokens[3]
            if target in labels:
                instr["imm"] = labels[target] - (idx + 1)
            else:
                instr["imm"] = int(target)
            instr["writes_reg"] = None
            instr["reads_regs"] = [instr["rs"], instr["rt"]]

        elif op == "J":
            # J label/address
            target = tokens[1]
            if target in labels:
                instr["imm"] = labels[target]
            else:
                instr["imm"] = int(target)
            instr["writes_reg"] = None
            instr["reads_regs"] = []

        else:
            raise ValueError(f"Instruccion no reconocida: {op}")

        # $0 nunca se escribe
        if instr["writes_reg"] == 0:
            instr["writes_reg"] = None

        # Filtrar $0 de lecturas (siempre es 0, no causa hazard)
        instr["reads_regs"] = [r for r in instr["reads_regs"] if r != 0]

        instructions.append(instr)

    return instructions, labels
