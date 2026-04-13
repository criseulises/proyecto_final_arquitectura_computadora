# Simulador de Pipeline RISC Clasico

## Informacion del Proyecto

- **Materia:** Arquitectura de Computadores
- **Grupo:** De blutus duais
- **Integrantes:**
  - Alejandro Bruno De Oleo
  - Cristian Alberto Tejeda Rojas
  - Cristian Eulises Sanchez Ramirez
  - Hansel Augusto Perez Espinosa
  - Lia Johanna De Oleo Cuello

---

## Tabla de Contenidos

1. [Descripcion del Proyecto](#descripcion-del-proyecto)
2. [Marco Teorico](#marco-teorico)
   - [Que es un Procesador y Como Ejecuta Instrucciones](#que-es-un-procesador-y-como-ejecuta-instrucciones)
   - [Procesador Monociclo vs Segmentado](#procesador-monociclo-vs-segmentado)
   - [Que es el Pipelining (Segmentacion)](#que-es-el-pipelining-segmentacion)
   - [Las 5 Etapas del Pipeline](#las-5-etapas-del-pipeline)
   - [Riesgos en el Pipeline (Hazards)](#riesgos-en-el-pipeline-hazards)
   - [Burbujas y Stalls](#burbujas-y-stalls)
   - [Adelanto de Datos (Data Forwarding)](#adelanto-de-datos-data-forwarding)
   - [Riesgos de Control (Branch Hazards)](#riesgos-de-control-branch-hazards)
   - [Metricas de Rendimiento](#metricas-de-rendimiento)
3. [Como Funciona el Simulador](#como-funciona-el-simulador)
   - [Arquitectura del Software](#arquitectura-del-software)
   - [Flujo de Ejecucion Interno](#flujo-de-ejecucion-interno)
   - [Algoritmo de Deteccion de Hazards](#algoritmo-de-deteccion-de-hazards)
   - [Algoritmo de Forwarding](#algoritmo-de-forwarding)
   - [Manejo de Saltos](#manejo-de-saltos)
4. [Conjunto de Instrucciones](#conjunto-de-instrucciones)
5. [Registros del Procesador](#registros-del-procesador)
6. [Instalacion y Ejecucion](#instalacion-y-ejecucion)
7. [Guia de Uso del Simulador](#guia-de-uso-del-simulador)
8. [Programas de Ejemplo Incluidos](#programas-de-ejemplo-incluidos)
9. [Estructura del Proyecto](#estructura-del-proyecto)
10. [Referencias Bibliograficas](#referencias-bibliograficas)

---

## Descripcion del Proyecto

Este proyecto es un simulador visual e interactivo de un procesador RISC con pipeline de 5 etapas. La herramienta toma codigo ensamblador MIPS simplificado, lo ejecuta ciclo a ciclo a traves de las 5 etapas del pipeline y muestra graficamente:

- Como fluyen las instrucciones a traves de cada etapa del pipeline.
- Donde ocurren los riesgos de datos (hazards) y por que.
- Como el procesador inserta burbujas (stalls) para resolver los conflictos.
- Como la tecnica de forwarding reduce las penalizaciones.
- Que sucede cuando un salto condicional se toma y el pipeline debe vaciarse (flush).
- El estado de los 32 registros y la memoria en cada ciclo de reloj.

El objetivo es permitir visualizar y comprender de forma practica los conceptos fundamentales de la segmentacion de instrucciones que se estudian en la materia de Arquitectura de Computadores.

---

## Marco Teorico

### Que es un Procesador y Como Ejecuta Instrucciones

Un procesador (CPU) es el componente central de una computadora que ejecuta las instrucciones de los programas. Cada instruccion pasa por una serie de pasos internos para completarse. En su forma mas basica, el procesador:

1. **Busca** la instruccion en la memoria (usando el Program Counter o PC).
2. **Decodifica** la instruccion para entender que operacion realizar y que datos necesita.
3. **Ejecuta** la operacion (suma, resta, comparacion, etc.) en la ALU (Unidad Aritmetico-Logica).
4. **Accede a memoria** si la instruccion lo requiere (cargar o almacenar datos).
5. **Escribe el resultado** de vuelta en un registro del procesador.

Estos 5 pasos son los que conforman las 5 etapas del pipeline.

### Procesador Monociclo vs Segmentado

Para entender por que existe el pipeline, primero hay que entender como funciona un procesador **sin** pipeline (monociclo):

**Procesador Monociclo:**
- Ejecuta una instruccion completa en un solo ciclo de reloj.
- El ciclo de reloj debe ser lo suficientemente largo para que la instruccion mas lenta pueda completarse.
- Mientras una instruccion se ejecuta, el resto del hardware esta inactivo.
- Si la instruccion mas lenta tarda 800ps (picosegundos), TODAS las instrucciones tardan 800ps, aunque algunas podrian completarse en 200ps.

```
Instruccion 1: |===== FI ===== DI ===== EXE ===== MEM ===== WB =====|
Instruccion 2:                                                        |===== FI ===== DI ===== EXE ===== MEM ===== WB =====|
Instruccion 3:                                                                                                              |===== FI ===== ...
```

Cada instruccion espera a que la anterior termine completamente. El hardware esta subutilizado.

**Procesador Segmentado (Pipelined):**
- Divide la ejecucion en etapas independientes.
- Cada etapa trabaja en una instruccion diferente al mismo tiempo.
- El ciclo de reloj es el tiempo de la etapa mas lenta (mucho mas corto).
- Multiples instrucciones se ejecutan en paralelo, cada una en una etapa distinta.

```
Instruccion 1: | FI | DI | EXE | MEM | WB |
Instruccion 2:      | FI | DI  | EXE | MEM | WB |
Instruccion 3:           | FI  | DI  | EXE | MEM | WB |
Instruccion 4:                 | FI  | DI  | EXE | MEM | WB |
Instruccion 5:                       | FI  | DI  | EXE | MEM | WB |
```

**Analogia:** El pipeline funciona como una linea de ensamblaje en una fabrica. En una fabrica de carros, no se espera a terminar un carro completo antes de empezar el siguiente. Mientras un carro se pinta, otro se ensambla y otro se prueba, todo al mismo tiempo. Cada estacion de trabajo (etapa) siempre esta ocupada.

**Ganancia teorica:** Con un pipeline de 5 etapas, el rendimiento ideal es 5 veces mayor que el procesador monociclo, porque en estado estable se completa una instruccion por ciclo (en vez de una cada 5 ciclos).

### Que es el Pipelining (Segmentacion)

El **pipelining** o **segmentacion de instrucciones** es una tecnica de implementacion de procesadores que permite ejecutar multiples instrucciones de forma solapada. La idea central es:

1. Dividir la ejecucion de cada instruccion en N etapas independientes.
2. Cada etapa tiene su propio hardware dedicado.
3. En cada ciclo de reloj, una nueva instruccion entra al pipeline.
4. Cuando el pipeline esta lleno, se completa una instruccion por ciclo.

**Puntos clave del pipelining:**

- **No reduce la latencia** de una instruccion individual (una instruccion sigue tardando 5 ciclos de principio a fin).
- **Si aumenta el throughput** (numero de instrucciones completadas por unidad de tiempo).
- La ganancia viene del paralelismo: mientras la instruccion 1 esta en EXE, la instruccion 2 esta en DI y la instruccion 3 esta en FI, todas al mismo tiempo.
- El pipeline es mas eficiente cuantas mas instrucciones se ejecuten en secuencia sin interrupciones.

### Las 5 Etapas del Pipeline

El pipeline clasico RISC de 5 etapas se compone de:

#### Etapa 1: FI (Fetch de Instruccion)

**Que hace:** Busca la siguiente instruccion en la memoria de instrucciones.

**Como funciona:**
- Lee el valor del **Program Counter (PC)**, que contiene la direccion de la siguiente instruccion a ejecutar.
- Accede a la memoria de instrucciones en esa direccion.
- Carga la instruccion en el registro de pipeline FI/DI.
- Incrementa el PC en 1 (PC = PC + 1) para apuntar a la siguiente instruccion.

**Hardware involucrado:** Memoria de instrucciones, Program Counter, sumador para PC+1.

**Ejemplo:** Si PC = 0, busca la instruccion en la posicion 0 de la memoria. Si esa instruccion es `ADDI $t0, $zero, 10`, la carga y pasa PC a 1.

#### Etapa 2: DI (Decodificacion / Lectura de Registros)

**Que hace:** Decodifica la instruccion para determinar que operacion realizar y lee los valores de los registros fuente.

**Como funciona:**
- Analiza los campos de la instruccion: codigo de operacion (opcode), registros fuente (rs, rt), registro destino (rd), valor inmediato.
- Lee los valores de los registros fuente del **banco de registros** (register file).
- Genera las senales de control que le dicen al resto del pipeline que operacion realizar.
- Extiende el signo del valor inmediato (si aplica).

**Hardware involucrado:** Unidad de control, banco de registros (32 registros), extensor de signo.

**Ejemplo:** Para `ADD $t2, $t0, $t1`: identifica que es una suma, lee el valor de $t0 y $t1 del banco de registros, y marca que el resultado ira a $t2.

#### Etapa 3: EXE (Ejecucion / Calculo de Direcciones)

**Que hace:** Realiza la operacion aritmetica o logica en la ALU, o calcula la direccion de memoria.

**Como funciona:**
- Para instrucciones aritmeticas (ADD, SUB, AND, OR, SLT): la ALU realiza la operacion con los valores leidos en DI.
- Para instrucciones de memoria (LW, SW): la ALU calcula la direccion efectiva sumando el registro base mas el desplazamiento (offset).
- Para saltos condicionales (BEQ, BNE): la ALU compara los dos registros y determina si el salto debe tomarse. Si se toma, calcula la direccion destino del salto.

**Hardware involucrado:** ALU (Unidad Aritmetico-Logica), multiplexores de entrada.

**Ejemplo:** Para `ADD $t2, $t0, $t1` donde $t0=10 y $t1=20: la ALU calcula 10 + 20 = 30.
Para `LW $t2, 0($t0)` donde $t0=100: la ALU calcula 100 + 0 = 100 (direccion de memoria).

#### Etapa 4: MEM (Acceso a Memoria)

**Que hace:** Accede a la memoria de datos para leer o escribir.

**Como funciona:**
- Para `LW` (Load Word): lee el dato de la memoria en la direccion calculada en EXE y lo pasa a la siguiente etapa.
- Para `SW` (Store Word): escribe el valor del registro en la direccion de memoria calculada en EXE.
- Para las demas instrucciones: esta etapa no hace nada, simplemente pasa el resultado de la ALU a la siguiente etapa.

**Hardware involucrado:** Memoria de datos (lectura y escritura).

**Ejemplo:** Para `LW $t2, 0($t0)` con direccion 100: lee el valor almacenado en Mem[100] y lo pasa a WB.
Para `SW $t1, 0($t0)` con $t1=42 y direccion 100: escribe 42 en Mem[100].

#### Etapa 5: WB (Write Back)

**Que hace:** Escribe el resultado final de vuelta en el banco de registros.

**Como funciona:**
- Para instrucciones aritmeticas: escribe el resultado de la ALU en el registro destino.
- Para `LW`: escribe el dato leido de memoria en el registro destino.
- Para `SW`, `BEQ`, `BNE`: no escribe nada (estas instrucciones no producen un resultado para un registro).

**Hardware involucrado:** Banco de registros (puerto de escritura).

**Ejemplo:** Para `ADD $t2, $t0, $t1` con resultado 30: escribe 30 en el registro $t2.

#### Registros de Pipeline (Pipeline Registers)

Entre cada etapa existen **registros de pipeline** (tambien llamados registros inter-etapa) que almacenan toda la informacion necesaria para que la siguiente etapa pueda trabajar. Estos registros son:

- **FI/DI:** Almacena la instruccion buscada.
- **DI/EXE:** Almacena los valores de registros leidos, senales de control, y el inmediato.
- **EXE/MEM:** Almacena el resultado de la ALU, el valor a escribir en memoria, y senales de control.
- **MEM/WB:** Almacena el dato leido de memoria o el resultado de la ALU, y la senal de escritura.

Estos registros se actualizan en cada flanco de reloj, permitiendo que cada etapa trabaje de forma independiente.

### Riesgos en el Pipeline (Hazards)

Los **hazards** (riesgos) son situaciones que impiden que la siguiente instruccion se ejecute en el ciclo que le corresponderia. Son el principal problema del pipelining y reducen su rendimiento ideal. Existen tres tipos:

#### 1. Riesgos de Datos (Data Hazards)

Ocurren cuando una instruccion depende del resultado de una instruccion anterior que aun no ha completado su ejecucion en el pipeline.

**Tipo RAW (Read After Write) - El mas comun:**

Una instruccion intenta **leer** un registro que una instruccion anterior aun no ha **escrito**.

```
ADDI $t0, $zero, 5     # Escribe $t0 en la etapa WB (ciclo 5)
ADD  $t1, $t0, $t0     # Lee $t0 en la etapa DI (ciclo 3) - PROBLEMA!
```

En el ciclo 3:
- `ADDI` esta en EXE, aun no ha escrito $t0 (eso ocurre en WB, ciclo 5).
- `ADD` esta en DI, necesita leer $t0 AHORA.
- El valor de $t0 todavia es 0 (el valor anterior), no 5.
- Si el pipeline no detecta esto, `ADD` leeria un valor INCORRECTO.

**Por que ocurre:** En un procesador sin pipeline, `ADDI` terminaria completamente antes de que `ADD` empiece. Pero en el pipeline, `ADD` entra al pipeline antes de que `ADDI` haya terminado de escribir su resultado. Esta es la contrapartida del paralelismo.

**Otros tipos de riesgos de datos (menos comunes en RISC):**
- **WAR (Write After Read):** Una instruccion escribe un registro antes de que la anterior lo lea. Raro en pipelines de 5 etapas porque la escritura ocurre despues de la lectura en el orden del pipeline.
- **WAW (Write After Write):** Dos instrucciones escriben el mismo registro y lo hacen en orden incorrecto. Raro en pipelines simples.

Este simulador detecta y maneja los riesgos RAW, que son los unicos que ocurren en un pipeline RISC clasico de 5 etapas.

#### 2. Riesgos Estructurales (Structural Hazards)

Ocurren cuando dos instrucciones necesitan usar el mismo recurso de hardware al mismo tiempo. Por ejemplo, si la memoria de instrucciones y la memoria de datos fueran la misma, no se podria hacer un fetch (FI) y un acceso a memoria (MEM) en el mismo ciclo.

En la arquitectura MIPS/RISC que simula este proyecto, se asume que la memoria de instrucciones y la memoria de datos estan separadas (arquitectura Harvard), por lo que no hay riesgos estructurales.

#### 3. Riesgos de Control (Control Hazards)

Ocurren con las instrucciones de salto (BEQ, BNE, J). El problema es que el pipeline ya busco las instrucciones siguientes al salto antes de saber si el salto se tomara o no. Se explican en detalle mas adelante.

### Burbujas y Stalls

Cuando se detecta un riesgo de datos RAW, el procesador debe **detener** (stall) las etapas anteriores del pipeline e insertar una **burbuja** (NOP) en la etapa donde ocurre el conflicto. Esto se conoce como un **pipeline stall**.

**Como funciona un stall:**

1. Se detecta que la instruccion en DI necesita un registro que la instruccion en EXE (o MEM) aun no ha escrito.
2. Se inserta una **burbuja** (instruccion NOP vacia) en la etapa EXE.
3. La instruccion en DI se **detiene** (no avanza a EXE).
4. La instruccion en FI tambien se **detiene** (no avanza a DI).
5. Las etapas MEM y WB continuan normalmente.
6. Se repite hasta que el dato conflictivo este disponible.

**Ejemplo visual con stall:**

Sin stall (resultado INCORRECTO):
```
Ciclo:          1    2    3    4    5    6    7
ADDI $t0,...:   FI   DI   EXE  MEM  WB
ADD $t1,$t0,:        FI   DI   EXE  MEM  WB        <- Lee $t0 en ciclo 3, pero $t0 se escribe en ciclo 5!
```

Con stall (resultado CORRECTO):
```
Ciclo:          1    2    3    4    5    6    7    8    9
ADDI $t0,...:   FI   DI   EXE  MEM  WB
ADD $t1,$t0,:        FI   DI   DI   DI   EXE  MEM  WB  <- Espera hasta que $t0 este escrito
                               [burbuja] [burbuja]
```

La instruccion `ADD` se detiene en DI durante 2 ciclos extra, esperando a que `ADDI` escriba $t0 en WB.

**Costo:** Cada burbuja representa un ciclo de reloj desperdiciado. El pipeline no esta completando ninguna instruccion util en esos ciclos. Por eso los stalls degradan el rendimiento.

### Adelanto de Datos (Data Forwarding)

El **forwarding** (tambien llamado **bypassing**) es una tecnica de hardware que reduce drasticamente los stalls. La idea es:

**En vez de esperar a que el dato se escriba en el banco de registros (etapa WB), se pasa el resultado directamente desde la etapa donde ya esta calculado hacia la etapa que lo necesita.**

**Como funciona:**

1. Cuando una instruccion calcula su resultado en EXE, ese resultado ya existe en el registro de pipeline EXE/MEM.
2. Si la siguiente instruccion necesita ese resultado en su etapa EXE, el hardware lo "adelanta" directamente desde EXE/MEM, sin esperar a que pase por MEM y WB.
3. Se agregan multiplexores y caminos de datos adicionales para hacer esto posible.

**Caminos de forwarding implementados:**

- **EXE/MEM -> EXE:** El resultado de una instruccion en MEM se adelanta a la instruccion en EXE. Elimina 1 stall.
- **MEM/WB -> EXE:** El resultado de una instruccion en WB se adelanta a la instruccion en EXE. Elimina 2 stalls.

**Ejemplo sin forwarding (2 stalls):**
```
Ciclo:          1    2    3    4    5    6    7    8    9
ADDI $t0,...:   FI   DI   EXE  MEM  WB
ADD $t1,$t0,:        FI   DI   [B]  [B]  EXE  MEM  WB    <- 2 burbujas, espera WB
```

**Ejemplo con forwarding (0 stalls):**
```
Ciclo:          1    2    3    4    5    6    7
ADDI $t0,...:   FI   DI   EXE  MEM  WB
ADD $t1,$t0,:        FI   DI   EXE  MEM  WB              <- Recibe $t0 de EXE/MEM por forwarding
                               ^----'
                         Forwarding directo
```

**Excepcion - Hazard Load-Use:**

Hay un caso donde el forwarding NO puede eliminar el stall completamente: cuando una instruccion `LW` es seguida inmediatamente por una instruccion que usa el dato cargado.

```
LW  $t2, 0($t0)       # El dato de $t2 no esta disponible hasta el final de MEM
ADD $t3, $t2, $t1      # Necesita $t2 en EXE, pero aun no salio de MEM
```

El dato de `LW` no esta disponible hasta que termina la etapa MEM (porque hay que leerlo de memoria). Pero la instruccion siguiente necesita el dato al inicio de EXE. Como MEM ocurre DESPUES de EXE en el tiempo, no se puede adelantar algo que aun no existe.

**Solucion:** Se inserta 1 burbuja (en vez de 2 sin forwarding), y luego se usa forwarding MEM/WB -> EXE:

```
Ciclo:          1    2    3    4    5    6    7    8
LW $t2, 0($t0): FI   DI   EXE  MEM  WB
ADD $t3,$t2,$t1:      FI   DI   [B]  EXE  MEM  WB       <- 1 burbuja + forwarding
                                      ^----'
                                Forwarding desde MEM/WB
```

El simulador muestra este comportamiento: con forwarding activado, los hazards normales se eliminan completamente, pero los hazards load-use aun requieren 1 stall.

### Riesgos de Control (Branch Hazards)

Los riesgos de control ocurren con las instrucciones de salto condicional (BEQ, BNE). El problema fundamental es:

**El procesador no sabe si el salto se tomara o no hasta que la instruccion llega a la etapa EXE** (donde se comparan los registros). Pero para ese momento, ya se han buscado 2 instrucciones siguientes al salto que podrian ser incorrectas.

**Que pasa cuando un salto se toma:**

```
Ciclo:          1    2    3    4    5    6    7    8
BEQ $t0,$t1,L:  FI   DI   EXE  MEM  WB                  <- En ciclo 3 se sabe que el salto se toma
Instr. sig. 1:       FI   DI   X                         <- Ya entro al pipeline, hay que descartarla
Instr. sig. 2:            FI   X                          <- Ya entro al pipeline, hay que descartarla
Instr. en L:                   FI   DI   EXE  MEM  WB    <- La instruccion correcta (destino del salto)
```

Las instrucciones que entraron al pipeline despues del salto pero antes de saber el resultado deben ser **descartadas** (flushed). Se reemplazan por burbujas. Esto causa una **penalizacion de 2 ciclos** por cada salto tomado.

**En este simulador:**
- El salto se resuelve en la etapa EXE.
- Si el salto se toma: se hace flush de FI y DI (2 ciclos perdidos).
- Si el salto no se toma: no hay penalizacion, las instrucciones siguientes eran correctas.
- Se muestra visualmente con una alerta amarilla "SALTO TOMADO - Pipeline flushed".

**Tecnicas avanzadas (no implementadas pero para referencia):**
- **Prediccion de saltos:** Intentar adivinar si el salto se tomara antes de saberlo, para reducir la penalizacion. Predictores de 1 bit, 2 bits, correlacionados, etc.
- **Branch delay slot:** Ejecutar siempre la instruccion despues del salto (MIPS original usa esto).
- **Resolucion temprana:** Mover la comparacion del salto a la etapa DI para reducir la penalizacion a 1 ciclo.

### Metricas de Rendimiento

El simulador calcula estas metricas para evaluar el rendimiento del pipeline:

#### CPI (Cycles Per Instruction - Ciclos Por Instruccion)

El CPI indica cuantos ciclos de reloj se necesitan en promedio para completar una instruccion.

**Formula:**
```
CPI = Ciclos totales / Numero de instrucciones
```

- **CPI ideal del pipeline = 1.0:** Una instruccion se completa por ciclo (despues de llenar el pipeline).
- **CPI > 1.0:** Hay penalizaciones (stalls por hazards, flushes por saltos).
- **CPI del monociclo = 5.0:** Cada instruccion tarda 5 ciclos completos.

**Ejemplo:** Si un programa de 10 instrucciones tarda 14 ciclos:
- CPI = 14/10 = 1.4
- Sin pipeline (monociclo) tardaria 50 ciclos (10 x 5)
- Speedup = 50/14 = 3.57x mas rapido con pipeline

#### Ciclos Totales

Numero total de ciclos de reloj desde que entra la primera instruccion hasta que sale la ultima.

**Formula para pipeline ideal (sin hazards):**
```
Ciclos = Numero de instrucciones + (Etapas - 1)
Ciclos = N + 4
```

Los 4 ciclos extra son el tiempo para llenar el pipeline. Despues, sale una instruccion por ciclo.

**Con hazards:**
```
Ciclos = N + 4 + Stalls + (2 x Saltos tomados)
```

#### Stalls

Numero de burbujas insertadas por riesgos de datos. Cada stall es un ciclo desperdiciado.

#### Speedup (Aceleracion)

```
Speedup = Tiempo monociclo / Tiempo pipeline = (N x 5) / Ciclos pipeline
```

El speedup maximo teorico con 5 etapas es 5x, pero en la practica es menor por los hazards.

---

## Como Funciona el Simulador

### Arquitectura del Software

El simulador tiene dos componentes principales:

**Backend (Python + Flask):**

```
app.py                    --> Servidor web, recibe el codigo y retorna la simulacion
simulator/assembler.py    --> Parsea el texto ensamblador a instrucciones estructuradas
simulator/pipeline.py     --> Motor de simulacion del pipeline ciclo a ciclo
```

**Frontend (HTML + CSS + JavaScript):**

```
templates/index.html      --> Estructura de la pagina
static/css/style.css      --> Estilos visuales (tema oscuro)
static/js/app.js          --> Logica de la interfaz, animaciones y controles
```

**Comunicacion:** El frontend envia el codigo ensamblador al backend via API REST (POST /api/simulate). El backend retorna un arreglo JSON con el estado completo de cada ciclo (snapshot).

### Flujo de Ejecucion Interno

Cuando el usuario presiona "Simular", ocurre lo siguiente:

**Paso 1 - Parsing (assembler.py):**

1. Se lee el texto linea por linea.
2. Se eliminan comentarios (todo despues de `#`).
3. **Primera pasada:** Se identifican las etiquetas (labels) como `loop:` y se registra su posicion numerica.
4. **Segunda pasada:** Se parsea cada instruccion extrayendo:
   - Codigo de operacion (ADD, SUB, LW, etc.)
   - Registros destino y fuente (rd, rs, rt)
   - Valor inmediato o desplazamiento
   - Que registros lee y que registro escribe (para deteccion de hazards)

**Paso 2 - Simulacion (pipeline.py):**

Se ejecuta un bucle donde cada iteracion es un ciclo de reloj. En cada ciclo:

1. **WB:** Si hay instruccion en WB con resultado, se escribe en el banco de registros.
2. **MEM:** Si hay LW, se lee de memoria. Si hay SW, se escribe en memoria.
3. **EXE:** Se ejecuta la operacion de la ALU. Si hay forwarding activo, se leen los valores adelantados.
4. **Deteccion de hazards:** Se verifica si la instruccion en DI tiene conflicto con las instrucciones en EXE o MEM.
5. **Avance del pipeline:**
   - Si hay stall: se inserta burbuja en EXE, FI y DI se detienen.
   - Si hay salto tomado: se hace flush de FI y DI, se redirige el PC.
   - Si no hay conflictos: cada instruccion avanza una etapa y se busca una nueva instruccion.
6. **Snapshot:** Se guarda el estado completo (etapas, registros, memoria, hazards) para la visualizacion.

**Paso 3 - Visualizacion (app.js):**

1. Se reciben todos los snapshots del backend.
2. Se construye el diagrama temporal (tabla instruccion x ciclo).
3. Se calculan las estadisticas.
4. El usuario navega ciclo a ciclo con los botones o reproduccion automatica.
5. En cada ciclo se actualiza: el diagrama del pipeline, los registros (con animacion si cambiaron), la memoria, y las alertas de hazards/saltos.

### Algoritmo de Deteccion de Hazards

El simulador detecta hazards RAW comparando los registros que la instruccion en DI necesita leer contra los registros que las instrucciones en EXE y MEM van a escribir:

```
Para cada registro que DI necesita leer (reads_regs):

    1. Si la instruccion en EXE escribe ese registro:
       -> HAZARD detectado. Insertar stall.
       
    2. Si la instruccion en MEM escribe ese registro (solo sin forwarding):
       -> HAZARD detectado. Insertar stall.
```

**Con forwarding activado:**
- Los hazards EXE->DI y MEM->DI se resuelven por forwarding (no se necesita stall).
- EXCEPTO el hazard Load-Use: si la instruccion en EXE es un LW, el dato no estara disponible hasta que termine MEM, asi que se necesita 1 stall.

### Algoritmo de Forwarding

Cuando el forwarding esta activado, en la etapa EXE se verifican los caminos de adelanto antes de ejecutar la operacion:

```
Para la instruccion en EXE:

    1. Verificar forwarding desde MEM (instruccion en MEM):
       - Si MEM escribe un registro que EXE lee como rs o rt:
       - Y la instruccion en MEM NO es LW (porque LW aun no tiene el dato):
       -> Usar el resultado de la ALU de MEM como valor de entrada.
       
    2. Verificar forwarding desde WB (instruccion en WB):
       - Si WB escribe un registro que EXE lee como rs o rt:
       - Y no hay ya un forwarding desde MEM para ese mismo registro:
       -> Usar el resultado de WB como valor de entrada.
```

La prioridad es: MEM tiene prioridad sobre WB (dato mas reciente).

### Manejo de Saltos

El simulador maneja los saltos de la siguiente manera:

1. El salto se evalua en la etapa **EXE** (se comparan los registros).
2. Si el salto **se toma:**
   - Las instrucciones en FI y DI se reemplazan por burbujas (flush).
   - El PC se actualiza con la direccion destino del salto.
   - Se genera una alerta visual amarilla.
   - Penalizacion: 2 ciclos perdidos.
3. Si el salto **no se toma:**
   - Las instrucciones en FI y DI son correctas.
   - No hay penalizacion.
   - El pipeline continua normalmente.

---

## Conjunto de Instrucciones

El simulador soporta un subconjunto del juego de instrucciones MIPS, suficiente para demostrar todos los conceptos del pipeline:

### Instrucciones Tipo R (Registro a Registro)

Formato: `OP $rd, $rs, $rt`

El resultado se calcula operando los valores de $rs y $rt, y se almacena en $rd.

| Instruccion | Operacion | Descripcion | Ejemplo |
|-------------|-----------|-------------|---------|
| ADD | rd = rs + rt | Suma entera | `ADD $t0, $t1, $t2` -> $t0 = $t1 + $t2 |
| SUB | rd = rs - rt | Resta entera | `SUB $t0, $t1, $t2` -> $t0 = $t1 - $t2 |
| AND | rd = rs & rt | AND bit a bit | `AND $t0, $t1, $t2` -> $t0 = $t1 AND $t2 |
| OR | rd = rs \| rt | OR bit a bit | `OR $t0, $t1, $t2` -> $t0 = $t1 OR $t2 |
| SLT | rd = (rs < rt) ? 1 : 0 | Comparacion (menor que) | `SLT $t0, $t1, $t2` -> $t0 = 1 si $t1 < $t2 |

### Instrucciones Tipo I (Inmediato)

Formato: `OP $rt, $rs, inmediato`

| Instruccion | Operacion | Descripcion | Ejemplo |
|-------------|-----------|-------------|---------|
| ADDI | rt = rs + imm | Suma con valor inmediato | `ADDI $t0, $zero, 10` -> $t0 = 0 + 10 = 10 |
| LW | rt = Mem[rs + offset] | Cargar palabra de memoria | `LW $t0, 4($t1)` -> $t0 = Mem[$t1 + 4] |
| SW | Mem[rs + offset] = rt | Almacenar palabra en memoria | `SW $t0, 0($t1)` -> Mem[$t1] = $t0 |
| BEQ | Si rs == rt, saltar | Saltar si iguales | `BEQ $t0, $t1, etiqueta` |
| BNE | Si rs != rt, saltar | Saltar si diferentes | `BNE $t0, $t1, etiqueta` |

### Instrucciones Tipo J (Salto)

| Instruccion | Operacion | Descripcion | Ejemplo |
|-------------|-----------|-------------|---------|
| J | PC = direccion | Salto incondicional | `J etiqueta` |

### Instrucciones Especiales

| Instruccion | Descripcion |
|-------------|-------------|
| NOP | No Operation. No hace nada, solo avanza el pipeline. Util para insertar espacios manualmente entre instrucciones dependientes. |
| HALT | Detiene la ejecucion del programa. El pipeline termina de vaciar las instrucciones restantes. |

### Sintaxis del Ensamblador

- Los registros se escriben con `$` seguido del numero o alias: `$0`, `$t0`, `$zero`, `$sp`.
- Los comentarios empiezan con `#` y se ignoran.
- Las etiquetas terminan con `:` y se usan como destino de saltos.
- Los operandos se separan con comas.
- Las direcciones de memoria usan el formato `offset($registro)`.

**Ejemplo de programa completo:**
```
# Programa ejemplo
ADDI $t0, $zero, 10     # Cargar 10 en $t0
ADDI $t1, $zero, 20     # Cargar 20 en $t1
NOP                      # Evitar hazard
NOP                      # Evitar hazard
ADD $t2, $t0, $t1        # $t2 = $t0 + $t1 = 30
HALT                     # Fin del programa
```

---

## Registros del Procesador

El simulador implementa los 32 registros del procesador MIPS. Cada registro tiene 32 bits y se puede referenciar por numero ($0 a $31) o por alias:

| Registro | Alias | Uso Convencional | Notas |
|----------|-------|------------------|-------|
| $0 | $zero | Constante 0 | Siempre vale 0, no se puede modificar |
| $1 | $at | Assembler Temporary | Reservado para el ensamblador |
| $2-$3 | $v0-$v1 | Valores de retorno | Usados para retornar valores de funciones |
| $4-$7 | $a0-$a3 | Argumentos | Usados para pasar argumentos a funciones |
| $8-$15 | $t0-$t7 | Temporales | Usados para calculos temporales |
| $16-$23 | $s0-$s7 | Salvados | Se preservan entre llamadas a funciones |
| $24-$25 | $t8-$t9 | Temporales | Mas registros temporales |
| $26-$27 | $k0-$k1 | Kernel | Reservados para el sistema operativo |
| $28 | $gp | Global Pointer | Apunta a la seccion de datos globales |
| $29 | $sp | Stack Pointer | Apunta al tope de la pila |
| $30 | $fp | Frame Pointer | Apunta al marco de pila actual |
| $31 | $ra | Return Address | Direccion de retorno de funciones |

**Nota sobre $zero:** El registro $0 siempre contiene el valor 0. Cualquier intento de escribir en el es ignorado. Esto es util para operaciones como cargar un valor inmediato: `ADDI $t0, $zero, 5` equivale a `$t0 = 0 + 5 = 5`.

---

## Instalacion y Ejecucion

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Un navegador web moderno (Chrome, Firefox, Safari, Edge)

### 1. Descargar el proyecto

Descargar la carpeta `proyecto_final_arquitectura_computadores` completa.

### 2. Instalar dependencias

Abrir una terminal en la carpeta del proyecto y ejecutar:

```bash
pip install -r requirements.txt
```

Esto instala Flask (servidor web) y Flask-CORS (para comunicacion entre frontend y backend).

### 3. Ejecutar el servidor

```bash
python app.py
```

Se vera un mensaje como:
```
* Serving Flask app 'app'
* Running on http://127.0.0.1:5050
```

### 4. Abrir en el navegador

Ir a la direccion: **http://localhost:5050**

La interfaz del simulador se cargara automaticamente con el primer programa de ejemplo.

---

## Guia de Uso del Simulador

### Interfaz Principal

La interfaz se divide en dos paneles:

- **Panel Izquierdo:** Contiene los programas de ejemplo, los controles de simulacion, y el editor de codigo ensamblador.
- **Panel Derecho:** Muestra la visualizacion del pipeline con tres vistas accesibles por pestanas.

### Paso a Paso

1. **Escribir o cargar codigo:** Escribir codigo ensamblador directamente en el editor, o hacer clic en uno de los 5 programas de ejemplo para cargarlo automaticamente.

2. **Configurar opciones:**
   - **Data Forwarding:** Activar el toggle para habilitar el adelanto de datos. El simulador mostrara menos burbujas.
   - **Velocidad:** Mover el slider para ajustar la velocidad de reproduccion automatica (100ms a 2000ms por ciclo).

3. **Presionar "Simular":** El backend procesa el codigo ensamblador, ejecuta la simulacion completa y retorna todos los ciclos.

4. **Navegar la simulacion:**
   - **Play/Pausa:** Inicia o detiene la reproduccion automatica ciclo a ciclo.
   - **Paso:** Avanza exactamente un ciclo.
   - **Reset:** Reinicia la simulacion al estado inicial.

5. **Atajos de teclado** (cuando el editor no tiene el foco):
   - `Flecha derecha:` Avanzar un ciclo.
   - `Flecha izquierda:` Retroceder un ciclo.
   - `Espacio o Enter:` Play/Pausa.

### Vistas Disponibles

**Vista Pipeline:**
- Muestra las 5 etapas como cajas de colores con la instruccion actual en cada una.
- Las burbujas se muestran con borde punteado y texto en gris.
- Alertas rojas cuando hay un hazard con detalle del conflicto.
- Alertas amarillas cuando un salto se toma.
- Panel de registros con animacion verde cuando un valor cambia.
- Panel de memoria mostrando las posiciones accedidas.

**Vista Diagrama Temporal:**
- Tabla donde cada fila es una instruccion y cada columna es un ciclo.
- Cada celda muestra en que etapa esta la instruccion en ese ciclo.
- Coloreado por etapa para facil lectura.
- Permite ver de un vistazo todo el flujo del programa.

**Vista Estadisticas:**
- Ciclos totales de ejecucion.
- Numero de instrucciones.
- CPI (Ciclos Por Instruccion).
- Numero de stalls.
- Numero de saltos tomados.
- Si el forwarding esta activo.

---

## Programas de Ejemplo Incluidos

### 1. Suma Basica (suma_basica.asm)

**Proposito:** Demostrar el flujo normal del pipeline sin conflictos.

```
ADDI $t0, $zero, 10    # $t0 = 10
ADDI $t1, $zero, 20    # $t1 = 20
NOP                     # Esperar
NOP                     # Esperar
ADD $t2, $t0, $t1      # $t2 = 30
NOP
NOP
SUB $t3, $t2, $t0      # $t3 = 20
HALT
```

Los NOPs se insertan manualmente para evitar hazards. En este ejemplo se ve como el pipeline fluye sin interrupciones cuando no hay dependencias.

**Resultado esperado:** $t0=10, $t1=20, $t2=30, $t3=20.

### 2. Hazard de Datos RAW (hazard_datos.asm)

**Proposito:** Mostrar como el pipeline detecta dependencias de datos e inserta burbujas automaticamente.

```
ADDI $t0, $zero, 5     # $t0 = 5
ADD $t1, $t0, $t0      # HAZARD: $t0 aun no escrito
SUB $t2, $t1, $t0      # HAZARD: $t1 aun no escrito
HALT
```

Cada instruccion depende del resultado de la anterior. El simulador detecta los conflictos y muestra alertas rojas con el detalle del hazard.

**Resultado esperado:** $t0=5, $t1=10, $t2=5. Se insertan 4 burbujas (2 por cada hazard).

### 3. Memoria LW/SW (memoria.asm)

**Proposito:** Demostrar operaciones de memoria y el hazard Load-Use.

```
ADDI $t0, $zero, 100   # Direccion base
ADDI $t1, $zero, 42    # Valor
NOP
NOP
SW $t1, 0($t0)         # Mem[100] = 42
LW $t2, 0($t0)         # $t2 = Mem[100] = 42
ADD $t3, $t2, $t1      # HAZARD Load-Use
HALT
```

El hazard Load-Use entre LW y ADD es especial: incluso con forwarding activado, se necesita 1 stall porque el dato de LW no esta disponible hasta que termina MEM.

**Resultado esperado:** $t0=100, $t1=42, $t2=42, $t3=84. Mem[100]=42.

### 4. Salto Condicional BEQ (salto_condicional.asm)

**Proposito:** Mostrar el flush del pipeline cuando un salto se toma.

```
ADDI $t0, $zero, 5     # $t0 = 5
ADDI $t1, $zero, 5     # $t1 = 5
NOP
NOP
BEQ $t0, $t1, salto    # $t0 == $t1, salto se toma
ADDI $t2, $zero, 99    # Se descarta (flush)
ADDI $t3, $zero, 99    # Se descarta (flush)
salto: ADDI $t4, $zero, 1  # Se ejecuta
HALT
```

Las instrucciones ADDI $t2 y ADDI $t3 entran al pipeline pero se descartan cuando el salto se resuelve en EXE. La alerta amarilla indica el flush.

**Resultado esperado:** $t0=5, $t1=5, $t4=1. $t2 y $t3 quedan en 0.

### 5. Bucle (bucle.asm)

**Proposito:** Demostrar un programa con un bucle que repite instrucciones.

```
ADDI $t0, $zero, 0     # suma = 0
ADDI $t1, $zero, 1     # contador = 1
ADDI $t2, $zero, 6     # limite = 6
NOP
NOP
loop: ADD $t0, $t0, $t1  # suma += contador
ADDI $t1, $t1, 1         # contador++
NOP
NOP
BNE $t1, $t2, loop       # Si contador != 6, repetir
NOP
NOP
HALT
```

El bucle se ejecuta 5 veces (contador de 1 a 5). Se puede observar como el BNE genera flushes en cada iteracion que salta de vuelta a `loop`.

**Resultado esperado:** $t0=15 (1+2+3+4+5), $t1=6, $t2=6.

---

## Estructura del Proyecto

```
proyecto_final_arquitectura_computadores/
|
|-- README.md                   # Documentacion completa del proyecto (este archivo)
|-- requirements.txt            # Dependencias de Python (Flask, Flask-CORS)
|-- app.py                      # Servidor Flask: rutas web y API REST
|
|-- simulator/                  # Modulo del simulador (logica en Python)
|   |-- __init__.py             # Inicializador del modulo
|   |-- assembler.py            # Parser de codigo ensamblador MIPS
|   |-- pipeline.py             # Motor de simulacion del pipeline de 5 etapas
|
|-- static/                     # Archivos estaticos del frontend
|   |-- css/
|   |   |-- style.css           # Estilos CSS (tema oscuro, colores por etapa)
|   |-- js/
|       |-- app.js              # Logica JavaScript (controles, renderizado, animaciones)
|
|-- templates/
|   |-- index.html              # Pagina HTML principal
|
|-- examples/                   # Programas de ejemplo en ensamblador
    |-- suma_basica.asm         # Operaciones sin hazards
    |-- hazard_datos.asm        # Riesgos RAW con burbujas
    |-- memoria.asm             # LW/SW con hazard Load-Use
    |-- salto_condicional.asm   # BEQ con flush del pipeline
    |-- bucle.asm               # Bucle con BNE
```

---

## Referencias Bibliograficas

- Patterson, D. A., & Hennessy, J. L. (2014). *Computer Organization and Design: The Hardware/Software Interface* (5ta ed.). Morgan Kaufmann.
- Stallings, W. (2016). *Computer Organization and Architecture: Designing for Performance* (10ma ed.). Pearson.
- Hennessy, J. L., & Patterson, D. A. (2019). *Computer Architecture: A Quantitative Approach* (6ta ed.). Morgan Kaufmann.
- Tanenbaum, A. S. (2013). *Structured Computer Organization* (6ta ed.). Pearson.
- Simulador RISC de la Universidad de las Islas Baleares (UIB).
- CREATOR - Simulador didactico de la Universidad Carlos III de Madrid (UC3M).
- PipeSim - Herramienta academica de planificacion de unidades funcionales segmentadas.
