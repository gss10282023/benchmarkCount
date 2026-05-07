# MiniWoB Human Audit Notes

Source bundle: `temp/miniwob_case_bundle`.

These notes record the first joint human audit pass for MiniWoB++. The goal is
to keep the data clean before the aggregate paper tables are treated as final.
The machine-readable ledger is
`reviews/evidence_adjudication/audit_items_miniwob.csv`.

## Current scorer output before adjudication

The flat score file has 300 records from 100 MiniWoB++ case units and three
agents.

| Layer | Count |
|---|---:|
| Released evaluator success | 120 / 300 |
| Native evidence P / F / U | 120 / 168 / 12 |
| Stronger evidence S / F / U / NA | 17 / 70 / 3 / 210 |
| Released success -> native non-Pass | 0 |
| Released failure -> native Unknown | 12 |
| Native Pass -> stronger non-Pass | 24 |

The important distinction is that the 12 native Unknown records are not real
evidence gaps. They are unfinished, reward-0 MiniWoB episodes that the released
benchmark already marks as failures. Under the paper's denominator rule, those
records remain in `N` and count as Evidence Fail.

## Human audit decisions

### Native-layer corrections

We apply two native-layer corrections.

1. Relabel all 12 native Unknown records to Evidence Fail. These are nonterminal
   or infeasible episodes with `DONE_GLOBAL=false` and native reward 0.
   Timeouts, incomplete episodes, and `report_infeasible` after task start are
   failures when the native benchmark would fail the run; they are not Unknown.
2. Relabel `miniwob.find-greatest` for GPT-5.4 and Claude 4.7 from Evidence
   Pass to Evidence Fail. The retained DOM shows that the selected card is not
   the greatest card, even though the native evaluator reports success.

After these corrections, the native-aligned MiniWoB result is:

| Scope | Released native score | Evidence P/F/U | Bound |
|---|---:|---:|---:|
| All MiniWoB | 120/300 = 40.0% | 118 / 182 / 0 | [39.3%, 39.3%] |
| GPT-5.4 | 39/100 = 39.0% | 38 / 62 / 0 | [38.0%, 38.0%] |
| Claude 4.7 | 42/100 = 42.0% | 41 / 59 / 0 | [41.0%, 41.0%] |
| DeepSeek V4 Pro | 39/100 = 39.0% | 39 / 61 / 0 | [39.0%, 39.0%] |

Thus MiniWoB does not show a native evidence-retention problem in this sample.
The corrected native bound is narrow; the small outside-bound gap is due to two
hard false-success records.

### Stronger-layer decisions

We keep the following as substantive stronger-measurement findings:

- `copy-paste` and `copy-paste-2`: agents can pass by directly filling the
  answer input instead of copying/pasting from the source textarea.
- `scroll-text`: agents can pass by filling the answer without scrolling the
  textarea.
- `click-tab-2-medium`: the official generator can empty Tab 2 and reward
  clicking the tab itself, even though the task text asks the agent to find and
  click a link.
- `click-checkboxes-large`: native reward can be positive even when one
  requested checkbox remains unchecked.
- `use-colorwheel`: direct fill of the underlying input, or submitting the
  default value, can satisfy the native positive-reward rule without using the
  color picker as requested.
- `stock-market`: the native evaluator reports success, but the retained
  observations bracket rather than pin the exact click-time price.

We treat the geometry tasks (`bisect-angle`, `circle-center`,
`find-midpoint`) as scorer/checklist overreach. The current stronger conditions
ask for exact geometry, while the MiniWoB native evaluator is tolerance-based.
Those rows should not be used as benchmark-facing evidence unless the stronger
condition is rewritten.

## Paper-facing interpretation

MiniWoB is useful as a contrast case. Unlike AgentDojo, it does not mainly fail
because post-state artifacts are missing. Unlike tau3 retail, it has only a
small native label conflict after audit. Its main lesson is different:
result-only or tolerance-based rewards can be well supported as native labels
while still being weak measurements of the interaction the task text appears to
request.
