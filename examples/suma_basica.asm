# Suma Basica - Sin hazards de datos
# Demuestra el flujo normal del pipeline sin conflictos

ADDI $t0, $zero, 10    # $t0 = 10
ADDI $t1, $zero, 20    # $t1 = 20
NOP                     # Esperar para evitar hazard
NOP                     # Esperar para evitar hazard
ADD $t2, $t0, $t1      # $t2 = $t0 + $t1 = 30
NOP
NOP
SUB $t3, $t2, $t0      # $t3 = $t2 - $t0 = 20
HALT
