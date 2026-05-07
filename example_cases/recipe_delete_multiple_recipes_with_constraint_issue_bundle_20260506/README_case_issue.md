This bundle packages the AndroidWorld case `RecipeDeleteMultipleRecipesWithConstraint` and the full local run artifacts that led us to classify it as a bad / invalid benchmark case.

Note on completeness:
- The original local `experiments/case_packets/androidworld/RecipeDeleteMultipleRecipesWithConstraint` directory was deleted earlier when this case was removed from the current AndroidWorld test list.
- Because of that, this bundle uses the preserved run-time artifacts plus the official AndroidWorld task-definition files to represent the case design and its generated concrete instance.

What the case is supposed to do:
- Official task template: "Delete the recipes from Broccoli app that use {ingredient} in the directions."
- In this concrete run, the ingredient is `Parmesan`.

Why this case looks broken:
1. The generated evaluator input says there are zero true target rows to delete: `task_params.row_objects = []`.
2. The same generated evaluator input also contains many `noise_row_objects` whose `directions` text explicitly mentions `Parmesan`, including examples such as `Chicken Alfredo Pasta`, `Pesto Pasta with Peas`, `Chicken Caesar Salad Wrap`, and `Eggplant Parmesan`.
3. During execution, the agent searched for `Parmesan`, inspected the visible results, found no visible qualifying recipe to delete, and then finished with "no deletions needed".
4. The evaluator still returned `success`.

So the problem is not "the agent successfully deleted the right things". The problem is that the generated target set is inconsistent with the visible world state / search results, which means the case can score success even when nothing is deleted.

Files to inspect first:
- `run/adapter/native_run/native_evaluator_input.json`
- `run/adapter/logs/stdout.log`
- `run/adapter/raw_run.json`
- `run/adapter/native_run/run_summary.json`
- `official_case_definition/recipe.py`
- `official_case_definition/task_metadata.json`
- `official_case_definition/recipe_test.py`

Suggested proof trail:
- In `native_evaluator_input.json`, inspect `task_params.ingredient`, `task_params.row_objects`, and `task_params.noise_row_objects`.
- In `stdout.log`, inspect the final reasoning where the agent concludes there are no deletions to perform.
- In `raw_run.json` and `run_summary.json`, verify that the run was still scored as success.
