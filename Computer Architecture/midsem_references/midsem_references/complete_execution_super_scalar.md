## Instruction Sequence

```asm
I1: ADD R1, R2, R3   ; R1 → P8
I2: MUL R4, R1, R5   ; R4 → P9
I3: SUB R6, R4, R7   ; R6 → P10
```

Assumptions:
- Physical registers: P0–P15
- Initial ARF mappings:
  ```
  R1→P1, R2→P2, R3→P3, R4→P4, R5→P5, R6→P6, R7→P7
  ```
- RRF starts empty
- Dispatch bandwidth: 1 instruction/cycle
- Completion bandwidth: 1 instruction/cycle
- All instructions are speculative (assume predicted path)

---

## Cycle-by-Cycle Execution Trace
---

### Cycle 1 — Dispatch I1

**ROB**

| Entry | Busy | Issued | Finished | Instr | Addr | Rename | Spec | Valid |
|-------|------|--------|----------|-------|------|--------|------|-------|
| 0     | ✅   | ❌     | ❌       | ADD   | PC1  | P8     | ✅   | ❌    |

**ARF**

| Arch Reg | Phys Reg | Busy |
|----------|----------|------|
| R1       | P8       | ✅   |
| R2       | P2       | ❌   |
| R3       | P3       | ❌   |
| R4       | P4       | ❌   |
| R5       | P5       | ❌   |
| R6       | P6       | ❌   |
| R7       | P7       | ❌   |

**RRF**

| Phys Reg | Valid | Busy | Value |
|----------|-------|------|-------|
| P8       | ❌    | ✅   | —     |

**RS**

| Entry | Busy | Opcode | Op1 | V1 | Op2 | V2 | Dest | Ready |
|-------|------|--------|-----|----|-----|----|------|--------|
| RS0   | ✅   | ADD    | P2  | ✅ | P3  | ✅ | P8   | ✅     |

---

### Cycle 2 — Dispatch I2, Issue I1

**ROB**

| Entry | Busy | Issued | Finished | Instr | Addr | Rename | Spec | Valid |
|-------|------|--------|----------|-------|------|--------|------|-------|
| 0     | ✅   | ✅     | ❌       | ADD   | PC1  | P8     | ✅   | ❌    |
| 1     | ✅   | ❌     | ❌       | MUL   | PC2  | P9     | ✅   | ❌    |

**ARF**

| Arch Reg | Phys Reg | Busy |
|----------|----------|------|
| R1       | P8       | ✅   |
| R4       | P9       | ✅   |
| R2–R3, R5–R7 | P2–P3, P5–P7 | ❌ |

**RRF**

| Phys Reg | Valid | Busy | Value |
|----------|-------|------|-------|
| P8       | ❌    | ✅   | —     |
| P9       | ❌    | ✅   | —     |

**RS**

| Entry | Busy | Opcode | Op1 | V1 | Op2 | V2 | Dest | Ready |
|-------|------|--------|-----|----|-----|----|------|--------|
| RS1   | ✅   | MUL    | P8  | ❌ | P5  | ✅ | P9   | ❌     |

---

### Cycle 3 — Dispatch I3, I1 Finishes, I2 Issued

**ROB**

| Entry | Busy | Issued | Finished | Instr | Addr | Rename | Spec | Valid |
|-------|------|--------|----------|-------|------|--------|------|-------|
| 0     | ✅   | ✅     | ✅       | ADD   | PC1  | P8     | ✅   | ✅    |
| 1     | ✅   | ✅     | ❌       | MUL   | PC2  | P9     | ✅   | ❌    |
| 2     | ✅   | ❌     | ❌       | SUB   | PC3  | P10    | ✅   | ❌    |

**ARF**

| Arch Reg | Phys Reg | Busy |
|----------|----------|------|
| R1       | P8       | ✅   |
| R4       | P9       | ✅   |
| R6       | P10      | ✅   |
| R2–R3, R5, R7 | P2–P3, P5, P7 | ❌ |

**RRF**

| Phys Reg | Valid | Busy | Value |
|----------|-------|------|-------|
| P8       | ✅    | ✅   | V8    |
| P9       | ❌    | ✅   | —     |
| P10      | ❌    | ✅   | —     |

**RS**

| Entry | Busy | Opcode | Op1 | V1 | Op2 | V2 | Dest | Ready |
|-------|------|--------|-----|----|-----|----|------|--------|
| RS2   | ✅   | SUB    | P9  | ❌ | P7  | ✅ | P10  | ❌     |

---

### Cycle 4 — I2 Finishes, I3 Issued

**ROB**

| Entry | Busy | Issued | Finished | Instr | Addr | Rename | Spec | Valid |
|-------|------|--------|----------|-------|------|--------|------|-------|
| 0     | ✅   | ✅     | ✅       | ADD   | PC1  | P8     | ✅   | ✅    |
| 1     | ✅   | ✅     | ✅       | MUL   | PC2  | P9     | ✅   | ✅    |
| 2     | ✅   | ✅     | ❌       | SUB   | PC3  | P10    | ✅   | ❌    |

**RRF**

| Phys Reg | Valid | Busy | Value |
|----------|-------|------|-------|
| P8       | ✅    | ✅   | V8    |
| P9       | ✅    | ✅   | V9    |
| P10      | ❌    | ✅   | —     |

**RS**

| Entry | Busy | Opcode | Op1 | V1 | Op2 | V2 | Dest | Ready |
|-------|------|--------|-----|----|-----|----|------|--------|
| RS2   | ✅   | SUB    | P9  | ✅ | P7  | ✅ | P10  | ✅     |

---

### Cycle 5 — I1 Commits, I3 Finishes

**ROB**

| Entry | Busy | Issued | Finished | Instr | Addr | Rename | Spec | Valid |
|-------|------|--------|----------|-------|------|--------|------|-------|
| 0     | ❌   | —      | —        | —     | —    | —      | —    | —     |
| 1     | ✅   | ✅     | ✅       | MUL   | PC2  | P9     | ✅   | ✅    |
| 2     | ✅   | ✅     | ✅       | SUB   | PC3  | P10    | ✅   | ✅    |

**ARF**

| Arch Reg | Phys Reg | Busy |
|----------|----------|------|
| R1       | P8       | ❌   |
| R4       | P9       | ✅   |
| R6       | P10      | ✅   |
| R2–R3, R5, R7 | P2–P3, P5, P7 | ❌ |

**RRF**

| Phys Reg | Valid | Busy | Value |
|----------|-------|------|-------|
| P8       | ✅    | ❌   | V8    |
| P9       | ✅    | ✅   | V9    |
| P10      | ✅    | ✅   | V10   |

**RS**

| All entries deallocated |

---

##  Cycle 6 — I2 Commits

**ROB**

| Entry | Busy | Issued | Finished | Instr | Addr | Rename | Spec | Valid |
|-------|------|--------|----------|-------|------|--------|------|-------|
| 0     | ❌   | —      | —        | —     | —    | —      | —    | —     |
| 1     | ❌   | —      | —        | —     | —    | —      | —    | —     |
| 2     | ✅   | ✅     | ✅       | SUB   | PC3  | P10    | ✅   | ✅    |

**ARF**

| Arch Reg | Phys Reg | Busy |
|----------|----------|------|
| R1       | P8       | ❌   |
| R2       | P2       | ❌   |
| R3       | P3       | ❌   |
| R4       | P9       | ❌   |
| R5       | P5       | ❌   |
| R6       | P10      | ✅   |
| R7       | P7       | ❌   |

**RRF**

| Phys Reg | Valid | Busy | Value |
|----------|-------|------|-------|
| P8       | ✅    | ❌   | V8    |
| P9       | ✅    | ❌   | V9    |
| P10      | ✅    | ✅   | V10   |

**RS**

| All entries deallocated |

---

## Cycle 7 — I3 Commits

**ROB**

| Entry | Busy | Issued | Finished | Instr | Addr | Rename | Spec | Valid |
|-------|------|--------|----------|-------|------|--------|------|-------|
| 0     | ❌   | —      | —        | —     | —    | —      | —    | —     |
| 1     | ❌   | —      | —        | —     | —    | —      | —    | —     |
| 2     | ❌   | —      | —        | —     | —    | —      | —    | —     |

**ARF**

| Arch Reg | Phys Reg | Busy |
|----------|----------|------|
| R1       | P8       | ❌   |
| R2       | P2       | ❌   |
| R3       | P3       | ❌   |
| R4       | P9       | ❌   |
| R5       | P5       | ❌   |
| R6       | P10      | ❌   |
| R7       | P7       | ❌   |

**RRF**

| Phys Reg | Valid | Busy | Value |
|----------|-------|------|-------|
| P8       | ✅    | ❌   | V8    |
| P9       | ✅    | ❌   | V9    |
| P10      | ✅    | ❌   | V10   |

**RS**

| All entries deallocated |

---

##  Final Snapshot

- **All instructions have committed** in program order.
- **ROB** is empty — no instructions in flight.
- **ARF** reflects the latest committed mappings, all marked not busy.
- **RRF** holds valid results in P8, P9, and P10 — all physical registers are free.
- **RS** is clear — all instructions have issued and retired.

