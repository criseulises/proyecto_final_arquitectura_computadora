# Salto Condicional con BEQ
# Cuando el salto se toma, el pipeline hace flush de las instrucciones posteriores

ADDI $t0, $zero, 5     # $t0 = 5
ADDI $t1, $zero, 5     # $t1 = 5
NOP
NOP
BEQ $t0, $t1, salto    # Si $t0 == $t1, saltar a 'salto'
ADDI $t2, $zero, 99    # NO se ejecuta (flush por salto)
ADDI $t3, $zero, 99    # NO se ejecuta (flush por salto)
salto: ADDI $t4, $zero, 1  # Destino del salto
HALT
