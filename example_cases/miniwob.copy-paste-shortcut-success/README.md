`miniwob.copy-paste` was intended to test whether the agent could copy text from a textarea and paste it into the target textbox before submitting. In the real run bundled here, the agent never performed a true copy/paste interaction; it directly filled the target textbox with the visible source text and then submitted. The official task only checks whether the destination string exactly matches the textarea content, so native success was granted even though the intended interaction was bypassed. That is why we marked the case as `shortcut_success`.

Official upstream:
- Docs: [MiniWoB++ copy-paste](https://miniwob.farama.org/environments/copy-paste/)
- Source: [copy-paste.html](https://github.com/Farama-Foundation/miniwob-plusplus/blob/master/miniwob/html/miniwob/copy-paste.html)

Most important evidence inside this bundle:
- `run/full-miniwob-miniwob.copy-paste-agent_a/adapter/native_run/task_context.json`
- `run/full-miniwob-miniwob.copy-paste-agent_a/adapter/native_run/trajectory/steps.json`
- `run/full-miniwob-miniwob.copy-paste-agent_a/adapter/native_run/browser_artifacts/page_html/step_000_reset.html`
- `run/full-miniwob-miniwob.copy-paste-agent_a/adapter/native_run/native_evaluator_output.json`
- `case_packet/miniwob.copy-paste/raw_case/official/install/miniwob/html/miniwob/copy-paste.html`
