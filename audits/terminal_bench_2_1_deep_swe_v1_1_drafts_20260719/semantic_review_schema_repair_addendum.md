# Schema-repair addendum for failed semantic-review receipts

Apply the complete `semantic_review.prompt.md` contract unchanged. This
addendum only makes the required JSON shape explicit for a `revise` response.
It does not change the audit criteria or the permitted evidence boundary.

When `decision` is `revise`, `revised_checklist` must contain exactly two
top-level fields:

```json
{"native": {"...": "complete native body"}, "stronger": {"additional_conditions": []}}
```

Do not include `schema_version`, `case_unit_id`, `domain`, or `task_id` inside
`revised_checklist`. For every stronger condition, use exactly these fields:

```json
{
  "id": "short_stable_id",
  "text": "case-specific stronger requirement",
  "rationale": "official support plus explicit native measurement gap",
  "decisive_artifacts": [
    {
      "artifact": "a packet-inventory artifact pattern",
      "question": "what this retained artifact can establish",
      "support": ["packet-local source pointer"]
    }
  ],
  "support": ["packet-local official and evaluator/oracle pointers"]
}
```

Do not use any aliases or extra fields such as `measurement_gap`,
`assessed_by`, `assess_with`, `success_if`, `fail_if`, or `undecided_if` inside
a stronger condition. Every `decisive_artifacts` entry must be an object with
`artifact`, `question`, and `support`, not a bare artifact string. If no
stronger condition is justified, use an empty `additional_conditions` array.
