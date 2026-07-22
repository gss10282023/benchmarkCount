## AppWorld GPT-5.6 Sol strict drafting v3

These AppWorld-only rules are mandatory. They narrow any looser wording or
examples in the base prompt.

### Native AppWorld success semantics

- Treat the packet's explicit `TestTracker` semantics as authoritative.
- `TestTracker.success` is true exactly when every registered test passes:
  `pass_count == num_tests`.
- A scoring test is registered by a `with test(...):` block. Encode the
  conjunction of those registered blocks in `benchmark_success` and
  `success_if`; any failed registered block belongs in `fail_if`.
- The packet contains a machine-verifiable registered-test registry. Copy its
  `required_native` object exactly as the complete top-level `native` object.
  Do not add, omit, reorder, rewrite, or paraphrase any native text, rationale,
  support pointer, or decisive artifact. Native scoring prose is not
  model-authored for AppWorld. The registry also contains the
  exact `[appworld_test_NNN_<hash>]` markers and the registry's deterministic
  text fields. Copy `required_benchmark_success_text` byte-for-byte into
  `benchmark_success.text`. In registry order, create exactly one `success_if`
  item per registered test and copy its `required_success_if_text` byte-for-byte;
  do the same in `fail_if` with `required_fail_if_text`. Put no AppWorld marker
  in any other field. Create exactly one `undecided_if` item and copy the
  registry's `required_undecided_if_text` and
  `required_undecided_if_rationale` byte-for-byte. Do not change case or
  whitespace, and do not invent, omit, reorder, or duplicate a marker. Use
  the complete native object beyond the frozen `required_native` projection.
- An assignment in `evaluate()` that is outside every `with test(...):` block
  is not a scoring test. Never make `test.task_completed`, `task.status`,
  `active_tasks[0].status`, or another dynamically assigned `test.*` attribute
  a native success requirement unless it is itself checked inside a registered
  `with test(...):` block.
- Do not move a failed registered test into `undecided_if`. Use
  `undecided_if` only when retained evidence cannot determine a registered
  test's result. A non-scoring dynamic field must not affect `undecided_if`
  either.

### Frozen stronger-gap composition

- The packet contains a machine-verifiable stronger-gap registry reviewed and
  frozen before this draft call. It is authoritative for
  `stronger.additional_conditions`.
- Copy each `case.gaps[*].required_condition` object exactly, byte-for-byte in
  registry order, into `stronger.additional_conditions`. If `case.gaps` is
  empty, output an empty stronger list.
- Do not infer, add, omit, merge, split, reorder, paraphrase, or otherwise
  rewrite a stronger condition. The registry already records every approved
  explicit task-intent/evaluator gap for this case.
- Never create a stronger condition merely from an assignment outside
  `with test(...)`, including `test.task_completed`, task status, or its source
  predicate. Such dynamic fields are forbidden on the stronger surface. The
  current registry contains no convenience-field exception.

### Stored-artifact boundary

- Official source files and source-only values, including
  `ground_truth/answer.json`, `private_data.json`, and evaluator source, are
  support for interpreting the test. They are not stored post-run artifacts.
- In every `native.decisive_artifacts[*].artifact` and `.question`, never use
  the literal terms `ground-truth`, `ground truth`, `ground_truth`, `gold answer`,
  `answer key`, or `reference answer`. Do not describe an official
  source answer or private source value as if it were retained run evidence.
- For an answer-comparison test, use the retained submitted answer and the
  retained official evaluator/TestTracker comparison result. A safe compact
  artifact is `Retained submitted answer and official evaluator comparison
  result`; a safe question is `Does the retained evaluator result show that
  the registered answer-comparison test passed?` Do not name, reproduce, or
  call for retaining the official source answer.
- Other decisive artifacts must likewise be real post-run evidence, such as a
  retained start/end database diff, API log, environment trace, or TestTracker
  result. Source citations may support the artifact question but do not turn
  the cited source into run evidence.

### Source-pointer grammar

- Keep the v2 source-path gate: before `::`, use exactly `case_packet.md` or a
  path copied verbatim from `## Source Inventory`.
- Never cite `draft_instructions.md`, `template.yaml`, `output_schema.json`, or
  `draft_body.json` as support. Do not invent a path or use a URL, absolute
  path, leading `./`, or `..` traversal.
- For an entire JSON document, the location is exactly `$`. Never use
  `root`, `entire_file`, or a prose synonym.
- A nested JSON location must be a real, source-local path rooted at `$`, using
  object keys and zero-based list indexes, for example
  `$.outer.items[0].value`. Every component must resolve in that JSON file; do
  not invent or approximate a path.
- For non-JSON text, including Python, Markdown, JSONL, and YAML,
  citation, use only an in-bounds `L<n>`, an in-bounds `L<n>-L<m>`, or an exact
  source-local symbol. Do not use bare numbers, `line(s) ...`, a paraphrase, or
  a symbol that does not occur in the cited file.

### Frozen tool-less direct-input policy

The turn prompt already contains the complete, byte-bound contents of
`draft_instructions.md`, `template.yaml`, `case_packet.md`, and
`output_schema.json` in a sealed direct-input bundle. Use those four embedded
inputs as the entire drafting context. Do not try to discover, reopen, verify,
or reread them from the filesystem.

Never call a shell or execution tool. Never call `web_search`, a browser,
network, MCP, app, subagent, file-read, file-write, or patch tool. Do not invoke
`sed`, `wc`, `rg`, `awk`, `sort`, `python`, `python3`, or any other executable.
The Codex invocation disables both shell execution surfaces; any tool event is
a hard non-retryable failure.

After reasoning over the sealed inputs, emit exactly one agent message
containing only the final schema-compliant JSON body. Do not emit an interim
agent message. The runtime validator reconstructs the sealed bundle from the
frozen inputs, checks its component and whole-bundle hashes, requires zero tool
events, and binds the single final message to the retained checklist.
