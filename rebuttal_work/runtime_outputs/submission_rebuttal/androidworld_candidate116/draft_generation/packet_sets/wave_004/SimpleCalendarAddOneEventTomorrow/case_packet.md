# AndroidWorld Fresh Draft Packet

## Fresh Generation Control

- domain: `androidworld`
- case_unit_id: `SimpleCalendarAddOneEventTomorrow`
- task_id: `SimpleCalendarAddOneEventTomorrow`
- selection_rank: `9`
- Every old draft is superseded and unavailable. Derive the checklist from source.
- The prior issue statements below are untrusted warnings, never source facts, support targets, or run evidence.

```json
{
  "fresh_generation": true,
  "prior_rejected_draft_issue_count": 1,
  "prior_rejected_draft_issues": [
    {
      "check": "manual_semantic_audit",
      "description": "Exact title/description and UI provenance are present, but one after-only row is not required to carry the full target tuple.",
      "issue_id": "stronger_missing_same_new_row_binding__manual_audit_b__001__6b016164ef0a",
      "required_fix": "Correct the audited semantic defect: Exact title/description and UI provenance are present, but one after-only row is not required to carry the full target tuple.",
      "severity": "error",
      "source_kind": "manual_audit_b"
    }
  ],
  "superseded_draft_content_available_to_model": false
}
```

## Authoritative Full Case Packet (verbatim; sole semantic authority)

# Case Packet

## Case Metadata

- domain: `androidworld`
- case_unit_id: `SimpleCalendarAddOneEventTomorrow`
- task_id: `SimpleCalendarAddOneEventTomorrow`

## Source Inventory

- `official/install/android_world/task_metadata.json`
- `official/install/android_world/registry.py`
- `official/install/android_world/task_evals/task_eval.py`
- `official/install/android_world/task_evals/single/calendar/calendar.py`
- `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py`
- `official/install/android_world/task_evals/common_validators/sqlite_validators.py`
- `official/install/android_world/suite_utils.py`
- `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/state_pb2.py`
- `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/task_pb2.py`
- `official/install/android_world/env/__init__.py`
- `official/install/android_world/env/actuation.py`
- `official/install/android_world/env/adb_utils.py`
- `official/install/android_world/env/android_world_controller.py`
- `official/install/android_world/env/device_constants.py`
- `official/install/android_world/env/interface.py`
- `official/install/android_world/env/json_action.py`
- `official/install/android_world/env/representation_utils.py`
- `official/install/android_world/env/setup_device/__init__.py`
- `official/install/android_world/env/setup_device/apps.py`
- `official/install/android_world/env/setup_device/setup.py`
- `official/install/android_world/env/tools.py`
- `official/install/android_world/task_evals/__init__.py`
- `official/install/android_world/task_evals/common_validators/__init__.py`
- `official/install/android_world/task_evals/information_retrieval/__init__.py`
- `official/install/android_world/task_evals/information_retrieval/datetime_utils.py`
- `official/install/android_world/task_evals/information_retrieval/joplin_app_utils.py`
- `official/install/android_world/task_evals/information_retrieval/proto/__init__.py`
- `official/install/android_world/task_evals/information_retrieval/proto/state.proto`
- `official/install/android_world/task_evals/information_retrieval/proto/task.proto`
- `official/install/android_world/task_evals/information_retrieval/proto_utils.py`
- `official/install/android_world/task_evals/single/calendar/__init__.py`
- `official/install/android_world/task_evals/single/calendar/calendar_evaluators.py`
- `official/install/android_world/task_evals/single/calendar/calendar_utils.py`
- `official/install/android_world/task_evals/single/calendar/events_generator.py`
- `official/install/android_world/task_evals/utils/__init__.py`
- `official/install/android_world/task_evals/utils/sqlite_schema_utils.py`
- `official/install/android_world/task_evals/utils/sqlite_utils.py`
- `official/install/android_world/utils/__init__.py`
- `official/install/android_world/utils/app_snapshot.py`
- `official/install/android_world/utils/contacts_utils.py`
- `official/install/android_world/utils/datetime_utils.py`
- `official/install/android_world/utils/file_utils.py`
- `official/install/android_world/utils/fuzzy_match_lib.py`
- `derived/selected_task_source.json`
- `derived/source_closure.json`
- `derived/canonical_task_semantics.json`

## Packet Source Files

### `official/install/android_world/task_metadata.json`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json`

```json
[
  {
    "task_name": "AudioRecorderRecordAudio",
    "task_template": "Record an audio clip using Audio Recorder app and save it.",
    "difficulty": "easy",
    "tags": ["requires_setup"],
    "optimal_steps": "6"
  },
  {
    "task_name": "AudioRecorderRecordAudioWithFileName",
    "task_template": "Record an audio clip and save it with name \"{file_name}\" using Audio Recorder app.",
    "difficulty": "easy",
    "tags": ["data_entry", "complex_ui_understanding", "parameterized"],
    "optimal_steps": "10"
  },
  {
    "task_name": "BrowserDraw",
    "task_template": "Open the file task.html in Downloads in the file manager; when prompted open it with Chrome. Then create a drawing using the three colors shown at the top and hit submit.",
    "difficulty": "easy",
    "tags": ["game_playing", "parameterized"],
    "optimal_steps": "5"
  },
  {
    "task_name": "BrowserMaze",
    "task_template": "Open the file task.html in Downloads in the file manager; when prompted open it with Chrome. Then navigate the X to the bottom-right cell, by using the direction buttons.",
    "difficulty": "easy",
    "tags": [
      "game_playing",
      "multi_app",
      "complex_ui_understanding",
      "memorization",
      "parameterized"
    ],
    "optimal_steps": "9"
  },
  {
    "task_name": "BrowserMultiply",
    "task_template": "Open the file task.html in Downloads in the file manager; when prompted open it with Chrome. Then click the button 5 times, remember the numbers displayed, and enter their product in the form.",
    "difficulty": "hard",
    "tags": ["math_counting", "memorization", "screen_reading"],
    "optimal_steps": "11"
  },
  {
    "task_name": "CameraTakePhoto",
    "task_template": "Take one photo.",
    "difficulty": "easy",
    "tags": [""],
    "optimal_steps": "2"
  },
  {
    "task_name": "CameraTakeVideo",
    "task_template": "Take one video.",
    "difficulty": "medium",
    "tags": [""],
    "optimal_steps": "3"
  },
  {
    "task_name": "ClockStopWatchPausedVerify",
    "task_template": "Pause the stopwatch.",
    "difficulty": "easy",
    "tags": ["verification"],
    "optimal_steps": "1"
  },
  {
    "task_name": "ClockStopWatchRunning",
    "task_template": "Run the stopwatch.",
    "difficulty": "easy",
    "tags": [""],
    "optimal_steps": "3"
  },
  {
    "task_name": "ClockTimerEntry",
    "task_template": "Create a timer with {hours} hours, {minutes} minutes, and {seconds} seconds. Do not start the timer.",
    "difficulty": "easy",
    "tags": ["data_entry", "parameterized"],
    "optimal_steps": "3"
  },
  {
    "task_name": "ContactsAddContact",
    "task_template": "Create a new contact for {name}. Their number is {number}.",
    "difficulty": "easy",
    "tags": ["data_entry", "parameterized"],
    "optimal_steps": "5"
  },
  {
    "task_name": "ContactsNewContactDraft",
    "task_template": "Go to the new contact screen and enter the following details: First Name: {first}, Last Name: {last}, Phone: {phone}, Phone Label: {phone_label}. Do NOT hit save.",
    "difficulty": "easy",
    "tags": ["screen_reading", "data_entry"],
    "optimal_steps": "6"
  },
  {
    "task_name": "ExpenseAddMultiple",
    "task_template": "Add the following expenses into the arduia pro expense: {expenses}",
    "difficulty": "medium",
    "tags": ["data_entry", "parameterized"],
    "optimal_steps": "20"
  },
  {
    "task_name": "ExpenseAddMultipleFromGallery",
    "task_template": "Add the expenses from expenses.jpg in Simple Gallery Pro to pro expense.",
    "difficulty": "hard",
    "tags": [
      "multi_app",
      "screen_reading",
      "data_entry",
      "information_retrieval",
      "parameterized"
    ],
    "optimal_steps": "10"
  },
  {
    "task_name": "ExpenseAddMultipleFromMarkor",
    "task_template": "Go through the transactions in my_expenses.txt in Markor. Log the reimbursable transactions in the arduia pro expense.",
    "difficulty": "hard",
    "tags": [
      "transcription",
      "repetition",
      "multi_app",
      "data_entry",
      "memorization",
      "parameterized"
    ],
    "optimal_steps": "15"
  },
  {
    "task_name": "ExpenseAddSingle",
    "task_template": "Add the following expenses into the arduia pro expense: {expense}",
    "difficulty": "easy",
    "tags": ["parameterized", "data_entry", "search"],
    "optimal_steps": "6"
  },
  {
    "task_name": "ExpenseDeleteDuplicates",
    "task_template": "Delete all but one of any expenses in arduia pro expense that are exact duplicates, ensuring at least one instance of each unique expense remains.",
    "difficulty": "medium",
    "tags": ["data_edit", "parameterized"],
    "optimal_steps": "6"
  },
  {
    "task_name": "ExpenseDeleteDuplicates2",
    "task_template": "Delete all but one of any expenses in arduia pro expense that are exact duplicates, ensuring at least one instance of each unique expense remains.",
    "difficulty": "medium",
    "tags": ["data_edit", "requires_setup", "parameterized"],
    "optimal_steps": "9"
  },
  {
    "task_name": "ExpenseDeleteMultiple",
    "task_template": "Delete the following expenses from arduia pro expense: {expenses}.",
    "difficulty": "easy",
    "tags": ["data_edit", "parameterized"],
    "optimal_steps": "10"
  },
  {
    "task_name": "ExpenseDeleteMultiple2",
    "task_template": "Delete the following expenses from arduia pro expense: {expenses}.",
    "difficulty": "hard",
    "tags": ["screen_reading", "parameterized"],
    "optimal_steps": "17"
  },
  {
    "task_name": "ExpenseDeleteSingle",
    "task_template": "Delete the following expenses from arduia pro expense: {expense}.",
    "difficulty": "easy",
    "tags": ["screen_reading", "parameterized"],
    "optimal_steps": "3"
  },
  {
    "task_name": "FilesDeleteFile",
    "task_template": "Delete the file {file_name} from the Android filesystem located in the {subfolder} folder within the sdk_gphone_x86_64 storage area.",
    "difficulty": "medium",
    "tags": ["data_edit", "parameterized"],
    "optimal_steps": "4"
  },
  {
    "task_name": "FilesMoveFile",
    "task_template": "Move the file {file_name} from {source_folder} within the sdk_gphone_x86_64 storage area to the {destination_folder} within the same sdk_gphone_x86_64 storage area in the Android filesystem.",
    "difficulty": "medium",
    "tags": ["search", "screen_reading", "parameterized"],
    "optimal_steps": "10"
  },
  {
    "task_name": "MarkorAddNoteHeader",
    "task_template": "Update the Markor note {file_name} by adding the following text, along with a new blank line before the existing content: \"{header}\".",
    "difficulty": "medium",
    "tags": ["data_entry", "parameterized"],
    "optimal_steps": "6"
  },
  {
    "task_name": "MarkorChangeNoteContent",
    "task_template": "Update the content of {file_name} to \"{updated_content}\" in Markor.",
    "difficulty": "medium",
    "tags": ["data_entry", "requires_setup", "parameterized"],
    "optimal_steps": "5"
  },
  {
    "task_name": "MarkorCreateFolder",
    "task_template": "Create a new folder in Markor named {folder_name}.",
    "difficulty": "easy",
    "tags": ["data_entry", "parameterized"],
    "optimal_steps": "4"
  },
  {
    "task_name": "MarkorCreateNote",
    "task_template": "Create a new note in Markor named {file_name} with the following text: {text}",
    "difficulty": "medium",
    "tags": ["data_entry", "parameterized"],
    "optimal_steps": "8"
  },
  {
    "task_name": "MarkorCreateNoteAndSms",
    "task_template": "Create a new note in Markor named {file_name} with the following text: {text}. Share the entire content of the note with the phone number {number} via SMS using Simple SMS Messenger",
    "difficulty": "hard",
    "tags": ["multi_app", "data_entry", "parameterized"],
    "optimal_steps": "9"
  },
  {
    "task_name": "MarkorCreateNoteFromClipboard",
    "task_template": "Create a note in Markor named {file_name}. Perform a paste operation in the note and save the note.",
    "difficulty": "medium",
    "tags": ["data_entry", "parameterized"],
    "optimal_steps": "7"
  },
  {
    "task_name": "MarkorDeleteAllNotes",
    "task_template": "Delete all my notes in Markor.",
    "difficulty": "easy",
    "tags": ["data_edit", "repetition", "parameterized"],
    "optimal_steps": "7"
  },
  {
    "task_name": "MarkorDeleteNewestNote",
    "task_template": "Delete the newest note in Markor.",
    "difficulty": "easy",
    "tags": ["data_edit", "parameterized"],
    "optimal_steps": "4"
  },
  {
    "task_name": "MarkorDeleteNote",
    "task_template": "Delete the note in Markor named {file_name}.",
    "difficulty": "easy",
    "tags": ["data_edit", "requires_setup", "parameterized"],
    "optimal_steps": "5"
  },
  {
    "task_name": "MarkorEditNote",
    "task_template": "Edit {file_name} in Markor. Add to the top of the note {header}",
    "difficulty": "easy",
    "tags": ["data_edit", "transcription", "parameterized"],
    "optimal_steps": "4"
  },
  {
    "task_name": "MarkorMergeNotes",
    "task_template": "Merge the contents of Markor notes {file1_name}, {file2_name} and {file3_name} (in the same order) into a new Markor note named {new_file_name} and save it. Add a new line between the content of each note.",
    "difficulty": "hard",
    "tags": ["data_edit", "data_entry", "parameterized"],
    "optimal_steps": "39"
  },
  {
    "task_name": "MarkorMoveNote",
    "task_template": "In Markor, move the note {file_name} from {source_folder} to {destination_folder}.",
    "difficulty": "medium",
    "tags": ["parameterized", "complex_ui_understanding"],
    "optimal_steps": "7"
  },
  {
    "task_name": "MarkorTranscribeReceipt",
    "task_template": "Create a file in Markor, called receipt.md with the transactions from the receipt.png. Use Simple Gallery to view the receipt. Please enter transactions in csv format including the header \"Date, Item, Amount\".",
    "difficulty": "medium",
    "tags": [
      "transcription",
      "data_entry",
      "multi_app",
      "screen_reading",
      "memorization",
      "parameterized"
    ],
    "optimal_steps": "9"
  },
  {
    "task_name": "MarkorTranscribeVideo",
    "task_template": "Transcribe the contents of video {video_name} by watching it in VLC player (located in Download) and writing the sequence of strings shown on each frame to the text file {file_name} in Markor as a comma separated list. For example, if the first frame shows the text \"edna\" and the second frame shows the text \"pineapple\", then the text file should contains only the following text: \"edna, pineapple\".",
    "difficulty": "hard",
    "tags": [
      "multi_app",
      "transcription",
      "requires_setup",
      "memorization",
      "screen_reading",
      "parameterized"
    ],
    "optimal_steps": "10"
  },
  {
    "task_name": "NotesIsTodo",
    "task_template": "Is the note titled '{title}' in the Joplin app marked as a todo item? Respond with either 'True' if it is a todo or 'False' if not.",
    "difficulty": "easy",
    "tags": ["information_retrieval", "parameterized"],
    "optimal_steps": "2"
  },
  {
    "task_name": "NotesMeetingAttendeeCount",
    "task_template": "How many attendees were present in the meeting titled '{title}' in the Joplin app? Express your answer as just a single number.",
    "difficulty": "easy",
    "tags": ["search", "parameterized"],
    "optimal_steps": "3"
  },
  {
    "task_name": "NotesRecipeIngredientCount",
    "task_template": "What quantity of {ingredient} do I need for the recipe '{title}' in the Joplin app? Express your answer in the format <amount> <unit> without using abbreviations.",
    "difficulty": "easy",
    "tags": ["search", "parameterized"],
    "optimal_steps": "2"
  },
  {
    "task_name": "NotesTodoItemCount",
    "task_template": "How many to-dos do I have in the '{folder}' folder in the Joplin app? Express your answer as just a single number.",
    "difficulty": "medium",
    "tags": ["information_retrieval", "math_counting", "parameterized"],
    "optimal_steps": "5"
  },
  {
    "task_name": "OpenAppTaskEval",
    "task_template": "Open the {app_name} app. Clear any pop-ups that may appear by granting all permissions that are required.",
    "difficulty": "easy",
    "tags": ["parameterized"],
    "optimal_steps": "2"
  },
  {
    "task_name": "OsmAndFavorite",
    "task_template": "Add a favorite location marker for {location} in the OsmAnd maps app.",
    "difficulty": "medium",
    "tags": ["search", "complex_ui_understanding", "parameterized"],
    "optimal_steps": "6"
  },
  {
    "task_name": "OsmAndMarker",
    "task_template": "Add a location marker for {location} in the OsmAnd maps app.",
    "difficulty": "hard",
    "tags": ["complex_ui_understanding", "search", "parameterized"],
    "optimal_steps": "10"
  },
  {
    "task_name": "OsmAndTrack",
    "task_template": "Save a track with waypoints Ruggell, Liechtenstein, Bendern, Liechtenstein in the OsmAnd maps app in the same order as listed.",
    "difficulty": "hard",
    "tags": [
      "complex_ui_understanding",
      "search",
      "data_entry",
      "repetition",
      "parameterized"
    ],
    "optimal_steps": "60"
  },
  {
    "task_name": "RecipeAddMultipleRecipes",
    "task_template": "Add the following recipes into the Broccoli app: {recipes}",
    "difficulty": "medium",
    "tags": ["data_entry", "parameterized"],
    "optimal_steps": "34"
  },
  {
    "task_name": "RecipeAddMultipleRecipesFromImage",
    "task_template": "Add the recipes from recipes.jpg in Simple Gallery Pro to the Broccoli recipe app.",
    "difficulty": "hard",
    "tags": [
      "transcription",
      "screen_reading",
      "data_entry",
      "complex_ui_understanding",
      "parameterized"
    ],
    "optimal_steps": "13"
  },
  {
    "task_name": "RecipeAddMultipleRecipesFromMarkor",
    "task_template": "Add the recipes from recipes.txt in Markor to the Broccoli recipe app.",
    "difficulty": "hard",
    "tags": [
      "data_entry",
      "multi_app",
      "screen_reading",
      "memorization",
      "parameterized"
    ],
    "optimal_steps": "24"
  },
  {
    "task_name": "RecipeAddMultipleRecipesFromMarkor2",
    "task_template": "Add the recipes from recipes.txt in Markor that take {prep_time} to prepare into the Broccoli recipe app.",
    "difficulty": "hard",
    "tags": [
      "parameterized",
      "screen_reading",
      "complex_ui_understanding",
      "repetition",
      "multi_app",
      "data_entry",
      "information_retrieval"
    ],
    "optimal_steps": "26"
  },
  {
    "task_name": "RecipeAddSingleRecipe",
    "task_template": "Add the following recipes into the Broccoli app:\n{recipe}",
    "difficulty": "easy",
    "tags": ["data_entry", "parameterized"],
    "optimal_steps": "12"
  },
  {
    "task_name": "RecipeDeleteDuplicateRecipes",
    "task_template": "Delete all but one of any recipes in the Broccoli app that are exact duplicates, ensuring at least one instance of each unique recipe remains",
    "difficulty": "easy",
    "tags": [
      "search",
      "data_edit",
      "screen_reading",
      "repetition",
      "parameterized"
    ],
    "optimal_steps": "4"
  },
  {
    "task_name": "RecipeDeleteDuplicateRecipes2",
    "task_template": "Delete all but one of any recipes in the Broccoli app that are exact duplicates, ensuring at least one instance of each unique recipe remains",
    "difficulty": "medium",
    "tags": ["repetition", "data_edit", "parameterized"],
    "optimal_steps": "11"
  },
  {
    "task_name": "RecipeDeleteDuplicateRecipes3",
    "task_template": "Delete all but one of any recipes in the Broccoli app that are exact duplicates, ensuring at least one instance of each unique recipe remains",
    "difficulty": "medium",
    "tags": ["data_edit", "parameterized"],
    "optimal_steps": "16"
  },
  {
    "task_name": "RecipeDeleteMultipleRecipes",
    "task_template": "Delete the following recipes from Broccoli app: {titles}.",
    "difficulty": "easy",
    "tags": ["data_edit", "parameterized"],
    "optimal_steps": "12"
  },
  {
    "task_name": "RecipeDeleteMultipleRecipesWithConstraint",
    "task_template": "Delete the recipes from Broccoli app that use {ingredient} in the directions.",
    "difficulty": "hard",
    "tags": ["screen_reading", "repetition", "parameterized"],
    "optimal_steps": "20"
  },
  {
    "task_name": "RecipeDeleteMultipleRecipesWithNoise",
    "task_template": "Delete the following recipes from Broccoli app: {titles}.",
    "difficulty": "medium",
    "tags": [
      "parameterized",
      "search",
      "complex_ui_understanding",
      "repetition"
    ],
    "optimal_steps": "17"
  },
  {
    "task_name": "RecipeDeleteSingleRecipe",
    "task_template": "Delete the following recipes from Broccoli app: {titles}.",
    "difficulty": "easy",
    "tags": ["data_edit", "search", "parameterized"],
    "optimal_steps": "5"
  },
  {
    "task_name": "RecipeDeleteSingleWithRecipeWithNoise",
    "task_template": "Delete the following recipes from Broccoli app: {titles}.",
    "difficulty": "easy",
    "tags": ["search", "screen_reading", "data_edit", "parameterized"],
    "optimal_steps": "10"
  },
  {
    "task_name": "RetroCreatePlaylist",
    "task_template": "Create a playlist in Retro Music titled \"{playlist_name}\" with the following songs, in order: {names}",
    "difficulty": "medium",
    "tags": ["data_entry", "repetition", "parameterized"],
    "optimal_steps": "12"
  },
  {
    "task_name": "RetroPlayingQueue",
    "task_template": "Add the following songs, in order, {names} to my playing queue in Retro music.",
    "difficulty": "easy",
    "tags": ["parameterized"],
    "optimal_steps": "16"
  },
  {
    "task_name": "RetroPlaylistDuration",
    "task_template": "Create a playlist in Retro Music titled \"{playlist_name}\" with a duration between 45 and 50 minutes using the provided songs.",
    "difficulty": "medium",
    "tags": [
      "math_counting",
      "complex_ui_understanding",
      "repetition",
      "parameterized"
    ],
    "optimal_steps": "15"
  },
  {
    "task_name": "RetroSavePlaylist",
    "task_template": "Create a playlist in Retro Music titled \"{playlist_name}\" with the following songs, in order: {names}. Then export the playlist to the Downloads directory on the device.",
    "difficulty": "hard",
    "tags": ["search", "repetition", "parameterized"],
    "optimal_steps": "25"
  },
  {
    "task_name": "SaveCopyOfReceiptTaskEval",
    "task_template": "Copy {file_name} in DCIM and save a copy with the same name in Download",
    "difficulty": "hard",
    "tags": ["parameterized", "complex_ui_understanding"],
    "optimal_steps": "8"
  },
  {
    "task_name": "SimpleCalendarAddOneEvent",
    "task_template": "In Simple Calendar Pro, create a calendar event on {year}-{month}-{day} at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins.",
    "difficulty": "hard",
    "tags": ["data_entry", "complex_ui_understanding", "parameterized"],
    "optimal_steps": "17"
  },
  {
    "task_name": "SimpleCalendarAddOneEventInTwoWeeks",
    "task_template": "In Simple Calendar Pro, create a calendar event in two weeks from today at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins.",
    "difficulty": "medium",
    "tags": ["data_entry", "math_counting", "parameterized"],
    "optimal_steps": "10"
  },
  {
    "task_name": "SimpleCalendarAddOneEventRelativeDay",
    "task_template": "In Simple Calendar Pro, create a calendar event for this {day_of_week} at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins.",
    "difficulty": "easy",
    "tags": ["data_entry", "parameterized"],
    "optimal_steps": "17"
  },
  {
    "task_name": "SimpleCalendarAddOneEventTomorrow",
    "task_template": "In Simple Calendar Pro, create a calendar event for tomorrow at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins.",
    "difficulty": "easy",
    "tags": ["data_entry", "parameterized"],
    "optimal_steps": "13"
  },
  {
    "task_name": "SimpleCalendarAddRepeatingEvent",
    "task_template": "In Simple Calendar Pro, create a recurring calendar event titled '{event_title}' starting on {year}-{month}-{day} at {hour}h. The event recurs {repeat_rule}, forever, and lasts for {duration_mins} minutes each occurrence. The event description should be '{event_description}'.",
    "difficulty": "easy",
    "tags": ["data_entry", "complex_ui_understanding", "parameterized"],
    "optimal_steps": "14"
  },
  {
    "task_name": "SimpleCalendarAnyEventsOnDate",
    "task_template": "Do I have any events {date} in Simple Calendar Pro? Answer with the titles only. If there are multiples titles, format your answer in a comma separated list.",
    "difficulty": "easy",
    "tags": ["information_retrieval", "parameterized"],
    "optimal_steps": "4"
  },
  {
    "task_name": "SimpleCalendarDeleteEvents",
    "task_template": "In Simple Calendar Pro, delete all the calendar events on {year}-{month}-{day}",
    "difficulty": "easy",
    "tags": ["parameterized", "data_edit"],
    "optimal_steps": "7"
  },
  {
    "task_name": "SimpleCalendarDeleteEventsOnRelativeDay",
    "task_template": "In Simple Calendar Pro, delete all events scheduled for this {day_of_week}.",
    "difficulty": "medium",
    "tags": ["data_edit", "parameterized"],
    "optimal_steps": "6"
  },
  {
    "task_name": "SimpleCalendarDeleteOneEvent",
    "task_template": "In Simple Calendar Pro, delete the calendar event on {year}-{month}-{day} at {hour}h with the title '{event_title}'",
    "difficulty": "easy",
    "tags": ["data_edit", "complex_ui_understanding", "parameterized"],
    "optimal_steps": "6"
  },
  {
    "task_name": "SimpleCalendarEventOnDateAtTime",
    "task_template": "What is on my schedule for {date} at {time} in Simple Calendar Pro? Answer with the titles only. If there are multiples titles, format your answer in a comma separated list.",
    "difficulty": "medium",
    "tags": ["information_retrieval", "parameterized"],
    "optimal_steps": "3"
  },
  {
    "task_name": "SimpleCalendarEventsInNextWeek",
    "task_template": "What events do I have in the next week in Simple Calendar Pro? Answer with the titles only. If there are multiples titles, format your answer in a comma separated list.",
    "difficulty": "easy",
    "tags": ["data_entry", "parameterized"],
    "optimal_steps": "3"
  },
  {
    "task_name": "SimpleCalendarEventsInTimeRange",
    "task_template": "Do I have any events between {start_time} and 8pm {date} in Simple Calendar Pro? Answer with the titles only. If there are multiples titles, format your answer in a comma separated list.",
    "difficulty": "easy",
    "tags": [
      "complex_ui_understanding",
      "screen_reading",
      "search",
      "transcription",
      "information_retrieval",
      "parameterized"
    ],
    "optimal_steps": "2"
  },
  {
    "task_name": "SimpleCalendarEventsOnDate",
    "task_template": "What events do I have {date} in Simple Calendar Pro? Answer with the titles only. If there are multiple titles, format your answer as a comma separated list.",
    "difficulty": "medium",
    "tags": ["information_retrieval", "parameterized"],
    "optimal_steps": "4"
  },
  {
    "task_name": "SimpleCalendarFirstEventAfterStartTime",
    "task_template": "What is my first event after {time} {date} in Simple Calendar Pro? Answer with the titles only. If there are multiples titles, format your answer in a comma separated list.",
    "difficulty": "easy",
    "tags": ["parameterized", "screen_reading"],
    "optimal_steps": "2"
  },
  {
    "task_name": "SimpleCalendarLocationOfEvent",
    "task_template": "What is the location of my {title} event in Simple Calendar Pro? Answer with the location only.",
    "difficulty": "easy",
    "tags": ["search", "parameterized"],
    "optimal_steps": "4"
  },
  {
    "task_name": "SimpleCalendarNextEvent",
    "task_template": "What is my next upcoming event in Simple Calendar Pro? Answer with the title only. If there are multiples titles, format your answer in a comma separated list.",
    "difficulty": "easy",
    "tags": [
      "complex_ui_understanding",
      "screen_reading",
      "information_retrieval",
      "parameterized"
    ],
    "optimal_steps": "4"
  },
  {
    "task_name": "SimpleCalendarNextMeetingWithPerson",
    "task_template": "When is my next meeting with {person} in Simple Calendar Pro? Express your answer in the format <month name> <day> <year> <hour in 24-hour format>:<minutes>.",
    "difficulty": "medium",
    "tags": ["information_retrieval", "parameterized"],
    "optimal_steps": "5"
  },
  {
    "task_name": "SimpleDrawProCreateDrawing",
    "task_template": "Create a new drawing in Simple Draw Pro. Name it {file_name}. Save it in the Pictures folder within the sdk_gphone_x86_64 storage area.",
    "difficulty": "easy",
    "tags": ["data_entry", "parameterized"],
    "optimal_steps": "9"
  },
  {
    "task_name": "SimpleSmsReply",
    "task_template": "Reply to {number} with message: {message} in Simple SMS Messenger",
    "difficulty": "easy",
    "tags": ["search", "data_entry", "parameterized"],
    "optimal_steps": "4"
  },
  {
    "task_name": "SimpleSmsReplyMostRecent",
    "task_template": "Reply to the most recent text message using Simple SMS Messenger with message: {message}",
    "difficulty": "medium",
    "tags": ["parameterized"],
    "optimal_steps": "5"
  },
  {
    "task_name": "SimpleSmsResend",
    "task_template": "Resend the message I just sent to {name} in Simple SMS Messenger",
    "difficulty": "medium",
    "tags": ["parameterized"],
    "optimal_steps": "6"
  },
  {
    "task_name": "SimpleSmsSend",
    "task_template": "Send a text message using Simple SMS Messenger to {number} with message: {message}",
    "difficulty": "medium",
    "tags": ["parameterized"],
    "optimal_steps": "6"
  },
  {
    "task_name": "SimpleSmsSendClipboardContent",
    "task_template": "Send a message to {number} with the clipboard content in Simple SMS Messenger",
    "difficulty": "easy",
    "tags": ["data_entry", "parameterized"],
    "optimal_steps": "6"
  },
  {
    "task_name": "SimpleSmsSendReceivedAddress",
    "task_template": "Text the address of the event to {name1} that {name2} just sent me in Simple SMS Messenger",
    "difficulty": "medium",
    "tags": ["information_retrieval", "parameterized"],
    "optimal_steps": "9"
  },
  {
    "task_name": "SportsTrackerActivitiesCountForWeek",
    "task_template": "How many {category} activities did I do this week in the OpenTracks app? Express your answer as a single integer.",
    "difficulty": "easy",
    "tags": ["search", "requires_setup", "parameterized"],
    "optimal_steps": "3"
  },
  {
    "task_name": "SportsTrackerActivitiesOnDate",
    "task_template": "What activities did I do {date} in the OpenTracks app? Answer with the category only. If there are multiples categories, format your answer in a comma separated list.",
    "difficulty": "hard",
    "tags": [
      "search",
      "complex_ui_understanding",
      "screen_reading",
      "information_retrieval",
      "transcription",
      "parameterized"
    ],
    "optimal_steps": "10"
  },
  {
    "task_name": "SportsTrackerActivityDuration",
    "task_template": "How long was my {category} activity {date} in the OpenTracks app? Express your answer in minutes as a single integer.",
    "difficulty": "easy",
    "tags": ["information_retrieval", "parameterized"],
    "optimal_steps": "6"
  },
  {
    "task_name": "SportsTrackerLongestDistanceActivity",
    "task_template": "What was the longest distance covered in a {category} activity in the OpenTracks app this week? Express your answer in meters as a single integer.",
    "difficulty": "easy",
    "tags": [
      "parameterized",
      "screen_reading",
      "information_retrieval",
      "math_counting"
    ],
    "optimal_steps": "2"
  },
  {
    "task_name": "SportsTrackerTotalDistanceForCategoryOverInterval",
    "task_template": "What was the total distance covered for {category} activities in the OpenTracks app from {start_date} to {end_date}? Express your answer in meters as a single integer.",
    "difficulty": "hard",
    "tags": ["search", "parameterized", "math_counting"],
    "optimal_steps": "11"
  },
  {
    "task_name": "SportsTrackerTotalDurationForCategoryThisWeek",
    "task_template": "What was the total duration of {category} activities in the OpenTracks app this week? Express your answer in minutes as a single integer.",
    "difficulty": "hard",
    "tags": ["math_counting", "search", "parameterized"],
    "optimal_steps": "8"
  },
  {
    "task_name": "SystemBluetoothTurnOff",
    "task_template": "Turn bluetooth {on_or_off}.",
    "difficulty": "easy",
    "tags": [""],
    "optimal_steps": "2"
  },
  {
    "task_name": "SystemBluetoothTurnOffVerify",
    "task_template": "Turn bluetooth {on_or_off}.",
    "difficulty": "easy",
    "tags": ["verification"],
    "optimal_steps": "2"
  },
  {
    "task_name": "SystemBluetoothTurnOn",
    "task_template": "Turn bluetooth {on_or_off}.",
    "difficulty": "easy",
    "tags": ["screen_reading"],
    "optimal_steps": "2"
  },
  {
    "task_name": "SystemBluetoothTurnOnVerify",
    "task_template": "Turn bluetooth {on_or_off}.",
    "difficulty": "easy",
    "tags": ["verification"],
    "optimal_steps": "2"
  },
  {
    "task_name": "SystemBrightnessMax",
    "task_template": "Turn brightness to the {max_or_min} value.",
    "difficulty": "easy",
    "tags": [""],
    "optimal_steps": "3"
  },
  {
    "task_name": "SystemBrightnessMaxVerify",
    "task_template": "Turn brightness to the {max_or_min} value.",
    "difficulty": "easy",
    "tags": ["verification"],
    "optimal_steps": "2"
  },
  {
    "task_name": "SystemBrightnessMin",
    "task_template": "Turn brightness to the {max_or_min} value.",
    "difficulty": "easy",
    "tags": [""],
    "optimal_steps": "3"
  },
  {
    "task_name": "SystemBrightnessMinVerify",
    "task_template": "Turn brightness to the {max_or_min} value.",
    "difficulty": "easy",
    "tags": ["verification"],
    "optimal_steps": "3"
  },
  {
    "task_name": "SystemCopyToClipboard",
    "task_template": "Copy the following text to the clipboard: {clipboard_content}",
    "difficulty": "easy",
    "tags": ["data_entry", "parameterized"],
    "optimal_steps": "2"
  },
  {
    "task_name": "SystemWifiTurnOff",
    "task_template": "Turn wifi {on_or_off}.",
    "difficulty": "easy",
    "tags": ["screen_reading"],
    "optimal_steps": "3"
  },
  {
    "task_name": "SystemWifiTurnOffVerify",
    "task_template": "Turn wifi {on_or_off}.",
    "difficulty": "easy",
    "tags": ["verification"],
    "optimal_steps": "3"
  },
  {
    "task_name": "SystemWifiTurnOn",
    "task_template": "Turn wifi {on_or_off}.",
    "difficulty": "easy",
    "tags": ["screen_reading"],
    "optimal_steps": "3"
  },
  {
    "task_name": "SystemWifiTurnOnVerify",
    "task_template": "Turn wifi {on_or_off}.",
    "difficulty": "easy",
    "tags": ["verification"],
    "optimal_steps": "3"
  },
  {
    "task_name": "TasksCompletedTasksForDate",
    "task_template": "Which tasks have I completed for {date} in Tasks app? Answer with the titles only. If there are multiples titles, format your answer in a comma separated list.",
    "difficulty": "medium",
    "tags": ["information_retrieval", "search", "parameterized"],
    "optimal_steps": "5"
  },
  {
    "task_name": "TasksDueNextWeek",
    "task_template": "How many tasks do I have due next week in Tasks app? Express your answer as a single integer.",
    "difficulty": "medium",
    "tags": ["information_retrieval", "parameterized"],
    "optimal_steps": "6"
  },
  {
    "task_name": "TasksDueOnDate",
    "task_template": "What tasks do I have due {date} in Tasks app? Answer with the titles only. If there are multiples titles, format your answer in a comma separated list.",
    "difficulty": "easy",
    "tags": ["search", "parameterized"],
    "optimal_steps": "2"
  },
  {
    "task_name": "TasksHighPriorityTasks",
    "task_template": "What are my high priority tasks in Tasks app? Answer with the titles only. If there are multiples titles, format your answer in a comma separated list.",
    "difficulty": "medium",
    "tags": [
      "complex_ui_understanding",
      "search",
      "information_retrieval",
      "transcription",
      "parameterized"
    ],
    "optimal_steps": "2"
  },
  {
    "task_name": "TasksHighPriorityTasksDueOnDate",
    "task_template": "Which tasks with high priority are due {date} in the Tasks app? Answer with the title only. If there are multiples titles, format your answer in a comma separated list.",
    "difficulty": "medium",
    "tags": ["information_retrieval", "screen_reading", "parameterized"],
    "optimal_steps": "5"
  },
  {
    "task_name": "TasksIncompleteTasksOnDate",
    "task_template": "What incomplete tasks do I have still have to do by {date} in Tasks app? Answer with the titles only. If there are multiples titles, format your answer in a comma separated list.",
    "difficulty": "easy",
    "tags": ["parameterized", "screen_reading", "information_retrieval"],
    "optimal_steps": "2"
  },
  {
    "task_name": "TurnOffWifiAndTurnOnBluetooth",
    "task_template": "Turn off WiFi, then enable bluetooth",
    "difficulty": "medium",
    "tags": [""],
    "optimal_steps": "5"
  },
  {
    "task_name": "TurnOnWifiAndOpenApp",
    "task_template": "Turn on Wifi, then open the {app_name} app",
    "difficulty": "easy",
    "tags": ["parameterized"],
    "optimal_steps": "4"
  },
  {
    "task_name": "VlcCreatePlaylist",
    "task_template": "Create a playlist titled \"{playlist_name}\" with the following files in VLC (located in Internal Memory/VLCVideos), in order: {files}",
    "difficulty": "medium",
    "tags": ["data_edit", "repetition", "parameterized"],
    "optimal_steps": "14"
  },
  {
    "task_name": "VlcCreateTwoPlaylists",
    "task_template": "Create a playlist titled \"{playlist_name1}\" with the following files in VLC, in order: {files1}. And then, Create a playlist titled \"{playlist_name2}\" with the following files in VLC (located in Internal Memory/VLCVideos), in order: {files1}",
    "difficulty": "medium",
    "tags": ["data_entry", "requires_setup", "parameterized"],
    "optimal_steps": "24"
  }
]
```

### `official/install/android_world/registry.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Registers the task classes."""

import types
from typing import Any, Final

from android_world.task_evals import task_eval
from android_world.task_evals.composite import markor_sms
from android_world.task_evals.composite import system as system_composite
from android_world.task_evals.information_retrieval import information_retrieval
from android_world.task_evals.information_retrieval import information_retrieval_registry
from android_world.task_evals.miniwob import miniwob_registry
from android_world.task_evals.single import audio_recorder
from android_world.task_evals.single import browser
from android_world.task_evals.single import camera
from android_world.task_evals.single import clock
from android_world.task_evals.single import contacts
from android_world.task_evals.single import expense
from android_world.task_evals.single import files
from android_world.task_evals.single import markor
from android_world.task_evals.single import osmand
from android_world.task_evals.single import recipe
from android_world.task_evals.single import retro_music
from android_world.task_evals.single import simple_draw_pro
from android_world.task_evals.single import simple_gallery_pro
from android_world.task_evals.single import sms
from android_world.task_evals.single import system
from android_world.task_evals.single import vlc
from android_world.task_evals.single.calendar import calendar


def get_information_retrieval_task_path() -> None:
  return None


def get_families() -> list[str]:
  return [
      TaskRegistry.ANDROID_WORLD_FAMILY,
      TaskRegistry.ANDROID_FAMILY,
      TaskRegistry.MINIWOB_FAMILY,
      TaskRegistry.MINIWOB_FAMILY_SUBSET,
      TaskRegistry.INFORMATION_RETRIEVAL_FAMILY,
  ]


class TaskRegistry:
  """Registry of tasks."""

  # The AndroidWorld family.
  ANDROID_WORLD_FAMILY: Final[str] = 'android_world'  # Entire suite.
  ANDROID_FAMILY: Final[str] = 'android'  # Subset.
  INFORMATION_RETRIEVAL_FAMILY: Final[str] = 'information_retrieval'  # Subset.

  # The MiniWoB family.
  MINIWOB_FAMILY: Final[str] = 'miniwob'
  MINIWOB_FAMILY_SUBSET: Final[str] = 'miniwob_subset'

  # Task registries; they contain a mapping from each task name to its class,
  # to construct instances of a task.
  ANDROID_TASK_REGISTRY = {}
  INFORMATION_RETRIEVAL_TASK_REGISTRY = (
      information_retrieval_registry.InformationRetrievalRegistry[
          information_retrieval.InformationRetrieval
      ](filename=get_information_retrieval_task_path()).registry
  )

  MINIWOB_TASK_REGISTRY = miniwob_registry.TASK_REGISTRY

  def get_registry(self, family: str) -> Any:
    """Gets the task registry for the given family.

    Args:
      family: The family.

    Returns:
      Task registry.

    Raises:
      ValueError: If provided family doesn't exist.
    """
    if family == self.ANDROID_WORLD_FAMILY:
      return {
          **self.ANDROID_TASK_REGISTRY,
          **self.INFORMATION_RETRIEVAL_TASK_REGISTRY,
      }
    elif family == self.ANDROID_FAMILY:
      return self.ANDROID_TASK_REGISTRY
    elif family == self.MINIWOB_FAMILY:
      return self.MINIWOB_TASK_REGISTRY
    elif family == self.MINIWOB_FAMILY_SUBSET:
      return miniwob_registry.TASK_REGISTRY_SUBSET
    elif family == self.INFORMATION_RETRIEVAL_FAMILY:
      return self.INFORMATION_RETRIEVAL_TASK_REGISTRY
    else:
      raise ValueError(f'Unsupported family: {family}')

  _TASKS = (
      # keep-sorted start
      audio_recorder.AudioRecorderRecordAudio,
      audio_recorder.AudioRecorderRecordAudioWithFileName,
      browser.BrowserDraw,
      browser.BrowserMaze,
      browser.BrowserMultiply,
      calendar.SimpleCalendarAddOneEvent,
      calendar.SimpleCalendarAddOneEventInTwoWeeks,
      calendar.SimpleCalendarAddOneEventRelativeDay,
      calendar.SimpleCalendarAddOneEventTomorrow,
      calendar.SimpleCalendarAddRepeatingEvent,
      calendar.SimpleCalendarDeleteEvents,
      calendar.SimpleCalendarDeleteEventsOnRelativeDay,
      calendar.SimpleCalendarDeleteOneEvent,
      camera.CameraTakePhoto,
      camera.CameraTakeVideo,
      clock.ClockStopWatchPausedVerify,
      clock.ClockStopWatchRunning,
      clock.ClockTimerEntry,
      contacts.ContactsAddContact,
      contacts.ContactsNewContactDraft,
      expense.ExpenseAddMultiple,
      expense.ExpenseAddMultipleFromGallery,
      expense.ExpenseAddMultipleFromMarkor,
      expense.ExpenseAddSingle,
      expense.ExpenseDeleteDuplicates,
      expense.ExpenseDeleteDuplicates2,
      expense.ExpenseDeleteMultiple,
      expense.ExpenseDeleteMultiple2,
      expense.ExpenseDeleteSingle,
      files.FilesDeleteFile,
      files.FilesMoveFile,
      markor.MarkorAddNoteHeader,
      markor.MarkorChangeNoteContent,
      markor.MarkorCreateFolder,
      markor.MarkorCreateNote,
      markor.MarkorCreateNoteFromClipboard,
      markor.MarkorDeleteAllNotes,
      markor.MarkorDeleteNewestNote,
      markor.MarkorDeleteNote,
      markor.MarkorEditNote,
      markor.MarkorMergeNotes,
      markor.MarkorMoveNote,
      markor.MarkorTranscribeReceipt,
      markor.MarkorTranscribeVideo,
      # Markor composite tasks.
      markor_sms.MarkorCreateNoteAndSms,
      # OsmAnd.
      osmand.OsmAndFavorite,
      osmand.OsmAndMarker,
      osmand.OsmAndTrack,
      recipe.RecipeAddMultipleRecipes,
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
      recipe.RecipeDeleteSingleRecipe,
      recipe.RecipeDeleteSingleWithRecipeWithNoise,
      retro_music.RetroCreatePlaylist,
      retro_music.RetroPlayingQueue,
      retro_music.RetroPlaylistDuration,
      retro_music.RetroSavePlaylist,
      simple_draw_pro.SimpleDrawProCreateDrawing,
      simple_gallery_pro.SaveCopyOfReceiptTaskEval,
      sms.SimpleSmsReply,
      sms.SimpleSmsReplyMostRecent,
      sms.SimpleSmsResend,
      sms.SimpleSmsSend,
      sms.SimpleSmsSendClipboardContent,
      sms.SimpleSmsSendReceivedAddress,
      system.OpenAppTaskEval,
      system.SystemBluetoothTurnOff,
      system.SystemBluetoothTurnOffVerify,
      system.SystemBluetoothTurnOn,
      system.SystemBluetoothTurnOnVerify,
      system.SystemBrightnessMax,
      system.SystemBrightnessMaxVerify,
      system.SystemBrightnessMin,
      system.SystemBrightnessMinVerify,
      system.SystemCopyToClipboard,
      system.SystemWifiTurnOff,
      system.SystemWifiTurnOffVerify,
      system.SystemWifiTurnOn,
      system.SystemWifiTurnOnVerify,
      system_composite.TurnOffWifiAndTurnOnBluetooth,
      system_composite.TurnOnWifiAndOpenApp,
      # keep-sorted end
      # VLC media player tasks.
      vlc.VlcCreatePlaylist,
      vlc.VlcCreateTwoPlaylists,
      # Phone operations are flaky and the root cause is not known. Disabling
      # until resolution.
      # phone.MarkorCallApartment,
      # phone.PhoneAnswerCall,
      # phone.PhoneCallTextSender,
      # phone.PhoneMakeCall,
      # phone.PhoneRedialNumber,
      # phone.PhoneReturnMissedCall,
      # sms.SimpleSmsSendAfterCall,
  )

  def register_task(
      self, task_registry: dict[Any, Any], task_class: type[task_eval.TaskEval]
  ) -> None:
    """Registers the task class.

    Args:
      task_registry: The registry to register the task in.
      task_class: The class to register.
    """
    task_registry[task_class.__name__] = task_class

  def __init__(self):
    for task in self._TASKS:
      self.register_task(self.ANDROID_TASK_REGISTRY, task)

  # Add names with "." notation for autocomplete in Colab.
  names = types.SimpleNamespace(**{
      k: k
      for k in {
          **ANDROID_TASK_REGISTRY,
          **INFORMATION_RETRIEVAL_TASK_REGISTRY,
          **MINIWOB_TASK_REGISTRY,
          **MINIWOB_TASK_REGISTRY,
      }
  })
```

### `official/install/android_world/task_evals/task_eval.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Interface for a task and the evaluation logic for that task."""

import abc
import random
from typing import Any

from absl import logging
from android_world.env import adb_utils
from android_world.env import device_constants
from android_world.env import interface
from android_world.env.setup_device import setup
from android_world.utils import app_snapshot
from android_world.utils import datetime_utils


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

  @classmethod
  @abc.abstractmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Returns a random set of parameters for defining the task."""

  def _initialize_apps(self, env: interface.AsyncEnv) -> None:

    for app_name in self.app_names:
      # Don't need to restore snapshot for clipper app since it doesn't have
      # any state.
      if app_name and app_name != "clipper":
        try:
          app_snapshot.restore_snapshot(app_name, env.controller)
        except RuntimeError as error:
          logging.warning("Skipping app snapshot loading : %s", error)

  def install_apps_if_not_installed(self, env: interface.AsyncEnv) -> None:
    for app_name in self.app_names:
      setup.install_app_if_not_installed(app_name, env)

  @classmethod
  def set_device_time(cls, env: interface.AsyncEnv) -> None:
    """Sets the device time."""
    del env
    cls.device_time = device_constants.DT

  def initialize_device_time(self, env: interface.AsyncEnv) -> None:
    """Initializes the device time."""
    datetime_utils.setup_datetime(env.controller)
    datetime_utils.set_datetime(env.controller, self.device_time)

  def initialize_task(self, env: interface.AsyncEnv) -> None:  # pylint: disable=unused-argument
    """Initializes the task."""
    # Reset the interaction cache so previous tasks don't affect this run:
    env.interaction_cache = ""
    self.initialize_device_time(env)
    self._initialize_apps(env)
    logging.info("Initializing %s", self.name)
    if self.initialized:
      raise RuntimeError(f"{self.name}.initialize_task() is already called.")
    self.initialized = True

    # Set random seed for so that any random params initialized here are
    # deterministic when initialize_task is called again.
    seed = self.params.get("seed")
    if seed is not None:
      random.seed(seed)

  def _check_is_initialized(self) -> None:
    if not self.initialized:
      raise RuntimeError(
          f"{self.name}.initialize_task() must be called before"
          f" {self.name}.is_successful()."
      )

  def is_successful(self, env: interface.AsyncEnv) -> float:  # pylint: disable=unused-argument
    """Determines if the task is successful.

    Args:
      env:

    Returns:
      0: Not successful.
      1.0: Task is successful.

      For composite tasks, that combine together multiple tasks, the output is
      defined as sum(successful_tasks)/total_tasks.
    """
    self._check_is_initialized()
    return 1.0

  def tear_down(self, env: interface.AsyncEnv) -> None:  # pylint: disable=unused-argument
    """Tears down the task."""
    self._initialize_apps(env)
    try:
      adb_utils.close_recents(env.controller)
    except:  # pylint: disable=bare-except
      logging.exception("Failed to close recent apps. Continuing.")
    self.initialized = False
    logging.info("Tearing down %s", self.name)
```

### `official/install/android_world/task_evals/single/calendar/calendar.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/calendar.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tasks for Simple Calendar Pro app."""

import dataclasses
import random
from typing import Any, Callable, Optional
from android_world.env import device_constants
from android_world.task_evals.common_validators import sqlite_validators
from android_world.task_evals.single.calendar import calendar_evaluators
from android_world.task_evals.single.calendar import calendar_utils
from android_world.task_evals.single.calendar import events_generator
from android_world.task_evals.utils import sqlite_schema_utils
from android_world.utils import datetime_utils

# Keys in generated parameters and used to populate goal template.
_YEAR = "year"
_MONTH = "month"
_DAY = "day"
_DAY_OF_WEEK = "day_of_week"
_HOUR = "hour"
EVENT_TITLE = "event_title"
_EVENT_DESCRIPTION = "event_description"
_DURATION_MINS = "duration_mins"
_REPEAT_INTERVAL = "repeat_rule"
_REPEAT_INTERVALS = {"daily": 60 * 60 * 24, "weekly": 60 * 60 * 24 * 7}


def generate_noise_events(
    target_events: list[sqlite_schema_utils.CalendarEvent],
    n: int,
    filter_fn: Optional[
        Callable[[sqlite_schema_utils.CalendarEvent], bool]
    ] = None,
) -> list[sqlite_schema_utils.CalendarEvent]:
  if filter_fn is None:
    target_titles = set(event.title for event in target_events)
    filter_fn = lambda candidate: candidate.title not in target_titles

  return sqlite_schema_utils.get_random_items(
      n,
      lambda: events_generator.generate_event(
          datetime_utils.create_random_october_2023_unix_ts(start_day=1)
      ),
      filter_fn=filter_fn,
  )


class _SimpleCalendar(sqlite_validators.SQLiteApp):
  """Base class for calendar tasks and evaluation logic.

                  October 2023
              Su Mo Tu We Th Fr Sa
              1  2  3  4  5  6  7
              8  9 10 11 12 13 14
              [15]16 17 18 19 20 21
              22 23 24 25 26 27 28
              29 30 31

  The current date on the emulator will be set as October 15, 2023.
  """

  app_name_with_db = "simple calendar pro"
  app_names = ("simple calendar pro",)
  schema = {}

  db_key = "id"
  db_path = calendar_utils.DB_PATH
  table_name = calendar_utils.EVENTS_TABLE
  row_type = sqlite_schema_utils.CalendarEvent


class SimpleCalendarAddOneEvent(
    sqlite_validators.AddMultipleRows, _SimpleCalendar
):
  """Task for creating a calendar event in Simple Calendar Pro.

  Uses the absolute date in the template.
  """

  n_rows = 1  # Unused, but required by base class.
  complexity = 3.4
  template = (
      "In Simple Calendar Pro, create a calendar event on {year}-{month}-{day}"
      " at {hour}h with the title '{event_title}' and the description"
      " '{event_description}'. The event should last for {duration_mins} mins."
  )

  @classmethod
  def _get_random_target_row(cls) -> sqlite_schema_utils.CalendarEvent:
    """Generates a random calendar event."""
    return events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts()
    )

  def validate_addition_integrity(
      self,
      before: list[sqlite_schema_utils.CalendarEvent],
      after: list[sqlite_schema_utils.CalendarEvent],
      reference_rows: list[sqlite_schema_utils.CalendarEvent],
  ) -> bool:
    """Validates the integrity of the event addition."""
    return calendar_evaluators.validate_event_addition_integrity(
        before,
        after,
        reference_rows,
        extras_compare=["repeat_rule", "repeat_interval"],
    )

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for a new calendar event task."""
    event = cls._get_random_target_row()
    n_noise_events = random.randint(0, 20)
    return {
        _YEAR: device_constants.DT.year,
        _MONTH: device_constants.DT.month,
        _DAY: event.start_datetime.day,
        _HOUR: event.start_datetime.hour,
        _DURATION_MINS: event.duration_mins,
        EVENT_TITLE: event.title,
        _EVENT_DESCRIPTION: event.description,
        sqlite_validators.ROW_OBJECTS: [event],
        sqlite_validators.NOISE_ROW_OBJECTS: generate_noise_events(
            [event], n_noise_events
        ),
    }


class SimpleCalendarAddOneEventRelativeDay(SimpleCalendarAddOneEvent):
  """Task for creating a calendar event in Simple Calendar Pro.

  Uses the relative day of week in the template: from "this Monday" -> "this
  Sunday".
  """

  complexity = 3.4
  _DAY_RANGE = 6

  template = (
      "In Simple Calendar Pro, create a calendar event for this {day_of_week}"
      " at {hour}h with the title '{event_title}' and the description"
      " '{event_description}'. The event should last for {duration_mins} mins."
  )

  @property
  def goal(self) -> str:
    # Add day of week.
    dt: sqlite_schema_utils.CalendarEvent = self.params[
        sqlite_validators.ROW_OBJECTS
    ][0]
    day_of_week = dt.start_datetime.strftime("%A")
    self.params[_DAY_OF_WEEK] = day_of_week
    return self.template.format(**self.params)

  @classmethod
  def _get_random_target_row(cls):
    return events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts(
            # Monday, Oct 16 -> Saturday, Oct 21.
            start_day=device_constants.DT.day + 1,
            end_day=(
                device_constants.DT.day
                + SimpleCalendarAddOneEventRelativeDay._DAY_RANGE
            ),
        )
    )


class SimpleCalendarAddOneEventTomorrow(SimpleCalendarAddOneEvent):
  """Task for creating a calendar event in Simple Calendar Pro for tomorrow."""

  complexity = 3.4
  template = (
      "In Simple Calendar Pro, create a calendar event for tomorrow"
      " at {hour}h with the title '{event_title}' and the description"
      " '{event_description}'. The event should last for {duration_mins} mins."
  )

  @classmethod
  def _get_random_target_row(cls):
    # Generate an event for tomorrow.
    return events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts(
            device_constants.DT.day + 1, device_constants.DT.day + 1
        )
    )


class SimpleCalendarAddOneEventInTwoWeeks(SimpleCalendarAddOneEvent):
  """Task for creating a calendar event in Simple Calendar Pro in two weeks from today."""

  complexity = 3.4
  template = (
      "In Simple Calendar Pro, create a calendar event in two weeks from today"
      " at {hour}h with the title '{event_title}' and the description"
      " '{event_description}'. The event should last for {duration_mins} mins."
  )

  @classmethod
  def _get_random_target_row(cls):
    return events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts(
            device_constants.DT.day + 14, device_constants.DT.day + 14
        )
    )


class SimpleCalendarAddRepeatingEvent(SimpleCalendarAddOneEvent):
  """Task for creating a repeating calendar event in Simple Calendar Pro."""

  complexity = 3.4
  template = (
      "In Simple Calendar Pro, create a recurring calendar event titled"
      " '{event_title}' starting on {year}-{month}-{day} at"
      " {hour}h. The event recurs {repeat_rule}, forever, and lasts for"
      " {duration_mins} minutes each occurrence. The event description should"
      " be '{event_description}'."
  )

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for a new calendar event task."""
    template = cls._get_random_target_row()
    repeat_interval = random.choice(list(_REPEAT_INTERVALS))
    if repeat_interval == "weekly":
      repeat_rule = calendar_utils.generate_simple_calendar_weekly_repeat_rule(
          template.start_datetime.isoweekday()
      )
    else:
      repeat_rule = 0
    event = dataclasses.replace(
        template,
        repeat_interval=_REPEAT_INTERVALS[repeat_interval],
        repeat_rule=repeat_rule,
    )
    noise_events = generate_noise_events([event], random.randint(0, 20))
    return {
        _YEAR: device_constants.DT.year,
        _MONTH: device_constants.DT.month,
        _DAY: event.start_datetime.day,
        _HOUR: event.start_datetime.hour,
        _DURATION_MINS: event.duration_mins,
        EVENT_TITLE: event.title,
        _EVENT_DESCRIPTION: event.description,
        sqlite_validators.ROW_OBJECTS: [event],
        sqlite_validators.NOISE_ROW_OBJECTS: noise_events,
        _REPEAT_INTERVAL: repeat_interval,
    }


class SimpleCalendarDeleteEvents(
    sqlite_validators.DeleteMultipleRows, _SimpleCalendar
):
  """Task to delete multiple calendar events in Simple Calendar Pro.

  Uses the absolute date in the template.
  """

  n_rows = 3
  n_rows_noise = 20
  complexity = 1.4
  template = (
      "In Simple Calendar Pro, delete all the calendar events on"
      " {year}-{month}-{day}"
  )

  def validate_deletion_integrity(
      self,
      before: list[sqlite_schema_utils.CalendarEvent],
      after: list[sqlite_schema_utils.CalendarEvent],
  ) -> bool:
    """Validates the integrity of the event deletion."""
    return calendar_evaluators.validate_event_removal_integrity(
        before, after, [r.id for r in self.rows_to_delete]
    )

  @classmethod
  def _get_random_target_row(cls, day: int):
    return events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts(
            start_day=day, end_day=day
        )
    )

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for a remove calendar event task."""
    template = events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts()
    )
    events = [
        cls._get_random_target_row(template.start_datetime.day)
        for _ in range(cls.n_rows)
    ]
    noise_events = generate_noise_events(
        events,
        cls.n_rows_noise,
        filter_fn=lambda candidate: candidate.start_datetime.day
        not in (target.start_datetime.day for target in events),
    )
    return {
        _YEAR: device_constants.DT.year,
        _MONTH: device_constants.DT.month,
        _DAY: template.start_datetime.day,
        sqlite_validators.ROW_OBJECTS: events,
        sqlite_validators.NOISE_ROW_OBJECTS: noise_events,
    }


class SimpleCalendarDeleteOneEvent(SimpleCalendarDeleteEvents):
  """Task to delete a single calendar event in Simple Calendar Pro.

  Uses the absolute date in the template.
  """

  n_rows = 1
  complexity = 1.2
  template = (
      "In Simple Calendar Pro, delete the calendar event on"
      " {year}-{month}-{day} at {hour}h with the title '{event_title}'"
  )

  @classmethod
  def _get_random_target_row(cls):
    return events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts()
    )

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for a remove calendar event task."""
    event = cls._get_random_target_row()
    noise_events = generate_noise_events(
        [event],
        cls.n_rows_noise,
        filter_fn=(
            lambda candidate: (candidate.start_datetime != event.start_datetime)
            and (candidate.title != event.title)
        ),
    )
    return {
        _YEAR: device_constants.DT.year,
        _MONTH: device_constants.DT.month,
        _DAY: event.start_datetime.day,
        _HOUR: event.start_datetime.hour,
        _DURATION_MINS: event.duration_mins,
        EVENT_TITLE: event.title,
        _EVENT_DESCRIPTION: event.description,
        sqlite_validators.ROW_OBJECTS: [event],
        sqlite_validators.NOISE_ROW_OBJECTS: noise_events,
    }


class SimpleCalendarDeleteEventsOnRelativeDay(SimpleCalendarDeleteEvents):
  """Task for deleting calendar events for day_of_week in Simple Calendar Pro.

  Uses the relative day of week in the template: from "this Monday" -> "this
  Sunday".
  """

  complexity = 1.2
  n_rows = 2
  _DAY_RANGE: int = 6

  template = (
      "In Simple Calendar Pro, delete all events scheduled for this"
      " {day_of_week}."
  )

  @classmethod
  def _get_random_target_row(cls, day: int):
    return events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts(
            start_day=day, end_day=day
        )
    )

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for a remove calendar event task."""
    template = events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts(
            # Monday, Oct 16 -> Saturday, Oct 21.
            start_day=device_constants.DT.day + 1,
            end_day=device_constants.DT.day + cls._DAY_RANGE,
        )
    )
    events = [
        cls._get_random_target_row(template.start_datetime.day)
        for _ in range(cls.n_rows)
    ]
    noise_events = generate_noise_events(
        events,
        cls.n_rows_noise,
        filter_fn=lambda candidate: candidate.start_datetime.day
        not in (target.start_datetime.day for target in events),
    )
    return {
        _YEAR: device_constants.DT.year,
        _MONTH: device_constants.DT.month,
        _DAY: template.start_datetime.day,
        _DAY_OF_WEEK: template.start_datetime.strftime("%A"),
        sqlite_validators.ROW_OBJECTS: events,
        sqlite_validators.NOISE_ROW_OBJECTS: noise_events,
    }
```

### `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tasks for Simple Calendar Pro app."""

import dataclasses
import random
from typing import Any, Callable, Optional
from android_world.env import device_constants
from android_world.task_evals.common_validators import sqlite_validators
from android_world.task_evals.single.calendar import calendar_evaluators
from android_world.task_evals.single.calendar import calendar_utils
from android_world.task_evals.single.calendar import events_generator
from android_world.task_evals.utils import sqlite_schema_utils
from android_world.utils import datetime_utils

# Keys in generated parameters and used to populate goal template.
_YEAR = "year"
_MONTH = "month"
_DAY = "day"
_DAY_OF_WEEK = "day_of_week"
_HOUR = "hour"
EVENT_TITLE = "event_title"
_EVENT_DESCRIPTION = "event_description"
_DURATION_MINS = "duration_mins"
_REPEAT_INTERVAL = "repeat_rule"
_REPEAT_INTERVALS = {"daily": 60 * 60 * 24, "weekly": 60 * 60 * 24 * 7}


def generate_noise_events(
    target_events: list[sqlite_schema_utils.CalendarEvent],
    n: int,
    filter_fn: Optional[
        Callable[[sqlite_schema_utils.CalendarEvent], bool]
    ] = None,
) -> list[sqlite_schema_utils.CalendarEvent]:
  if filter_fn is None:
    target_titles = set(event.title for event in target_events)
    filter_fn = lambda candidate: candidate.title not in target_titles

  return sqlite_schema_utils.get_random_items(
      n,
      lambda: events_generator.generate_event(
          datetime_utils.create_random_october_2023_unix_ts(start_day=1)
      ),
      filter_fn=filter_fn,
  )


class _SimpleCalendar(sqlite_validators.SQLiteApp):
  """Base class for calendar tasks and evaluation logic.

                  October 2023
              Su Mo Tu We Th Fr Sa
              1  2  3  4  5  6  7
              8  9 10 11 12 13 14
              [15]16 17 18 19 20 21
              22 23 24 25 26 27 28
              29 30 31

  The current date on the emulator will be set as October 15, 2023.
  """

  app_name_with_db = "simple calendar pro"
  app_names = ("simple calendar pro",)
  schema = {}

  db_key = "id"
  db_path = calendar_utils.DB_PATH
  table_name = calendar_utils.EVENTS_TABLE
  row_type = sqlite_schema_utils.CalendarEvent


class SimpleCalendarAddOneEvent(
    sqlite_validators.AddMultipleRows, _SimpleCalendar
):
  """Task for creating a calendar event in Simple Calendar Pro.

  Uses the absolute date in the template.
  """

  n_rows = 1  # Unused, but required by base class.
  complexity = 3.4
  template = (
      "In Simple Calendar Pro, create a calendar event on {year}-{month}-{day}"
      " at {hour}h with the title '{event_title}' and the description"
      " '{event_description}'. The event should last for {duration_mins} mins."
  )

  @classmethod
  def _get_random_target_row(cls) -> sqlite_schema_utils.CalendarEvent:
    """Generates a random calendar event."""
    return events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts()
    )

  def validate_addition_integrity(
      self,
      before: list[sqlite_schema_utils.CalendarEvent],
      after: list[sqlite_schema_utils.CalendarEvent],
      reference_rows: list[sqlite_schema_utils.CalendarEvent],
  ) -> bool:
    """Validates the integrity of the event addition."""
    return calendar_evaluators.validate_event_addition_integrity(
        before,
        after,
        reference_rows,
        extras_compare=["repeat_rule", "repeat_interval"],
    )

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for a new calendar event task."""
    event = cls._get_random_target_row()
    n_noise_events = random.randint(0, 20)
    return {
        _YEAR: device_constants.DT.year,
        _MONTH: device_constants.DT.month,
        _DAY: event.start_datetime.day,
        _HOUR: event.start_datetime.hour,
        _DURATION_MINS: event.duration_mins,
        EVENT_TITLE: event.title,
        _EVENT_DESCRIPTION: event.description,
        sqlite_validators.ROW_OBJECTS: [event],
        sqlite_validators.NOISE_ROW_OBJECTS: generate_noise_events(
            [event], n_noise_events
        ),
    }


class SimpleCalendarAddOneEventRelativeDay(SimpleCalendarAddOneEvent):
  """Task for creating a calendar event in Simple Calendar Pro.

  Uses the relative day of week in the template: from "this Monday" -> "this
  Sunday".
  """

  complexity = 3.4
  _DAY_RANGE = 6

  template = (
      "In Simple Calendar Pro, create a calendar event for this {day_of_week}"
      " at {hour}h with the title '{event_title}' and the description"
      " '{event_description}'. The event should last for {duration_mins} mins."
  )

  @property
  def goal(self) -> str:
    # Add day of week.
    dt: sqlite_schema_utils.CalendarEvent = self.params[
        sqlite_validators.ROW_OBJECTS
    ][0]
    day_of_week = dt.start_datetime.strftime("%A")
    self.params[_DAY_OF_WEEK] = day_of_week
    return self.template.format(**self.params)

  @classmethod
  def _get_random_target_row(cls):
    return events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts(
            # Monday, Oct 16 -> Saturday, Oct 21.
            start_day=device_constants.DT.day + 1,
            end_day=(
                device_constants.DT.day
                + SimpleCalendarAddOneEventRelativeDay._DAY_RANGE
            ),
        )
    )


class SimpleCalendarAddOneEventTomorrow(SimpleCalendarAddOneEvent):
  """Task for creating a calendar event in Simple Calendar Pro for tomorrow."""

  complexity = 3.4
  template = (
      "In Simple Calendar Pro, create a calendar event for tomorrow"
      " at {hour}h with the title '{event_title}' and the description"
      " '{event_description}'. The event should last for {duration_mins} mins."
  )

  @classmethod
  def _get_random_target_row(cls):
    # Generate an event for tomorrow.
    return events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts(
            device_constants.DT.day + 1, device_constants.DT.day + 1
        )
    )


class SimpleCalendarAddOneEventInTwoWeeks(SimpleCalendarAddOneEvent):
  """Task for creating a calendar event in Simple Calendar Pro in two weeks from today."""

  complexity = 3.4
  template = (
      "In Simple Calendar Pro, create a calendar event in two weeks from today"
      " at {hour}h with the title '{event_title}' and the description"
      " '{event_description}'. The event should last for {duration_mins} mins."
  )

  @classmethod
  def _get_random_target_row(cls):
    return events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts(
            device_constants.DT.day + 14, device_constants.DT.day + 14
        )
    )


class SimpleCalendarAddRepeatingEvent(SimpleCalendarAddOneEvent):
  """Task for creating a repeating calendar event in Simple Calendar Pro."""

  complexity = 3.4
  template = (
      "In Simple Calendar Pro, create a recurring calendar event titled"
      " '{event_title}' starting on {year}-{month}-{day} at"
      " {hour}h. The event recurs {repeat_rule}, forever, and lasts for"
      " {duration_mins} minutes each occurrence. The event description should"
      " be '{event_description}'."
  )

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for a new calendar event task."""
    template = cls._get_random_target_row()
    repeat_interval = random.choice(list(_REPEAT_INTERVALS))
    if repeat_interval == "weekly":
      repeat_rule = calendar_utils.generate_simple_calendar_weekly_repeat_rule(
          template.start_datetime.isoweekday()
      )
    else:
      repeat_rule = 0
    event = dataclasses.replace(
        template,
        repeat_interval=_REPEAT_INTERVALS[repeat_interval],
        repeat_rule=repeat_rule,
    )
    noise_events = generate_noise_events([event], random.randint(0, 20))
    return {
        _YEAR: device_constants.DT.year,
        _MONTH: device_constants.DT.month,
        _DAY: event.start_datetime.day,
        _HOUR: event.start_datetime.hour,
        _DURATION_MINS: event.duration_mins,
        EVENT_TITLE: event.title,
        _EVENT_DESCRIPTION: event.description,
        sqlite_validators.ROW_OBJECTS: [event],
        sqlite_validators.NOISE_ROW_OBJECTS: noise_events,
        _REPEAT_INTERVAL: repeat_interval,
    }


class SimpleCalendarDeleteEvents(
    sqlite_validators.DeleteMultipleRows, _SimpleCalendar
):
  """Task to delete multiple calendar events in Simple Calendar Pro.

  Uses the absolute date in the template.
  """

  n_rows = 3
  n_rows_noise = 20
  complexity = 1.4
  template = (
      "In Simple Calendar Pro, delete all the calendar events on"
      " {year}-{month}-{day}"
  )

  def validate_deletion_integrity(
      self,
      before: list[sqlite_schema_utils.CalendarEvent],
      after: list[sqlite_schema_utils.CalendarEvent],
  ) -> bool:
    """Validates the integrity of the event deletion."""
    return calendar_evaluators.validate_event_removal_integrity(
        before, after, [r.id for r in self.rows_to_delete]
    )

  @classmethod
  def _get_random_target_row(cls, day: int):
    return events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts(
            start_day=day, end_day=day
        )
    )

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for a remove calendar event task."""
    template = events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts()
    )
    events = [
        cls._get_random_target_row(template.start_datetime.day)
        for _ in range(cls.n_rows)
    ]
    noise_events = generate_noise_events(
        events,
        cls.n_rows_noise,
        filter_fn=lambda candidate: candidate.start_datetime.day
        not in (target.start_datetime.day for target in events),
    )
    return {
        _YEAR: device_constants.DT.year,
        _MONTH: device_constants.DT.month,
        _DAY: template.start_datetime.day,
        sqlite_validators.ROW_OBJECTS: events,
        sqlite_validators.NOISE_ROW_OBJECTS: noise_events,
    }


class SimpleCalendarDeleteOneEvent(SimpleCalendarDeleteEvents):
  """Task to delete a single calendar event in Simple Calendar Pro.

  Uses the absolute date in the template.
  """

  n_rows = 1
  complexity = 1.2
  template = (
      "In Simple Calendar Pro, delete the calendar event on"
      " {year}-{month}-{day} at {hour}h with the title '{event_title}'"
  )

  @classmethod
  def _get_random_target_row(cls):
    return events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts()
    )

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for a remove calendar event task."""
    event = cls._get_random_target_row()
    noise_events = generate_noise_events(
        [event],
        cls.n_rows_noise,
        filter_fn=(
            lambda candidate: (candidate.start_datetime != event.start_datetime)
            and (candidate.title != event.title)
        ),
    )
    return {
        _YEAR: device_constants.DT.year,
        _MONTH: device_constants.DT.month,
        _DAY: event.start_datetime.day,
        _HOUR: event.start_datetime.hour,
        _DURATION_MINS: event.duration_mins,
        EVENT_TITLE: event.title,
        _EVENT_DESCRIPTION: event.description,
        sqlite_validators.ROW_OBJECTS: [event],
        sqlite_validators.NOISE_ROW_OBJECTS: noise_events,
    }


class SimpleCalendarDeleteEventsOnRelativeDay(SimpleCalendarDeleteEvents):
  """Task for deleting calendar events for day_of_week in Simple Calendar Pro.

  Uses the relative day of week in the template: from "this Monday" -> "this
  Sunday".
  """

  complexity = 1.2
  n_rows = 2
  _DAY_RANGE: int = 6

  template = (
      "In Simple Calendar Pro, delete all events scheduled for this"
      " {day_of_week}."
  )

  @classmethod
  def _get_random_target_row(cls, day: int):
    return events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts(
            start_day=day, end_day=day
        )
    )

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for a remove calendar event task."""
    template = events_generator.generate_event(
        datetime_utils.create_random_october_2023_unix_ts(
            # Monday, Oct 16 -> Saturday, Oct 21.
            start_day=device_constants.DT.day + 1,
            end_day=device_constants.DT.day + cls._DAY_RANGE,
        )
    )
    events = [
        cls._get_random_target_row(template.start_datetime.day)
        for _ in range(cls.n_rows)
    ]
    noise_events = generate_noise_events(
        events,
        cls.n_rows_noise,
        filter_fn=lambda candidate: candidate.start_datetime.day
        not in (target.start_datetime.day for target in events),
    )
    return {
        _YEAR: device_constants.DT.year,
        _MONTH: device_constants.DT.month,
        _DAY: template.start_datetime.day,
        _DAY_OF_WEEK: template.start_datetime.strftime("%A"),
        sqlite_validators.ROW_OBJECTS: events,
        sqlite_validators.NOISE_ROW_OBJECTS: noise_events,
    }
```

### `official/install/android_world/task_evals/common_validators/sqlite_validators.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/common_validators/sqlite_validators.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Base class for task evaluations interacting with SQLite-based Android apps."""

import abc
import dataclasses
from typing import Any
from typing import Optional
from typing import Type
from absl import logging
from android_world.env import interface
from android_world.task_evals import task_eval
from android_world.task_evals.utils import sqlite_schema_utils
from android_world.task_evals.utils import sqlite_utils
from android_world.utils import fuzzy_match_lib


def verify_playlist(
    device_playlist_rows: list[sqlite_schema_utils.PlaylistInfo],
    candidate_playlist_name: str,
    candidate_files: list[str],
) -> bool:
  """Verifies if the playlist on the device matches the expected name, files, and their order.

  Args:
    device_playlist_rows: The playlist rows queried from the device.
    candidate_playlist_name: The expected name of the playlist.
    candidate_files: The list of expected media file names in the playlist.

  Returns:
    True if the actual playlist matches the expected criteria, False otherwise.
  """
  total = sum(
      1
      for actual_item in device_playlist_rows
      if fuzzy_match_lib.fuzzy_match(
          actual_item.playlist_name, candidate_playlist_name, ignore_case=True
      )
  )

  if total != len(candidate_files):
    return False

  matched_files = 0
  for index, expected_file in enumerate(candidate_files):
    if any(
        fuzzy_match_lib.fuzzy_match(
            actual_item.playlist_name, candidate_playlist_name, ignore_case=True
        )
        and actual_item.media_file_name == expected_file
        and (actual_item.order_in_playlist == index)
        for actual_item in device_playlist_rows
    ):
      matched_files += 1
    else:
      return False

  return matched_files == len(candidate_files)


def validate_rows_removal_integrity(
    before: list[sqlite_schema_utils.RowType],
    after: list[sqlite_schema_utils.RowType],
    ids: list[int],
    id_name: str,
) -> bool:
  """Validates that specified rows have been removed correctly from the rows list and that the remaining rows are unaltered.

  This function checks that all rows with IDs in `ids` are not present
  in the `after` state and that all other rows from the `before` state remain
  unchanged. It also ensures that no new rows have been inadvertently added.

  Args:
    before: State of the rows before removal.
    after: State of the rows after attempted removal.
    ids: IDs of the rows expected to be removed.
    id_name: The name of the ID column in the database.

  Returns:
    True if specified rows are removed and the integrity of the rows list is
    maintained; False if any specified rows are not removed, if any
    non-specified rows are missing, or if new rows have been added.
  """
  for row_id in ids:
    if not any(row for row in before if getattr(row, id_name) == row_id):
      raise ValueError(f"row ID {row_id} not present in before.")

  # Validate the removal and intactness of other rows
  for row in before:
    # If the row ID is in the list of removed row IDs
    if getattr(row, id_name) in ids:
      if row in after:
        return False
    elif row not in after:
      # Make sure we didn't remove other rows.
      return False

  # Check that no new unexpected rows have been added
  for row in after:
    if row not in before:
      return False

  return True


def validate_rows_addition_integrity(
    before: list[sqlite_schema_utils.RowType],
    after: list[sqlite_schema_utils.RowType],
    reference_rows: list[sqlite_schema_utils.RowType],
    compare_fields: list[str],
    free_form_fields: list[str] | None = None,
) -> bool:
  """Validates that specific rows have been added correctly without side effects.

  Checks that `reference_rows` are present in `after` and not in `before`, and
  that the rest of the rows in `before` remain unaltered in `after`. This
  validation ensures that no unrelated rows were added, removed, or changed in
  the process.

  Args:
    before: The state of the rows before the addition.
    after: The state of the rows after the attempted addition.
    reference_rows: A list of rows that are expected to be added.
    compare_fields: Which fields to use for comparison for each row.
    free_form_fields: Free-form, text fields where fuzzy matching will be used
      for comparison.

  Returns:
      bool: True if the rows were added correctly and other rows remained
      unaltered. False otherwise.
  """
  if not compare_fields:
    raise ValueError("compare_fields must not be empty.")
  if not free_form_fields:
    free_form_fields = []

  def db_row_matches_reference(
      reference_row: sqlite_schema_utils.RowType,
      row: sqlite_schema_utils.RowType,
  ) -> bool:
    for field in compare_fields:
      reference_value = getattr(reference_row, field)
      candidate_value = getattr(row, field)
      # Fuzzy match for text fields.
      if field in free_form_fields:
        if not fuzzy_match_lib.fuzzy_match(reference_value, candidate_value):
          return False
      else:
        if reference_value != candidate_value:
          return False
    return True

  # Check if the added rows are present in the 'after' state
  for reference_row in reference_rows:
    if not any(db_row_matches_reference(reference_row, row) for row in after):
      logging.warning(
          "Expected row %s not found in the 'after' state.", reference_row
      )
      return False

  if len(after) != len(before) + len(reference_rows):
    logging.warning(
        "The length of after %i is not equal to the length of before %i +"
        " length of added rows %i",
        len(after),
        len(before),
        len(reference_rows),
    )
    return False

  # Validate that no other rows were altered or removed during the addition
  for row in before:
    if row not in after:
      logging.warning(
          "row %s from 'before' state missing or altered in the 'after' state.",
          row,
      )
      return False

  return True


# Represents row objects to be added or deleted internally.
ROW_OBJECTS = "row_objects"
NOISE_ROW_OBJECTS = "noise_row_objects"


class SQLiteApp(task_eval.TaskEval, abc.ABC):
  """Base class for tasks interacting with SQLite-based Android apps."""

  app_name_with_db: str
  db_path: str
  db_key: str
  table_name: str
  row_type: Type[sqlite_schema_utils.SQLiteRow]

  def list_rows(
      self,
      env: interface.AsyncEnv,
      timeout_sec: Optional[float] = None,
  ) -> list[sqlite_schema_utils.RowType]:
    """Lists all rows from the specified table in the app's database using ADB.

    Args:
        env: The Android environment interface.
        timeout_sec: An optional timeout for the ADB operations.

    Returns:
        A list of row objects, each representing a row from the specified table
        in the database.
    """
    return sqlite_utils.get_rows_from_remote_device(
        self.table_name, self.db_path, self.row_type, env, timeout_sec
    )

  def add_rows(
      self,
      rows: list[sqlite_schema_utils.RowType],
      env: interface.AsyncEnv,
      timeout_sec: Optional[float] = None,
  ) -> None:
    sqlite_utils.insert_rows_to_remote_db(
        rows,
        self.db_key,
        self.table_name,
        self.db_path,
        self.app_name_with_db,
        env,
        timeout_sec,
    )

  def _clear_db(self, env: interface.AsyncEnv) -> None:
    """Clears the app's SQLite database."""
    sqlite_utils.delete_all_rows_from_table(
        self.table_name, self.db_path, env, self.app_name_with_db
    )
    try:
      self.list_rows(env)
    except ValueError as e:
      raise RuntimeError(
          "After clearing the old SQLite database, a new empty database was"
          " not created."
      ) from e

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    """Initializes the task environment."""
    self._clear_db(env)  # In case the previous run crashed.
    super().initialize_task(env)
    self._clear_db(env)
    if NOISE_ROW_OBJECTS in self.params:
      self.add_rows(self.params[NOISE_ROW_OBJECTS], env)

  def tear_down(self, env: interface.AsyncEnv):
    """Cleans up after task completion."""
    super().tear_down(env)
    self._clear_db(env)


class AddMultipleRows(SQLiteApp, abc.ABC):
  """Abstract class for tasks that involve adding multiple rows to a SQLite database."""

  n_rows: int = -1  # Number of rows to be added, to be defined in subclasses.

  def __init__(self, params: dict[str, Any]):
    super().__init__(params)
    self.before = []

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    """Initial setup for the task, if necessary."""
    super().initialize_task(env)
    self.before = self.list_rows(env)

  @abc.abstractmethod
  def validate_addition_integrity(
      self,
      before: list[sqlite_schema_utils.RowType],
      after: list[sqlite_schema_utils.RowType],
      reference_rows: list[sqlite_schema_utils.RowType],
  ) -> bool:
    """Validates the integrity of the rows addition.

    Args:
      before: State of database before modification.
      after: Current state of the database.
      reference_rows: The rows that we are checking if are added and in the
        current state.

    Returns:
      Whether the reference rows were successfully added.
    """

  def is_successful(self, env: interface.AsyncEnv) -> float:
    """Determine if the row addition task was successful."""
    after = self.list_rows(env)
    row_addition_successful = self.validate_addition_integrity(
        self.before, after, self.params[ROW_OBJECTS]
    )
    return 1.0 if row_addition_successful else 0.0

  @classmethod
  @abc.abstractmethod
  def _get_random_target_row(cls) -> sqlite_schema_utils.RowType:
    """Generates a random row. To be implemented in subclasses."""

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for new row addition tasks."""
    if cls.n_rows == -1:
      raise ValueError("n_rows must be defined in subclasses.")
    random_rows = [cls._get_random_target_row() for _ in range(cls.n_rows)]
    return {ROW_OBJECTS: random_rows}


class DeleteMultipleRows(SQLiteApp, abc.ABC):
  """Abstract class for tasks that involve deleting multiple rows from a SQLite database."""

  n_rows: int  # Number of rows to be deleted, to be defined in subclasses.
  n_rows_noise: int  # Number of additional rows to add not relevant to goal.

  def __init__(self, params: dict[str, Any]):
    super().__init__(params)
    self.rows_to_delete = []
    self.before = []

  def _validate_initial_state(
      self, before: list[sqlite_schema_utils.RowType]
  ) -> None:
    """Validates the initial state before the deletion process starts."""
    if len(before) != (self.n_rows + self.n_rows_noise):
      raise RuntimeError(
          "Initial state validation failed. The number of rows before deletion"
          f" does not match the expected count. Found {len(before)} in DB, but"
          f" expected {self.n_rows + self.n_rows_noise}."
      )

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    """Initial setup for the task, if necessary."""
    super().initialize_task(env)
    n_rows = 0
    if ROW_OBJECTS in self.params:
      self.add_rows(self.params[ROW_OBJECTS], env)
      n_rows = len(self.params[ROW_OBJECTS])
    self.before = self.list_rows(env)
    # Newly added rows are at the end.
    self.rows_to_delete = self.before[len(self.before) - n_rows :]
    self._validate_initial_state(self.before)

  def is_successful(self, env: interface.AsyncEnv) -> float:
    """Determine if the row deletion task was successful."""
    super().is_successful(env)

    # Get the state of the database after the deletion attempt
    after = self.list_rows(env)

    # Validate the integrity of the deletion
    deletion_successful = self.validate_deletion_integrity(self.before, after)
    return 1.0 if deletion_successful else 0.0

  @abc.abstractmethod
  def validate_deletion_integrity(
      self,
      before: list[sqlite_schema_utils.RowType],
      after: list[sqlite_schema_utils.RowType],
  ):
    """Validates the integrity of the row deletion."""


class DeleteDuplicateRows(DeleteMultipleRows):
  """Abstract class for tasks that involve deleting duplicate rows from a SQLite database."""

  def _validate_candidates(
      self, candidates: list[sqlite_schema_utils.RowType]
  ) -> None:
    """Validates the initial state before the deletion process starts."""
    if len(candidates) % 2 != 0:
      raise ValueError(
          "Initial state validation failed. Must contain exactly two rows."
      )
    val1, val2 = candidates
    for field in dataclasses.fields(val1):
      if field.name == self.db_key:
        continue
      if getattr(val1, field.name) != getattr(val2, field.name):
        raise ValueError(
            "Initial state validation failed. Doesn't contain duplicate rows."
        )

  def _validate_initial_state(
      self, before: list[sqlite_schema_utils.RowType]
  ) -> None:
    """Validates the initial state before the deletion process starts."""
    if len(before) != (2 + self.n_rows_noise):
      raise ValueError(
          "Initial state validation failed. The number of rows before deletion"
          f" does not match the expected count. Found {len(before)} in DB, but"
          f" expected {2 + self.n_rows_noise}."
      )

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    """Initial setup for the task, if necessary."""
    super().initialize_task(env)
    self._validate_candidates(self.params[ROW_OBJECTS])
    self.duplicate_rows = self.rows_to_delete
```

### `official/install/android_world/suite_utils.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/suite_utils.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities for evaluating automation agents."""

import collections
import datetime
import hashlib
import logging
import os
import random
import time
import traceback
from typing import Any, Callable, Type, TypeVar

from android_env import env_interface
from android_world import checkpointer as checkpointer_lib
from android_world import constants
from android_world import episode_runner
from android_world.agents import base_agent
from android_world.env import adb_utils
from android_world.env import interface
from android_world.task_evals import task_eval
from android_world.task_evals.miniwob import miniwob_base
from fuzzywuzzy import process
import numpy as np
import pandas as pd

# A fixed seed to use when use identical parameters but seed is not set.
_FIXED_SEED = 123
_TASK_TEMPLATE_COLUMN = 'task_template'
_TASK_PROMPT_COLUMN = 'task_prompt'
TaskEvalType = TypeVar('TaskEvalType', bound=task_eval.TaskEval)


class Suite(dict[str, list[task_eval.TaskEval]]):
  """A suite of tasks.

  Each key is the task name as defined in registry.py and its value is a list
  of instantiated task objects. These instances differ from each other by their
  parameter initializations; i.e. each task will have different task parameters.
  """

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._suite_family = None

  @property
  def suite_family(self) -> str:
    """Getter for suite_family."""
    if self._suite_family is None:
      raise ValueError('Suite family is not set; please first set it.')
    return self._suite_family

  @suite_family.setter
  def suite_family(self, value: str):
    """Setter for suite_family."""
    self._suite_family = value


def _log_and_print(msg: str, *args: object) -> None:
  formatted = msg % args if args else msg
  logging.info(formatted)
  print(formatted)


def _instantiate_task(
    task: Type[task_eval.TaskEval],
    params: dict[str, Any] | None = None,
    seed: int | None = None,
    env: interface.AsyncEnv | None = None,
) -> task_eval.TaskEval:
  """Creates an instance of a task with params.

  If params is not provided, it will use random params, controlled by a seed.

  Args:
    task: The task to instantiate.
    params: Params to use.
    seed: Seed for the random number generator.
    env: The environment.

  Returns:
    An instance of a task.
  """
  task.set_device_time(env)
  if params is None:
    if seed is not None:
      random.seed(seed)
    params = task.generate_random_params()
    params[constants.EpisodeConstants.SEED] = seed
  return task(params)


def create_suite(
    task_registry: dict[str, Type[task_eval.TaskEval]],
    n_task_combinations: int = 1,
    seed: int | None = None,
    tasks: list[str] | None = None,
    use_identical_params: bool = False,
    env: interface.AsyncEnv | None = None
) -> Suite:
  """Creates task suite.

  A task suite is a set of tasks. Each task is instantiated
  `n_task_combinations` times using new parameters. For example a task suite
  could look like:

  ```python
  {
      'GoogleSearchTask': [
          GoogleSearchTask({'term': 'cute cats'}),
          GoogleSearchTask({'term': 'comfy pillows'}),
      ],
      'WifiDisable': [  # No params for WiFi task.
          WifiDisable({}),
          WifiDisable({}),
      ],
  }
  ```

  Args:
    task_registry: Maps task names to their TaskEvals.
    n_task_combinations: Number of instances to create per task. Each instance
      will have unique param combinations.
    seed: Seed for the random number generator. Setting the seed will result in
      the same sequence of params for task instantiation per each task.
    tasks: List of task types that should be in the suite. If value is `None`
      all task types and associated instances will be created.
    use_identical_params: If True, each instance of a task, for a total of
      `n_task_combinations`, will have the same params.
    env: The environment that will be run on.

  Returns:
    A mapping of task name to instances of the task.
  """

  def _get_instance_seed(name: str, i: int) -> int:
    unique_seed_str = f'{seed}_{name}_{i}'
    return int(hashlib.sha256(unique_seed_str.encode()).hexdigest(), 16) % (
        2**32
    )

  suite = {}
  for name, task_type in task_registry.items():
    current = []
    for i in range(n_task_combinations):
      if use_identical_params:
        instance_seed = (
            _get_instance_seed(name, 0) if seed is not None else _FIXED_SEED
        )
      elif seed is not None:
        instance_seed = _get_instance_seed(name, i)
      else:
        instance_seed = None
      current.append(_instantiate_task(task_type, seed=instance_seed, env=env))
    suite[name] = current
  suite = _filter_tasks(suite, task_registry, tasks)

  # Sort suite alphabetically by task name.
  return Suite(sorted(suite.items()))


def _suggest_keyword(
    typo: str, keywords: list[str], threshold: int = 80
) -> str:
  """Suggests a keyword."""
  suggestion, score = process.extractOne(typo, keywords)
  if score >= threshold:
    return f" Did you mean '{suggestion}'?"
  else:
    return ''


def _filter_tasks(
    suite: dict[str, list[task_eval.TaskEval]],
    task_registry: dict[str, Type[task_eval.TaskEval]],
    tasks: list[str] | None = None,
) -> dict[str, list[task_eval.TaskEval]]:
  """Filters a suite by specific tasks.

  Args:
    suite: The suite to retrieve tasks from.
    task_registry: The task registry the suite is from.
    tasks: The tasks to retrieve. If None, just return entire suite.

  Returns:
    A "mini-suite" of tasks from suite.

  Raises:
    ValueError: If invalid task name.
  """
  if tasks is None:
    return suite
  subset = {}

  # Validate.
  for name in tasks:
    if name not in task_registry:
      raise ValueError(
          f'Task {name} not found in the task registry.'
          + _suggest_keyword(name, list(task_registry.keys()))
      )

  # Filter.
  for name, instances in suite.items():
    if name in tasks:
      subset[name] = instances
  return subset


def _run_task(
    task: TaskEvalType,
    run_episode: Callable[[TaskEvalType], episode_runner.EpisodeResult],
    env: interface.AsyncEnv,
    demo_mode: bool,
) -> dict[str, Any]:
  """Runs a task.

  Args:
    task: The task.
    run_episode: Runs the agent on the task.
    env: Environment that will be run on.
    demo_mode: Whether running in demo mode; will display success overlay if so.

  Returns:
    Episode data and associated success signals.

  Raises:
    ValueError: If step data was not as expected.
  """
  start = time.time()
  try:
    task.initialize_task(env)
    _log_and_print('Running task %s with goal "%s"', task.name, task.goal)
    interaction_results = run_episode(task)
    task_successful = task.is_successful(env)
  except Exception as e:  # pylint: disable=broad-exception-caught
    _log_and_print('%s\nSKIPPING %s.', '~' * 80, task.name)
    logging.exception(
        'Logging exception and skipping task. Will keep running. Task: %s: %s',
        task.name,
        e,
    )
    traceback.print_exc()
    return _create_failed_result(
        task.name, task.goal, traceback.format_exc(), time.time() - start
    )
  else:
    agent_successful = task_successful if interaction_results.done else 0.0
    _log_and_print(
        '%s; %s',
        'Task Successful ✅' if agent_successful > 0.5 else 'Task Failed ❌',
        f' {task.goal}',
    )

    if demo_mode:
      _display_success_overlay(env.controller, agent_successful)

    result = {
        constants.EpisodeConstants.GOAL: task.goal,
        constants.EpisodeConstants.TASK_TEMPLATE: task.name,
        constants.EpisodeConstants.EPISODE_DATA: interaction_results.step_data,
        constants.EpisodeConstants.IS_SUCCESSFUL: agent_successful,
        constants.EpisodeConstants.RUN_TIME: time.time() - start,
        constants.EpisodeConstants.FINISH_DTIME: datetime.datetime.now(),
        constants.EpisodeConstants.EPISODE_LENGTH: len(
            interaction_results.step_data[constants.STEP_NUMBER]
        ),
        constants.EpisodeConstants.AUX_DATA: interaction_results.aux_data,
        constants.EpisodeConstants.SCREEN_CONFIG: _get_screen_config(task),
        constants.EpisodeConstants.EXCEPTION_INFO: None,
        constants.EpisodeConstants.SEED: task.params[
            constants.EpisodeConstants.SEED
        ],
    }
    task.tear_down(env)
    return result


def _get_task_info(
    episodes: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
  """Gets task info from episodes.

  Args:
    episodes: Episodes to get info from.

  Returns:
    A tuple of completed and failed task lookup tables.
  """

  completed = collections.defaultdict(list)
  failed = collections.defaultdict(list)
  for episode in episodes:
    instance_name = (
        episode[constants.EpisodeConstants.TASK_TEMPLATE]
        + checkpointer_lib.INSTANCE_SEPARATOR
        + str(episode[constants.EpisodeConstants.INSTANCE_ID])
    )
    if episode.get(constants.EpisodeConstants.EXCEPTION_INFO) is not None:
      failed[instance_name].append(episode)
    else:
      completed[instance_name].append(episode)
  return completed, failed


def _run_task_suite(
    suite: Suite,
    run_episode: Callable[[task_eval.TaskEval], episode_runner.EpisodeResult],
    env: interface.AsyncEnv,
    checkpointer: checkpointer_lib.Checkpointer = checkpointer_lib.NullCheckpointer(),
    demo_mode: bool = False,
    agent_name: str = '',
    return_full_episode_data: bool = False,
    process_episodes_fn=None,
    check_episode_fn: Callable[[dict[str, Any]], bool] | None = None,
) -> list[dict[str, Any]]:
  """Runs e2e system on suite.

  Args:
    suite: The suite to run it on.
    run_episode: The e2e system. See run_suite.py for an example.
    env: The environment e2e system runs on.
    checkpointer: See docstring from `run`.
    demo_mode: Whether to display the scoreboard.
    agent_name: The name of the agent.
    return_full_episode_data: Whether to return full episode data instead of
      just metadata.
    process_episodes_fn: The function to process episode data. Usually to
      compute metrics. Deafaults to process_episodes from this file.
    check_episode_fn: The function to check episode data.

  Returns:
    Metadata for each episode, including the scripted reward.
  """
  metadata_fields = [
      constants.EpisodeConstants.GOAL,
      constants.EpisodeConstants.TASK_TEMPLATE,
      constants.EpisodeConstants.INSTANCE_ID,
      constants.EpisodeConstants.IS_SUCCESSFUL,
      constants.EpisodeConstants.EPISODE_LENGTH,
      constants.EpisodeConstants.RUN_TIME,
      constants.EpisodeConstants.EXCEPTION_INFO,
      constants.EpisodeConstants.AUX_DATA,
  ]
  completed_tasks, failed_tasks = _get_task_info(
      checkpointer.load(fields=metadata_fields)
  )
  if process_episodes_fn is None:
    process_episodes_fn = process_episodes

  if (completed_tasks or failed_tasks) and return_full_episode_data:
    raise ValueError(
        'Cannot return full episode data when resuming from a checkpoint.'
    )
  episodes_metadata: list[dict[str, Any]] = []
  full_episode_data = []
  correct, total = 0, 0
  for name, instances in suite.items():
    msg = 'Running task: ' + name
    _log_and_print(msg + '\n' + '=' * len(msg))

    for i, instance in enumerate(instances):
      instance_name = (
          instance.name + checkpointer_lib.INSTANCE_SEPARATOR + str(i)
      )
      # Transferring from old checkpoint.
      if instance_name in completed_tasks:
        completed_episodes: list[dict[str, Any]] = completed_tasks[
            instance_name
        ]
        episodes_metadata.extend(completed_episodes)
      if instance_name in failed_tasks:
        episodes_metadata.extend(failed_tasks[instance_name])
      already_processed = (
          instance_name in completed_tasks and instance_name not in failed_tasks
      )
      if already_processed:
        _log_and_print('Skipping already processed task %s', instance_name)
        continue

      episode = _run_task(instance, run_episode, env, demo_mode=demo_mode)
      if (
          episode.get(constants.EpisodeConstants.EXCEPTION_INFO) is None
          and check_episode_fn is not None
      ):
        if not check_episode_fn(episode):
          continue
      episode[constants.EpisodeConstants.AGENT_NAME] = agent_name
      episode[constants.EpisodeConstants.INSTANCE_ID] = i
      checkpointer.save_episodes([episode], instance_name)

      if return_full_episode_data:
        full_episode_data.append(episode)

      episodes_metadata.append({k: episode[k] for k in metadata_fields})
      process_episodes_fn(episodes_metadata, print_summary=True)

      if episode[constants.EpisodeConstants.EXCEPTION_INFO] is not None:
        # Don't include episode in tally if execution/eval logic errored out.
        continue
      correct += episode[constants.EpisodeConstants.IS_SUCCESSFUL]
      total += 1
      if demo_mode:
        _update_scoreboard(correct, total, env.controller)
    print()

  return full_episode_data if return_full_episode_data else episodes_metadata


def run(
    suite: Suite,
    agent: base_agent.EnvironmentInteractingAgent,
    checkpointer: checkpointer_lib.Checkpointer = checkpointer_lib.NullCheckpointer(),
    demo_mode: bool = False,
    return_full_episode_data: bool = False,
    process_episodes_fn=None,
    check_episode_fn: Callable[[dict[str, Any]], bool] | None = None,
) -> list[dict[str, Any]]:
  """Create suite and runs eval suite.

  Args:
    suite: The suite of tasks to run on.
    agent: An agent that interacts on the environment.
    checkpointer: Checkpointer that loads from existing run and resumes from
      there. NOTE: It will resume from the last fully completed task template.
      Relatedly, data for a task template will not be saved until all instances
      are executed.
    demo_mode: Whether to run in demo mode, which displays a scoreboard and the
      task instruction as a notification.
    return_full_episode_data: Whether to return full episode data instead of
      just metadata.
    process_episodes_fn: The function to process episode data. Usually to
      compute metrics. Deafaults to process_episodes from this file.
    check_episode_fn: The function to check episode data.

  Returns:
    Step-by-step data from each episode.
  """

  def run_episode(task: task_eval.TaskEval) -> episode_runner.EpisodeResult:
    if demo_mode:
      _display_goal(agent.env, task)
    return episode_runner.run_episode(
        goal=task.goal,
        agent=agent,
        max_n_steps=_allocate_step_budget(task.complexity),
        start_on_home_screen=task.start_on_home_screen,
        termination_fn=(
            miniwob_base.is_episode_terminated
            if task.name.lower().startswith('miniwob')
            else None
        ),
    )

  if demo_mode:
    adb_utils.send_android_intent(
        'broadcast',
        'com.example.ACTION_UPDATE_SCOREBOARD',
        agent.env.controller,
        extras={'player_name': agent.name, 'scoreboard_value': '00/00'},
    )

  results = _run_task_suite(
      suite,
      run_episode,
      agent.env,
      checkpointer=checkpointer,
      demo_mode=demo_mode,
      agent_name=agent.name,
      return_full_episode_data=return_full_episode_data,
      process_episodes_fn=process_episodes_fn,
      check_episode_fn=check_episode_fn,
  )

  return results


def _allocate_step_budget(task_complexity: float) -> int:
  """Allocates number of steps dynamically based on the complexity score.

  Args:
    task_complexity: Complexity score of the task.

  Returns:
    Allocated number of steps for the task.
  """
  if task_complexity is None:
    raise ValueError('Task complexity must be provided.')
  return int(10 * (task_complexity))


def _display_message(
    header: str, body: str, env: env_interface.AndroidEnvInterface
) -> None:
  adb_utils.send_android_intent(
      'broadcast',
      'com.example.ACTION_UPDATE_OVERLAY',
      env,
      extras={'task_type_string': header, 'goal_string': body},
  )


def _display_goal(env: interface.AsyncEnv, task: task_eval.TaskEval) -> None:
  """Displays the goal on the screen using Android World.

  Args:
    env: The environment.
    task: The current task.
  """
  adb_utils.launch_app('android world', env.controller)
  time.sleep(1.0)
  _display_message(task.goal, task.name, env.controller)
  time.sleep(6.0)
  adb_utils.press_home_button(env.controller)
  time.sleep(1.0)


def _get_screen_config(task: task_eval.TaskEval) -> dict[str, Any]:
  return {
      'width': task.width if hasattr(task, 'width') else 1080,
      'height': task.height if hasattr(task, 'height') else 2400,
      'orientation': (
          task.orientation if hasattr(task, 'orientation') else 'portrait'
      ),
      'config_name': (
          task.config_name if hasattr(task, 'config_name') else 'default'
      ),
  }


def _create_failed_result(
    name: str, goal: str, exception: str, run_time: float
) -> dict[str, Any]:
  """Creates empty result to use if the run fails for some reason."""
  return {
      constants.EpisodeConstants.GOAL: goal,
      constants.EpisodeConstants.TASK_TEMPLATE: name,
      constants.EpisodeConstants.EPISODE_DATA: np.nan,
      constants.EpisodeConstants.IS_SUCCESSFUL: np.nan,
      constants.EpisodeConstants.FINISH_DTIME: datetime.datetime.now(),
      constants.EpisodeConstants.RUN_TIME: run_time,
      constants.EpisodeConstants.EPISODE_LENGTH: np.nan,
      constants.EpisodeConstants.EXCEPTION_INFO: exception,
      constants.EpisodeConstants.AUX_DATA: None,
  }


def _display_success_overlay(
    env: env_interface.AndroidEnvInterface, success: float
) -> None:
  """Displays success overlay."""
  adb_utils.send_android_intent(
      'broadcast',
      'com.example.ACTION_UPDATE_OVERLAY',
      env,
      extras={'success_string': str(int(success))},
  )
  time.sleep(1.0)  # Let display linger.


def _update_scoreboard(
    n_correct: int, n: int, env: env_interface.AndroidEnvInterface
) -> None:
  """Updates the scoreboard."""
  percentage = (n_correct / n) * 100
  scoreboard_value = f'{n_correct}/{n} ({percentage:.1f}%)'

  adb_utils.send_android_intent(
      'broadcast',
      'com.example.ACTION_UPDATE_SCOREBOARD',
      env,
      extras={'scoreboard_value': scoreboard_value},
  )


def _extract_task_metadata() -> pd.DataFrame:
  """Extracts metadata from task_metadata.json."""
  name = 'task_metadata.json'
  filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
  df = pd.read_json(filepath)
  df.rename(columns={_TASK_TEMPLATE_COLUMN: _TASK_PROMPT_COLUMN}, inplace=True)
  df.rename(columns={'task_name': _TASK_TEMPLATE_COLUMN}, inplace=True)
  return df.set_index(_TASK_TEMPLATE_COLUMN)[
      ['difficulty', 'optimal_steps', 'tags']
  ]


def _print_results_by_tag(result_df: pd.DataFrame) -> None:
  exploded_df = result_df.explode('tags').reset_index()
  exploded_df.replace(regex={'tags': r''}, value='untagged', inplace=True)  # pytype: disable=wrong-arg-types
  return (
      exploded_df.groupby(['tags', 'difficulty'], as_index=False)
      .agg(
          num_tasks=(_TASK_TEMPLATE_COLUMN, 'count'),
          mean_success_rate=('mean_success_rate', 'mean'),
      )
      .pivot_table(
          index=['tags'],
          columns='difficulty',
          values=[
              'mean_success_rate',
          ],
      )
      .fillna('-')
      .reindex(columns=['easy', 'medium', 'hard'], level='difficulty')
  )


def process_episodes(
    episodes: list[dict[str, Any]], print_summary: bool = False
) -> pd.DataFrame:
  """Processes task suite results; i.e. the output from `run_task_suite`.

  results = run_task_suite(...)
  # Contents of results.
  results = [
    {
        'goal': 'Pause the stopwatch.',
        'task_template': 'ClockStopWatchPaused',
        'episode_data': ...,
        'is_successful': True
    },
    {
        'goal': 'Pause the stopwatch.',
        'task_template': 'ClockStopWatchPaused',
        'episode_data': ...,
        'is_successful': False
    },
    {
        'goal': 'Run the stopwatch.',
        'task_template': 'ClockStopWatchRunnin',
        'episode_data': ...,
        'is_successful': True
    },
    {
        'goal': 'Run the stopwatch.',
        'task_template': 'ClockStopWatchRunnin',
        'episode_data': ...,
        'is_successful': True
    }
  ]

  process_episodes(results)
  # Output:
  # | task_template               |   n_trials |   average_success_rate |
  # |:----------------------------|-----------:|-----------------------:|
  # | ClockStopWatchPausedVerify  |          2 |                   0.5  |
  # | ClockStopWatchRunning       |          2 |                   1    |
  # | ==========Average========== |          2 |                   0.75 |

  Args:
    episodes: Results from running `run_task_suite`.
    print_summary: Whether to print the dataframe with a summary row.

  Returns:
    A dataframe aggregating results of run.
  """

  df = pd.DataFrame(list(episodes))

  # Add exeception info for backwards compatibility.
  df = df.assign(**{
      constants.EpisodeConstants.EXCEPTION_INFO: df.get(
          constants.EpisodeConstants.EXCEPTION_INFO, np.nan
      )
  })

  result_df = df.groupby(
      constants.EpisodeConstants.TASK_TEMPLATE, dropna=True
  ).agg({
      constants.EpisodeConstants.IS_SUCCESSFUL: ['count', 'mean'],
      constants.EpisodeConstants.EPISODE_LENGTH: 'mean',
      constants.EpisodeConstants.RUN_TIME: 'sum',
      constants.EpisodeConstants.EXCEPTION_INFO: [
          ('none_count', lambda x: x.notnull().sum())
      ],
  })
  result_df = result_df.sort_index()
  result_df.columns = [
      'num_complete_trials',
      'mean_success_rate',
      'mean_episode_length',
      'total_runtime_s',
      'num_fail_trials',
  ]
  result_df['total_runtime_s'] = result_df['total_runtime_s'].map(
      lambda x: float('{:.1f}'.format(x))
  )

  # Extract metadata and merge with the results table.
  metadata_df = _extract_task_metadata()
  tagged_result_df = result_df.merge(
      metadata_df, on=[_TASK_TEMPLATE_COLUMN], how='left'
  )

  if print_summary:
    avg = result_df.mean(axis=0)
    avg.name = '========= Average ========='

    result = pd.concat([result_df, avg.to_frame().T])
    result.index.name = 'task'
    result.insert(0, 'task_num', list(range(len(result) - 1)) + [0])
    result.task_num = result.task_num.astype(int)
    pd.set_option('display.max_columns', 100)
    pd.set_option('display.max_rows', 1000)
    pd.set_option('display.width', 1000)
    _log_and_print('\n\n%s', result)  # Use lazy % formatting

    # Add a chart that shows mean success rate by tag and difficulty.
    tags_df = _print_results_by_tag(tagged_result_df)
    pd.set_option('display.precision', 2)
    _log_and_print('\n\n%s', tags_df)

  return tagged_result_df
```

### `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/state_pb2.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/state_pb2.py`

```python
# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: android_world/task_evals/information_retrieval/proto/state.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'android_world/task_evals/information_retrieval/proto/state.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n@android_world/task_evals/information_retrieval/proto/state.proto\x12\x34\x61ndroid_world.task_evals.information_retrieval.proto\"\xe5\x02\n\x05State\x12P\n\x08\x63\x61lendar\x18\x01 \x01(\x0b\x32>.android_world.task_evals.information_retrieval.proto.Calendar\x12Q\n\ttasks_app\x18\x02 \x01(\x0b\x32>.android_world.task_evals.information_retrieval.proto.TasksApp\x12\x64\n\x13sports_activity_app\x18\x03 \x01(\x0b\x32G.android_world.task_evals.information_retrieval.proto.SportsActivityApp\x12Q\n\tnotes_app\x18\x04 \x01(\x0b\x32>.android_world.task_evals.information_retrieval.proto.NotesApp\"U\n\x08NotesApp\x12I\n\x05notes\x18\x01 \x03(\x0b\x32:.android_world.task_evals.information_retrieval.proto.Note\"\\\n\x04Note\x12\x0e\n\x06\x66older\x18\x01 \x01(\t\x12\r\n\x05title\x18\x02 \x01(\t\x12\x0c\n\x04\x62ody\x18\x03 \x01(\t\x12\x0f\n\x07is_todo\x18\x04 \x01(\t\x12\x16\n\x0etodo_completed\x18\x05 \x01(\t\"t\n\x11SportsActivityApp\x12_\n\x11sports_activities\x18\x01 \x03(\x0b\x32\x44.android_world.task_evals.information_retrieval.proto.SportsActivity\"\xc7\x01\n\x0eSportsActivity\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x02 \x01(\t\x12\x10\n\x08\x63\x61tegory\x18\x03 \x01(\t\x12\x12\n\nstart_date\x18\x04 \x01(\t\x12\x12\n\nstart_time\x18\x05 \x01(\t\x12\x10\n\x08\x64uration\x18\x06 \x01(\t\x12\x16\n\x0etotal_distance\x18\x07 \x01(\t\x12\x16\n\x0e\x65levation_gain\x18\x08 \x01(\t\x12\x16\n\x0e\x65levation_loss\x18\t \x01(\t\"g\n\x08TasksApp\x12[\n\x0ftasks_app_tasks\x18\x01 \x03(\x0b\x32\x42.android_world.task_evals.information_retrieval.proto.TasksAppTask\"\xc6\x01\n\x0cTasksAppTask\x12\r\n\x05title\x18\x01 \x01(\t\x12\x12\n\nimportance\x18\x02 \x01(\t\x12\x10\n\x08\x64ue_date\x18\x03 \x01(\t\x12\x10\n\x08\x64ue_time\x18\x04 \x01(\t\x12\x17\n\x0fhide_until_date\x18\x05 \x01(\t\x12\x17\n\x0fhide_until_time\x18\x06 \x01(\t\x12\x16\n\x0e\x63ompleted_date\x18\x08 \x01(\t\x12\x16\n\x0e\x63ompleted_time\x18\t \x01(\t\x12\r\n\x05notes\x18\n \x01(\t\"i\n\x08\x43\x61lendar\x12\x10\n\x08\x61pp_name\x18\x02 \x01(\t\x12K\n\x06\x65vents\x18\x01 \x03(\x0b\x32;.android_world.task_evals.information_retrieval.proto.Event\"w\n\x05\x45vent\x12\x12\n\nstart_date\x18\x01 \x01(\t\x12\x12\n\nstart_time\x18\x02 \x01(\t\x12\x10\n\x08\x64uration\x18\x03 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x04 \x01(\t\x12\r\n\x05title\x18\x05 \x01(\t\x12\x10\n\x08location\x18\x06 \x01(\t')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'android_world.task_evals.information_retrieval.proto.state_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_STATE']._serialized_start=123
  _globals['_STATE']._serialized_end=480
  _globals['_NOTESAPP']._serialized_start=482
  _globals['_NOTESAPP']._serialized_end=567
  _globals['_NOTE']._serialized_start=569
  _globals['_NOTE']._serialized_end=661
  _globals['_SPORTSACTIVITYAPP']._serialized_start=663
  _globals['_SPORTSACTIVITYAPP']._serialized_end=779
  _globals['_SPORTSACTIVITY']._serialized_start=782
  _globals['_SPORTSACTIVITY']._serialized_end=981
  _globals['_TASKSAPP']._serialized_start=983
  _globals['_TASKSAPP']._serialized_end=1086
  _globals['_TASKSAPPTASK']._serialized_start=1089
  _globals['_TASKSAPPTASK']._serialized_end=1287
  _globals['_CALENDAR']._serialized_start=1289
  _globals['_CALENDAR']._serialized_end=1394
  _globals['_EVENT']._serialized_start=1396
  _globals['_EVENT']._serialized_end=1515
# @@protoc_insertion_point(module_scope)
```

### `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/task_pb2.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/task_pb2.py`

```python
# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: android_world/task_evals/information_retrieval/proto/task.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'android_world/task_evals/information_retrieval/proto/task.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from android_world.task_evals.information_retrieval.proto import state_pb2 as android__world_dot_task__evals_dot_information__retrieval_dot_proto_dot_state__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n?android_world/task_evals/information_retrieval/proto/task.proto\x12\x34\x61ndroid_world.task_evals.information_retrieval.proto\x1a@android_world/task_evals/information_retrieval/proto/state.proto\"R\n\x05Tasks\x12I\n\x05tasks\x18\x01 \x03(\x0b\x32:.android_world.task_evals.information_retrieval.proto.Task\"\xcd\x02\n\x04Task\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x12\n\ncomplexity\x18\x06 \x01(\x05\x12\x0e\n\x06prompt\x18\x02 \x01(\t\x12U\n\x0btask_params\x18\x03 \x03(\x0b\x32@.android_world.task_evals.information_retrieval.proto.TaskParams\x12[\n\x0erelevant_state\x18\x04 \x01(\x0b\x32\x43.android_world.task_evals.information_retrieval.proto.RelevantState\x12_\n\x10success_criteria\x18\x05 \x01(\x0b\x32\x45.android_world.task_evals.information_retrieval.proto.SuccessCriteria\"3\n\nTaskParams\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x17\n\x0fpossible_values\x18\x02 \x03(\t\"j\n\x0fSuccessCriteria\x12W\n\x0c\x65xpectations\x18\x01 \x03(\x0b\x32\x41.android_world.task_evals.information_retrieval.proto.Expectation\"\xd7\x01\n\x13\x46ieldTransformation\x12\x66\n\toperation\x18\x01 \x01(\x0e\x32S.android_world.task_evals.information_retrieval.proto.FieldTransformation.Operation\x12\x12\n\nfield_name\x18\x02 \x01(\t\"D\n\tOperation\x12\x15\n\x11OPERATION_UNKNOWN\x10\x00\x12\x07\n\x03SUM\x10\x01\x12\t\n\x05\x43OUNT\x10\x02\x12\x0c\n\x08IDENTITY\x10\x03\"\x82\x03\n\x0b\x45xpectation\x12i\n\x14\x66ield_transformation\x18\x01 \x01(\x0b\x32I.android_world.task_evals.information_retrieval.proto.FieldTransformationH\x00\x12\x18\n\x0e\x65xpected_value\x18\x02 \x01(\tH\x00\x12_\n\nmatch_type\x18\x03 \x01(\x0e\x32K.android_world.task_evals.information_retrieval.proto.Expectation.MatchType\x12\x11\n\ttolerance\x18\x04 \x01(\x02\"g\n\tMatchType\x12\x16\n\x12MATCH_TYPE_UNKNOWN\x10\x00\x12\x10\n\x0cSTRING_MATCH\x10\x01\x12\x10\n\x0cNUMBER_MATCH\x10\x02\x12\x0e\n\nDATE_MATCH\x10\x03\x12\x0e\n\nTIME_MATCH\x10\x04\x42\x11\n\x0f\x65xpected_answer\"\xc3\x01\n\rRelevantState\x12J\n\x05state\x18\x01 \x01(\x0b\x32;.android_world.task_evals.information_retrieval.proto.State\x12\x66\n\x14\x65xclusion_conditions\x18\x02 \x03(\x0b\x32H.android_world.task_evals.information_retrieval.proto.ExclusionCondition\"\xb4\x02\n\x12\x45xclusionCondition\x12\x65\n\toperation\x18\x01 \x01(\x0e\x32R.android_world.task_evals.information_retrieval.proto.ExclusionCondition.Operation\x12\r\n\x05\x66ield\x18\x02 \x01(\t\x12\r\n\x05value\x18\x03 \x01(\t\"\x98\x01\n\tOperation\x12\x15\n\x11OPERATION_UNKNOWN\x10\x00\x12\x0c\n\x08\x45QUAL_TO\x10\x01\x12\x0c\n\x08\x43ONTAINS\x10\x02\x12\x10\n\x0cGREATER_THAN\x10\x03\x12\r\n\tLESS_THAN\x10\x04\x12\x1c\n\x18GREATER_THAN_OR_EQUAL_TO\x10\x05\x12\x19\n\x15LESS_THAN_OR_EQUAL_TO\x10\x06')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'android_world.task_evals.information_retrieval.proto.task_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_TASKS']._serialized_start=187
  _globals['_TASKS']._serialized_end=269
  _globals['_TASK']._serialized_start=272
  _globals['_TASK']._serialized_end=605
  _globals['_TASKPARAMS']._serialized_start=607
  _globals['_TASKPARAMS']._serialized_end=658
  _globals['_SUCCESSCRITERIA']._serialized_start=660
  _globals['_SUCCESSCRITERIA']._serialized_end=766
  _globals['_FIELDTRANSFORMATION']._serialized_start=769
  _globals['_FIELDTRANSFORMATION']._serialized_end=984
  _globals['_FIELDTRANSFORMATION_OPERATION']._serialized_start=916
  _globals['_FIELDTRANSFORMATION_OPERATION']._serialized_end=984
  _globals['_EXPECTATION']._serialized_start=987
  _globals['_EXPECTATION']._serialized_end=1373
  _globals['_EXPECTATION_MATCHTYPE']._serialized_start=1251
  _globals['_EXPECTATION_MATCHTYPE']._serialized_end=1354
  _globals['_RELEVANTSTATE']._serialized_start=1376
  _globals['_RELEVANTSTATE']._serialized_end=1571
  _globals['_EXCLUSIONCONDITION']._serialized_start=1574
  _globals['_EXCLUSIONCONDITION']._serialized_end=1882
  _globals['_EXCLUSIONCONDITION_OPERATION']._serialized_start=1730
  _globals['_EXCLUSIONCONDITION_OPERATION']._serialized_end=1882
# @@protoc_insertion_point(module_scope)
```

### `official/install/android_world/env/__init__.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/__init__.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Android World environment package."""
```

### `official/install/android_world/env/actuation.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/actuation.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilies for actuation."""

import copy
import logging
import time
from typing import Any
from android_env import env_interface
from android_world.env import adb_utils
from android_world.env import android_world_controller
from android_world.env import json_action
from android_world.env import representation_utils


def execute_adb_action(
    action: json_action.JSONAction,
    screen_elements: list[Any],  # list[UIElement]
    screen_size: tuple[int, int],
    env: env_interface.AndroidEnvInterface,
) -> None:
  """Execute an action based on a JSONAction object.

  Args:
      action: JSONAction object containing the action to be executed.
      screen_elements: List of UI elements on the screen.
      screen_size: The (width, height) of the screen.
      env: The environment to execute the action in.
  """
  if action.action_type in ['click', 'double_tap', 'long_press']:
    idx = action.index
    x = action.x
    y = action.y
    if idx is not None:
      if idx < 0 or idx >= len(screen_elements):
        raise ValueError(
            f'Invalid element index: {idx}, must be between 0 and'
            f' {len(screen_elements)-1}.'
        )
      element = screen_elements[idx]
      if element.bbox_pixels is None:
        raise ValueError('Bbox is not present on element.')
      x, y = element.bbox_pixels.center
      x, y = int(x), int(y)
      if action.action_type == 'click':
        adb_utils.tap_screen(x, y, env)
      elif action.action_type == 'double_tap':
        adb_utils.double_tap(x, y, env)
      else:
        adb_utils.long_press(x, y, env)
    elif x is not None and y is not None:
      x, y = int(x), int(y)
      if action.action_type == 'click':
        adb_utils.tap_screen(x, y, env)
      elif action.action_type == 'double_tap':
        adb_utils.double_tap(x, y, env)
      else:
        adb_utils.long_press(x, y, env)
    else:
      raise ValueError(f'Invalid click action: {action}')

  elif action.action_type == 'input_text':
    text = action.text
    if text:
      if action.index is not None or (
          action.x is not None and action.y is not None
      ):
        # First focus on enter text UI element.
        click_action = copy.deepcopy(action)
        click_action.action_type = 'click'
        execute_adb_action(click_action, screen_elements, screen_size, env)
        time.sleep(1.0)

      if action.clear_text:
        # Select all existing text and delete it.
        adb_utils.issue_generic_request(
            [
                'shell',
                'input',
                'keycombination',
                '113',
                '29',
                '&&',
                'input',
                'keyevent',
                '67',
            ],
            env,
        )
        time.sleep(1.0)

      adb_utils.type_text(text, env, timeout_sec=10)
      adb_utils.press_enter_button(env)
    else:
      logging.warning(
          'Input_text action indicated, but no text provided. No '
          'action will be executed.'
      )

  elif action.action_type == 'keyboard_enter':
    adb_utils.press_enter_button(env)

  elif action.action_type == 'navigate_home':
    adb_utils.press_home_button(env)

  elif action.action_type == 'navigate_back':
    adb_utils.press_back_button(env)

  elif action.action_type == 'press_keyboard':
    adb_utils.press_keyboard_generic(action.keycode, env)
  elif action.action_type == 'drag_and_drop':
    if action.touch_xy is not None and action.lift_xy is not None:
      command = adb_utils.generate_drag_and_drop_command(
          action.touch_xy[0],
          action.touch_xy[1],
          action.lift_xy[0],
          action.lift_xy[1],
          4000,
      )
      adb_utils.issue_generic_request(command, env)
    else:
      logging.warning(
          'Drag and drop action indicated, but no coordinates provided. No '
          'action will be executed.'
      )
  elif action.action_type == 'scroll':

    screen_width, screen_height = screen_size
    if action.index:
      x_min, y_min, x_max, y_max = (
          max(screen_elements[action.index].bbox_pixels.x_min, 0),
          max(screen_elements[action.index].bbox_pixels.y_min, 0),
          min(screen_elements[action.index].bbox_pixels.x_max, screen_width),
          min(screen_elements[action.index].bbox_pixels.y_max, screen_height),
      )
    else:
      x_min, y_min, x_max, y_max = (0, 0, screen_width, screen_height)

    start_x, start_y = (x_min + x_max) // 2, (y_min + y_max) // 2
    direction = action.direction
    if direction == 'down':
      end_x, end_y = (x_min + x_max) // 2, y_min
    elif direction == 'up':
      end_x, end_y = (x_min + x_max) // 2, y_max
    elif direction == 'right':
      end_x, end_y = x_min, (y_min + y_max) // 2
    elif direction == 'left':
      end_x, end_y = x_max, (y_min + y_max) // 2
    else:
      print('Invalid direction')
      return
    command = adb_utils.generate_swipe_command(
        int(start_x), int(start_y), int(end_x), int(end_y)
    )
    adb_utils.issue_generic_request(command, env)

  elif action.action_type == 'swipe':  # Inverse of scroll.
    screen_width, screen_height = screen_size
    mid_x, mid_y = 0.5 * screen_width, 0.5 * screen_height
    direction = action.direction
    if direction == 'down':
      start_x, start_y = mid_x, 0
      end_x, end_y = mid_x, screen_height
    elif direction == 'up':
      start_x, start_y = mid_x, screen_height
      end_x, end_y = mid_x, 0
    elif direction == 'left':
      start_x, start_y = 0, mid_y
      end_x, end_y = screen_width, mid_y
    elif direction == 'right':
      start_x, start_y = screen_width, mid_y
      end_x, end_y = 0, mid_y
    else:
      print('Invalid direction')
      return
    command = adb_utils.generate_swipe_command(
        int(start_x), int(start_y), int(end_x), int(end_y), 500
    )
    adb_utils.issue_generic_request(command, env)

  elif action.action_type == 'open_app':
    app_name = action.app_name
    if app_name:
      adb_utils.launch_app(app_name, env)
    else:
      raise ValueError('No app name provided')

  elif action.action_type == 'wait':
    time.sleep(1.0)

  elif action.action_type == 'launch_adb_activity':
    if action.activity_nickname == 'app_drawer':
      adb_utils.press_home_button(env)
      time.sleep(1.0)
      start_x, start_y = int(screen_size[0] / 2), int(screen_size[1] * 0.9)
      end_x = start_x
      end_y = int(0.3 * screen_size[1])
      request = adb_utils.generate_swipe_command(start_x, start_y, end_x, end_y)
      adb_utils.issue_generic_request(request, env)
    elif action.activity_nickname == 'quick_settings':
      start_x, start_y = int(screen_size[0] / 2), 30
      end_x = start_x
      end_y = int(0.3 * screen_size[1])
      request = adb_utils.generate_swipe_command(
          start_x, start_y, end_x, end_y, duration_ms=10
      )
      adb_utils.issue_generic_request(request, env)
  elif action.action_type == 'change_orientation':
    adb_utils.change_orientation(action.orientation, env)
  elif action.action_type == json_action.UNKNOWN:
    print('Unknown action type; no action will be executed. Try again...')
  else:
    print('Invalid action type')


def find_and_click_element(
    element_text: str,
    env: android_world_controller.AndroidWorldController,
    case_sensitive: bool = False,
):
  """Identifies element with element_text and clicks it.

  Args:
    element_text: Text of the UI element to click on.
    env: The Android env instance.
    case_sensitive: Whether to use case sensitivity when determining which UI
      element to tap.
  """
  # Find text.
  action = _wait_and_find_click_element(element_text, env, case_sensitive)

  ui_elements = env.get_ui_elements()
  screen_size = (0, 0)  # Unused, but required.
  execute_adb_action(action, ui_elements, screen_size, env)


def _wait_and_find_click_element(
    target_text: str,
    env: android_world_controller.AndroidWorldController,
    case_sensitive: bool,
    dist_threshold: int = 1,  # Allow one character difference.
) -> json_action.JSONAction:
  """Wait for the screen to update until "element_text" appears."""
  ui_elements = env.get_ui_elements()
  element, distance = _find_target_element(
      ui_elements, target_text, case_sensitive
  )
  start = time.time()
  current = time.time()
  while current - start < 10:
    if distance <= dist_threshold:
      return json_action.JSONAction(action_type='click', index=element)
    ui_elements = env.get_ui_elements()
    element, distance = _find_target_element(
        ui_elements, target_text, case_sensitive
    )
    current = time.time()
  raise ValueError(f'Target text "{target_text}" not found.')


def _find_target_element(
    ui_elements: list[representation_utils.UIElement],
    target_text: str,
    case_sensitive: bool,
) -> tuple[int, int]:
  """Determine the UI element with the closest match to target_text, by looking at the `text` and `content_description` of each UI element."""
  best_match_index = -1
  lowest_distance = int(1e9)

  for i, element in enumerate(ui_elements):
    for attr in [element.text, element.content_description]:
      if attr is not None:
        if case_sensitive:
          distance = _levenshtein_distance(target_text, attr)
        else:
          distance = _levenshtein_distance(target_text.lower(), attr.lower())
        if distance < lowest_distance:
          lowest_distance = distance
          best_match_index = i

  return (best_match_index, lowest_distance)


def _levenshtein_distance(s1: str, s2: str) -> int:
  """Compute the Levenshtein distance between two strings."""
  if len(s1) < len(s2):
    s1, s2 = s2, s1

  if not s2:
    return len(s1)

  previous_row = range(len(s2) + 1)
  for i, c1 in enumerate(s1):
    current_row = [i + 1]
    for j, c2 in enumerate(s2):
      insertions = previous_row[j + 1] + 1
      deletions = current_row[j] + 1
      substitutions = previous_row[j] + (c1 != c2)
      current_row.append(min(insertions, deletions, substitutions))
    previous_row = current_row

  return previous_row[-1]
```

### `official/install/android_world/env/adb_utils.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/adb_utils.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilties to interact with the environment using adb."""

import json
import os
import re
import time
from typing import Any, Callable, Collection, Iterable, Literal, Optional, TypeVar
import unicodedata
from absl import logging
from android_env import env_interface
from android_env.components import errors
from android_env.proto import adb_pb2
import immutabledict

T = TypeVar('T')

_DEFAULT_TIMEOUT_SECS = 10

# pylint: disable=line-too-long
# Maps app names to the activity that should be launched to open the app.
_PATTERN_TO_ACTIVITY = immutabledict.immutabledict({
    'google chrome|chrome': (
        'com.android.chrome/com.google.android.apps.chrome.Main'
    ),
    'google chat': (
        'com.google.android.apps.dynamite/com.google.android.apps.dynamite.startup.StartUpActivity'
    ),
    'settings|system settings': 'com.android.settings/.Settings',
    'youtube|yt': (
        'com.google.android.youtube/com.google.android.apps.youtube.app.WatchWhileActivity'
    ),
    'google play|play store|gps': (
        'com.android.vending/com.google.android.finsky.activities.MainActivity'
    ),
    'gmail|gemail|google mail|google email|google mail client': (
        'com.google.android.gm/.ConversationListActivityGmail'
    ),
    'google maps|gmaps|maps|google map': (
        'com.google.android.apps.maps/com.google.android.maps.MapsActivity'
    ),
    'google photos|gphotos|photos|google photo|google pics|google images': (
        'com.google.android.apps.photos/com.google.android.apps.photos.home.HomeActivity'
    ),
    'google calendar|gcal': (
        'com.google.android.calendar/com.android.calendar.AllInOneActivity'
    ),
    'camera': 'com.android.camera2/com.android.camera.CameraLauncher',
    'audio recorder': (
        'com.dimowner.audiorecorder/com.dimowner.audiorecorder.app.welcome.WelcomeActivity'
    ),
    'google drive|gdrive|drive': (
        'com.google.android.apps.docs/.drive.startup.StartupActivity'
    ),
    'google keep|gkeep|keep': (
        'com.google.android.keep/.activities.BrowseActivity'
    ),
    'grubhub': (
        'com.grubhub.android/com.grubhub.dinerapp.android.splash.SplashActivity'
    ),
    'tripadvisor': (
        'com.tripadvisor.tripadvisor/com.tripadvisor.android.ui.launcher.LauncherActivity'
    ),
    'starbucks': 'com.starbucks.mobilecard/.main.activity.LandingPageActivity',
    'google docs|gdocs|docs': (
        'com.google.android.apps.docs.editors.docs/com.google.android.apps.docs.editors.homescreen.HomescreenActivity'
    ),
    'google sheets|gsheets|sheets': (
        'com.google.android.apps.docs.editors.sheets/com.google.android.apps.docs.editors.homescreen.HomescreenActivity'
    ),
    'google slides|gslides|slides': (
        'com.google.android.apps.docs.editors.slides/com.google.android.apps.docs.editors.homescreen.HomescreenActivity'
    ),
    'google voice|voice': (
        'com.google.android.apps.googlevoice/com.google.android.apps.googlevoice.SplashActivity'
    ),
    'clock': 'com.google.android.deskclock/com.android.deskclock.DeskClock',
    'google search|google': (
        'com.google.android.googlequicksearchbox/com.google.android.googlequicksearchbox.SearchActivity'
    ),
    'contacts': (
        'com.google.android.contacts/com.android.contacts.activities.PeopleActivity'
    ),
    'facebook|fb': 'com.facebook.katana/com.facebook.katana.LoginActivity',
    'whatsapp|wa': 'com.whatsapp/com.whatsapp.Main',
    'instagram|ig': (
        'com.instagram.android/com.instagram.mainactivity.MainActivity'
    ),
    'twitter|tweet': 'com.twitter.android/com.twitter.app.main.MainActivity',
    'snapchat|sc': 'com.snapchat.android/com.snap.mushroom.MainActivity',
    'telegram|tg': 'org.telegram.messenger/org.telegram.ui.LaunchActivity',
    'linkedin': (
        'com.linkedin.android/com.linkedin.android.authenticator.LaunchActivity'
    ),
    'spotify|spot': 'com.spotify.music/com.spotify.music.MainActivity',
    'netflix': (
        'com.netflix.mediaclient/com.netflix.mediaclient.ui.launch.UIWebViewActivity'
    ),
    'amazon shopping|amazon|amzn': (
        'com.amazon.mShop.android.shopping/com.amazon.mShop.home.HomeActivity'
    ),
    'tiktok|tt': (
        'com.zhiliaoapp.musically/com.ss.android.ugc.aweme.splash.SplashActivity'
    ),
    'discord': 'com.discord/com.discord.app.AppActivity$Main',
    'reddit': 'com.reddit.frontpage/com.reddit.frontpage.MainActivity',
    'pinterest': 'com.pinterest/com.pinterest.activity.PinterestActivity',
    'android world': 'com.example.androidworld/.MainActivity',
    'files': (
        'com.google.android.documentsui/com.android.documentsui.files.FilesActivity'
    ),
    'markor': 'net.gsantner.markor/net.gsantner.markor.activity.MainActivity',
    'clipper': 'ca.zgrs.clipper/ca.zgrs.clipper.Main',
    'messages': (
        'com.google.android.apps.messaging/com.google.android.apps.messaging.ui.ConversationListActivity'
    ),
    'simple sms messenger|simple sms': (
        'com.simplemobiletools.smsmessenger/com.simplemobiletools.smsmessenger.activities.MainActivity'
    ),
    'dialer|phone': (
        'com.google.android.dialer/com.google.android.dialer.extensions.GoogleDialtactsActivity'
    ),
    'simple calendar pro|simple calendar': (
        'com.simplemobiletools.calendar.pro/com.simplemobiletools.calendar.pro.activities.MainActivity'
    ),
    'simple gallery pro|simple gallery': (
        'com.simplemobiletools.gallery.pro/com.simplemobiletools.gallery.pro.activities.MainActivity'
    ),
    'miniwob': (
        'com.google.androidenv.miniwob/com.google.androidenv.miniwob.app.MainActivity'
    ),
    'simple draw pro': (
        'com.simplemobiletools.draw.pro/com.simplemobiletools.draw.pro.activities.MainActivity'
    ),
    'pro expense|pro expense app': (
        'com.arduia.expense/com.arduia.expense.ui.MainActivity'
    ),
    'broccoli|broccoli app|broccoli recipe app|recipe app': (
        'com.flauschcode.broccoli/com.flauschcode.broccoli.MainActivity'
    ),
    'caa|caa test|context aware access': (
        'com.google.ccc.hosted.contextawareaccess.thirdpartyapp/.ChooserActivity'
    ),
    'osmand': 'net.osmand/net.osmand.plus.activities.MapActivity',
    'tasks|tasks app|tasks.org:': (
        'org.tasks/com.todoroo.astrid.activity.MainActivity'
    ),
    'open tracks sports tracker|activity tracker|open tracks|opentracks': (
        'de.dennisguse.opentracks/de.dennisguse.opentracks.TrackListActivity'
    ),
    'joplin|joplin app': 'net.cozic.joplin/.MainActivity',
    'vlc|vlc app|vlc player': 'org.videolan.vlc/.gui.MainActivity',
    'retro music|retro|retro player': (
        'code.name.monkey.retromusic/.activities.MainActivity'
    ),
})
# pylint: enable=line-too-long

_ORIENTATIONS = {
    'portrait': '0',
    'landscape': '1',
    'portrait_reversed': '2',
    'landscape_reversed': '3',
}

# Special app names that will trigger opening the default app.
_DEFAULT_URIS: dict[str, str] = {
    'calendar': 'content://com.android.calendar',
    'browser': 'http://',
    'contacts': 'content://contacts/people/',
    'email': 'mailto:',
    'gallery': 'content://media/external/images/media/',
}


def check_ok(response: adb_pb2.AdbResponse, message=None) -> None:
  """Check an ADB response and raise RuntimeError if not OK.

  Args:
    response: AdbResponse to check.
    message: Error message to raise on non-ok response. If not specified, a
      generic "ADB command failed" error message is used.

  Raises:
    RuntimeError: If response status is not OK.
  """
  if response.status != adb_pb2.AdbResponse.Status.OK:
    if message is not None:
      raise RuntimeError(message)
    else:
      raise RuntimeError(
          f'ADB command failed with status {response.status}:'
          f' {response.generic.output.decode()}.'
      )


def start_activity(
    activity: str,
    extra_args: Optional[Collection[str]],
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Issues an AdbRequest to launch the given activity.

  Args:
    activity: The activity to launch in standard android_package/activity_name
      format.
    extra_args: Optional set of arguments to be issued with the ABD broadcast.
    env: The environment.
    timeout_sec: A timeout to use for this operation.

  Returns:
    The adb response received after issuing the request.
  """
  logging.info('Attempting to launch %r', activity)
  response = env.execute_adb_call(
      adb_pb2.AdbRequest(
          start_activity=adb_pb2.AdbRequest.StartActivity(
              full_activity=activity, extra_args=extra_args
          ),
          timeout_sec=timeout_sec,
      )
  )
  if response.status != adb_pb2.AdbResponse.Status.OK:
    logging.error('Failed to launch activity: %r', activity)
    return response

  logging.debug('Launch package output %r', response.generic.output)
  return response


def get_current_activity(
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = _DEFAULT_TIMEOUT_SECS,
) -> tuple[Optional[str], adb_pb2.AdbResponse]:
  """Returns the full activity name that is currently opened to the user.

  Args:
    env: The environment.
    timeout_sec: A timeout to use for this operation.

  Returns:
    A tuple (current_activity_name, adb_response) containing the string with
      the current activity or None if no current activity can be
      extracted, and the adb response received after issuing the request.
  """
  response = env.execute_adb_call(
      adb_pb2.AdbRequest(
          get_current_activity=adb_pb2.AdbRequest.GetCurrentActivity(),
          timeout_sec=timeout_sec,
      )
  )
  if response.status != adb_pb2.AdbResponse.Status.OK:
    logging.warning(
        'Failed to obtain visible task. error_message: %r',
        response.error_message,
    )
    return (None, response)

  activity = response.get_current_activity.full_activity
  return (activity, response)


def tap_screen(
    x: int,
    y: int,
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Issues an AdbRequest to tap the screen at the specified point.

  Args:
    x: X coordinate on the screen, in pixels.
    y: Y coordinate on the screen, in pixels.
    env: The environment.
    timeout_sec: A timeout to use for this operation.

  Returns:
    The adb response received after issuing the request.
  """
  logging.info('Attempting to tap the screen at (%d, %d)', x, y)
  response = env.execute_adb_call(
      adb_pb2.AdbRequest(
          tap=adb_pb2.AdbRequest.Tap(x=x, y=y), timeout_sec=timeout_sec
      )
  )

  if response.status != adb_pb2.AdbResponse.Status.OK:
    logging.error('Failed to tap the screen')

  return response


def double_tap(
    x: int,
    y: int,
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Issues two AdbRequests to double tap the screen at the specified point.

  Args:
    x: X coordinate on the screen, in pixels.
    y: Y coordinate on the screen, in pixels.
    env: The environment.
    timeout_sec: A timeout to use for this operation.

  Returns:
    The adb response received after issuing the second tap request.
  """
  logging.info('Attempting to double tap the screen at (%d, %d)', x, y)
  first_tap = tap_screen(x, y, env, timeout_sec=0)
  second_tap = tap_screen(x, y, env, timeout_sec=timeout_sec)
  logging.info('First tap: %s', first_tap)
  logging.info('Second tap: %s', second_tap)
  return second_tap


def long_press(
    x: int,
    y: int,
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Issues an AdbRequest to long press the screen at the specified point.

  Args:
    x: X coordinate on the screen, in pixels.
    y: Y coordinate on the screen, in pixels.
    env: The environment.
    timeout_sec: A timeout to use for this operation.

  Returns:
    The adb response received after issuing long press.
  """
  logging.info('Attempting to long press the screen at (%d, %d)', x, y)
  return issue_generic_request(
      ['shell', 'input', 'swipe', str(x), str(y), str(x), str(y), '1000'],
      env,
      timeout_sec,
  )


def press_home_button(
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Issues an AdbRequest to press the HOME button in the nav bar.

  Args:
    env: The environment.
    timeout_sec: A timeout to use for this operation.

  Returns:
    The adb response received after issuing the request.
  """
  logging.info('Attempting to press the HOME button')
  response = env.execute_adb_call(
      adb_pb2.AdbRequest(
          press_button=adb_pb2.AdbRequest.PressButton(
              button=adb_pb2.AdbRequest.PressButton.HOME
          ),
          timeout_sec=timeout_sec,
      )
  )

  if response.status != adb_pb2.AdbResponse.Status.OK:
    logging.error('Failed to press the HOME button')
  return response


def press_back_button(
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Issues an AdbRequest to press the BACK button in the nav bar.

  Args:
    env: The environment.
    timeout_sec: A timeout to use for this operation.

  Returns:
    The adb response received after issuing the request.
  """
  logging.info('Attemting to press the BACK button')
  response = env.execute_adb_call(
      adb_pb2.AdbRequest(
          press_button=adb_pb2.AdbRequest.PressButton(
              button=adb_pb2.AdbRequest.PressButton.BACK
          ),
          timeout_sec=timeout_sec,
      )
  )

  if response.status != adb_pb2.AdbResponse.Status.OK:
    logging.error('Failed to press the BACK button')

  return response


def press_enter_button(
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Issues an AdbRequest to press the ENTER button in the nav bar.

  Args:
    env: The environment.
    timeout_sec: A timeout to use for this operation.

  Returns:
    The adb response received after issuing the request.
  """
  logging.info('Attemting to press the ENTER button')
  response = env.execute_adb_call(
      adb_pb2.AdbRequest(
          press_button=adb_pb2.AdbRequest.PressButton(
              button=adb_pb2.AdbRequest.PressButton.ENTER
          ),
          timeout_sec=timeout_sec,
      )
  )

  if response.status != adb_pb2.AdbResponse.Status.OK:
    logging.error('Failed to press the ENTER button')

  return response


def press_keyboard_generic(
    keycode: str,
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Issues an AdbRequest to press any button in the keyboard.

  Args:
    keycode: The keycode to press.
    env: The environment.
    timeout_sec: A timeout to use for this operation.

  Returns:
    The adb response received after issuing the request.
  """
  logging.info('Attemting to press the keyboard button: %s', keycode)

  response = issue_generic_request(
      ['shell', 'input', 'keyevent', keycode],
      env,
      timeout_sec,
  )

  if response.status != adb_pb2.AdbResponse.Status.OK:
    logging.error('Failed to press the keyboard button: %s', keycode)

  return response


def _adb_text_format(text: str) -> str:
  """Prepares text for use with adb."""
  to_escape = [
      '\\',
      ';',
      '|',
      '`',
      '\r',
      ' ',
      "'",
      '"',
      '&',
      '<',
      '>',
      '(',
      ')',
      '#',
      '$',
  ]
  for char in to_escape:
    text = text.replace(char, '\\' + char)
  normalized_text = unicodedata.normalize('NFKD', text)
  return normalized_text.encode('ascii', 'ignore').decode('ascii')


def _split_words_and_newlines(text: str) -> Iterable[str]:
  """Split lines of text into individual words and newline chars."""
  lines = text.split('\n')
  for i, line in enumerate(lines):
    words = line.split(' ')
    for j, word in enumerate(words):
      if word:
        yield word
      if j < len(words) - 1:
        yield '%s'
    if i < len(lines) - 1:
      yield '\n'


def type_text(
    text: str,
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = _DEFAULT_TIMEOUT_SECS,
) -> None:
  """Issues an AdbRequest to type the specified text string word-by-word.

  It types word-by-word to fix issue where sometimes long text strings can be
  typed out of order at the character level. Additionally, long strings can time
  out and word-by-word fixes this, while allowing us to keep a lot timeout per
  word.

  Args:
    text: The text string to be typed.
    env: The environment.
    timeout_sec: A timeout to use for this operation. Note: For longer texts,
      this should be longer as it takes longer to type.
  """
  words = _split_words_and_newlines(text)
  for word in words:
    if word == '\n':
      logging.info('Found \\n, pressing enter button.')
      press_enter_button(env)
      continue
    formatted = _adb_text_format(word)
    logging.info('Attempting to type word: %r', formatted)
    response = env.execute_adb_call(
        adb_pb2.AdbRequest(
            input_text=adb_pb2.AdbRequest.InputText(text=formatted),
            timeout_sec=timeout_sec,
        )
    )

    if response.status != adb_pb2.AdbResponse.Status.OK:
      logging.error('Failed to type word: %r', formatted)


def issue_generic_request(
    args: Collection[str] | str,
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Issues a generic adb command.

  Example:
  ~~~~~~~

  issue_generic_request(['shell', 'ls'], env)
  # or
  issue_generic_request('shell ls', env)

  Args:
    args: Set of arguments to be issued with the ABD broadcast. Can also be a
      string.
    env: The environment.
    timeout_sec: A timeout to use for this operation.

  Returns:
    The adb response received after issuing the request.
  """
  if isinstance(args, str):
    args_str = args
    args = args.split(' ')
  else:
    args_str = ' '.join(args)

  response = env.execute_adb_call(
      adb_pb2.AdbRequest(
          generic=adb_pb2.AdbRequest.GenericRequest(args=args),
          timeout_sec=timeout_sec,
      )
  )
  if response.status != adb_pb2.AdbResponse.Status.OK:
    logging.error('Failed to issue generic adb request: %r', args_str)

  return response


def get_adb_activity(app_name: str) -> Optional[str]:
  """Get a mapping of regex patterns to ADB activities top Android apps."""
  for pattern, activity in _PATTERN_TO_ACTIVITY.items():
    if re.match(pattern.lower(), app_name.lower()):
      return activity


def get_all_package_names(
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = _DEFAULT_TIMEOUT_SECS,
) -> list[str]:
  """Returns all packages installed on the device.

  Args:
    env: The AndroidEnv interface.
    timeout_sec: A timeout to use for this operation.

  Returns:
    A list of installed package names.
  """
  response = env.execute_adb_call(
      adb_pb2.AdbRequest(
          package_manager=adb_pb2.AdbRequest.PackageManagerRequest(
              list=adb_pb2.AdbRequest.PackageManagerRequest.List(
                  packages=adb_pb2.AdbRequest.PackageManagerRequest.List.Packages()
              )
          ),
          timeout_sec=timeout_sec,
      )
  )
  if response.status != adb_pb2.AdbResponse.Status.OK:
    logging.error('Failed to issue package manager request.')

  package_names = list(response.package_manager.list.items)
  return package_names


def get_all_apps(
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = _DEFAULT_TIMEOUT_SECS,
) -> list[str]:
  """Returns all apps installed on the device.

  Note: the output list will not be exhaustive as it is currently based on a
  mapping we define, so any apps not included in that mapping will not be
  output here.

  Args:
    env: The AndroidEnv interface.
    timeout_sec: A timeout to use for this operation. If not set the default
      timeout will be used.

  Returns:
    A list of app names.
  """
  packages = get_all_package_names(env, timeout_sec)
  package_to_app = {
      v.split('/')[0]: k.split('|')[0] for k, v in _PATTERN_TO_ACTIVITY.items()
  }
  app_names = []
  for package in packages:
    if package in package_to_app:
      app_names.append(package_to_app[package])

  return app_names


def _launch_default_app(
    app_key: str,
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Launches a default application with a predefined data URI."""
  if app_key not in _DEFAULT_URIS:
    raise ValueError(
        f'Unrecognized app key: {app_key}. Must be one of'
        f' {list(_DEFAULT_URIS.keys())}'
    )
  data_uri = _DEFAULT_URIS[app_key]
  adb_command = [
      'shell',
      'am',
      'start',
      '-a',
      'android.intent.action.VIEW',
      '-d',
      data_uri,
  ]
  response = issue_generic_request(adb_command, env, timeout_sec)
  return response


def launch_app(
    app_name: str,
    env: env_interface.AndroidEnvInterface,
) -> Optional[str]:
  """Uses regex and ADB activity to try to launch an app.

  Args:
    app_name: The name of the app, as represented as a key in
      _PATTERN_TO_ACTIVITY.
    env: The environment.

  Returns:
    The name of the app that is launched.
  """

  if app_name in _DEFAULT_URIS:
    _launch_default_app(app_name, env)
    return app_name

  activity = get_adb_activity(app_name)
  if activity is None:
    #  If the app name is not in the mapping, assume it is a package name.
    response = issue_generic_request(
        ['shell', 'monkey', '-p', app_name, '1'], env, timeout_sec=5
    )
    logging.info('Launching app by package name, response: %r', response)
    return app_name
  start_activity(activity, extra_args=[], env=env, timeout_sec=5)
  return app_name


def extract_package_name(activity: str) -> str:
  """Extract the package name from the activity string."""
  return activity.split('/')[0]


def close_recents(env: env_interface.AndroidEnvInterface):
  """Closes all recent apps."""
  response = issue_generic_request('shell dumpsys activity recents', env)
  if response.status != adb_pb2.AdbResponse.Status.OK:
    return
  recents_ids = re.findall(r'id=(\d+)', response.generic.output.decode())
  for recents_id in recents_ids:
    issue_generic_request(['shell', 'am', 'stack', 'remove', recents_id], env)


def close_app(
    app_name: str,
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = _DEFAULT_TIMEOUT_SECS,
) -> Optional[str]:
  """Uses regex and ADB package name to try to directly close an app.

  Args:
    app_name: The name of the app, as represented as a key in
      _PATTERN_TO_ACTIVITY.
    env: The environment.
    timeout_sec: The timeout.

  Returns:
    The app name that is closed.
  """
  activity = get_adb_activity(app_name)
  if activity is None:
    logging.error('Failed to close app: %r', app_name)
    return None
  package_name = extract_package_name(activity)
  issue_generic_request(
      ['shell', 'am', 'force-stop', package_name], env, timeout_sec
  )
  return app_name


def generate_swipe_command(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration_ms: Optional[int] = None,
) -> list[str]:
  """Sends a swipe action to the simulator.

  Args:
    start_x: The x-coordinate of the start of the swipe.
    start_y: The y-coordinate of the start of the swipe.
    end_x: The x-coordinate of the end of the swipe.
    end_y: The y-coordinate of the end of the swipe.
    duration_ms: If given, the duration of time in milliseconds to take to
      complete the swipe. This value can differentiate a swipe from a fling.

  Returns:
    List of adb arguments.
  """
  duration_str = str(duration_ms) if duration_ms else ''
  return [
      'shell',
      'input',
      'swipe',
      str(start_x),
      str(start_y),
      str(end_x),
      str(end_y),
      duration_str,
  ]


def generate_drag_and_drop_command(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration_ms: Optional[int] = None,
) -> list[str]:
  """Sends a drag and drop action to the simulator.

  Args:
    start_x: The x-coordinate of the start of the drag and drop.
    start_y: The y-coordinate of the start of the drag and drop.
    end_x: The x-coordinate of the end of the drag and drop.
    end_y: The y-coordinate of the end of the drag and drop.
    duration_ms: If given, the duration of time in milliseconds to take to
      complete the drag and drop.

  Returns:
    List of adb arguments.
  """
  duration_str = str(duration_ms) if duration_ms else ''
  return [
      'shell',
      'input',
      'draganddrop',
      str(start_x),
      str(start_y),
      str(end_x),
      str(end_y),
      duration_str,
  ]


def send_android_intent(
    command: str,
    action: str,
    env: env_interface.AndroidEnvInterface,
    data_uri: str | None = None,
    mime_type: str | None = None,
    extras: dict[str, Any] | None = None,
    timeout_sec: int = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Sends an intent to Android device using adb.

  This is a low-level command for sending an intent with additional parameters.
  When these additional parameters are not necessary, consider instead using
  `adb_utils.start_activity()` or `env.execute_adb_call()` with
  `AdbRequest.StartActivity` or `AdbRequest.SendBroadcast`.

  Args:
    command: Either "start" for start activity intents or "broadcast" for
      broadcast intents.
    action: The broadcast action (e.g. "android.intent.action.VIEW").
    env: The environment to which the broadcast is sent.
    data_uri: Optional intent data URI (e.g. "content://contacts/people/1").
    mime_type: Optional mime type (e.g. "image/png").
    extras: Dictionary containing keys and values to be sent as extras.
    timeout_sec: The maximum time in seconds to wait for the broadcast to
      complete.

  Returns:
    AdbResponse object.
  """
  if command not in ['start', 'broadcast']:
    raise ValueError('Intent command must be either "start" or "broadcast"')

  adb_command = ['shell', 'am', command, '-a', action]

  if data_uri:
    adb_command.extend(['-d', f'"{data_uri}"'])

  if mime_type:
    adb_command.extend(['-t', f'"{mime_type}"'])

  if extras:
    for key, value in extras.items():
      if isinstance(value, tuple):
        type_override, value = value
        if type_override == 'str':
          adb_command.extend(['--es', key, f'"{value}"'])
        elif type_override == 'bool':
          adb_command.extend(['--ez', key, f'"{value}"'])
        elif type_override == 'int':
          adb_command.extend(['--ei', key, f'"{value}"'])
        elif type_override == 'long':  # long type only available via override.
          adb_command.extend(['--el', key, f'"{value}"'])
        elif type_override == 'float':
          adb_command.extend(['--ef', key, f'"{value}"'])
        elif type_override == 'string array':
          array_str = ','.join(value)
          adb_command.extend(['--esa', key, f'"{array_str}"'])
      elif isinstance(value, str):
        adb_command.extend(['--es', key, f'"{value}"'])
      elif isinstance(value, bool):
        adb_command.extend(['--ez', key, f'"{value}"'])
      elif isinstance(value, int):
        adb_command.extend(['--ei', key, f'"{value}"'])
      # long type only available via override above.
      elif isinstance(value, float):
        adb_command.extend(['--ef', key, f'"{value}"'])
      elif isinstance(value, list):
        array_str = ','.join(value)
        adb_command.extend(['--esa', key, f'"{array_str}"'])
      else:
        raise ValueError(f'Unrecognized extra type for {key}')

  return issue_generic_request(adb_command, env, timeout_sec)


def get_api_level(env: env_interface.AndroidEnvInterface) -> int:
  """Gets the API level of the device.

  Args:
    env: The environment.

  Returns:
    The API level.

  Raises:
    RuntimeError: If adb command does not successfully execute.
  """
  version = issue_generic_request(
      ['shell', 'getprop ro.build.version.sdk'], env
  )
  if version.status != adb_pb2.AdbResponse.Status.OK:
    raise RuntimeError('Failed to get API level.')
  return int(version.generic.output)


def _toggle_svc(
    service: str,
    on_or_off: Literal['on', 'off'],
    env: env_interface.AndroidEnvInterface,
) -> adb_pb2.AdbResponse:
  """Toggles a system service on or off using svc.

  Args:
    service: The name of the service to toggle.
    on_or_off: The state to set ('on' or 'off').
    env: The Android environment.

  Returns:
    adb status.

  Raises:
    ValueError: If invalid on_or_off is provided.
  """
  if on_or_off not in ('on', 'off'):
    raise ValueError('Must be one of on or off.')

  cmd = 'enable' if on_or_off == 'on' else 'disable'
  return issue_generic_request(['shell', 'svc', service, cmd], env)


def toggle_wifi(
    env: env_interface.AndroidEnvInterface, on_or_off: Literal['on', 'off']
) -> adb_pb2.AdbResponse:
  """Toggles wifi on or off.

  Args:
    env: The Android environment.
    on_or_off: Whether to turn it on or off.

  Returns:
    adb status.
  """
  return _toggle_svc('wifi', on_or_off, env)


def toggle_bluetooth(
    env: env_interface.AndroidEnvInterface, on_or_off: Literal['on', 'off']
) -> adb_pb2.AdbResponse:
  """Toggles Bluetooth on or off.

  Args:
    env: The Android environment.
    on_or_off: Whether to turn it on or off.

  Returns:
    adb status.
  """
  return _toggle_svc('bluetooth', on_or_off, env)


def set_brightness(
    max_or_min: str, env: env_interface.AndroidEnvInterface
) -> adb_pb2.AdbResponse:
  """Sets screen brightness to maximum or minimum.

  Args:
    max_or_min: Whether to set it to maximum or minimum.
    env: The environment.

  Returns:
    The adb status.

  Raises:
    ValueError: If invalid max_or_min is provided.
  """
  if max_or_min not in ('max', 'min'):
    raise ValueError('Must be one of max or min.')

  brightness_level = '255' if max_or_min == 'max' else '1'

  return issue_generic_request(
      [
          'shell',
          'settings',
          'put',
          'system',
          'screen_brightness',
          brightness_level,
      ],
      env,
  )


def clear_app_data(
    package_name: str, env: env_interface.AndroidEnvInterface
) -> adb_pb2.AdbResponse:
  """Clears all data for a given package.

  Args:
    package_name: The package name of the app whose data is to be cleared.
    env: The environment.

  Returns:
    adb status.
  """
  try:
    return issue_generic_request(['shell', 'pm', 'clear', package_name], env)
  except errors.AdbControllerError as exc:
    raise errors.AdbControllerError(
        f'Failed to clear app data for package {package_name}. Is the app'
        ' installed?'
    ) from exc


def toggle_airplane_mode(
    on_or_off: Literal['on', 'off'], env: env_interface.AndroidEnvInterface
) -> adb_pb2.AdbResponse:
  """Toggles airplane mode on or off.

  Args:
    on_or_off: Whether to turn it on or off.
    env: The Android environment.

  Returns:
    adb status.

  Raises:
    ValueError: If invalid on_or_off is provided.
  """
  if on_or_off not in ('on', 'off'):
    raise ValueError('Must be one of on or off.')
  state = '1' if on_or_off == 'on' else '0'
  return issue_generic_request(
      ['shell', 'settings', 'put', 'global', 'airplane_mode_on', state], env
  )


def install_apk(
    apk_location: str, env: env_interface.AndroidEnvInterface
) -> None:
  """Installs Android World APK.

  Args:
    apk_location: Location of apk.
    env: The environment.

  Raises:
    ValueError: If apk location does not exist.
  """
  if not os.path.exists(apk_location):
    raise ValueError('APK does not exist.')
  issue_generic_request(['install', apk_location], env, timeout_sec=30.0)


def check_airplane_mode(env: env_interface.AndroidEnvInterface) -> bool:
  """Checks if airplane mode is enabled.

  Args:
    env: The Android environment.

  Returns:
    True if airplane mode is enabled, False otherwise.

  Raises:
    RuntimeError: If cannot execute airplane mode check.
  """
  response = issue_generic_request(
      ['shell', 'settings', 'get', 'global', 'airplane_mode_on'], env
  )

  if response.status != adb_pb2.AdbResponse.Status.OK:
    raise RuntimeError(
        f'ADB command failed with status {response.status}:'
        f' {response.generic.output.decode()}.'
    )

  return response.generic.output.decode().replace('\r', '').strip('\n') == '1'


def extract_broadcast_data(raw_output: str) -> Optional[str]:
  """Extracts the data from an adb broadcast command output.

  Args:
    raw_output: The adb command output.

  Returns:
    Extracted data as a string, or None if the result is 0.
  """
  if 'Broadcast completed: result=-1, data=' in raw_output:
    return raw_output.split('data=')[1].strip('"\r\n')
  elif 'Broadcast completed: result=0' in raw_output:
    return None
  else:
    raise ValueError(f'Unexpected broadcast output: {raw_output}')


def _extract_clipper_output(raw_output: str) -> str:
  """Parses the clipper output from the adb command.

  Args:
    raw_output: The adb command output.

  Returns:
    The clipboard content as a string.

  Raises:
    RuntimeError: If the adb command does not successfully execute or if the
      app is not in the foreground.
  """
  parsed_data = extract_broadcast_data(raw_output)
  if parsed_data is not None:
    return parsed_data
  else:
    raise RuntimeError(
        'Clipper app must be in the foreground to access clipboard. '
        'Additionally, app privileges must be granted manually by opening the '
        'clipper app and granting them.'
    )


def get_clipboard_contents(env: env_interface.AndroidEnvInterface) -> str:
  """Gets the clipboard content from the Android device.

  Args:
    env: The environment.

  Returns:
    The clipboard content as a string.

  Raises:
    RuntimeError: If the adb command does not successfully execute or if the
      app is not in the foreground.
  """
  if launch_app('clipper', env) is None:
    raise RuntimeError(
        'Clipper app must be in the foreground to access clipboard. You may'
        ' need to install clipper app.'
    )

  time.sleep(0.5)
  res = issue_generic_request(
      ['shell', 'am', 'broadcast', '-a', 'clipper.get'], env
  )

  if res.status != adb_pb2.AdbResponse.Status.OK:
    raise RuntimeError('Failed to get clipboard content.')

  output_str = res.generic.output.decode('utf-8')
  result = _extract_clipper_output(output_str)

  press_back_button(env)
  return result


def change_orientation(
    orientation: str, env: env_interface.AndroidEnvInterface
) -> None:
  """Changes the screen orientation.

  Args:
    orientation: str, The new orientation. Can be portrait, landscape,
      reverse_portrait, or reverse_landscape.
    env: The environment.

  Raises:
    ValueError if invalid orientation is provided.
  """
  if orientation not in _ORIENTATIONS:
    raise ValueError(
        f'Unknown orientation provided: {orientation} not in'
        f' {_ORIENTATIONS.keys()}'
    )
  command = [
      'shell',
      'settings',
      'put',
      'system',
  ]
  # Turn off accelerometer.
  issue_generic_request(command + ['accelerometer_rotation', '0'], env)
  issue_generic_request(
      command + ['user_rotation', _ORIENTATIONS[orientation]], env
  )


def set_clipboard_contents(
    content: str, env: env_interface.AndroidEnvInterface
) -> None:
  """Sets the clipboard content on the Android device.

  NOTE: If using an Emulator, the contents of your clipboard on your local
  machine may transfer to the emulator when focused on the emulator. Thus the
  result of this function can be overwritten just by switching windows.

  Args:
    content: Content to put into clipboard.
    env: The environment.

  Raises:
    RuntimeError: If the adb command does not successfully execute or if the
    app is not in the foreground.
  """
  if launch_app('clipper', env) is None:
    raise RuntimeError(
        'Clipper app must be in the foreground to access clipboard. You may'
        ' need to install clipper app.'
    )

  time.sleep(0.5)
  content = _adb_text_format(content)
  output_str = issue_generic_request(
      ['shell', 'am', 'broadcast', '-a', 'clipper.set', '-e', 'text', content],
      env,
  ).generic.output.decode('utf-8')
  _extract_clipper_output(output_str)
  press_back_button(env)


def grant_permissions(
    activity_name: str,
    permission: str,
    env: env_interface.AndroidEnvInterface,
) -> None:
  """Grants permissions on an activity.

  This is useful because it prevents pop-ups prompting user/agent for
  permission.

  See https://developer.android.com/reference/android/Manifest.permission for
  available permissions to grant.

  Args:
    activity_name: The name of the activity.
    permission: The permission to grant.
    env: The AndroidEnv instance.
  """
  issue_generic_request(
      ['shell', 'pm', 'grant', activity_name, permission],
      env,
  )


def execute_sql_command(
    db_path: str,
    sql_command: str,
    env: env_interface.AndroidEnvInterface,
) -> adb_pb2.AdbResponse:
  """Execute an arbitrary SQL command on a SQLite database file via ADB.

  Args:
    db_path: The path to the SQLite database on the Android device.
    sql_command: The SQL command to execute.
    env: The environment.

  Returns:
    The adb response received after issuing the request.
  """
  set_root_if_needed(env)
  adb_command = ['shell', f'sqlite3 {db_path} "{sql_command}"']
  adb_response = issue_generic_request(adb_command, env)
  return adb_response


def get_call_state(
    env: env_interface.AndroidEnvInterface,
    timeout_sec: float = _DEFAULT_TIMEOUT_SECS,
) -> str:
  """Query the call state and the dialed number of the phone through ADB.

  Args:
    env: The Android environment interface.
    timeout_sec: A timeout for the ADB operation.

  Returns:
    A tuple containing the call state as a string and the dialed number as a
    string.
  """
  adb_args = ['shell', 'dumpsys', 'telephony.registry']
  response = issue_generic_request(adb_args, env, timeout_sec)

  output = response.generic.output.decode('utf-8')
  state_match = re.search(r'mCallState=(\d)', output)

  state = 'UNKNOWN'

  if state_match:
    state_code = state_match.group(1)
    if state_code == '0':
      state = 'IDLE'
    elif state_code == '1':
      state = 'RINGING'
    elif state_code == '2':
      state = 'OFFHOOK'

  return state


def call_emulator(
    env: env_interface.AndroidEnvInterface,
    phone_number: str,
    timeout_sec: float = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Simulate an incoming call in an emulator using ADB.

  Args:
    env: The Android environment interface.
    phone_number: The incoming phone number.
    timeout_sec: A timeout for the ADB operation.

  Returns:
    adb_pb2.AdbResponse: A response object containing the ADB operation result.
  """
  escaped_phone_number = re.sub(r'[^0-9+]', '', phone_number)
  adb_args = ['emu', 'gsm', 'call', f'{escaped_phone_number}']
  response = issue_generic_request(adb_args, env, timeout_sec)
  return response


def end_call_if_active(
    env: 'env_interface.AndroidEnvInterface',
    timeout_sec: float = _DEFAULT_TIMEOUT_SECS,
) -> None:
  """Ends phone call if on an active call."""
  current_state = get_call_state(env, timeout_sec)

  # This check is crucial. Otherwise pressing endcall key results in black
  # screen, potentially because it's simulating turning display off?
  if current_state in ('OFFHOOK', 'RINGING'):
    adb_args = ['shell', 'input', 'keyevent', 'KEYCODE_ENDCALL']
    issue_generic_request(adb_args, env, timeout_sec)


def clear_android_emulator_call_log(
    env: env_interface.AndroidEnvInterface,
    timeout_sec: float = _DEFAULT_TIMEOUT_SECS,
) -> None:
  """Clears the call log of a specific Android emulator using the Android environment interface.

  Args:
    env: The Android environment interface.
    timeout_sec: A timeout for the ADB operation.
  """
  adb_args = ['shell', 'content', 'delete', '--uri', 'content://call_log/calls']
  issue_generic_request(adb_args, env, timeout_sec)


def call_phone_number(
    env: env_interface.AndroidEnvInterface,
    phone_number: str,
    timeout_sec: float = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Initiate a phone call using ADB.

  Args:
    env: The Android environment interface.
    phone_number: The phone number to dial.
    timeout_sec: A timeout for the ADB operation.

  Returns:
    A response object containing the ADB operation result.
  """
  escaped_phone_number = re.sub(r'[^0-9]', '', phone_number)
  adb_args = [
      'shell',
      'am',
      'start',
      '-a',
      'android.intent.action.CALL',
      '-d',
      f'tel:{escaped_phone_number}',
  ]
  return issue_generic_request(adb_args, env, timeout_sec)


def text_emulator(
    env: env_interface.AndroidEnvInterface,
    phone_number: str,
    message: str,
    timeout_sec: float = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Simulate an incoming text message in an emulator using ADB.

  Args:
    env: The Android environment interface.
    phone_number: The sender's phone number.
    message: The text message content.
    timeout_sec: A timeout for the ADB operation.

  Returns:
    A response object containing the ADB operation result.
  """
  escaped_phone_number = re.sub(r'[^0-9+]', '', phone_number)
  adb_args = [
      'emu',
      'sms',
      'send',
      f'{escaped_phone_number}',
      f'{message}',
  ]
  response = issue_generic_request(adb_args, env, timeout_sec)
  return response


def set_default_app(
    setting_key: str,
    package_name: str,
    env: env_interface.AndroidEnvInterface,
    timeout_sec: float = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Set the default application for a given type using ADB.

  Args:
    setting_key: The setting key for the default application type (e.g.,
      'sms_default_application').
    package_name: The package name of the application to be set as default.
    env: The Android environment interface.
    timeout_sec: A timeout for the ADB operation.

  Returns:
    A response object containing the ADB operation result.
  """
  adb_args = ['shell', 'settings', 'put', 'secure', setting_key, package_name]
  response = issue_generic_request(adb_args, env, timeout_sec)
  return response


def disable_headsup_notifications(
    env: env_interface.AndroidEnvInterface,
    timeout_sec: float = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Disables the heads up notifications.

  Args:
    env: The Android environment interface.
    timeout_sec: A timeout for the ADB operation.

  Returns:
    A response object containing the ADB operation result.
  """
  adb_args = [
      'shell',
      'settings',
      'put',
      'global',
      'heads_up_notifications_enabled',
      '0',
  ]
  response = issue_generic_request(adb_args, env, timeout_sec)
  return response


def enable_headsup_notifications(
    env: env_interface.AndroidEnvInterface,
    timeout_sec: float = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Enables the heads up notifications.

  Args:
    env: The Android environment interface.
    timeout_sec: A timeout for the ADB operation.

  Returns:
    A response object containing the ADB operation result.
  """
  adb_args = [
      'shell',
      'settings',
      'put',
      'global',
      'heads_up_notifications_enabled',
      '1',
  ]
  response = issue_generic_request(adb_args, env, timeout_sec)
  return response


def put_settings(
    namespace: adb_pb2.AdbRequest.SettingsRequest.Namespace,
    key: str,
    value: str,
    env: env_interface.AndroidEnvInterface,
) -> adb_pb2.AdbResponse:
  """Change a setting in the Android system via ADB.

  Args:
    namespace: The namespace in which the setting resides (SYSTEM, SECURE,
      GLOBAL).
    key: The key of the setting to change.
    value: The new value for the setting.
    env: The Android environment interface.

  Returns:
    The adb response received after issuing the request.
  """
  if not key:
    raise ValueError('Key must be provided.')
  if not value:
    raise ValueError('Value must be provided.')
  settings_request = adb_pb2.AdbRequest.SettingsRequest(
      name_space=namespace,
      put=adb_pb2.AdbRequest.SettingsRequest.Put(key=key, value=value),
  )
  adb_request = adb_pb2.AdbRequest(settings=settings_request)
  return env.execute_adb_call(adb_request)


def _post_process_settings(settings: dict[str, str]) -> dict[str, Any]:
  """Post process settings to remove non-deterministic fields."""

  # Remove theme timestamp
  theme_key = 'theme_customization_overlay_packages'
  if theme_key in settings:
    theme = json.loads(settings[theme_key])
    theme.pop('_applied_timestamp')
    settings[theme_key] = theme

  # Remove zen_duration
  settings.pop('zen_duration')

  return settings


def get_all_settings(env: env_interface.AndroidEnvInterface) -> dict[str, str]:
  """Get all settings from the Android system via ADB."""
  adb_commands = [
      'shell settings list secure',
      'shell settings list global',
      'shell settings list system',
  ]
  settings = {}
  for adb_command in adb_commands:
    response = issue_generic_request(adb_command, env)
    lines = response.generic.output.decode().split('\n')
    for line in lines:
      if not line:
        continue
      key, value = line.split('=', 1)
      settings[key] = value
  return _post_process_settings(settings)


def delete_contacts(
    env: env_interface.AndroidEnvInterface,
    timeout_sec: float = _DEFAULT_TIMEOUT_SECS,
) -> adb_pb2.AdbResponse:
  """Deletes all contacts.

  Args:
    env: The Android environment interface.
    timeout_sec: A timeout for the ADB operation.

  Returns:
    A response object containing the ADB operation result.
  """
  adb_args = [
      'shell',
      'pm',
      'clear',
      'com.android.providers.contacts',
  ]
  response = issue_generic_request(adb_args, env, timeout_sec)
  return response


def _parse_screen_size_response(response: str) -> tuple[int, int]:
  """Parse the adb response to extract screen size.

  Args:
    response: The adb response string.

  Returns:
    The screen width and height in pixels.
  """
  match = re.search(r'Physical size: (\d+)x(\d+)', response)
  if match:
    width, height = map(int, match.groups())
    return width, height
  else:
    raise ValueError(
        f'Screen size information not found in adb response: "{response}"'
    )


def get_screen_size(env: env_interface.AndroidEnvInterface) -> tuple[int, int]:
  """Get the screen size in pixels of an Android device via ADB.

  Args:
    env: The environment.

  Returns:
    The screen width and height in pixels.
  """
  adb_command = ['shell', 'wm size']
  adb_response = issue_generic_request(adb_command, env)
  return _parse_screen_size_response(
      adb_response.generic.output.decode('utf-8')
  )


def get_logical_screen_size(
    env: env_interface.AndroidEnvInterface,
) -> tuple[int, int]:
  """Returns the logical screen size.

  The logical screen size is the screen size that applications use to render
  their interfaces which might be different than the physical screen size when
  orientation/resolution changes. The coordinates we get from A11y tree are
  based on the logical screen size.

  Args:
    env: The AndroidEnv interface.

  Returns:
    The logical screen size in (width, height).
  """
  response = issue_generic_request(
      'shell dumpsys input | grep logicalFrame', env
  )
  if response.status:
    raw_output = response.generic.output.decode('utf-8')
    pattern = r'logicalFrame=\[0, 0, (\d+), (\d+)\]'
    matches = re.findall(pattern, raw_output)
    for m in matches:
      if int(m[0]) == 0 and int(m[1]) == 0:
        continue
      width, height = (int(m[0]), int(m[1]))
      return (width, height)
  raise ValueError('Failed to get logical screen size.')


def get_physical_frame_boundary(
    env: env_interface.AndroidEnvInterface,
) -> tuple[int, int, int, int]:
  """Returns the physical frame boundary.

  Args:
    env: The AndroidEnv interface.

  Returns:
    First two integers are the coordinates for top left corner, last two are for
    lower right corner. All coordinates are given in portrait orientation.
  """
  response = issue_generic_request(
      'shell dumpsys input | grep physicalFrame', env
  )
  if response.status:
    raw_output = response.generic.output.decode('utf-8')
    pattern = r'physicalFrame=\[(\d+), (\d+), (\d+), (\d+)\]'
    matches = re.findall(pattern, raw_output)
    for m in matches:
      if (
          int(m[0]) == 0
          and int(m[1]) == 0
          and int(m[2]) == 0
          and int(m[3]) == 0
      ):
        continue
      orientation = get_orientation(env)
      if orientation == 0 or orientation == 2:
        return (int(m[0]), int(m[1]), int(m[2]), int(m[3]))
      return (int(m[1]), int(m[0]), int(m[3]), int(m[2]))
  raise ValueError('Failed to get physical frame boundary.')


def get_orientation(
    env: env_interface.AndroidEnvInterface,
) -> int:
  """Returns the current screen orientation.

  The returned value follows the normal convention, 0 for portrait, 1 for
  landscape, 2 for reverse portrait, 3 for reverse landscape.

  Args:
    env: The AndroidEnv interface.

  Returns:
    The screen orientation.
  """
  response = issue_generic_request(
      'shell dumpsys window | grep mCurrentRotation', env
  )
  if response.status:
    raw_output = response.generic.output.decode('utf-8')
    pattern = r'mCurrentRotation=ROTATION_(\d+)'
    matches = re.findall(pattern, raw_output)
    for m in matches:
      return int(m) // 90
  raise ValueError('Failed to get orientation.')


def set_screen_size(
    width: int,
    height: int,
    env: env_interface.AndroidEnvInterface,
) -> adb_pb2.AdbResponse:
  """Sets the (logical) screen size (resolution) of the Android device via ADB.

  Args:
    width: The desired screen width.
    height: The desired screen height.
    env: The AndroidEnv interface.

  Returns:
    The adb response received after issuing the request.
  """
  # Command will fail if width equals height.
  if width <= 0 or height <= 0 or width == height:
    raise ValueError(
        'Screen size not valid (need to be positive, width can not equal'
        ' height).'
    )
  # Construct the ADB command for setting screen size
  adb_command = ['shell', f'wm size {width}x{height}']

  # Issue the command and return the response
  return issue_generic_request(adb_command, env)


def retry(n: int) -> Callable[[Any], Any]:
  """Decorator to retry ADB commands."""

  def decorator(func: Callable[..., T]) -> Callable[..., T]:
    def wrapper(*args: Any, **kwargs: Any) -> T:
      attempts = 0
      while attempts < n:
        try:
          return func(*args, **kwargs)
        except errors.AdbControllerError:
          attempts += 1
          if attempts >= n:
            raise
          print(f'Could not execute {func}. Retrying...')
          time.sleep(2)
        except Exception as exc:
          raise exc

    return wrapper

  return decorator


def set_root_if_needed(
    env: env_interface.AndroidEnvInterface, timeout_sec: Optional[float] = None
) -> adb_pb2.AdbResponse:
  """Checks if ADB is running as root, and if not, attempts to set root.

  Args:
      env: The environment.
      timeout_sec: A timeout to use for this operation.

  Returns:
      bool: True if root is set (or was already set), False otherwise.
  """
  response = issue_generic_request(['shell', 'whoami'], env, timeout_sec)

  if response.generic.output.decode('utf-8').strip() == 'root':
    return response

  return issue_generic_request(['root'], env, timeout_sec)


def uiautomator_dump(env, timeout_sec: Optional[float] = 30) -> str:
  """Issues a uiautomator dump request and returns the UI hierarchy."""
  dump_args = 'shell uiautomator dump /sdcard/window_dump.xml'
  issue_generic_request(dump_args, env, timeout_sec=timeout_sec)

  read_args = 'shell cat /sdcard/window_dump.xml'
  response = issue_generic_request(read_args, env, timeout_sec=timeout_sec)

  return response.generic.output.decode('utf-8')
```

### `official/install/android_world/env/android_world_controller.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/android_world_controller.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Controller for Android that adds UI tree information to the observation."""

import contextlib
import enum
import os
import time
from typing import Any
from typing import cast
from typing import Optional
from absl import logging
from android_env import env_interface
from android_env import loader
from android_env.components import config_classes
from android_env.proto.a11y import android_accessibility_forest_pb2
from android_env.wrappers import a11y_grpc_wrapper
from android_env.wrappers import base_wrapper
from android_world.env import adb_utils
from android_world.env import representation_utils
from android_world.utils import file_utils
import dm_env


def _has_wrapper(
    env: env_interface.AndroidEnvInterface,
    target_wrapper: Any,
) -> bool:
  """Checks recursively if an environment object has a certain wrapper.

  Args:
    env: The environment object potentially wrapped.
    target_wrapper: The wrapper type to search for.

  Returns:
    True if the target_wrapper is found, otherwise False.
  """
  if isinstance(env, target_wrapper):
    return True
  elif hasattr(env, '_env'):
    return _has_wrapper(env._env, target_wrapper)  # pylint: disable=protected-access
  else:
    return False


def get_a11y_tree(
    env: env_interface.AndroidEnvInterface,
    max_retries: int = 5,
    sleep_duration: float = 1.0,
) -> android_accessibility_forest_pb2.AndroidAccessibilityForest:
  """Gets a11y tree.

  Args:
    env: AndroidEnv.
    max_retries: Maximum number of retries to get a11y tree.
    sleep_duration: Time to sleep between each retry in seconds.

  Returns:
    A11y tree.

  Raises:
    RuntimeError: If the a11y tree was not able to be retrieved.
  """
  if not _has_wrapper(env, a11y_grpc_wrapper.A11yGrpcWrapper):
    raise ValueError(
        'Must use a11y_grpc_wrapper.A11yGrpcWrapper to get the a11y tree.'
    )
  env = cast(a11y_grpc_wrapper.A11yGrpcWrapper, env)
  if adb_utils.retry(3)(adb_utils.check_airplane_mode)(env):
    logging.warning(
        'Airplane mode is on -- cannot retrieve a11y tree via gRPC. Turning'
        ' it off...'
    )
    logging.info('Enabling networking...')
    env.attempt_enable_networking()
    time.sleep(1.0)

  forest: Optional[
      android_accessibility_forest_pb2.AndroidAccessibilityForest
  ] = None
  for _ in range(max_retries):
    try:
      forest = env.accumulate_new_extras()['accessibility_tree'][-1]  # pytype:disable=attribute-error
      return forest
    except KeyError:
      logging.warning('Could not get a11y tree, retrying.')
    time.sleep(sleep_duration)

  if forest is None:
    raise RuntimeError('Could not get a11y tree.')
  return forest


_TASK_PATH = file_utils.convert_to_posix_path(
    file_utils.get_local_tmp_directory(), 'default.textproto'
)
DEFAULT_ADB_PATH = '~/Android/Sdk/platform-tools/adb'


# UI tree-specific keys that are added to observations:

# The forest is essentially a comprehensive snapshot of all user interface
# elements currently displayed on an Android device's screen. Each 'tree' in
# this 'forest' represents the accessibility details of a different window or
# screen section, providing structured information. The tree's origin is from
# the AccessibilityService. Please see the following for more detail:
# https://developer.android.com/reference/android/accessibilityservice/AccessibilityService

OBSERVATION_KEY_FOREST = 'forest'
# UI elements are specific nodes extracted from forest. See
# representation_utils.forest_to_ui_elements for details.
OBSERVATION_KEY_UI_ELEMENTS = 'ui_elements'


class A11yMethod(enum.Enum):
  """Method to get a11y tree."""

  # Custom gRPC wrapper that uses a11y forwarder app.
  A11Y_FORWARDER_APP = 'a11y_forwarder_app'

  # From `uiautomator dump``.
  UIAUTOMATOR = 'uiautomator'

  # No A11y tree retrieval
  NONE = 'none'


def apply_a11y_forwarder_app_wrapper(
    env: env_interface.AndroidEnvInterface, install_a11y_forwarding_app: bool
) -> env_interface.AndroidEnvInterface:
  return a11y_grpc_wrapper.A11yGrpcWrapper(
      env,
      install_a11y_forwarding=install_a11y_forwarding_app,
      start_a11y_service=True,
      enable_a11y_tree_info=True,
      latest_a11y_info_only=True,
  )


class AndroidWorldController(base_wrapper.BaseWrapper):
  """Controller for an Android instance that adds accessibility tree data.

  The Accessibility Tree in Android is a tree-based structure, originally for
  for assisting accessibility services. It provides information about UI
  elements (like text, buttons, and images) in a hierarchical format. The tree
  includes details such as the properties and actions available for each
  element.
  """

  def __init__(
      self,
      env: env_interface.AndroidEnvInterface,
      a11y_method: A11yMethod = A11yMethod.A11Y_FORWARDER_APP,
      install_a11y_forwarding_app: bool = True,
  ):
    self._original_env = env
    if a11y_method == A11yMethod.A11Y_FORWARDER_APP:
      self._env = apply_a11y_forwarder_app_wrapper(
          env, install_a11y_forwarding_app
      )
      self._env.reset()  # Initializes required server services in a11y wrapper.
    else:
      self._env = env
    self._a11y_method = a11y_method

  @property
  def device_screen_size(self) -> tuple[int, int]:
    """Returns the physical screen size of the device: (width, height)."""
    return adb_utils.get_screen_size(self._env)

  @property
  def logical_screen_size(self) -> tuple[int, int]:
    """Returns the logical screen size of the device.

    This will be different with the physical size if orientation or resolution
    is changed.
    """
    return adb_utils.get_logical_screen_size(self._env)

  @property
  def env(self) -> env_interface.AndroidEnvInterface:
    return self._env

  def refresh_env(self):
    # pylint: disable=protected-access
    # pytype: disable=attribute-error
    # Reconnect to emulator and reload a11y wrapper in case we lose connection.
    self._env = get_controller(
        console_port=self.env._coordinator._simulator._config.emulator_launcher.emulator_console_port,
        adb_path=self.env._coordinator._simulator._config.adb_controller.adb_path,
        grpc_port=self.env._coordinator._simulator._config.emulator_launcher.grpc_port,
    ).env
    # pylint: enable=protected-access
    # pytype: enable=attribute-error

  def _get_a11y_forest(
      self,
  ) -> android_accessibility_forest_pb2.AndroidAccessibilityForest:
    return get_a11y_tree(self._env)

  def get_a11y_forest(
      self,
  ) -> android_accessibility_forest_pb2.AndroidAccessibilityForest:
    """Returns the most recent a11y forest from the device."""
    try:
      return self._get_a11y_forest()
    except RuntimeError:
      print(
          'Could not get a11y tree. Reconnecting to Android, reinitializing'
          ' AndroidEnv, and restarting a11y forwarding.'
      )
      self.refresh_env()
      return self._get_a11y_forest()

  def get_ui_elements(self) -> list[representation_utils.UIElement]:
    """Returns the most recent UI elements from the device."""
    if self._a11y_method == A11yMethod.A11Y_FORWARDER_APP:
      return representation_utils.forest_to_ui_elements(
          self.get_a11y_forest(),
          exclude_invisible_elements=True,
      )
    elif self._a11y_method == A11yMethod.UIAUTOMATOR:
      return representation_utils.xml_dump_to_ui_elements(
          adb_utils.uiautomator_dump(self._env)
      )
    else:
      return []

  def _process_timestep(self, timestep: dm_env.TimeStep) -> dm_env.TimeStep:
    """Adds a11y tree info to the observation."""
    if self._a11y_method == A11yMethod.A11Y_FORWARDER_APP:
      forest = self.get_a11y_forest()
      ui_elements = representation_utils.forest_to_ui_elements(
          forest,
          exclude_invisible_elements=True,
      )
    else:
      forest = None
      ui_elements = self.get_ui_elements()
    timestep.observation[OBSERVATION_KEY_FOREST] = forest
    timestep.observation[OBSERVATION_KEY_UI_ELEMENTS] = ui_elements
    return timestep

  def pull_file(
      self, remote_db_file_path: str, timeout_sec: Optional[float] = None
  ) -> contextlib._GeneratorContextManager[str]:
    """Pulls a file from the device to a temporary directory.

    The directory will be deleted when the context manager exits.
    Args:
      remote_db_file_path: The path to the file on the device.
      timeout_sec: Timeout in seconds for the adb calls.

    Returns:
      The path to the temporary directory containing the file.
    """
    remote_db_directory = os.path.dirname(remote_db_file_path)
    return file_utils.tmp_directory_from_device(
        remote_db_directory, self.env, timeout_sec
    )

  def push_file(
      self,
      local_db_file_path: str,
      remote_db_file_path: str,
      timeout_sec: Optional[float] = None,
  ) -> None:
    """Pushes a local file to the device."""

    remote_db_directory = os.path.dirname(remote_db_file_path)

    # First delete old .db, .db-wal, and .db-shm files.
    file_utils.clear_directory(remote_db_directory, self)
    file_utils.copy_data_to_device(
        local_db_file_path,
        remote_db_file_path,
        self.env,
        timeout_sec,
    )


def _write_default_task_proto() -> str:
  with open(_TASK_PATH, 'w') as f:
    f.write("""\
id: "default"

name: "Default task for device control."
description: "Empty task"

max_episode_sec: 7200  # Prevent infinite episodes.
  """)
  return _TASK_PATH


def get_controller(
    console_port: int = 5554,
    adb_path: str = DEFAULT_ADB_PATH,
    grpc_port: int = 8554,
) -> AndroidWorldController:
  """Creates a controller by connecting to an existing Android environment."""

  config = config_classes.AndroidEnvConfig(
      task=config_classes.FilesystemTaskConfig(
          path=_write_default_task_proto()
      ),
      simulator=config_classes.EmulatorConfig(
          emulator_launcher=config_classes.EmulatorLauncherConfig(
              emulator_console_port=console_port,
              adb_port=console_port + 1,
              grpc_port=grpc_port,
          ),
          adb_controller=config_classes.AdbControllerConfig(adb_path=adb_path),
      ),
  )
  android_env_instance = loader.load(config)
  logging.info('Setting up AndroidWorldController.')
  return AndroidWorldController(android_env_instance)
```

### `official/install/android_world/env/device_constants.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/device_constants.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Constants for the Pixel 6, API 33, emulator."""

import datetime

# Screen dimensions of Pixel 6.
SCREEN_HEIGHT, SCREEN_WIDTH = 2400, 1080

# Where data on emulator is stored.
EMULATOR_DATA = "/storage/emulated/0/"

# Location where app snapshots are stored.
SNAPSHOT_DATA = "/data/data/android_world/snapshots"

# keep-sorted start
AUDIORECORDER_DATA = "/storage/emulated/0/Android/data/com.dimowner.audiorecorder/files/Music/records"
DOWNLOAD_DATA = "/storage/emulated/0/Download"
GALLERY_DATA = "/sdcard/DCIM"
MARKOR_DATA = "/storage/emulated/0/Documents/Markor"
MUSIC_DATA = "/sdcard/Music"
OSMAND_DATA = "/storage/emulated/0/Android/data/net.osmand/files"
PHOTOS_DATA = "/sdcard/Pictures"
VIDEOS_DATA = "/sdcard/Movies"
# keep-sorted end

# Every task starts October 15, 2023 @ 15:34:00.
TIMEZONE = "UTC"
DT = datetime.datetime(2023, 10, 15, 15, 34, 0, tzinfo=datetime.timezone.utc)

# Format the datetime object into the Android date-time format
ANDROID_DT = DT.strftime("%m%d%H%M%y.%S")
```

### `official/install/android_world/env/interface.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/interface.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Environment interface for real-time interaction Android."""

import abc
import dataclasses
import time
from typing import Any, Optional, Self

from absl import logging
from android_env.components import action_type
from android_world.env import actuation
from android_world.env import adb_utils
from android_world.env import android_world_controller
from android_world.env import json_action
from android_world.env import representation_utils
import dm_env
import numpy as np


def _get_no_op_action() -> dict[str, Any]:
  """Creates a no-op action; used to retrieve screen & UI tree."""
  return {
      'action_type': np.array(action_type.ActionType.LIFT, dtype=np.int32),
      'touch_position': np.array((0.0, 0.0)),
  }


@dataclasses.dataclass(frozen=True)
class State:
  """State of the Android environment.

  Attributes:
    pixels: RGB array of current screen.
    forest: Raw UI forest; see android_world_controller.py for more info.
    ui_elements: Processed children and stateful UI elements extracted from
      forest.
    auxiliaries: Additional information about the state.
  """

  pixels: np.ndarray
  forest: Any
  ui_elements: list[representation_utils.UIElement]
  auxiliaries: dict[str, Any] | None = None

  @classmethod
  def create_and_infer_elements(
      cls,
      pixels: np.ndarray,
      forest: Any,
      screen_size: Optional[tuple[int, int]] = None,
  ) -> Self:
    """Creates a new instance, inferring UI elements from the forest."""

    elements = representation_utils.forest_to_ui_elements(
        forest, screen_size=screen_size
    )
    return cls(pixels, forest, elements)


class AsyncEnv(abc.ABC):
  """Interface for interacting with a real-time Android device.

  Computing environments, such as Android, run in real-time, independently of
  the agent interacting with it. All observations and actions are asynchronous
  and OS does not pause when providing observations or when accepting actions.
  Changes from action execution may take some time to appear.
  """

  @property
  @abc.abstractmethod
  def controller(self) -> android_world_controller.AndroidWorldController:
    """Returns the controller for the environment."""

  @abc.abstractmethod
  def reset(self, go_home: bool = False) -> State:
    """Go home on reset.

    Args:
      go_home: Whether to go home during the reset.
    """

  @abc.abstractmethod
  def get_state(self, wait_to_stabilize: bool = False) -> State:
    """Gets the state of the environment; i.e., screenshot & UI tree.

    In practice this will usually be called after executing an action. Logic
    should be implemented, perhaps a simple time.sleep, to ensure the
    environment updates after the action.

    Args:
      wait_to_stabilize: Whether to wait for the screen to stabilize before
        returning state.

    Returns:
      Observation containing RGB array of screen, the accessibility forest,
        and UI elements derived from the forest. See android_world_controller.py
        for
        more detail.
    """

  def display_message(self, message: str, header: str = '') -> None:
    """Displays a message on the screen."""

  @abc.abstractmethod
  def ask_question(
      self, question: str, timeout_seconds: float = -1.0
  ) -> str | None:
    """Asks a question to a hypothetical user in the environment.

    Common uses are to ask a question to clarify the user-provided goal, to ask
    for help when the agent is stuck, or when there is ambiguity in the current
    screen.

    Args:
      question: The question to ask the user.
      timeout_seconds: The timeout in seconds to wait for a response. If
        negative, then wait indefinitely.

    Returns:
      The response from the user or None if the user did not answer within the
      timeout.
    """

  @abc.abstractmethod
  def execute_action(self, action: json_action.JSONAction) -> None:
    """Executes action on the environment."""

  @property
  @abc.abstractmethod
  def foreground_activity_name(self) -> str:
    """Returns the activity name of the app currently opened in foreground."""

  @property
  @abc.abstractmethod
  def device_screen_size(self) -> tuple[int, int]:
    """Returns the screen size of the environment in pixels: (width, height)."""

  @property
  @abc.abstractmethod
  def logical_screen_size(self) -> tuple[int, int]:
    """Retrieves the logical screen size of the Android device.

    While the physical size is a fixed attribute of the display, the logical
    size is flexible and varies based on system settings such as the orientation
    or if the resolution is changed.

    Returns: The (width, height) in pixels, denoting the logical dimensions of
    the screen. Width and height values are aligned with the device's current
    orientation, meaning width is always logical horizontal direction (like in
    the landscape orientation width will be the physical vertical direction).
    """

  @abc.abstractmethod
  def close(self) -> None:
    """Closes the environment."""

  @property
  @abc.abstractmethod
  def interaction_cache(self) -> str:
    """Returns the interaction cache of the environment."""

  @abc.abstractmethod
  def hide_automation_ui(self) -> None:
    """Hides any UI, such as screen coordinates,."""

  @property
  @abc.abstractmethod
  def orientation(self) -> int:
    """Returns the orientation of the environment.

    Returns: 0 for portrait, 1 for landscape, 2 for reverse portrait,
    3 for reverse landscape.
    """

  @property
  @abc.abstractmethod
  def physical_frame_boundary(self) -> tuple[int, int, int, int]:
    """Returns the physical frame boundary of the environment.

    Returns: First two integers are the coordinates for top left corner, last
    two are for lower right corner. All coordinates are given in portrait
    orientation.
    """


def _process_timestep(timestep: dm_env.TimeStep) -> State:
  """Parses timestep observation and returns State."""
  return State(
      pixels=timestep.observation['pixels'],
      forest=timestep.observation[
          android_world_controller.OBSERVATION_KEY_FOREST
      ],
      ui_elements=timestep.observation[
          android_world_controller.OBSERVATION_KEY_UI_ELEMENTS
      ],
      auxiliaries={},
  )


class AsyncAndroidEnv(AsyncEnv):
  """Async environment interface using AndroidEnv to communicate with device."""

  interaction_cache = ''

  def __init__(
      self, controller: android_world_controller.AndroidWorldController
  ):
    self._controller = controller
    self._prior_state = None
    # Variable used to temporarily save interactions between agent and user.
    # Like when agent use answer action to answer user questions, we
    # use this to save the agent response. Or later on when agent has the
    # ability to ask user question, user's answer will be saved here as well.
    self.interaction_cache = ''

  @property
  def controller(self) -> android_world_controller.AndroidWorldController:
    return self._controller

  def reset(self, go_home: bool = False) -> State:
    if go_home:
      adb_utils.press_home_button(self.controller)
    self.interaction_cache = ''

    return _process_timestep(self.controller.reset())

  def _get_state(self):
    return _process_timestep(self.controller.step(_get_no_op_action()))

  def _get_stable_state(
      self,
      stability_threshold: int = 3,
      sleep_duration: float = 0.5,
      timeout: float = 6.0,
  ) -> State:
    """Checks if the UI elements remain stable over a number of checks and returns the state.

    Args:
        stability_threshold: Number of consecutive checks where UI elements must
          remain the same to consider UI stable.
        sleep_duration: Minimum time in seconds between each check.
        timeout: Maximum time in seconds to wait for UI to become stable before
          giving up.

    Returns:
        The current state of the UI if stability is achieved within the timeout.
    """
    if not self._prior_state:
      self._prior_state = self._get_state()
    if stability_threshold <= 0:
      raise ValueError('Stability threshold must be a positive integer.')

    stable_checks = 1
    start_time = time.time()
    deadline = start_time + timeout

    while stable_checks < stability_threshold and time.time() < deadline:
      iteration_start_time = time.time()
      current_state = self._get_state()

      if self._prior_state.ui_elements == current_state.ui_elements:
        stable_checks += 1
        if stable_checks == stability_threshold:
          break  # Exit early if stability is achieved.
      else:
        stable_checks = 1  # Reset if any change is detected
        self._prior_state = current_state

      elapsed_time = time.time() - iteration_start_time
      remaining_sleep = sleep_duration - elapsed_time
      if remaining_sleep > 0:
        sleep_time = min(remaining_sleep, deadline - time.time())
        if sleep_time > 0:
          time.sleep(sleep_time)
      # If remaining_sleep <= 0, proceed immediately to the next iteration

    return current_state  # pylint: disable=undefined-variable

  def get_state(self, wait_to_stabilize: bool = False) -> State:
    if wait_to_stabilize:
      return self._get_stable_state()
    return self._get_state()

  def execute_action(self, action: json_action.JSONAction) -> None:
    if action.action_type == json_action.ANSWER:
      self.interaction_cache = action.text
      if action.text:
        self.display_message(action.text, header='Agent answered:')
      return
    if action.action_type == json_action.STATUS:
      # Do nothing if it is a termination action.
      return
    state = self.get_state(wait_to_stabilize=False)
    actuation.execute_adb_action(
        action,
        state.ui_elements,
        self.logical_screen_size,
        self.controller,
    )

  def hide_automation_ui(self) -> None:
    """Hides the coordinates on screen."""
    adb_utils.issue_generic_request(
        'shell settings put system pointer_location 0', self.controller
    )

  def display_message(self, message: str, header: str = '') -> None:
    adb_utils.send_android_intent(
        command='broadcast',
        action='com.example.ACTION_UPDATE_OVERLAY',
        env=self.controller,
        extras={'task_type_string': header, 'goal_string': message},
    )

  def ask_question(
      self, question: str, timeout_seconds: float = -1.0
  ) -> str | None:
    raise NotImplementedError('ask_question is not implemented.')

  @property
  def foreground_activity_name(self) -> str:
    activity = adb_utils.get_current_activity(self.controller)[0]
    if activity:
      return activity
    else:
      return ''

  @property
  def device_screen_size(self) -> tuple[int, int]:
    return self.controller.device_screen_size

  @property
  def logical_screen_size(self) -> tuple[int, int]:
    return adb_utils.get_logical_screen_size(self.controller)

  def close(self) -> None:
    try:
      self.controller.close()
    except:  # pylint: disable=bare-except
      logging.warning('Failed to close controller. Continuing.')

  @property
  def orientation(self) -> int:
    return adb_utils.get_orientation(self.controller)

  @property
  def physical_frame_boundary(self) -> tuple[int, int, int, int]:
    return adb_utils.get_physical_frame_boundary(self.controller)
```

### `official/install/android_world/env/json_action.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/json_action.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Represents an action for Android interaction, parsed from a JSON format."""

import dataclasses
import json
from typing import Any, Optional


_JSON_SEPARATORS = (',', ':')

ANSWER = 'answer'
CLICK = 'click'
DOUBLE_TAP = 'double_tap'
INPUT_TEXT = 'input_text'
KEYBOARD_ENTER = 'keyboard_enter'
LONG_PRESS = 'long_press'
NAVIGATE_BACK = 'navigate_back'
NAVIGATE_HOME = 'navigate_home'
OPEN_APP = 'open_app'
SCROLL = 'scroll'
STATUS = 'status'
SWIPE = 'swipe'
UNKNOWN = 'unknown'
WAIT = 'wait'

_ACTION_TYPES = (
    CLICK,
    DOUBLE_TAP,
    SCROLL,
    SWIPE,
    INPUT_TEXT,
    NAVIGATE_HOME,
    NAVIGATE_BACK,
    KEYBOARD_ENTER,
    OPEN_APP,
    STATUS,
    WAIT,
    LONG_PRESS,
    ANSWER,
    UNKNOWN,
)

_SCROLL_DIRECTIONS = ('left', 'right', 'down', 'up')

# Keys of JSON action.
ACTION_TYPE = 'action_type'
INDEX = 'index'
X = 'x'
Y = 'y'
TEXT = 'text'
DIRECTION = 'direction'
APP_NAME = 'app_name'
GOAL_STATUS = 'goal_status'

ACTION_KEYS = [
    ACTION_TYPE,
    INDEX,
    X,
    Y,
    TEXT,
    DIRECTION,
    APP_NAME,
    GOAL_STATUS,
]


@dataclasses.dataclass()
class JSONAction:
  """Represents a parsed JSON action.

  # Example
  result_json = {'action_type': 'click', 'x': %d, 'y': %d}
  action = JSONAction(**result_json)

  Attributes:
    action_type: The action type.
    index: The index to click, if action is a click. Either an index or a <x, y>
      should be provided. See x, y attributes below.
    x: The x position to click, if the action is a click.
    y: The y position to click, if the action is a click.
    text: The text to type, if action is type.
    direction: The direction to scroll, if action is scroll.
    goal_status: If the status is a 'status' type, indicates the status of the
      goal.
    app_name: The app name to launch, if the action type is 'open_app'.
    keycode: Keycode actions are necessary for an agent to interact with complex
      UI elements (like large textareas) that can't be accessed or controlled by
      simply taping, ensuring precise control over navigation and selection in
      the interface.
    clear_text: Whether to clear the text field before typing.
  """

  action_type: Optional[str] = None
  index: Optional[str | int] = None
  x: Optional[int] = None
  y: Optional[int] = None
  text: Optional[str] = None
  direction: Optional[str] = None
  goal_status: Optional[str] = None
  app_name: Optional[str] = None
  keycode: Optional[str] = None
  clear_text: Optional[bool] = None

  def __post_init__(self):
    if self.action_type not in _ACTION_TYPES:
      raise ValueError(f'Invalid action type: {self.action_type}')
    if self.index is not None:
      self.index = int(self.index)
      if self.x is not None or self.y is not None:
        raise ValueError('Either an index or a <x, y> should be provided.')
    if self.direction and self.direction not in _SCROLL_DIRECTIONS:
      raise ValueError(f'Invalid scroll direction: {self.direction}')
    if self.text is not None and not isinstance(self.text, str):
      self.text = str(self.text)
    if self.keycode is not None and not self.keycode.startswith('KEYCODE_'):
      raise ValueError(f'Invalid keycode: {self.keycode}')

  def __repr__(self) -> str:
    properties = []
    for key, value in self.as_dict(skip_none=True).items():
      if isinstance(value, float):
        value = f'{value:.3f}'
      properties.append(f'{key}={value!r}')
    return f"JSONAction({', '.join(properties)})"

  def __eq__(self, other):
    if isinstance(other, JSONAction):
      return _compare_actions(self, other)
    return False

  def __ne__(self, other):
    return not self.__eq__(other)

  def as_dict(self, skip_none: bool = True) -> dict[str, Any]:
    """Returns a dict representation of the action.

    Args:
      skip_none: Whether to skip none values.

    Returns:
      A dict representation of the action.
    """
    non_null = {}
    for key, value in self.__dict__.items():
      if value is not None:
        if skip_none and value is None:
          continue
        non_null[key] = value
    return non_null

  def json_str(self) -> str:
    non_null = self.as_dict(skip_none=True)
    return json.dumps(non_null, separators=_JSON_SEPARATORS)


def _compare_actions(a: JSONAction, b: JSONAction) -> bool:
  """Compares two JSONActions.

  Args:
    a: The first action.
    b: The second action.

  Returns:
    If the actions are equal.
  """
  # Ignore cases.
  if a.app_name is not None and b.app_name is not None:
    app_name_match = a.app_name.lower() == b.app_name.lower()
  else:
    app_name_match = a.app_name == b.app_name

  if a.text is not None and b.text is not None:
    text_match = a.text.lower() == b.text.lower()
  else:
    text_match = a.text == b.text

  # Compare the non-metadata fields.
  return (
      app_name_match
      and text_match
      and a.action_type == b.action_type
      and a.index == b.index
      and a.x == b.x
      and a.y == b.y
      and a.keycode == b.keycode
      and a.direction == b.direction
      and a.goal_status == b.goal_status
  )
```

### `official/install/android_world/env/representation_utils.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/representation_utils.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tools for processing and representing accessibility trees."""

import dataclasses
from typing import Any, Optional
import xml.etree.ElementTree as ET
from android_env.proto.a11y import android_accessibility_forest_pb2


@dataclasses.dataclass
class BoundingBox:
  """Class for representing a bounding box."""

  x_min: float | int
  x_max: float | int
  y_min: float | int
  y_max: float | int

  @property
  def center(self) -> tuple[float, float]:
    """Gets center of bounding box."""
    return (self.x_min + self.x_max) / 2.0, (self.y_min + self.y_max) / 2.0

  @property
  def width(self) -> float | int:
    """Gets width of bounding box."""
    return self.x_max - self.x_min

  @property
  def height(self) -> float | int:
    """Gets height of bounding box."""
    return self.y_max - self.y_min

  @property
  def area(self) -> float | int:
    return self.width * self.height


@dataclasses.dataclass
class UIElement:
  """Represents a UI element."""

  text: Optional[str] = None
  content_description: Optional[str] = None
  class_name: Optional[str] = None
  bbox: Optional[BoundingBox] = None
  bbox_pixels: Optional[BoundingBox] = None
  hint_text: Optional[str] = None
  is_checked: Optional[bool] = None
  is_checkable: Optional[bool] = None
  is_clickable: Optional[bool] = None
  is_editable: Optional[bool] = None
  is_enabled: Optional[bool] = None
  is_focused: Optional[bool] = None
  is_focusable: Optional[bool] = None
  is_long_clickable: Optional[bool] = None
  is_scrollable: Optional[bool] = None
  is_selected: Optional[bool] = None
  is_visible: Optional[bool] = None
  package_name: Optional[str] = None
  resource_name: Optional[str] = None
  tooltip: Optional[str] = None
  resource_id: Optional[str] = None
  metadata: Optional[dict[str, Any]] = None


def accessibility_node_to_ui_element(
    node: Any,
    screen_size: Optional[tuple[int, int]] = None,
) -> UIElement:
  """Converts a node from an accessibility tree to a UIElement."""

  def text_or_none(text: Optional[str]) -> Optional[str]:
    """Returns None if text is None or 0 length."""
    return text if text else None

  node_bbox = node.bounds_in_screen
  bbox_pixels = BoundingBox(
      node_bbox.left, node_bbox.right, node_bbox.top, node_bbox.bottom
  )

  if screen_size is not None:
    bbox_normalized = _normalize_bounding_box(bbox_pixels, screen_size)
  else:
    bbox_normalized = None

  return UIElement(
      text=text_or_none(node.text),
      content_description=text_or_none(node.content_description),
      class_name=text_or_none(node.class_name),
      bbox=bbox_normalized,
      bbox_pixels=bbox_pixels,
      hint_text=text_or_none(node.hint_text),
      is_checked=node.is_checked,
      is_checkable=node.is_checkable,
      is_clickable=node.is_clickable,
      is_editable=node.is_editable,
      is_enabled=node.is_enabled,
      is_focused=node.is_focused,
      is_focusable=node.is_focusable,
      is_long_clickable=node.is_long_clickable,
      is_scrollable=node.is_scrollable,
      is_selected=node.is_selected,
      is_visible=node.is_visible_to_user,
      package_name=text_or_none(node.package_name),
      resource_name=text_or_none(node.view_id_resource_name),
  )


def _normalize_bounding_box(
    node_bbox: BoundingBox,
    screen_width_height_px: tuple[int, int],
) -> BoundingBox:
  width, height = screen_width_height_px
  return BoundingBox(
      node_bbox.x_min / width,
      node_bbox.x_max / width,
      node_bbox.y_min / height,
      node_bbox.y_max / height,
  )


def forest_to_ui_elements(
    forest: android_accessibility_forest_pb2.AndroidAccessibilityForest | Any,
    exclude_invisible_elements: bool = False,
    screen_size: Optional[tuple[int, int]] = None,
) -> list[UIElement]:
  """Extracts nodes from accessibility forest and converts to UI elements.

  We extract all nodes that are either leaf nodes or have content descriptions
  or is scrollable.

  Args:
    forest: The forest to extract leaf nodes from.
    exclude_invisible_elements: True if invisible elements should not be
      returned.
    screen_size: The size of the device screen in pixels (width, height).

  Returns:
    The extracted UI elements.
  """
  elements = []
  for window in forest.windows:
    for node in window.tree.nodes:
      if not node.child_ids or node.content_description or node.is_scrollable:
        if exclude_invisible_elements and not node.is_visible_to_user:
          continue
        else:
          elements.append(accessibility_node_to_ui_element(node, screen_size))
  return elements


def _parse_ui_hierarchy(xml_string: str) -> dict[str, Any]:
  """Parses the UI hierarchy XML into a dictionary structure."""
  root = ET.fromstring(xml_string)

  def parse_node(node):
    result = node.attrib
    result['children'] = [parse_node(child) for child in node]
    return result

  return parse_node(root)


def xml_dump_to_ui_elements(xml_string: str) -> list[UIElement]:
  """Converts a UI hierarchy XML dump from uiautomator dump to UIElements."""
  parsed_hierarchy = _parse_ui_hierarchy(xml_string)
  ui_elements = []

  def process_node(node, is_root):
    bounds = node.get('bounds')
    if bounds:
      x_min, y_min, x_max, y_max = map(
          int, bounds.strip('[]').replace('][', ',').split(',')
      )
      bbox = BoundingBox(x_min, x_max, y_min, y_max)
    else:
      bbox = None

    ui_element = UIElement(
        text=node.get('text'),
        content_description=node.get('content-desc'),
        class_name=node.get('class'),
        bbox=bbox,
        bbox_pixels=bbox,
        is_checked=node.get('checked') == 'true',
        is_checkable=node.get('checkable') == 'true',
        is_clickable=node.get('clickable') == 'true',
        is_enabled=node.get('enabled') == 'true',
        is_focused=node.get('focused') == 'true',
        is_focusable=node.get('focusable') == 'true',
        is_long_clickable=node.get('long-clickable') == 'true',
        is_scrollable=node.get('scrollable') == 'true',
        is_selected=node.get('selected') == 'true',
        package_name=node.get('package'),
        resource_id=node.get('resource-id'),
        is_visible=True,
    )
    if not is_root:
      ui_elements.append(ui_element)

    for child in node.get('children', []):
      process_node(child, is_root=False)

  process_node(parsed_hierarchy, is_root=True)
  return ui_elements
```

### `official/install/android_world/env/setup_device/__init__.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/setup_device/__init__.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Device setup utilities."""
```

### `official/install/android_world/env/setup_device/apps.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/setup_device/apps.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This module defines classes for setting up various applications in the Android World environment.

Each class represents an app and includes methods for retrieving its APK name
and performing setup tasks specific to that app using the Android Environment
Interface.
"""

import abc
import os
import time
from typing import Iterable
from absl import logging
from android_world.env import adb_utils
from android_world.env import interface
from android_world.env import tools
from android_world.task_evals.information_retrieval import joplin_app_utils
from android_world.utils import file_utils
import requests


APP_DATA = file_utils.convert_to_posix_path(os.path.dirname(__file__),
'app_data')


def download_app_data(file_name: str) -> str:
  """Downloads file from a GCS bucket, if not cached, and installs it."""
  cache_dir = file_utils.convert_to_posix_path(
      file_utils.get_local_tmp_directory(), "android_world", "app_data"
  )
  remote_url = (
      f"https://storage.googleapis.com/gresearch/android_world/{file_name}"
  )
  full_path = file_utils.convert_to_posix_path(cache_dir, file_name)
  os.makedirs(cache_dir, exist_ok=True)
  if not os.path.isfile(full_path):
    logging.info("Downloading file_name %s to cache %s", file_name, cache_dir)
    response = requests.get(remote_url)
    if response.status_code == 200:
      with open(full_path, "wb") as file:
        file.write(response.content)
    else:
      raise RuntimeError(
          f"Failed to download file_name from {remote_url}, status code:"
          f" {response.status_code}"
      )
  else:
    logging.info("File already %s exists in cache %s", file_name, cache_dir)
  return full_path


class AppSetup(abc.ABC):
  """Abstract class for setting up an app."""

  # The APK name of the app. This will assumed to be downloaded in setup.py and
  # each instance of an AppSetup will be referenced using the `apk` name as the
  # key for downloading. Some apps contain multiple APK names since different
  # versions are distributed depending on the architecture. E.g., M1 Macs
  # require different APKs for some apps.
  apk_names = ""

  # The short name of the app, as used by adb_utils.
  app_name = ""

  @classmethod
  def package_name(cls) -> str:
    return adb_utils.extract_package_name(
        adb_utils.get_adb_activity(cls.app_name)
    )

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    """Performs setup tasks specific to the app."""
    adb_utils.clear_app_data(
        adb_utils.extract_package_name(
            adb_utils.get_adb_activity(cls.app_name)
        ),
        env.controller,
    )

  @classmethod
  def _copy_data_to_device(
      cls,
      files: Iterable[str],
      device_path: str,
      env: interface.AsyncEnv,
  ) -> None:
    """Helper method for copying app data  to the device.

    Args:
      files: Names of files to copy from {APP_DATA}/app_name/ to {device_path}.
      device_path: Location on device to load the files.
      env: Android environment.
    """
    for file in files:
      copy_to_device = lambda path: adb_utils.check_ok(
          file_utils.copy_data_to_device(
              path,
              device_path,
              env.controller,
          ),
          f"Failed to copy {device_path} to device.",
      )

      full_path = download_app_data(file)
      copy_to_device(full_path)


class CameraApp(AppSetup):
  """Class for setting up pre-installed Camera app."""

  app_name = "camera"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)

    # Prevent pop-up asking for permission.
    adb_utils.grant_permissions(
        adb_utils.extract_package_name(
            adb_utils.get_adb_activity(cls.app_name)
        ),
        "android.permission.ACCESS_COARSE_LOCATION",
        env.controller,
    )

    # Click through onboarding screens during first time launch.
    adb_utils.launch_app(cls.app_name, env.controller)
    try:
      controller = tools.AndroidToolController(env=env.controller)
      time.sleep(2.0)
      controller.click_element("NEXT")
      time.sleep(2.0)
    finally:
      adb_utils.close_app(cls.app_name, env.controller)


class ChromeApp(AppSetup):
  """Class for setting up pre-installed Chrome app."""

  app_name = "chrome"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)

    # Click through onboarding screens during first time launch.
    adb_utils.launch_app(cls.app_name, env.controller)
    try:
      controller = tools.AndroidToolController(env=env.controller)
      time.sleep(2.0)
      # Welcome screen.
      controller.click_element("Accept & continue")
      time.sleep(2.0)
      # Turn on sync?
      controller.click_element("No thanks")
      time.sleep(2.0)
      # Enable notifications?
      controller.click_element("No thanks")
      time.sleep(2.0)
    finally:
      adb_utils.close_app(cls.app_name, env.controller)


class ClockApp(AppSetup):
  """Class for setting up pre-installed Clock app."""

  app_name = "clock"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)

    # Open once for initial tool tip display.
    adb_utils.launch_app(cls.app_name, env.controller)
    time.sleep(2.0)
    adb_utils.close_app(cls.app_name, env.controller)


class ContactsApp(AppSetup):
  """Class for setting up pre-installed Contacts app."""

  app_name = "contacts"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)

    # Click through onboarding screens during first time launch.
    adb_utils.launch_app(cls.app_name, env.controller)
    try:
      controller = tools.AndroidToolController(env=env.controller)
      time.sleep(2.0)
      # Back up & organize your contacts with Google.
      controller.click_element("Skip")
      time.sleep(2.0)
      # Allow Contacts to send you notifications?
      controller.click_element("Don't allow")
      time.sleep(2.0)
    finally:
      adb_utils.close_app(cls.app_name, env.controller)


class DialerApp(AppSetup):
  """Class for setting up pre-installed Dialer app."""

  app_name = "dialer"


class FilesApp(AppSetup):
  """Class for setting up pre-installed Files app."""

  app_name = "files"


class SettingsApp(AppSetup):
  """Class for setting up pre-installed Settings app."""

  app_name = "settings"


class MarkorApp(AppSetup):
  """Class for setting up Markor app."""

  apk_names = ("net.gsantner.markor_146.apk",)
  app_name = "markor"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)

    adb_utils.launch_app(cls.app_name, env.controller)
    try:
      controller = tools.AndroidToolController(env=env.controller)
      time.sleep(2.0)
      controller.click_element("NEXT")
      time.sleep(2.0)
      controller.click_element("NEXT")
      time.sleep(2.0)
      controller.click_element("NEXT")
      time.sleep(2.0)
      controller.click_element("NEXT")
      time.sleep(2.0)
      controller.click_element("DONE")
      time.sleep(2.0)

      controller.click_element("OK")
      time.sleep(2.0)
      controller.click_element("Allow access to manage all files")
      time.sleep(2.0)
    finally:
      adb_utils.close_app(cls.app_name, env.controller)


class AndroidWorldApp(AppSetup):
  """Class for setting up Android World app.

  AndroidWorld app provides on-screen visualization of tasks and rewards.
  """

  apk_names = ("androidworld.apk",)
  app_name = "android world"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)
    adb_utils.issue_generic_request(
        [
            "shell",
            "appops",
            "set",
            adb_utils.extract_package_name(
                adb_utils.get_adb_activity("android world")
            ),
            "android:system_alert_window",
            "allow",
        ],
        env.controller,
    )
    adb_utils.launch_app(cls.app_name, env.controller)
    adb_utils.close_app(cls.app_name, env.controller)


class ClipperApp(AppSetup):
  """Class for setting up clipper app."""

  apk_names = ("clipper.apk",)
  app_name = "clipper"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)
    controller = tools.AndroidToolController(env=env.controller)
    adb_utils.launch_app(cls.app_name, env.controller)
    try:
      time.sleep(2.0)
      controller.click_element("Continue")
      time.sleep(2.0)
      controller.click_element("OK")
    finally:
      adb_utils.close_app(cls.app_name, env.controller)


class SimpleCalendarProApp(AppSetup):
  """Class for setting up simple calendar pro app."""

  apk_names = ("com.simplemobiletools.calendar.pro_238.apk",)
  app_name = "simple calendar pro"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)
    adb_utils.launch_app(cls.app_name, env.controller)
    adb_utils.close_app(cls.app_name, env.controller)

    # Grant permissions for calendar app.
    calendar_package = adb_utils.extract_package_name(
        adb_utils.get_adb_activity("simple calendar pro")
    )
    adb_utils.grant_permissions(
        calendar_package,
        "android.permission.READ_CALENDAR",
        env.controller,
    )
    adb_utils.grant_permissions(
        calendar_package,
        "android.permission.WRITE_CALENDAR",
        env.controller,
    )
    adb_utils.grant_permissions(
        calendar_package,
        "android.permission.POST_NOTIFICATIONS",
        env.controller,
    )


class TasksApp(AppSetup):
  """Class for setting up Tasks app."""

  apk_names = ("org.tasks_130605.apk",)
  app_name = "tasks"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)
    adb_utils.launch_app(cls.app_name, env.controller)
    adb_utils.close_app(cls.app_name, env.controller)


class SimpleDrawProApp(AppSetup):
  """Class for setting up simple draw pro app."""

  apk_names = ("com.simplemobiletools.draw.pro_79.apk",)
  app_name = "simple draw pro"


class SimpleGalleryProApp(AppSetup):
  """Class for setting up Simple Gallery Pro app."""

  PERMISSIONS = (
      "android.permission.WRITE_EXTERNAL_STORAGE",
      "android.permission.ACCESS_MEDIA_LOCATION",
      "android.permission.READ_MEDIA_IMAGES",
      "android.permission.READ_MEDIA_VIDEO",
      "android.permission.POST_NOTIFICATIONS",
  )

  apk_names = ("com.simplemobiletools.gallery.pro_396.apk",)
  app_name = "simple gallery pro"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)

    # Grant permissions for gallery app.
    package = adb_utils.extract_package_name(
        adb_utils.get_adb_activity(cls.app_name)
    )
    for permission in cls.PERMISSIONS:
      adb_utils.grant_permissions(package, permission, env.controller)

    adb_utils.launch_app("simple gallery pro", env.controller)
    try:
      controller = tools.AndroidToolController(env=env.controller)
      time.sleep(2.0)
      controller.click_element("All files")
      time.sleep(2.0)
      controller.click_element("Allow access to manage all files")
    finally:
      adb_utils.close_app(cls.app_name, env.controller)


class SimpleSMSMessengerApp(AppSetup):
  """Class for setting up Simple SMS Messenger app."""

  apk_names = ("com.simplemobiletools.smsmessenger_85.apk",)
  app_name = "simple sms messenger"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)

    # Make Simple Messenger the default SMS app.
    adb_utils.set_default_app(
        "sms_default_application",
        adb_utils.extract_package_name(
            adb_utils.get_adb_activity("simple sms messenger")
        ),
        env.controller,
    )

    adb_utils.launch_app(cls.app_name, env.controller)
    try:
      controller = tools.AndroidToolController(env=env.controller)
      time.sleep(2.0)
      controller.click_element("SMS Messenger")
      time.sleep(2.0)
      controller.click_element("Set as default")
    finally:
      adb_utils.close_app(cls.app_name, env.controller)


class AudioRecorder(AppSetup):
  """Class for setting up Audio Recorder app."""

  apk_names = ("com.dimowner.audiorecorder_926.apk",)
  app_name = "audio recorder"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)
    adb_utils.grant_permissions(
        "com.dimowner.audiorecorder",
        "android.permission.RECORD_AUDIO",
        env.controller,
    )
    adb_utils.grant_permissions(
        "com.dimowner.audiorecorder",
        "android.permission.POST_NOTIFICATIONS",
        env.controller,
    )

    # Launch the app
    adb_utils.issue_generic_request(
        [
            "shell",
            "monkey",
            "-p",
            "com.dimowner.audiorecorder",
            "-candroid.intent.category.LAUNCHER",
            "1",
        ],
        env.controller,
    )
    time.sleep(2.0)  # Let app setup.
    adb_utils.close_app(cls.app_name, env.controller)


class MiniWobApp(AppSetup):
  """Class for setting up MiniWoB app."""

  apk_names = ("miniwobapp.apk",)
  app_name = "miniwob"


class ExpenseApp(AppSetup):
  """Class for setting up Arduia Pro Expense app."""

  apk_names = ("com.arduia.expense_11.apk",)
  app_name = "pro expense"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)
    adb_utils.launch_app(cls.app_name, env.controller)
    try:
      time.sleep(2.0)
      controller = tools.AndroidToolController(env=env.controller)
      controller.click_element("NEXT")
      time.sleep(2.0)
      controller.click_element("CONTINUE")
      time.sleep(3.0)
    finally:
      adb_utils.close_app(cls.app_name, env.controller)


class RecipeApp(AppSetup):
  """Class for setting up Broccoli Recipe app."""

  apk_names = ("com.flauschcode.broccoli_1020600.apk",)
  app_name = "broccoli app"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)
    adb_utils.launch_app(cls.app_name, env.controller)
    time.sleep(2.0)
    adb_utils.close_app(cls.app_name, env.controller)


class OsmAndApp(AppSetup):
  """Class for setting up OsmAndApp map app.

  OsmAnd handles the following intents (among others*). In addition to geo
  URIs, it can handle intents using the Google Maps API as well as a few
  other apps not listed here.

  Android geo intents:
    geo:latitude,longitude
    geo:latitude,longitude?z=zoom
    geo:0,0?q=my+street+address
    geo:0,0?q=business+near+city

  OsmAnd specific intents:
    http://download.osmand.net/go?lat=&lon=&z=
    http://osmand.net/go?lat=34&lon=-106&z=11

  Google:
    google.navigation:q=34.99393,-106.61568
    http://maps.google.com/maps?q=N34.939,W106
    http://maps.google.com/maps?f=d&saddr=My+Location&daddr=lat,lon
    http://maps.google.com/maps/@34,-106,11z
    http://maps.google.com/maps/ll=34.99393,-106.61568,z=11
    https://maps.google.com/maps?q=loc:-21.8835112,-47.7838932 (Name)
    http://maps.google.com/maps?q=34,-106
    http://www.google.com/maps/dir/Current+Location/34,-106

  * https://osmand.net/docs/technical/algorithms/osmand-intents/
  """

  PERMISSIONS = (
      "android.permission.POST_NOTIFICATIONS",
      # For other possible permissions see the manifest
      # https://github.com/osmandapp/OsmAnd/blob/master/OsmAnd/AndroidManifest.xml
  )

  DEVICE_MAPS_PATH = "/storage/emulated/0/Android/data/net.osmand/files/"

  MAP_NAMES = ("Liechtenstein_europe.obf",)

  apk_names = ("net.osmand-4.6.13.apk",)
  app_name = "osmand"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)
    adb_utils.launch_app(cls.app_name, env.controller)
    time.sleep(2.0)

    try:
      controller = tools.AndroidToolController(env=env.controller)
      controller.click_element("SKIP DOWNLOAD")
      time.sleep(2.0)
    except ValueError:
      logging.warn(
          "First time setup did not click through all anticipated screens."
      )
    finally:
      adb_utils.close_app(cls.app_name, env.controller)

    # Grant permissions for OsmAnd mapping app.
    package = adb_utils.extract_package_name(
        adb_utils.get_adb_activity(cls.app_name)
    )
    for permission in cls.PERMISSIONS:
      adb_utils.grant_permissions(package, permission, env.controller)

    # Copy maps to data directory.
    cls._copy_data_to_device(cls.MAP_NAMES, cls.DEVICE_MAPS_PATH, env)

    # Make sure security context is correct so that the files can be accessed.
    for map_file in cls.MAP_NAMES:
      adb_utils.check_ok(
          adb_utils.issue_generic_request(
              [
                  "shell",
                  "chcon",
                  "u:object_r:media_rw_data_file:s0",
                  file_utils.convert_to_posix_path(
                      cls.DEVICE_MAPS_PATH, map_file
                  ),
              ],
              env.controller,
          )
      )

    adb_utils.close_app(cls.app_name, env.controller)


class OpenTracksApp(AppSetup):
  """Class for setting up OpenTracks app."""

  apk_names = ("de.dennisguse.opentracks_5705.apk",)
  app_name = "open tracks sports tracker"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    adb_utils.launch_app(cls.app_name, env.controller)
    adb_utils.close_app(cls.app_name, env.controller)

    # Grant permissions for open tracks app.
    open_tracks_package = adb_utils.extract_package_name(
        adb_utils.get_adb_activity("open tracks")
    )
    adb_utils.grant_permissions(
        open_tracks_package,
        "android.permission.ACCESS_COARSE_LOCATION",
        env.controller,
    )
    adb_utils.grant_permissions(
        open_tracks_package,
        "android.permission.ACCESS_FINE_LOCATION",
        env.controller,
    )
    adb_utils.grant_permissions(
        open_tracks_package,
        "android.permission.POST_NOTIFICATIONS",
        env.controller,
    )
    time.sleep(2.0)
    controller = tools.AndroidToolController(env=env.controller)
    # Give permission for bluetooth, can't be done through adb.
    controller.click_element("Allow")
    adb_utils.launch_app("activity tracker", env.controller)
    adb_utils.close_app("activity tracker", env.controller)


class VlcApp(AppSetup):
  """Class for setting up VLC app."""

  videos_path = "/storage/emulated/0/VLCVideos"  # Store videos here.
  apk_names = (
      "org.videolan.vlc_13050408.apk",
      "org.videolan.vlc_13050407.apk",  # Arch86 for Mac M1/M2/etc.
  )
  app_name = "vlc"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)
    package = adb_utils.extract_package_name(
        adb_utils.get_adb_activity(cls.app_name)
    )
    adb_utils.grant_permissions(
        package, "android.permission.POST_NOTIFICATIONS", env.controller
    )
    if not file_utils.check_directory_exists(cls.videos_path, env.controller):
      file_utils.mkdir(cls.videos_path, env.controller)

    time.sleep(2.0)
    # Launch similar to opening app from app launcher. This runs setup logic not
    # available using `adb shell am start`. Specifically, it will create the
    # /data/data/org.videolan.vlc/app_db/vlc_media.db file.
    adb_utils.issue_generic_request(
        [
            "shell",
            "monkey",
            "-p",
            package,
            "-candroid.intent.category.LAUNCHER",
            "1",
        ],
        env.controller,
    )
    time.sleep(2.0)
    try:
      controller = tools.AndroidToolController(env=env.controller)
      controller.click_element("Skip")
      time.sleep(2.0)
      controller.click_element("GRANT PERMISSION")
      time.sleep(2.0)
      controller.click_element("OK")
      time.sleep(2.0)
      controller.click_element("Allow access to manage all files")
    finally:
      adb_utils.close_app(cls.app_name, env.controller)


class JoplinApp(AppSetup):
  """Class for setting up Joplin app."""

  apk_names = ("net.cozic.joplin_2097740.apk",)
  app_name = "joplin"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)

    # Grant permissions for joplin app.
    joplin_package = adb_utils.extract_package_name(
        adb_utils.get_adb_activity(cls.app_name)
    )
    adb_utils.grant_permissions(
        joplin_package,
        "android.permission.ACCESS_COARSE_LOCATION",
        env.controller,
    )
    adb_utils.grant_permissions(
        joplin_package,
        "android.permission.ACCESS_FINE_LOCATION",
        env.controller,
    )

    # Launch the app, similar to how user launches it from App Drawer.
    adb_utils.issue_generic_request(
        [
            "shell",
            "monkey",
            "-p",
            joplin_package,
            "-candroid.intent.category.LAUNCHER",
            "1",
        ],
        env.controller,
    )
    time.sleep(10.0)
    adb_utils.close_app(cls.app_name, env.controller)
    time.sleep(10.0)

    # Calling clear_dbs() without having added a note seems to make
    # the sqlite table inaccessible. Every subsequent call to clear_dbs()
    # works fine.
    joplin_app_utils.create_note(
        folder="new folder",
        title="new_note",
        body="",
        folder_mapping={},
        env=env,
    )
    joplin_app_utils.clear_dbs(env)


class RetroMusicApp(AppSetup):
  """Class for setting up Retro Music."""

  PERMISSIONS = (
      "android.permission.READ_MEDIA_AUDIO",
      "android.permission.POST_NOTIFICATIONS",
  )

  apk_names = ("code.name.monkey.retromusic_10603.apk",)
  app_name = "retro music"

  @classmethod
  def setup(cls, env: interface.AsyncEnv) -> None:
    super().setup(env)
    package = adb_utils.extract_package_name(
        adb_utils.get_adb_activity("retro music")
    )
    for permission in cls.PERMISSIONS:
      adb_utils.grant_permissions(package, permission, env.controller)

    adb_utils.launch_app(cls.app_name, env.controller)
    time.sleep(2.0)
    adb_utils.close_app(cls.app_name, env.controller)
```

### `official/install/android_world/env/setup_device/setup.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/setup_device/setup.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Setup tool for Android World.

It does the following:

* APK Management: Automates installations of apks needed for Android World.
* Sets up environment: Configures emulator with necessary permissions, using adb
  and basic automation.
"""

import os
from typing import Type

from absl import logging
from android_env import env_interface
from android_env.components import errors
from android_world.env import adb_utils
from android_world.env import interface
from android_world.env.setup_device import apps
from android_world.utils import app_snapshot

# APKs required for Android World.
_APPS = (
    # keep-sorted start
    apps.AndroidWorldApp,
    apps.AudioRecorder,
    apps.CameraApp,
    apps.ChromeApp,
    apps.ClipperApp,
    apps.ClockApp,
    apps.ContactsApp,
    apps.DialerApp,
    apps.ExpenseApp,
    apps.FilesApp,
    apps.JoplinApp,
    apps.MarkorApp,
    apps.MiniWobApp,
    apps.OpenTracksApp,
    apps.OsmAndApp,
    apps.RecipeApp,
    apps.RetroMusicApp,
    apps.SettingsApp,
    apps.SimpleCalendarProApp,
    apps.SimpleDrawProApp,
    apps.SimpleGalleryProApp,
    apps.SimpleSMSMessengerApp,
    apps.TasksApp,
    apps.VlcApp,
    # keep-sorted end
)


def get_installed_packages(env: interface.AsyncEnv) -> frozenset[str]:
  """Returns the set of installed packages."""
  return frozenset(adb_utils.get_all_package_names(env.controller.env))


def is_package_installed(package_name: str, env: interface.AsyncEnv) -> bool:
  """Checks if a package is installed."""
  installed_packages = get_installed_packages(env)
  return package_name in installed_packages


def get_app_mapping(app_name: str) -> Type[apps.AppSetup] | None:
  if not app_name:
    return None
  mapping = {app.app_name: app for app in _APPS}
  if app_name in mapping:
    return mapping[app_name]
  return None


def get_app_list_to_setup(
    task_ids: list[str] | None,
) -> tuple[Type[apps.AppSetup], ...] | None:
  """Returns the list of apps that are required by the tasks.

  Args:
    task_ids: A list of tasks.

  Returns:
    A tuple of AppSetup classes.
  """
  if not task_ids:
    return None
  required_apps = set()
  for app_class in _APPS:
    # Convert app_name to PascalCase, handling existing capitalization.
    pascal_case_app_name = "".join(
        word.capitalize() for word in app_class.app_name.split()
    )
    for task_id in task_ids:
      if pascal_case_app_name in task_id:
        required_apps.add(app_class)
  return tuple(required_apps)


def download_and_install_apk(
    apk: str, raw_env: env_interface.AndroidEnvInterface
) -> None:
  """Downloads APK from remote location and installs it."""
  path = apps.download_app_data(apk)
  adb_utils.install_apk(path, raw_env)


def setup_app(app: Type[apps.AppSetup], env: interface.AsyncEnv) -> None:
  """Sets up a single app."""
  try:
    logging.info("Setting up app %s", app.app_name)
    app.setup(env)
  except ValueError as e:
    logging.warning(
        "Failed to automatically setup app %s: %s.\n\nYou will need to"
        " manually setup the app.",
        app.app_name,
        e,
    )
  app_snapshot.save_snapshot(app.app_name, env.controller)


def install_app_if_not_installed(app_name: str, env: interface.AsyncEnv):
  """Installs the apk of an app only if the apk is not installed."""
  path = apps.download_app_data(apk)
  adb_utils.install_apk(path, raw_env)


def maybe_install_app(
    app: Type[apps.AppSetup], env: interface.AsyncEnv
) -> None:
  """Installs all APKs for Android World."""
  if not app.apk_names:  # Ignore 1p apps that don't have an APK.
    return
  logging.info("Installing app: %s.", app.app_name)

  apk_installed = False
  for apk_name in app.apk_names:
    try:
      download_and_install_apk(apk_name, env.controller.env)
      apk_installed = True
      break
    except errors.AdbControllerError:
      # Try apk compiled for a different architecture, e.g., Mac M1.
      continue
  if not apk_installed:
    raise RuntimeError(f"Failed to download and install APK for {app.app_name}")


def setup_apps(
    env: interface.AsyncEnv,
    app_list: tuple[Type[apps.AppSetup], ...] | None = None,
) -> None:
  """Sets up apps for Android World.

  Args:
    env: The Android environment.
    app_list: The list of apps to setup. If not specified, the default list of
      apps will be used.

  Raises:
    RuntimeError: If cannot install APK.
  """
  # Make sure quick-settings are not displayed, which can override foreground
  # apps, and impede UI navigation required for setting up.
  adb_utils.press_home_button(env.controller)
  adb_utils.set_root_if_needed(env.controller)

  logging.info(
      "Installing and setting up applications on Android device. Please do not"
      " interact with device while installation is running."
  )
  if app_list is None:
    app_list = _APPS
  for app in app_list:
    maybe_install_app(app, env)
    setup_app(app, env)
```

### `official/install/android_world/env/tools.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/tools.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""API tools library for Android agents."""

import inspect
import json
import time
from typing import Optional, Union

from android_world.env import actuation
from android_world.env import adb_utils
from android_world.env import android_world_controller
from android_world.utils import contacts_utils


# When the compose message is pulled up, the send button has this as text for
# Simple SMS Messenger.
SIMPLE_SMS_SEND_TEXT = "SMS"
# For Google messaging app.
SMS_SEND_TEXT = "Send SMS"


class AndroidToolController:
  """Executes API tools on an Android device."""

  def __init__(
      self,
      env: android_world_controller.AndroidWorldController,
  ):
    """Initializes the controller with an Android environment instance.

    Args:
      env: The AndroidEnv interface to be used.
    """
    self._env = env

  def click_element(self, element_text: str):
    actuation.find_and_click_element(element_text, self._env)

  def open_web_page(self, url: str):
    """Open a web page in the default browser on an Android device.

    This function sends an intent to the Android system to open the specified
    URL.

    Args:
      url: The URL of the web page to open. E.g., http://www.google.com.
    """
    if not url.startswith("http://"):
      url = "http://" + url
    adb_command = ["shell", f"am start -a android.intent.action.VIEW -d {url}"]
    adb_utils.issue_generic_request(adb_command, self._env)

  def send_sms(
      self,
      phone_number: str,
      message: str,
  ):
    """Send an SMS to a specified phone number.

    This function sends an intent to the Android system to open the messaging
    app with the recipient's number and message pre-filled.

    Args:
      phone_number: The phone number to which the SMS should be sent.
      message: The pre-filled message text.
    """
    # Construct the Intent command
    intent_command = (
        "am start -a android.intent.action.SENDTO -d sms:{phone_number} "
        f'--es sms_body "{message}"'
    ).format(phone_number=phone_number)

    adb_command = ["shell", intent_command]
    adb_utils.issue_generic_request(adb_command, self._env)
    time.sleep(5.0)

    package_name = adb_utils.extract_package_name(
        adb_utils.get_current_activity(self._env)[0]
    )
    # Depending on what the default SMS app we need to click different buttons.
    if package_name == "com.google.android.apps.messaging":
      self.click_element(SMS_SEND_TEXT)
    elif package_name == "com.simplemobiletools.smsmessenger":
      self.click_element(SIMPLE_SMS_SEND_TEXT)
    else:
      raise ValueError(f"Messaging app not supported: {package_name}")

  def _gather_tool_details(
      self,
  ) -> dict[str, list[Optional[dict[str, Union[dict[str, str], str]]]]]:
    """Get the details and examples of usage for public APIs related to Android tools.

    Returns:
        A dictionary where the keys are API names and the values are lists of
        dictionaries containing the docstrings and usage examples.
    """
    return {
        "open_web_page": self._tool_info(
            self.open_web_page,
            [
                {"url": "http://www.google.com"},
                {"url": "http://www.example.com"},
            ],
        ),
        "send_sms": self._tool_info(
            self.send_sms,
            [
                {
                    "phone_number": "+123456789",
                    "message": "Hello, how are you?",
                },
                {
                    "phone_number": "+987654321",
                    "message": "Meeting rescheduled to 3 PM.",
                },
            ],
        ),
        "add_contact": self._tool_info(
            contacts_utils.add_contact,
            [
                {"name": "John Doe", "phone_number": "+123456789"},
                {"name": "Joe", "phone_number": "987654321"},
            ],
        ),
    }

  def _tool_info(
      self, method, example_args: list[dict[str, str]]
  ) -> list[Optional[dict[str, Union[dict[str, str], str]]]]:
    """Helper function to construct tool information and examples.

    Args:
        method: The method for which to gather information.
        example_args: A list of argument dictionaries for examples.

    Returns:
        A list containing the method's documentation and examples.
    """
    doc_info = {"doc": inspect.getdoc(method)}
    examples = [
        {"method": method.__name__, "args": args} for args in example_args
    ]
    return [doc_info, *examples]

  def display_tool_usage(self) -> str:
    """Format the tool information and examples into a user-friendly string.

    Returns:
        A string representing the available tools and their usage examples.
    """
    tools_info = self._gather_tool_details()
    formatted_info = ["Available Tools and Usage Examples:\n"]

    for tool_name, tool_details in tools_info.items():
      formatted_info.append(f"\nAPI: {tool_name}\n")
      formatted_info.append(f"Description: {tool_details[0]['doc']}\n")
      formatted_info.append("Examples:\n")
      for example in tool_details[1:]:
        formatted_info.append(f"  - JSON Request: {example}\n")

    return "".join(formatted_info)

  def handle_json_request(self, json_request: str):
    """Handle a JSON formatted request to use a tool.

    Args:
        json_request: A JSON string with the method and arguments.
    """
    request = json.loads(json_request)
    method_name = request["method"]
    args = request.get("args", {})

    if hasattr(self, method_name) and callable(getattr(self, method_name)):
      method = getattr(self, method_name)
      method(**args)
    else:
      raise ValueError(f"Method {method_name} not found.")
```

### `official/install/android_world/task_evals/__init__.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/__init__.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Task evaluation modules for AndroidWorld."""
```

### `official/install/android_world/task_evals/common_validators/__init__.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/common_validators/__init__.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Common validators for AndroidWorld tasks."""
```

### `official/install/android_world/task_evals/information_retrieval/__init__.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/__init__.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Information retrieval task evaluations."""
```

### `official/install/android_world/task_evals/information_retrieval/datetime_utils.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/datetime_utils.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Information Retrieval utils for datetime."""

import datetime
import random
from android_world.env import device_constants

DATE_FORMAT = '%B %d %Y'


def get_date(date_str: str) -> datetime.date:
  return datetime.datetime.strptime(date_str, DATE_FORMAT).date()


def _generate_nl_date_options(date_str: str) -> list[str]:
  """Lists all options for a natural language way of expressing date.

  Possible options include:
    - today, tomorrow, yesterday if they apply
    - <day of week> if the day is within a week in the future or in the past.
    - 'this <day of week>' if the day is within a week in the future.
    - 'the <day of week> after next' if it applies.
    - <month name> <day>
    - <month name> <day> <year>

  Args:
    date_str: The date to rephrase in a natural language formats.

  Returns:
    A list of strings representing the date in a natural way.
  """
  date = get_date(date_str)
  options = [date.strftime('%B %d'), date.strftime(DATE_FORMAT)]
  if date == device_constants.DT.date():
    options.append('today')
  if date == device_constants.DT.date() + datetime.timedelta(days=1):
    options.append('tomorrow')
  if date == device_constants.DT.date() - datetime.timedelta(days=1):
    options.append('yesterday')
  if date > device_constants.DT.date():
    day_name = date.strftime('%A')
    if date - device_constants.DT.date() <= datetime.timedelta(days=7):
      options.append(day_name)
      options.append('this {}'.format(day_name))
    elif date - device_constants.DT.date() <= datetime.timedelta(days=14):
      options.append('the {} after next'.format(day_name))
  if date < device_constants.DT.date():
    day_name = date.strftime('%A')
    if device_constants.DT.date() - date <= datetime.timedelta(days=7):
      options.append(day_name)
  return options


def generate_reworded_date(date_str: str) -> str:
  """Randomly generates a natural language way of expressing date.

  Uses the following options:
    - today, tomorrow, yesterday if they apply
    - <day of week> if the day is within a week in the future or in the past.
    - 'this <day of week>' if the day is within a week in the future.
    - 'the <day of week> after next' if it applies.
    - <month name> <day>
    - <month name> <day> <year>

  Args:
    date_str: The date to rephrase in a natural language format.

  Returns:
    A string representing the date in a natural way.
  """

  options = _generate_nl_date_options(date_str)
  return random.choice(options)


def parse_time(time_str: str) -> datetime.time:
  """Parse a time string into a datetime object using multiple formats.

  The following formats are handled:
    <24 hour format>:<minute> : e.g. 10:00, 15:00
    <12 hour format>:<minute><pm/am>: e.g. 10:00am, 10:00pm
    <12 hour format><pm/am> : e.g. 10am, 10pm

  Args:
    time_str: The string representation of the time.

  Returns:
    A datetime.time object representing the time.

  Raises:
    ValueError: If the time string does not match any of the expected formats.
  """
  time_formats = ('%H:%M', '%I:%M%p', '%I%p')
  for fmt in time_formats:
    try:
      dt = datetime.datetime.strptime(time_str, fmt)
      return datetime.time(hour=dt.hour, minute=dt.minute)
    except ValueError:
      pass
  raise ValueError(f"Time string '{time_str}' does not match any known format.")
```

### `official/install/android_world/task_evals/information_retrieval/joplin_app_utils.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/joplin_app_utils.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utils for Joplin app."""

import os
import random

from android_world.env import adb_utils
from android_world.env import interface
from android_world.task_evals.information_retrieval import proto_utils
from android_world.task_evals.information_retrieval.proto import state_pb2
from android_world.task_evals.information_retrieval.proto import task_pb2
from android_world.task_evals.utils import sqlite_schema_utils
from android_world.task_evals.utils import sqlite_utils
from android_world.utils import file_utils

_NOTES_TABLE = "notes"
_NOTES_NORMALIZED_TABLE = "notes_normalized"
_FOLDER_TABLE = "folders"
_DB_PATH = "/data/data/net.cozic.joplin/databases/joplin.sqlite"
_APP_NAME = "joplin"
# Sometimes this field gets added to the Joplin db, but we do not need it.
_EXCLUDE_FIELD = "deleted_time"


def setup_task_state(
    relevant_state: state_pb2.NotesApp,
    exclusion_conditions: list[task_pb2.ExclusionCondition],
    env: interface.AsyncEnv,
) -> None:
  """Sets up the  state for the Joplin app.

  Args:
    relevant_state: The state to set up.
    exclusion_conditions: The exclusion conditions to use when generating random
      notes.
    env: The Android environment interface for database interaction.
  """
  clear_dbs(env)
  notes = []

  # Keep track of already created folders.
  folder_mapping = {}
  notes += _generate_random_notes(
      100,
      exclusion_conditions,
      [note.folder for note in relevant_state.notes],
      folder_mapping,
      env,
  )
  for note in relevant_state.notes:
    notes.append(_create_note_from_proto(note, folder_mapping, env))
  random.shuffle(notes)
  add_notes(notes, env)


def clear_dbs(env: interface.AsyncEnv) -> None:
  """Clears Joplin databases."""
  sqlite_utils.delete_all_rows_from_table(
      _FOLDER_TABLE, _DB_PATH, env, _APP_NAME
  )
  sqlite_utils.delete_all_rows_from_table(
      _NOTES_TABLE, _DB_PATH, env, _APP_NAME
  )
  sqlite_utils.delete_all_rows_from_table(
      _NOTES_NORMALIZED_TABLE, _DB_PATH, env, _APP_NAME
  )
  adb_utils.close_app(_APP_NAME, env.controller)  # Register changes.


def _get_folder_to_id(
    env: interface.AsyncEnv,
) -> dict[str, str]:
  """Gets a mapping from folder title to ID as represented in Folder table."""
  with env.controller.pull_file(_DB_PATH) as local_db_directory:
    local_db_path = file_utils.convert_to_posix_path(
        local_db_directory, os.path.split(_DB_PATH)[1]
    )
    folder_info = sqlite_utils.execute_query(
        f"select * from {_FOLDER_TABLE};",
        local_db_path,
        sqlite_schema_utils.JoplinFolder,
    )

  result = {}
  for row in folder_info:
    result[row.title] = row.id
  return result


def _add_folders(
    rows: list[sqlite_schema_utils.JoplinFolder],
    env: interface.AsyncEnv,
) -> None:
  """Inserts multiple folder rows into the remote Joplin database.

  Args:
      rows: A list of JoplinFolder instances to be inserted.
      env: The Android environment interface for database interaction.
  """

  sqlite_utils.insert_rows_to_remote_db(
      rows,
      _EXCLUDE_FIELD,
      _FOLDER_TABLE,
      _DB_PATH,
      _APP_NAME,
      env,
  )


def create_note(
    folder: str,
    title: str,
    body: str,
    folder_mapping: dict[str, str],
    env: interface.AsyncEnv,
    is_todo: int = False,
    todo_completed: bool = False,
) -> sqlite_schema_utils.JoplinNote:
  """Generates random note."""
  if not folder_mapping:
    folder_mapping.update(_get_folder_to_id(env))

  if folder not in folder_mapping:
    # Folder hasn't been created yet.
    _add_folders([sqlite_schema_utils.JoplinFolder(folder)], env)
    folder_mapping.clear()
    folder_mapping.update(_get_folder_to_id(env))
    if folder not in folder_mapping:
      raise ValueError("Something went wrong could not find or create folder.")
  parent_id = folder_mapping[folder]
  return sqlite_schema_utils.JoplinNote(
      parent_id=parent_id,
      title=title,
      body=body,
      is_todo=int(is_todo),
      todo_completed=int(todo_completed),
  )


def add_notes(
    rows: list[sqlite_schema_utils.JoplinNote],
    env: interface.AsyncEnv,
) -> None:
  """Inserts multiple note rows into the remote Joplin database."""
  sqlite_utils.insert_rows_to_remote_db(
      rows,
      None,
      _NOTES_TABLE,
      _DB_PATH,
      _APP_NAME,
      env,
  )
  sqlite_utils.insert_rows_to_remote_db(
      _normalize_notes(rows),
      None,
      _NOTES_NORMALIZED_TABLE,
      _DB_PATH,
      _APP_NAME,
      env,
  )


def _normalize_notes(
    notes: list[sqlite_schema_utils.JoplinNote],
) -> list[sqlite_schema_utils.JoplinNormalizedNote]:
  return [
      sqlite_schema_utils.JoplinNormalizedNote(
          id=note.id,
          parent_id=note.parent_id,
          title=note.title.lower(),
          body=note.body,
          is_todo=note.is_todo,
          todo_completed=note.todo_completed,
          user_created_time=note.user_created_time,
          user_updated_time=note.user_updated_time,
          latitude=note.latitude,
          longitude=note.longitude,
          altitude=note.altitude,
          source_url=note.source_url,
          todo_due=note.todo_due,
      )
      for note in notes
  ]


def list_notes(
    env: interface.AsyncEnv,
) -> list[sqlite_schema_utils.JoplinNote]:
  return sqlite_utils.get_rows_from_remote_device(
      _NOTES_TABLE,
      _DB_PATH,
      sqlite_schema_utils.JoplinNote,
      env,
  )


def _create_note_from_proto(
    note: state_pb2.Note,
    folder_mapping: dict[str, str],
    env: interface.AsyncEnv,
) -> sqlite_schema_utils.JoplinNote:
  """Creates a JoplinNote object from a state_pb2.Note proto."""
  is_todo = note.is_todo.lower() == "true"
  todo_completed = note.todo_completed.lower() == "true"
  return create_note(
      note.folder,
      note.title,
      note.body,
      folder_mapping,
      env,
      is_todo,
      todo_completed,
  )


def _generate_random_notes(
    num_notes: int,
    exclusion_conditions: list[task_pb2.ExclusionCondition],
    relevant_folders: list[str],
    folder_mapping: dict[str, str],
    env: interface.AsyncEnv,
) -> list[sqlite_schema_utils.JoplinNote]:
  """Generates random notes with the given exclusion conditions."""
  return sqlite_schema_utils.get_random_items(
      num_notes,
      generate_item_fn=lambda: _generate_random_note(
          relevant_folders, folder_mapping, env
      ),
      filter_fn=lambda x: _check_note_conditions(
          x, exclusion_conditions, folder_mapping
      ),
  )


def _generate_random_note(
    relevant_folders: list[str],
    folder_mapping: dict[str, str],
    env: interface.AsyncEnv,
):
  """Generates a single random sqlite_schema_utils.JoplinNote object."""
  new_note = state_pb2.Note()
  # add to relevant folders 30% of the time:
  add_to_relevant_folder = random.random() < 0.3
  if add_to_relevant_folder:
    folder = random.choice(relevant_folders)
    if folder not in _FOLDERS:
      raise ValueError("Unexpected folder name: {}".format(folder))
  else:
    folder = random.choice(list(_FOLDERS.keys()))
  new_note.folder = folder
  new_note.is_todo = str(random.choice([True, False]))
  if new_note.is_todo:
    new_note.todo_completed = random.choice(["True", "False"])
  random_note = random.choice(_FOLDERS[folder])

  new_note.title = random_note["title"]
  new_note.body = random_note["body"]
  note = _create_note_from_proto(new_note, folder_mapping, env)
  return note


def _check_note_conditions(
    note: sqlite_schema_utils.JoplinNote,
    exclusion_conditions: list[task_pb2.ExclusionCondition],
    folder_mapping: dict[str, str],
) -> bool:
  """Evaluates the specified task against a set of exclusion conditions.

  A note is considered eligible if it does not satisfy all of the conditions
  specified in the exclusion_conditions list. Each condition is checked against
  various fields of the note. The note is eligible if not all of these
  conditions are met, ensuring it doesn't fall under any exclusion criteria
  defined.

  Args:
    note: The note to check.
    exclusion_conditions: All the conditions the note will be checked against,
      if they are all met, this note should be excluded and does not meet the
      conditions.
    folder_mapping: A map from folder name to ID as represented in the Folder
      table.

  Returns:
    A bool, True if the note does not meet all of the exclusion conditions,
    False otherwise.
  """
  if not exclusion_conditions:
    return True
  # Keeps track of whether an exclusion condition is met.
  all_conditions_met = True
  for condition in exclusion_conditions:
    if condition.field == "title":
      all_conditions_met = all_conditions_met and proto_utils.compare(
          note.title.lower(),
          condition.operation,
          condition.value.lower(),
      )
    elif condition.field == "folder":
      folder_name = [
          key.lower()
          for (key, value) in folder_mapping.items()
          if note.parent_id == value
      ]
      all_conditions_met = all_conditions_met and proto_utils.compare(
          folder_name[0],
          condition.operation,
          condition.value.lower(),
      )
    elif condition.field == "is_todo":
      all_conditions_met = all_conditions_met and proto_utils.compare(
          note.is_todo,
          condition.operation,
          1 if condition.value.lower() == "true" else 0,
      )
    elif condition.field == "todo_completed":
      all_conditions_met = all_conditions_met and proto_utils.compare(
          note.todo_completed,
          condition.operation,
          1 if condition.value.lower() == "true" else 0,
      )

  return not all_conditions_met


_RECIPES = [
    {
        "title": "Zesty Quinoa Salad",
        "body": (
            "Ingredients:\nCooked quinoa, chopped cucumber, diced tomato,"
            " crumbled feta cheese, lemon vinaigrette\nInstructions:\nToss"
            " ingredients together. Season to taste."
        ),
    },
    {
        "title": "Peanut Butter Power Smoothie",
        "body": (
            "Ingredients:\nPeanut butter, banana, milk of choice, protein"
            " powder, ice\nInstructions:\nBlend until smooth and creamy."
        ),
    },
    {
        "title": "Cheesy Veggie Scramble",
        "body": (
            "Ingredients:\nEggs, shredded cheese, diced bell pepper, chopped"
            " spinach, hot sauce (optional)\nInstructions:\nSauté peppers and"
            " spinach. Whisk eggs with cheese, add to pan, and scramble. Top"
            " with hot sauce if desired."
        ),
    },
    {
        "title": "Tuna Salad Surprise",
        "body": (
            "Ingredients:\nCanned tuna, celery, mayonnaise, relish, crackers or"
            " bread\nInstructions:\nMix tuna, celery, mayonnaise, and relish."
            " Serve on crackers or bread."
        ),
    },
    {
        "title": "Spicy Black Bean Wrap",
        "body": (
            "Ingredients:\nBlack beans, salsa, shredded cheese, avocado,"
            " tortilla\nInstructions:\nWarm beans, top tortilla with beans,"
            " salsa, cheese, and avocado."
        ),
    },
    {
        "title": "Fruity Yogurt Parfait",
        "body": (
            "Ingredients:\nGreek yogurt, granola, mixed"
            " berries\nInstructions:\nLayer yogurt, granola, and berries in a"
            " glass or jar."
        ),
    },
    {
        "title": "Sweet Potato Hash",
        "body": (
            "Ingredients:\nDiced sweet potato, onion, breakfast sausage"
            " (optional), seasoning\nInstructions:\nCook sweet potatoes and"
            " onion until tender. Add sausage if desired. Season to taste."
        ),
    },
    {
        "title": "Hummus and Veggie Delight",
        "body": (
            "Ingredients:\nHummus, pita bread, cucumber slices, carrot"
            " sticks\nInstructions:\nSpread hummus on pita, top with cucumbers"
            " and carrots."
        ),
    },
    {
        "title": "Creamy Tomato Soup",
        "body": (
            "Ingredients:\nCanned tomatoes, heavy cream, basil, grilled cheese"
            " sandwich (for dipping)\nInstructions:\nBlend tomatoes and cream,"
            " heat gently. Season with basil. Serve with grilled cheese for"
            " dipping."
        ),
    },
    {
        "title": "Apple Cinnamon Overnight Oats",
        "body": (
            "Ingredients:\nRolled oats, milk of choice, grated apple, cinnamon,"
            " pinch of brown sugar\nInstructions:\nCombine oats, milk, apple,"
            " cinnamon, and brown sugar. Refrigerate overnight."
        ),
    },
    {
        "title": "Chicken Tikka Masala",
        "body": (
            "Marinated chicken cooked in a creamy tomato sauce with aromatic"
            " spices."
        ),
    },
    {
        "title": "Chocolate Chip Cookies",
        "body": (
            "Classic recipe for chewy cookies with chocolate chips and a hint"
            " of vanilla."
        ),
    },
    {
        "title": "Beef Stir-Fry",
        "body": (
            "Quick and easy stir-fry with tenderbeef, colorful vegetables, and"
            " a savory sauce."
        ),
    },
    {
        "title": "Vegetarian Chili",
        "body": (
            "Hearty chili packed with beans, vegetables, and spices, perfect"
            " for a cold day."
        ),
    },
    {
        "title": "Salmon with Roasted Vegetables",
        "body": (
            "Healthy and flavorful dish with baked salmon and seasonal"
            " vegetables."
        ),
    },
    {
        "title": "Homemade Pizza",
        "body": (
            "Pizza dough recipe, sauce options, topping ideas for a"
            " customizable pizza night."
        ),
    },
    {
        "title": "Pasta Carbonara",
        "body": (
            "Creamy pasta dish with pancetta, eggs, Parmesan cheese, and black"
            " pepper."
        ),
    },
    {
        "title": "Pad Thai",
        "body": (
            "Stir-fried rice noodles with tofu or shrimp, eggs, bean sprouts,"
            " and a tangy sauce."
        ),
    },
    {
        "title": "Chicken Pot Pie",
        "body": (
            "Comforting pie filled with chicken, vegetables, and creamy sauce,"
            " topped with flaky crust."
        ),
    },
    {
        "title": "Shrimp Scampi",
        "body": (
            "Garlic butter shrimp with pasta, lemon juice, white wine, and"
            " fresh herbs."
        ),
    },
    {
        "title": "French Onion Soup",
        "body": (
            "Rich and flavorful soup with caramelized onions, beef broth, and"
            " crusty bread topped with melted cheese."
        ),
    },
    {
        "title": "Vegetable Curry",
        "body": (
            "Aromatic curry with a variety of vegetables, coconut milk, and"
            " spices."
        ),
    },
    {
        "title": "Quinoa Salad",
        "body": (
            "Healthy and refreshing salad with quinoa, vegetables, herbs, and a"
            " lemon vinaigrette."
        ),
    },
    {
        "title": "Banana Bread",
        "body": (
            "Moist and flavorful bread made with ripe bananas, perfect for"
            " breakfast or a snack."
        ),
    },
    {
        "title": "Breakfast Burritos",
        "body": (
            "Scrambled eggs, sausage, cheese, and vegetables wrapped in a warm"
            " tortilla."
        ),
    },
    {
        "title": "Chocolate Mousse",
        "body": (
            "Decadent dessert made with chocolate, eggs, and cream, perfect for"
            " a special occasion."
        ),
    },
    {
        "title": "Apple Pie",
        "body": (
            "Classic American dessert with a flaky crust filled with sweet and"
            " tart apples."
        ),
    },
    {
        "title": "Brownies",
        "body": "Fudgy or cakey brownies with chocolate chips or nuts.",
    },
    {
        "title": "Pancakes",
        "body": (
            "Fluffy pancakes topped with butter, maple syrup, and fresh fruit."
        ),
    },
    {
        "title": "Smoothie Recipes",
        "body": (
            "Various combinations of fruits, vegetables, yogurt, and protein"
            " powder for healthy and refreshing smoothies."
        ),
    },
]

_TASKS = [
    {
        "title": "Morning Routine",
        "body": (
            "Tasks:\nMake bed\nShower and get dressed\nHealthy"
            " breakfast\nReview daily schedule"
        ),
    },
    {
        "title": "Website Updates",
        "body": (
            "Tasks:\nAdd new product photos\nUpdate contact form\nFix broken"
            " link on About page\nRun website speed test"
        ),
    },
    {
        "title": "Grocery Trip",
        "body": (
            "Tasks:\nCheck pantry staples\nMake a list of needed"
            " items\nRemember reusable bags\nCheck for coupons or deals"
        ),
    },
    {
        "title": "Travel Packing",
        "body": (
            "Tasks:\nCheck weather forecast\nChoose outfits and pack\nGather"
            " toiletries and essentials\nPrint travel documents"
        ),
    },
    {
        "title": "Apartment Cleanup",
        "body": (
            "Tasks:\nDo the dishes\nVacuum floors\nTidy living room\nTake out"
            " the trash"
        ),
    },
    {
        "title": "Project Brainstorm",
        "body": (
            "Tasks:\nDefine project goals\nFree-write potential ideas\nCreate a"
            " mind map\nIdentify next steps"
        ),
    },
    {
        "title": "Email Inbox Zero",
        "body": (
            "Tasks:\nDelete junk mail\nRespond to urgent emails\nOrganize"
            " important emails into folders\nUnsubscribe from unwanted lists"
        ),
    },
    {
        "title": "Workout Routine",
        "body": (
            "Tasks:\n5-minute warmup\n30 minutes cardio\nStrength"
            " training\nCool-down and stretching"
        ),
    },
    {
        "title": "Meal Planning",
        "body": (
            "Tasks:\nChoose recipes for the week\nMake a grocery list\nPrep"
            " ingredients if possible\nPlan for leftovers"
        ),
    },
    {
        "title": "Relax and Recharge",
        "body": (
            "Tasks:\nRead a book\nTake a relaxing bath\nListen to calming"
            " music\nGo for an evening walk"
        ),
    },
    {
        "title": "Grocery Shopping",
        "body": (
            "- Milk, eggs, bread \n- Fruits and vegetables \n- Chicken breast"
            " \n- Pasta \n- Toilet paper"
        ),
    },
    {
        "title": "Pay Bills",
        "body": (
            "- Electricity bill due May 15th \n- Internet bill due May 20th \n-"
            " Credit card payment due May 25th"
        ),
    },
    {
        "title": "Schedule Doctor's Appointment",
        "body": "Call Dr. Smith's office to schedule a check-up for next week.",
    },
    {
        "title": "Email Project Update to Client",
        "body": (
            "Send a summary of project progress and next steps to Acme Corp. by"
            " EOD."
        ),
    },
    {
        "title": "Finish Presentation Slides for Team Meeting",
        "body": "Complete slides on Q2 marketing strategy by Tuesday morning.",
    },
    {
        "title": "Book Flight for Summer Vacation",
        "body": "Research and book round-trip flights to Hawaii for July.",
    },
    {
        "title": "Renew Driver's License",
        "body": (
            "Visit the DMV to renew driver's license before it expires next"
            " month."
        ),
    },
    {
        "title": "Research Summer Camps for Kids",
        "body": (
            "Find options for summer camps that align with kids' interests and"
            " ages."
        ),
    },
    {
        "title": "Meal Prep for the Week",
        "body": (
            "Cook a large batch of chicken and vegetables for lunches and"
            " dinners."
        ),
    },
    {
        "title": "Clean Out Garage",
        "body": (
            "Sort through items, donate unwanted items, organize remaining"
            " items."
        ),
    },
    {
        "title": "Write Thank You Notes for Wedding Gifts",
        "body": "Send personalized thank you notes to all wedding guests.",
    },
    {
        "title": "Call Mom for Her Birthday",
        "body": "Wish Mom a happy birthday and catch up.",
    },
    {
        "title": "Schedule Oil Change for Car",
        "body": (
            "Make an appointment with the mechanic for an oil change and tire"
            " rotation."
        ),
    },
    {
        "title": "Research New Laptop",
        "body": "Compare features, prices, and reviews of different laptops.",
    },
    {
        "title": "Plant Vegetable Garden",
        "body": (
            "Buy seeds or seedlings, prepare soil, plant vegetables in raised"
            " beds."
        ),
    },
    {
        "title": "Organize Closet",
        "body": (
            "Declutter clothes, donate or sell unwanted items, rearrange"
            " remaining clothes."
        ),
    },
    {
        "title": "File Taxes",
        "body": (
            "Gather tax documents, complete tax return, submit online or by"
            " mail."
        ),
    },
    {
        "title": "Plan Weekend Getaway",
        "body": (
            "Research destinations, book accommodations, plan activities for a"
            " short trip."
        ),
    },
    {
        "title": "Learn New Skill",
        "body": (
            "Enroll in online course or workshop on photography, coding, or"
            " language learning."
        ),
    },
    {
        "title": "Set Up Retirement Account",
        "body": (
            "Open a Roth IRA or 401(k) and start contributing to retirement"
            " savings."
        ),
    },
]

_ATTENDEES = [
    "Emily",
    "John",
    "Sarah",
    "David",
    "Ava",
    "Michael",
    "Jessica",
    "Joshua",
]
_ACTION_ITEMS = [
    "Follow up with client on proposal",
    "Draft project timeline",
    "Research market trends",
    "Schedule team check-in",
    "Create design mockups",
    "Update website content",
    "Review budget report",
    "Send out meeting follow-up email",
    "Conduct user testing",
    "Finalize presentation materials",
    "Order supplies for event",
    "Coordinate with external vendors",
    "Submit reimbursement requests",
]

_MEETING_NOTES = [
    {
        "title": "Team Meeting - May 6, 2024",
        "body": (
            "Agenda, discussion points, action items, decisions made, next"
            " steps."
        ),
    },
    {
        "title": "Client Meeting - Acme Corp. - April 25, 2024",
        "body": (
            "Attendees, project updates, feedback, next steps, action items."
        ),
    },
    {
        "title": "Brainstorming Session - New Product Ideas - April 18, 2024",
        "body": (
            "Generated ideas, pros and cons, feasibility assessment, next"
            " steps."
        ),
    },
    {
        "title": "Project Kickoff Meeting - Website Redesign - April 10, 2024",
        "body": (
            "Project scope, timeline, team roles, communication plan, budget."
        ),
    },
    {
        "title": "One-on-One Meeting with John - April 3, 2024",
        "body": (
            "Performance feedback, career goals discussion, development"
            " opportunities."
        ),
    },
    {
        "title": "Board Meeting - Q1 Financial Results - March 28, 2024",
        "body": (
            "Financial report review, key performance indicators, budget"
            " discussion, future outlook."
        ),
    },
    {
        "title": "Weekly Team Update - March 21, 2024",
        "body": (
            "Progress updates on individual tasks, roadblocks, upcoming"
            " deadlines, team collaboration."
        ),
    },
    {
        "title": "Client Presentation - Proposal Review - March 14, 2024",
        "body": (
            "Proposal summary, client feedback, questions, revisions needed,"
            " next steps."
        ),
    },
    {
        "title": "Training Session - New Software - March 7, 2024",
        "body": (
            "Key features, how-to guide, troubleshooting tips, Q&A session."
        ),
    },
    {
        "title": "Conference Call - Remote Team - February 28, 2024",
        "body": (
            "Agenda, discussion points, action items for remote team"
            " collaboration and communication."
        ),
    },
    {
        "title": "Performance Review Meeting - Sarah - February 21, 2024",
        "body": (
            "Strengths, areas for improvement, goals for next quarter,"
            " development plan."
        ),
    },
    {
        "title": "Departmental Budget Meeting - February 14, 2024",
        "body": (
            "Budget review, cost-cutting measures, resource allocation,"
            " approval process."
        ),
    },
    {
        "title": "All-Hands Meeting - Company Update - February 7, 2024",
        "body": (
            "CEO presentation on company performance, new initiatives, Q&A"
            " session."
        ),
    },
    {
        "title": "Client Feedback Session - Project X - January 31, 2024",
        "body": (
            "Gathering feedback from client on project X, addressing concerns,"
            " identifying improvements."
        ),
    },
    {
        "title": "Strategic Planning Meeting - January 24, 2024",
        "body": (
            "Defining long-term goals, SWOT analysis, strategy development,"
            " implementation plan."
        ),
    },
    {
        "title": "Team Building Workshop - January 17, 2024",
        "body": (
            "Activities and exercises to improve communication, collaboration,"
            " and trust among team members."
        ),
    },
    {
        "title": "New Hire Orientation - January 10, 2024",
        "body": (
            "Welcome new employees, introduce company culture, provide"
            " onboarding information."
        ),
    },
    {
        "title": "Annual Performance Review - Self-Assessment - December 2023",
        "body": (
            "Reflect on accomplishments, challenges, areas for growth, goals"
            " for the coming year."
        ),
    },
    {
        "title": "Holiday Party Planning Meeting - December 2023",
        "body": (
            "Venue selection, catering options, entertainment, budget,"
            " decorations, guest list."
        ),
    },
    {
        "title": "Year-End Review Meeting - December 2023",
        "body": (
            "Summary of company performance, achievements, challenges, goals"
            " for the next year."
        ),
    },
    {
        "title": "Project Kickoff",
        "body": (
            "Attendees:\n"
            + "\n".join(random.sample(_ATTENDEES, 3))
            + "\nAgenda:\nProject scope and objectives\nTimeline and"
            " milestones\nRoles and responsibilities\nAction Items:\n"
            + "\n".join(random.sample(_ACTION_ITEMS, 3))
        ),
    },
    {
        "title": "Marketing Strategy Brainstorm",
        "body": (
            "Attendees:\n"
            + "\n".join(random.sample(_ATTENDEES, 2))
            + "\nAgenda:\nTarget audience analysis\nCampaign ideas\nBudget"
            " considerations\nAction Items:\n"
            + "\n".join(random.sample(_ACTION_ITEMS, 2))
        ),
    },
    {
        "title": "Website Redesign Review",
        "body": (
            "Attendees:\n"
            + "\n".join(random.sample(_ATTENDEES, 4))
            + "\nAgenda:\nReview proposed wireframes\nDiscuss content"
            " updates\nFeedback on user experience\nAction Items:\n"
            + "\n".join(random.sample(_ACTION_ITEMS, 4))
        ),
    },
    {
        "title": "Quarterly Sales Meeting",
        "body": (
            "Attendees:\n"
            + "\n".join(random.sample(_ATTENDEES, 3))
            + "\nAgenda:\nSales performance review\nNew product launch"
            " updates\nMarket analysis\nAction Items:\n"
            + "\n".join(random.sample(_ACTION_ITEMS, 2))
        ),
    },
    {
        "title": "Team Building Workshop",
        "body": (
            "Attendees:\n"
            + "\n".join(random.sample(_ATTENDEES, 3))
            + "\nAgenda:\nTeam challenges discussion\nCommunication"
            " exercises\nGoal-setting activities\nAction Items:\n"
            + "\n".join(random.sample(_ACTION_ITEMS, 2))
        ),
    },
    {
        "title": "Client Project Update",
        "body": (
            "Attendees:\n"
            + "\n".join(random.sample(_ATTENDEES, 3))
            + "\nAgenda:\nProject progress status\nChallenges and"
            " solutions\nBudget review\nAction Items:\n"
            + "\n".join(random.sample(_ACTION_ITEMS, 2))
        ),
    },
    {
        "title": "HR Policy Review",
        "body": (
            "Attendees:\n"
            + "\n".join(random.sample(_ATTENDEES, 4))
            + "\nAgenda:\nReview updates to vacation policy\nDiscuss benefits"
            " package changes\nNew hire onboarding process\nAction Items:\n"
            + "\n".join(random.sample(_ACTION_ITEMS, 4))
        ),
    },
    {
        "title": "Design Sprint Planning",
        "body": (
            "Attendees:\n"
            + "\n".join(random.sample(_ATTENDEES, 3))
            + "\nAgenda:\nDefine problem statement\nBrainstorm"
            " solutions\nPrototype and test ideas\nAction Items:\n"
            + "\n".join(random.sample(_ACTION_ITEMS, 2))
        ),
    },
    {
        "title": "Budget Review Meeting",
        "body": (
            "Attendees:\n"
            + "\n".join(random.sample(_ATTENDEES, 2))
            + "\nAgenda:\nReview past quarter expenses\nAnalyze budget"
            " variances\nDiscuss upcoming project costs\nAction Items:\n"
            + "\n".join(random.sample(_ACTION_ITEMS, 2))
        ),
    },
    {
        "title": "All-Hands Team Meeting",
        "body": (
            "Attendees:\n"
            + "\n".join(random.sample(_ATTENDEES, 4))
            + "\nAgenda:\nCompany updates\nDepartment announcements\nCelebrate"
            " wins\nAction Items:\n"
            + "\n".join(random.sample(_ACTION_ITEMS, 3))
        ),
    },
]

_PERSONAL = [
    {
        "title": "Dream Journal Entry",
        "body": "Had a vivid dream about flyingover a vast ocean.",
    },
    {
        "title": "Bucket List",
        "body": "1. Learn to surf. 2. Visit Machu Picchu. 3. Write a novel.",
    },
    {
        "title": "Grocery List",
        "body": "Milk, eggs, bread, cheese, fruit, vegetables",
    },
    {
        "title": "Favorite Quotes",
        "body": (
            '"The only limit to our realization of tomorrow will be our doubts'
            ' of today." - Franklin D. Roosevelt'
        ),
    },
    {
        "title": "Movie Recommendations",
        "body": (
            "- Everything Everywhere All at Once \n- The Grand Budapest Hotel"
            " \n- Parasite"
        ),
    },
    {
        "title": "Birthday Gift Ideas for Mom",
        "body": "Spa day, gardening tools, personalized photo album",
    },
    {
        "title": "Workout Routine",
        "body": (
            "Monday: Cardio \nTuesday: Strength training \nWednesday: Rest"
            " \nThursday: Yoga \nFriday: Cardio \nWeekend: Active recovery"
        ),
    },
    {
        "title": "Travel Itinerary for Japan",
        "body": (
            "Day 1: Arrive in Tokyo, explore Shinjuku \nDay 2: Visit the"
            " Imperial Palace and Sensoji Temple \nDay 3: Take a day trip to"
            " Hakone \nDay 4: Travel to Kyoto, visit Kiyomizu-dera Temple \nDay"
            " 5: Explore Arashiyama Bamboo Forest \nDay 6: Depart from Osaka"
        ),
    },
    {
        "title": "Things I'm Grateful For",
        "body": "My family, my health, my friends, my home, my job",
    },
    {
        "title": "Home Improvement Projects",
        "body": (
            "Repaint the living room, install new kitchen backsplash, build a"
            " deck in the backyard"
        ),
    },
    {
        "title": "Party Planning Checklist",
        "body": (
            "Send invitations, plan menu, decorate venue, create playlist, hire"
            " photographer"
        ),
    },
    {
        "title": "Random Thoughts",
        "body": (
            "I wonder why cats purr? Is time travel possible? What's the"
            " meaning of life?"
        ),
    },
    {
        "title": "Password Ideas",
        "body": (
            "Combination of letters, numbers, symbols, not easily guessable"
        ),
    },
    {
        "title": "Favorite Recipes",
        "body": "Chocolate chip cookies, lasagna, chicken tikka masala",
    },
    {
        "title": "Book Recommendations",
        "body": (
            "- The Lord of the Rings \n- The Hitchhiker's Guide to the Galaxy"
            " \n- Pride and Prejudice"
        ),
    },
    {
        "title": "Song Lyrics I Love",
        "body": '"Imagine no possessions, I wonder if you can." - John Lennon',
    },
    {
        "title": "Things to Do This Weekend",
        "body": (
            "Hike in the mountains, visit a museum, have a picnic in the park"
        ),
    },
    {
        "title": "Self-Care Ideas",
        "body": (
            "Take a bubble bath, read a good book, meditate, spend time in"
            " nature"
        ),
    },
    {
        "title": "Personal Goals for the Year",
        "body": (
            "1. Save for a down payment on a house. 2. Get a promotion at work."
            " 3. Run a marathon."
        ),
    },
]

_WORK = [
    {
        "title": "Meeting Notes - Q2 Marketing Strategy",
        "body": (
            "Discussed social media campaigns, new product launch timeline,"
            " budget allocation."
        ),
    },
    {
        "title": "Project Timeline - Website Redesign",
        "body": (
            "Phase 1: Wireframes due May 15th \nPhase 2: Design approvals by"
            " June 1st \nPhase 3: Development complete by July 15th \nPhase 4:"
            " Launch by August 1st"
        ),
    },
    {
        "title": "Performance Review Talking Points",
        "body": (
            "- Exceeded sales targets by 15% \n- Successfully led"
            " cross-functional team \n- Developed new client onboarding process"
        ),
    },
    {
        "title": "Client Feedback - Acme Corp.",
        "body": (
            "Positive feedback on project delivery, requested additional"
            " features for Phase 2."
        ),
    },
    {
        "title": "To-Do List",
        "body": (
            "1. Respond to client emails \n2. Prepare presentation for team"
            " meeting \n3. Review budget proposal \n4. Schedule one-on-one with"
            " Sarah"
        ),
    },
    {
        "title": "Conference Notes - Tech Summit 2024",
        "body": (
            "Key takeaways on emerging technologies, potential applications for"
            " our industry."
        ),
    },
    {
        "title": "Team Brainstorming - New Product Ideas",
        "body": (
            "Generated 15 potential product ideas, will narrow down to top 3"
            " for further development."
        ),
    },
    {
        "title": "Employee Onboarding Checklist",
        "body": (
            "1. Set up workstation \n2. Provide access to company systems \n3."
            " Schedule training sessions \n4. Assign mentor"
        ),
    },
    {
        "title": "Company Policies and Procedures",
        "body": (
            "Links to documents on vacation policy, expense reimbursement, code"
            " of conduct."
        ),
    },
    {
        "title": "Travel Itinerary - Client Visit",
        "body": (
            "Flights booked, hotel reservations confirmed, meeting schedule"
            " finalized."
        ),
    },
    {
        "title": "KPI Report - Q1 2024",
        "body": (
            "Sales revenue up 10%, customer satisfaction rating at 92%,"
            " employee turnover rate at 5%."
        ),
    },
    {
        "title": "Code Snippets - Python",
        "body": (
            "Useful code examples for data analysis, web scraping, automation"
            " tasks."
        ),
    },
    {
        "title": "Industry News and Trends",
        "body": (
            "Summary of recent articles on market developments, competitor"
            " activity, regulatory changes."
        ),
    },
    {
        "title": "Job Descriptions - Open Positions",
        "body": (
            "Detailed descriptions for Marketing Manager, Software Engineer,"
            " Sales Representative roles."
        ),
    },
    {
        "title": "Meeting Minutes - Weekly Team Update",
        "body": (
            "Summary of discussion points, action items, decisions made during"
            " the meeting."
        ),
    },
    {
        "title": "Training Materials - New Software",
        "body": (
            "Step-by-step guides, video tutorials, FAQs for learning how to use"
            " the new software."
        ),
    },
    {
        "title": "Contact List - Key Clients",
        "body": (
            "Names, email addresses, phone numbers, company affiliations of"
            " important clients."
        ),
    },
    {
        "title": "Budget Proposal - 2025",
        "body": (
            "Detailed breakdown of projected expenses and revenue for each"
            " department."
        ),
    },
    {
        "title": "Professional Development Resources",
        "body": (
            "Links to online courses, workshops, conferences relevant to career"
            " growth."
        ),
    },
    {
        "title": "Team Building Activities",
        "body": (
            "Ideas for virtual and in-person activities to improve team morale"
            " and collaboration."
        ),
    },
]

_SCHOOL = [
    {
        "title": "Lecture Notes - Intro to Psychology",
        "body": (
            "Key concepts: nature vs. nurture, cognitive development, social"
            " psychology."
        ),
    },
    {
        "title": "Reading List - American Literature",
        "body": "- The Scarlet Letter \n- The Great Gatsby \n- Moby Dick",
    },
    {
        "title": "Study Guide - Calculus Midterm",
        "body": "Topics covered: derivatives, integrals, limits, applications.",
    },
    {
        "title": "Research Paper Outline - Climate Change",
        "body": (
            "I. Introduction \nII. Causes of Climate Change \nIII. Impacts on"
            " the Environment \nIV. Solutions \nV. Conclusion"
        ),
    },
    {
        "title": "Group Project Notes - Marketing Campaign",
        "body": (
            "Team members: Sarah, David, Emily. Due date: May 30th. Focus:"
            " promoting a new sustainable product."
        ),
    },
    {
        "title": "Exam Schedule - Spring Semester",
        "body": (
            "May 10th: Calculus \nMay 15th: American Literature \nMay 20th:"
            " Psychology"
        ),
    },
    {
        "title": "Class Syllabus - Introduction to Computer Science",
        "body": (
            "Course overview, grading policy, weekly schedule, required"
            " readings."
        ),
    },
    {
        "title": "Essay Draft - The Role of Technology in Education",
        "body": (
            "Discusses the benefits and challenges of integrating technology"
            " into classrooms."
        ),
    },
    {
        "title": "Lab Report - Chemistry Experiment",
        "body": "Purpose, materials, procedure, results, analysis, conclusion.",
    },
    {
        "title": "Flashcards - Spanish Vocabulary",
        "body": "Front: hola \nBack: hello",
    },
    {
        "title": "Scholarship Application Deadlines",
        "body": (
            "May 1st: National Merit Scholarship \nJune 1st: College Board"
            " Opportunity Scholarships"
        ),
    },
    {
        "title": "Student Club Meeting Notes - Debate Club",
        "body": (
            "Discussed upcoming tournament, new member recruitment, fundraising"
            " ideas."
        ),
    },
    {
        "title": "Campus Resources - Writing Center",
        "body": (
            "Offers one-on-one tutoring for essays, research papers, and other"
            " writing assignments."
        ),
    },
    {
        "title": "Professor Contact Information",
        "body": (
            "Dr. Smith: jsmith@university.edu \nDr. Johnson:"
            " sjohnson@university.edu"
        ),
    },
    {
        "title": "Financial Aid Checklist",
        "body": (
            "1. Submit FAFSA \n2. Apply for scholarships \n3. Contact financial"
            " aid office"
        ),
    },
    {
        "title": "Campus Event Calendar",
        "body": (
            "May 10th: Spring Concert \nMay 15th: Career Fair \nMay 20th: Guest"
            " Speaker Lecture"
        ),
    },
    {
        "title": "Study Tips for Final Exams",
        "body": (
            "Create a study schedule, review notes regularly, form study"
            " groups, practice with past exams."
        ),
    },
    {
        "title": "Internship Opportunities - Summer 2024",
        "body": (
            "Marketing internship at XYZ Company, Research internship at"
            " ABC Lab"
        ),
    },
    {
        "title": "Book Recommendations from Professor",
        "body": (
            "- Sapiens: A Brief History of Humankind \n- Thinking, Fast and"
            " Slow \n- Outliers: The Story of Success"
        ),
    },
    {
        "title": "Study Abroad Programs - Fall 2024",
        "body": (
            "Programs available in Spain, France, Italy, Germany, and Japan."
        ),
    },
]

_HOME = [
    {
        "title": "Home Maintenance Schedule",
        "body": (
            "Spring: clean gutters, check roof for damage, service AC \nSummer:"
            " mow lawn weekly, trim hedges, check sprinkler system \nFall: rake"
            " leaves, clean chimney, winterize pipes \nWinter: check for ice"
            " dams, shovel snow, change air filters"
        ),
    },
    {
        "title": "Grocery List",
        "body": (
            "- Milk \n- Eggs \n- Bread \n- Cheese \n- Fruits \n- Vegetables \n-"
            " Toilet paper"
        ),
    },
    {
        "title": "Recipe - Chicken Noodle Soup",
        "body": (
            "Ingredients: chicken, noodles, carrots, celery, onion, broth,"
            " herbs."
        ),
    },
    {
        "title": "Cleaning Checklist",
        "body": (
            "Kitchen: clean countertops, wipe down appliances, sweep and mop"
            " floor \nBathroom: clean toilet, sink, shower/tub, mirrors"
            " \nLiving room: dust furniture, vacuum carpet, fluff pillows"
        ),
    },
    {
        "title": "Home Renovation Ideas",
        "body": (
            "- Update kitchen cabinets \n- Refinish hardwood floors \n- Paint"
            " living room walls"
        ),
    },
    {
        "title": "Packing List - Summer Vacation",
        "body": (
            "- Clothes for warm weather \n- Swimsuit \n- Sunscreen \n- Hat \n-"
            " Sunglasses"
        ),
    },
    {
        "title": "Gardening Tips",
        "body": (
            "Water plants regularly, fertilize monthly, prune as needed, check"
            " for pests."
        ),
    },
    {
        "title": "Emergency Contact List",
        "body": "Police: 911 \nFire: 911 \nNeighbor: (123) 456-7890",
    },
    {
        "title": "Wi-Fi Password",
        "body": "Network Name: MyHomeWifi \nPassword: supersecretpassword",
    },
    {
        "title": "Home Inventory",
        "body": (
            "List of valuable items in case of insurance claim (electronics,"
            " jewelry, furniture)."
        ),
    },
    {
        "title": "Houseplant Care Guide",
        "body": (
            "Specific care instructions for each houseplant (watering"
            " frequency, light needs, soil type)."
        ),
    },
    {
        "title": "Utility Bill Due Dates",
        "body": (
            "Electricity: 15th of every month \nGas: 20th of every month"
            " \nWater: 5th of every month"
        ),
    },
    {
        "title": "Party Planning - Birthday",
        "body": "Guest list, menu, decorations, entertainment.",
    },
    {
        "title": "Neighborhood Watch Meeting Notes",
        "body": "Discussed recent crime trends, safety tips, upcoming events.",
    },
    {
        "title": "Pet Care Reminders",
        "body": (
            "Feed dog twice a day, walk dog daily, clean litter box, schedule"
            " vet checkups."
        ),
    },
    {
        "title": "DIY Project - Bookshelf",
        "body": "Materials needed: wood, screws, nails, saw, drill.",
    },
    {
        "title": "Movie Night Ideas",
        "body": "List of family-friendly movies to watch together.",
    },
    {
        "title": "Recipes to Try",
        "body": "Links or descriptions of new recipes to cook at home.",
    },
    {
        "title": "Home Security Checklist",
        "body": (
            "Lock doors and windows, install alarm system, set timers for"
            " lights, don't hide spare keys outside."
        ),
    },
    {
        "title": "Holiday Decoration Ideas",
        "body": "Themes, color schemes, DIY crafts, shopping list.",
    },
]

_PROJECTS = [
    {
        "title": "Community Garden Project",
        "body": (
            "Create a shared green space for the neighborhood, promoting"
            " sustainable food production and community connection."
        ),
    },
    {
        "title": "Home Renovation - Kitchen Remodel",
        "body": (
            "Design plans, budget, materials list, contractor quotes, timeline"
            " for a kitchen renovation."
        ),
    },
    {
        "title": "Mobile App Development - Expense Tracker",
        "body": (
            "Project outline, wireframes, technology stack, development"
            " timeline, marketing plan."
        ),
    },
    {
        "title": "Book Writing Project - Mystery Novel",
        "body": (
            "Outline, character sketches, plot points, research notes, writing"
            " schedule."
        ),
    },
    {
        "title": "Online Course Creation - Web Development Basics",
        "body": (
            "Course curriculum, lesson plans, video scripts, assessment"
            " questions, marketing strategy."
        ),
    },
    {
        "title": "DIY Furniture Building - Coffee Table",
        "body": (
            "Design plans, materials list, tools required, step-by-step"
            " instructions, finishing options."
        ),
    },
    {
        "title": "Photography Portfolio Website",
        "body": (
            "Website design mockups, image selection, content writing, hosting"
            " platform, launch plan."
        ),
    },
    {
        "title": "Charity Fundraising Event - 5K Run/Walk",
        "body": (
            "Event logistics, sponsorships, marketing plan, registration"
            " process, volunteer coordination."
        ),
    },
    {
        "title": "Small Business Launch - Handmade Jewelry",
        "body": (
            "Business plan, product line, branding, pricing, marketing"
            " strategy, online store setup."
        ),
    },
    {
        "title": "Art Installation - Public Sculpture",
        "body": (
            "Concept sketches, material selection, fabrication process,"
            " installation logistics, funding proposals."
        ),
    },
    {
        "title": "Documentary Film - Local Environmental Issues",
        "body": (
            "Research topics, interview subjects, filming locations, script"
            " outline, editing plan."
        ),
    },
    {
        "title": "Music Album Recording - Indie Rock Band",
        "body": (
            "Songwriting, studio booking, recording schedule, mixing and"
            " mastering, album artwork design."
        ),
    },
    {
        "title": "Community Theater Production - Shakespeare Play",
        "body": (
            "Casting calls, rehearsal schedule, set design, costume design,"
            " marketing plan."
        ),
    },
    {
        "title": "Coding Challenge - Machine Learning Algorithm",
        "body": (
            "Problem statement, data set, algorithm implementation, performance"
            " evaluation, results analysis."
        ),
    },
    {
        "title": "Website Redesign - Non-Profit Organization",
        "body": (
            "Needs analysis, wireframes, design mockups, content migration,"
            " development plan."
        ),
    },
    {
        "title": "Product Launch - Smart Home Device",
        "body": (
            "Market research, product specifications, pricing strategy,"
            " marketing campaign, launch timeline."
        ),
    },
    {
        "title": "Interior Design Project - Living Room Makeover",
        "body": (
            "Mood board, furniture selection, color palette, lighting plan,"
            " accessories."
        ),
    },
    {
        "title": "Travel Blog - Solo Trip Around Southeast Asia",
        "body": (
            "Itinerary, travel tips, destination highlights, photography plan,"
            " content schedule."
        ),
    },
    {
        "title": "Language Learning Project - Conversational Spanish",
        "body": (
            "Study plan, learning resources, practice activities, language"
            " exchange partners, progress tracking."
        ),
    },
    {
        "title": "Health and Fitness Challenge - 30-Day Transformation",
        "body": (
            "Workout plan, meal plan, progress tracking, motivation tips,"
            " before-and-after photos."
        ),
    },
]

_IDEAS = [
    {
        "title": "Personalized Pet Portraits",
        "body": (
            "Offer custom-painted portraits of pets based on photos provided by"
            " clients."
        ),
    },
    {
        "title": "Language Learning App",
        "body": (
            "Gamified language learning app with interactive exercises and"
            " personalized feedback."
        ),
    },
    {
        "title": "Sustainable Fashion Subscription Box",
        "body": (
            "Curated selection of eco-friendly clothing and accessories"
            " delivered monthly."
        ),
    },
    {
        "title": "Virtual Reality Escape Room",
        "body": "Immersive escape room experience using VR technology.",
    },
    {
        "title": "Food Delivery Service for Dietary Restrictions",
        "body": (
            "Cater to people with allergies, intolerances, or specific diets."
        ),
    },
    {
        "title": "Mental Health Support App",
        "body": (
            "Provides resources, guided meditations, and online therapy"
            " options."
        ),
    },
    {
        "title": "AI-Powered Personalized Travel Itinerary Generator",
        "body": (
            "Creates custom travel plans based on user preferences and"
            " interests."
        ),
    },
    {
        "title": "Smart Home Gardening System",
        "body": (
            "Automated watering, lighting, and nutrient monitoring for indoor"
            " plants."
        ),
    },
    {
        "title": "Subscription Box for Book Lovers",
        "body": (
            "Curated selection of books, bookish goodies, and exclusive author"
            " content."
        ),
    },
    {
        "title": "Online Platform for Local Artisans",
        "body": (
            "Showcase and sell handmade crafts and artwork directly to"
            " consumers."
        ),
    },
    {
        "title": "Eco-Friendly Cleaning Products",
        "body": (
            "Develop and market a line of sustainable cleaning products for"
            " households."
        ),
    },
    {
        "title": "Personalized Nutrition Coaching App",
        "body": (
            "Offers customized meal plans and fitness recommendations based on"
            " individual goals and needs."
        ),
    },
    {
        "title": "Social Media Platform for Pet Owners",
        "body": (
            "Connect with other pet owners, share photos, and find pet-related"
            " services."
        ),
    },
    {
        "title": "Online Marketplace for Vintage Clothing",
        "body": "Buy and sell unique vintage clothing and accessories.",
    },
    {
        "title": "Augmented Reality Furniture Shopping App",
        "body": (
            "Visualize how furniture would look in your home before buying."
        ),
    },
    {
        "title": "Subscription Service for Sustainable Home Goods",
        "body": (
            "Deliver eco-friendly household products and reusable alternatives"
            " to single-use items."
        ),
    },
    {
        "title": "Crowdfunding Platform for Creative Projects",
        "body": (
            "Support artists, musicians, filmmakers, and other creatives in"
            " funding their projects."
        ),
    },
    {
        "title": "Mobile App for Finding Local Volunteer Opportunities",
        "body": (
            "Connect volunteers with organizations in need of their skills and"
            " time."
        ),
    },
    {
        "title": "Online Marketplace for Personalized Gifts",
        "body": "Offer custom-made gifts for various occasions and interests.",
    },
    {
        "title": "Zero-Waste Grocery Store",
        "body": (
            "Sell bulk food items and package-free products to reduce waste."
        ),
    },
]

_HEALTH = [
    {
        "title": "Workout Routine - Strength Training",
        "body": (
            "Exercises for each muscle group, sets, reps, rest periods, weekly"
            " schedule."
        ),
    },
    {
        "title": "Meal Plan - Week of May 6th",
        "body": (
            "Breakfast, lunch, dinner, snacks for each day, grocery list,"
            " recipes."
        ),
    },
    {
        "title": "Doctor's Appointment Notes - May 3rd",
        "body": (
            "Summary of discussion with doctor, diagnosis, treatment plan,"
            " medication list, follow-up appointments."
        ),
    },
    {
        "title": "Medication Schedule",
        "body": (
            "List of medications, dosage, frequency, time to take, potential"
            " side effects, refills needed."
        ),
    },
    {
        "title": "Health Goals for 2024",
        "body": (
            "Lose 10 pounds, run a 5K, reduce stress, improve sleep quality,"
            " get regular checkups."
        ),
    },
    {
        "title": "Fitness Tracker Data - April 2024",
        "body": (
            "Steps taken, calories burned, active minutes, sleep duration,"
            " heart rate."
        ),
    },
    {
        "title": "Mental Health Resources",
        "body": (
            "Contact information for therapists, support groups, hotlines,"
            " websites, apps for mental well-being."
        ),
    },
    {
        "title": "Healthy Recipes to Try",
        "body": (
            "Links or descriptions of nutritious recipes for breakfast, lunch,"
            " dinner, snacks, desserts."
        ),
    },
    {
        "title": "Nutrition Tips",
        "body": (
            "Guidelines for balanced eating, portion control, healthy food"
            " swaps, meal prep ideas."
        ),
    },
    {
        "title": "Exercise Ideas",
        "body": (
            "Variety of workouts for different fitness levels and interests"
            " (cardio, strength, flexibility)."
        ),
    },
    {
        "title": "Sleep Hygiene Checklist",
        "body": (
            "Tips for creating a relaxing bedtime routine, improving sleep"
            " environment, getting quality sleep."
        ),
    },
    {
        "title": "Health Insurance Information",
        "body": (
            "Policy number, provider contact information, coverage details,"
            " copayments, deductibles."
        ),
    },
    {
        "title": "Allergy Information",
        "body": (
            "List of allergies, triggers, symptoms, treatment plan, emergency"
            " contact information."
        ),
    },
    {
        "title": "Medical History",
        "body": (
            "Summary of past illnesses, surgeries, medications, immunizations,"
            " family medical history."
        ),
    },
    {
        "title": "Weight Loss Progress Tracker",
        "body": (
            "Starting weight, current weight, goal weight, weight loss"
            " milestones, measurements."
        ),
    },
    {
        "title": "Meditation and Mindfulness Resources",
        "body": (
            "Guided meditations, mindfulness exercises, breathing techniques"
            " for stress reduction."
        ),
    },
    {
        "title": "Health-Related Articles and Blogs",
        "body": (
            "Links to informative articles on health topics, wellness trends,"
            " medical research."
        ),
    },
    {
        "title": "Health Challenges and Solutions",
        "body": (
            "Personal notes on overcoming health obstacles, strategies for"
            " managing chronic conditions."
        ),
    },
    {
        "title": "Fitness Class Schedule",
        "body": (
            "Days, times, locations of fitness classes (yoga, Pilates, Zumba,"
            " strength training)."
        ),
    },
    {
        "title": "Food Diary",
        "body": (
            "Record of daily food intake, calories, macronutrients,"
            " micronutrients, water intake."
        ),
    },
]

_TRAVEL = [
    {
        "title": "Trip Itinerary - Europe Summer 2024",
        "body": (
            "Flights, accommodations, transportation, daily activities,"
            " sightseeing plans, restaurant reservations."
        ),
    },
    {
        "title": "Packing List - Beach Vacation",
        "body": (
            "Clothing, toiletries, electronics, travel documents, beach gear,"
            " first-aid kit."
        ),
    },
    {
        "title": "Travel Budget - Southeast Asia Backpacking",
        "body": (
            "Estimated costs for flights, accommodation, food, transportation,"
            " activities, visas."
        ),
    },
    {
        "title": "Travel Insurance Information",
        "body": (
            "Policy number, provider contact information, coverage details,"
            " claim procedures."
        ),
    },
    {
        "title": "Language Phrasebook - Italian",
        "body": (
            "Common phrases for greetings, directions, ordering food, asking"
            " for help."
        ),
    },
    {
        "title": "Travel Tips - Staying Healthy Abroad",
        "body": (
            "Vaccinations, food and water safety, jet lag prevention, managing"
            " common illnesses."
        ),
    },
    {
        "title": "Bucket List Destinations",
        "body": (
            "Dream travel destinations with reasons for visiting and potential"
            " activities."
        ),
    },
    {
        "title": "Hotel Reviews - Paris",
        "body": (
            "Reviews of hotels in Paris based on location, amenities, price,"
            " service, cleanliness."
        ),
    },
    {
        "title": "Flight Confirmation - Round-trip to Tokyo",
        "body": (
            "Airline, flight numbers, departure and arrival times, seat"
            " assignments, baggage allowance."
        ),
    },
    {
        "title": "Restaurant Recommendations - Rome",
        "body": (
            "List of restaurants in Rome with cuisine type, price range,"
            " location, reviews."
        ),
    },
    {
        "title": "Travel Photography Tips",
        "body": (
            "Equipment recommendations, composition techniques, capturing"
            " different types of travel photos."
        ),
    },
    {
        "title": "Visa Requirements - China",
        "body": (
            "Information on visa types, application process, required"
            " documents, processing times."
        ),
    },
    {
        "title": "Travel Journal - Road Trip Across America",
        "body": (
            "Daily entries documenting experiences, observations, thoughts, and"
            " feelings during the trip."
        ),
    },
    {
        "title": "Transportation Options - London",
        "body": (
            "Information on public transportation (tube, buses), taxis,"
            " ride-sharing services, bike rentals."
        ),
    },
    {
        "title": "Travel Apps and Websites",
        "body": (
            "List of useful apps for booking flights, hotels, finding"
            " restaurants, translating languages, navigating."
        ),
    },
    {
        "title": "Cultural Etiquette Tips - Japan",
        "body": (
            "Customs and traditions to be aware of, do's and don'ts,"
            " appropriate behavior in different settings."
        ),
    },
    {
        "title": "Solo Travel Tips",
        "body": (
            "Advice on staying safe, meeting people, planning activities,"
            " budgeting for solo travelers."
        ),
    },
    {
        "title": "Travel Gear Checklist",
        "body": (
            "Essentials like luggage, backpacks, travel adapters, toiletries,"
            " first-aid kit, travel pillow."
        ),
    },
    {
        "title": "Festivals and Events Calendar - Europe",
        "body": (
            "List of upcoming festivals, cultural events, concerts, exhibitions"
            " in different European countries."
        ),
    },
    {
        "title": "Travel Photography Gear",
        "body": (
            "Camera, lenses, tripod, filters, memory cards, batteries, cleaning"
            " supplies."
        ),
    },
]

_FINANCE = [
    {
        "title": "Monthly Budget - May 2024",
        "body": (
            "Income, expenses, savings goals, spending categories, debt"
            " repayment plan."
        ),
    },
    {
        "title": "Investment Portfolio Summary",
        "body": (
            "Breakdown of investments (stocks, bonds, mutual funds),"
            " performance overview, asset allocation."
        ),
    },
    {
        "title": "Retirement Savings Plan",
        "body": (
            "Contribution schedule, target retirement age, projected retirement"
            " income, investment options."
        ),
    },
    {
        "title": "Tax Preparation Checklist - 2023",
        "body": (
            "Documents needed (W-2, 1099 forms), deductions to claim, tax"
            " filing deadline."
        ),
    },
    {
        "title": "Mortgage Payment Schedule",
        "body": (
            "Loan amount, interest rate, monthly payment, remaining balance,"
            " amortization schedule."
        ),
    },
    {
        "title": "Emergency Fund Progress",
        "body": (
            "Current balance, savings goal, monthly contributions, target"
            " amount (3-6 months of expenses)."
        ),
    },
    {
        "title": "Credit Card Statement - April 2024",
        "body": (
            "Transactions, due date, minimum payment, outstanding balance,"
            " rewards earned."
        ),
    },
    {
        "title": "Financial Goals for 2024",
        "body": (
            "Save for a down payment on a house, pay off student loan debt,"
            " increase retirement contributions."
        ),
    },
    {
        "title": "Investment Research - Tech Stocks",
        "body": (
            "Analysis of potential tech companies to invest in, growth"
            " projections, risk assessment."
        ),
    },
    {
        "title": "Budgeting Tips & Tricks",
        "body": (
            "Strategies for saving money, reducing expenses, tracking spending,"
            " automating savings."
        ),
    },
    {
        "title": "Financial Advisor Contact Information",
        "body": (
            "Name, email address, phone number, website of financial advisor."
        ),
    },
    {
        "title": "Online Banking Login Details",
        "body": (
            "Username, password, security questions, account numbers for online"
            " banking access."
        ),
    },
    {
        "title": "Insurance Policies Summary",
        "body": (
            "Coverage details for health, auto, home, life insurance policies,"
            " contact information for insurers."
        ),
    },
    {
        "title": "Debt Repayment Plan",
        "body": (
            "List of debts (credit cards, student loans), balances, interest"
            " rates, minimum payments, payoff strategies."
        ),
    },
    {
        "title": "Expense Tracking Spreadsheet",
        "body": (
            "Template for tracking daily expenses, categorizing spending,"
            " identifying areas for saving."
        ),
    },
    {
        "title": "Financial News & Analysis",
        "body": (
            "Summary of articles and reports on market trends, economic"
            " outlook, investment strategies."
        ),
    },
    {
        "title": "Personal Finance Resources",
        "body": (
            "Links to helpful websites, blogs, podcasts, books on personal"
            " finance topics."
        ),
    },
    {
        "title": "College Savings Plan - 529 Account",
        "body": (
            "Beneficiary information, investment options, contribution history,"
            " projected college costs."
        ),
    },
    {
        "title": "Estate Planning Documents",
        "body": (
            "Will, power of attorney, healthcare directive, beneficiaries,"
            " executor information."
        ),
    },
    {
        "title": "Charitable Giving Log",
        "body": (
            "Record of donations to charitable organizations, amounts, dates,"
            " tax-deductible status."
        ),
    },
]

# Folder names contains all possibilities for the revelant folder names
# in the task proto.
_FOLDERS = {
    "Recipes": _RECIPES,
    "Tasks": _TASKS,
    "Meeting Notes": _MEETING_NOTES,
    "Personal": _PERSONAL,
    "Work": _WORK,
    "School": _SCHOOL,
    "Home": _HOME,
    "Projects": _PROJECTS,
    "Ideas": _IDEAS,
    "Health": _HEALTH,
    "Travel": _TRAVEL,
    "Finance": _FINANCE,
}
```

### `official/install/android_world/task_evals/information_retrieval/proto/__init__.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/proto/__init__.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Protocol buffer definitions for information retrieval tasks."""
```

### `official/install/android_world/task_evals/information_retrieval/proto/state.proto`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/proto/state.proto`

```text
// Format for representing the state of an Android device.

syntax = "proto2";

package android_world.task_evals.information_retrieval.proto;

// Represents app-specific states on an Android device.
message State {
  optional Calendar calendar = 1;
  optional TasksApp tasks_app = 2;
  optional SportsActivityApp sports_activity_app = 3;
  optional NotesApp notes_app = 4;
}

message NotesApp {
  repeated Note notes = 1;
}

message Note {
  optional string folder = 1;
  optional string title = 2;
  optional string body = 3;
  optional string is_todo = 4;
  optional string todo_completed = 5;
}

message SportsActivityApp {
  repeated SportsActivity sports_activities = 1;
}

message SportsActivity {
  optional string name = 1;
  optional string description = 2;

  // For valid categories see _ACTIVITY_CATEGORIES:
  // intelligence/dbw/modeling/eval/task_evals/information_retrieval/activity_app_utils.py
  optional string category = 3;

  // Supported format for start_date:
  // - '<month> <day> <year>'
  //    - e.g. 'October 30 2024'
  optional string start_date = 4;
  // The start time can be specified with the following formats:
  // - <24 hour format>:<minutes>
  //    e.g. 14:40
  // - <12 hour format>am|pm
  //    e.g. 2pm, 11am
  // - <12 hour format>:<minutes>am|pm
  //    e.g. 2:30pm, 11:55am
  optional string start_time = 5;

  // The duration of the activity in minutes. Should only contain numbers or a
  // placeholder value.
  optional string duration = 6;

  // Distance in meters
  optional string total_distance = 7;

  // Elevation is in meters.
  optional string elevation_gain = 8;
  optional string elevation_loss = 9;
}

message TasksApp {
  repeated TasksAppTask tasks_app_tasks = 1;
}

message TasksAppTask {
  optional string title = 1;

  // The priority of the task, an integer from 0 to 3 where 0 is the highest
  // priority.
  optional string importance = 2;

  // The due date is specified with the following format:
  // - '<month> <day> <year>'
  //    - e.g. 'October 30 2024'
  optional string due_date = 3;
  // The due time can be specified with the following formats:
  // - <24 hour format>:<minutes>
  //    e.g. 14:40
  // - <12 hour format>am|pm
  //    e.g. 2pm, 11am
  // - <12 hour format>:<minutes>am|pm
  //    e.g. 2:30pm, 11:55am
  optional string due_time = 4;

  // Follows same format as due_date.
  optional string hide_until_date = 5;

  // Follows same format as due_time.
  optional string hide_until_time = 6;

  // Follows same format as due_date.
  optional string completed_date = 8;

  // Follows same format as due_time.
  optional string completed_time = 9;
  optional string notes = 10;
}

message Calendar {
  optional string app_name = 2;
  repeated Event events = 1;
}

// Represents a Calendar event.
message Event {
  // The start date is specified with the following format:
  // - '<month> <day> <year>'
  //    - e.g. 'October 30 2024'
  optional string start_date = 1;

  // The start time can be specified with the following formats:
  // - <24 hour format>:<minutes>
  //    e.g. 14:40
  // - <12 hour format>am|pm
  //    e.g. 2pm, 11am
  // - <12 hour format>:<minutes>am|pm
  //    e.g. 2:30pm, 11:55am
  optional string start_time = 2;

  // The duration of the event. It needs to specified either in minutes or
  // hours. e.g. '30m', '30 m', '30 minutes'. '2h', '2 h', '2 hours'
  optional string duration = 3;

  optional string description = 4;
  optional string title = 5;
  optional string location = 6;
}
```

### `official/install/android_world/task_evals/information_retrieval/proto/task.proto`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/proto/task.proto`

```text
// Format for tasks given to agents to perform.

syntax = "proto2";

package android_world.task_evals.information_retrieval.proto;

import "android_world/task_evals/information_retrieval/proto/state.proto";

// Wrapper around Task to create a collection of them.
message Tasks {
  repeated Task tasks = 1;
}

// Represents a single task that an agent is asked to perform
message Task {
  // The name is used as a key in a dictionary containing all tasks and needs to
  // be unique. Using a summary of the task makes it more friendly for
  // debugging.
  optional string name = 1;

  // The complexity of the task. Maps to TaskEval.complexity
  // in android_world/task_evals/task_eval.py.
  optional int32 complexity = 6;

  // What the agent is asked to do, can contain parameters from
  // task_params.
  optional string prompt = 2;

  // Used to define parameters. Parameters can be used in the prompt,
  // relevant_state, and success_criteria to add randomness to tasks.
  // Use cases:
  //  1. Set the field value to '{<task_param.name>}'. This will generate
  //     a single value and replace all instances of that parameter with that
  //     value.
  //  2. {<task_param.name>_without_replacement}. This will generate a new
  //     value for that specific instance and will make sure not to re-use
  //     previously used values.
  repeated TaskParams task_params = 3;

  // The initial state the device should be initialized to before the start of
  // the task. This should contain whatever is necessary to answer the prompt
  // as well as extra events to make the test more robust.
  // Parameters can be used for state values, but will need to be specified
  // in the task_param field.
  optional RelevantState relevant_state = 4;

  // Contains the answer to the prompt given the relevant_state. Parameters can
  // be used here if they are also used in relevant_state.
  optional SuccessCriteria success_criteria = 5;
}

// Defines parameters used in the task.
message TaskParams {
  // The parameter name. To use a parameter, specify it using the format {name}
  // E.g. prompt = "What events do I have on {date}?", where name = "date"
  optional string name = 1;

  // A list of values that the parameter can be set to. Only these values will
  // be used to replace the parameter where specified in the Task.
  repeated string possible_values = 2;
}

message SuccessCriteria {
  // A list of expectations to perform on the answer.  Also specifies how to
  // create the expected answer from the relevant_state. Currently, only
  // supports a single expectation or 2 expectations where one is a DATE_MATCH
  // and the other a TIME_MATCH.
  repeated Expectation expectations = 1;
}

// Specifies how to transform a field from the RelevantState to get the expected
// answer.
message FieldTransformation {
  enum Operation {
    OPERATION_UNKNOWN = 0;

    // Computes the summation of the specified field.
    SUM = 1;

    // Computes the count of the specified field.
    COUNT = 2;

    // Simply returns the value unchanged. If there are multiple fields with
    // field_name, a list containing each value will be created.
    IDENTITY = 3;
  }

  // The operation to perform on the given field in the RelevantState to
  // generate the expected answer.
  optional Operation operation = 1;
  optional string field_name = 2;
}

message Expectation {
  enum MatchType {
    MATCH_TYPE_UNKNOWN = 0;

    // Performs a string match between each element of the expected answer and
    // the agent answer.
    STRING_MATCH = 1;

    // Performs a number match between each element of the expected answer and
    // the agent answer.
    NUMBER_MATCH = 2;

    // Performs a date match between each element of the expected answer and
    // the agent answer.
    DATE_MATCH = 3;

    // Performs a time match between each element of the expected answer and
    // the agent answer.
    TIME_MATCH = 4;
  }

  // The expected answer is defined either by how to generate it from the
  // RelevantState or as the exact answer itself.
  oneof expected_answer {
    FieldTransformation field_transformation = 1;
    // If this is set, simply do the specified match type on the agent answer
    // with this value.
    string expected_value = 2;
  }

  // How to compare/match the value either set or generated in expected_answer.
  // If the expected answer is a list, will perform this match on the unordered
  // lists.
  optional MatchType match_type = 3;

  // The tolerance to use for the absolute difference when performing a match
  // for match type NUMBER_MATCH
  optional float tolerance = 4;
}

message RelevantState {
  optional State state = 1;
  // Lists all conditions that should be excluded for all additional random
  // initial state (not defined in state). Operates as an 'AND'.
  repeated ExclusionCondition exclusion_conditions = 2;
}

// Represents a condition that should be excluded from the initial state.
// An initial state needs to be excluded if (field OPERATION value) == true.
message ExclusionCondition {
  enum Operation {
    OPERATION_UNKNOWN = 0;
    EQUAL_TO = 1;
    CONTAINS = 2;
    GREATER_THAN = 3;
    LESS_THAN = 4;
    GREATER_THAN_OR_EQUAL_TO = 5;
    LESS_THAN_OR_EQUAL_TO = 6;
  }
  optional Operation operation = 1;

  // The field name in the State proto this condition applies to
  optional string field = 2;
  optional string value = 3;
}
```

### `official/install/android_world/task_evals/information_retrieval/proto_utils.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/proto_utils.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utils for manipulating the task and initialization protos."""

from collections.abc import Iterator
import datetime
import random
import re
from typing import Any, TypeVar

from android_world.task_evals.information_retrieval import datetime_utils as datetime_utils_ir
from android_world.task_evals.information_retrieval.proto import state_pb2
from android_world.task_evals.information_retrieval.proto import task_pb2
from android_world.utils import fuzzy_match_lib
from google.protobuf import message

ExpectedAnswer = TypeVar(
    'ExpectedAnswer',
    str,
    datetime.datetime,
    datetime.date,
    datetime.time,
    float,
    int,
)

AppData = TypeVar(
    'AppData', state_pb2.Event, state_pb2.TasksAppTask, state_pb2.SportsActivity
)

FieldMessage = TypeVar(
    'FieldMessage',
    state_pb2.Event,
    task_pb2.Expectation,
    state_pb2.TasksAppTask,
    state_pb2.SportsActivity,
    task_pb2.ExclusionCondition,
)


def _combine_date_and_time(
    answer1: ExpectedAnswer, answer2: ExpectedAnswer
) -> str | datetime.datetime:
  """Combines two expectations into a single answer.

  Combines them in the following ways:
   - one of the inputs is a date and the other is a time - will output a
   datetime
   - all other combinations will be combined as a string with a single space
   between the two.

  Args:
    answer1: The first answer to be merged.
    answer2: The second answer to be merged

  Returns:
    The merged result, either a datetime or a string.
  """
  if isinstance(answer1, datetime.date) and isinstance(answer2, datetime.time):
    return datetime.datetime(
        answer1.year, answer1.month, answer1.day, answer2.hour, answer2.minute
    )
  elif isinstance(answer2, datetime.date) and isinstance(
      answer1, datetime.time
  ):
    return datetime.datetime(
        answer2.year, answer2.month, answer2.day, answer1.hour, answer1.minute
    )
  else:
    raise ValueError(f'Unsupported combination: {answer1} and {answer2}')


def _check_match_types(
    match_types: list[task_pb2.Expectation.MatchType],
) -> None:
  """Checks if the match types are supported."""

  if len(match_types) == 1 or not match_types:
    return
  if len(match_types) > 2:
    raise ValueError(
        'Unsupported combined match types: {}'.format([
            task_pb2.Expectation.MatchType.Name(match_type)
            for match_type in match_types
        ])
    )
  if set(match_types) != set((
      task_pb2.Expectation.MatchType.DATE_MATCH,
      task_pb2.Expectation.MatchType.TIME_MATCH,
  )):
    raise ValueError(
        'Unsupported combined match types: {}'.format([
            task_pb2.Expectation.MatchType.Name(match_type)
            for match_type in match_types
        ])
    )


def _cast_answers_to_type(
    match_types: list[task_pb2.Expectation.MatchType], answers: list[str]
) -> list[ExpectedAnswer]:
  if not match_types:
    return answers
  match match_types:
    case [task_pb2.Expectation.MatchType.STRING_MATCH]:
      return [str(answer) for answer in answers]
    case [task_pb2.Expectation.MatchType.NUMBER_MATCH]:
      return [float(answer) for answer in answers]
    case [task_pb2.Expectation.MatchType.DATE_MATCH]:
      return [
          datetime.datetime.strptime(
              answer, datetime_utils_ir.DATE_FORMAT
          ).date()
          for answer in answers
      ]
    case [task_pb2.Expectation.MatchType.TIME_MATCH]:
      return [
          datetime.datetime.strptime(answer, '%H:%M').time()
          for answer in answers
      ]
    case [
        task_pb2.Expectation.MatchType.DATE_MATCH,
        task_pb2.Expectation.MatchType.TIME_MATCH,
    ]:
      return [
          datetime.datetime.strptime(
              answer, datetime_utils_ir.DATE_FORMAT + ' %H:%M'
          )
          for answer in answers
      ]
    case _:
      raise ValueError(f'Unsupported match types: {match_types}')


def check_agent_answer(agent_answer: str, task: task_pb2.Task) -> bool:
  """Checks if the agent answer matches the task's expectations."""
  # If there are multiple answers, they are separated by commas
  answers = [answer.strip() for answer in agent_answer.split(',')]
  match_types = list(
      map(
          lambda expectation: expectation.match_type,
          task.success_criteria.expectations,
      )
  )
  _check_match_types(match_types)

  try:
    type_cast_answers = _cast_answers_to_type(match_types, answers)
  except ValueError as e:
    raise ValueError('Answer given in the incorrect format.') from e

  expected_answers = get_expected_answer(task)
  comparator = lambda x, y: x == y
  if task_pb2.Expectation.MatchType.STRING_MATCH in match_types:
    comparator = fuzzy_match_lib.fuzzy_match
  elif (
      task_pb2.Expectation.MatchType.NUMBER_MATCH in match_types
      and task.success_criteria.expectations[0].HasField('tolerance')
  ):
    comparator = (
        lambda x, y: abs(x - y)
        < task.success_criteria.expectations[0].tolerance
    )
  if len(type_cast_answers) != len(expected_answers):
    return False
  return all(
      any(comparator(x, y) for y in expected_answers) for x in type_cast_answers
  )


def get_expected_answer(
    task: task_pb2.Task,
) -> list[ExpectedAnswer]:
  """Gets the expected answer from the task's success criteria."""
  expected_answers = []
  for expectation in task.success_criteria.expectations:
    if expectation.HasField('expected_value'):
      return _cast_answers_to_type(
          [expectation.match_type], [expectation.expected_value]
      )
    field_transformation = expectation.field_transformation
    field_values = _get_field_values(
        task.relevant_state.state, field_transformation.field_name
    )
    expected_answer = []
    # SUM and COUNT are of type NUMBER_MATCH so handle those first.
    if (
        field_transformation.operation
        == task_pb2.FieldTransformation.Operation.SUM
    ):
      return [sum((float(value) for value in field_values))]
    elif (
        field_transformation.operation
        == task_pb2.FieldTransformation.Operation.COUNT
    ):
      return [len(list(field_values))]
    elif expectation.match_type == task_pb2.Expectation.MatchType.STRING_MATCH:
      return list(field_values)
    elif expectation.match_type == task_pb2.Expectation.MatchType.NUMBER_MATCH:
      return [float(value) for value in field_values]
    elif expectation.match_type == task_pb2.Expectation.MatchType.DATE_MATCH:
      expected_answer.extend([
          datetime.datetime.strptime(
              value, datetime_utils_ir.DATE_FORMAT
          ).date()
          for value in field_values
      ])
    elif expectation.match_type == task_pb2.Expectation.MatchType.TIME_MATCH:
      expected_answer.extend(
          [datetime_utils_ir.parse_time(value) for value in field_values]
      )
    if not expected_answers:
      expected_answers.extend(expected_answer)
    else:
      expected_answers = [
          _combine_date_and_time(answer1, answer2)
          for answer1, answer2 in zip(expected_answers, expected_answer)
      ]
  return expected_answers


def _get_field_values(proto: message.Message, field_name: str) -> Iterator[Any]:
  """Gets the values for the given field_name from a proto."""
  for field, _ in proto.ListFields():
    field_value = getattr(proto, field.name)
    is_repeated_field = not isinstance(
        field_value, message.Message
    ) and not isinstance(field_value, str)
    if field.name == field_name:
      if is_repeated_field:
        for value in field_value:
          yield value
      else:
        yield field_value
    elif isinstance(field_value, message.Message):
      yield from _get_field_values(field_value, field_name)
    elif is_repeated_field:
      for element in field_value:
        yield from _get_field_values(element, field_name)


def _remove_used_params(
    used_params: dict[str, Any], all_params: list[task_pb2.TaskParams]
) -> None:
  """Removes the used params from the list of params."""
  for index, param in enumerate(all_params):
    if (
        param.name not in used_params
        or used_params[param.name] not in param.possible_values
    ):
      continue
    used_value = used_params[param.name]
    new_param = task_pb2.TaskParams()
    new_param.CopyFrom(param)
    new_param.possible_values.remove(used_value)
    all_params[index] = new_param


def format_state_with_params(
    state: state_pb2.State,
    task_params: dict[str, Any],
    all_params: list[task_pb2.TaskParams],
) -> None:
  """Formats the state with the task params and all_params if necessary."""
  # Make a copy of the list so that the caller's copy isn't affected.
  unused_params = all_params.copy()
  _remove_used_params(task_params, unused_params)
  for field, _ in state.ListFields():
    app_proto: (
        state_pb2.Calendar
        | state_pb2.TasksAppTask
        | state_pb2.SportsActivityApp
    ) = getattr(state, field.name)
    for app_field, _ in app_proto.ListFields():
      if app_field.name == 'app_name':
        continue
      app_data_list = getattr(app_proto, app_field.name)
      for app_data in app_data_list:
        for app_data_field, _ in app_data.ListFields():
          _format_field_if_exists(
              app_data, app_data_field.name, task_params, unused_params
          )


def format_relevant_state_with_params(
    relevant_state: task_pb2.RelevantState,
    task_params: dict[str, Any],
    all_params: list[task_pb2.TaskParams],
) -> None:
  unused_params = all_params.copy()
  _remove_used_params(task_params, unused_params)
  format_state_with_params(relevant_state.state, task_params, unused_params)
  for condition in relevant_state.exclusion_conditions:
    _format_field_if_exists(condition, 'value', task_params, unused_params)


def _format_params_with_params(
    task_params: list[task_pb2.TaskParams], params: dict[str, Any]
):
  for task_param in task_params:
    for index, possible_value in enumerate(task_param.possible_values):
      task_param.possible_values[index] = possible_value.format(**params)
  for param_name, param_value in params.items():
    if isinstance(param_value, str):
      params[param_name] = param_value.format(**params)


def initialize_proto(task: task_pb2.Task, task_params: dict[str, Any]):
  _format_params_with_params(list(task.task_params), task_params)
  _format_success_criteria_with_params(task.success_criteria, task_params)
  format_relevant_state_with_params(
      task.relevant_state, task_params, list(task.task_params)
  )


def _format_success_criteria_with_params(
    success_criteria: task_pb2.SuccessCriteria, task_params: dict[str, Any]
):
  for expectation in success_criteria.expectations:
    if expectation.HasField('expected_value'):
      _format_field_if_exists(expectation, 'expected_value', task_params, [])


def _format_field_if_exists(
    proto: FieldMessage,
    field_name: str,
    task_params: dict[str, Any],
    unused_params: list[task_pb2.TaskParams],
):
  """Formats the field if it exists with the params.

  Formats each field with task_params. Additionaly, if the field has a param
  with '_without_replacement' in its name, it will pick parameters from
  unused_params to format it. These picked parameter values will then be
  removed from the unused_params list.

  Args:
    proto: The proto whose field will be formatted.
    field_name: The name of the field to format.
    task_params: The task's parameters to format the field with.
    unused_params: Extra list of parameters to chose from if task_params does
      not fully format the field.
  """
  if proto.HasField(field_name):
    if '_without_replacement}' in str(getattr(proto, field_name)):
      _format_without_replacement(proto, field_name, unused_params)
    else:
      setattr(
          proto,
          field_name,
          getattr(proto, field_name).format(**task_params),
      )


def _format_without_replacement(
    proto: FieldMessage,
    field_name: str,
    unused_params: list[task_pb2.TaskParams],
):
  """Handles field formatting when the param name contains '_without_replacement'.

  The field's parameter value will be chosen from the unused_params list and
  that value will then be removed as a possible value from that list.

  Args:
    proto: The proto whose field will be formatted.
    field_name: The name of the field to format.
    unused_params: A list of TaskParams containing possible values that have not
      yet been used for other field formatting.
  """
  field_value = getattr(proto, field_name)
  # Get the names of the parameter:
  without_replacement_params = [
      param_name[1 : param_name.find('_without_replacement')]
      for param_name in re.findall(r'\{.+?\}', field_value)
      if param_name.endswith('without_replacement}')
  ]
  for param_name in without_replacement_params:
    original_param_name = param_name + '_without_replacement'
    new_value = None
    for task_param in unused_params:
      if task_param.name == param_name:
        new_value = random.choice(list(task_param.possible_values))
        _remove_used_params({task_param.name: new_value}, unused_params)
        break

    setattr(
        proto,
        field_name,
        getattr(proto, field_name).format(**{original_param_name: new_value}),
    )


_T = TypeVar('_T')


def compare(
    field_value: _T,
    operator: task_pb2.ExclusionCondition.Operation,
    comparison_value: _T,
) -> bool:
  """Compares the field value against the comparison value using the operator."""
  if operator == task_pb2.ExclusionCondition.Operation.EQUAL_TO:
    return field_value == comparison_value
  elif operator == task_pb2.ExclusionCondition.Operation.GREATER_THAN:
    return field_value > comparison_value
  elif (
      operator == task_pb2.ExclusionCondition.Operation.GREATER_THAN_OR_EQUAL_TO
  ):
    return field_value >= comparison_value
  elif operator == task_pb2.ExclusionCondition.Operation.LESS_THAN:
    return field_value < comparison_value
  elif operator == task_pb2.ExclusionCondition.Operation.LESS_THAN_OR_EQUAL_TO:
    return field_value <= comparison_value
  elif operator == task_pb2.ExclusionCondition.Operation.CONTAINS:
    return comparison_value in str(field_value)
  else:
    raise ValueError(f'Unsupported operator: {operator}')
```

### `official/install/android_world/task_evals/single/calendar/__init__.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/__init__.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Calendar task evaluations."""
```

### `official/install/android_world/task_evals/single/calendar/calendar_evaluators.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/calendar_evaluators.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Evaluators for Simple Calendar Pro.

They look at the underlying state of the sqlite database.
"""

from android_world.task_evals.common_validators import sqlite_validators
from android_world.task_evals.utils import sqlite_schema_utils


def validate_event_removal_integrity(
    before: list[sqlite_schema_utils.CalendarEvent],
    after: list[sqlite_schema_utils.CalendarEvent],
    event_ids: list[int],
) -> bool:
  """Validates that events have been removed from the event list.

  See `sqlite_evaluators.validate_rows_removal_integrity` for details.

  Args:
    before: State of the events before removal, as a list of event tuples.
    after: State of the events after attempted removal, as a list of event
      tuples.
    event_ids: IDs of the events expected to be removed.

  Returns:
    True if specified events are removed and the integrity of the event list is
    maintained; False if any specified events are not removed, if any
    non-specified events are missing, or if new events have been added.
  """
  return sqlite_validators.validate_rows_removal_integrity(
      before, after, event_ids, 'id'
  )


def validate_event_addition_integrity(
    before: list[sqlite_schema_utils.CalendarEvent],
    after: list[sqlite_schema_utils.CalendarEvent],
    reference_events: list[sqlite_schema_utils.CalendarEvent],
    extras_compare: list[str] | None = None,
) -> bool:
  """Validates that specific events have been added correctly without side effects.

  By default, checks the following fields:
    - start_ts
    - end_ts
    - title  # Uses fuzzy match.
    - location  # Uses fuzzy match.
    - description  # Uses fuzzy match.

  Additional fields can be checked with `extras_compare`.

  Args:
      before: The state of the events before the addition.
      after: The state of the events after the attempted addition.
      reference_events: A list of events that are expected to be added.
      extras_compare: Additional fields to compare, if any.

  Returns:
      bool: True if the events were added correctly and other events remained
      unaltered. False otherwise.
  """

  # Default fields to compare
  compare_fields = [
      'start_ts',
      'end_ts',
      'title',
      'location',
      'description',
  ]
  free_form_fields = ['title', 'location', 'description']
  if extras_compare:
    compare_fields += extras_compare
  return sqlite_validators.validate_rows_addition_integrity(
      before, after, reference_events, compare_fields, free_form_fields
  )
```

### `official/install/android_world/task_evals/single/calendar/calendar_utils.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/calendar_utils.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utils for Simple Calendar Pro."""

from typing import Optional
from android_world.env import interface
from android_world.task_evals.single.calendar import events_generator
from android_world.task_evals.utils import sqlite_schema_utils
from android_world.task_evals.utils import sqlite_utils
from android_world.utils import datetime_utils


DB_PATH = '/data/data/com.simplemobiletools.calendar.pro/databases/events.db'
EVENTS_TABLE = 'events'  # Table in events.db.
DB_KEY = 'id'


def clear_calendar_db(
    env: interface.AsyncEnv, timeout_sec: Optional[float] = None
) -> None:
  """Removes the calendar database on the device."""
  sqlite_utils.delete_all_rows_from_table(
      EVENTS_TABLE, DB_PATH, env, 'simple calendar pro'
  )
  try:
    sqlite_utils.get_rows_from_remote_device(
        EVENTS_TABLE,
        DB_PATH,
        sqlite_schema_utils.CalendarEvent,
        env,
        timeout_sec,
    )
  except ValueError as e:
    raise RuntimeError(
        'After clearing the old SQLite database, a new empty database was'
        ' not created.'
    ) from e


def add_events(
    events: list[sqlite_schema_utils.CalendarEvent],
    env: interface.AsyncEnv,
    timeout_sec: Optional[float] = None,
) -> None:
  """Adds an event to the Android calendar database using ADB.

  Performs a round trip: copies db over from device, adds event, then sends
  db back to device.

  Args:
      events: The list of Events to add to the database.
      env: The Android environment interface.
      timeout_sec: A timeout for the ADB operations.
  """
  sqlite_utils.insert_rows_to_remote_db(
      events,
      DB_KEY,
      EVENTS_TABLE,
      DB_PATH,
      'simple calendar pro',
      env,
      timeout_sec,
  )


def add_random_events(env: interface.AsyncEnv, n: int = 75) -> None:
  """Adds random events to calendar to increase task complexity."""
  events = [
      events_generator.generate_event(
          datetime_utils.create_random_october_2023_unix_ts(start_day=1)
      )
      for _ in range(n)
  ]
  add_events(events, env)


def generate_simple_calendar_weekly_repeat_rule(day_of_week: int) -> int:
  """Generates a weekly repeat rule based on the provided list of weekdays.

  This logic is specific to Simple Calendar Pro, where each day is represented
  by 2^(n-1), with n being the day's number (1 for Monday, 2 for Tuesday, etc.).

  Args:
    day_of_week: Day of week, where Monday is 1, Tuesday is 2, ..., Sunday is 7.

  Returns:
    The repeat rule as an integer.
  """
  if not (1 <= day_of_week <= 7):
    raise ValueError('Invalid day of the week. Must be in range 1-7.')
  return 1 << (day_of_week - 1)
```

### `official/install/android_world/task_evals/single/calendar/events_generator.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/events_generator.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module for generating realistic calendar events.

It includes functions to generate event titles and descriptions using
predefined lists of titles, names, subjects, actions, and additional notes.
"""

import random
from android_world.task_evals.utils import sqlite_schema_utils


# Titles and Subjects for the event title generation
TITLES_PREFIXES = [
    'Meeting with',
    'Call with',
    'Workshop on',
    'Appointment for',
    'Catch up on',
    'Review session for',
]
NAMES = ['Alice', 'Bob', 'the Team', 'HR', 'Dr. Smith', 'Marketing']
SUBJECTS = ['Project X', 'Annual Report', 'Budget Planning', 'Campaign']

# Actions and Subjects Descriptions for the event description generation
ACTIONS = [
    'discuss',
    'finalize',
    'plan',
    'celebrate',
    'prepare for',
    'review',
    'explore',
    'understand',
    'organize',
    'strategize about',
]
SUBJECTS_DESCRIPTIONS = [
    'upcoming project milestones',
    'marketing strategies',
    'annual budget',
    'product launch',
    'team roles',
    'client feedback',
    'contract details',
    'software updates',
    'business objectives',
]
ADDITIONAL_NOTES = [
    'Please bring relevant documents.',
    'Remember to confirm attendance.',
    "Let's be punctual.",
    'Looking forward to productive discussions.',
    'Snacks will be provided.',
]


def generate_event(start_time: int) -> sqlite_schema_utils.CalendarEvent:
  """Generates a realistic calendar event.

  Args:
    start_time: The time to start the event. A Unix timestamp

  Returns:
    The event with random parameters.
  """
  end_time = start_time + (random.choice([15, 30, 45, 60]) * 60)
  return sqlite_schema_utils.CalendarEvent(
      start_ts=start_time,
      end_ts=end_time,
      title=generate_event_title(),
      description=generate_event_description(),
  )


def generate_event_title() -> str:
  """Generates a realistic event title."""
  title = random.choice(TITLES_PREFIXES)

  if 'with' in title:
    title += f' {random.choice(NAMES)}'
  else:
    title += f' {random.choice(SUBJECTS)}'

  return title


def generate_event_description() -> str:
  """Generates a realistic event description."""
  description = (
      'We will'
      f' {random.choice(ACTIONS)} {random.choice(SUBJECTS_DESCRIPTIONS)}.'
  )

  if random.choice([False, True]):
    description += f' {random.choice(ADDITIONAL_NOTES)}'

  return description
```

### `official/install/android_world/task_evals/utils/__init__.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/utils/__init__.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Task evaluation utilities."""
```

### `official/install/android_world/task_evals/utils/sqlite_schema_utils.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/utils/sqlite_schema_utils.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities for creating and processing rows in a SQLite database."""

import dataclasses
import datetime
import textwrap
from typing import Any, Callable, ClassVar, Optional, TypeVar
import uuid
from android_world.env import device_constants
from android_world.utils import datetime_utils

_YESTERDAY = device_constants.DT - datetime.timedelta(days=1)


@dataclasses.dataclass(frozen=True)
class SQLiteRow:
  """Base class for representing a row in a SQLite database table.

  Subclasses should define attributes corresponding to the table columns.
  """

  def to_csv_row(self, fields: list[str]) -> str:
    """Generates a CSV string representation of this instance.

    Args:
      fields: The fields of this instance to include in the CSV output.

    Returns:
      A string representing the CSV row for this instance.
    """
    return '|'.join(str(getattr(self, field, '')) for field in fields)

  def to_text_block(self, description_key: str, fields: list[str]) -> str:
    """Generates a text block representation of this instance.

    Args:
      description_key: The key for the main description/title of the text block.
      fields: The fields of this instance to include in the text block.

    Returns:
      A string representing the text block for this instance.
    """
    # Fetch the description/title.
    description = getattr(self, description_key, '')
    text_block = f'{description_key}: {description}\n'

    # Append additional fields.
    for field in fields:
      value = getattr(self, field, '')
      text_block += f' {field}: {value}\n'
    return text_block


def get_text_representation_of_rows(
    rows: list[SQLiteRow],
    fields: list[str],
    format_type: str = 'csv',
    description_key: str | None = None,
    wrap_width: int | None = None,
) -> str:
  """Formats a list of dataclass instances into a CSV string or a series of text blocks.

  Args:
    rows: A list of SQLiteRow instances.
    fields: The fields to include from each instance.
    format_type: The output format ('csv' or 'text_block').
    description_key: Key for the main description/title in text block format
      (required if format_type is 'text_block').
    wrap_width: If provided wrap text to be this width.

  Returns:
    A string representing the formatted output for the list of instances.
  """
  if format_type == 'csv':
    header = '|'.join(fields)
    rows = [
        '|'.join(str(getattr(instance, field, '')) for field in fields)
        for instance in rows
    ]
    return header + '\n' + '\n'.join(rows)
  elif format_type == 'text_block':
    blocks = []
    for instance in rows:
      if not description_key:
        raise ValueError('description_key is required for text block format')
      description = getattr(instance, description_key, '')
      text_block = f'{instance.__class__.__name__}: {description}\n'
      for field in fields:
        if field == description_key:
          continue
        value = getattr(instance, field, '')
        if wrap_width is not None:
          value = '\n'.join(textwrap.wrap(value, wrap_width))
        text_block += f' {field}: {value}\n'
      blocks.append(text_block)
    return '\n'.join(blocks)
  else:
    raise ValueError(
        "Invalid format_type specified. Choose 'csv' or 'text_block'."
    )


RowType = TypeVar('RowType', bound=SQLiteRow)


@dataclasses.dataclass(frozen=True)
class GenericRow(SQLiteRow):
  """Holds a row from an arbitrary database."""

  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)

  def __getitem__(self, key):
    return self.__dict__[key]

  def __setitem__(self, key, value):
    raise TypeError('GenericRow is immutable')

  def __iter__(self):
    return iter(self.__dict__)

  def __len__(self):
    return len(self.__dict__)


@dataclasses.dataclass(frozen=True)
class CalendarEvent(SQLiteRow):
  """Represents a calendar event from the Simple Calendar Pro database."""

  start_ts: int
  end_ts: int
  title: str
  location: str = ''
  description: str = ''
  repeat_interval: int = 0
  repeat_rule: int = 0

  # Currently unused. We fill in with default values.
  reminder_1_minutes: int = -1
  reminder_2_minutes: int = -1
  reminder_3_minutes: int = -1
  reminder_1_type: int = 0
  reminder_2_type: int = 0
  reminder_3_type: int = 0
  repeat_limit: int = 0
  repetition_exceptions: str = '[]'
  attendees: str = ''
  import_id: str = ''
  time_zone: str = device_constants.TIMEZONE
  flags: int = 0
  event_type: int = 1
  parent_id: int = 0
  last_updated: int = 0
  source: str = 'imported-ics'
  availability: int = 0
  color: int = 0
  type: int = 0

  # Events in the database get an ID, due to autoincrement. Events initialized
  # independent on the DB do not need an ID.
  id: int = -1

  @property
  def duration_mins(self) -> int:
    if (self.end_ts - self.start_ts) % 60 != 0:
      raise ValueError('Duration should be even number of minutes.')
    return (self.end_ts - self.start_ts) // 60

  @property
  def start_datetime(self) -> datetime.datetime:
    """Python datetime object for the start time."""
    return datetime_utils.timestamp_to_localized_datetime(
        self.start_ts, timezone=device_constants.TIMEZONE
    )

  @property
  def end_datetime(self) -> datetime.datetime:
    """Python datetime object for the end time."""
    return datetime_utils.timestamp_to_localized_datetime(
        self.end_ts, timezone=device_constants.TIMEZONE
    )


@dataclasses.dataclass(frozen=True)
class Recipe(SQLiteRow):
  """Dataclass for a recipe in the Broccoli app."""

  title: str
  description: str = ''
  servings: str = ''
  preparationTime: str = ''  # pylint: disable=invalid-name
  source: str = ''
  ingredients: str = ''
  directions: str = ''
  favorite: int = 0

  imageName: str = ''  # pylint: disable=invalid-name

  # Auto-incremented primary key, default to -1 when not retrieved from the
  # database
  recipeId: int = -1  # pylint: disable=invalid-name


@dataclasses.dataclass(frozen=True)
class Expense(SQLiteRow):
  """Dataclass for an expense record."""

  name: str
  amount: int
  category: int = 0
  note: Optional[str] = ''
  created_date: int = 0
  modified_date: int = 0

  # Auto-incremented primary key, default to -1 when not retrieved from the
  # database
  expense_id: int = -1
  category_id_to_name: ClassVar[dict[int, str]] = {
      1: 'Others',
      2: 'Income',
      3: 'Food',
      4: 'Housing',
      5: 'Social',
      6: 'Entertainment',
      7: 'Transportation',
      8: 'Clothes',
      9: 'Health Care',
      10: 'Education',
      11: 'Donation',
  }

  @property
  def amount_dollars(self) -> str:
    return f'${self.amount / 100}'

  @property
  def category_name(self) -> str:
    return self.category_id_to_name[self.category]


@dataclasses.dataclass(frozen=True)
class PlaylistInfo(SQLiteRow):
  """Represents a playlist and metadata in VLC or similar media apps."""

  playlist_name: str
  media_file_name: str
  order_in_playlist: int
  duration_ms: int | None = None


# pylint: disable=invalid-name
@dataclasses.dataclass(frozen=True)
class Task(SQLiteRow):
  """Dataclass for a task in the application."""

  title: str
  importance: int = 0
  dueDate: int = 0
  hideUntil: int = 0
  created: int = 0
  modified: int = 0
  completed: int = 0
  deleted: int = 0
  notes: str | None = None
  estimatedSeconds: int = 0
  elapsedSeconds: int = 0
  timerStart: int = 0
  notificationFlags: int = 0
  lastNotified: int = 0
  recurrence: str | None = None
  repeat_from: int = 0
  calendarUri: str | None = None
  remoteId: str = ''
  collapsed: int = 0
  parent: int = 0
  order: int | None = None
  read_only: int = 0
  # pylint: enable=invalid-name

  # Auto-incremented primary key, default to -1 when not retrieved from the
  # database
  _id: int = -1


@dataclasses.dataclass(frozen=True)
class OsmAndMapMarker(SQLiteRow):
  """Dataclass for an OsmAnd app db row representing a map marker."""

  marker_id: str = ''
  marker_lat: float = -1.0
  marker_lon: float = -1.0
  marker_description: str = ''
  marker_active: int = 0
  marker_added: int = 0
  marker_visited: int = 0
  group_name: str = ''
  group_key: str = ''
  marker_color: int = 0
  marker_next_key: str = ''
  marker_disabled: int = 0
  marker_selected: int = 0
  marker_map_object_name: str = ''
  title: str = ''


@dataclasses.dataclass(frozen=True)
class SportsActivity(SQLiteRow):
  """Represents a row from the "track" table in OpenTracks.

  Note: These default values are provided for ease of use, but some of them
  should be set before uploading to table.
  """

  name: str
  description: str = ''
  category: str = ''
  # Should be equal to category, seems to simply set the activity icon in
  # the activity list.
  activity_type: str = ''
  starttime: int = 0
  stoptime: int = 0
  numpoints: int = 0
  totaldistance: float = 0.0  # Meters.
  # Milliseconds
  totaltime: int = 0
  movingtime: int = 0
  # All speed in meters per second.
  # If it doesn't match the given distance over time, the app recalculates them.
  # If they are set to 0, the app defaults to mph (instead of min/mile).
  avgspeed: float = 0.0
  avgmovingspeed: float = 0.0
  maxspeed: float = 0.0
  minelevation: float = 0.0
  maxelevation: float = 0.0
  elevationgain: float = 0.0
  icon: Optional[str] = None
  uuid: bytes = dataclasses.field(default_factory=lambda: uuid.uuid4().bytes)
  elevationloss: float = 0.0
  starttime_offset: int = 0

  # Auto-incremented primary key, default to -1 when not retrieved from the
  # database
  _id: int = -1


@dataclasses.dataclass(frozen=True)
class JoplinNormalizedNote(SQLiteRow):
  """Represents a row from the "notes_normalized" table in Joplin.

  Notes need to be added to this table for them to be searchable.
  """

  parent_id: str = ''
  title: str = ''
  body: str = ''
  latitude: float = 0.0
  longitude: float = 0.0
  altitude: float = 0.0
  source_url: str = ''
  is_todo: int = 0
  todo_due: int = 0
  todo_completed: int = 0
  user_created_time: int = 0
  user_updated_time: int = 0

  id: str = ''


@dataclasses.dataclass(frozen=True)
class JoplinNote(SQLiteRow):
  """Represents a row from the "notes" table in Joplin."""

  parent_id: str = ''
  title: str = ''
  body: str = ''
  created_time: int = int(_YESTERDAY.timestamp() * 1000)
  updated_time: int = int(_YESTERDAY.timestamp() * 1000)
  is_conflict: int = 0
  latitude: float = 0.0
  longitude: float = 0.0
  altitude: float = 0.0
  author: str = ''
  source_url: str = ''
  is_todo: int = 0
  todo_due: int = 0
  todo_completed: int = 0
  source: str = ''
  source_application: str = ''
  application_data: str = ''
  order: float = 0.0
  user_created_time: int = int(_YESTERDAY.timestamp() * 1000)
  user_updated_time: int = int(_YESTERDAY.timestamp() * 1000)
  encryption_cipher_text: str = ''
  encryption_applied: int = 0
  markup_language: int = 1
  is_shared: int = 0
  share_id: str = ''
  conflict_original_id: str = ''
  master_key_id: str = ''
  user_data: str = ''

  id: str = dataclasses.field(default_factory=lambda: uuid.uuid4().hex)


@dataclasses.dataclass(frozen=True)
class JoplinFolder(SQLiteRow):
  """Represents a row from "folder" table in Joplin."""

  title: str
  id: str = dataclasses.field(default_factory=lambda: uuid.uuid4().hex)
  created_time: int = int(_YESTERDAY.timestamp() * 1000)
  updated_time: int = int(_YESTERDAY.timestamp() * 1000)
  user_created_time: int = int(_YESTERDAY.timestamp() * 1000)
  user_updated_time: int = int(_YESTERDAY.timestamp() * 1000)
  deleted_time: int = 0
  encryption_cipher_text: str = ''
  encryption_applied: int = 0
  parent_id: str = ''
  is_shared: int = 0
  share_id: str = ''
  master_key_id: str = ''
  icon: str = ''
  user_data: str = ''


def insert_into_db(
    data_object: SQLiteRow,
    table_name: str,
    exclude_key: str | None = None,
) -> tuple[str, tuple[Any, ...]]:
  """Generates an SQL INSERT command to add a new row to the specified table.

  Args:
      data_object: An object representing the data to be added.
      table_name: Name of the table to insert data into.
      exclude_key: Typically, the ID key which is auto-incrementing, so we do
        not add it; the db will create it.

  Returns:
      A tuple containing the SQL INSERT command and the values to be inserted.
  """
  fields = []
  for field in dataclasses.fields(data_object):
    if exclude_key is not None and field.name == exclude_key:
      continue
    fields.append(field)
  column_names = ', '.join(f'"{field.name}"' for field in fields)
  placeholders = ', '.join('?' * len(fields))

  insert_command = (
      f'INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})'
  )
  values = tuple(getattr(data_object, field.name) for field in fields)

  return insert_command, values


def _is_candidate_equal_to_any_result(
    candidate: Any, result: list[Any]
) -> bool:
  """Private function to check if a candidate is equal to any of the objects in result."""
  for existing in result:
    if all(
        getattr(candidate, field.name) == getattr(existing, field.name)
        for field in dataclasses.fields(candidate)
    ):
      return True
  return False


def get_random_items(
    n: int,
    generate_item_fn: Callable[[], RowType],
    replacement: bool = False,
    filter_fn: Optional[Callable[[RowType], bool]] = None,
) -> list[RowType]:
  """Generates a list of random items, optionally filtering and avoiding duplicates.

  Args:
      n: The number of items to generate.
      generate_item_fn: Function to generate a single random item.
      replacement: Whether to allow replacement (duplicates) in the returned
        list.
      filter_fn: Optional function to filter items. If None, all items are
        accepted.

  Returns:
      A list of randomly generated items.
  """
  if not filter_fn:
    filter_fn = lambda _: True
  result = []
  i = 0
  while len(result) < n:
    candidate = generate_item_fn()
    i += 1
    if i > 10_000:
      raise ValueError(
          'Something went wrong: generation exhaused. There are total of'
          f" {len(result)} items created; couldn't generate {n} items."
      )
    if not filter_fn(candidate):
      continue
    if replacement:
      result.append(candidate)
    elif not _is_candidate_equal_to_any_result(candidate, result):
      result.append(candidate)
  return result
```

### `official/install/android_world/task_evals/utils/sqlite_utils.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/utils/sqlite_utils.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utility functions for interacting with SQLite database on an Android device."""

import os
import sqlite3
import time
from typing import Optional, Type
from android_world.env import adb_utils
from android_world.env import interface
from android_world.task_evals.utils import sqlite_schema_utils
from android_world.utils import file_utils


def execute_query(
    query: str, db_path: str, row_type: Type[sqlite_schema_utils.RowType]
) -> list[sqlite_schema_utils.RowType]:
  """Retrieves all rows from the given SQLite database path.

  Args:
    query: The query to issue.
    db_path: The path to the SQLite database file.
    row_type: The object type that will be created for each retrieved row.

  Returns:
      A list of tuples, each representing an row from the database.
  """
  conn = sqlite3.connect(db_path)
  conn.row_factory = sqlite3.Row
  cursor = conn.cursor()
  raw_rows = cursor.execute(query).fetchall()
  conn.close()

  rows = []
  for row in raw_rows:
    row = dict(row)
    rows.append(row_type(**row))  # pytype: disable=bad-return-type
  return rows


def get_rows_from_remote_device(
    table_name: str,
    remote_db_file_path: str,
    row_type: Type[sqlite_schema_utils.RowType],
    env: interface.AsyncEnv,
    timeout_sec: Optional[float] = None,
    n_retries: int = 3,
) -> list[sqlite_schema_utils.RowType]:
  """Retrieves rows from a table in a SQLite database located on a remote Android device.

  This function first copies the database from the remote device to a
  temporary local directory.

  Args:
    table_name: The name of the table from which to retrieve rows.
    remote_db_file_path: The database path on the remote device.
    row_type: The class type corresponding to the table's row structure. Each
      new database needs an equivalent python representation class type.
    env: The Android environment interface used for interacting with the remote
      device.
    timeout_sec: Optional timeout in seconds for the database copy operation.
    n_retries: The number of times to try. This is relevant in cases where a
      database has not been created/being created when an app is launched for
      the first time after clearing the database.

  Returns:
    All rows from the table.

  Raises:
    ValueError: If cannot query table.
  """
  with env.controller.pull_file(
      remote_db_file_path, timeout_sec
  ) as local_db_directory:
    local_db_path = file_utils.convert_to_posix_path(
        local_db_directory, os.path.split(remote_db_file_path)[1]
    )
    for _ in range(n_retries):
      try:
        return execute_query(
            f"SELECT * FROM {table_name};",
            local_db_path,
            row_type,
        )
      except sqlite3.OperationalError:
        time.sleep(1.0)
  raise ValueError(
      f"Failed to retrieve rows from {table_name} from"
      f" {remote_db_file_path} after {n_retries} retries. Try increasing the "
      "number of retries."
  )


def table_exists(
    table_name: str,
    remote_db_file_path: str,
    env: interface.AsyncEnv,
) -> bool:
  """Checks if a table exists in a SQLite database on a remote Android device.

  Args:
    table_name: The name of the table from which to retrieve rows.
    remote_db_file_path: The path to the sqlite database on the device.
    env: The environment.

  Returns:
    True if the table exists in the database.
  """
  try:
    get_rows_from_remote_device(
        table_name,
        remote_db_file_path,
        sqlite_schema_utils.GenericRow,
        env,
    )
    return True
  except (FileNotFoundError, ValueError):
    return False


def delete_all_rows_from_table(
    table_name: str,
    remote_db_file_path: str,
    env: interface.AsyncEnv,
    app_name: str,
    timeout_sec: Optional[float] = None,
) -> None:
  """Deletes all rows from a specified table in a SQLite database on a remote Android device.

  Args:
    table_name: Deletes all rows from the table.
    remote_db_file_path: The path to the sqlite database on the device.
    env: The environment.
    app_name: The name of the app that owns the database.
    timeout_sec: Timeout in seconds.
  """
  if not table_exists(table_name, remote_db_file_path, env):
    # If the database was never created, opening the app may create it.
    adb_utils.launch_app(app_name, env.controller)
    time.sleep(7.0)

  with env.controller.pull_file(
      remote_db_file_path, timeout_sec
  ) as local_db_directory:
    local_db_path = file_utils.convert_to_posix_path(
        local_db_directory, os.path.split(remote_db_file_path)[1]
    )

    conn = sqlite3.connect(local_db_path)
    cursor = conn.cursor()
    delete_command = f"DELETE FROM {table_name}"
    cursor.execute(delete_command)
    conn.commit()
    conn.close()
    env.controller.push_file(local_db_path, remote_db_file_path, timeout_sec)
    adb_utils.close_app(
        app_name, env.controller
    )  # Close app to register the changes.


def insert_rows_to_remote_db(
    rows: list[sqlite_schema_utils.RowType],
    exclude_key: str | None,
    table_name: str,
    remote_db_file_path: str,
    app_name: str,
    env: interface.AsyncEnv,
    timeout_sec: Optional[float] = None,
) -> None:
  """Inserts rows into a SQLite database located on a remote Android device.

  Args:
    rows: The rows to insert into the remote database.
    exclude_key: Name of field to exclude adding to database. Typically an auto
      incrementing key.
    table_name: The name of the table to insert rows into.
    remote_db_file_path: Location of the SQLite database to insert rows into.
    app_name: The name of the app that owns the database.
    env: The environment.
    timeout_sec: Optional timeout in seconds for the database copy operation.
  """
  with env.controller.pull_file(
      remote_db_file_path, timeout_sec
  ) as local_db_directory:
    local_db_path = file_utils.convert_to_posix_path(
        local_db_directory, os.path.split(remote_db_file_path)[1]
    )

    conn = sqlite3.connect(local_db_path)
    cursor = conn.cursor()
    for row in rows:
      insert_command, values = sqlite_schema_utils.insert_into_db(
          row, table_name, exclude_key
      )
      cursor.execute(insert_command, values)
    conn.commit()
    conn.close()

    env.controller.push_file(local_db_path, remote_db_file_path, timeout_sec)
    adb_utils.close_app(app_name, env.controller)
```

### `official/install/android_world/utils/__init__.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/__init__.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utility modules for AndroidWorld."""
```

### `official/install/android_world/utils/app_snapshot.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/app_snapshot.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utils for handling snapshots for apps."""

from absl import logging
from android_env import env_interface
from android_world.env import adb_utils
from android_world.env import device_constants
from android_world.utils import file_utils


def _app_data_path(app_name: str) -> str:
  package_name = adb_utils.extract_package_name(
      adb_utils.get_adb_activity(app_name)
  )
  return file_utils.convert_to_posix_path("/data/data/", package_name)


def _snapshot_path(app_name: str) -> str:
  package_name = adb_utils.extract_package_name(
      adb_utils.get_adb_activity(app_name)
  )
  return file_utils.convert_to_posix_path(
      device_constants.SNAPSHOT_DATA, package_name
  )


def clear_snapshot(
    app_name: str,
    env: env_interface.AndroidEnvInterface,
):
  """Removes the stored snapshot of app state.

  Args:
    app_name: Package name for the application snapshot to remove.
    env: Android environment.
  """
  snapshot_path = _snapshot_path(app_name)
  file_utils.clear_directory(snapshot_path, env)


def save_snapshot(app_name: str, env: env_interface.AndroidEnvInterface):
  """Stores a snapshot of application data on the device.

  Only a single snapshot is stored at any given time. Repeated calls to
  `save_snapshot()` overwrite any prior snapshot.

  Args:
    app_name: App package to be snapshotted.
    env: Android environment.

  Raises:
    RuntimeError: on failed or incomplete snapshot.
  """
  snapshot_path = _snapshot_path(app_name)
  try:
    file_utils.clear_directory(snapshot_path, env)
  except RuntimeError:
    logging.warn(
        "Continuing to save %s snapshot after failing to clear prior snapshot.",
        app_name,
    )

  file_utils.copy_dir(_app_data_path(app_name), snapshot_path, env)


def restore_snapshot(app_name: str, env: env_interface.AndroidEnvInterface):
  """Loads a snapshot of application data.

  Args:
    app_name: App package that will have its data overwritten with the stored
      snapshot.
    env: Android environment.

  Raises:
    RuntimeError: when there is no available snapshot or a failure occurs while
      loading the snapshot.
  """
  adb_utils.close_app(app_name, env)

  snapshot_path = _snapshot_path(app_name)
  if not file_utils.check_directory_exists(snapshot_path, env):
    raise RuntimeError(f"Snapshot not found in {snapshot_path}.")

  app_data_path = _app_data_path(app_name)
  try:
    file_utils.clear_directory(app_data_path, env)
  except RuntimeError:
    logging.warn(
        "Continuing to restore %s snapshot after failing to clear application"
        " data.",
        app_name,
    )

  file_utils.copy_dir(snapshot_path, app_data_path, env)

  # File permissions, ownership, and security context may be lost during save
  # and/or loading of the snapshot. As a workaround, restore the security
  # context and open up full file permissions.
  adb_utils.check_ok(
      adb_utils.issue_generic_request(
          ["shell", "restorecon", "-RD", app_data_path], env
      ),
      "Failed to restore app data security context.",
  )
  adb_utils.check_ok(
      adb_utils.issue_generic_request(
          ["shell", "chmod", "777", "-R", app_data_path], env
      ),
      "Failed to set app data permissions.",
  )
```

### `official/install/android_world/utils/contacts_utils.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/contacts_utils.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utils for contacts operations using adb."""

import dataclasses
import re
import time
from typing import Iterator

from android_world.env import actuation
from android_world.env import adb_utils
from android_world.env import android_world_controller


def clean_phone_number(phone_number: str) -> str:
  """Removes all non-numeric characters from a phone number.

  Args:
    phone_number: The phone number to clean.

  Returns:
    The phone number with all non-numeric characters removed.
  """
  return re.sub(r"\D", "", phone_number)


def add_contact(
    name: str,
    phone_number: str,
    env: android_world_controller.AndroidWorldController,
    ui_delay_sec: float = 1.0,
):
  """Adds a contact with the specified name and phone number.

  This function sends an intent to the Android system to add a contact with
  the information pre-filled, clicks the "Save" button to create it, and then
  returns from the activity.

  Args:
    name: The name of the new contact
    phone_number: The phone number belonging to that contact.
    env: The android environment to add the contact to.
    ui_delay_sec: Delay between UI interactions. If this value is too low, the
      "save" button may be mis-clicked.
  """
  intent_command = (
      "am start -a android.intent.action.INSERT -t"
      f' vnd.android.cursor.dir/contact -e name "{name}" -e phone'
      f" {phone_number}"
  )

  adb_command = ["shell", intent_command]
  adb_utils.issue_generic_request(adb_command, env)
  time.sleep(ui_delay_sec)
  actuation.find_and_click_element("SAVE", env)
  time.sleep(ui_delay_sec)
  adb_utils.press_back_button(env)
  time.sleep(ui_delay_sec)


@dataclasses.dataclass(frozen=True)
class Contact:
  """Basic contact information."""
  name: str
  number: str


def list_contacts(
    env: android_world_controller.AndroidWorldController,
) -> list[Contact]:
  """Lists all contacts available in the Android environment.

  Args:
    env: Android environment to search for contacts.

  Returns:
    A list of all contact names and numbers present on the device.
  """
  intent_command = (
      "content query --uri content://contacts/phones/ --projection"
      " display_name:number"
  )
  adb_command = ["shell", intent_command]

  def parse(adb_output: str) -> Iterator[Contact]:
    for match in re.finditer(r"display_name=(.*), number=(.*)", adb_output):
      yield Contact(match.group(1), clean_phone_number(match.group(2)))

  return list(
      parse(
          adb_utils.issue_generic_request(
              adb_command, env
          ).generic.output.decode("utf-8")
      )
  )


def clear_contacts(env: android_world_controller.AndroidWorldController):
  """Clears all contacts on the device."""
  adb_utils.clear_app_data("com.android.providers.contacts", env)
```

### `official/install/android_world/utils/datetime_utils.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/datetime_utils.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Manages date and time settings on an Android device using ADB commands."""

import datetime
import enum
import random
import zoneinfo

from android_env import env_interface
from android_env.proto import adb_pb2
from android_world.env import adb_utils
from android_world.env import device_constants


def timestamp_to_localized_datetime(
    timestamp: int, timezone: str = device_constants.TIMEZONE
) -> datetime.datetime:
  """Converts a UNIX timestamp to a localized datetime object.

  Args:
    timestamp: The UNIX timestamp to convert.
    timezone: The timezone string to localize the datetime.

  Returns:
    A localized datetime object.
  """
  utc_dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
  localized_dt = utc_dt.astimezone(zoneinfo.ZoneInfo(timezone))
  return localized_dt


def _create_unix_ts(
    *,
    day: int,
    hour: int,
    month: int = device_constants.DT.month,
    year: int = device_constants.DT.year,
    timezone: str = device_constants.TIMEZONE,
) -> int:
  """Converts a year, month, day, and hour into a timestamp.

  Args:
    day: The day of the date.
    hour: The hour of the date.
    month: The month of the date.
    year: The year of the date.
    timezone: The timezone to use for the date. Defaults to
      device_constants.TIMEZONE.

  Returns:
    int: The timestamp corresponding to the input date and hour.
  """
  dt = datetime.datetime(year, month, day, hour)
  localized_dt = dt.replace(tzinfo=zoneinfo.ZoneInfo(timezone))
  result = int(localized_dt.timestamp())
  return result


def create_random_october_2023_unix_ts(
    start_day: int = device_constants.DT.day,
    end_day: int = 31,
    start_hour: int = 0,
) -> int:
  """Creates a random Unix timestamp in October 2023, the time period the device is set to.

  Args:
    start_day: The day to start in the random range.
    end_day: The day to end in the random range.
    start_hour: The hour to start in the random range; hour will be [start_hour,
      31]

  Returns:
    Unix timestamp.
  """
  return _create_unix_ts(
      day=random.randint(start_day, end_day),
      hour=random.randint(start_hour, 23),
      month=device_constants.DT.month,
      year=device_constants.DT.year,
      timezone=device_constants.TIMEZONE,
  )


class Toggle(enum.Enum):
  ON = '1'
  OFF = '0'


def toggle_auto_settings(
    env: env_interface.AndroidEnvInterface, toggle: Toggle
) -> None:
  """Disables the automatic date, time, and timezone settings.

  This is to maintain benchmark consistency and prevent external time updates.

  Args:
    env: AndroidEnv instance.
    toggle: Whether to enable or disable the settings.
  """
  adb_utils.put_settings(
      adb_pb2.AdbRequest.SettingsRequest.Namespace.GLOBAL,
      'auto_time',
      toggle.value,
      env,
  )
  adb_utils.put_settings(
      adb_pb2.AdbRequest.SettingsRequest.Namespace.GLOBAL,
      'auto_time_zone',
      toggle.value,
      env,
  )


def setup_datetime(env: env_interface.AndroidEnvInterface) -> None:
  """Prepares the Android device's date and time settings for benchmarking.

  This function should be called once before starting the benchmark tests. It
  disables automatic date, time, and timezone updates and sets the device to a
  24-hour time format. The purpose is to create a consistent environment for
  reproducible results.

  Args:
    env: AndroidEnv instance.
  """
  adb_utils.set_root_if_needed(env)
  toggle_auto_settings(env, Toggle.OFF)
  _enable_24_hour_format(env)
  _set_timezone_to_utc(env)


def set_datetime(
    env: env_interface.AndroidEnvInterface, dt: datetime.datetime
) -> None:
  """Configures the specific date and time for each task in the benchmark.

  This function should be called at the beginning of every task in the benchmark
  to set a specific date and time, ensuring consistency across repeated runs of
  the same task.

  Args:
    env: AndroidEnv instance.
    dt: The datetime to set the device to.
  """
  adb_utils.set_root_if_needed(env)
  _set_datetime(env, dt)


def advance_system_time(
    delta: datetime.timedelta,
    env: env_interface.AndroidEnvInterface,
) -> None:
  """Advance system time by a given time delta.

  Args:
    delta: Specify the amount of time to add to current time.
    env: AndroidEnv instance.
  """
  # Get current system time by parsing the output of running adb shell date
  # which looks like "Sun Oct 15 17:04:16 UTC 2023".
  current_time = datetime.datetime.strptime(
      adb_utils.issue_generic_request(
          ['shell', 'date'], env
      ).generic.output.decode().strip(),
      '%a %b %d %H:%M:%S %Z %Y',
  )

  # Set new system time.
  adb_utils.issue_generic_request(
      ['shell', 'date', (current_time + delta).strftime('%m%d%H%M%y.%S')], env
  )


def _enable_24_hour_format(env: env_interface.AndroidEnvInterface) -> None:
  """Sets to 24-hour time format to be consistent and region-independent."""
  adb_utils.put_settings(
      adb_pb2.AdbRequest.SettingsRequest.Namespace.SYSTEM,
      'time_12_24',
      '24',
      env,
  )


def _set_timezone_to_utc(env: env_interface.AndroidEnvInterface) -> None:
  """Sets the Android device's timezone to UTC.

  Args:
      env: An instance of AndroidEnv interface.
  """
  adb_command = ['shell', 'service', 'call', 'alarm', '3', 's16', 'UTC']
  adb_utils.issue_generic_request(adb_command, env)


def _set_datetime(
    env: env_interface.AndroidEnvInterface, dt: datetime.datetime
) -> None:
  """Sets the date and time on the Android device."""
  adb_utils.issue_generic_request(
      ['shell', 'date', dt.strftime('%m%d%H%M%y.%S')], env
  )


def generate_random_datetime(
    window_size: datetime.timedelta = datetime.timedelta(days=14),
    window_center: datetime.datetime = device_constants.DT,
) -> datetime.datetime:
  """Generates a random datetime within the given window.

  The window that the generated datetime is taken from is centered on
  device_constants.DT (= today) and is of length window_size.

  Args:
    window_size: The window size to generate a random datetime for.
    window_center: The center of the window to generate a random datetime for.

  Returns:
    A random datetime within the specified window.
  """
  start = window_center - (window_size / 2)
  return start + datetime.timedelta(
      minutes=random.randrange(window_size.days * 24 * 60)
  )
```

### `official/install/android_world/utils/file_utils.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/file_utils.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utils for file operations using adb."""

import contextlib
import dataclasses
import datetime
import os
import pathlib
import random
import shutil
import string
import tempfile
from typing import Iterator
from typing import Optional

from absl import logging
from android_env import env_interface
from android_env.components import errors
from android_env.proto import adb_pb2
from android_world.env import adb_utils
from android_world.utils import fuzzy_match_lib


def get_local_tmp_directory() -> str:
  """Returns the local temporary directory path.

  Returns:
    str: The local temporary directory path.
  """
  return tempfile.gettempdir()


def convert_to_posix_path(*args):
  """Converts the given path to a posix path.

  It can also be used to join paths.

  Args:
    *args: The paths to join.

  Returns:
    str: The path in posix format.
  """
  return str(pathlib.Path(*args).as_posix())


@dataclasses.dataclass(frozen=True)
class FileWithMetadata:
  """File with its metadata like change time.

  Attributes:
    file_name: file name.
    full_path: file name with full path.
    file_size: file size in bytes.
    change_time: file change time (ctime).
  """

  file_name: str
  full_path: str
  file_size: int
  change_time: datetime.datetime


def remove_single_file(
    target: str,
    base_path: str,
    env: env_interface.AndroidEnvInterface,
) -> None:
  """Remove a file (specified by its full path) if exists.

  Args:
    target: Target file name.
    base_path: Base directory to search for
    env: The environment to use.
  """
  if check_directory_exists(base_path, env):
    file_list = get_file_list_with_metadata(base_path, env)
    if target in [file_info.file_name for file_info in file_list]:
      adb_utils.issue_generic_request(
          ["shell", "rm", "-r", convert_to_posix_path(base_path, target)],
          env,
      )
  else:
    logging.warn(
        "Base path %s does not exist, ignoring remove_single_file.", base_path
    )


def clear_directory(
    directory_path: str,
    env: env_interface.AndroidEnvInterface,
) -> None:
  """Removes all files in the folder; also checks if folder is not empty.

  Args:
    directory_path: Location to create the file.
    env: The environment to use.

  Raises:
    RuntimeError when directory exists a failure occured while deleting files.
  """
  if not check_directory_exists(directory_path, env):
    return

  # Check if the folder is empty
  res = adb_utils.issue_generic_request(
      ["shell", "ls", "-1", directory_path], env
  )
  folder_contents = res.generic.output.decode().replace("\r", "").strip()

  if folder_contents:
    adb_utils.check_ok(
        adb_utils.issue_generic_request(
            ["shell", "rm", "-r", f"{directory_path}/*"],
            env,
        ),
        f"Failed to clear directory {directory_path}.",
    )


def create_file(
    file_name: str,
    directory_path: str,
    env: env_interface.AndroidEnvInterface,
    content: str = "",
) -> str:
  """Creates a new file.

  Args:
    file_name: Name of file.
    directory_path: Location to create the file.
    env: The environment to use.
    content: The contents to write to the file. If nothing is provided, then
      random text will be added.

  Returns:
    Content of the created file.
  """
  if not content:
    content = "".join(
        random.choices(string.ascii_letters + string.digits, k=20)
    )
  # Escape quotes to avoid issues with writing them to file.
  content = content.replace("'", "'\"'\"'")
  mkdir(directory_path, env)
  adb_utils.issue_generic_request(
      [
          "shell",
          "echo",
          f"'{content}'",
          ">",
          f"{directory_path}/{file_name}",
      ],
      env,
  )
  return content


def mkdir(directory_path: str, env: env_interface.AndroidEnvInterface) -> None:
  """Makes a directory using adb.

  Args:
    directory_path: The location to make it.
    env: The environment.

  Raises:
    RuntimeError when directory could not be created.
  """
  adb_utils.check_ok(
      adb_utils.issue_generic_request(
          [
              "shell",
              "mkdir",
              "-p",
              directory_path,
          ],
          env,
      ),
      f"Failed to create directory {directory_path}.",
  )


def copy_dir(
    source_path: str, dest_path: str, env: env_interface.AndroidEnvInterface
):
  """Recursively copies from one directory to another on device.

  Args:
    source_path: Source directory path on device.
    dest_path: Destination directory path on device.
    env: The environment.

  Raises:
    RuntimeError when the contents of the source path directory can not be
    written to the destination path.
  """

  if not check_directory_exists(source_path, env):
    logging.warn(
        "Source directory %s does not exist, ignoring copy_dir.", source_path
    )
    return

  if not check_directory_exists(dest_path, env):
    mkdir(dest_path, env)  # RuntimeError raised if path exists as a file.

  adb_utils.check_ok(
      adb_utils.issue_generic_request(
          ["shell", "cp", "-a", f"{source_path}/.", f"{dest_path}/"], env
      ),
      f"Failure copying {source_path} directory to {dest_path}.",
  )


def check_file_or_folder_exists(
    target: str, base_path: str, env: env_interface.AndroidEnvInterface
) -> bool:
  """Recursively checks if a file or folder exists under the specified base path.

  Args:
      target: Name of the file or folder to search for.
      base_path: The directory path under which to search.
      env: The Android environment interface.

  Returns:
      bool: True if the file or folder exists, False otherwise.

  Raises:
    RuntimeError: When ADB does not correctly execute.
  """
  if not check_directory_exists(base_path, env):
    return False

  # List all files and folders recursively under the base path
  res = adb_utils.issue_generic_request(
      ["shell", "find", base_path, "-type", "f", "-o", "-type", "d"], env
  )

  if not res.status:
    raise RuntimeError("ADB command failed.")

  all_paths = set(res.generic.output.decode().replace("\r", "").split("\n"))

  full_target_path = convert_to_posix_path(base_path, target)
  return full_target_path in all_paths


def check_file_exists(
    path: str,
    env: env_interface.AndroidEnvInterface,
    bash_file_test: str = "-f",
) -> bool:
  """Check if a file exists.

  Args:
    path: The path to check.
    env: The environment.
    bash_file_test: Bash test string. Use "-f" for file, "-d" for directory, and
      "-e" for either.

  Returns:
    Whether the file exists.
  """
  bash_script = f"""
  if [ {bash_file_test} "{path}" ]; then
      echo "Exists"
  else
      echo "Does not exist"
  fi
  """
  response = adb_utils.issue_generic_request(["shell", bash_script], env)
  if "Exists" in response.generic.output.decode("utf-8"):
    return True
  elif "Does not exist" in response.generic.output.decode("utf-8"):
    return False
  else:
    raise errors.AdbControllerError("Unexpected output from file check")


def check_directory_exists(
    path: str, env: env_interface.AndroidEnvInterface
) -> bool:
  """Check if a directory exists.

  Args:
    path: The path to check.
    env: The environment.

  Returns:
    Whether the directory exists.
  """
  return check_file_exists(path, env, bash_file_test="-d")


@contextlib.contextmanager
def tmp_directory_from_device(
    device_path: str,
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = None,
):
  """Copy a directory from the device to a local temporary directory using ADB.

  Args:
    device_path: The path of the directory on the Android device.
    env: The Android environment interface.
    timeout_sec: A timeout for the ADB operations.

  Yields:
    A temporary folder that contains files copied from the device that is
    automatically deleted after use.

  Raises:
    FileExistsError: If the temp directory already exists.
    FileNotFoundError: If the remote directory does not exist.
    RuntimeError: If there is an adb communication error.
  """
  tmp_directory = tempfile.mkdtemp()
  logging.info(
      "Copying %s directory to local tmp %s", device_path, tmp_directory
  )

  adb_utils.set_root_if_needed(env, timeout_sec)

  if not check_directory_exists(device_path, env):
    raise FileNotFoundError(f"{device_path} does not exist.")
  try:
    os.makedirs(tmp_directory, exist_ok=True)
    files = get_file_list_with_metadata(device_path, env, timeout_sec)
    for file in files:
      pull_response = env.execute_adb_call(
          adb_pb2.AdbRequest(
              pull=adb_pb2.AdbRequest.Pull(path=file.full_path),
              timeout_sec=timeout_sec,
          )
      )
      adb_utils.check_ok(pull_response)
      with open(
          convert_to_posix_path(tmp_directory, file.file_name), "wb"
      ) as f:
        f.write(pull_response.pull.content)

    yield tmp_directory

  finally:
    try:
      shutil.rmtree(tmp_directory)
    except Exception as e:  # pylint: disable=broad-exception-caught
      logging.error(
          "Failed to delete temporary directory: %s with error %s",
          tmp_directory,
          e,
      )


@contextlib.contextmanager
def tmp_file_from_device(
    device_file: str,
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = None,
) -> Iterator[str]:
  """Copies a remote file to a local temporary file.

  Args:
    device_file: The path on the device pointing to a file.
    env: The environment.
    timeout_sec: A timeout for the ADB operations.

  Yields:
    The name of the local temporary file.

  Raises:
    FileNotFoundError: If device_file does not exist.
    RuntimeError: If there is an adb communication error.
  """
  tmp_directory = tempfile.mkdtemp()
  head, tail = os.path.split(device_file)
  dir_and_file_name = convert_to_posix_path(os.path.basename(head), tail)
  local_file = convert_to_posix_path(tmp_directory, dir_and_file_name)
  try:
    # Need root access to access many directories.
    adb_utils.set_root_if_needed(env, timeout_sec)

    if not check_file_exists(device_file, env):
      raise FileNotFoundError(f"{device_file} does not exist.")
    if not os.path.exists(os.path.dirname(local_file)):
      os.makedirs(os.path.dirname(local_file), exist_ok=True)
    pull_response = env.execute_adb_call(
        adb_pb2.AdbRequest(
            pull=adb_pb2.AdbRequest.Pull(path=device_file),
            timeout_sec=timeout_sec,
        )
    )
    adb_utils.check_ok(pull_response)

    with open(local_file, "wb") as f:
      f.write(pull_response.pull.content)

    yield local_file
  finally:
    try:
      shutil.rmtree(tmp_directory)
    except Exception as e:  # pylint: disable=broad-exception-caught
      logging.error(
          "Failed to delete temporary directory: %s with error %s",
          tmp_directory,
          e,
      )


def copy_file_to_device(
    local_file_path: str,
    remote_file_path: str,
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = None,
) -> adb_pb2.AdbResponse:
  """Copies a local file to a remote file."""
  with open(local_file_path, "rb") as f:
    file_contents = f.read()
    push_request = adb_pb2.AdbRequest(
        push=adb_pb2.AdbRequest.Push(
            content=file_contents, path=remote_file_path
        ),
        timeout_sec=timeout_sec,
    )
  push_response = env.execute_adb_call(push_request)

  # ' and whitespace are special characters in adb commands that need to be
  # escaped.
  escaped_path = remote_file_path.replace(" ", r"\ ").replace("'", r"\'")

  adb_utils.issue_generic_request(["shell", "chmod", "777", escaped_path], env)
  return push_response


def copy_data_to_device(
    local_path: str,
    remote_path: str,
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = None,
) -> adb_pb2.AdbResponse:
  """Copy a file or directory to the device from the local file system using ADB.

  Args:
    local_path: The path of the file or directory on the local file system.
    remote_path: The destination path on the Android device.
    env: The Android environment interface.
    timeout_sec: A timeout for the ADB operation.

  Returns:
    A response object containing the ADB operation result.

  Raises:
    FileNotFoundError: If the local file or directory does not exist. Or if
      remote path does not exist.
  """
  if not os.path.exists(local_path):
    raise FileNotFoundError(f"{local_path} does not exist.")
  response = adb_pb2.AdbResponse()
  if os.path.isfile(local_path):
    # If the file extension is different, remote_path is likely a directory.
    if os.path.splitext(local_path)[1] != os.path.splitext(remote_path)[1]:
      remote_path = convert_to_posix_path(
          remote_path, os.path.basename(local_path)
      )
    return copy_file_to_device(local_path, remote_path, env, timeout_sec)

  # Copying a directory over, push every file separately.
  for file_path in os.listdir(local_path):
    current_response = copy_file_to_device(
        convert_to_posix_path(local_path, file_path),
        convert_to_posix_path(remote_path, os.path.basename(file_path)),
        env,
        timeout_sec,
    )
    if current_response.status != adb_pb2.AdbResponse.OK:
      return current_response
    response = current_response

  return response


def get_file_list_with_metadata(
    directory_path: str,
    env: env_interface.AndroidEnvInterface,
    timeout_sec: Optional[float] = None,
) -> list[FileWithMetadata]:
  """Get the list of all (regular) files with metadata in a given directory.

  Right now we only list regular files in the given directory and only grab file
  name, full directory and change time in metadata.

  Args:
    directory_path: The directory to list all its files.
    env: The Android environment interface.
    timeout_sec: A timeout for the ADB operation.

  Returns:
    A list of files with metadata.
  Raises:
    RuntimeError: If the input directory path is not valid or shell ls fails.
  """
  if not check_directory_exists(directory_path, env):
    raise RuntimeError(f"{directory_path} is not a valid directory.")
  # Run [adb shell ls] to list all files in the given directory.
  try:
    ls_response = adb_utils.issue_generic_request(
        f"shell ls {directory_path} -ll -au", env, timeout_sec
    )
    adb_utils.check_ok(ls_response, "Failed to list files in directory.")
    files = []
    # Each file (including links and directories) will be listed in format as
    # follows,
    #  -rw-rw---- 1 u0_a158 media_rw 0 2023-11-28 23:17:43.176000000 +0000 1.txt
    # We loop through all the files and collect regular files with metadata.
    for file_details in ls_response.generic.output.decode("utf-8").split("\n"):
      # In shell output, the first character is used to indicate file type and
      # "-" means the file is a regular file.
      if file_details.startswith("-"):
        parts = file_details.split(None, 8)
        if len(parts) < 9:
          raise RuntimeError(f"Failed to parse file details: {file_details}")

        file_name = parts[
            8
        ].strip()  # This will preserve spaces in the filename
        files.append(
            FileWithMetadata(
                file_name=file_name,
                full_path=convert_to_posix_path(directory_path, file_name),
                file_size=int(parts[4]),
                change_time=datetime.datetime.fromisoformat(
                    " ".join(parts[5:7])[:-3]
                ),
            )
        )
    return files
  except errors.AdbControllerError as e:
    print(e)
    raise RuntimeError("Failed to list files in directory.") from e


def check_file_content(
    file_full_path: str,
    content: str,
    env: env_interface.AndroidEnvInterface,
    exact_match: bool = False,
    timeout_sec: Optional[float] = None,
) -> bool:
  """Check if a file content equals a given string.

  Args:
    file_full_path: Full path to the file, will return False if file does not
      exist.
    content: The expected file content.
    env: The Android environment interface.
    exact_match: A boolean indicates whether we use exact match or fuzzy match.
    timeout_sec: A timeout for the ADB operation.

  Returns:
    If the given file has the given content, will return False in the case of
    incorrect file path/file does not exist.
  """

  try:
    res = adb_utils.issue_generic_request(
        ["shell", "cat", file_full_path], env, timeout_sec
    )
    res_content = res.generic.output.decode().replace("\r", "")
    if exact_match:
      return res_content == content
    return fuzzy_match_lib.fuzzy_match(res_content.strip(), content)
  except errors.AdbControllerError as e:
    print(e)
    return False
```

### `official/install/android_world/utils/fuzzy_match_lib.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/fuzzy_match_lib.py`

```python
# Copyright 2026 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utility functions for fuzzy matching."""

import difflib


# Threshold for determining if two strings are equal using
# difflib.SequenceMatcher(...).ratio().
_MIN_DIFF_SIMILARITY = 0.9


def fuzzy_match(text1: str, text2: str, ignore_case: bool = True) -> bool:
  """Compares two strings.

  Args:
    text1: The first text.
    text2: The second text.
    ignore_case: Whether to ignore case during comparison.

  Returns:
    Whether the two strings are approximately equal.
  """
  if text1 is None or text2 is None:
    return False
  text1 = str(text1)
  text2 = str(text2)

  def text_similarity(text1: str, text2: str, ignore_case: bool) -> float:
    """Computes similiarity between two texts."""
    if ignore_case:
      text1 = text1.lower()
      text2 = text2.lower()

    return difflib.SequenceMatcher(None, text1, text2).ratio()
  return (
      text_similarity(text1, text2, ignore_case=ignore_case)
      >= _MIN_DIFF_SIMILARITY
  )
```

### `derived/selected_task_source.json`

Source ref: `androidworld://SimpleCalendarAddOneEventTomorrow`

```json
{
  "base_class_name": "SimpleCalendarAddOneEvent",
  "base_module": "android_world.task_evals.single.calendar.calendar",
  "base_source_file": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
  "canonical_goal_authority": "runtime task goal plus evaluator code; metadata conflicts are recorded, never silently preferred",
  "canonical_goal_representation_kind": "format_template",
  "case_unit_id": "SimpleCalendarAddOneEventTomorrow",
  "class_name": "SimpleCalendarAddOneEventTomorrow",
  "difficulty": "easy",
  "metadata_code_conflict_count": 0,
  "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
  "metadata_task_template": "In Simple Calendar Pro, create a calendar event for tomorrow at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins.",
  "module": "android_world.task_evals.single.calendar.calendar",
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
      "archive_path": "official/install/android_world/task_evals/single/calendar/calendar.py",
      "sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/calendar.py"
    },
    {
      "archive_path": "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
      "sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/common_validators/sqlite_validators.py",
      "sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/common_validators/sqlite_validators.py"
    },
    {
      "archive_path": "official/install/android_world/suite_utils.py",
      "sha256": "caf4d3a8765c914a2b978d119921cc4c062176e5a362c20c53905d4d0dbe083b",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/suite_utils.py"
    }
  ],
  "optimal_steps": "13",
  "packet_files": [
    "official/install/android_world/task_metadata.json",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_evals/single/calendar/calendar.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
    "official/install/android_world/task_evals/common_validators/sqlite_validators.py",
    "official/install/android_world/suite_utils.py",
    "derived/selected_task_source.json"
  ],
  "runtime_reported_module": "android_world.task_evals.single.calendar.calendar",
  "runtime_reported_source_file": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
  "selection_order_key": "19a8db551ff6bce9e703a6cbeffc0a655fa0a1ba00ba9f90fadd209c8fa7fbe2",
  "selection_rank": 9,
  "semantic_authority_files": [
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/calendar.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/common_validators/sqlite_validators.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/suite_utils.py"
  ],
  "semantic_record_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/SimpleCalendarAddOneEventTomorrow/canonical_task_semantics.json",
  "semantic_record_sha256": "6f3bf04dc0a5669ad3a4c464332f4402c3eee076dedfd08806c6f3f3b028de4c",
  "source_file": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/calendar.py",
  "source_ref": "androidworld://SimpleCalendarAddOneEventTomorrow",
  "source_sha256": "1e7c209fa319d47a83ce04bfb1b0b560e73dca2834bd2b20e28c5a2d1315b0ca",
  "tags": [
    "data_entry",
    "parameterized"
  ],
  "task_id": "SimpleCalendarAddOneEventTomorrow",
  "task_name": "SimpleCalendarAddOneEventTomorrow",
  "task_template": "In Simple Calendar Pro, create a calendar event for tomorrow at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins."
}
```

### `derived/source_closure.json`

Source ref: `androidworld-source-closure://SimpleCalendarAddOneEventTomorrow@d9c569f764b3a5629321858de03ff653d0f24056`

```json
{
  "algorithm": "recursive Python AST closure from task/base/task_eval plus explicit dynamic-IR resources; registry retained but not expanded",
  "case_unit_id": "SimpleCalendarAddOneEventTomorrow",
  "closure_file_count": 43,
  "closure_sha256": "ccb5b4118bf685869042fdbc3bbd881c1f3b4532a7985ecf573d300695a9b0cf",
  "core_descriptor_count": 7,
  "external_python_packages_not_embedded": [
    "abc",
    "absl",
    "android_env",
    "collections",
    "contextlib",
    "copy",
    "dataclasses",
    "datetime",
    "difflib",
    "dm_env",
    "enum",
    "google",
    "immutabledict",
    "inspect",
    "json",
    "logging",
    "numpy",
    "os",
    "pathlib",
    "random",
    "re",
    "requests",
    "shutil",
    "sqlite3",
    "string",
    "tempfile",
    "textwrap",
    "time",
    "typing",
    "unicodedata",
    "uuid",
    "xml",
    "zoneinfo"
  ],
  "files": [
    {
      "archive_path": "official/install/android_world/task_metadata.json",
      "git_blob_oid": "3ee67af832b3840fe9fc01fcabdad87b3f019e85",
      "sha256": "fd3cf23ebb26e461a961dd60ff3f011d7e6ec78c992c10babbbdb86f9dd591e1",
      "source_kind": "frozen_core_descriptor",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json"
    },
    {
      "archive_path": "official/install/android_world/registry.py",
      "git_blob_oid": "d6f052297332f402255cda409cff58e8fb17a269",
      "sha256": "47380849f428b231747365ac8ba50a83212cdc34180ab6376ff49e90b93af12b",
      "source_kind": "frozen_core_descriptor",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/task_eval.py",
      "git_blob_oid": "a04b5f4dc97eb5a6033d2ae54e611601b565e367",
      "sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
      "source_kind": "frozen_core_descriptor",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/single/calendar/calendar.py",
      "git_blob_oid": "a2c4dd782f4564ae9e88923dee58fc89ab7a1fb9",
      "sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
      "source_kind": "frozen_core_descriptor",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/calendar.py"
    },
    {
      "archive_path": "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
      "git_blob_oid": "a2c4dd782f4564ae9e88923dee58fc89ab7a1fb9",
      "sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
      "source_kind": "frozen_core_descriptor",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/common_validators/sqlite_validators.py",
      "git_blob_oid": "3ac58cd5f37c3df154734ce691c7502afff53676",
      "sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
      "source_kind": "frozen_core_descriptor",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/common_validators/sqlite_validators.py"
    },
    {
      "archive_path": "official/install/android_world/suite_utils.py",
      "git_blob_oid": "cdf46e5208195d1d55dc4107a64b2550d83a7d1c",
      "sha256": "caf4d3a8765c914a2b978d119921cc4c062176e5a362c20c53905d4d0dbe083b",
      "source_kind": "frozen_core_descriptor",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/suite_utils.py"
    },
    {
      "archive_path": "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/state_pb2.py",
      "git_blob_oid": null,
      "sha256": "7fcc0e0c1cd8c1d03d644e23a2c2d3e17709d6f1cddc4b04655be9bda035cde4",
      "source_kind": "generated_build_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/state_pb2.py"
    },
    {
      "archive_path": "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/task_pb2.py",
      "git_blob_oid": null,
      "sha256": "1cc5638cf6dc51463dffd7ca9ee3c85cbabcb66e89815ee4bf53f61dc7c7e84c",
      "source_kind": "generated_build_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/task_pb2.py"
    },
    {
      "archive_path": "official/install/android_world/env/__init__.py",
      "git_blob_oid": "1cc89603d74875e0e5a6b1ead9ff2bfcb0380ad7",
      "sha256": "1cb8fdedd768b8016bb55733b1077301ecfe9b801b28fbcb028addbbc0981239",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/__init__.py"
    },
    {
      "archive_path": "official/install/android_world/env/actuation.py",
      "git_blob_oid": "6a30fec8b80207a796c0617adbcb6f7155132992",
      "sha256": "6be679b15544a713279aeaad3f4864757747accda1bd00185ae7f67b22623725",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/actuation.py"
    },
    {
      "archive_path": "official/install/android_world/env/adb_utils.py",
      "git_blob_oid": "17a53f530af03927f36573d670b59d5b7511ec25",
      "sha256": "15c61078c8d6d091c2784feef231e1477e11304da0c7d383cf574fff629c1d00",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/adb_utils.py"
    },
    {
      "archive_path": "official/install/android_world/env/android_world_controller.py",
      "git_blob_oid": "2f3133060cd12239312c7af96249b4d5420dd791",
      "sha256": "989968aba1a2ef5f9bd70af24762e5480d809ef0c4c07f82c7b8167e5d8bbf8c",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/android_world_controller.py"
    },
    {
      "archive_path": "official/install/android_world/env/device_constants.py",
      "git_blob_oid": "ad8e3b1af0e3925cc9dfd5244922847e52c9fc75",
      "sha256": "259b41e545a2887e734991c389b0c85db8ff4824149a9e2458e93ec7741a731c",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/device_constants.py"
    },
    {
      "archive_path": "official/install/android_world/env/interface.py",
      "git_blob_oid": "e4440b022703b1f361f1a64fa8a5e49db777e619",
      "sha256": "c9372c3dcaef98cd20d67f7bf9084ab9609c5b2eeb2da9f35448d0ebe0483a00",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/interface.py"
    },
    {
      "archive_path": "official/install/android_world/env/json_action.py",
      "git_blob_oid": "5f1efd34d27377b2238a5c7676318c6e9e5eb386",
      "sha256": "142755d4e0a2d3f761562b726d849d906b49c83f4a91b09dfa3a779e24386127",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/json_action.py"
    },
    {
      "archive_path": "official/install/android_world/env/representation_utils.py",
      "git_blob_oid": "b42e75893a942ccd9a8a2f57d16988918bc5c3f7",
      "sha256": "4fdfc593668ade52dc477a119f7c8d83d77cdc939d5c97ce8dd291a018ca56d2",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/representation_utils.py"
    },
    {
      "archive_path": "official/install/android_world/env/setup_device/__init__.py",
      "git_blob_oid": "4489fb44f1cfa82d148a0c9219f3fa19f44803fa",
      "sha256": "55029b4439d73a294227fe467ee2b3c3d7ad9820b61bfd58bf5b39af1601a87e",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/setup_device/__init__.py"
    },
    {
      "archive_path": "official/install/android_world/env/setup_device/apps.py",
      "git_blob_oid": "8e113e72fb02eef40c65b41c05549b3328339d2b",
      "sha256": "109e51edba6a3bf6b9451d084d6cd8ca2c06e0e1415db1eac441af63e83783f6",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/setup_device/apps.py"
    },
    {
      "archive_path": "official/install/android_world/env/setup_device/setup.py",
      "git_blob_oid": "644c156be91f0345829ba4443d412d2dd5c335ee",
      "sha256": "1874126ccc2ca48265c6803c2b420f77ae6a2a4193ba9d7279cd96d84f571de6",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/setup_device/setup.py"
    },
    {
      "archive_path": "official/install/android_world/env/tools.py",
      "git_blob_oid": "edf11570e2464d77a2725fb8a60e60ed1edb124f",
      "sha256": "987f97ffdc76ba4745ea1401044a11f23fc79b49ac642e7a6c8cbef3ae9b5b9a",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/tools.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/__init__.py",
      "git_blob_oid": "50ccd3065cd7acaded2664e2e8da1d6f73e8cb30",
      "sha256": "d99873f57aa5a9e5598581e873ab497f6e3cc2fcb9800de4a2896169fcfc0f0a",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/__init__.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/common_validators/__init__.py",
      "git_blob_oid": "ec74422ce9356321a0725bcf4b9f09d03c60589a",
      "sha256": "5a5942e515bf7fafc12f799e1f569109193ea59b912daf7ffd6d484f422ea3da",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/common_validators/__init__.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/information_retrieval/__init__.py",
      "git_blob_oid": "2341e0ec46dadf33709834218d417d1ea32ef8e7",
      "sha256": "e3b356b9bc0d1f8d3e3edbdf1c0d25dc59aacd02118d59302fdb8624cd345aa4",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/__init__.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/information_retrieval/datetime_utils.py",
      "git_blob_oid": "d158f175d5baf35c07702dbebe08677835c383d8",
      "sha256": "6812cb1dedc17914eb3c89678fedaacb360a4f71bf3cc5bd8849a986f9f5ba90",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/datetime_utils.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/information_retrieval/joplin_app_utils.py",
      "git_blob_oid": "acb5db8d257e0628039930f7f17f6a3d64d29f37",
      "sha256": "fceb231218c9b59dbdfa35dabb8713e9700338cf3787ae7c69f565d959ba18fe",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/joplin_app_utils.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/information_retrieval/proto/__init__.py",
      "git_blob_oid": "adc96a25497a9199ff9b32442512923813af1e5f",
      "sha256": "0a303e72ba0eacbf79ad584c605af6205d6e5f3c176c722b14d4e0ce990ca89b",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/proto/__init__.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/information_retrieval/proto/state.proto",
      "git_blob_oid": "8b006162fc232fd7549dd375e7e4eccf49aa8a14",
      "sha256": "17bbf2880baace87b35c4fcf8729b44414d53e07c623ad8705742012ad8661ab",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/proto/state.proto"
    },
    {
      "archive_path": "official/install/android_world/task_evals/information_retrieval/proto/task.proto",
      "git_blob_oid": "2b418edb15cd3f51bd36f82777db783d2652b61c",
      "sha256": "c8c25f9034abe201055e4e8a457e3101b1a64cbd876323f22eca47fc5f5b9d8a",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/proto/task.proto"
    },
    {
      "archive_path": "official/install/android_world/task_evals/information_retrieval/proto_utils.py",
      "git_blob_oid": "57d0ac81c33c7132f4f3fac11caecedebda0b926",
      "sha256": "301f83956b1b2ac2ce5bca0f75357f7a31d2a9a8a8145da737efa1539d6961cb",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/proto_utils.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/single/calendar/__init__.py",
      "git_blob_oid": "734e41465f70fdeb7091d74f1ae6ded716cead65",
      "sha256": "5f65b84304b8d15f58871be761f7b624ec9ad389fe08848a41d2a4ab7395b08a",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/__init__.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/single/calendar/calendar_evaluators.py",
      "git_blob_oid": "951b0f34bee648d6586b328bf13c0002f339097b",
      "sha256": "ad25b8064ee5d5341f97a902ff222342456e9932a431ee06945f5f8992d53273",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/calendar_evaluators.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/single/calendar/calendar_utils.py",
      "git_blob_oid": "e70055ab1c621c30420c4378c6fd51e5f45cc784",
      "sha256": "14ff8d7db0d1ffaf7c45307f79ed7b6bc200c62143d5892833f7fe88706fc315",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/calendar_utils.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/single/calendar/events_generator.py",
      "git_blob_oid": "a85222e6002eddb97af8d5a307fa571e8c46cddf",
      "sha256": "0b894783493407dfffff4b7e02b68e778f7d2667358965e5bb4f9a78a7fb5963",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/events_generator.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/utils/__init__.py",
      "git_blob_oid": "f3f61910fa66bcdaab8a1b62674ff13d447de1da",
      "sha256": "761fd2724b3525c58df44e4b0ab36953c60aa8b9af8bf12460bd508ff2d3ba1b",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/utils/__init__.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/utils/sqlite_schema_utils.py",
      "git_blob_oid": "645812f593bbd5949a5ef1bdade51038ebc9cb87",
      "sha256": "0e995bbc182e2ea35f3c68200a766cd288a60a597d71082f3ba5617b665366ed",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/utils/sqlite_schema_utils.py"
    },
    {
      "archive_path": "official/install/android_world/task_evals/utils/sqlite_utils.py",
      "git_blob_oid": "532c13f220f724b0796526be48e43b4c21be2a52",
      "sha256": "61cab2a77135b47915843b4202b98be735af1cdd4220908f9f35da4265098c8a",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/utils/sqlite_utils.py"
    },
    {
      "archive_path": "official/install/android_world/utils/__init__.py",
      "git_blob_oid": "bad40fa3a752f8adfb40c01d8be15965d1fc149b",
      "sha256": "9edbb8eb66e5175a40f26ff4424d2b62dc66077ab81f78768e1da879e866a69a",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/__init__.py"
    },
    {
      "archive_path": "official/install/android_world/utils/app_snapshot.py",
      "git_blob_oid": "8632ef293baa114530a7f91e34047460e3df9bd9",
      "sha256": "9689192d31ffd29298c3f740ac29783bb03294faebdd5c1964a2904fdb3bddd4",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/app_snapshot.py"
    },
    {
      "archive_path": "official/install/android_world/utils/contacts_utils.py",
      "git_blob_oid": "5f23281a7a84b2b38f526580a3b16c8c026b6b09",
      "sha256": "92f193c0cedd301fdc8f5f7a8ba6fec2410f16d82d0259ab9cdd844dbd0925c3",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/contacts_utils.py"
    },
    {
      "archive_path": "official/install/android_world/utils/datetime_utils.py",
      "git_blob_oid": "8ee68a0d71b10c68885fb4ade0014b3e6cfbcc97",
      "sha256": "32594fcd09e038467166678c7894b649f32c3a815f054b5d85c0fdb69b9d6e81",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/datetime_utils.py"
    },
    {
      "archive_path": "official/install/android_world/utils/file_utils.py",
      "git_blob_oid": "bf2280346a0334f458530de47592569fbd71b564",
      "sha256": "5bd04ccdafba65f4b909c8bb9fca166e5eba92dc2e64c83f80729941dfab2d1d",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/file_utils.py"
    },
    {
      "archive_path": "official/install/android_world/utils/fuzzy_match_lib.py",
      "git_blob_oid": "a87a232da4381024f66728f151598dd32c20b8e1",
      "sha256": "e7376554fd9a413ff00d71656e09609c9070d0b384028b89fd931e32fcfb2969",
      "source_kind": "git_source_dependency",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/fuzzy_match_lib.py"
    }
  ],
  "internal_import_edge_count": 133,
  "schema_version": "androidworld_case_source_closure/v1",
  "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
  "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
  "source_commit": "d9c569f764b3a5629321858de03ff653d0f24056",
  "task_id": "SimpleCalendarAddOneEventTomorrow",
  "unresolved_internal_imports": []
}
```

### `derived/canonical_task_semantics.json`

Source ref: `androidworld-canonical-semantics://SimpleCalendarAddOneEventTomorrow@6f3bf04dc0a5669ad3a4c464332f4402c3eee076dedfd08806c6f3f3b028de4c`

```json
{
  "canonical_module": "android_world.task_evals.single.calendar.calendar",
  "canonical_source_file": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/calendar/calendar.py",
  "case_unit_id": "SimpleCalendarAddOneEventTomorrow",
  "definition": {
    "definition_kind": "python_class",
    "incidental_runtime_module_excluded": null,
    "mro": [
      {
        "canonical_androidworld_source": true,
        "module": "android_world.task_evals.single.calendar.calendar",
        "qualname": "SimpleCalendarAddOneEventTomorrow",
        "source_ref": {
          "ast_sha256": "bd140103ca3d1023f79dda89955a07e058c56425856513e6f9d8eeda7e9d2356",
          "end_line": 199,
          "file_sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
          "path": "android_world/task_evals/single/calendar/calendar.py",
          "snippet_sha256": "1a63eb7a5713125134623149f3d89dc1c4086215f9152de05b16d4aaca13a041",
          "start_line": 182,
          "symbol": "SimpleCalendarAddOneEventTomorrow"
        }
      },
      {
        "canonical_androidworld_source": true,
        "module": "android_world.task_evals.single.calendar.calendar",
        "qualname": "SimpleCalendarAddOneEvent",
        "source_ref": {
          "ast_sha256": "a4a1d999e3126c9c8b7a9afabd9a4feaf2eda5d4a20aef994bce4db3e7e45e84",
          "end_line": 139,
          "file_sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
          "path": "android_world/task_evals/single/calendar/calendar.py",
          "snippet_sha256": "8b23addea3162b0268dc4fad8e87e094c44fec5a168ad06ed3ea1116cb0b22a2",
          "start_line": 85,
          "symbol": "SimpleCalendarAddOneEvent"
        }
      },
      {
        "canonical_androidworld_source": true,
        "module": "android_world.task_evals.common_validators.sqlite_validators",
        "qualname": "AddMultipleRows",
        "source_ref": {
          "ast_sha256": "2e801c534950f863ba825b6366be40b9679d4a4d48069ab04807b94018035d11",
          "end_line": 323,
          "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
          "path": "android_world/task_evals/common_validators/sqlite_validators.py",
          "snippet_sha256": "7b415c9bb1ebc10ece14a0ed262889b4c4db0fbecd327dd2c5f8261d2523e13f",
          "start_line": 271,
          "symbol": "AddMultipleRows"
        }
      },
      {
        "canonical_androidworld_source": true,
        "module": "android_world.task_evals.single.calendar.calendar",
        "qualname": "_SimpleCalendar",
        "source_ref": {
          "ast_sha256": "b37475fef92212b5ad9abc69fb854b2f09e4ca45c6849c9e1da584950ce94ac5",
          "end_line": 82,
          "file_sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
          "path": "android_world/task_evals/single/calendar/calendar.py",
          "snippet_sha256": "24705bc4830c48802dba65136f58cf31f4c8411d4b0e605e826c48941bab03ca",
          "start_line": 61,
          "symbol": "_SimpleCalendar"
        }
      },
      {
        "canonical_androidworld_source": true,
        "module": "android_world.task_evals.common_validators.sqlite_validators",
        "qualname": "SQLiteApp",
        "source_ref": {
          "ast_sha256": "44df368e12e9cf79cc0f4a5a3050a530e05ec7bd8341716c986019ffef8b5f7e",
          "end_line": 268,
          "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
          "path": "android_world/task_evals/common_validators/sqlite_validators.py",
          "snippet_sha256": "18cd7e4fc846f3bcad8cd564f530cc0c286ffd7ea74dfa8c338f571b9a90b7ac",
          "start_line": 200,
          "symbol": "SQLiteApp"
        }
      },
      {
        "canonical_androidworld_source": true,
        "module": "android_world.task_evals.task_eval",
        "qualname": "TaskEval",
        "source_ref": {
          "ast_sha256": "85d1a56897097bc400580d972badbaf66e2063a3fb9ddf45bfa65bfe92d05f09",
          "end_line": 190,
          "file_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
          "path": "android_world/task_evals/task_eval.py",
          "snippet_sha256": "555d49d2ef6e2fdd5d52484234181bdb3f7d874ac66bb5e068d01403f050351b",
          "start_line": 30,
          "symbol": "TaskEval"
        }
      },
      {
        "canonical_androidworld_source": false,
        "qualname": "ABC",
        "runtime_reported_module": "abc",
        "source_ref": null
      },
      {
        "canonical_androidworld_source": false,
        "module": "builtins",
        "qualname": "object",
        "source_ref": null
      }
    ],
    "runtime_reported_module": "android_world.task_evals.single.calendar.calendar",
    "source_bindings": [
      {
        "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/calendar/calendar.py",
        "ast_sha256": "bd140103ca3d1023f79dda89955a07e058c56425856513e6f9d8eeda7e9d2356",
        "end_line": 199,
        "owner_module": "android_world.task_evals.single.calendar.calendar",
        "owner_qualname": "SimpleCalendarAddOneEventTomorrow",
        "sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
        "snippet_sha256": "1a63eb7a5713125134623149f3d89dc1c4086215f9152de05b16d4aaca13a041",
        "start_line": 182
      }
    ]
  },
  "evaluator": {
    "branches": [],
    "method_chain": [
      {
        "branch_node_count": 1,
        "direct_calls": [
          "self.list_rows",
          "self.validate_addition_integrity"
        ],
        "direct_parameter_reads": [],
        "owner_class": "AddMultipleRows",
        "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
        "source_ref": {
          "ast_sha256": "f2751ca3568b387056d6f4fdec053268e79d42a6e48ba54bce1e094203f0e07a",
          "end_line": 310,
          "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
          "path": "android_world/task_evals/common_validators/sqlite_validators.py",
          "snippet_sha256": "64097499692465a3a591ea95f000120ccced1957f73425ff2dc757e9ae1745c7",
          "start_line": 304,
          "symbol": "AddMultipleRows.is_successful"
        }
      },
      {
        "branch_node_count": 0,
        "direct_calls": [
          "self._check_is_initialized"
        ],
        "direct_parameter_reads": [],
        "owner_class": "TaskEval",
        "owner_module": "android_world.task_evals.task_eval",
        "source_ref": {
          "ast_sha256": "4ba02bae85e87232a171f4ab6decd0f081113181a5d2fcbd220a205512f58e16",
          "end_line": 180,
          "file_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
          "path": "android_world/task_evals/task_eval.py",
          "snippet_sha256": "cb4c4fd2a9f4efa9fe8fb8328f459b54febf84903006338ae246acd0c445e098",
          "start_line": 166,
          "symbol": "TaskEval.is_successful"
        }
      }
    ],
    "runner_score_semantics": {
      "display_success_threshold": "agent_successful > 0.5",
      "done_gate": "task_successful if interaction_results.done else 0.0",
      "source_ref": {
        "ast_sha256": "6287c8b53ca1ea7313f4a186e885a27263c51c622f46921cbe7cc4433a04edaa",
        "end_line": 289,
        "file_sha256": "caf4d3a8765c914a2b978d119921cc4c062176e5a362c20c53905d4d0dbe083b",
        "path": "android_world/suite_utils.py",
        "snippet_sha256": "b24c573174d61b7642dd5dd746911d21c904d793e37582c91e5972a73d634062",
        "start_line": 223,
        "symbol": "suite_utils._run_task"
      },
      "task_raw_score": "task.is_successful(env)"
    },
    "source_bindings": [
      {
        "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sqlite_validators.py",
        "ast_sha256": "f2751ca3568b387056d6f4fdec053268e79d42a6e48ba54bce1e094203f0e07a",
        "end_line": 310,
        "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
        "owner_qualname": "AddMultipleRows.is_successful",
        "sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
        "snippet_sha256": "64097499692465a3a591ea95f000120ccced1957f73425ff2dc757e9ae1745c7",
        "start_line": 304
      },
      {
        "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "ast_sha256": "4ba02bae85e87232a171f4ab6decd0f081113181a5d2fcbd220a205512f58e16",
        "end_line": 180,
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.is_successful",
        "sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
        "snippet_sha256": "cb4c4fd2a9f4efa9fe8fb8328f459b54febf84903006338ae246acd0c445e098",
        "start_line": 166
      },
      {
        "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/suite_utils.py",
        "ast_sha256": "6287c8b53ca1ea7313f4a186e885a27263c51c622f46921cbe7cc4433a04edaa",
        "end_line": 289,
        "owner_module": "android_world.suite_utils",
        "owner_qualname": "suite_utils._run_task",
        "sha256": "caf4d3a8765c914a2b978d119921cc4c062176e5a362c20c53905d4d0dbe083b",
        "snippet_sha256": "b24c573174d61b7642dd5dd746911d21c904d793e37582c91e5972a73d634062",
        "start_line": 223
      }
    ]
  },
  "goal": {
    "authority": "runtime_goal_dispatched_by_android_world.suite_utils",
    "branches": [],
    "dispatch_phase": "after_initialize_task",
    "generation_semantics": {
      "computed_goal_semantics": null,
      "runtime_samples": [
        {
          "construction_goal": "In Simple Calendar Pro, create a calendar event for tomorrow at 13h with the title 'Workshop on Campaign' and the description 'We will explore team roles. Let's be punctual.'. The event should last for 15 mins.",
          "device_initialization_executed": false,
          "dispatch_goal_model": "In Simple Calendar Pro, create a calendar event for tomorrow at 13h with the title 'Workshop on Campaign' and the description 'We will explore team roles. Let's be punctual.'. The event should last for 15 mins.",
          "dispatch_goal_sha256": "be747e1fea3a2633f561ff9d68a37abf9698a679d6244d0ea009faf4492034fb",
          "params_at_dispatch_model": {
            "day": 16,
            "duration_mins": 15,
            "event_description": "We will explore team roles. Let's be punctual.",
            "event_title": "Workshop on Campaign",
            "hour": 13,
            "month": 10,
            "noise_row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize team roles.",
                  "end_ts": 1698561000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698559200,
                  "time_zone": "UTC",
                  "title": "Workshop on Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand business objectives.",
                  "end_ts": 1696907700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696906800,
                  "time_zone": "UTC",
                  "title": "Review session for Budget Planning",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize software updates. Snacks will be provided.",
                  "end_ts": 1697118300,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697115600,
                  "time_zone": "UTC",
                  "title": "Catch up on Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will explore upcoming project milestones. Let's be punctual.",
                  "end_ts": 1696814100,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696813200,
                  "time_zone": "UTC",
                  "title": "Meeting with Marketing",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will celebrate product launch.",
                  "end_ts": 1696808700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696806000,
                  "time_zone": "UTC",
                  "title": "Review session for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will review business objectives. Please bring relevant documents.",
                  "end_ts": 1698296400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698292800,
                  "time_zone": "UTC",
                  "title": "Meeting with Alice",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize client feedback.",
                  "end_ts": 1696959900,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696957200,
                  "time_zone": "UTC",
                  "title": "Review session for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about contract details. Snacks will be provided.",
                  "end_ts": 1698781500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698778800,
                  "time_zone": "UTC",
                  "title": "Appointment for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss team roles. Please bring relevant documents.",
                  "end_ts": 1696757400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696755600,
                  "time_zone": "UTC",
                  "title": "Call with Bob",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize business objectives. Snacks will be provided.",
                  "end_ts": 1696368600,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696366800,
                  "time_zone": "UTC",
                  "title": "Call with Alice",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about contract details. Looking forward to productive discussions.",
                  "end_ts": 1696869000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696867200,
                  "time_zone": "UTC",
                  "title": "Call with Marketing",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about marketing strategies. Snacks will be provided.",
                  "end_ts": 1697492700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697490000,
                  "time_zone": "UTC",
                  "title": "Meeting with the Team",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for marketing strategies.",
                  "end_ts": 1697884200,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697882400,
                  "time_zone": "UTC",
                  "title": "Call with Alice",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize annual budget.",
                  "end_ts": 1697089500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697086800,
                  "time_zone": "UTC",
                  "title": "Appointment for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will celebrate marketing strategies. Please bring relevant documents.",
                  "end_ts": 1696270500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696269600,
                  "time_zone": "UTC",
                  "title": "Meeting with Alice",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will celebrate annual budget.",
                  "end_ts": 1697080500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697079600,
                  "time_zone": "UTC",
                  "title": "Catch up on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize contract details.",
                  "end_ts": 1697436900,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697436000,
                  "time_zone": "UTC",
                  "title": "Review session for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for client feedback. Remember to confirm attendance.",
                  "end_ts": 1698394500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698393600,
                  "time_zone": "UTC",
                  "title": "Call with Alice",
                  "type": 0
                }
              }
            ],
            "row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will explore team roles. Let's be punctual.",
                  "end_ts": 1697462100,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697461200,
                  "time_zone": "UTC",
                  "title": "Workshop on Campaign",
                  "type": 0
                }
              }
            ],
            "seed": 0,
            "year": 2023
          },
          "params_before_goal": {
            "day": 16,
            "duration_mins": 15,
            "event_description": "We will explore team roles. Let's be punctual.",
            "event_title": "Workshop on Campaign",
            "hour": 13,
            "month": 10,
            "noise_row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize team roles.",
                  "end_ts": 1698561000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698559200,
                  "time_zone": "UTC",
                  "title": "Workshop on Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand business objectives.",
                  "end_ts": 1696907700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696906800,
                  "time_zone": "UTC",
                  "title": "Review session for Budget Planning",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize software updates. Snacks will be provided.",
                  "end_ts": 1697118300,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697115600,
                  "time_zone": "UTC",
                  "title": "Catch up on Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will explore upcoming project milestones. Let's be punctual.",
                  "end_ts": 1696814100,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696813200,
                  "time_zone": "UTC",
                  "title": "Meeting with Marketing",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will celebrate product launch.",
                  "end_ts": 1696808700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696806000,
                  "time_zone": "UTC",
                  "title": "Review session for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will review business objectives. Please bring relevant documents.",
                  "end_ts": 1698296400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698292800,
                  "time_zone": "UTC",
                  "title": "Meeting with Alice",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize client feedback.",
                  "end_ts": 1696959900,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696957200,
                  "time_zone": "UTC",
                  "title": "Review session for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about contract details. Snacks will be provided.",
                  "end_ts": 1698781500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698778800,
                  "time_zone": "UTC",
                  "title": "Appointment for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss team roles. Please bring relevant documents.",
                  "end_ts": 1696757400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696755600,
                  "time_zone": "UTC",
                  "title": "Call with Bob",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize business objectives. Snacks will be provided.",
                  "end_ts": 1696368600,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696366800,
                  "time_zone": "UTC",
                  "title": "Call with Alice",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about contract details. Looking forward to productive discussions.",
                  "end_ts": 1696869000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696867200,
                  "time_zone": "UTC",
                  "title": "Call with Marketing",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about marketing strategies. Snacks will be provided.",
                  "end_ts": 1697492700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697490000,
                  "time_zone": "UTC",
                  "title": "Meeting with the Team",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for marketing strategies.",
                  "end_ts": 1697884200,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697882400,
                  "time_zone": "UTC",
                  "title": "Call with Alice",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize annual budget.",
                  "end_ts": 1697089500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697086800,
                  "time_zone": "UTC",
                  "title": "Appointment for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will celebrate marketing strategies. Please bring relevant documents.",
                  "end_ts": 1696270500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696269600,
                  "time_zone": "UTC",
                  "title": "Meeting with Alice",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will celebrate annual budget.",
                  "end_ts": 1697080500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697079600,
                  "time_zone": "UTC",
                  "title": "Catch up on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize contract details.",
                  "end_ts": 1697436900,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697436000,
                  "time_zone": "UTC",
                  "title": "Review session for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for client feedback. Remember to confirm attendance.",
                  "end_ts": 1698394500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698393600,
                  "time_zone": "UTC",
                  "title": "Call with Alice",
                  "type": 0
                }
              }
            ],
            "row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will explore team roles. Let's be punctual.",
                  "end_ts": 1697462100,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697461200,
                  "time_zone": "UTC",
                  "title": "Workshop on Campaign",
                  "type": 0
                }
              }
            ],
            "seed": 0,
            "year": 2023
          },
          "pure_pre_dispatch_transforms": [],
          "reproducible_from_frozen_source_and_seed": true,
          "sample_kind": "fixed_seed",
          "suite_seed": 0
        },
        {
          "construction_goal": "In Simple Calendar Pro, create a calendar event for tomorrow at 18h with the title 'Workshop on Project X' and the description 'We will understand software updates. Looking forward to productive discussions.'. The event should last for 15 mins.",
          "device_initialization_executed": false,
          "dispatch_goal_model": "In Simple Calendar Pro, create a calendar event for tomorrow at 18h with the title 'Workshop on Project X' and the description 'We will understand software updates. Looking forward to productive discussions.'. The event should last for 15 mins.",
          "dispatch_goal_sha256": "4bcd3fa002d585b07fc321d2e720d975920d6d54bc11210030dca1fda84e5c46",
          "params_at_dispatch_model": {
            "day": 16,
            "duration_mins": 15,
            "event_description": "We will understand software updates. Looking forward to productive discussions.",
            "event_title": "Workshop on Project X",
            "hour": 18,
            "month": 10,
            "noise_row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about upcoming project milestones. Let's be punctual.",
                  "end_ts": 1696432500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696431600,
                  "time_zone": "UTC",
                  "title": "Appointment for Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize product launch. Looking forward to productive discussions.",
                  "end_ts": 1698755400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698753600,
                  "time_zone": "UTC",
                  "title": "Appointment for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will celebrate software updates. Please bring relevant documents.",
                  "end_ts": 1697615100,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697612400,
                  "time_zone": "UTC",
                  "title": "Call with Marketing",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for marketing strategies. Snacks will be provided.",
                  "end_ts": 1697303700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697302800,
                  "time_zone": "UTC",
                  "title": "Call with Marketing",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about software updates. Snacks will be provided.",
                  "end_ts": 1698672600,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698670800,
                  "time_zone": "UTC",
                  "title": "Workshop on Budget Planning",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will explore contract details.",
                  "end_ts": 1698458400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698454800,
                  "time_zone": "UTC",
                  "title": "Call with Marketing",
                  "type": 0
                }
              }
            ],
            "row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand software updates. Looking forward to productive discussions.",
                  "end_ts": 1697480100,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697479200,
                  "time_zone": "UTC",
                  "title": "Workshop on Project X",
                  "type": 0
                }
              }
            ],
            "seed": 1,
            "year": 2023
          },
          "params_before_goal": {
            "day": 16,
            "duration_mins": 15,
            "event_description": "We will understand software updates. Looking forward to productive discussions.",
            "event_title": "Workshop on Project X",
            "hour": 18,
            "month": 10,
            "noise_row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about upcoming project milestones. Let's be punctual.",
                  "end_ts": 1696432500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696431600,
                  "time_zone": "UTC",
                  "title": "Appointment for Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize product launch. Looking forward to productive discussions.",
                  "end_ts": 1698755400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698753600,
                  "time_zone": "UTC",
                  "title": "Appointment for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will celebrate software updates. Please bring relevant documents.",
                  "end_ts": 1697615100,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697612400,
                  "time_zone": "UTC",
                  "title": "Call with Marketing",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for marketing strategies. Snacks will be provided.",
                  "end_ts": 1697303700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697302800,
                  "time_zone": "UTC",
                  "title": "Call with Marketing",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about software updates. Snacks will be provided.",
                  "end_ts": 1698672600,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698670800,
                  "time_zone": "UTC",
                  "title": "Workshop on Budget Planning",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will explore contract details.",
                  "end_ts": 1698458400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698454800,
                  "time_zone": "UTC",
                  "title": "Call with Marketing",
                  "type": 0
                }
              }
            ],
            "row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand software updates. Looking forward to productive discussions.",
                  "end_ts": 1697480100,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697479200,
                  "time_zone": "UTC",
                  "title": "Workshop on Project X",
                  "type": 0
                }
              }
            ],
            "seed": 1,
            "year": 2023
          },
          "pure_pre_dispatch_transforms": [],
          "reproducible_from_frozen_source_and_seed": true,
          "sample_kind": "fixed_seed",
          "suite_seed": 1
        },
        {
          "construction_goal": "In Simple Calendar Pro, create a calendar event for tomorrow at 2h with the title 'Workshop on Annual Report' and the description 'We will prepare for team roles.'. The event should last for 15 mins.",
          "device_initialization_executed": false,
          "dispatch_goal_model": "In Simple Calendar Pro, create a calendar event for tomorrow at 2h with the title 'Workshop on Annual Report' and the description 'We will prepare for team roles.'. The event should last for 15 mins.",
          "dispatch_goal_sha256": "af623f7312b5202dbec6af9bface41e3ed3a82f703af4bf5763e364472d3b61e",
          "params_at_dispatch_model": {
            "day": 16,
            "duration_mins": 15,
            "event_description": "We will prepare for team roles.",
            "event_title": "Workshop on Annual Report",
            "hour": 2,
            "month": 10,
            "noise_row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize client feedback. Snacks will be provided.",
                  "end_ts": 1696271400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696269600,
                  "time_zone": "UTC",
                  "title": "Appointment for Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will review contract details. Snacks will be provided.",
                  "end_ts": 1696814100,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696813200,
                  "time_zone": "UTC",
                  "title": "Workshop on Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss annual budget. Remember to confirm attendance.",
                  "end_ts": 1696613400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696611600,
                  "time_zone": "UTC",
                  "title": "Call with Bob",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand contract details. Snacks will be provided.",
                  "end_ts": 1696524300,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696521600,
                  "time_zone": "UTC",
                  "title": "Catch up on Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand business objectives.",
                  "end_ts": 1697112000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697108400,
                  "time_zone": "UTC",
                  "title": "Call with HR",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand software updates. Snacks will be provided.",
                  "end_ts": 1697446800,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697443200,
                  "time_zone": "UTC",
                  "title": "Catch up on Budget Planning",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will review annual budget. Looking forward to productive discussions.",
                  "end_ts": 1698170400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698166800,
                  "time_zone": "UTC",
                  "title": "Appointment for Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will celebrate marketing strategies.",
                  "end_ts": 1698547500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698544800,
                  "time_zone": "UTC",
                  "title": "Review session for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will explore upcoming project milestones.",
                  "end_ts": 1698481800,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698480000,
                  "time_zone": "UTC",
                  "title": "Call with Alice",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss marketing strategies.",
                  "end_ts": 1697110200,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697108400,
                  "time_zone": "UTC",
                  "title": "Call with Marketing",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss client feedback. Remember to confirm attendance.",
                  "end_ts": 1698718500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698717600,
                  "time_zone": "UTC",
                  "title": "Meeting with Marketing",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will explore upcoming project milestones.",
                  "end_ts": 1698384600,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698382800,
                  "time_zone": "UTC",
                  "title": "Catch up on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for client feedback. Please bring relevant documents.",
                  "end_ts": 1696468500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696467600,
                  "time_zone": "UTC",
                  "title": "Workshop on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about annual budget. Remember to confirm attendance.",
                  "end_ts": 1696947300,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696946400,
                  "time_zone": "UTC",
                  "title": "Workshop on Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand annual budget. Looking forward to productive discussions.",
                  "end_ts": 1696369500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696366800,
                  "time_zone": "UTC",
                  "title": "Meeting with Alice",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for contract details.",
                  "end_ts": 1697538600,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697536800,
                  "time_zone": "UTC",
                  "title": "Workshop on Budget Planning",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for upcoming project milestones.",
                  "end_ts": 1698082200,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698080400,
                  "time_zone": "UTC",
                  "title": "Review session for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize upcoming project milestones.",
                  "end_ts": 1696569300,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696568400,
                  "time_zone": "UTC",
                  "title": "Appointment for Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize product launch. Let's be punctual.",
                  "end_ts": 1696806000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696802400,
                  "time_zone": "UTC",
                  "title": "Meeting with the Team",
                  "type": 0
                }
              }
            ],
            "row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for team roles.",
                  "end_ts": 1697422500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697421600,
                  "time_zone": "UTC",
                  "title": "Workshop on Annual Report",
                  "type": 0
                }
              }
            ],
            "seed": 2,
            "year": 2023
          },
          "params_before_goal": {
            "day": 16,
            "duration_mins": 15,
            "event_description": "We will prepare for team roles.",
            "event_title": "Workshop on Annual Report",
            "hour": 2,
            "month": 10,
            "noise_row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize client feedback. Snacks will be provided.",
                  "end_ts": 1696271400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696269600,
                  "time_zone": "UTC",
                  "title": "Appointment for Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will review contract details. Snacks will be provided.",
                  "end_ts": 1696814100,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696813200,
                  "time_zone": "UTC",
                  "title": "Workshop on Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss annual budget. Remember to confirm attendance.",
                  "end_ts": 1696613400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696611600,
                  "time_zone": "UTC",
                  "title": "Call with Bob",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand contract details. Snacks will be provided.",
                  "end_ts": 1696524300,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696521600,
                  "time_zone": "UTC",
                  "title": "Catch up on Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand business objectives.",
                  "end_ts": 1697112000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697108400,
                  "time_zone": "UTC",
                  "title": "Call with HR",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand software updates. Snacks will be provided.",
                  "end_ts": 1697446800,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697443200,
                  "time_zone": "UTC",
                  "title": "Catch up on Budget Planning",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will review annual budget. Looking forward to productive discussions.",
                  "end_ts": 1698170400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698166800,
                  "time_zone": "UTC",
                  "title": "Appointment for Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will celebrate marketing strategies.",
                  "end_ts": 1698547500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698544800,
                  "time_zone": "UTC",
                  "title": "Review session for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will explore upcoming project milestones.",
                  "end_ts": 1698481800,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698480000,
                  "time_zone": "UTC",
                  "title": "Call with Alice",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss marketing strategies.",
                  "end_ts": 1697110200,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697108400,
                  "time_zone": "UTC",
                  "title": "Call with Marketing",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss client feedback. Remember to confirm attendance.",
                  "end_ts": 1698718500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698717600,
                  "time_zone": "UTC",
                  "title": "Meeting with Marketing",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will explore upcoming project milestones.",
                  "end_ts": 1698384600,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698382800,
                  "time_zone": "UTC",
                  "title": "Catch up on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for client feedback. Please bring relevant documents.",
                  "end_ts": 1696468500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696467600,
                  "time_zone": "UTC",
                  "title": "Workshop on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about annual budget. Remember to confirm attendance.",
                  "end_ts": 1696947300,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696946400,
                  "time_zone": "UTC",
                  "title": "Workshop on Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand annual budget. Looking forward to productive discussions.",
                  "end_ts": 1696369500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696366800,
                  "time_zone": "UTC",
                  "title": "Meeting with Alice",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for contract details.",
                  "end_ts": 1697538600,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697536800,
                  "time_zone": "UTC",
                  "title": "Workshop on Budget Planning",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for upcoming project milestones.",
                  "end_ts": 1698082200,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698080400,
                  "time_zone": "UTC",
                  "title": "Review session for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize upcoming project milestones.",
                  "end_ts": 1696569300,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696568400,
                  "time_zone": "UTC",
                  "title": "Appointment for Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize product launch. Let's be punctual.",
                  "end_ts": 1696806000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696802400,
                  "time_zone": "UTC",
                  "title": "Meeting with the Team",
                  "type": 0
                }
              }
            ],
            "row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for team roles.",
                  "end_ts": 1697422500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697421600,
                  "time_zone": "UTC",
                  "title": "Workshop on Annual Report",
                  "type": 0
                }
              }
            ],
            "seed": 2,
            "year": 2023
          },
          "pure_pre_dispatch_transforms": [],
          "reproducible_from_frozen_source_and_seed": true,
          "sample_kind": "fixed_seed",
          "suite_seed": 2
        },
        {
          "construction_goal": "In Simple Calendar Pro, create a calendar event for tomorrow at 18h with the title 'Workshop on Campaign' and the description 'We will strategize about marketing strategies.'. The event should last for 30 mins.",
          "device_initialization_executed": false,
          "dispatch_goal_model": "In Simple Calendar Pro, create a calendar event for tomorrow at 18h with the title 'Workshop on Campaign' and the description 'We will strategize about marketing strategies.'. The event should last for 30 mins.",
          "dispatch_goal_sha256": "109ddf5fe2ec40faef794e4767560e4b04f629ffbf63d720fbe2e83326aa4d25",
          "params_at_dispatch_model": {
            "day": 16,
            "duration_mins": 30,
            "event_description": "We will strategize about marketing strategies.",
            "event_title": "Workshop on Campaign",
            "hour": 18,
            "month": 10,
            "noise_row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand business objectives. Looking forward to productive discussions.",
                  "end_ts": 1696872600,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696870800,
                  "time_zone": "UTC",
                  "title": "Call with Marketing",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize contract details.",
                  "end_ts": 1697862600,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697860800,
                  "time_zone": "UTC",
                  "title": "Review session for Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for upcoming project milestones. Looking forward to productive discussions.",
                  "end_ts": 1697941800,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697940000,
                  "time_zone": "UTC",
                  "title": "Catch up on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will explore software updates.",
                  "end_ts": 1697846400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697842800,
                  "time_zone": "UTC",
                  "title": "Review session for Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand product launch. Looking forward to productive discussions.",
                  "end_ts": 1698578100,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698577200,
                  "time_zone": "UTC",
                  "title": "Meeting with Bob",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about client feedback. Snacks will be provided.",
                  "end_ts": 1698266700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698264000,
                  "time_zone": "UTC",
                  "title": "Appointment for Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will review business objectives.",
                  "end_ts": 1696760100,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696759200,
                  "time_zone": "UTC",
                  "title": "Workshop on Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for marketing strategies.",
                  "end_ts": 1698093000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698091200,
                  "time_zone": "UTC",
                  "title": "Review session for Budget Planning",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize contract details.",
                  "end_ts": 1697490000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697486400,
                  "time_zone": "UTC",
                  "title": "Meeting with the Team",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss upcoming project milestones. Snacks will be provided.",
                  "end_ts": 1696154400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696150800,
                  "time_zone": "UTC",
                  "title": "Appointment for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss team roles.",
                  "end_ts": 1697046300,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697043600,
                  "time_zone": "UTC",
                  "title": "Catch up on Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for team roles.",
                  "end_ts": 1696302900,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696302000,
                  "time_zone": "UTC",
                  "title": "Call with HR",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will plan contract details. Looking forward to productive discussions.",
                  "end_ts": 1698025500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698022800,
                  "time_zone": "UTC",
                  "title": "Workshop on Budget Planning",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about business objectives. Looking forward to productive discussions.",
                  "end_ts": 1698512400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698508800,
                  "time_zone": "UTC",
                  "title": "Review session for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss contract details.",
                  "end_ts": 1696986000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696982400,
                  "time_zone": "UTC",
                  "title": "Catch up on Budget Planning",
                  "type": 0
                }
              }
            ],
            "row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about marketing strategies.",
                  "end_ts": 1697481000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697479200,
                  "time_zone": "UTC",
                  "title": "Workshop on Campaign",
                  "type": 0
                }
              }
            ],
            "seed": 3,
            "year": 2023
          },
          "params_before_goal": {
            "day": 16,
            "duration_mins": 30,
            "event_description": "We will strategize about marketing strategies.",
            "event_title": "Workshop on Campaign",
            "hour": 18,
            "month": 10,
            "noise_row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand business objectives. Looking forward to productive discussions.",
                  "end_ts": 1696872600,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696870800,
                  "time_zone": "UTC",
                  "title": "Call with Marketing",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize contract details.",
                  "end_ts": 1697862600,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697860800,
                  "time_zone": "UTC",
                  "title": "Review session for Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for upcoming project milestones. Looking forward to productive discussions.",
                  "end_ts": 1697941800,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697940000,
                  "time_zone": "UTC",
                  "title": "Catch up on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will explore software updates.",
                  "end_ts": 1697846400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697842800,
                  "time_zone": "UTC",
                  "title": "Review session for Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand product launch. Looking forward to productive discussions.",
                  "end_ts": 1698578100,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698577200,
                  "time_zone": "UTC",
                  "title": "Meeting with Bob",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about client feedback. Snacks will be provided.",
                  "end_ts": 1698266700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698264000,
                  "time_zone": "UTC",
                  "title": "Appointment for Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will review business objectives.",
                  "end_ts": 1696760100,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696759200,
                  "time_zone": "UTC",
                  "title": "Workshop on Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for marketing strategies.",
                  "end_ts": 1698093000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698091200,
                  "time_zone": "UTC",
                  "title": "Review session for Budget Planning",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize contract details.",
                  "end_ts": 1697490000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697486400,
                  "time_zone": "UTC",
                  "title": "Meeting with the Team",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss upcoming project milestones. Snacks will be provided.",
                  "end_ts": 1696154400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696150800,
                  "time_zone": "UTC",
                  "title": "Appointment for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss team roles.",
                  "end_ts": 1697046300,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697043600,
                  "time_zone": "UTC",
                  "title": "Catch up on Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for team roles.",
                  "end_ts": 1696302900,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696302000,
                  "time_zone": "UTC",
                  "title": "Call with HR",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will plan contract details. Looking forward to productive discussions.",
                  "end_ts": 1698025500,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698022800,
                  "time_zone": "UTC",
                  "title": "Workshop on Budget Planning",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about business objectives. Looking forward to productive discussions.",
                  "end_ts": 1698512400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698508800,
                  "time_zone": "UTC",
                  "title": "Review session for Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss contract details.",
                  "end_ts": 1696986000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696982400,
                  "time_zone": "UTC",
                  "title": "Catch up on Budget Planning",
                  "type": 0
                }
              }
            ],
            "row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about marketing strategies.",
                  "end_ts": 1697481000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697479200,
                  "time_zone": "UTC",
                  "title": "Workshop on Campaign",
                  "type": 0
                }
              }
            ],
            "seed": 3,
            "year": 2023
          },
          "pure_pre_dispatch_transforms": [],
          "reproducible_from_frozen_source_and_seed": true,
          "sample_kind": "fixed_seed",
          "suite_seed": 3
        },
        {
          "construction_goal": "In Simple Calendar Pro, create a calendar event for tomorrow at 9h with the title 'Review session for Campaign' and the description 'We will understand annual budget.'. The event should last for 15 mins.",
          "device_initialization_executed": false,
          "dispatch_goal_model": "In Simple Calendar Pro, create a calendar event for tomorrow at 9h with the title 'Review session for Campaign' and the description 'We will understand annual budget.'. The event should last for 15 mins.",
          "dispatch_goal_sha256": "f9fbd6338ad3a1f91823d22be90179153e1dcf4369e2b1afe00a271b667d56b3",
          "params_at_dispatch_model": {
            "day": 16,
            "duration_mins": 15,
            "event_description": "We will understand annual budget.",
            "event_title": "Review session for Campaign",
            "hour": 9,
            "month": 10,
            "noise_row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize business objectives. Let's be punctual.",
                  "end_ts": 1696164300,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696161600,
                  "time_zone": "UTC",
                  "title": "Meeting with Bob",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss team roles. Remember to confirm attendance.",
                  "end_ts": 1698210900,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698210000,
                  "time_zone": "UTC",
                  "title": "Workshop on Annual Report",
                  "type": 0
                }
              }
            ],
            "row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand annual budget.",
                  "end_ts": 1697447700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697446800,
                  "time_zone": "UTC",
                  "title": "Review session for Campaign",
                  "type": 0
                }
              }
            ],
            "seed": 4,
            "year": 2023
          },
          "params_before_goal": {
            "day": 16,
            "duration_mins": 15,
            "event_description": "We will understand annual budget.",
            "event_title": "Review session for Campaign",
            "hour": 9,
            "month": 10,
            "noise_row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize business objectives. Let's be punctual.",
                  "end_ts": 1696164300,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696161600,
                  "time_zone": "UTC",
                  "title": "Meeting with Bob",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss team roles. Remember to confirm attendance.",
                  "end_ts": 1698210900,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698210000,
                  "time_zone": "UTC",
                  "title": "Workshop on Annual Report",
                  "type": 0
                }
              }
            ],
            "row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand annual budget.",
                  "end_ts": 1697447700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697446800,
                  "time_zone": "UTC",
                  "title": "Review session for Campaign",
                  "type": 0
                }
              }
            ],
            "seed": 4,
            "year": 2023
          },
          "pure_pre_dispatch_transforms": [],
          "reproducible_from_frozen_source_and_seed": true,
          "sample_kind": "fixed_seed",
          "suite_seed": 4
        },
        {
          "construction_goal": "In Simple Calendar Pro, create a calendar event for tomorrow at 23h with the title 'Review session for Project X' and the description 'We will understand product launch.'. The event should last for 45 mins.",
          "device_initialization_executed": false,
          "dispatch_goal_model": "In Simple Calendar Pro, create a calendar event for tomorrow at 23h with the title 'Review session for Project X' and the description 'We will understand product launch.'. The event should last for 45 mins.",
          "dispatch_goal_sha256": "cc8ce2eaba8dfab6fb6ba2c24438f73c56a89432edc027ec2ee4c970f529060e",
          "params_at_dispatch_model": {
            "day": 16,
            "duration_mins": 45,
            "event_description": "We will understand product launch.",
            "event_title": "Review session for Project X",
            "hour": 23,
            "month": 10,
            "noise_row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize marketing strategies.",
                  "end_ts": 1696420800,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696417200,
                  "time_zone": "UTC",
                  "title": "Call with HR",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will plan contract details.",
                  "end_ts": 1696203000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696201200,
                  "time_zone": "UTC",
                  "title": "Appointment for Budget Planning",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will plan annual budget.",
                  "end_ts": 1698201000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698199200,
                  "time_zone": "UTC",
                  "title": "Catch up on Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will plan team roles. Remember to confirm attendance.",
                  "end_ts": 1698453000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698451200,
                  "time_zone": "UTC",
                  "title": "Call with Bob",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will celebrate contract details. Please bring relevant documents.",
                  "end_ts": 1697664600,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697662800,
                  "time_zone": "UTC",
                  "title": "Call with Marketing",
                  "type": 0
                }
              }
            ],
            "row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand product launch.",
                  "end_ts": 1697499900,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697497200,
                  "time_zone": "UTC",
                  "title": "Review session for Project X",
                  "type": 0
                }
              }
            ],
            "seed": 5,
            "year": 2023
          },
          "params_before_goal": {
            "day": 16,
            "duration_mins": 45,
            "event_description": "We will understand product launch.",
            "event_title": "Review session for Project X",
            "hour": 23,
            "month": 10,
            "noise_row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize marketing strategies.",
                  "end_ts": 1696420800,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696417200,
                  "time_zone": "UTC",
                  "title": "Call with HR",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will plan contract details.",
                  "end_ts": 1696203000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696201200,
                  "time_zone": "UTC",
                  "title": "Appointment for Budget Planning",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will plan annual budget.",
                  "end_ts": 1698201000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698199200,
                  "time_zone": "UTC",
                  "title": "Catch up on Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will plan team roles. Remember to confirm attendance.",
                  "end_ts": 1698453000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698451200,
                  "time_zone": "UTC",
                  "title": "Call with Bob",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will celebrate contract details. Please bring relevant documents.",
                  "end_ts": 1697664600,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697662800,
                  "time_zone": "UTC",
                  "title": "Call with Marketing",
                  "type": 0
                }
              }
            ],
            "row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand product launch.",
                  "end_ts": 1697499900,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697497200,
                  "time_zone": "UTC",
                  "title": "Review session for Project X",
                  "type": 0
                }
              }
            ],
            "seed": 5,
            "year": 2023
          },
          "pure_pre_dispatch_transforms": [],
          "reproducible_from_frozen_source_and_seed": true,
          "sample_kind": "fixed_seed",
          "suite_seed": 5
        },
        {
          "construction_goal": "In Simple Calendar Pro, create a calendar event for tomorrow at 4h with the title 'Review session for Project X' and the description 'We will finalize business objectives.'. The event should last for 60 mins.",
          "device_initialization_executed": false,
          "dispatch_goal_model": "In Simple Calendar Pro, create a calendar event for tomorrow at 4h with the title 'Review session for Project X' and the description 'We will finalize business objectives.'. The event should last for 60 mins.",
          "dispatch_goal_sha256": "da7a98425cb4029bae7909c37d8e5e27e00ae7abe45bc179ab89ec6dc045de0e",
          "params_at_dispatch_model": {
            "day": 16,
            "duration_mins": 60,
            "event_description": "We will finalize business objectives.",
            "event_title": "Review session for Project X",
            "hour": 4,
            "month": 10,
            "noise_row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will explore contract details.",
                  "end_ts": 1697679000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697677200,
                  "time_zone": "UTC",
                  "title": "Meeting with Alice",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize product launch.",
                  "end_ts": 1696734000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696730400,
                  "time_zone": "UTC",
                  "title": "Meeting with Dr. Smith",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss business objectives.",
                  "end_ts": 1697742000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697738400,
                  "time_zone": "UTC",
                  "title": "Meeting with Bob",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about team roles.",
                  "end_ts": 1696944600,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696942800,
                  "time_zone": "UTC",
                  "title": "Catch up on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize marketing strategies.",
                  "end_ts": 1696444200,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696442400,
                  "time_zone": "UTC",
                  "title": "Workshop on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will review software updates. Let's be punctual.",
                  "end_ts": 1697785200,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697781600,
                  "time_zone": "UTC",
                  "title": "Review session for Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize team roles. Let's be punctual.",
                  "end_ts": 1696923000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696921200,
                  "time_zone": "UTC",
                  "title": "Review session for Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize business objectives. Remember to confirm attendance.",
                  "end_ts": 1698158700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698156000,
                  "time_zone": "UTC",
                  "title": "Catch up on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss marketing strategies. Let's be punctual.",
                  "end_ts": 1698229800,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698228000,
                  "time_zone": "UTC",
                  "title": "Appointment for Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize marketing strategies. Looking forward to productive discussions.",
                  "end_ts": 1698062400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698058800,
                  "time_zone": "UTC",
                  "title": "Catch up on Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for software updates. Looking forward to productive discussions.",
                  "end_ts": 1698095700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698094800,
                  "time_zone": "UTC",
                  "title": "Meeting with Marketing",
                  "type": 0
                }
              }
            ],
            "row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize business objectives.",
                  "end_ts": 1697432400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697428800,
                  "time_zone": "UTC",
                  "title": "Review session for Project X",
                  "type": 0
                }
              }
            ],
            "seed": 7,
            "year": 2023
          },
          "params_before_goal": {
            "day": 16,
            "duration_mins": 60,
            "event_description": "We will finalize business objectives.",
            "event_title": "Review session for Project X",
            "hour": 4,
            "month": 10,
            "noise_row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will explore contract details.",
                  "end_ts": 1697679000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697677200,
                  "time_zone": "UTC",
                  "title": "Meeting with Alice",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize product launch.",
                  "end_ts": 1696734000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696730400,
                  "time_zone": "UTC",
                  "title": "Meeting with Dr. Smith",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss business objectives.",
                  "end_ts": 1697742000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697738400,
                  "time_zone": "UTC",
                  "title": "Meeting with Bob",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will strategize about team roles.",
                  "end_ts": 1696944600,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696942800,
                  "time_zone": "UTC",
                  "title": "Catch up on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize marketing strategies.",
                  "end_ts": 1696444200,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696442400,
                  "time_zone": "UTC",
                  "title": "Workshop on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will review software updates. Let's be punctual.",
                  "end_ts": 1697785200,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697781600,
                  "time_zone": "UTC",
                  "title": "Review session for Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize team roles. Let's be punctual.",
                  "end_ts": 1696923000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696921200,
                  "time_zone": "UTC",
                  "title": "Review session for Annual Report",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize business objectives. Remember to confirm attendance.",
                  "end_ts": 1698158700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698156000,
                  "time_zone": "UTC",
                  "title": "Catch up on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will discuss marketing strategies. Let's be punctual.",
                  "end_ts": 1698229800,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698228000,
                  "time_zone": "UTC",
                  "title": "Appointment for Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize marketing strategies. Looking forward to productive discussions.",
                  "end_ts": 1698062400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698058800,
                  "time_zone": "UTC",
                  "title": "Catch up on Campaign",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for software updates. Looking forward to productive discussions.",
                  "end_ts": 1698095700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698094800,
                  "time_zone": "UTC",
                  "title": "Meeting with Marketing",
                  "type": 0
                }
              }
            ],
            "row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will finalize business objectives.",
                  "end_ts": 1697432400,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697428800,
                  "time_zone": "UTC",
                  "title": "Review session for Project X",
                  "type": 0
                }
              }
            ],
            "seed": 7,
            "year": 2023
          },
          "pure_pre_dispatch_transforms": [],
          "reproducible_from_frozen_source_and_seed": true,
          "sample_kind": "fixed_seed",
          "suite_seed": 7
        },
        {
          "construction_goal": "In Simple Calendar Pro, create a calendar event for tomorrow at 17h with the title 'Appointment for Annual Report' and the description 'We will plan business objectives. Snacks will be provided.'. The event should last for 60 mins.",
          "device_initialization_executed": false,
          "dispatch_goal_model": "In Simple Calendar Pro, create a calendar event for tomorrow at 17h with the title 'Appointment for Annual Report' and the description 'We will plan business objectives. Snacks will be provided.'. The event should last for 60 mins.",
          "dispatch_goal_sha256": "078c174834e235a084200a7f6aefe3754b208638abbf6573884c4143c72371a5",
          "params_at_dispatch_model": {
            "day": 16,
            "duration_mins": 60,
            "event_description": "We will plan business objectives. Snacks will be provided.",
            "event_title": "Appointment for Annual Report",
            "hour": 17,
            "month": 10,
            "noise_row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize upcoming project milestones. Looking forward to productive discussions.",
                  "end_ts": 1696430700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696428000,
                  "time_zone": "UTC",
                  "title": "Call with Alice",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize marketing strategies.",
                  "end_ts": 1697931000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697929200,
                  "time_zone": "UTC",
                  "title": "Catch up on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand client feedback. Snacks will be provided.",
                  "end_ts": 1696228200,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696226400,
                  "time_zone": "UTC",
                  "title": "Catch up on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand upcoming project milestones.",
                  "end_ts": 1698388200,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698386400,
                  "time_zone": "UTC",
                  "title": "Review session for Budget Planning",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for client feedback.",
                  "end_ts": 1697402700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697400000,
                  "time_zone": "UTC",
                  "title": "Appointment for Project X",
                  "type": 0
                }
              }
            ],
            "row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will plan business objectives. Snacks will be provided.",
                  "end_ts": 1697479200,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697475600,
                  "time_zone": "UTC",
                  "title": "Appointment for Annual Report",
                  "type": 0
                }
              }
            ],
            "seed": 11,
            "year": 2023
          },
          "params_before_goal": {
            "day": 16,
            "duration_mins": 60,
            "event_description": "We will plan business objectives. Snacks will be provided.",
            "event_title": "Appointment for Annual Report",
            "hour": 17,
            "month": 10,
            "noise_row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize upcoming project milestones. Looking forward to productive discussions.",
                  "end_ts": 1696430700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696428000,
                  "time_zone": "UTC",
                  "title": "Call with Alice",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will organize marketing strategies.",
                  "end_ts": 1697931000,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697929200,
                  "time_zone": "UTC",
                  "title": "Catch up on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand client feedback. Snacks will be provided.",
                  "end_ts": 1696228200,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1696226400,
                  "time_zone": "UTC",
                  "title": "Catch up on Project X",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will understand upcoming project milestones.",
                  "end_ts": 1698388200,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1698386400,
                  "time_zone": "UTC",
                  "title": "Review session for Budget Planning",
                  "type": 0
                }
              },
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will prepare for client feedback.",
                  "end_ts": 1697402700,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697400000,
                  "time_zone": "UTC",
                  "title": "Appointment for Project X",
                  "type": 0
                }
              }
            ],
            "row_objects": [
              {
                "$type": "android_world.task_evals.utils.sqlite_schema_utils.CalendarEvent",
                "fields": {
                  "attendees": "",
                  "availability": 0,
                  "color": 0,
                  "description": "We will plan business objectives. Snacks will be provided.",
                  "end_ts": 1697479200,
                  "event_type": 1,
                  "flags": 0,
                  "id": -1,
                  "import_id": "",
                  "last_updated": 0,
                  "location": "",
                  "parent_id": 0,
                  "reminder_1_minutes": -1,
                  "reminder_1_type": 0,
                  "reminder_2_minutes": -1,
                  "reminder_2_type": 0,
                  "reminder_3_minutes": -1,
                  "reminder_3_type": 0,
                  "repeat_interval": 0,
                  "repeat_limit": 0,
                  "repeat_rule": 0,
                  "repetition_exceptions": "[]",
                  "source": "imported-ics",
                  "start_ts": 1697475600,
                  "time_zone": "UTC",
                  "title": "Appointment for Annual Report",
                  "type": 0
                }
              }
            ],
            "seed": 11,
            "year": 2023
          },
          "pure_pre_dispatch_transforms": [],
          "reproducible_from_frozen_source_and_seed": true,
          "sample_kind": "fixed_seed",
          "suite_seed": 11
        }
      ],
      "samples_are_examples_not_generic_templates": true,
      "templates": [
        {
          "placeholders": [
            "duration_mins",
            "event_description",
            "event_title",
            "hour"
          ],
          "template": "In Simple Calendar Pro, create a calendar event for tomorrow at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins.",
          "variant_id": "default"
        }
      ]
    },
    "representation_kind": "format_template",
    "source_bindings": [
      {
        "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "ast_sha256": "25a7b24a351ed012c02d1854080b239788b8650c232f75a55874f431f46d375a",
        "end_line": 109,
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.goal",
        "sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
        "snippet_sha256": "0ab83521d040a0a8449aed8286bde0da755f1f2ab5361cba898a64c0d5033f91",
        "start_line": 106
      },
      {
        "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/calendar/calendar.py",
        "ast_sha256": "bd140103ca3d1023f79dda89955a07e058c56425856513e6f9d8eeda7e9d2356",
        "end_line": 199,
        "owner_module": "android_world.task_evals.single.calendar.calendar",
        "owner_qualname": "SimpleCalendarAddOneEventTomorrow.template",
        "sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
        "snippet_sha256": "1a63eb7a5713125134623149f3d89dc1c4086215f9152de05b16d4aaca13a041",
        "start_line": 182
      }
    ],
    "template": "In Simple Calendar Pro, create a calendar event for tomorrow at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins."
  },
  "group": "official100",
  "initialize_task": {
    "device_execution_performed_during_extraction": false,
    "method_chain": [
      {
        "branch_node_count": 0,
        "direct_calls": [
          "self.list_rows",
          "super",
          "super.initialize_task"
        ],
        "direct_parameter_reads": [],
        "owner_class": "AddMultipleRows",
        "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
        "source_ref": {
          "ast_sha256": "eea233290c4a63c1a86fd0539bc8d92335bcdf7b2673badda11c990be2979db5",
          "end_line": 283,
          "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
          "path": "android_world/task_evals/common_validators/sqlite_validators.py",
          "snippet_sha256": "57b20e4b7ef5cbeb3d74750a51770e8f57e2b74d5d33310c8bcabccd5b2f6654",
          "start_line": 280,
          "symbol": "AddMultipleRows.initialize_task"
        }
      },
      {
        "branch_node_count": 1,
        "direct_calls": [
          "self._clear_db",
          "self.add_rows",
          "super",
          "super.initialize_task"
        ],
        "direct_parameter_reads": [],
        "owner_class": "SQLiteApp",
        "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
        "source_ref": {
          "ast_sha256": "8ec142f52bd60efe8bf0eb5325d739d2511462452523437f3f96f9604aa5f8d1",
          "end_line": 263,
          "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
          "path": "android_world/task_evals/common_validators/sqlite_validators.py",
          "snippet_sha256": "97320f8846ae2e43d66bdcaedf01c6c896901a39582cd8890390fcde9cbf4710",
          "start_line": 257,
          "symbol": "SQLiteApp.initialize_task"
        }
      },
      {
        "branch_node_count": 2,
        "direct_calls": [
          "RuntimeError",
          "logging.info",
          "random.seed",
          "self._initialize_apps",
          "self.initialize_device_time",
          "self.params.get"
        ],
        "direct_parameter_reads": [
          "seed"
        ],
        "owner_class": "TaskEval",
        "owner_module": "android_world.task_evals.task_eval",
        "source_ref": {
          "ast_sha256": "789c520bbfefb2cf815434042709e7d9d74585ebb19c2598d02dfe9c38769b1c",
          "end_line": 157,
          "file_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
          "path": "android_world/task_evals/task_eval.py",
          "snippet_sha256": "51c8fe9ebb14bc1362b24c3c53691dc666b9eaf949e8e6dc7251472e335f8c47",
          "start_line": 142,
          "symbol": "TaskEval.initialize_task"
        }
      }
    ],
    "source_bindings": [
      {
        "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sqlite_validators.py",
        "ast_sha256": "eea233290c4a63c1a86fd0539bc8d92335bcdf7b2673badda11c990be2979db5",
        "end_line": 283,
        "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
        "owner_qualname": "AddMultipleRows.initialize_task",
        "sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
        "snippet_sha256": "57b20e4b7ef5cbeb3d74750a51770e8f57e2b74d5d33310c8bcabccd5b2f6654",
        "start_line": 280
      },
      {
        "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sqlite_validators.py",
        "ast_sha256": "8ec142f52bd60efe8bf0eb5325d739d2511462452523437f3f96f9604aa5f8d1",
        "end_line": 263,
        "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
        "owner_qualname": "SQLiteApp.initialize_task",
        "sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
        "snippet_sha256": "97320f8846ae2e43d66bdcaedf01c6c896901a39582cd8890390fcde9cbf4710",
        "start_line": 257
      },
      {
        "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "ast_sha256": "789c520bbfefb2cf815434042709e7d9d74585ebb19c2598d02dfe9c38769b1c",
        "end_line": 157,
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
        "snippet_sha256": "51c8fe9ebb14bc1362b24c3c53691dc666b9eaf949e8e6dc7251472e335f8c47",
        "start_line": 142
      }
    ]
  },
  "is_successful": {
    "branches": [],
    "live_evaluator_execution_performed": false,
    "method_chain": [
      {
        "branch_node_count": 1,
        "direct_calls": [
          "self.list_rows",
          "self.validate_addition_integrity"
        ],
        "direct_parameter_reads": [],
        "owner_class": "AddMultipleRows",
        "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
        "source_ref": {
          "ast_sha256": "f2751ca3568b387056d6f4fdec053268e79d42a6e48ba54bce1e094203f0e07a",
          "end_line": 310,
          "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
          "path": "android_world/task_evals/common_validators/sqlite_validators.py",
          "snippet_sha256": "64097499692465a3a591ea95f000120ccced1957f73425ff2dc757e9ae1745c7",
          "start_line": 304,
          "symbol": "AddMultipleRows.is_successful"
        }
      },
      {
        "branch_node_count": 0,
        "direct_calls": [
          "self._check_is_initialized"
        ],
        "direct_parameter_reads": [],
        "owner_class": "TaskEval",
        "owner_module": "android_world.task_evals.task_eval",
        "source_ref": {
          "ast_sha256": "4ba02bae85e87232a171f4ab6decd0f081113181a5d2fcbd220a205512f58e16",
          "end_line": 180,
          "file_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
          "path": "android_world/task_evals/task_eval.py",
          "snippet_sha256": "cb4c4fd2a9f4efa9fe8fb8328f459b54febf84903006338ae246acd0c445e098",
          "start_line": 166,
          "symbol": "TaskEval.is_successful"
        }
      }
    ],
    "source_bindings": [
      {
        "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sqlite_validators.py",
        "ast_sha256": "f2751ca3568b387056d6f4fdec053268e79d42a6e48ba54bce1e094203f0e07a",
        "end_line": 310,
        "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
        "owner_qualname": "AddMultipleRows.is_successful",
        "sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
        "snippet_sha256": "64097499692465a3a591ea95f000120ccced1957f73425ff2dc757e9ae1745c7",
        "start_line": 304
      },
      {
        "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "ast_sha256": "4ba02bae85e87232a171f4ab6decd0f081113181a5d2fcbd220a205512f58e16",
        "end_line": 180,
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.is_successful",
        "sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
        "snippet_sha256": "cb4c4fd2a9f4efa9fe8fb8328f459b54febf84903006338ae246acd0c445e098",
        "start_line": 166
      },
      {
        "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/suite_utils.py",
        "ast_sha256": "6287c8b53ca1ea7313f4a186e885a27263c51c622f46921cbe7cc4433a04edaa",
        "end_line": 289,
        "owner_module": "android_world.suite_utils",
        "owner_qualname": "suite_utils._run_task",
        "sha256": "caf4d3a8765c914a2b978d119921cc4c062176e5a362c20c53905d4d0dbe083b",
        "snippet_sha256": "b24c573174d61b7642dd5dd746911d21c904d793e37582c91e5972a73d634062",
        "start_line": 223
      }
    ]
  },
  "metadata_comparison": {
    "canonical_templates": [
      "In Simple Calendar Pro, create a calendar event for tomorrow at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins."
    ],
    "comparison_is_semantic_proof": true,
    "differences": [],
    "fixed_seed_sample_shape_matches": [
      true,
      true,
      true,
      true,
      true,
      true,
      true,
      true
    ],
    "has_difference": false,
    "matches_runtime": true,
    "metadata_placeholders": [
      "duration_mins",
      "event_description",
      "event_title",
      "hour"
    ],
    "metadata_template": "In Simple Calendar Pro, create a calendar event for tomorrow at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins.",
    "status": "exact"
  },
  "metadata_conflicts": [],
  "raw_metadata": {
    "semantic_role": "descriptive_non_authoritative",
    "source_ref": {
      "file_sha256": "fd3cf23ebb26e461a961dd60ff3f011d7e6ec78c992c10babbbdb86f9dd591e1",
      "json_pointer": "/66",
      "line_hint": 540,
      "path": "android_world/task_metadata.json",
      "value_sha256": "6012b8c38e13c8745dd431b7c2276cb3760f1f910e022fb15a2226a45825a41a"
    },
    "template_placeholders": [
      "duration_mins",
      "event_description",
      "event_title",
      "hour"
    ],
    "value": {
      "difficulty": "easy",
      "optimal_steps": "13",
      "tags": [
        "data_entry",
        "parameterized"
      ],
      "task_name": "SimpleCalendarAddOneEventTomorrow",
      "task_template": "In Simple Calendar Pro, create a calendar event for tomorrow at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins."
    }
  },
  "raw_semantic_record_sha256": "cd9d23a46ac17c00dde0f31c63ad4ae19e6d7426541b3255970505392f27d3a6",
  "readiness": {
    "canonical_runtime_resolution_applied": true,
    "canonical_source_complete": true,
    "draft_blockers": [],
    "goal_samples_reproducible": true,
    "live_run_blockers": [
      "device/emulator execution is outside this static extractor"
    ],
    "live_run_ready": false,
    "live_runtime_verified": false,
    "metadata_has_open_material_conflict": false,
    "metadata_has_open_unresolved_conflict": false,
    "metadata_is_excluded_from_canonical_goal_when_conflicting": true,
    "static_draft_ready": true,
    "static_semantic_record_complete": true
  },
  "record_sha256": "6f3bf04dc0a5669ad3a4c464332f4402c3eee076dedfd08806c6f3f3b028de4c",
  "runtime_reported_class": "SimpleCalendarAddOneEventTomorrow",
  "runtime_reported_module": "android_world.task_evals.single.calendar.calendar",
  "schema": {
    "observed_parameter_keys": [
      "day",
      "duration_mins",
      "event_description",
      "event_title",
      "hour",
      "month",
      "noise_row_objects",
      "row_objects",
      "seed",
      "year"
    ],
    "observed_parameter_types": {
      "day": [
        "builtins.int"
      ],
      "duration_mins": [
        "builtins.int"
      ],
      "event_description": [
        "builtins.str"
      ],
      "event_title": [
        "builtins.str"
      ],
      "hour": [
        "builtins.int"
      ],
      "month": [
        "builtins.int"
      ],
      "noise_row_objects": [
        "builtins.list"
      ],
      "row_objects": [
        "builtins.list"
      ],
      "seed": [
        "builtins.int"
      ],
      "year": [
        "builtins.int"
      ]
    },
    "runner_injected_parameters": [
      "seed"
    ],
    "schema_completeness": "empty",
    "source_bindings": [
      {
        "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/calendar/calendar.py",
        "ast_sha256": "b37475fef92212b5ad9abc69fb854b2f09e4ca45c6849c9e1da584950ce94ac5",
        "end_line": 82,
        "owner_module": "android_world.task_evals.single.calendar.calendar",
        "owner_qualname": "_SimpleCalendar.schema",
        "sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
        "snippet_sha256": "24705bc4830c48802dba65136f58cf31f4c8411d4b0e605e826c48941bab03ca",
        "start_line": 61
      },
      {
        "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/calendar/calendar.py",
        "ast_sha256": "f25c295d8b655d79d805256776455a9ea16eaa7e4a5da2d8467d039ca3afa60c",
        "end_line": 139,
        "owner_module": "android_world.task_evals.single.calendar.calendar",
        "owner_qualname": "SimpleCalendarAddOneEvent.generate_random_params",
        "sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
        "snippet_sha256": "a0de00951ae81703ebff24524b5b3845158a727a96d429253fbd9effc4e5a6f7",
        "start_line": 122
      }
    ],
    "value": {}
  },
  "schema_version": "androidworld_case_semantics/v2",
  "selection_rank": 9,
  "task_id": "SimpleCalendarAddOneEventTomorrow"
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "SimpleCalendarAddOneEventTomorrow",
  "copied_files": [
    "derived/canonical_task_semantics.json",
    "derived/selected_task_source.json",
    "derived/source_closure.json",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/state_pb2.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/task_pb2.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
    "official/install/android_world/env/__init__.py",
    "official/install/android_world/env/actuation.py",
    "official/install/android_world/env/adb_utils.py",
    "official/install/android_world/env/android_world_controller.py",
    "official/install/android_world/env/device_constants.py",
    "official/install/android_world/env/interface.py",
    "official/install/android_world/env/json_action.py",
    "official/install/android_world/env/representation_utils.py",
    "official/install/android_world/env/setup_device/__init__.py",
    "official/install/android_world/env/setup_device/apps.py",
    "official/install/android_world/env/setup_device/setup.py",
    "official/install/android_world/env/tools.py",
    "official/install/android_world/registry.py",
    "official/install/android_world/suite_utils.py",
    "official/install/android_world/task_evals/__init__.py",
    "official/install/android_world/task_evals/common_validators/__init__.py",
    "official/install/android_world/task_evals/common_validators/sqlite_validators.py",
    "official/install/android_world/task_evals/information_retrieval/__init__.py",
    "official/install/android_world/task_evals/information_retrieval/datetime_utils.py",
    "official/install/android_world/task_evals/information_retrieval/joplin_app_utils.py",
    "official/install/android_world/task_evals/information_retrieval/proto/__init__.py",
    "official/install/android_world/task_evals/information_retrieval/proto/state.proto",
    "official/install/android_world/task_evals/information_retrieval/proto/task.proto",
    "official/install/android_world/task_evals/information_retrieval/proto_utils.py",
    "official/install/android_world/task_evals/single/calendar/__init__.py",
    "official/install/android_world/task_evals/single/calendar/calendar.py",
    "official/install/android_world/task_evals/single/calendar/calendar_evaluators.py",
    "official/install/android_world/task_evals/single/calendar/calendar_utils.py",
    "official/install/android_world/task_evals/single/calendar/events_generator.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_evals/utils/__init__.py",
    "official/install/android_world/task_evals/utils/sqlite_schema_utils.py",
    "official/install/android_world/task_evals/utils/sqlite_utils.py",
    "official/install/android_world/task_metadata.json",
    "official/install/android_world/utils/__init__.py",
    "official/install/android_world/utils/app_snapshot.py",
    "official/install/android_world/utils/contacts_utils.py",
    "official/install/android_world/utils/datetime_utils.py",
    "official/install/android_world/utils/file_utils.py",
    "official/install/android_world/utils/fuzzy_match_lib.py"
  ],
  "derived_files": [
    "derived/canonical_task_semantics.json",
    "derived/selected_task_source.json",
    "derived/source_closure.json"
  ],
  "domain": "androidworld",
  "file_sources": {
    "derived/canonical_task_semantics.json": "androidworld-canonical-semantics://SimpleCalendarAddOneEventTomorrow@6f3bf04dc0a5669ad3a4c464332f4402c3eee076dedfd08806c6f3f3b028de4c",
    "derived/selected_task_source.json": "androidworld://SimpleCalendarAddOneEventTomorrow",
    "derived/source_closure.json": "androidworld-source-closure://SimpleCalendarAddOneEventTomorrow@d9c569f764b3a5629321858de03ff653d0f24056",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/state_pb2.py": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/state_pb2.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/task_pb2.py": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/task_pb2.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
    "official/install/android_world/env/__init__.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/__init__.py",
    "official/install/android_world/env/actuation.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/actuation.py",
    "official/install/android_world/env/adb_utils.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/adb_utils.py",
    "official/install/android_world/env/android_world_controller.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/android_world_controller.py",
    "official/install/android_world/env/device_constants.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/device_constants.py",
    "official/install/android_world/env/interface.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/interface.py",
    "official/install/android_world/env/json_action.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/json_action.py",
    "official/install/android_world/env/representation_utils.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/representation_utils.py",
    "official/install/android_world/env/setup_device/__init__.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/setup_device/__init__.py",
    "official/install/android_world/env/setup_device/apps.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/setup_device/apps.py",
    "official/install/android_world/env/setup_device/setup.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/setup_device/setup.py",
    "official/install/android_world/env/tools.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/tools.py",
    "official/install/android_world/registry.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py",
    "official/install/android_world/suite_utils.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/suite_utils.py",
    "official/install/android_world/task_evals/__init__.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/__init__.py",
    "official/install/android_world/task_evals/common_validators/__init__.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/common_validators/__init__.py",
    "official/install/android_world/task_evals/common_validators/sqlite_validators.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/common_validators/sqlite_validators.py",
    "official/install/android_world/task_evals/information_retrieval/__init__.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/__init__.py",
    "official/install/android_world/task_evals/information_retrieval/datetime_utils.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/datetime_utils.py",
    "official/install/android_world/task_evals/information_retrieval/joplin_app_utils.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/joplin_app_utils.py",
    "official/install/android_world/task_evals/information_retrieval/proto/__init__.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/proto/__init__.py",
    "official/install/android_world/task_evals/information_retrieval/proto/state.proto": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/proto/state.proto",
    "official/install/android_world/task_evals/information_retrieval/proto/task.proto": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/proto/task.proto",
    "official/install/android_world/task_evals/information_retrieval/proto_utils.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/proto_utils.py",
    "official/install/android_world/task_evals/single/calendar/__init__.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/__init__.py",
    "official/install/android_world/task_evals/single/calendar/calendar.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/calendar.py",
    "official/install/android_world/task_evals/single/calendar/calendar_evaluators.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/calendar_evaluators.py",
    "official/install/android_world/task_evals/single/calendar/calendar_utils.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/calendar_utils.py",
    "official/install/android_world/task_evals/single/calendar/events_generator.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/events_generator.py",
    "official/install/android_world/task_evals/task_eval.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_evals/utils/__init__.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/utils/__init__.py",
    "official/install/android_world/task_evals/utils/sqlite_schema_utils.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/utils/sqlite_schema_utils.py",
    "official/install/android_world/task_evals/utils/sqlite_utils.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/utils/sqlite_utils.py",
    "official/install/android_world/task_metadata.json": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json",
    "official/install/android_world/utils/__init__.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/__init__.py",
    "official/install/android_world/utils/app_snapshot.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/app_snapshot.py",
    "official/install/android_world/utils/contacts_utils.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/contacts_utils.py",
    "official/install/android_world/utils/datetime_utils.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/datetime_utils.py",
    "official/install/android_world/utils/file_utils.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/file_utils.py",
    "official/install/android_world/utils/fuzzy_match_lib.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/fuzzy_match_lib.py"
  },
  "official_files": [
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/state_pb2.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/task_pb2.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
    "official/install/android_world/env/__init__.py",
    "official/install/android_world/env/actuation.py",
    "official/install/android_world/env/adb_utils.py",
    "official/install/android_world/env/android_world_controller.py",
    "official/install/android_world/env/device_constants.py",
    "official/install/android_world/env/interface.py",
    "official/install/android_world/env/json_action.py",
    "official/install/android_world/env/representation_utils.py",
    "official/install/android_world/env/setup_device/__init__.py",
    "official/install/android_world/env/setup_device/apps.py",
    "official/install/android_world/env/setup_device/setup.py",
    "official/install/android_world/env/tools.py",
    "official/install/android_world/registry.py",
    "official/install/android_world/suite_utils.py",
    "official/install/android_world/task_evals/__init__.py",
    "official/install/android_world/task_evals/common_validators/__init__.py",
    "official/install/android_world/task_evals/common_validators/sqlite_validators.py",
    "official/install/android_world/task_evals/information_retrieval/__init__.py",
    "official/install/android_world/task_evals/information_retrieval/datetime_utils.py",
    "official/install/android_world/task_evals/information_retrieval/joplin_app_utils.py",
    "official/install/android_world/task_evals/information_retrieval/proto/__init__.py",
    "official/install/android_world/task_evals/information_retrieval/proto/state.proto",
    "official/install/android_world/task_evals/information_retrieval/proto/task.proto",
    "official/install/android_world/task_evals/information_retrieval/proto_utils.py",
    "official/install/android_world/task_evals/single/calendar/__init__.py",
    "official/install/android_world/task_evals/single/calendar/calendar.py",
    "official/install/android_world/task_evals/single/calendar/calendar_evaluators.py",
    "official/install/android_world/task_evals/single/calendar/calendar_utils.py",
    "official/install/android_world/task_evals/single/calendar/events_generator.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_evals/utils/__init__.py",
    "official/install/android_world/task_evals/utils/sqlite_schema_utils.py",
    "official/install/android_world/task_evals/utils/sqlite_utils.py",
    "official/install/android_world/task_metadata.json",
    "official/install/android_world/utils/__init__.py",
    "official/install/android_world/utils/app_snapshot.py",
    "official/install/android_world/utils/contacts_utils.py",
    "official/install/android_world/utils/datetime_utils.py",
    "official/install/android_world/utils/file_utils.py",
    "official/install/android_world/utils/fuzzy_match_lib.py"
  ],
  "packet_files": [
    "official/install/android_world/task_metadata.json",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_evals/single/calendar/calendar.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
    "official/install/android_world/task_evals/common_validators/sqlite_validators.py",
    "official/install/android_world/suite_utils.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/state_pb2.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/task_pb2.py",
    "official/install/android_world/env/__init__.py",
    "official/install/android_world/env/actuation.py",
    "official/install/android_world/env/adb_utils.py",
    "official/install/android_world/env/android_world_controller.py",
    "official/install/android_world/env/device_constants.py",
    "official/install/android_world/env/interface.py",
    "official/install/android_world/env/json_action.py",
    "official/install/android_world/env/representation_utils.py",
    "official/install/android_world/env/setup_device/__init__.py",
    "official/install/android_world/env/setup_device/apps.py",
    "official/install/android_world/env/setup_device/setup.py",
    "official/install/android_world/env/tools.py",
    "official/install/android_world/task_evals/__init__.py",
    "official/install/android_world/task_evals/common_validators/__init__.py",
    "official/install/android_world/task_evals/information_retrieval/__init__.py",
    "official/install/android_world/task_evals/information_retrieval/datetime_utils.py",
    "official/install/android_world/task_evals/information_retrieval/joplin_app_utils.py",
    "official/install/android_world/task_evals/information_retrieval/proto/__init__.py",
    "official/install/android_world/task_evals/information_retrieval/proto/state.proto",
    "official/install/android_world/task_evals/information_retrieval/proto/task.proto",
    "official/install/android_world/task_evals/information_retrieval/proto_utils.py",
    "official/install/android_world/task_evals/single/calendar/__init__.py",
    "official/install/android_world/task_evals/single/calendar/calendar_evaluators.py",
    "official/install/android_world/task_evals/single/calendar/calendar_utils.py",
    "official/install/android_world/task_evals/single/calendar/events_generator.py",
    "official/install/android_world/task_evals/utils/__init__.py",
    "official/install/android_world/task_evals/utils/sqlite_schema_utils.py",
    "official/install/android_world/task_evals/utils/sqlite_utils.py",
    "official/install/android_world/utils/__init__.py",
    "official/install/android_world/utils/app_snapshot.py",
    "official/install/android_world/utils/contacts_utils.py",
    "official/install/android_world/utils/datetime_utils.py",
    "official/install/android_world/utils/file_utils.py",
    "official/install/android_world/utils/fuzzy_match_lib.py",
    "derived/selected_task_source.json",
    "derived/source_closure.json",
    "derived/canonical_task_semantics.json"
  ],
  "sha256_per_file": {
    "derived/canonical_task_semantics.json": "5480682bb3766027863281316f690573f0bc063da9ed059fb68a2ac99aecc1f8",
    "derived/selected_task_source.json": "faa5cae651cd964cab34486ca49e2261afae4c6747b1e31678391b9b00dd9ade",
    "derived/source_closure.json": "166d85c7d01495a44eac3fbe6dfa4f1b9f07ee5a4dbe194eee9395327b70524b",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/state_pb2.py": "7fcc0e0c1cd8c1d03d644e23a2c2d3e17709d6f1cddc4b04655be9bda035cde4",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/task_pb2.py": "1cc5638cf6dc51463dffd7ca9ee3c85cbabcb66e89815ee4bf53f61dc7c7e84c",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
    "official/install/android_world/env/__init__.py": "1cb8fdedd768b8016bb55733b1077301ecfe9b801b28fbcb028addbbc0981239",
    "official/install/android_world/env/actuation.py": "6be679b15544a713279aeaad3f4864757747accda1bd00185ae7f67b22623725",
    "official/install/android_world/env/adb_utils.py": "15c61078c8d6d091c2784feef231e1477e11304da0c7d383cf574fff629c1d00",
    "official/install/android_world/env/android_world_controller.py": "989968aba1a2ef5f9bd70af24762e5480d809ef0c4c07f82c7b8167e5d8bbf8c",
    "official/install/android_world/env/device_constants.py": "259b41e545a2887e734991c389b0c85db8ff4824149a9e2458e93ec7741a731c",
    "official/install/android_world/env/interface.py": "c9372c3dcaef98cd20d67f7bf9084ab9609c5b2eeb2da9f35448d0ebe0483a00",
    "official/install/android_world/env/json_action.py": "142755d4e0a2d3f761562b726d849d906b49c83f4a91b09dfa3a779e24386127",
    "official/install/android_world/env/representation_utils.py": "4fdfc593668ade52dc477a119f7c8d83d77cdc939d5c97ce8dd291a018ca56d2",
    "official/install/android_world/env/setup_device/__init__.py": "55029b4439d73a294227fe467ee2b3c3d7ad9820b61bfd58bf5b39af1601a87e",
    "official/install/android_world/env/setup_device/apps.py": "109e51edba6a3bf6b9451d084d6cd8ca2c06e0e1415db1eac441af63e83783f6",
    "official/install/android_world/env/setup_device/setup.py": "1874126ccc2ca48265c6803c2b420f77ae6a2a4193ba9d7279cd96d84f571de6",
    "official/install/android_world/env/tools.py": "987f97ffdc76ba4745ea1401044a11f23fc79b49ac642e7a6c8cbef3ae9b5b9a",
    "official/install/android_world/registry.py": "47380849f428b231747365ac8ba50a83212cdc34180ab6376ff49e90b93af12b",
    "official/install/android_world/suite_utils.py": "caf4d3a8765c914a2b978d119921cc4c062176e5a362c20c53905d4d0dbe083b",
    "official/install/android_world/task_evals/__init__.py": "d99873f57aa5a9e5598581e873ab497f6e3cc2fcb9800de4a2896169fcfc0f0a",
    "official/install/android_world/task_evals/common_validators/__init__.py": "5a5942e515bf7fafc12f799e1f569109193ea59b912daf7ffd6d484f422ea3da",
    "official/install/android_world/task_evals/common_validators/sqlite_validators.py": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
    "official/install/android_world/task_evals/information_retrieval/__init__.py": "e3b356b9bc0d1f8d3e3edbdf1c0d25dc59aacd02118d59302fdb8624cd345aa4",
    "official/install/android_world/task_evals/information_retrieval/datetime_utils.py": "6812cb1dedc17914eb3c89678fedaacb360a4f71bf3cc5bd8849a986f9f5ba90",
    "official/install/android_world/task_evals/information_retrieval/joplin_app_utils.py": "fceb231218c9b59dbdfa35dabb8713e9700338cf3787ae7c69f565d959ba18fe",
    "official/install/android_world/task_evals/information_retrieval/proto/__init__.py": "0a303e72ba0eacbf79ad584c605af6205d6e5f3c176c722b14d4e0ce990ca89b",
    "official/install/android_world/task_evals/information_retrieval/proto/state.proto": "17bbf2880baace87b35c4fcf8729b44414d53e07c623ad8705742012ad8661ab",
    "official/install/android_world/task_evals/information_retrieval/proto/task.proto": "c8c25f9034abe201055e4e8a457e3101b1a64cbd876323f22eca47fc5f5b9d8a",
    "official/install/android_world/task_evals/information_retrieval/proto_utils.py": "301f83956b1b2ac2ce5bca0f75357f7a31d2a9a8a8145da737efa1539d6961cb",
    "official/install/android_world/task_evals/single/calendar/__init__.py": "5f65b84304b8d15f58871be761f7b624ec9ad389fe08848a41d2a4ab7395b08a",
    "official/install/android_world/task_evals/single/calendar/calendar.py": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
    "official/install/android_world/task_evals/single/calendar/calendar_evaluators.py": "ad25b8064ee5d5341f97a902ff222342456e9932a431ee06945f5f8992d53273",
    "official/install/android_world/task_evals/single/calendar/calendar_utils.py": "14ff8d7db0d1ffaf7c45307f79ed7b6bc200c62143d5892833f7fe88706fc315",
    "official/install/android_world/task_evals/single/calendar/events_generator.py": "0b894783493407dfffff4b7e02b68e778f7d2667358965e5bb4f9a78a7fb5963",
    "official/install/android_world/task_evals/task_eval.py": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
    "official/install/android_world/task_evals/utils/__init__.py": "761fd2724b3525c58df44e4b0ab36953c60aa8b9af8bf12460bd508ff2d3ba1b",
    "official/install/android_world/task_evals/utils/sqlite_schema_utils.py": "0e995bbc182e2ea35f3c68200a766cd288a60a597d71082f3ba5617b665366ed",
    "official/install/android_world/task_evals/utils/sqlite_utils.py": "61cab2a77135b47915843b4202b98be735af1cdd4220908f9f35da4265098c8a",
    "official/install/android_world/task_metadata.json": "fd3cf23ebb26e461a961dd60ff3f011d7e6ec78c992c10babbbdb86f9dd591e1",
    "official/install/android_world/utils/__init__.py": "9edbb8eb66e5175a40f26ff4424d2b62dc66077ab81f78768e1da879e866a69a",
    "official/install/android_world/utils/app_snapshot.py": "9689192d31ffd29298c3f740ac29783bb03294faebdd5c1964a2904fdb3bddd4",
    "official/install/android_world/utils/contacts_utils.py": "92f193c0cedd301fdc8f5f7a8ba6fec2410f16d82d0259ab9cdd844dbd0925c3",
    "official/install/android_world/utils/datetime_utils.py": "32594fcd09e038467166678c7894b649f32c3a815f054b5d85c0fdb69b9d6e81",
    "official/install/android_world/utils/file_utils.py": "5bd04ccdafba65f4b909c8bb9fca166e5eba92dc2e64c83f80729941dfab2d1d",
    "official/install/android_world/utils/fuzzy_match_lib.py": "e7376554fd9a413ff00d71656e09609c9070d0b384028b89fd931e32fcfb2969"
  },
  "source_refs": [
    "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/state_pb2.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/information_retrieval/proto/task_pb2.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/__init__.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/actuation.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/adb_utils.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/android_world_controller.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/device_constants.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/interface.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/json_action.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/representation_utils.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/setup_device/__init__.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/setup_device/apps.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/setup_device/setup.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/env/tools.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/suite_utils.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/__init__.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/common_validators/__init__.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/common_validators/sqlite_validators.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/__init__.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/datetime_utils.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/joplin_app_utils.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/proto/__init__.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/proto/state.proto",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/proto/task.proto",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/information_retrieval/proto_utils.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/__init__.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/calendar.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/calendar_evaluators.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/calendar_utils.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/single/calendar/events_generator.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/utils/__init__.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/utils/sqlite_schema_utils.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/utils/sqlite_utils.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/__init__.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/app_snapshot.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/contacts_utils.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/datetime_utils.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/file_utils.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/utils/fuzzy_match_lib.py",
    "androidworld-canonical-semantics://SimpleCalendarAddOneEventTomorrow@6f3bf04dc0a5669ad3a4c464332f4402c3eee076dedfd08806c6f3f3b028de4c",
    "androidworld-source-closure://SimpleCalendarAddOneEventTomorrow@d9c569f764b3a5629321858de03ff653d0f24056",
    "androidworld://SimpleCalendarAddOneEventTomorrow"
  ],
  "task_id": "SimpleCalendarAddOneEventTomorrow"
}
```
