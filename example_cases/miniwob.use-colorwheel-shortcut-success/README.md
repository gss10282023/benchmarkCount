`miniwob.use-colorwheel` was intended to test whether the agent could use the color-picker widget to select red and submit. In the real run bundled here, the agent never manipulated the picker widget itself; it directly filled the underlying `input#col` value with `FF0000` and then submitted. The official task computes reward directly from the input field's hex value, so native success was real even though the widget interaction was bypassed. That is why we marked the case as `shortcut_success`.

Official upstream:
- Docs: [MiniWoB++ use-colorwheel](https://miniwob.farama.org/environments/use-colorwheel/)
- Source: [use-colorwheel.html](https://github.com/Farama-Foundation/miniwob-plusplus/blob/master/miniwob/html/miniwob/use-colorwheel.html)

Most important evidence inside this bundle:
- `run/full-miniwob-miniwob.use-colorwheel-agent_b/adapter/native_run/task_context.json`
- `run/full-miniwob-miniwob.use-colorwheel-agent_b/adapter/native_run/trajectory/steps.json`
- `run/full-miniwob-miniwob.use-colorwheel-agent_b/adapter/native_run/browser_artifacts/page_html/step_001.html`
- `run/full-miniwob-miniwob.use-colorwheel-agent_b/adapter/native_run/native_evaluator_output.json`
- `case_packet/miniwob.use-colorwheel/raw_case/official/install/miniwob/html/miniwob/use-colorwheel.html`
