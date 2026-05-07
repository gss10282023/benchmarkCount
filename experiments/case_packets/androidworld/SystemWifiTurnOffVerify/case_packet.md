# Case Packet

## Case Metadata

- domain: `androidworld`
- case_unit_id: `SystemWifiTurnOffVerify`
- task_id: `SystemWifiTurnOffVerify`

## Source Inventory

- `official/install/android_world/task_metadata.json`
- `official/install/android_world/registry.py`
- `official/install/android_world/task_evals/task_eval.py`
- `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/system.py`
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

### `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/system.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/system.py`

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

"""Tasks for general system tasks like interacting with settings."""

import dataclasses
import random
from typing import Any

from absl import logging
from android_world.env import adb_utils
from android_world.env import interface
from android_world.task_evals import task_eval
from android_world.utils import fuzzy_match_lib
import immutabledict


class _SystemBrightnessToggle(task_eval.TaskEval):
  """Task for checking that the screen brightness has been set to {max_or_min}."""

  app_names = ('settings',)
  complexity = 1
  schema = {
      'type': 'object',
      'properties': {'max_or_min': {'type': 'string', 'enum': ['max', 'min']}},
      'required': ['max_or_min'],
  }
  template = 'Turn brightness to the {max_or_min} value.'

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    res = adb_utils.issue_generic_request(
        ['shell', 'settings', 'get', 'system', 'screen_brightness'],
        env.controller,
    )
    brightness_level = int(res.generic.output.decode().strip())

    if self.params['max_or_min'] == 'max':
      return 1.0 if brightness_level == 255 else 0.0
    else:
      return 1.0 if brightness_level == 1 else 0.0

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    return {'max_or_min': 'max' if random.choice([True, False]) else 'min'}


class SystemBrightnessMinVerify(_SystemBrightnessToggle):
  """Task for verifying that the screen brightness is already at minimum.

  Precondition: Screen brightness is at minimum.
  """

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    adb_utils.set_brightness('min', env.controller)

  @classmethod
  def generate_random_params(cls) -> dict[str, str]:
    return {'max_or_min': 'min'}


class SystemBrightnessMaxVerify(_SystemBrightnessToggle):
  """Task for verifying that the screen brightness is already at maximum.

  Precondition: Screen brightness is at maximum.
  """

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    adb_utils.set_brightness('max', env.controller)

  @classmethod
  def generate_random_params(cls) -> dict[str, str]:
    return {'max_or_min': 'max'}


class SystemBrightnessMin(_SystemBrightnessToggle):
  """Task for ensuring that the screen brightness is set to minimum.

  Precondition: Screen brightness is not at minimum.
  """

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    adb_utils.set_brightness('max', env.controller)

  @classmethod
  def generate_random_params(cls) -> dict[str, str]:
    return {'max_or_min': 'min'}


class SystemBrightnessMax(_SystemBrightnessToggle):
  """Task for ensuring that the screen brightness is set to maximum.

  Precondition: Screen brightness is not at maximum.
  """

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    adb_utils.set_brightness('min', env.controller)

  @classmethod
  def generate_random_params(cls) -> dict[str, str]:
    return {'max_or_min': 'max'}


class _SystemWifiToggle(task_eval.TaskEval):
  """Task for checking that WiFi has been turned {on_or_off}."""

  app_names = ('settings',)
  complexity = 1
  schema = {
      'type': 'object',
      'properties': {'on_or_off': {'type': 'string', 'enum': ['on', 'off']}},
      'required': ['on_or_off'],
  }
  template = 'Turn wifi {on_or_off}.'

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    res = adb_utils.issue_generic_request(
        ['shell', 'settings', 'get', 'global', 'wifi_on'], env.controller
    )
    wifi_status = res.generic.output.decode().strip()

    if self.params['on_or_off'] == 'on':
      # WiFi is on when the value is either 1 or 2. If Airplane mode is on, and
      # WiFi is on, it will be "2".
      return 1.0 if wifi_status in ['1', '2'] else 0.0
    else:
      # WiFi is off when the value is 0.
      return 1.0 if wifi_status == '0' else 0.0

  @classmethod
  def generate_random_params(cls) -> dict[str, str]:
    return {'on_or_off': 'on' if random.choice([True, False]) else 'off'}


class SystemWifiTurnOffVerify(_SystemWifiToggle):
  """Task for verifying that WiFi is already turned off.

  Precondition: WiFi is off.
  """

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    adb_utils.toggle_wifi(env.controller, 'off')

  @classmethod
  def generate_random_params(cls) -> dict[str, str]:
    return {'on_or_off': 'off'}


class SystemWifiTurnOnVerify(_SystemWifiToggle):
  """Task for verifying that WiFi is already turned on.

  Precondition: WiFi is on.
  """

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    adb_utils.toggle_wifi(env.controller, 'on')

  @classmethod
  def generate_random_params(cls) -> dict[str, str]:
    return {'on_or_off': 'on'}


class SystemWifiTurnOff(_SystemWifiToggle):
  """Task for ensuring that WiFi is turned off.

  Precondition: WiFi is on.
  """

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    adb_utils.toggle_wifi(env.controller, 'on')

  @classmethod
  def generate_random_params(cls) -> dict[str, str]:
    return {'on_or_off': 'off'}


class SystemWifiTurnOn(_SystemWifiToggle):
  """Task for ensuring that WiFi is turned on.

  Precondition: WiFi is off.
  """

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    adb_utils.toggle_wifi(env.controller, 'off')

  @classmethod
  def generate_random_params(cls) -> dict[str, str]:
    return {'on_or_off': 'on'}


class _SystemBluetoothToggle(task_eval.TaskEval):
  """Task for checking that Bluetooth has been turned {on_or_off}."""

  app_names = ('settings',)
  complexity = 1
  schema = {
      'type': 'object',
      'properties': {'on_or_off': {'type': 'string', 'enum': ['on', 'off']}},
      'required': ['on_or_off'],
  }
  template = 'Turn bluetooth {on_or_off}.'

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    res = adb_utils.issue_generic_request(
        ['shell', 'settings', 'get', 'global', 'bluetooth_on'], env.controller
    )
    bluetooth_status = res.generic.output.decode().strip()
    expected_status = '1' if self.params['on_or_off'] == 'on' else '0'
    return 1.0 if bluetooth_status == expected_status else 0.0

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    return {'on_or_off': 'on' if random.choice([True, False]) else 'off'}


class SystemBluetoothTurnOffVerify(_SystemBluetoothToggle):
  """Task for verifying that Bluetooth is already turned off.

  Precondition: Bluetooth is off.
  """

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    adb_utils.toggle_bluetooth(env.controller, 'off')

  @classmethod
  def generate_random_params(cls) -> dict[str, str]:
    return {'on_or_off': 'off'}


class SystemBluetoothTurnOnVerify(_SystemBluetoothToggle):
  """Task for verifying that Bluetooth is already turned on.

  Precondition: Bluetooth is on.
  """

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    adb_utils.toggle_bluetooth(env.controller, 'on')

  @classmethod
  def generate_random_params(cls) -> dict[str, str]:
    return {'on_or_off': 'on'}


class SystemBluetoothTurnOff(_SystemBluetoothToggle):
  """Task for ensuring that Bluetooth is turned off.

  Precondition: Bluetooth is on.
  """

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    adb_utils.toggle_bluetooth(env.controller, 'on')

  @classmethod
  def generate_random_params(cls) -> dict[str, str]:
    return {'on_or_off': 'off'}


class SystemBluetoothTurnOn(_SystemBluetoothToggle):
  """Task for ensuring that Bluetooth is turned on.

  Precondition: Bluetooth is off.
  """

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    adb_utils.toggle_bluetooth(env.controller, 'off')

  @classmethod
  def generate_random_params(cls) -> dict[str, str]:
    return {'on_or_off': 'on'}


class SystemCopyToClipboard(task_eval.TaskEval):
  """Task for verifying that the correct params are copied to the clipboard."""

  app_names = ('clipper',)
  complexity = 1
  schema = {
      'type': 'object',
      'properties': {
          'clipboard_content': {'type': 'string'},
      },
      'required': ['clipboard_content'],
  }

  template = 'Copy the following text to the clipboard: {clipboard_content}'

  def __init__(self, params: dict[str, Any]):
    """Initialize the task with given params."""
    super().__init__(params)
    self.clipboard_content = params['clipboard_content']

  def _clear_clipboard(self, env: interface.AsyncEnv) -> None:
    # Use a unique string to set the clipboard contents.
    adb_utils.set_clipboard_contents('~~~RESET~~~', env.controller)

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    self._clear_clipboard(env)

  def is_successful(self, env: interface.AsyncEnv) -> float:
    """Check if the clipboard content matches the expected content."""
    actual_clipboard_content = adb_utils.get_clipboard_contents(env.controller)
    return (
        1.0
        if fuzzy_match_lib.fuzzy_match(
            self.clipboard_content, actual_clipboard_content
        )
        else 0.0
    )

  def tear_down(self, env: interface.AsyncEnv) -> None:
    super().tear_down(env)
    self._clear_clipboard(env)

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    return {
        'clipboard_content': random.choice([
            '1234 Elm St, Springfield, IL',
            'Acme Corp, Suite 200',
            'john.doe@example.com',
            "Jane's Flower Shop",
            'Call me at 555-1234',
            'Order No: A123456',
            'Reservation under: Jane',
            'Discount code: SAVE20',
            'Membership ID: XYZ789',
            'Invoice #98765',
            'Tracking #: 1Z204E2A',
            'Transaction ID: abc123',
            '9876 Pine Ave, Riverside, CA',
            'Global Tech, Floor 3',
            'jane.smith@example.com',
            "Mike's Grocery Store",
            'Text me at 555-6789',
            'Order No: B654321',
            'Reservation under: Mike',
            'Promo code: DEAL30',
            'Membership ID: ABC123',
            'Invoice #54321',
            'Tracking #: 3H488Y2B',
            'Transaction ID: def456',
            '2554 Oak Street, Boston, MA',
            'Innovate Inc, Room 10',
            'alex.jordan@example.net',
            "Sara's Bakery",
            'Reach out at 555-9101',
            'Order No: C987654',
            'Reservation under: Sara',
            'Coupon code: OFF50',
            'Membership ID: LMN456',
            'Invoice #32198',
            'Tracking #: 5K672F4C',
            'Transaction ID: ghi789',
        ])
    }


@dataclasses.dataclass(frozen=True)
class _ComponentName:
  """Android identifier for an application component.

  Identifier for an application component - i.e., an Activity, a Service, a
  BroadcastReceiver, or a Content Provider. Encapsulates two pieces of
  information used to identify the component - the package name of the app it
  exists in, and the class name of the object within that app.
  """

  package_name: str
  class_name: str


def _normalize_class_name(package_name: str, class_name: str) -> str:
  """Normalizes a fully qualified class name to be relative to the package.

  Class names are strings, which can be fully qualified or relative to the
  app's package. This function normalizes a fully qualified class name to be
  relative, to make it easy to test two class names for equality.

      normalized_class_name = _normalize_class_name(
          'com.android.settings',
          'com.android.settings.Settings'
      )
      assert normalized_class_name == '.Settings'

  Args:
    package_name: The package name of the app.
    class_name: The name of the class.

  Returns:
    The class name, normalized to be relative if fully qualified.
  """
  if class_name.startswith(package_name):
    return class_name[len(package_name) :]
  return class_name


def parse_component_name(component_name: str) -> _ComponentName:
  """Parses a ComponentName from a string.

  Args:
    component_name: The string representation of the component name, e.g.
      'com.android.settings/com.android.settings.Settings'.

  Returns:
    The parsed ComponentName.
  Raises:
    ValueError: If called with an invalid string representation of a
      ComponentName.
  """
  parts = component_name.split('/')
  if len(parts) != 2:
    raise ValueError(
        'Badly formed component name: the package and class names must be '
        'separated by a single slash'
    )
  return _ComponentName(
      package_name=parts[0],
      class_name=_normalize_class_name(
          package_name=parts[0], class_name=parts[1]
      ),
  )


_APP_NAME_TO_PACKAGE_NAME = immutabledict.immutabledict({
    'camera': 'com.android.camera2',
    'clock': 'com.google.android.deskclock',
    'contacts': 'com.google.android.contacts',
    'settings': 'com.android.settings',
    'dialer': 'com.google.android.dialer',
})


class OpenAppTaskEval(task_eval.TaskEval):
  """Task eval for opening an app."""

  app_names = tuple(_APP_NAME_TO_PACKAGE_NAME.keys())

  complexity = 1

  schema = {
      'type': 'object',
      'properties': {
          'app_name': {'type': 'string'},
      },
      'required': ['app_name'],
  }

  template = (
      'Open the {app_name} app. Clear any pop-ups that may appear by granting'
      ' all permissions that are required.'
  )

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    app_name = random.choice(list(_APP_NAME_TO_PACKAGE_NAME.keys()))
    return {'app_name': app_name}

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    active_activity, _ = adb_utils.get_current_activity(env.controller)
    expected_package_name = _APP_NAME_TO_PACKAGE_NAME[self.params['app_name']]
    if (
        parse_component_name(active_activity).package_name
        == expected_package_name
    ):
      return 1.0
    else:
      logging.info(
          'Expected %s to be active app but saw %s',
          expected_package_name,
          active_activity,
      )
      return 0.0
```

### `derived/selected_task_source.json`

Source ref: `androidworld://SystemWifiTurnOffVerify`

```json
{
  "base_class_name": "_SystemWifiToggle",
  "base_module": "android_world.task_evals.single.system",
  "base_source_file": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/system.py",
  "case_unit_id": "SystemWifiTurnOffVerify",
  "class_name": "SystemWifiTurnOffVerify",
  "difficulty": "easy",
  "module": "android_world.task_evals.single.system",
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
      "archive_path": "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/system.py",
      "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/system.py"
    }
  ],
  "optimal_steps": "3",
  "packet_files": [
    "official/install/android_world/task_metadata.json",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/system.py",
    "derived/selected_task_source.json"
  ],
  "selection_order_key": "9145aff92071ee8e59654dbb60b8afa4071d347e66a8f4987955a18437a26516",
  "selection_rank": 69,
  "source_file": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/system.py",
  "source_ref": "androidworld://SystemWifiTurnOffVerify",
  "source_sha256": "08dc72cbb08d4c6995ec360e7eb561151cd46ee32b51aedf0ff134aaa0286201",
  "tags": [
    "verification"
  ],
  "task_id": "SystemWifiTurnOffVerify",
  "task_name": "SystemWifiTurnOffVerify",
  "task_template": "Turn wifi {on_or_off}."
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "SystemWifiTurnOffVerify",
  "copied_files": [
    "derived/selected_task_source.json",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/system.py",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_metadata.json"
  ],
  "derived_files": [
    "derived/selected_task_source.json"
  ],
  "domain": "androidworld",
  "file_sources": {
    "derived/selected_task_source.json": "androidworld://SystemWifiTurnOffVerify",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/system.py": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/system.py",
    "official/install/android_world/registry.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_metadata.json": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json"
  },
  "official_files": [
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/system.py",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_metadata.json"
  ],
  "packet_files": [
    "official/install/android_world/task_metadata.json",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/system.py",
    "derived/selected_task_source.json"
  ],
  "sha256_per_file": {
    "derived/selected_task_source.json": "a0812762c5125f89cd1011fed09c7d846ab0f28bf43c152dfba07c1bd4a52f8e",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/system.py": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
    "official/install/android_world/registry.py": "47380849f428b231747365ac8ba50a83212cdc34180ab6376ff49e90b93af12b",
    "official/install/android_world/task_evals/task_eval.py": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
    "official/install/android_world/task_metadata.json": "fd3cf23ebb26e461a961dd60ff3f011d7e6ec78c992c10babbbdb86f9dd591e1"
  },
  "source_refs": [
    "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/system.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json",
    "androidworld://SystemWifiTurnOffVerify"
  ],
  "task_id": "SystemWifiTurnOffVerify"
}
```
