# Findings, limitations and decisions

| Observation | Class / owner | Outcome |
|---|---|---|
| `text.substring` created a full suffix before copying a field; 512 KiB CSV exhausted the 64 MiB VM string pool | Library + typed MIR/text VM/native | Fixed with a shared range operation, retaining both UTF-8 checks, an owned result and errors. The regression repeatedly extracts short ranges from 512 KiB. |
| A scanner with 428 blocks/674 registers exceeded the bytecode-verifier budget | Toolchain / bytecode must-analysis | Fixed with an RPO-initialized queue. Budget, meet and invalidation were not relaxed. |
| First execution of a new native file exceeds 100 ms | Shared startup/host boundary; exact system cause unestablished | Open acceptance blocker. Repeated samples do not replace the first execution; no security or warmup workaround. |
| Whole input up to 1 MiB, JSON up to 1 MiB | Explicit application and standard-API boundary | Sufficient for the defined dialect; arbitrary-size file processing is outside the claim. |

The CSV state machine and source-lint contexts differ; shared `support.my`
contains only CLI handling, limits and reading/writing. `mmay_acceptance.py` v1
was reused unchanged. Business-record fields use `std/json` rather than a
handwritten serializer. This record preserves historical findings, not a new
verification of the current compiler.

Additional open observations:

- Small `mmay run`: 500–532 ms against a 500 ms budget; repeated test-both:
  5.506 s against 2 s. The next shared task is to profile program/test preparation
  and then remeasure the same workload. Shrinking the scanner or moving its
  algorithm to C to meet the budget is not an acceptable substitute.
- A literal `match` on `byte` is still rejected with I0001 by checker scalar-match.
  Minimal example: `fn main(): int { const ch: byte = 36;
  return match ch { 36 => 1, _ => 0 }; }`. The application uses ordinary byte
  comparisons and `match` on bool. This is a preview limitation, not a checker
  fix; it needs an explicit decision in the shared CP42 matrix.
- `Set.add` reports whether insertion occurred. After `contains`, this fact is
  intentionally discarded with `const _`. This retains D079: the Result error
  is handled with `mapError`/`?`.

The linter is deliberately bounded to six textual rules. Full grammar,
exhaustiveness/type checking and automatic fixes are outside its contract.
