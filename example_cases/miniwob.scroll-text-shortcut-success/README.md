`miniwob.scroll-text` was intended to test whether the agent could scroll a text area, find the final word, and submit it. In the real run bundled here, the agent never used a `scroll(...)` action; it directly filled the answer field with `lorem.` and submitted, because the full textarea contents, including the last word, were exposed in the DOM and the textarea `value`. This is why we marked the case as `shortcut_success`: native success was real, but the task's intended interaction was bypassed.

Official upstream:
- Docs: [MiniWoB++ scroll-text](https://miniwob.farama.org/environments/scroll-text/)
- Source: [scroll-text.html](https://github.com/Farama-Foundation/miniwob-plusplus/blob/master/miniwob/html/miniwob/scroll-text.html)

Most important evidence inside this bundle:
- `run/full-miniwob-miniwob.scroll-text-agent_a/adapter/native_run/task_context.json`
- `run/full-miniwob-miniwob.scroll-text-agent_a/adapter/native_run/trajectory/steps.json`
- `run/full-miniwob-miniwob.scroll-text-agent_a/adapter/native_run/browser_artifacts/page_html/step_000_reset.html`
- `run/full-miniwob-miniwob.scroll-text-agent_a/adapter/native_run/native_evaluator_output.json`
- `case_packet/miniwob.scroll-text/raw_case/official/install/miniwob/html/miniwob/scroll-text.html`
