# Case Packet

## Case Metadata

- domain: `androidworld`
- case_unit_id: `MarkorCreateNoteAndSms`
- task_id: `MarkorCreateNoteAndSms`

## Source Inventory

- `official/install/android_world/task_metadata.json`
- `official/install/android_world/registry.py`
- `official/install/android_world/task_evals/task_eval.py`
- `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/composite/markor_sms.py`
- `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/markor.py`
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

### `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/composite/markor_sms.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/composite/markor_sms.py`

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

"""Tasks that involve Markor and SMS."""


from absl import logging
from android_world.env import interface
from android_world.task_evals.common_validators import sms_validators
from android_world.task_evals.single import markor


class MarkorCreateNoteAndSms(markor.Markor):
  """Task for checking that a new note in Markor has been created and then an SMS has been sent."""

  app_names = ("markor", "simple sms messenger")
  complexity = 1.8
  schema = {
      "type": "object",
      "properties": {
          "file_name": {"type": "string"},
          "text": {"type": "string"},
          "number": {"type": "string"},
      },
      "required": ["file_name", "text", "number"],
  }

  template = (
      "Create a new note in Markor named {file_name} with the following text:"
      " {text}. Share the entire content of the note with the phone number"
      " {number} via SMS using Simple SMS Messenger"
  )

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    self.markor_task = markor.MarkorCreateNote(
        params={
            "file_name": self.params["file_name"],
            "text": self.params["text"],
        }
    )
    self.markor_task.initialize_task(env)

    self.sms_task = sms_validators.SimpleSMSSendSms(
        params={"number": self.params["number"], "message": self.params["text"]}
    )
    self.sms_task.initialize_task(env)

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    markor_success = self.markor_task.is_successful(env)
    logging.info("Markor success: %s", markor_success)

    sms_success = self.sms_task.is_successful(env)
    logging.info("SMS success: %s", sms_success)

    return (markor_success + sms_success) / 2.0

  def tear_down(self, env: interface.AsyncEnv):
    super().tear_down(env)
    self.markor_task.tear_down(env)
    self.sms_task.tear_down(env)

  @classmethod
  def generate_random_params(cls) -> dict[str, str | int]:
    markor_params = markor.MarkorCreateNote.generate_random_params()
    sms_params = sms_validators.SimpleSMSSendSms.generate_random_params()

    compound_params = {
        "file_name": markor_params["file_name"],
        "text": markor_params["text"],
        "number": sms_params["number"],
    }

    return compound_params
```

### `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/markor.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/markor.py`

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

"""Tasks for Markor app."""

import dataclasses
import datetime
import random
from typing import Any

from absl import logging
from android_world.env import adb_utils
from android_world.env import device_constants
from android_world.env import interface
from android_world.task_evals import task_eval
from android_world.task_evals.common_validators import file_validators
from android_world.task_evals.single import vlc
from android_world.task_evals.utils import receipt_generator
from android_world.task_evals.utils import user_data_generation
from android_world.utils import datetime_utils
from android_world.utils import file_utils
from android_world.utils import fuzzy_match_lib


@dataclasses.dataclass(frozen=True)
class _Note:
  name: str
  content: str


generate_random_sentence = lambda: random.choice(
    user_data_generation.RANDOM_SENTENCES
)


def _generate_random_note() -> _Note:
  """Generates a random note."""
  extensions = [".md", ".txt"]
  random_file_name = (
      user_data_generation.generate_random_file_name()
      + random.choice(extensions)
  )
  return _Note(random_file_name, generate_random_sentence())


class Markor(task_eval.TaskEval):
  app_names = ("markor",)

  def initialize_task(self, env: interface.AsyncEnv):
    super().initialize_task(env)
    file_utils.clear_directory(device_constants.MARKOR_DATA, env.controller)

  def tear_down(self, env: interface.AsyncEnv) -> None:
    super().tear_down(env)
    file_utils.clear_directory(device_constants.MARKOR_DATA, env.controller)


class MarkorMoveNote(Markor):
  """Task for checking that a file has been moved in Markor."""

  complexity = 1.4
  schema = file_validators.MoveFile.schema
  template = (
      "In Markor, move the note {file_name} from {source_folder} to"
      " {destination_folder}."
  )

  def __init__(self, params: dict[str, Any]):
    """Initialize the task."""
    super().__init__(params)
    self.move_file_task = file_validators.MoveFile(
        params, device_constants.MARKOR_DATA
    )

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    self.move_file_task.initialize_task(env)

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    return self.move_file_task.is_successful(env)

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    subfolders = [
        "BookNotes",
        "CodeSnippets",
        "DailyNotes",
        "FitnessPlans",
        "MeetingMinutes",
        "PersonalJournal",
        "RecipeCollections",
        "StudyGuides",
        "TravelItineraries",
        "WorkProjects",
    ]
    source_folder = random.choice(subfolders)
    destination_folder = random.choice(
        [folder for folder in subfolders if folder != source_folder]
    )
    file_name = _generate_random_note().name
    return {
        "file_name": file_name,
        "source_folder": source_folder,
        "destination_folder": destination_folder,
        "noise_candidates": _NOTE_TITLES,
    }

  def tear_down(self, env: interface.AsyncEnv) -> None:
    super().tear_down(env)
    self.move_file_task.tear_down(env)


class MarkorCreateFolder(Markor):
  """Task for checking that a new folder in Markor has been created with a specific name."""

  complexity = 1
  schema = {
      "type": "object",
      "properties": {
          "folder_name": {"type": "string"},
      },
      "required": ["folder_name"],
  }
  template = "Create a new folder in Markor named {folder_name}."

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    user_data_generation.generate_noise_files(
        "file",
        device_constants.MARKOR_DATA,
        env.controller,
        _NOTE_TITLES,
    )

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    folder_name = self.params["folder_name"]

    exists = file_utils.check_file_or_folder_exists(
        folder_name, device_constants.MARKOR_DATA, env.controller
    )

    if not exists:
      logging.info("%s not found", folder_name)
      return 0.0

    return 1.0

  @classmethod
  def generate_random_params(cls) -> dict[str, str | int]:
    random_folder_name = "folder_" + str(
        datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    return {"folder_name": random_folder_name}


class MarkorEditNote(Markor):
  """Task for editing an existing note in Markor."""

  complexity = 1.2
  schema = {
      "type": "object",
      "properties": {
          "file_name": {"type": "string"},
          "header": {"type": "string"},
          "footer": {"type": "string"},
          "replace_text": {"type": "string"},
          "edit_type": {
              "type": "string",
              "enum": ["header", "footer", "replace"],
          },
      },
      "required": ["file_name", "edit_type"],
  }

  @property
  def template(self) -> str:
    templates = {
        "header": (
            "Edit {file_name} in Markor. Add to the top of the note {header}"
        ),
        "footer": (
            "Edit {file_name} in Markor. Add to the bottom of the note {footer}"
        ),
        "replace": (
            "Edit {file_name} in Markor. Replace the text with {replace_text}"
        ),
    }

    if "edit_type" not in self.params and "edit_type" not in templates:
      return templates.get(
          self.params.get("edit_type"),
          "Invalid edit_type for {file_name} in Markor.",
      )
    return templates[self.params.get("edit_type")]

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    user_data_generation.generate_noise_files(
        self.params["file_name"],
        device_constants.MARKOR_DATA,
        env.controller,
        _NOTE_TITLES,
    )
    self.original_content = file_utils.create_file(
        self.params["file_name"],
        device_constants.MARKOR_DATA,
        env.controller,
        content=generate_random_sentence(),
    )

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    res = adb_utils.issue_generic_request(
        [
            "shell",
            "cat",
            file_utils.convert_to_posix_path(
                device_constants.MARKOR_DATA, self.params["file_name"]
            ),
        ],
        env.controller,
    )
    file_contents = res.generic.output.decode().replace("\r", "").strip()
    logging.info("Retrieved file contents: %s", file_contents)

    if self.params["edit_type"] == "header":
      expected_content = self.params["header"] + "\n" + self.original_content
    elif self.params["edit_type"] == "footer":
      expected_content = self.original_content + "\n" + self.params["footer"]
    else:
      expected_content = self.params["replace_text"]

    is_match = fuzzy_match_lib.fuzzy_match(file_contents, expected_content)
    logging.info(
        "Is content match: %s.\nFound: %s\nExpected: %s",
        is_match,
        file_contents,
        expected_content,
    )

    return 1.0 if is_match else 0.0

  @classmethod
  def generate_random_params(cls) -> dict[str, str | int]:
    extensions = [".md", ".txt"]

    random_file_name = (
        "note_"
        + user_data_generation.generate_random_string(5)
        + random.choice(extensions)
    )

    edit_type = random.choice(["header", "footer", "replace"])

    params = {
        "file_name": random_file_name,
        "edit_type": edit_type,
    }

    if edit_type == "header":
      params["header"] = generate_random_sentence()
    elif edit_type == "footer":
      params["footer"] = generate_random_sentence()
    elif edit_type == "replace":
      params["replace_text"] = "\n".join(
          [generate_random_sentence() for _ in range(3)]
      )

    return params


class MarkorDeleteNote(Markor):
  """Task for checking that a note in Markor has been deleted."""

  complexity = 1
  schema = file_validators.DeleteFile.schema
  template = "Delete the note in Markor named {file_name}."

  def __init__(self, params: dict[str, Any]):
    """Initialize the task."""
    super().__init__(params)
    self.delete_file_task = file_validators.DeleteFile(
        params, device_constants.MARKOR_DATA
    )

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    self.delete_file_task.initialize_task(env)

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    return self.delete_file_task.is_successful(env)

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    file_name = user_data_generation.generate_random_file_name()
    return {"file_name": file_name, "noise_candidates": _NOTE_TITLES}

  def tear_down(self, env: interface.AsyncEnv) -> None:
    super().tear_down(env)
    self.delete_file_task.tear_down(env)


class MarkorDeleteNewestNote(Markor):
  """Task for deleting the newest note in Markor."""

  complexity = 1
  schema = {}
  template = "Delete the newest note in Markor."

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    # Generate some random notes in Markor.
    for _ in range(random.randint(2, 6)):
      note = _generate_random_note()
      file_utils.create_file(
          note.name,
          device_constants.MARKOR_DATA,
          env.controller,
          content=note.content,
      )
      # Advance system time so the change time for these initial notes can be
      # separated.
      datetime_utils.advance_system_time(
          datetime.timedelta(minutes=random.randint(-500, 500)), env.controller
      )

    file_list = file_utils.get_file_list_with_metadata(
        device_constants.MARKOR_DATA, env.controller
    )
    self.initial_file_list_sorted = sorted(
        file_list, key=lambda f: f.change_time
    )

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    new_file_list = file_utils.get_file_list_with_metadata(
        device_constants.MARKOR_DATA, env.controller
    )
    new_file_list_sorted = sorted(new_file_list, key=lambda f: f.change_time)
    for i in range(len(new_file_list)):
      # Both file lists are ordered by file change time, so by simply checking
      # file names and their change time are the same, we can ensure all other
      # files have not been changed.
      if not (
          new_file_list_sorted[i].file_name
          == self.initial_file_list_sorted[i].file_name
          and new_file_list_sorted[i].change_time
          == self.initial_file_list_sorted[i].change_time
      ):
        return 0.0
    one_fewer_file = (
        len(new_file_list_sorted) == len(self.initial_file_list_sorted) - 1
    )
    return 1.0 if one_fewer_file else 0.0

  @classmethod
  def generate_random_params(cls) -> dict[str, str | int]:
    return {}


class MarkorDeleteAllNotes(Markor):
  """Task for deleting all notes in Markor."""

  # For this task's complexity, the agent may complete this task by deleting the
  # files one-by-one which envolves many steps (more than 10), but there is also
  # an optimal approach by first long pressing one file, then tapping to select
  # all others and deleting them all together.
  complexity = 1.4
  schema = {}
  template = "Delete all my notes in Markor."

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    user_data_generation.generate_noise_files(
        user_data_generation.generate_random_string(5),
        device_constants.MARKOR_DATA,
        env.controller,
        _NOTE_TITLES,
        random.randint(2, 6),
    )

    file_list = file_utils.get_file_list_with_metadata(
        device_constants.MARKOR_DATA, env.controller
    )

    if not file_list:
      raise RuntimeError("Something went wrong, file was not created.")

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    file_list = file_utils.get_file_list_with_metadata(
        device_constants.MARKOR_DATA, env.controller
    )
    return 0.0 if file_list else 1.0

  @classmethod
  def generate_random_params(cls) -> dict[str, str | int]:
    return {}


class MarkorCreateNote(Markor):
  """Task for checking that a new note in Markor has been created with a specific name and text."""

  app_names = ("markor",)
  complexity = 1.6
  schema = file_validators.CreateFile.schema
  template = (
      "Create a new note in Markor named {file_name} with the following text:"
      " {text}"
  )

  def __init__(self, params: dict[str, Any]):
    """See base class."""
    super().__init__(params)

    self.create_file_task = file_validators.CreateFile(
        params, device_constants.MARKOR_DATA
    )

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    self.create_file_task.initialize_task(env)  # Delegate

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    return self.create_file_task.is_successful(env)  # Delegate

  @classmethod
  def generate_random_params(cls) -> dict[str, str | int]:
    note = _generate_random_note()
    return {"file_name": note.name, "text": note.content}

  def tear_down(self, env: interface.AsyncEnv) -> None:
    super().tear_down(env)
    self.create_file_task.tear_down(env)


class MarkorCreateNoteFromClipboard(Markor):
  """Task for creating a note using text in clipboard in Markor."""

  app_names = ("markor", "clipper")
  complexity = 1.4
  schema = {
      "type": "object",
      "properties": {
          "file_name": {"type": "string"},
          "file_content": {"type": "string"},
      },
      "required": ["file_name", "file_content"],
  }
  template = (
      "Create a note in Markor named {file_name}. Perform a paste operation in"
      " the note and save the note."
  )

  def __init__(self, params: dict[str, Any]):
    """Initialize the task."""
    super().__init__(params)
    if "file_content" not in params or not params["file_content"]:
      params["file_content"] = user_data_generation.generate_random_string(20)
    self.create_file_task = file_validators.CreateFile(
        {"file_name": params["file_name"], "text": params["file_content"]},
        device_constants.MARKOR_DATA,
    )

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    adb_utils.set_clipboard_contents(
        self.params["file_content"], env.controller
    )
    if (
        adb_utils.get_clipboard_contents(env.controller)
        != self.params["file_content"]
    ):
      raise RuntimeError(
          "Something went wrong, clipboard not set up correctly."
      )
    self.create_file_task.initialize_task(env)

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    return self.create_file_task.is_successful(env)

  @classmethod
  def generate_random_params(cls) -> dict[str, str | int]:
    return {
        "file_name": _generate_random_note().name,
        "file_content": user_data_generation.generate_random_string(10),
    }

  def tear_down(self, env: interface.AsyncEnv) -> None:
    super().tear_down(env)
    self.create_file_task.tear_down(env)


class MarkorMergeNotes(Markor):
  """Task for merging three existing notes into a new one."""

  complexity = 7.8
  schema = {
      "type": "object",
      "properties": {
          "file1_name": {"type": "string"},
          "file2_name": {"type": "string"},
          "file3_name": {"type": "string"},
          "new_file_name": {"type": "string"},
          "file1_content": {"type": "string"},
          "file2_content": {"type": "string"},
          "file3_content": {"type": "string"},
      },
      "required": [
          "file1_name",
          "file2_name",
          "file3_name",
          "new_file_name",
          "file1_content",
          "file2_content",
          "file3_content",
      ],
  }
  template = (
      "Merge the contents of Markor notes {file1_name}, {file2_name} and"
      " {file3_name} (in the same order) into a new Markor note named"
      " {new_file_name} and save it. Add a new line between the content of each"
      " note."
  )

  def __init__(self, params: dict[str, Any]):
    """Initialize the task."""
    super().__init__(params)
    self.create_file_task = file_validators.CreateFile(
        {
            "file_name": params["new_file_name"],
            # file_util.create_file with non-empty content will add a \n to the
            # end of the file.
            "text": (
                "\n\n".join([
                    self.params["file1_content"],
                    self.params["file2_content"],
                    self.params["file3_content"],
                ])
                + "\n"
            ),
        },
        device_constants.MARKOR_DATA,
    )

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    self.create_file_task.initialize_task(env)
    file_utils.create_file(
        self.params["file1_name"],
        device_constants.MARKOR_DATA,
        env.controller,
        content=self.params["file1_content"],
    )
    file_utils.create_file(
        self.params["file2_name"],
        device_constants.MARKOR_DATA,
        env.controller,
        content=self.params["file2_content"],
    )
    file_utils.create_file(
        self.params["file3_name"],
        device_constants.MARKOR_DATA,
        env.controller,
        content=self.params["file3_content"],
    )

  def tear_down(self, env: interface.AsyncEnv) -> None:
    super().tear_down(env)
    file_utils.remove_single_file(
        self.params["file1_name"],
        device_constants.MARKOR_DATA,
        env.controller,
    )
    file_utils.remove_single_file(
        self.params["file2_name"],
        device_constants.MARKOR_DATA,
        env.controller,
    )
    file_utils.remove_single_file(
        self.params["file3_name"],
        device_constants.MARKOR_DATA,
        env.controller,
    )
    self.create_file_task.tear_down(env)

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    if not self.create_file_task.is_successful(env):
      return 0.0
    # The CreateFile task is using a fuzzy match in its is_successful function,
    # but here we want to explicitly check if the agent adds a blank line
    # between the notes. The following check only works based on the current way
    # we generate notes with the assumption that each file's content is a string
    # of length less than 20, consisting of letters and digits, ended with a \n.
    merged_file = (
        adb_utils.issue_generic_request(
            [
                "shell",
                "cat",
                file_utils.convert_to_posix_path(
                    device_constants.MARKOR_DATA, self.params["new_file_name"]
                ),
            ],
            env.controller,
        )
        .generic.output.decode()
        .replace("\r", "")
        .strip()
    )

    # merged_file should look like,
    # file1\n\nfile2\n\nfile3, where the first and third \n are inserted by
    # create_file in file_utils, the second and the forth \n should be inserted
    # by agent.
    content_split = merged_file.split("\n")
    are_notes_merged = (
        len(content_split) == 5
        and (not content_split[1])
        and (not content_split[3])
    )
    return 1.0 if are_notes_merged else 0.0

  @classmethod
  def generate_random_params(cls) -> dict[str, str | int]:
    return {
        "file1_name": _generate_random_note().name,
        "file2_name": _generate_random_note().name,
        "file3_name": _generate_random_note().name,
        "new_file_name": user_data_generation.generate_random_string(8),
        "file1_content": user_data_generation.generate_random_string(20),
        "file2_content": user_data_generation.generate_random_string(20),
        "file3_content": user_data_generation.generate_random_string(20),
    }


class MarkorChangeNoteContent(Markor):
  """Task for changing an existing note's content and renaming it."""

  complexity = 1.2
  schema = {
      "type": "object",
      "properties": {
          "original_name": {"type": "string"},
          "new_name": {"type": "string"},
          "updated_content": {"type": "string"},
      },
      "required": ["original_name", "new_name", "updated_content"],
  }
  template = (
      'Update the content of {original_name} to "{updated_content}" in Markor'
      " and change its name to {new_name}."
  )

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    file_utils.create_file(
        self.params["original_name"],
        device_constants.MARKOR_DATA,
        env.controller,
        content=user_data_generation.generate_random_string(20),
    )
    user_data_generation.generate_noise_files(
        self.params["original_name"],
        device_constants.MARKOR_DATA,
        env.controller,
        _NOTE_TITLES,
    )
    if not file_utils.check_file_or_folder_exists(
        self.params["original_name"],
        device_constants.MARKOR_DATA,
        env.controller,
    ):
      raise RuntimeError("Something went wrong, file not created correctly.")

  def tear_down(self, env: interface.AsyncEnv) -> None:
    super().tear_down(env)
    file_utils.remove_single_file(
        self.params["original_name"],
        device_constants.MARKOR_DATA,
        env.controller,
    )

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    if file_utils.check_file_or_folder_exists(
        self.params["original_name"],
        device_constants.MARKOR_DATA,
        env.controller,
    ):
      return 0.0
    if not file_utils.check_file_or_folder_exists(
        self.params["new_name"],
        device_constants.MARKOR_DATA,
        env.controller,
    ):
      return 0.0
    content_updated = file_utils.check_file_content(
        file_utils.convert_to_posix_path(
            device_constants.MARKOR_DATA, self.params["new_name"]
        ),
        self.params["updated_content"],
        env.controller,
    )
    return 1.0 if content_updated else 0.0

  @classmethod
  def generate_random_params(cls) -> dict[str, str | int]:
    original = _generate_random_note().name
    new = _generate_random_note().name
    return {
        "original_name": original,
        "new_name": new,
        "updated_content": user_data_generation.generate_random_string(20),
    }


class MarkorAddNoteHeader(Markor):
  """Task for adding a header to an existing note and renaming it."""

  complexity = 1.2
  schema = {
      "type": "object",
      "properties": {
          "original_name": {"type": "string"},
          "new_name": {"type": "string"},
          "header": {"type": "string"},
          "original_content": {"type": "string"},
      },
      "required": ["original_name", "new_name", "header", "original_content"],
  }
  template = (
      "Update the Markor note {original_name} by adding the following text,"
      ' along with a new blank line before the existing content: "{header}",'
      " and rename it to {new_name}."
  )

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    file_utils.create_file(
        self.params["original_name"],
        device_constants.MARKOR_DATA,
        env.controller,
        content=self.params["original_content"],
    )
    user_data_generation.generate_noise_files(
        self.params["original_name"],
        device_constants.MARKOR_DATA,
        env.controller,
        _NOTE_TITLES,
    )

    if not file_utils.check_file_or_folder_exists(
        self.params["original_name"],
        device_constants.MARKOR_DATA,
        env.controller,
    ):
      raise RuntimeError("Something went wrong, file not created correctly.")

  def tear_down(self, env: interface.AsyncEnv) -> None:
    super().tear_down(env)
    file_utils.remove_single_file(
        self.params["original_name"],
        device_constants.MARKOR_DATA,
        env.controller,
    )

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    if file_utils.check_file_or_folder_exists(
        self.params["original_name"],
        device_constants.MARKOR_DATA,
        env.controller,
    ):
      return 0.0
    if not file_utils.check_file_or_folder_exists(
        self.params["new_name"],
        device_constants.MARKOR_DATA,
        env.controller,
    ):
      return 0.0
    correct = file_utils.check_file_content(
        file_utils.convert_to_posix_path(
            device_constants.MARKOR_DATA, self.params["new_name"]
        ),
        self.params["header"] + "\n\n" + self.params["original_content"] + "\n",
        env.controller,
        exact_match=True,
    )
    return 1.0 if correct else 0.0

  @classmethod
  def generate_random_params(cls) -> dict[str, str | int]:
    return {
        "original_name": _generate_random_note().name,
        "original_content": generate_random_sentence(),
        "new_name": _generate_random_note().name,
        "header": user_data_generation.generate_random_string(20),
    }


class MarkorTranscribeReceipt(task_eval.TaskEval):
  """Task for creating a markdown file from a receipt image using Simple Gallery and Markor.

  This task involves viewing a receipt image in Simple Gallery and then
  creating a markdown file in Markor with details of the transactions
  listed in the image. The file should be named 'receipt.md' and include
  transactions with the format "Date, Item, Amount".
  """

  app_names = ("simple gallery pro", "markor")
  complexity = 1.8
  template = (
      "Create a file in Markor, called receipt.md with the transactions from"
      " the receipt.png. Use Simple Gallery to view the receipt. Please enter"
      ' transactions in csv format including the header "Date, Item, Amount".'
  )

  schema = file_validators.CreateFile.schema

  def __init__(self, params: dict[str, Any]):
    super().__init__(params)
    self.img = params.pop("img")
    self.create_file_task = file_validators.CreateFile(
        params, device_constants.MARKOR_DATA
    )

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    """Initializes the task for creating a receipt markdown file."""
    super().initialize_task(env)
    self.create_file_task.initialize_task(env)
    receipt_img_path = file_utils.convert_to_posix_path(
        file_utils.get_local_tmp_directory(), "receipt.png"
    )
    self.img.save(receipt_img_path)
    file_utils.copy_data_to_device(
        receipt_img_path,
        device_constants.GALLERY_DATA,
        env.controller,
    )

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    return self.create_file_task.is_successful(env)

  def tear_down(self, env: interface.AsyncEnv):
    super().tear_down(env)
    self.create_file_task.tear_down(env)

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    img, text = receipt_generator.create_receipt(random.randint(1, 5))
    text = "\n".join(text.split("\n")[2:])  # Remove header.
    return {
        "img": img,
        "file_name": "receipt.md",
        "text": text,
    }


class MarkorTranscribeVideo(Markor):
  """Task for transcribing a video using Markor."""

  complexity = 2
  schema = file_validators.CreateFile.schema
  app_names = ("markor", "vlc")

  template = (
      "Transcribe the contents of video {video_name} by watching it in VLC"
      " player (located in Download) and writing the sequence of strings shown"
      " on each frame to the text file {file_name} in Markor as a comma"
      ' separated list. For example, if the first frame shows the text "edna"'
      ' and the second frame shows the text "pineapple", then the text file'
      ' should contain only the following text: "edna, pineapple".'
  )

  def __init__(self, params: dict[str, Any]):
    super().__init__(params)
    self.create_file_task = file_validators.CreateFile(
        params, device_constants.MARKOR_DATA
    )

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    super().initialize_task(env)
    self.create_file_task.initialize_task(env)
    user_data_generation.write_video_file_to_device(
        self.params["video_name"],
        device_constants.DOWNLOAD_DATA,
        env,
        messages=self.params["messages"],
        message_display_time=8,
    )
    for file in self.params["noise_files"]:
      user_data_generation.write_video_file_to_device(
          file,
          device_constants.DOWNLOAD_DATA,
          env,
          messages=[user_data_generation.generate_random_string(10)],
          fps=1,
          message_display_time=random.randint(20, 180),
      )

  def is_successful(self, env: interface.AsyncEnv) -> float:
    super().is_successful(env)
    return self.create_file_task.is_successful(env)

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    messages = list(
        random.sample(
            user_data_generation.COMMON_GIVEN_NAMES, random.randint(2, 4)
        )
    )
    video_name = vlc.generate_file_name()
    text_file_name = f"{video_name.split('.')[0]}_transcription.txt"
    return {
        "file_name": text_file_name,
        "text": ",".join(messages),
        # Video specific.
        "messages": messages,
        "video_name": video_name,
        "noise_files": [
            vlc.generate_file_name() for _ in range(random.randint(5, 20))
        ],
    }

_NOTE_TITLES = [
    "grocery_list_weekly.md",
    "meeting_notes_project_team.md",
    "personal_goals_2024.md",
    "reading_list_2024.md",
    "research_paper_summary.md",
    "summer_vacation_plans.md",
    "budget_home_renovation.md",
    "april_workout_routine.md",
    "birthday_gift_ideas_mom.md",
    "recipe_homemade_pizza.md",
    "weekend_todo_list.md",
    "insurance_plan_comparison.md",
    "art_project_sketches.md",
    "python_learning_goals.md",
    "trip_reflections_recent.md",
    "startup_ideas_launch.md",
    "client_meetings_schedule.md",
    "favorite_book_quotes.md",
    "garden_layout_plan.md",
    "upcoming_presentation_outline.md",
]
```

### `derived/selected_task_source.json`

Source ref: `androidworld://MarkorCreateNoteAndSms`

```json
{
  "base_class_name": "Markor",
  "base_module": "android_world.task_evals.single.markor",
  "base_source_file": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/markor.py",
  "case_unit_id": "MarkorCreateNoteAndSms",
  "class_name": "MarkorCreateNoteAndSms",
  "difficulty": "hard",
  "module": "android_world.task_evals.composite.markor_sms",
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
      "archive_path": "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/composite/markor_sms.py",
      "sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/composite/markor_sms.py"
    },
    {
      "archive_path": "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/markor.py",
      "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/markor.py"
    }
  ],
  "optimal_steps": "9",
  "packet_files": [
    "official/install/android_world/task_metadata.json",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/composite/markor_sms.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/markor.py",
    "derived/selected_task_source.json"
  ],
  "selection_order_key": "20932dfd31d1168720799e18d4ce8acb9ca23314d1893077e617cc3f61b2d672",
  "selection_rank": 14,
  "source_file": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/composite/markor_sms.py",
  "source_ref": "androidworld://MarkorCreateNoteAndSms",
  "source_sha256": "bd5d9f85527296fd6a532085a9304b436fdc8ea7c1e34668ad732f3f2920a41e",
  "tags": [
    "multi_app",
    "data_entry",
    "parameterized"
  ],
  "task_id": "MarkorCreateNoteAndSms",
  "task_name": "MarkorCreateNoteAndSms",
  "task_template": "Create a new note in Markor named {file_name} with the following text: {text}. Share the entire content of the note with the phone number {number} via SMS using Simple SMS Messenger"
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "MarkorCreateNoteAndSms",
  "copied_files": [
    "derived/selected_task_source.json",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/composite/markor_sms.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/markor.py",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_metadata.json"
  ],
  "derived_files": [
    "derived/selected_task_source.json"
  ],
  "domain": "androidworld",
  "file_sources": {
    "derived/selected_task_source.json": "androidworld://MarkorCreateNoteAndSms",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/composite/markor_sms.py": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/composite/markor_sms.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/markor.py": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/markor.py",
    "official/install/android_world/registry.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_metadata.json": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json"
  },
  "official_files": [
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/composite/markor_sms.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/markor.py",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_metadata.json"
  ],
  "packet_files": [
    "official/install/android_world/task_metadata.json",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/composite/markor_sms.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/markor.py",
    "derived/selected_task_source.json"
  ],
  "sha256_per_file": {
    "derived/selected_task_source.json": "156051975e6db710a408a8afa7fb95f071487f9541d14e408397eaff90af32a2",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/composite/markor_sms.py": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/markor.py": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
    "official/install/android_world/registry.py": "47380849f428b231747365ac8ba50a83212cdc34180ab6376ff49e90b93af12b",
    "official/install/android_world/task_evals/task_eval.py": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
    "official/install/android_world/task_metadata.json": "fd3cf23ebb26e461a961dd60ff3f011d7e6ec78c992c10babbbdb86f9dd591e1"
  },
  "source_refs": [
    "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/composite/markor_sms.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/markor.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json",
    "androidworld://MarkorCreateNoteAndSms"
  ],
  "task_id": "MarkorCreateNoteAndSms"
}
```
