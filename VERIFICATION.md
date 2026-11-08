# Historical verification — 2026-09-09, macOS arm64

This translates the original record; it does not report a new run. Compiler:
candidate after `0567634`, SHA-256
`7da536ea73bfdec7809ee6369bc4839133fb99aff4adfc167635d47287c8b0be`. CP42 language evidence relates the exact compiler commit to this
candidate; JSON source hashes identify the application.

- Source tests: **4**, `mmay test . --engine both`.
- **38** process cases plus help in VM/native Debug/Release; **3** closed stdout cases.
- Managed heap: **64 MiB**; large synthetic inputs: **512 KiB**.
- Raw [acceptance](evidence/acceptance.json) and
  [measurements](evidence/measurements.json) include commands, input/output
  hashes, executable/source identity and all samples.

| Dataset | Engine | First sample, ms | Repeated range, ms | Peak RSS, MiB |
|---|---|---:|---:|---:|
| small | native | 386.84 | 6.60–10.96 | 1.88 |
| small | vm | 511.45 | 500.14–531.69 | 49.12 |
| stateful-256k-v1 | native | 164.70 | 164.47–164.47 | 66.58 |
| stateful-256k-v1 | vm | 2348.56 | 2347.85–2347.85 | 114.92 |
| stateful-512k-v1 | native | 323.26 | 323.23–323.23 | 76.27 |
| stateful-512k-v1 | vm | 4225.09 | 4209.21–4209.21 | 125.36 |

Repeated test-both: **5.506 s**, budget 2 s.

Processes were measured sequentially; full C/ASan checks did not run during
measurement. The first native execution followed build with no application
warmup. The new native artifact exceeded 100 ms; the precise host/startup
cause remained unestablished. This remained an acceptance blocker and the
budget was unchanged.
Small VM run also exceeded 500 ms and test-both exceeded 2 s. All misses
remain in the original JSON. A zero exit status from the measure script means
that it recorded results, not that the budgets passed.

Large-workload and RSS results met preliminary limits, and functional checks
passed locally. Full CP42, other Tier 1 platforms, Linux LeakSanitizer and
broader platform acceptance remained open. This was not public-release status.
