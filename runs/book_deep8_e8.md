# Opening book: runs/deep8_c1_300_e8/net_0300.pt at 16384 sims, depth 4, top-3 replies per node, rule count

Values are the deep-search value for X after the moves (search-relative: what this net + search prefers, not game-theoretic). Moves are `m(b<board>c<cell>)`, m = 9*board + cell. The line follows the most-visited move. A reply is one *orbit* (replies equivalent under the symmetries that fix the position), shown by its canonical (smallest-index) member with the orbit size in brackets when > 1; share is the orbit's summed visit share; every line is in the frame of its first move.

| first move | value X | best reply orbit (O) | share | X's next | line to depth 4 | paired X score | draw share | deep8_c1_300_e4 value / best reply |
|---|---|---|---|---|---|---|---|---|
| 40(b4c4) | +0.524 | 36(b4c0) [4] | 0.94 | 0(b0c0) | 36(b4c0)(+0.54) 0(b0c0)(+0.54) 8(b0c8)(+0.54) | 73 % (44) | 18 % | +0.495 / 36(b4c0) = |
| 36(b4c0) | +0.429 | 5(b0c5) [2] | 0.70 | 50(b5c5) | 5(b0c5)(+0.43) 50(b5c5)(+0.44) 48(b5c3)(+0.44) | 68 % (80) | 24 % | +0.395 / 0(b0c0) != |
| 0(b0c0) | +0.329 | 8(b0c8) | 0.47 | 80(b8c8) | 8(b0c8)(+0.33) 80(b8c8)(+0.33) 77(b8c5)(+0.34) | 68 % (78) | 15 % | +0.309 / 1(b0c1) != |
| 37(b4c1) | +0.294 | 10(b1c1) | 0.90 | 9(b1c0) | 10(b1c1)(+0.29) 9(b1c0)(+0.30) 0(b0c0)(+0.30) | 70 % (54) | 15 % | +0.305 / 10(b1c1) = |
| 5(b0c5) | +0.292 | 45(b5c0) | 0.54 | 8(b0c8) | 45(b5c0)(+0.29) 8(b0c8)(+0.29) 80(b8c8)(+0.28) | 63 % (110) | 29 % | +0.254 / 50(b5c5) != |
| 4(b0c4) | +0.244 | 40(b4c4) | 0.99 | 36(b4c0) | 40(b4c4)(+0.24) 36(b4c0)(+0.24) 5(b0c5)(+0.24) | 64 % (36) | 28 % | +0.192 / 40(b4c4) = |
| 8(b0c8) | +0.244 | 80(b8c8) | 0.95 | 72(b8c0) | 80(b8c8)(+0.24) 72(b8c0)(+0.25) 5(b0c5)(+0.25) | 67 % (42) | 14 % | +0.232 / 80(b8c8) = |
| 2(b0c2) | +0.228 | 20(b2c2) | 0.87 | 23(b2c5) | 20(b2c2)(+0.22) 23(b2c5)(+0.23) 50(b5c5)(+0.22) | 58 % (102) | 26 % | +0.157 / 20(b2c2) = |
| 10(b1c1) | +0.221 | 16(b1c7) | 0.90 | 66(b7c3) | 16(b1c7)(+0.22) 66(b7c3)(+0.20) 30(b3c3)(+0.20) | 67 % (80) | 11 % | +0.170 / 16(b1c7) = |
| 1(b0c1) | +0.194 | 10(b1c1) | 0.38 | 16(b1c7) | 10(b1c1)(+0.19) 16(b1c7)(+0.20) 70(b7c7)(+0.19) | 57 % (96) | 22 % | +0.171 / 10(b1c1) = |
| 12(b1c3) | +0.177 | 28(b3c1) | 0.78 | 14(b1c5) | 28(b3c1)(+0.17) 14(b1c5)(+0.17) 50(b5c5)(+0.17) | 62 % (84) | 21 % | +0.166 / 30(b3c3) != |
| 16(b1c7) | +0.129 | 70(b7c7) | 0.75 | 66(b7c3) | 70(b7c7)(+0.12) 66(b7c3)(+0.12) 30(b3c3)(+0.12) | 54 % (48) | 25 % | +0.090 / 70(b7c7) = |
| 15(b1c6) | +0.121 | 60(b6c6) | 0.98 | 62(b6c8) | 60(b6c6)(+0.12) 62(b6c8)(+0.12) 73(b8c1)(+0.11) | 67 % (66) | 23 % | +0.094 / 60(b6c6) = |
| 9(b1c0) | +0.079 | 5(b0c5) | 0.46 | 50(b5c5) | 5(b0c5)(+0.08) 50(b5c5)(+0.08) 46(b5c1)(+0.07) | 56 % (70) | 34 % | +0.039 / 0(b0c0) != |
| 13(b1c4) | -0.060 | 40(b4c4) | 1.00 | 37(b4c1) | 40(b4c4)(-0.06) 37(b4c1)(-0.07) 12(b1c3)(-0.09) | 57 % (40) | 20 % | -0.079 / 40(b4c4) = |

Agreement with runs/deep8_c1_300_e4/net_0300.pt on the most-visited reply orbit: 0.74 over 465 shared nodes (by depth: 1: 0.67, 2: 0.83, 3: 0.75, 4: 0.73); mean |value difference| 0.026.

Nodes: 583; built 2026-09-13 00:55 in 2305 s.
