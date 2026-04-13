# Operaciones de Memoria con Hazard Load-Use
# Demuestra LW, SW y el hazard cuando se usa un dato recien cargado

ADDI $t0, $zero, 100   # $t0 = 100 (direccion base)
ADDI $t1, $zero, 42    # $t1 = 42 (valor a guardar)
NOP
NOP
SW $t1, 0($t0)         # Mem[100] = 42
LW $t2, 0($t0)         # $t2 = Mem[100] = 42
ADD $t3, $t2, $t1      # HAZARD Load-Use: $t2 no disponible
HALT
