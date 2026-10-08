# ARCHITECTURE.md — карта кода Turtle2Py

Python-порт `turtle.f` (Watcom FORTRAN 77, 3195 строк). Задача — **побитовое**
совпадение вывода с эталоном `test_ref.res`. Физические модели и порядок
операций не меняются; порт следует исходнику строка-за-строкой.

## Точка входа

```
python -m turtle2py <input.dat> <output.res>
```

- `turtle2py/__main__.py`, `turtle2py/cli.py` — CLI.
- `turtle2py/fields.py:941 turtle(inp, outp)` — PROGRAM TURTLE
  (`turtle.f:53-79`): читатель карт → SETUP → HEDING → ZERO →
  «REST SPACE» → RAYRUN → OHIST → APLIM → запись файла.

## Слои (по зависимостям, снизу вверх)

| Модуль | Строки | Роль | Прототип в turtle.f |
|---|---|---|---|
| `turtle2py/x87.py` | 233 | Эмуляция x87-расширения Watcom: `V` (extended-регистр), `S` (store в REAL*4), `P` (степень), transcendental на расширенных аргументах; mpmath `prec=64` | арифметика компилятора |
| `turtle2py/random.py` | 52 | ГПСЧ G900: `DS=(DS*DM) mod 2**48`, `DR=DS/2**48`, `M=44485709377909`, `S0=48131768981101` | `RANF` 3130–3165 |
| `turtle2py/state.py` | 170 | `Context` — dataclass, поля 1:1 к COMMON-блокам `/BLOC1/…/BLOC16/`; `idata` = `data.view(np.int32)` (EQUIVALENCE) | COMMON |
| `turtle2py/formats.py` | 314 | Рендер FORMAT: carriage control, `I/F/E/A`, `X`, `nH`, `/`, группы; семантика исчерпания аргументов Watcom (см. PHYSICS_SPEC §6) | FORMAT |
| `turtle2py/io.py` | 627 | CardReader: чтение карт, `UNPACK`, цепочки чтения REAL (напр. `PBEAM=1.8881509304046631`), `_mpf/_f32m` | `READ`, `UNPACK` |
| `turtle2py/elements.py` | 537 | Диспетчер элементов: `NU`, `RESET`, `REPEAT`, `QUAD`, `BEND` (+`_bend_sector`), `SEXT`, `SOLO`, `MULTI`, `FOCUS`, `HSTUN`, `HSTVAL`, `QSTOP`, `BSTOP` | `NU` 1995, `BEND` 1694, `FOCUS` 1909, … |
| `turtle2py/tracking.py` | 867 | `EMIT_MY` (251), `SCATT_MY` (1014), `DECAY` (372), `RAYRUN` (1125) — главный цикл трассировки | те же |
| `turtle2py/fields.py` | 962 | `SETUP` (2554) с диспетчером меток `_l10…_l600`, `INITZE`, `ZERO`, `DECAYP`, `DECAYZ`, `HSTUN/HSTVAL`-хелперы, `turtle()` | `SETUP`, `RDELMT` 2134 |
| `turtle2py/hist.py` | 150 | `HISTO` (644), `ENTMAT` (668), `EHIST` (611) | те же |
| `turtle2py/report.py` | 546 | Вывод: `PRINT1` (2030), `DIGITAL`/`BCDWR` (2069+), `HISCAP` (611), `HEDING` (575), `TRHST` (1583), `OUTMAT` (871), `OHIST` (588), `APLIM` (116) | те же |

## Ключевые соглашения

- **Все REAL = `np.float32`.** Арифметика трассировки идёт через `x87.V`
  (mpmath, 64-битная мантисса; `R` — загрузка REAL*4 в регистр, `S` — store
  с единственным округлением, `P` — целая степень как unrolled-умножение,
  `K` — REAL*4-литерал) с округлением только при сохранении в переменную
  Fortran. Локальные BEND (X10, Q1, Q2, T116…, A1..C2) живут в
  расширенной точности и не округляются; COMMON-массивы (KH2, KV2, RH, RV,
  RAY2) хранятся REAL*4.
- **Литералы округляются как REAL\*4-константы**: `PI=_c(6.2831853)`,
  `Z_TEMP=_c(11.037)`, `0.1 → 0.100000001490116119384765625`.
- **Сpill-асимметрии Watcom зафиксированы и не «причёсываются»**:
  `SIN(THETA1+ALFA)` — расширенный аргумент, `COS(THETA1+ALFA)` внутри
  `RAY2(1)` — аргумент через REAL*4-спил (`x87.cos32`); в `scatt_my`
  `a1=S(sig_r1*sig)`, `del_x1` — extended `cos(phi)`, `del_y1` — `S(sin(phi))`.
- Выходной файл: CRLF, carriage control пишется как байт записи (см.
  PHYSICS_SPEC §6).

## Тесты и зонды

- `tests/` — pytest (20 тестов: RNG, читатель, элементы).
- `probe/*.py` — сверки с фортранными дампами (`probe/*.f` → Watcom →
  `probeN.res`); запуск из корня: `python probe/<имя>.py`.
- `probe/small_run.py` — полный малый кейс (100 лучей) против
  `small_ref.res`; `probe/full_run.py` — полный кейс против `test_ref.res`.
