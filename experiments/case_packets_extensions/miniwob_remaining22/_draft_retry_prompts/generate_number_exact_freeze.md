MiniWoB frozen-layer repair instruction for this retry:

- Read `raw_case/derived/drafting_context.json` from the supplied case packet.
- For every item in `stronger_measurement.required_additional_conditions`, copy
  `id`, `text`, `rationale`, and `support` into the corresponding checklist
  condition exactly, without paraphrasing, shortening, reordering, adding, or
  removing entries.
- Keep `decisive_artifacts` separate from source support. Each `artifact` value
  must name a retained post-run artifact type or path from the packet's artifact
  inventory; never put a JSON pointer or source pointer in the `artifact` value.
- Do not add any other stronger condition or change the native criterion.
