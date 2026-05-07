# Case Packet

## Case Metadata

- domain: `androidworld`
- case_unit_id: `SimpleCalendarAddOneEvent`
- task_id: `SimpleCalendarAddOneEvent`

## Source Inventory

- `official/install/android_world/task_metadata.json`
- `official/install/android_world/registry.py`
- `official/install/android_world/task_evals/task_eval.py`
- `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py`
- `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/common_validators/sqlite_validators.py`
- `derived/selected_task_source.json`

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

### `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/common_validators/sqlite_validators.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/common_validators/sqlite_validators.py`

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

### `derived/selected_task_source.json`

Source ref: `androidworld://SimpleCalendarAddOneEvent`

```json
{
  "base_class_name": "AddMultipleRows",
  "base_module": "android_world.task_evals.common_validators.sqlite_validators",
  "base_source_file": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/common_validators/sqlite_validators.py",
  "case_unit_id": "SimpleCalendarAddOneEvent",
  "class_name": "SimpleCalendarAddOneEvent",
  "difficulty": "hard",
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
      "archive_path": "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
      "sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py"
    },
    {
      "archive_path": "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/common_validators/sqlite_validators.py",
      "sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/common_validators/sqlite_validators.py"
    }
  ],
  "optimal_steps": "17",
  "packet_files": [
    "official/install/android_world/task_metadata.json",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/common_validators/sqlite_validators.py",
    "derived/selected_task_source.json"
  ],
  "selection_order_key": "6b03b8bb5abdf1325bac62d1c5ea2c5b7d5c38c6f04e04afde8f34bc34fb0879",
  "selection_rank": 52,
  "source_file": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
  "source_ref": "androidworld://SimpleCalendarAddOneEvent",
  "source_sha256": "bdc0d9a2dbed616d925efaf7931a5f1bcef559b02e0eeda0b42cd4652e500a08",
  "tags": [
    "data_entry",
    "complex_ui_understanding",
    "parameterized"
  ],
  "task_id": "SimpleCalendarAddOneEvent",
  "task_name": "SimpleCalendarAddOneEvent",
  "task_template": "In Simple Calendar Pro, create a calendar event on {year}-{month}-{day} at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins."
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "SimpleCalendarAddOneEvent",
  "copied_files": [
    "derived/selected_task_source.json",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/common_validators/sqlite_validators.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_metadata.json"
  ],
  "derived_files": [
    "derived/selected_task_source.json"
  ],
  "domain": "androidworld",
  "file_sources": {
    "derived/selected_task_source.json": "androidworld://SimpleCalendarAddOneEvent",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/common_validators/sqlite_validators.py": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/common_validators/sqlite_validators.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
    "official/install/android_world/registry.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_metadata.json": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json"
  },
  "official_files": [
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/common_validators/sqlite_validators.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_metadata.json"
  ],
  "packet_files": [
    "official/install/android_world/task_metadata.json",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/common_validators/sqlite_validators.py",
    "derived/selected_task_source.json"
  ],
  "sha256_per_file": {
    "derived/selected_task_source.json": "e3bf40ea9a0ef0fc987598b1f645a7adb7de32c668ee274549e917f5786296f5",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/common_validators/sqlite_validators.py": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
    "official/install/android_world/registry.py": "47380849f428b231747365ac8ba50a83212cdc34180ab6376ff49e90b93af12b",
    "official/install/android_world/task_evals/task_eval.py": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
    "official/install/android_world/task_metadata.json": "fd3cf23ebb26e461a961dd60ff3f011d7e6ec78c992c10babbbdb86f9dd591e1"
  },
  "source_refs": [
    "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/common_validators/sqlite_validators.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/calendar/calendar.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json",
    "androidworld://SimpleCalendarAddOneEvent"
  ],
  "task_id": "SimpleCalendarAddOneEvent"
}
```
