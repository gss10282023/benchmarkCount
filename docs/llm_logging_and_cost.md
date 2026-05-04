# LLM Logging And Cost

## Scope

LLM logging covers Agent A-D calls, contract_drafter calls, judge_only diagnostic calls, and any future LLM role declared in config/manifest. It records audit and cost metadata. It does not fill `tab:cost`; `tab:cost` uses human-time logs only.

## Configuration Source

Provider, model, model version, API key environment variable name, temperature, max_tokens, timeout, retry, rate limit, prompt version, prompt hash, response metadata setting, and cost tracking setting are read from `configs/agents.yaml` and locked manifest. Formal run fails closed on disagreement.

Values for Agent A-D, `contract_drafter`, and `judge_only` must not be hardcoded in code, tests, scorer, runner, paper output, or review packets. API key values are read from environment variables and are never logged.

## LLM Call Log Schema

Each call writes `llm_call/v1`:

```json
{
  "schema_version": "llm_call/v1",
  "call_id": "...",
  "run_id": "...",
  "record_slot_id": "...",
  "attempt_id": "...",
  "contract_draft_id": null,
  "case_unit_id": null,
  "evidence_contract_id": null,
  "contract_version": null,
  "visible_input_hash": null,
  "hidden_input_assertion_hash": null,
  "domain": "...",
  "phase": "...",
  "experiment_type": "...",
  "priority": "...",
  "agent_id_or_role": "Agent A|Agent B|Agent C|Agent D|contract_drafter|judge_only",
  "provider": "...",
  "model": "...",
  "model_version": "...",
  "api_key_env": "...",
  "prompt_version": "...",
  "prompt_hash": "...",
  "prompt_hash_method": "sha256",
  "temperature": 0,
  "max_tokens": 0,
  "timeout_seconds": 0,
  "retry_index": 0,
  "rate_limit_bucket": "...",
  "request_timestamp": "...",
  "response_timestamp": "...",
  "response_metadata": {},
  "token_usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "cached_prompt_tokens": 0,
    "reasoning_tokens": 0,
    "total_tokens": 0
  },
  "cost": {
    "amount": null,
    "currency": "USD",
    "pricing_source": "provider_response|config_estimate|unavailable",
    "pricing_table_id": null,
    "pricing_table_version": null,
    "pricing_source_hash": null,
    "cost_calculation_method": "provider_reported|tokens_times_config_rate|unavailable"
  },
  "config_hash": "...",
  "manifest_hash": "...",
  "redaction_status": "no_secret_logged"
}
```

For Agent A-D execution calls, run-centric fields (`run_id`, `record_slot_id`, `attempt_id`) are required. For contract-drafting calls, which happen before benchmark runs and before locked contract hashes exist, the required linkage fields are:

```text
contract_draft_id
case_unit_id
domain
task_id when available
evidence_contract_id when assigned
contract_template_version/hash
prompt_version
prompt_hash
visible_input_hash
hidden_input_assertion_hash
source_bundle_hash
call_id
```

The locked contract metadata must back-reference the exact contract-drafting LLM `call_id` and `contract_draft_id`. `tab:contract-drafting-metadata`, LLM cost provenance, and drafter-visibility validation must fail closed if a locked contract cannot be linked to the exact LLM call log entry that produced its draft, or if visible-input / hidden-input assertion hashes are missing.

If provider response includes token/cost metadata, use it. If cost is unavailable and a pricing table is configured, mark `pricing_source=config_estimate` and record `pricing_table_id`, `pricing_table_version`, `pricing_source_hash`, and `cost_calculation_method`. If neither is available, record unavailable; do not invent cost. Token usage should preserve provider-specific categories where available, including input, output, cached input, and reasoning tokens.

## Contract Drafter Visibility

Contract drafter allowed inputs:

```text
task_text
official_policy
evaluator_code_or_description
database/API/browser/file/tool schema
trace_schema
available_post_run_artifact_types
native_aligned vs stronger_measurement template
```

Forbidden inputs:

```text
agent identity
agent trace
native score
native evaluator pass/fail scalar
outcome label
alternate view verdicts
evidence label
UNRESOLVE reason
scored values
paper-output values
```

Any contract draft that sees forbidden inputs is discarded for main results and must be redrafted/reviewed/locked.

## Judge-Only Visibility

Judge-only diagnostic must be blind to native_label, native_score, native evaluator pass/fail scalar, outcome label, scored/paper-output values, agent identity, evidence label, UNRESOLVE reason, and alternate view verdicts. The log records a forbidden-input assertion.

## LLM Cost Use

LLM cost logs support audit, monitoring, and final report cost/latency/failure provenance when the paper/report asks for LLM usage statistics. They do not feed `tab:cost`. `tab:cost` is trained annotator wall-clock human-time only.
