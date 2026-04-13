"""
Simulador de Pipeline RISC de 5 etapas.

Etapas: FI (Fetch), DI (Decode), EXE (Execute), MEM (Memory), WB (Write Back)

Detecta hazards de datos (RAW) e inserta burbujas (stalls).
Maneja saltos con flush del pipeline (2 ciclos de penalizacion).
"""

from copy import deepcopy


def simulate(instructions, forwarding_enabled=False):
    """
    Ejecuta la simulacion completa del pipeline.
    Retorna una lista de snapshots, uno por cada ciclo.
    """
    if not instructions:
        return []

    # Estado del CPU
    registers = [0] * 32
    memory = {}
    pc = 0
    halted = False
    flushing = False

    # Pipeline: cada etapa tiene una instruccion o None
    stages = {"FI": None, "DI": None, "EXE": None, "MEM": None, "WB": None}

    snapshots = []
    cycle = 0
    max_cycles = 500  # Limite de seguridad

    while cycle < max_cycles:
        cycle += 1
        stall = False
        hazard_info = None
        branch_taken = False
        branch_target = None

        # ============================================================
        # ETAPA WB: Write Back
        # ============================================================
        wb_instr = stages["WB"]
        if wb_instr and wb_instr.get("wb_value") is not None and wb_instr.get("writes_reg"):
            reg = wb_instr["writes_reg"]
            if reg != 0:
                registers[reg] = wb_instr["wb_value"]

        # ============================================================
        # ETAPA MEM: Acceso a Memoria
        # ============================================================
        mem_instr = stages["MEM"]
        if mem_instr:
            op = mem_instr["op"]
            if op == "LW":
                addr = mem_instr.get("alu_result", 0)
                mem_instr["wb_value"] = memory.get(addr, 0)
            elif op == "SW":
                addr = mem_instr.get("alu_result", 0)
                memory[addr] = mem_instr.get("store_value", 0)
                mem_instr["wb_value"] = None
            else:
                mem_instr["wb_value"] = mem_instr.get("alu_result")

        # ============================================================
        # ETAPA EXE: Ejecucion
        # ============================================================
        exe_instr = stages["EXE"]
        if exe_instr:
            op = exe_instr["op"]
            rs_val = exe_instr.get("rs_val", 0)
            rt_val = exe_instr.get("rt_val", 0)
            imm = exe_instr.get("imm", 0) or 0

            # Forwarding desde MEM y WB
            if forwarding_enabled:
                rs_reg = exe_instr.get("rs")
                rt_reg = exe_instr.get("rt")

                # Forward desde MEM
                if mem_instr and mem_instr.get("writes_reg"):
                    fwd_reg = mem_instr["writes_reg"]
                    fwd_val = mem_instr.get("alu_result", 0)
                    if mem_instr["op"] != "LW":  # LW no disponible aun
                        if rs_reg == fwd_reg and rs_reg != 0:
                            rs_val = fwd_val
                        if rt_reg == fwd_reg and rt_reg != 0:
                            rt_val = fwd_val

                # Forward desde WB
                if wb_instr and wb_instr.get("writes_reg"):
                    fwd_reg = wb_instr["writes_reg"]
                    fwd_val = wb_instr.get("wb_value", 0)
                    if rs_reg == fwd_reg and rs_reg != 0:
                        if not (mem_instr and mem_instr.get("writes_reg") == fwd_reg and mem_instr["op"] != "LW"):
                            rs_val = fwd_val
                    if rt_reg == fwd_reg and rt_reg != 0:
                        if not (mem_instr and mem_instr.get("writes_reg") == fwd_reg and mem_instr["op"] != "LW"):
                            rt_val = fwd_val

            alu_result = 0
            if op == "ADD":
                alu_result = rs_val + rt_val
            elif op == "SUB":
                alu_result = rs_val - rt_val
            elif op == "AND":
                alu_result = rs_val & rt_val
            elif op == "OR":
                alu_result = rs_val | rt_val
            elif op == "SLT":
                alu_result = 1 if rs_val < rt_val else 0
            elif op == "ADDI":
                alu_result = rs_val + imm
            elif op in ("LW", "SW"):
                alu_result = rs_val + imm
                if op == "SW":
                    exe_instr["store_value"] = rt_val
            elif op == "BEQ":
                if rs_val == rt_val:
                    branch_taken = True
                    branch_target = exe_instr["pc_at_fetch"] + 1 + imm
            elif op == "BNE":
                if rs_val != rt_val:
                    branch_taken = True
                    branch_target = exe_instr["pc_at_fetch"] + 1 + imm
            elif op == "J":
                branch_taken = True
                branch_target = imm

            exe_instr["alu_result"] = alu_result

        # ============================================================
        # Deteccion de Hazards de Datos (RAW)
        # ============================================================
        di_instr = stages["DI"]
        if di_instr and di_instr["op"] not in ("NOP", "HALT"):
            reads = di_instr.get("reads_regs", [])

            if reads:
                # Verificar contra instruccion en EXE
                if exe_instr and exe_instr.get("writes_reg"):
                    exe_dest = exe_instr["writes_reg"]
                    if exe_dest in reads:
                        if forwarding_enabled:
                            if exe_instr["op"] == "LW":
                                stall = True
                                hazard_info = {
                                    "type": "Load-Use",
                                    "source_stage": "EXE",
                                    "register": f"${exe_dest}",
                                    "instr_source": exe_instr["raw"],
                                    "instr_waiting": di_instr["raw"],
                                }
                        else:
                            stall = True
                            hazard_info = {
                                "type": "RAW",
                                "source_stage": "EXE",
                                "register": f"${exe_dest}",
                                "instr_source": exe_instr["raw"],
                                "instr_waiting": di_instr["raw"],
                            }

                # Verificar contra instruccion en MEM (solo sin forwarding)
                if not forwarding_enabled and not stall:
                    if mem_instr and mem_instr.get("writes_reg"):
                        mem_dest = mem_instr["writes_reg"]
                        if mem_dest in reads:
                            stall = True
                            hazard_info = {
                                "type": "RAW",
                                "source_stage": "MEM",
                                "register": f"${mem_dest}",
                                "instr_source": mem_instr["raw"],
                                "instr_waiting": di_instr["raw"],
                            }

        # ============================================================
        # Avanzar el Pipeline
        # ============================================================

        # WB se descarta
        stages["WB"] = stages["MEM"]

        # MEM <- EXE
        stages["MEM"] = stages["EXE"]

        if stall:
            # Insertar burbuja en EXE, mantener FI y DI
            stages["EXE"] = _make_bubble()
        else:
            # EXE <- DI
            if di_instr and di_instr["op"] not in ("NOP", "HALT"):
                # Leer valores de registros
                if di_instr.get("rs") is not None:
                    di_instr["rs_val"] = registers[di_instr["rs"]]
                if di_instr.get("rt") is not None:
                    di_instr["rt_val"] = registers[di_instr["rt"]]
            stages["EXE"] = stages["DI"]

            if branch_taken:
                # Flush: limpiar FI y DI
                stages["DI"] = _make_bubble()
                stages["FI"] = _make_bubble()
                pc = branch_target
                flushing = True
            else:
                # DI <- FI
                stages["DI"] = stages["FI"]

                # FI <- nueva instruccion
                if not halted and pc < len(instructions):
                    new_instr = deepcopy(instructions[pc])
                    new_instr["pc_at_fetch"] = pc
                    stages["FI"] = new_instr
                    if new_instr["op"] == "HALT":
                        halted = True
                    pc += 1
                else:
                    stages["FI"] = None
                    halted = True

            if flushing and not branch_taken:
                flushing = False

        # Si hubo branch, en el siguiente ciclo fetch desde branch_target
        if branch_taken:
            flushing = False

        # ============================================================
        # Guardar snapshot del ciclo
        # ============================================================
        snapshot = {
            "cycle": cycle,
            "stages": {},
            "registers": list(registers),
            "memory": {str(k): v for k, v in sorted(memory.items())},
            "stall": stall,
            "hazard": hazard_info,
            "branch_taken": branch_taken,
            "pc": pc,
        }

        for stage_name in ["FI", "DI", "EXE", "MEM", "WB"]:
            s = stages[stage_name]
            if s and s.get("is_bubble"):
                snapshot["stages"][stage_name] = {
                    "instruction": "BURBUJA",
                    "index": -1,
                    "is_bubble": True,
                }
            elif s:
                snapshot["stages"][stage_name] = {
                    "instruction": s["raw"],
                    "index": s.get("index", -1),
                    "is_bubble": False,
                }
            else:
                snapshot["stages"][stage_name] = None

        snapshots.append(snapshot)

        # Terminar si pipeline esta vacio
        all_empty = all(
            stages[s] is None or stages[s].get("is_bubble")
            for s in ["FI", "DI", "EXE", "MEM", "WB"]
        )
        if halted and all_empty:
            break

    return snapshots


def _make_bubble():
    return {
        "op": "NOP",
        "raw": "BURBUJA",
        "is_bubble": True,
        "writes_reg": None,
        "reads_regs": [],
    }
