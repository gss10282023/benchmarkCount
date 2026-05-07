# Case Packet

## Case Metadata

- domain: `androidworld`
- case_unit_id: `RecipeDeleteMultipleRecipesWithConstraint`
- task_id: `RecipeDeleteMultipleRecipesWithConstraint`

## Source Inventory

- `official/install/android_world/task_metadata.json`
- `official/install/android_world/registry.py`
- `official/install/android_world/task_evals/task_eval.py`
- `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py`
- `derived/official_task_source.json`

## Packet Source Files

### `official/install/android_world/task_metadata.json`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json`

```json
[
  {
    "task_name": "RecipeDeleteMultipleRecipesWithConstraint",
    "task_template": "Delete the recipes from Broccoli app that use {ingredient} in the directions.",
    "difficulty": "hard",
    "tags": [
      "screen_reading",
      "repetition",
      "parameterized"
    ],
    "optimal_steps": "20"
  }
]
```

### `official/install/android_world/registry.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py`

```python
      recipe.RecipeAddMultipleRecipesFromImage,
      recipe.RecipeAddMultipleRecipesFromMarkor,
      recipe.RecipeAddMultipleRecipesFromMarkor2,
      recipe.RecipeAddSingleRecipe,
      recipe.RecipeDeleteDuplicateRecipes,
      recipe.RecipeDeleteDuplicateRecipes2,
      recipe.RecipeDeleteDuplicateRecipes3,
      recipe.RecipeDeleteMultipleRecipes,
      recipe.RecipeDeleteMultipleRecipesWithConstraint,
      recipe.RecipeDeleteMultipleRecipesWithNoise,
```

### `official/install/android_world/task_evals/task_eval.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py`

```python
class TaskEval(abc.ABC):
  """Interface for a task and its evaluation.

  It consists of two parts: a) defining the task, which consists of a template
  and parameters and b) logic to determine if a task is complete.
  """

  template = ""  # Each task eval needs a template.
  device_time = device_constants.DT

  start_on_home_screen = True

  def __init__(self, params: dict[str, Any]):
    self.initialized = False

    # Disabling this check for now as it is causing issues on occasion with a
    # with a RefResolutionError due to inability to resolve json-schema.org.
    # jsonschema.validate(params, self.schema)
    self._params = params

  @property
  @abc.abstractmethod
  def complexity(self) -> float:
    """The complexity of the task.

    We use heuristics to dynamically allocate number of steps based on the
    complexity of the task. These are roughly calculated.

    complexity | budget
    1 | 1-10 steps
    2 | 11-20 steps
    ...
    """

  @property
  def name(self) -> str:
    """The name of the task."""
    return self.__class__.__name__

  @property
  @abc.abstractmethod
  def app_names(self) -> tuple[str, ...]:
    """The names of the apps that the agent will be interacting with during the task.

    Apps will be closed upon app initialization. The app names should correspond
    to the regex patterns in adb_utils._PATTERN_TO_ACTIVITY.
    """

  @property
  @abc.abstractmethod
  def schema(self) -> dict[str, Any]:
    """The JSON Schema of parameters for defining the task.

    E.g., for a task that validates a certain date has been set, this could be
    ```
    {
      "type": "object",
      "properties": {
          "day": {"type": "string"},
          "month": {"type": "string"},
          "year": {"type": "string"},
      },
      "required": ["day", "month", "year"],
    }
    ```
    """

  @property
  def params(self) -> dict[str, Any]:
    """The parameters for defining the task.

    They define the task's inputs: i.e. what is necessary for the task to be
    performed + evaluated.
    """
    return self._params

  @property
  def goal(self) -> str:
    """The language goal constructed from the template with the params."""
    return self.template.format(**self.params)
```

### `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py`

```python
class _RecipeApp(sqlite_validators.SQLiteApp):
  # From TaskEval.
  schema = {}
  app_names = (_APP_NAME,)
  template = ''  # Unused, since we directly build goal in implementations.

  # From sqlite_base.SQLiteApp
  app_name_with_db = _APP_NAME
  db_key = _DB_KEY
  db_path = _DB_PATH
  table_name = _TABLE_NAME
  row_type = sqlite_schema_utils.Recipe


class _RecipeDeleteMultipleRecipes(
    sqlite_validators.DeleteMultipleRows, _RecipeApp
):
  """Task to delete multiple recipes in Broccoli Recipe App."""

  complexity = 2
  n_rows = 3
  n_rows_noise = 0

  @property
  def goal(self) -> str:
    targets = self.params[sqlite_validators.ROW_OBJECTS]
    titles = [r.title for r in targets]
    titles = ', '.join(titles)
    return f'Delete the following recipes from Broccoli app: {titles}.'

  def validate_deletion_integrity(
      self,
      before: list[sqlite_schema_utils.Recipe],
      after: list[sqlite_schema_utils.Recipe],
  ) -> bool:
    """Validates the integrity of the recipe deletion."""
    return sqlite_validators.validate_rows_removal_integrity(
        before, after, [r.recipeId for r in self.rows_to_delete], self.db_key
    )

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for a remove recipe task."""

    recipes = []
    while len(recipes) < cls.n_rows + cls.n_rows_noise:
      candidate = _generate_random_recipe()
      if not any([candidate.title == r.title for r in recipes]):
        recipes.append(candidate)

    if cls.n_rows_noise > 0:
      noise_rows = recipes[: cls.n_rows_noise]
      target_rows = recipes[cls.n_rows_noise :]
      return {
          sqlite_validators.ROW_OBJECTS: target_rows,
          sqlite_validators.NOISE_ROW_OBJECTS: noise_rows,
      }
    else:
      return {
          sqlite_validators.ROW_OBJECTS: recipes,
      }


class RecipeDeleteSingleRecipe(_RecipeDeleteMultipleRecipes):
  """Delete single recipe in Broccoli Recipe App without noise."""

  complexity = 1
  n_rows = 1
  n_rows_noise = 0


class RecipeDeleteSingleWithRecipeWithNoise(_RecipeDeleteMultipleRecipes):
  """Delete single recipe in Broccoli Recipe App with noise."""

  complexity = 2
  n_rows = 1
  n_rows_noise = 29


class RecipeDeleteMultipleRecipes(_RecipeDeleteMultipleRecipes):
  """Delete multiple recipes in Broccoli Recipe App."""

  complexity = 2.4
  n_rows = 3
  n_rows_noise = 0


class RecipeDeleteMultipleRecipesWithNoise(_RecipeDeleteMultipleRecipes):
  """Delete multiple recipes in Broccoli Recipe App with noise."""

  complexity = 3.4
  n_rows = 3
  n_rows_noise = 29


class RecipeDeleteMultipleRecipesWithConstraint(_RecipeDeleteMultipleRecipes):
  """Delete multiple recipes in Broccoli Recipe App based on ingredient."""

  complexity = 4
  n_rows = 3
  n_rows_noise = 29

  @property
  def goal(self) -> str:
    ingredient = self.params['ingredient']
    return (
        f'Delete the recipes from Broccoli app that use {ingredient} in the'
        ' directions.'
    )

  def _validate_initial_state(
      self, before: list[sqlite_schema_utils.RowType]
  ) -> None:
    del before

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for a remove recipe task."""
    ingredient = random.choice(_COMMON_INGREDIENTS)
    noise = sqlite_schema_utils.get_random_items(
        cls.n_rows_noise,
        _generate_random_recipe,
        replacement=False,
        filter_fn=lambda r: ingredient not in r.directions.lower(),
    )
    targets = []
    n_rows = cls.n_rows
    while n_rows > 0:
      try:
        targets = sqlite_schema_utils.get_random_items(
            n_rows,
            _generate_random_recipe,
            replacement=False,
            filter_fn=lambda r: ingredient in r.directions.lower(),
        )
        break
      except ValueError:
        n_rows -= 1
    return {
        sqlite_validators.ROW_OBJECTS: targets,
        sqlite_validators.NOISE_ROW_OBJECTS: noise,
        'ingredient': ingredient,
    }
```

### `derived/official_task_source.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/androidworld_official_task_metadata_116.json`

```json
{
  "base_class_name": "_RecipeDeleteMultipleRecipes",
  "base_module": "android_world.task_evals.single.recipe",
  "base_source_file": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py",
  "case_unit_id": "RecipeDeleteMultipleRecipesWithConstraint",
  "class_name": "RecipeDeleteMultipleRecipesWithConstraint",
  "difficulty": "hard",
  "module": "android_world.task_evals.single.recipe",
  "optimal_steps": "20",
  "selection_order_key": "5b07fb9a2346c22f49902bb4f273cf4d06eed98e8b1efefe392baca922fb3e13",
  "selection_rank": 42,
  "source_file": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py",
  "tags": [
    "screen_reading",
    "repetition",
    "parameterized"
  ],
  "task_id": "RecipeDeleteMultipleRecipesWithConstraint",
  "task_name": "RecipeDeleteMultipleRecipesWithConstraint",
  "task_template": "Delete the recipes from Broccoli app that use {ingredient} in the directions.",
  "official_files": [
    {
      "archive_path": "official/install/android_world/task_metadata.json",
      "sha256": "fd3cf23ebb26e461a961dd60ff3f011d7e6ec78c992c10babbbdb86f9dd591e1",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json"
    },
    {
      "archive_path": "official/install/android_world/registry.py",
      "sha256": "47380849f428b231747365ac8ba50a83212cdc34180ab6376ff49e90b93af12b",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/task_eval.py",
      "sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py"
    },
    {
      "archive_path": "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py",
      "sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py"
    }
  ],
  "packet_files": [
    "official/install/android_world/task_metadata.json",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py",
    "derived/official_task_source.json"
  ]
}
```
