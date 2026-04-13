# Hazard de Datos RAW (Read After Write)
# El pipeline detecta dependencias e inserta burbujas automaticamente

ADDI $t0, $zero, 5     # $t0 = 5
ADD $t1, $t0, $t0      # HAZARD: $t0 aun no escrito cuando se lee
SUB $t2, $t1, $t0      # HAZARD: $t1 aun no escrito cuando se lee
HALT
