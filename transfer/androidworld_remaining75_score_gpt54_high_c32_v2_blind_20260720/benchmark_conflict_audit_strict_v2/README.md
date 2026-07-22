# AndroidWorld Remaining-75 Strict Conflict Re-audit

## Outcome

The prior 36 conflict flags (12 cases x 3 agents) are retracted. Under the strict record-level standard, this re-audit confirms 0 benchmark conflicts in the previously flagged set.

The pinned official source does contain 12 stale or inconsistent `task_metadata.json` prompt entries. Those are benchmark-owned metadata defects, but the executable runner sends `task.goal` to the agent and the task evaluator checks the same instantiated task parameters. The metadata prompt is not used to run or score these records.

## Root Cause

The prior audit was our code's false positive: it treated a manually enumerated `metadata_conflicts` field as dispositive and set `confirmed = bool(material_conflicts)`. It did not independently establish a task/target/evaluator/reward mismatch. In addition, `native_evaluator_output.json::goal` is written by our adapter from the same `run_result['goal']`; equality with `task_context.json::goal` is a binding check, not independent evaluator-target evidence.

## Case Review

| Case | Strict conflict | Benchmark issue | Direct finding |
|---|---:|---|---|
| `MarkorAddNoteHeader` | No | Metadata defect only | The dispatched goal includes header insertion and rename; is_successful checks removal of original_name, existence of new_name, and the exact requested content on the same task params. |
| `MarkorChangeNoteContent` | No | Metadata defect only | The dispatched goal includes content replacement and rename; is_successful checks the same original_name, new_name, and updated_content params. |
| `MarkorEditNote` | No | Metadata defect only | The actual record dispatches its selected edit_type (replace in these three records), and is_successful branches on that same edit_type and target file. |
| `NotesRecipeIngredientCount` | No | Metadata defect only | The agent-visible proto prompt and STRING_MATCH expected ingredient_quantity are constructed from the same task proto and params. |
| `OsmAndTrack` | No | Metadata defect only | The runtime goal renders params['waypoints']; initialize_task resolves those same waypoints and is_successful checks them in order in a saved GPX track. |
| `SportsTrackerActivitiesCountForWeek` | No | Metadata defect only | The executable prompt, relevant-state date window, exclusions, and COUNT/NUMBER_MATCH target are defined in one task proto and evaluated from that instantiated proto. |
| `SportsTrackerActivitiesOnDate` | No | Metadata defect only | This is terminology drift, not target drift: task construction writes the same category value to both the category and activity_type fields, and the evaluator returns that value. |
| `SportsTrackerLongestDistanceActivity` | No | Metadata defect only | The executable prompt, Monday-Sunday target construction, total_distance target, and NUMBER_MATCH tolerance are defined and evaluated from the same instantiated task proto. |
| `SportsTrackerTotalDistanceForCategoryOverInterval` | No | Metadata defect only | The executable prompt, interval/category state construction, and SUM(total_distance) NUMBER_MATCH target are defined and evaluated from the same instantiated task proto. |
| `SportsTrackerTotalDurationForCategoryThisWeek` | No | Metadata defect only | The executable prompt, Monday-Sunday target construction, and SUM(duration) NUMBER_MATCH target are defined and evaluated from the same instantiated task proto. |
| `TasksDueNextWeek` | No | Metadata defect only | The executable prompt, next-week task state, exclusions, and COUNT/NUMBER_MATCH target are defined and evaluated from the same instantiated task proto. |
| `VlcCreateTwoPlaylists` | No | Metadata defect only | The runtime goal uses files1 and files2 correctly; __init__ creates two evaluators from those same params and is_successful averages their binary playlist checks, so the runner's >0.5 threshold requires both. |

## Scoring Impact

All 225 packaged checklists match their frozen canonical checklist hashes. None of the 12 reviewed checklists cites `task_metadata.json`, and no final score/reasoning artifact mentions the prior conflict markers. The evidence scores therefore are not shown to be invalidated by this audit-code error.

This report does not claim that all possible AndroidWorld benchmark defects are absent. It retracts the previously asserted 36 conflicts after a direct re-audit of exactly those records.
