# Budgets defined before measurement

macOS arm64, Release compiler, ordinary desktop without forced cache eviction.
The first native execution follows build immediately; build does not execute
the application.

- Small **repeated** native execution ≤100 ms (decision D125). The first
  execution is published next to a same-host trivial-binary baseline instead of
  being budgeted: a fresh Mach-O image pays about 240 ms of page-in and
  signature validation before `main`, so a first-run ceiling measures the
  platform, not this program. The re-measurement that produced this rule is in
  the CP42 startup re-check evidence (2026-11-11).
- `mmay run` (VM) ≤500 ms.
- Repeated `mmay test . --engine both` with a ready cache ≤2 s.
- `stateful-512k-v1`: native ≤2 s, VM ≤20 s, for the complete process.
- Peak RSS: native ≤128 MiB, VM ≤256 MiB.
- Functional acceptance uses a 64 MiB managed-heap limit.

Delimited: 2048 rows of 8 fields containing 31 ASCII bytes each, a delimiter
after the first seven fields and LF after the last: exactly 524288 bytes.
Source-lint: 8192 lines of 64 bytes, each an LF-terminated comment without
TODO/FIXME, indentation tabs or trailing whitespace: exactly 524288 bytes.
The second size uses half the same lines to check scaling. The harness
generates synthetic data and records its bytes and SHA.

These preliminary boundaries are fixed. A miss blocks affected acceptance;
functional completion does not establish budget or Tier 1 acceptance.
