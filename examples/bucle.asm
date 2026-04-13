# Bucle: Suma de numeros del 1 al 5
# Resultado esperado: $t0 = 15 (1+2+3+4+5)

ADDI $t0, $zero, 0     # $t0 = suma = 0
ADDI $t1, $zero, 1     # $t1 = contador = 1
ADDI $t2, $zero, 6     # $t2 = limite = 6
NOP
NOP
loop: ADD $t0, $t0, $t1  # suma += contador
ADDI $t1, $t1, 1        # contador++
NOP
NOP
BNE $t1, $t2, loop      # Si contador != limite, repetir
NOP
NOP
HALT
