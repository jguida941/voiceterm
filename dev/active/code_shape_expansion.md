# Code Shape Expansion Plan

**Status**: active  |  **Last updated**: 2026-03-16 | **Owner:** Tooling/code governance
Execution plan contract: required
This tracked companion remains mirrored in `dev/active/MASTER_PLAN.md` under
`MP-378`. It is a **subordinate research-evidence document** feeding
`dev/active/review_probes.md` Phase 5b+ evaluation decisions rather than a
second execution authority. New probes researched here extend future
`review_probes.md` tranches and use the same framework:
`probe_bootstrap.py`, `check_bootstrap.py`, `RiskHint`, `ProbeReport`,
`GuardContext`, and the existing function scanners.

## Scope

Add new deterministic code-shape guards and probes that detect structural
anti-patterns not covered by any existing guard, probe, CodeRabbit rule, or
standard static analyzer. The thesis: **good code has a recognizable shape**,
and that shape can be measured without running the code. These measurements
guide AI agents toward better code by providing machine-readable detection
with actionable remediation instructions.

### Relationship to other plans

- **`review_probes.md`** (MP-368..375): Owns probe framework + 13 shipped
  probes + Phase 5b evaluation gate. This plan is subordinate; new probes
  must pass Phase 5b evidence checks before shipping.
- **`portable_code_governance.md`** (MP-376): Owns engine portability. New
  probes must stay portable (zero devctl imports, repo-policy-driven scoping).
- **`ai_governance_platform.md`** (MP-377): Owns product extraction. Phases
  7-8 of this plan are BLOCKED until MP-377 ships runtime contracts.

### Phase 5b evaluation gate (required)

Before any probe implementation proceeds, the probe must satisfy
`review_probes.md` Phase 5b criteria:
1. Baseline VoiceTerm scan shows <5% false-positive rate
2. Findings are TRUE positives (real problems, not acceptable code)
3. AI instruction is actionable (AI agent can implement the fix)
4. No conflicting guidance with existing guards/probes

### What makes these different from existing tools

| Property | CodeRabbit / SonarQube | ESLint / Clippy | This system |
|---|---|---|---|
| Growth-based non-regression | No | No | Yes — diff-based, not absolute |
| AI remediation instructions | No | No | Yes — `ai_instruction` per finding |
| Closed-loop AI fix cycle | No | No | Yes — autonomy-loop reads findings |
| Three-tier severity model | No | Partially | Yes — hard guard vs probe vs AI review |
| Academic metric coverage | Partial (SonarQube has cognitive complexity) | No | Expanding here |

### Strategic principles

1. Each new probe/guard must detect a pattern that is **deterministic** (same
   input always produces same output) and **structural** (visible from AST or
   text, no runtime needed).
2. Prefer probes (advisory, exit 0) for new detection categories until
   false-positive rate is validated below 5%. Promote to hard guard only after
   dogfooding with explicit criteria: <2% FP rate, shipped 2+ weeks, zero
   suppression requests.
3. Every finding must carry an `ai_instruction` that tells an AI agent exactly
   how to fix it — not just what's wrong.
4. New probes must use existing scanning infrastructure (`scan_rust_functions`,
   `scan_python_functions`, `GuardContext`, `strip_cfg_test_blocks`) to stay
   portable.
5. Registration in `script_catalog.py`, `check_support.py`, `AGENTS.md`, and
   the probe report renderer must happen in the same change as the probe code.

---

## Shared infrastructure build order

Build these shared modules before the phases that need them:

### Phase 0a: tokenizer_utils.py (~100 lines) — before Phase 1

Regex-based identifier/word extractor for Python and Rust. Reused by
`probe_identifier_density` (Phase 1) and later by `probe_halstead_volume` /
`probe_code_entropy` (Phase 4).

- Rust: mask comments/strings (existing `mask_rust_comments_and_strings()`),
  then regex tokenize on `\b[A-Za-z_]\w*\b`.
- Python: regex tokenize (can't rely on `ast.tokenize` for partial code).
- Output: set of unique identifiers, total identifier count.

### Phase 0b: halstead_metrics.py (~300 lines) — before Phase 4

Extends tokenizer to classify operators vs operands. Computes Halstead
Volume, Difficulty, and Shannon entropy.

- Token stream extractor (language-aware regex): ~150 lines
- Halstead volume/difficulty calculator: ~100 lines
- Shannon entropy calculator: ~50 lines

### Phase 5 prereq: cohesion_graph_builder.py (~150 lines)

Builds method-connectivity graphs for LCOM4 calculation. Methods are nodes,
edges connect methods sharing instance variables. Count connected components.

---

## Probe metadata registry

Every probe must specify `review_lens`, `risk_type`, severity thresholds,
and a `practices.py` entry. Audit-validated assignments:

| Probe | Language | review_lens | risk_type | MEDIUM | HIGH |
|---|---|---|---|---|---|
| `probe_blank_line_frequency` | Both | `design_quality` | `readability_smell` | >30L, <2 blanks | >20L, 0 blanks |
| `probe_cognitive_complexity` | Both | `design_quality` | `readability_smell` | score >15 | score >25 |
| `probe_identifier_density` | Both | `design_quality` | `readability_smell` | >20 unique IDs | >30 unique IDs |
| `probe_fan_out` | Both | `design_quality` | `coupling_smell` | >15 calls | >20 calls |
| `probe_mutable_parameter_density` | Rust | `ownership` | `ownership_smell` | 3 &mut params | 4+ &mut params |
| `probe_tuple_return_complexity` | Rust | `design_quality` | `design_smell` | 3-element tuple | 4+ element tuple |
| `probe_side_effect_mixing` | Python | `design_quality` | `design_smell` | 1 I/O + return | 2+ I/O + return |
| `probe_match_arm_complexity` | Rust | `design_quality` | `design_smell` | arm >5 lines | arm >10 lines |
| `probe_halstead_volume` | Both | `design_quality` | `readability_smell` | Volume >500 | Volume >1000 |
| `probe_code_entropy` | Both | `design_quality` | `design_smell` | similarity >0.75 | similarity >0.85 |
| `check_return_type_consistency` | Python | (hard guard) | (hard guard) | — | — |
| `probe_lcom4` | Both | `design_quality` | `design_smell` | LCOM4 = 2 | LCOM4 ≥ 3 |
| `probe_return_point_density` | Both | `design_quality` | `readability_smell` | >5 returns | >8 returns |
| `probe_type_signature_complexity` | Rust | `design_quality` | `readability_smell` | >4 generics | >6 trait bounds |
| `probe_struct_field_cohesion` | Rust | `design_quality` | `design_smell` | 4 shared prefix | 6+ shared prefix |
| `check_enum_conversion_duplication` | Rust | (hard guard) | (hard guard) | — | — |
| `probe_assertion_density` | Rust | `error_handling` | `resilience_gap` | >500 LOC, 0 asserts | (inverse signal) |

### Dropped probes (audit-rejected)

- **`probe_method_chain_length`**: DROPPED — 85% false-positive rate on
  VoiceTerm codebase. Idiomatic Rust iterator chains
  (`.iter().map().filter().collect()`) dominate findings. Would require
  fundamental redesign with comprehensive iterator/builder allowlist before
  re-evaluation.
- **`probe_mutation_density`**: MERGED into existing `probe_dict_as_struct` —
  both detect sequential `d["key"] = value` patterns and suggest dataclasses.
  Enhance `probe_dict_as_struct` with sequential-mutation signal instead of
  creating a duplicate probe.

---

## Execution Checklist

- [x] Research codebase gaps: 4-agent parallel sweep (Rust, Python, infra, academic)
- [x] Create phased execution plan with MP-378 scope
- [x] Register in INDEX.md, MASTER_PLAN.md, AGENTS.md
- [x] 8-agent architecture audit (overlap, infrastructure, scalability, signal validation)
- [x] Incorporate audit findings: drop method_chain, merge mutation_density,
      add metadata registry, add infrastructure deps, add Phase 5b gate
- [ ] Phase 1: Readability shape probes (blank-line, cognitive complexity, identifier density)
- [ ] Phase 2: Structural coupling + AI-specific probes (fan-out, mutable params, tuple return, side effects, match arms)
- [ ] Phase 3: Information-theoretic probes (Halstead volume, code entropy)
- [ ] Phase 4: Cohesion and return-shape (return type consistency guard, LCOM4, return density)
- [ ] Phase 5: Rust-specific structural (type signature, struct cohesion, enum dedup guard, assertion density)
- [ ] Phase 6: Cross-file and commit-level analysis (CBO, RFC, copy-paste ratio, SLAP) — BLOCKED on MP-377
- [ ] Phase 7: Language expansion (JS/TS and Go scanners + probe ports) — BLOCKED on MP-377

---

## Phase 1: Readability shape probes (MP-378a) — NEXT

Highest value, lowest implementation effort. These address the most common
AI-generated code problems: walls of code, dense expressions, and poor visual
structure. All are advisory probes (exit 0).

Validated on VoiceTerm: 130+ blank-line findings (100% TP), 46+ cognitive
complexity findings (85% TP), identifier density findings (projected high TP).

### probe_blank_line_frequency — Python + Rust

Detects functions >20 lines with zero blank lines (wall-of-code). Research
(Buse & Weimer 2008) shows blank lines improve readability more than comments.
AI-generated code notoriously lacks visual structure.

**Metadata:** `review_lens="design_quality"`, `risk_type="readability_smell"`

**Signals:**
- Function >20 lines with 0 blank lines → HIGH
- Function >30 lines with <2 blank lines → MEDIUM

**AI instruction:** "Add blank lines between logical sections of this function.
Group related statements, separate setup from computation from output. Aim for
one blank line every 5-8 lines of code."

**Best-practice entry:**
```
Key: blank_line_structure
Title: Add visual breaks between logical blocks
Example before: 50-line wall of code with no blank lines
Example after: Same code with blank lines separating setup, computation, output
```

**Implementation:** Reuse `scan_rust_functions` / `scan_python_functions` to
extract function bodies, count blank lines in each body.

### probe_cognitive_complexity — Python + Rust

Measures reading difficulty with nesting-multiplicative penalties. Unlike the
existing `check_structural_complexity` (which adds branch points + nesting as
a flat sum with max_score=90), cognitive complexity penalizes nesting
multiplicatively. These are **different metrics answering different questions**:
- Structural complexity: "How much state/flow does this function contain?"
- Cognitive complexity: "How hard is it to read?"

Example divergence:
- Flat `match` with 20 arms: structural score=20, cognitive score=20
- 4-deep nested `if`: structural score=7, cognitive score=1+2+3+4=10

**Metadata:** `review_lens="design_quality"`, `risk_type="readability_smell"`

**Signals:**
- Score >15 per function → MEDIUM
- Score >25 per function → HIGH

**Calibration note:** These thresholds are NOT comparable to
`check_structural_complexity` max_score=90. They must be validated against
VoiceTerm baseline distribution (percentile-based: 75th=MEDIUM, 90th=HIGH).

**Scoring rules:**
1. +1 for each break in linear flow (`if`, `else if`, `else`, `for`, `while`,
   `match`, `catch`, ternary, mixed `&&`/`||` sequences)
2. +1 nesting penalty per enclosing level when a flow-break occurs inside
   another
3. No increment for early `return`, `break`, `continue` (shorthand patterns)

**AI instruction:** "This function has cognitive complexity {score} (threshold:
{threshold}). The deeply nested control flow makes it hard to read. Refactor by:
(1) extracting nested blocks into named helper functions, (2) using early
returns to flatten guard clauses, (3) keeping each function at one level of
abstraction."

**Best-practice entry:**
```
Key: cognitive_complexity
Title: Reduce reading difficulty by extracting nested logic
Example before: if a { if b { for x in items { if c { ... } } } }
Example after: if !a { return; } if !b { return; } process_items(items);
```

**Implementation:** Walk function bodies tracking nesting depth. On each
flow-break keyword, add `1 + current_nesting_depth`. Can reuse branch-point
regex patterns from `check_structural_complexity.py`.

### probe_identifier_density — Python + Rust

Measures unique identifiers per function. >20 unique identifiers means a reader
must track 20+ names in working memory simultaneously. AI generates many
throwaway temporaries that inflate this count.

**Metadata:** `review_lens="design_quality"`, `risk_type="readability_smell"`

**Signals:**
- >20 unique identifiers in one function → MEDIUM
- >30 unique identifiers → HIGH
- >30% single-character identifiers (excluding `i`, `j`, `k`, `_`) → MEDIUM

**AI instruction:** "This function uses {count} unique identifiers — too many
to hold in working memory. Extract sub-computations into named helper functions
that encapsulate their own variable scope, aiming for 10-15 identifiers per
function."

**Best-practice entry:**
```
Key: identifier_density
Title: Reduce unique identifier count per function
Example before: def transform(data): x=...; y=...; z=...; w=...; u=...; v=...
Example after: def transform(data): subtotal = compute_subtotal(data); return apply_adjustment(subtotal)
```

**Implementation:** Use `tokenizer_utils.py` (Phase 0a) for regex word-boundary
extraction. Collect unique identifier sets, exclude language keywords and
builtins.

### Execution checklist (Phase 1)

- [ ] Build `tokenizer_utils.py` shared module (Phase 0a prerequisite)
- [ ] `probe_blank_line_frequency.py` — implement + tests
- [ ] `probe_cognitive_complexity.py` — implement + tests
- [ ] `probe_identifier_density.py` — implement + tests
- [ ] Register all three in `script_catalog.py` and `check_support.py`
- [ ] Add 3 best-practice entries to `probe_report/practices.py`
- [ ] Add signal-to-practice mappings in renderer
- [ ] Update `AGENTS.md` probe catalog
- [ ] Run `probe-report` on VoiceTerm codebase, validate <5% FP rate
- [ ] Update `run_probe_report.py` to include new probes
- [ ] Record Phase 5b evaluation evidence in progress log

---

## Phase 2: Structural coupling + AI-specific probes (MP-378b) — NEXT AFTER PHASE 1

Merged original Phases 2+3 after audit reordering. Simpler probes first
(mutable_parameter_density), complex probes later (fan_out, match_arm).

Validated on VoiceTerm: fan_out 100-120 findings at >15 threshold (~70% TP),
tuple_return 10 findings (0% FP, perfect signal), side_effect_mixing ~70
findings (~75% TP), match_arm_complexity (projected high TP).

### probe_fan_out — Python + Rust

Counts distinct function/method calls per function. High fan-out means a
function depends on many other modules — hard to test, hard to change.

**Metadata:** `review_lens="design_quality"`, `risk_type="coupling_smell"`

**Signals:**
- >15 distinct calls in one function → MEDIUM (raised from 10 per audit — 70% TP at 10, projected 85%+ at 15)
- >20 distinct calls → HIGH

**AI instruction:** "This function calls {count} different functions — it's an
orchestrator mixing too many concerns. Extract groups of related calls into
sub-orchestrators, each responsible for one aspect (e.g., separate setup,
computation, and output phases)."

**Implementation:** Regex-based call extraction from function bodies. Count
unique `name(` patterns, excluding keywords (`if`, `for`, `while`, `match`,
`return`, `print`).

### probe_mutable_parameter_density — Rust only

Detects functions accepting 3+ `&mut` parameters. Multiple mutable references
make it impossible for callers to see which parameter gets modified.
Complements `check_parameter_count` (which measures total arity, not mutation
surface).

**Metadata:** `review_lens="ownership"`, `risk_type="ownership_smell"`

**Signals:**
- 3 `&mut` parameters → MEDIUM
- 4+ `&mut` parameters → HIGH

**AI instruction:** "This function takes {count} mutable references (`&mut`).
Callers can't see which parameter gets modified. Aggregate related mutable
state into a single context struct (e.g., `struct EventLoopContext {{ state:
&mut State, timers: &mut Timers, deps: &mut Deps }}`) so the function
signature clearly communicates its mutation surface."

**Implementation:** Parse function signatures for `&mut` parameter patterns.
Exclude `&mut self`.

### probe_tuple_return_complexity — Rust only

Detects functions returning tuples with 3+ elements. Found in
`dispatch_pty.rs:209` — `(bool, bool, bool, bool, Option<T>)`. Call sites
become unreadable. 0% FP rate — perfect signal.

**Metadata:** `review_lens="design_quality"`, `risk_type="design_smell"`

**Signals:**
- 3-element tuple return → MEDIUM
- 4+ element tuple return → HIGH

**AI instruction:** "This function returns a {count}-element tuple. Define a
named struct with descriptive field names (e.g., `struct CursorState {{ saved:
bool, restored: bool, active: bool }}`) so call sites access results by name
instead of position."

**Best-practice entry:**
```
Key: tuple_return_complexity
Title: Replace tuple returns with named structs
Example before: fn parse(input: &str) -> (bool, String, Vec<String>) { ... }
Example after: struct ParseResult { success: bool, value: String, errors: Vec<String> }
               fn parse(input: &str) -> ParseResult { ... }
```

**Implementation:** Parse function return types for tuple syntax `-> (T, U, V)`.
Count comma-separated type elements.

### probe_side_effect_mixing — Python only

Detects functions that both compute values AND write to disk/stdout. Found
7+ instances in VoiceTerm tooling (e.g., SVG generation + file write in same
function). Makes unit testing require filesystem mocking.

**Metadata:** `review_lens="design_quality"`, `risk_type="design_smell"`

**Signals:**
- Function contains both `return <value>` AND `path.write_text()`/`open(` → MEDIUM
- Function contains `return <value>` AND ≥2 I/O operations → HIGH

**Exclusions:** Test files, pure logging (`logging.info`), `__main__` blocks.

**AI instruction:** "This function both computes a value AND performs I/O.
Split into a pure function returning data and a thin I/O wrapper:
`def generate_and_save(path): content = pure_generate(); path.write_text(content)`"

**Best-practice entry:**
```
Key: side_effect_mixing
Title: Separate computation from I/O
Example before: def render(path): content = compute(); path.write_text(content); return content
Example after: def pure_render() -> str: return compute()
               def render(path): content = pure_render(); path.write_text(content); return content
```

### probe_match_arm_complexity — Rust only

Detects match expressions with arms containing 5+ lines of procedural code
with state mutations. Found in `overlay.rs:50-200` with 15+ arms each calling
2-3 state-mutating functions.

**Metadata:** `review_lens="design_quality"`, `risk_type="design_smell"`

**Signals (priority order):**
1. Match arm with >10 lines of body → HIGH
2. Match arm with >5 lines of body → MEDIUM
3. Match expression with >10 arms each >3 lines → HIGH (dispatch table smell)

**AI instruction:** "This match expression has {count} complex arms (>{threshold}
lines each). Extract each arm's logic into a named handler function so the match
becomes a clean dispatch table:
`Event::Click(btn) => handle_click(btn),`"

**Best-practice entry:**
```
Key: match_arm_complexity
Title: Extract complex match arms into handler functions
Example before: match event { Click(btn) => { if enabled(btn) { handle(btn); update(btn); } } ... }
Example after: match event { Click(btn) => handle_click(btn), Hover => handle_hover() }
```

### Execution checklist (Phase 2)

- [ ] `probe_fan_out.py` — implement + tests
- [ ] `probe_mutable_parameter_density.py` — implement + tests
- [ ] `probe_tuple_return_complexity.py` — implement + tests
- [ ] `probe_side_effect_mixing.py` — implement + tests
- [ ] `probe_match_arm_complexity.py` — implement + tests
- [ ] Register all five in catalog + support + AGENTS.md
- [ ] Add 5 best-practice entries + renderer mappings
- [ ] Validate on VoiceTerm codebase, record Phase 5b evaluation evidence
- [ ] Enhance `probe_dict_as_struct` with sequential-mutation signal (replaces
      dropped `probe_mutation_density`)

---

## Phase 3: Information-theoretic probes (MP-378c) — PLANNED

Academic-grade metrics that capture dimensions none of the existing guards
touch. Requires `halstead_metrics.py` (Phase 0b) infrastructure.

### probe_halstead_volume — Python + Rust

Measures information density: `Length × log₂(Vocabulary)` where vocabulary =
distinct operators + operands, length = total operators + operands.

**Metadata:** `review_lens="design_quality"`, `risk_type="readability_smell"`

**Signals:**
- Volume >500 per function → MEDIUM
- Volume >1000 per function → HIGH

**Calibration required:** Run tokenizer on all Rust/Python source, compute
Halstead distributions, set percentile-based thresholds (75th=MEDIUM,
90th=HIGH). Validate <5% FP on 100-200 function sample.

**AI instruction:** "This function has Halstead Volume {volume} — it uses too
many distinct symbols for comfortable reading. Split into sub-functions with
focused vocabularies of 10-15 distinct identifiers each."

### probe_code_entropy — Python + Rust (diagnostic only)

Measures Shannon entropy of token distributions per function. Catches
near-duplicate code that differs by 1-2 tokens. This is a **diagnostic
probe** — near-duplicates require domain understanding to fix, so the
ai_instruction is advisory rather than prescriptive.

**Metadata:** `review_lens="design_quality"`, `risk_type="design_smell"`

**Signals:**
- Two functions in same file with entropy-based similarity >0.75 → MEDIUM
- Two functions with similarity >0.85 → HIGH (near-duplicate)
- Entropy <0.3 (repetitive boilerplate) in function >15 lines → LOW

**AI instruction:** "Functions `{fn_a}` and `{fn_b}` are {pct}% similar by
token distribution. Inspect manually — if they're near-duplicates, extract
shared logic into a parameterized helper. If they're legitimately different,
no action needed."

### Execution checklist (Phase 3)

- [ ] Build `halstead_metrics.py` shared module (Phase 0b prerequisite)
- [ ] `probe_halstead_volume.py` — implement + tests
- [ ] `probe_code_entropy.py` — implement + tests
- [ ] Calibrate thresholds against VoiceTerm baseline (100-200 function sample)
- [ ] Register + best-practice entries
- [ ] Validate on VoiceTerm codebase

---

## Phase 4: Cohesion and return-shape (MP-378d) — LATER

Requires cross-method analysis within classes. Guard promotion candidates.

### check_return_type_consistency — Python (hard guard)

Detect functions declaring `dict`/`list`/`tuple` return type but having code
paths that return `None` without `Optional`/`| None` annotation. This is a
safety issue — callers will get `NoneType has no attribute` at runtime.

**Guard promotion criteria:** Implement as hard guard (exit 1) from day one
— type mismatches are safety bugs, not style issues. Growth-based: only flag
new inconsistencies.

### probe_lcom4 — Python + Rust

Lack of Cohesion of Methods (LCOM4). Requires `cohesion_graph_builder.py`.
Complements `check_god_class` (which measures size, not cohesion). Can reuse
cross-scope analysis patterns from `probe_fan_out` (Phase 2).

**Metadata:** `review_lens="design_quality"`, `risk_type="design_smell"`

**AI instruction:** "This class has LCOM4={n} — it contains {n} disconnected
method groups that don't share instance variables. Methods {group1} use fields
{fields1} while methods {group2} use fields {fields2}. Split into separate
focused classes."

### probe_return_point_density — Python + Rust

**Metadata:** `review_lens="design_quality"`, `risk_type="readability_smell"`

**AI instruction:** "This function has {count} return statements (density
{density:.0%}). Multiple scattered return points make control flow hard to
trace. Consolidate into 1-2 exit points using intermediate variables or early
guard clauses."

### Execution checklist (Phase 4)

- [ ] Build `cohesion_graph_builder.py` (Phase 5 prereq)
- [ ] `check_return_type_consistency.py` — implement + tests
- [ ] `probe_lcom4.py` — implement + tests
- [ ] `probe_return_point_density.py` — implement + tests

---

## Phase 5: Rust-specific structural probes (MP-378e) — LATER

### probe_type_signature_complexity — Rust

**Metadata:** `review_lens="design_quality"`, `risk_type="readability_smell"`

**Calibration note:** Run probe on 10+ real VoiceTerm impl blocks and validate
>10 trait-bound cases are correctly counted before shipping.

### probe_struct_field_cohesion — Rust

**Metadata:** `review_lens="design_quality"`, `risk_type="design_smell"`

### check_enum_conversion_duplication — Rust (hard guard)

**Guard promotion criteria:** Implement as hard guard only after proving
repeated enum conversion families are common enough to justify blocking CI.
Start as probe, promote after 2+ weeks with <2% FP rate.

### probe_assertion_density — Rust

**Metadata:** `review_lens="error_handling"`, `risk_type="resilience_gap"`

Note: This is an inverse signal (absence of assertions). Unique measurement.

### Execution checklist (Phase 5)

- [ ] `probe_type_signature_complexity.py` — implement + tests
- [ ] `probe_struct_field_cohesion.py` — implement + tests
- [ ] `check_enum_conversion_duplication.py` — start as probe, evaluate for guard
- [ ] `probe_assertion_density.py` — implement + tests

---

## Phase 6: Cross-file and commit-level analysis (MP-378f) — BACKLOG

**BLOCKED until MP-377 ships runtime contracts.** Requires call-graph
construction, git-diff integration, and multi-file import analysis that
must align with the portable runtime boundaries being defined in MP-377.

### probe_coupling_between_objects — Python + Rust

CBO (Chidamber & Kemerer): count distinct external types referenced by a
class/module. >10 = high coupling. Requires cross-file import/type resolution.
Effort: 500+ LOC, requires call-graph builder.

### probe_response_for_class — Python + Rust

RFC: total methods callable in response to a message (own methods + first-level
callees). >50 = hard to test. Requires call-graph construction.

### probe_copy_paste_ratio — Both (commit-level)

GitClear 2025 research: classify changed lines as added/copy-pasted/moved/
modified/deleted. Flag commits where copy-paste ratio >15%. Requires git
diff analysis with fuzzy similarity matching. Effort: 400-600 LOC + external
dependencies.

### probe_abstraction_level_consistency — Both

SLAP (Single Level of Abstraction Principle). Heuristic; hardest to implement
well. Classify statements as high-level calls vs low-level primitives.

---

## Phase 7: Language expansion (MP-378g) — BACKLOG

**BLOCKED until MP-377 ships repo-pack packaging and language scanner
registry.** Without defined language-pack semantics, adding JS/TS/Go probes
may create portability debt instead of products. Defers to
`review_probes.md` Phases 13-14 which independently track language expansion.

---

## Summary: Phase priority and effort

| Phase | Theme | Probes/Guards | Effort | Priority |
|---|---|---|---|---|
| 0 | Shared infrastructure | tokenizer, Halstead module | LOW | PREREQUISITE |
| 1 | Readability shape | 3 probes | LOW-MED | NEXT |
| 2 | Coupling + AI-specific | 5 probes | MEDIUM | NEXT |
| 3 | Information theory | 2 probes | HIGH | PLANNED |
| 4 | Cohesion + return shape | 2 probes + 1 guard | MEDIUM | LATER |
| 5 | Rust-specific structure | 3 probes + 1 guard | MEDIUM-HIGH | LATER |
| 6 | Cross-file / commit-level | 4 probes | VERY HIGH | BACKLOG (MP-377 blocked) |
| 7 | Language expansion | scanners + ports | VERY HIGH | BACKLOG (MP-377 blocked) |

Total new instruments: **20 probes + 2 hard guards** across 7 phases
(reduced from 22+2 after dropping method_chain and merging mutation_density).

---

## Academic references

- **Cognitive Complexity:** SonarSource white paper (2016). Nesting-multiplicative
  readability scoring.
- **Halstead Metrics:** Halstead (1977). Information-theoretic code measurement
  from operator/operand counts.
- **Maintainability Index:** Oman & Hagemeister (1992). Composite of Halstead
  Volume + cyclomatic complexity + LOC.
- **Buse-Weimer Readability:** Buse & Weimer (2008/2010). ML-validated
  structural features — blank lines, identifier density, parenthesis density.
- **LCOM4:** Chidamber & Kemerer suite. Cohesion via shared-variable graph
  connectivity.
- **CBO/RFC:** Chidamber & Kemerer suite. Coupling and response-surface
  complexity.
- **Code Entropy:** Shannon entropy applied to token distributions for
  near-duplicate detection.
- **GitClear 2025:** AI code quality research — copy-paste ratio, moved-line
  ratio as AI-specific quality metrics.
- **Assertion Density:** Microsoft Research (2006). Negative correlation between
  assertion density and fault density.
- **Identifier Quality:** Butler et al. (2010), Hofmeister et al. (2017).
  Descriptive names correlate with faster defect detection.

---

## Progress Log

- 2026-03-16: Plan created from comprehensive 4-agent research sweep.
  Studied all 60 guards + 13 probes + infrastructure layer. Analyzed Rust
  source (239 files) and Python tooling (515 files) for uncovered patterns.
  Cross-referenced against academic literature and industry tools
  (SonarQube, CodeRabbit, ESLint, Clippy, GitClear). Identified 22 new
  probe candidates + 2 guard candidates across 8 phases, prioritized by
  value and implementation effort.
- 2026-03-16: 8-agent architecture audit completed. Findings:
  (1) Authority fragmentation — plan restructured as subordinate to
  review_probes.md with Phase 5b evaluation gate requirement.
  (2) probe_method_chain_length DROPPED — 85% FP rate on VoiceTerm
  (idiomatic iterator chains dominate findings).
  (3) probe_mutation_density MERGED into existing probe_dict_as_struct —
  both detect same d["key"] = value pattern.
  (4) Shared infrastructure build order documented (tokenizer, Halstead,
  cohesion graph).
  (5) Probe metadata registry added (review_lens, risk_type for all probes).
  (6) AI instructions strengthened with code examples.
  (7) fan_out threshold raised from >10 to >15 (70% TP at 10, projected
  85%+ at 15).
  (8) Phases 6-7 explicitly BLOCKED on MP-377 runtime contracts.
  (9) Phase 7 language expansion deferred to review_probes.md Phases 13-14.
  (10) Signal validation: blank_line (130+ findings, 100% TP),
  mutation_density (205+, 100% TP), tuple_return (10, 0% FP),
  cognitive_complexity (46, 85% TP), side_effect (70, 75% TP).
- 2026-03-16: Authority surfaces reconciled after review-channel/runtime fix
  work. `INDEX.md`, `MASTER_PLAN.md`, and `AGENTS.md` now describe this file
  as a supporting research/calibration companion, while `review_probes.md`
  owns promotion, sequencing, and implementation authority for any accepted
  Phase 5b+ probe.
- 2026-03-16: First promotion shipped through `review_probes.md`: the existing
  `probe_tuple_return_complexity.py` implementation is now enabled as the
  initial code-shape addition because it already existed in-tree, tested
  cleanly, and had the strongest low-noise audit result. Readability probes
  remain the next staged backlog after incremental signal quality is verified
  against the current structural-complexity surfaces.
- 2026-03-16: Follow-up architecture audit from `check --profile ci` clarified
  the next packaging requirement for this companion tranche: before additional
  code-shape probes are enabled, move the family out of the crowded flat
  `dev/scripts/checks/` root into a focused namespace with thin public
  wrappers, and remove the two copied helper bodies currently tripping the
  duplication guard.
- 2026-03-16: That namespace cleanup is now complete. The staged probe family
  moved under `dev/scripts/checks/code_shape_probes/`, root entrypoints were
  reduced to metadata-bearing shims, the tuple-return test moved under the
  topic-aligned `dev/scripts/devctl/tests/checks/code_shape_probes/` path, and
  the duplicated signature/path helpers were consolidated into one package
  helper module.

## Audit Evidence

- Research sweep: 4 parallel agents (Rust gaps, Python gaps, infrastructure
  study, academic/industry research)
- Architecture audit: 8 parallel agents (phase structure, infrastructure reuse,
  overlap analysis, platform alignment, registration scalability, AI instruction
  quality, review_probes integration, real-world signal validation)
- Rust analysis: 10 uncovered pattern categories across 239 files
- Python analysis: 9 uncovered pattern categories across 515 files
- Signal validation: 7 probes spot-checked against VoiceTerm codebase with
  concrete finding counts and FP rates
- Dropped: probe_method_chain_length (85% FP), probe_mutation_density (merged)
