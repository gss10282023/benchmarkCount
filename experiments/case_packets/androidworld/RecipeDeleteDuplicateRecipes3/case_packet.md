# Case Packet

## Case Metadata

- domain: `androidworld`
- case_unit_id: `RecipeDeleteDuplicateRecipes3`
- task_id: `RecipeDeleteDuplicateRecipes3`

## Source Inventory

- `official/install/android_world/task_metadata.json`
- `official/install/android_world/registry.py`
- `official/install/android_world/task_evals/task_eval.py`
- `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py`
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

### `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py`

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

"""Tasks for recipes app."""

import dataclasses
import random
from typing import Any
from android_world.env import device_constants
from android_world.env import interface
from android_world.task_evals.common_validators import sqlite_validators
from android_world.task_evals.utils import sqlite_schema_utils
from android_world.task_evals.utils import user_data_generation
from android_world.utils import file_utils


_DB_PATH = '/data/data/com.flauschcode.broccoli/databases/broccoli'
_TABLE_NAME = 'recipes'
_APP_NAME = 'broccoli app'
_DB_KEY = 'recipeId'

# How to represent recipes in text form (csv or block of text) for generated
# files.
_TEXT_REPRESENTATION_TYPE = 'text_representation_type'


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


class RecipeDeleteDuplicateRecipes(
    sqlite_validators.DeleteDuplicateRows, _RecipeApp
):
  """Deduplicate recipes from Broccoli Recipe App."""

  complexity = 1
  n_rows = 1
  n_rows_noise = 5

  @property
  def goal(self) -> str:
    return (
        'Delete all but one of any recipes in the Broccoli app that are exact'
        ' duplicates, ensuring at least one instance of each unique recipe'
        ' remains'
    )

  def validate_deletion_integrity(
      self,
      before: list[sqlite_schema_utils.Recipe],
      after: list[sqlite_schema_utils.Recipe],
  ) -> bool:
    """Validates the integrity of the recipe deletion."""
    target1, target2 = self.rows_to_delete
    return sqlite_validators.validate_rows_removal_integrity(
        before, after, [target1.recipeId], self.db_key
    ) or sqlite_validators.validate_rows_removal_integrity(
        before, after, [target2.recipeId], self.db_key
    )

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for a remove recipe task."""

    rows = sqlite_schema_utils.get_random_items(
        cls.n_rows_noise + cls.n_rows,
        _generate_random_recipe,
        replacement=False,
    )
    target = rows.pop()
    return {
        sqlite_validators.ROW_OBJECTS: [target, target],
        sqlite_validators.NOISE_ROW_OBJECTS: rows,
    }


class RecipeDeleteDuplicateRecipes2(RecipeDeleteDuplicateRecipes):
  """Medium hard deduplication task, with more noise events."""

  complexity = 2.4
  n_rows = 1
  n_rows_noise = 10

  @property
  def goal(self) -> str:
    return (
        'Delete all but one of any recipes in the Broccoli app that are exact'
        ' duplicates, ensuring at least one instance of each unique recipe'
        ' remains'
    )

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for a remove recipe task."""
    noise = sqlite_schema_utils.get_random_items(
        7,
        _generate_random_recipe,
        replacement=False,
    )

    target = noise.pop()

    # Add variations of target recipe, with different properties.
    while len(noise) < cls.n_rows_noise:
      value = sqlite_schema_utils.get_random_items(
          1,
          _generate_random_recipe,
          replacement=True,
          filter_fn=lambda r: r.title == target.title,
      )[0]
      if value != target:
        noise.append(value)

    return {
        sqlite_validators.ROW_OBJECTS: [target, target],
        sqlite_validators.NOISE_ROW_OBJECTS: noise,
    }


class RecipeDeleteDuplicateRecipes3(RecipeDeleteDuplicateRecipes):
  """Harder deduplication task, with more noise events and agent must scroll."""

  complexity = 3.4
  n_rows = 1
  n_rows_noise = 30

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for a remove recipe task."""
    noise = sqlite_schema_utils.get_random_items(
        22,
        _generate_random_recipe,
        replacement=False,
        filter_fn=lambda r: r.title != 'Avocado Toast with Egg',
    )

    target = noise.pop()

    # Add noise at the top of the recipe screen, requiring agent to scroll.
    noise += sqlite_schema_utils.get_random_items(
        3,
        _generate_random_recipe,
        replacement=False,
        filter_fn=lambda r: r.title == 'Avocado Toast with Egg',
    )

    # Add variations of target recipe, with different properties.
    while len(noise) < cls.n_rows_noise:
      value = sqlite_schema_utils.get_random_items(
          1,
          _generate_random_recipe,
          replacement=True,
          filter_fn=lambda r: (
              r.title == target.title and r.description == target.description
          ),
      )[0]
      if value != target:
        noise.append(value)

    return {
        sqlite_validators.ROW_OBJECTS: [target, target],
        sqlite_validators.NOISE_ROW_OBJECTS: noise,
    }


def _get_rows_as_text(
    rows: list[sqlite_schema_utils.Recipe],
    format_type: str,
    wrap_width: int | None = None,
) -> str:
  return sqlite_schema_utils.get_text_representation_of_rows(
      rows,
      [
          'title',
          'description',
          'servings',
          'preparationTime',
          'ingredients',
          'directions',
      ],
      format_type,
      'title',
      wrap_width=wrap_width,
  )


class _RecipeAddMultipleRecipes(sqlite_validators.AddMultipleRows, _RecipeApp):
  """Task to delete multiple recipes in Broccoli Recipe App."""

  complexity = 3
  n_rows = 3
  n_rows_noise = 10

  @property
  def goal(self) -> str:
    text_repr = _get_rows_as_text(
        self.params[sqlite_validators.ROW_OBJECTS],
        self.params[_TEXT_REPRESENTATION_TYPE],
    )
    return f'Add the following recipes into the Broccoli app:\n{text_repr}'

  def validate_addition_integrity(
      self,
      before: list[sqlite_schema_utils.Recipe],
      after: list[sqlite_schema_utils.Recipe],
      reference_rows: list[sqlite_schema_utils.RowType],
  ) -> bool:
    """Validates the integrity of the recipe deletion."""
    return sqlite_validators.validate_rows_addition_integrity(
        before,
        after,
        reference_rows,
        compare_fields=[
            'title',
            'description',
            'servings',
            'preparationTime',
            'source',
            'ingredients',
            'directions',
            'favorite',
        ],
        free_form_fields=[
            'title',
            'description',
            'servings',
            'preparationTime',
            'source',
            'ingredients',
            'directions',
        ],
    )

  @classmethod
  def _get_random_target_row(cls) -> sqlite_schema_utils.Recipe:
    """Currently unused."""
    return _generate_random_recipe()

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for an add recipe task."""
    target_rows = sqlite_schema_utils.get_random_items(
        cls.n_rows,
        _generate_random_recipe,
        replacement=False,
    )
    noise_rows = sqlite_schema_utils.get_random_items(
        cls.n_rows_noise,
        _generate_random_recipe,
        replacement=False,
        filter_fn=lambda r: any([r.title != t.title for t in target_rows]),
    )
    return {
        sqlite_validators.ROW_OBJECTS: target_rows,
        sqlite_validators.NOISE_ROW_OBJECTS: noise_rows,
        _TEXT_REPRESENTATION_TYPE: random.choice(['csv', 'text_block']),
    }


class RecipeAddSingleRecipe(_RecipeAddMultipleRecipes):
  """Task to delete a single recipe in Broccoli Recipe App."""

  complexity = 2.4
  n_rows = 1
  n_rows_noise = 10


class RecipeAddMultipleRecipes(_RecipeAddMultipleRecipes):
  """Task to delete multiple recipes in Broccoli Recipe App."""

  complexity = 6
  n_rows = 3
  n_rows_noise = 10


class RecipeAddMultipleRecipesFromMarkor(_RecipeAddMultipleRecipes):
  """Task to add multiple recipes from a text file to Broccoli Recipe App."""

  complexity = 6
  n_rows = 3
  n_rows_noise = 10
  app_names = (_APP_NAME, 'markor')

  @property
  def goal(self) -> str:
    return (
        'Add the recipes from recipes.txt in Markor to the Broccoli recipe app.'
    )

  def initialize_task(self, env: interface.AsyncEnv):
    super().initialize_task(env)
    file_utils.clear_directory(device_constants.MARKOR_DATA, env.controller)
    user_data_generation.write_to_markor(
        _get_rows_as_text(
            self.params[sqlite_validators.ROW_OBJECTS],
            self.params[_TEXT_REPRESENTATION_TYPE],
        ),
        'recipes.txt',
        env,
    )

  def tear_down(self, env: interface.AsyncEnv):
    super().tear_down(env)
    file_utils.clear_directory(device_constants.MARKOR_DATA, env.controller)


class RecipeAddMultipleRecipesFromMarkor2(RecipeAddMultipleRecipesFromMarkor):
  """Harder add recipe task, that involves navigating a large text file."""

  n_rows = 3
  n_rows_noise = 40
  complexity = 6

  @property
  def goal(self) -> str:
    prep_time = self.params['prep_time']
    return (
        f'Add the recipes from recipes.txt in Markor that take {prep_time} to '
        'prepare into the Broccoli recipe app.'
    )

  def initialize_task(self, env: interface.AsyncEnv):
    super().initialize_task(env)
    rows = (
        self.params[sqlite_validators.ROW_OBJECTS]
        + self.params[sqlite_validators.NOISE_ROW_OBJECTS]
    )
    random.shuffle(rows)
    file_utils.clear_directory(device_constants.MARKOR_DATA, env.controller)
    user_data_generation.write_to_markor(
        _get_rows_as_text(
            rows,
            self.params[_TEXT_REPRESENTATION_TYPE],
        ),
        'recipes.txt',
        env,
    )

  def tear_down(self, env: interface.AsyncEnv):
    super().tear_down(env)
    file_utils.clear_directory(device_constants.MARKOR_DATA, env.controller)

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    """Generate random parameters for an add recipe task."""
    prep_time = random.choice(_PREP_TIME_OPTIONS)
    target_rows = sqlite_schema_utils.get_random_items(
        cls.n_rows,
        _generate_random_recipe,
        replacement=False,
        filter_fn=lambda r: r.preparationTime == prep_time,
    )
    noise_rows = sqlite_schema_utils.get_random_items(
        cls.n_rows_noise,
        _generate_random_recipe,
        replacement=False,
        filter_fn=lambda r: r.preparationTime != prep_time,
    )
    return {
        sqlite_validators.ROW_OBJECTS: target_rows,
        sqlite_validators.NOISE_ROW_OBJECTS: noise_rows,
        _TEXT_REPRESENTATION_TYPE: random.choice(['csv', 'text_block']),
        'prep_time': prep_time,
    }


class RecipeAddMultipleRecipesFromImage(_RecipeAddMultipleRecipes):
  """Task to add multiple recipes from an image file to Broccoli Recipe App."""

  app_names = (_APP_NAME, 'simple gallery pro')
  complexity = 6
  n_rows = 3
  n_rows_noise = 10

  @property
  def goal(self) -> str:
    return (
        'Add the recipes from recipes.jpg in Simple Gallery Pro to the Broccoli'
        ' recipe app.'
    )

  def initialize_task(self, env: interface.AsyncEnv):
    super().initialize_task(env)
    user_data_generation.clear_device_storage(env)
    data = _get_rows_as_text(
        self.params[sqlite_validators.ROW_OBJECTS], 'text_block', wrap_width=60
    )
    user_data_generation.write_to_gallery(data, 'recipes.jpg', env)

  def tear_down(self, env: interface.AsyncEnv):
    super().tear_down(env)
    user_data_generation.clear_device_storage(env)

#### Utility functions used for generating recipes #############################


def _generate_random_recipe() -> sqlite_schema_utils.Recipe:
  """Generates a random recipe."""

  descriptions = [
      'A quick and easy meal, perfect for busy weekdays.',
      'A delicious and healthy choice for any time of the day.',
      (
          'An ideal recipe for experimenting with different flavors and'
          ' ingredients.'
      ),
  ]
  directions_additions = [
      'Try adding a pinch of your favorite spices for extra flavor.',
      'Feel free to substitute with ingredients you have on hand.',
      'Garnish with fresh herbs for a more vibrant taste.',
  ]
  ingredient_descriptors = [
      'see directions',
      'as per recipe',
      'varies',
      'to preference',
      'quantities to taste',
      'as needed',
      'optional ingredients',
      'n/a',
      'various amounts',
      'adjustable',
      'to your liking',
      'flexible ingredients',
      'per individual taste',
      'as desired',
      'subject to change',
  ]

  recipe = random.choice(_RECIPES)

  return dataclasses.replace(
      recipe,
      description=random.choice(descriptions),
      servings=random.choice(_SERVINGS_OPTIONS),
      preparationTime=random.choice(_PREP_TIME_OPTIONS),
      directions=f'{recipe.directions} {random.choice(directions_additions)}',
      ingredients=random.choice(ingredient_descriptors),
  )


_RECIPES = [
    sqlite_schema_utils.Recipe(
        title='Spicy Tuna Wraps',
        directions=(
            'Mix canned tuna with mayo and sriracha. Spread on tortillas, add'
            ' lettuce and cucumber slices, roll up.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Avocado Toast with Egg',
        directions=(
            'Toast bread, top with mashed avocado, a fried egg, salt, pepper,'
            ' and chili flakes.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Greek Salad Pita Pockets',
        directions=(
            'Fill pita pockets with lettuce, cucumber, tomato, feta, olives,'
            ' and Greek dressing.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Quick Fried Rice',
        directions=(
            'Sauté cooked rice with vegetables, add soy sauce and scrambled'
            ' eggs. Toss until hot.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Pesto Pasta with Peas',
        directions=(
            'Cook pasta, stir in pesto sauce and cooked peas. Add Parmesan'
            ' cheese before serving.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='BBQ Chicken Quesadillas',
        directions=(
            'Mix shredded cooked chicken with BBQ sauce. Place on tortillas'
            ' with cheese, fold and cook until crispy.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Tomato Basil Bruschetta',
        directions=(
            'Top sliced baguette with a mix of chopped tomatoes, basil,'
            ' garlic, olive oil, salt, and pepper.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Lemon Garlic Tilapia',
        directions=(
            'Sauté tilapia in butter, add lemon juice and garlic. Serve with'
            ' steamed vegetables.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Turkey and Cheese Panini',
        directions=(
            'Layer turkey and cheese on bread, grill in a panini press until'
            ' golden.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Veggie and Hummus Sandwich',
        directions=(
            'Spread hummus on bread, add cucumber, bell pepper, carrot, and'
            ' lettuce.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Mango Chicken Curry',
        directions=(
            'Cook chicken pieces in a pan, add onions, garlic, and ginger. Stir'
            ' in curry powder, coconut milk, and mango pieces. Simmer until'
            ' chicken is cooked.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Beef Stir Fry',
        directions=(
            'Stir-fry beef slices with broccoli, bell peppers, and onions in'
            ' soy sauce and garlic. Serve over rice or noodles.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Shrimp Avocado Salad',
        directions=(
            'Mix cooked shrimp with avocado, tomatoes, cucumber, and onion.'
            ' Dress with lime juice, olive oil, salt, and pepper.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Spinach and Feta Stuffed Chicken',
        directions=(
            'Stuff chicken breasts with a mixture of spinach, feta, garlic, and'
            ' herbs. Bake until chicken is cooked through.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Zucchini Noodles with Pesto',
        directions=(
            'Spiralize zucchini into noodles, sauté with garlic, then mix with'
            ' pesto sauce. Top with grated Parmesan cheese.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Cauliflower Fried "Rice"',
        directions=(
            'Pulse cauliflower in a food processor until it resembles rice.'
            ' Sauté with vegetables, soy sauce, and add scrambled eggs.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Sweet Potato and Black Bean Tacos',
        directions=(
            'Roast sweet potato cubes, mix with black beans, and use as filling'
            ' for tacos. Top with avocado and cilantro lime sauce.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Salmon with Dill Sauce',
        directions=(
            'Bake salmon fillets and serve with a sauce made from Greek yogurt,'
            ' dill, lemon juice, and garlic.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Quinoa Salad with Vegetables',
        directions=(
            'Mix cooked quinoa with diced vegetables, feta cheese, and a lemon'
            ' olive oil dressing.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Chickpea Vegetable Soup',
        directions=(
            'Sauté onions, carrots, and celery, add broth, canned tomatoes, and'
            ' chickpeas. Simmer with spinach and seasonings.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Chicken Caesar Salad Wrap',
        directions=(
            'Toss chopped romaine lettuce with Caesar dressing, grilled chicken'
            ' strips, and Parmesan cheese. Wrap in a large tortilla.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Vegetarian Chili',
        directions=(
            'Cook onions, garlic, bell peppers, and carrots. Add canned'
            ' tomatoes, kidney beans, black beans, corn, and chili seasoning.'
            ' Simmer until vegetables are tender.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Pan-Seared Salmon with Quinoa',
        directions=(
            'Pan-sear salmon fillets until crispy. Serve over cooked quinoa'
            ' with a side of steamed asparagus.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Caprese Salad Skewers',
        directions=(
            'Thread cherry tomatoes, basil leaves, and mozzarella balls onto'
            ' skewers. Drizzle with balsamic glaze.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Chicken Alfredo Pasta',
        directions=(
            'Cook fettuccine pasta, toss with Alfredo sauce and grilled chicken'
            ' strips. Serve with a sprinkle of Parmesan cheese.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Stuffed Bell Peppers',
        directions=(
            'Mix cooked quinoa, black beans, corn, tomato sauce, and spices.'
            ' Stuff into bell peppers and bake until tender.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Eggplant Parmesan',
        directions=(
            'Slice eggplant, bread, and fry. Layer in a baking dish with'
            ' marinara sauce and mozzarella cheese. Bake until bubbly.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Thai Peanut Noodle Salad',
        directions=(
            'Toss cooked noodles with a Thai peanut sauce, sliced red bell'
            ' peppers, cabbage, carrots, and cilantro.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Butternut Squash Soup',
        directions=(
            'Sauté onions and garlic, add cubed butternut squash and broth.'
            ' Puree until smooth and season with nutmeg, salt, and pepper.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Baked Cod with Lemon and Dill',
        directions=(
            'Place cod fillets in a baking dish, season with lemon juice, dill,'
            ' salt, and pepper. Bake until fish flakes easily.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Vegetable Stir Fry with Tofu',
        directions=(
            'Stir-fry tofu cubes until golden, add assorted vegetables and a'
            ' stir-fry sauce. Serve over rice or noodles.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Classic Margherita Pizza',
        directions=(
            'Spread pizza dough with tomato sauce, top with slices of'
            ' mozzarella cheese and fresh basil leaves. Bake until crust is'
            ' golden.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Raspberry Almond Smoothie',
        directions=(
            'Blend together raspberries, almond milk, banana, and a scoop of'
            ' almond butter until smooth.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Moroccan Chickpea Stew',
        directions=(
            'Sauté onions, garlic, carrots, and spices. Add canned chickpeas,'
            ' diced tomatoes, and vegetable broth. Simmer until flavors meld.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Kale and Quinoa Salad',
        directions=(
            'Toss chopped kale, cooked quinoa, dried cranberries, sliced'
            ' almonds, and feta cheese with a lemon vinaigrette.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Grilled Cheese with Tomato and Basil',
        directions=(
            'Butter bread slices, layer with cheese, tomato slices, and basil.'
            ' Grill until bread is toasted and cheese is melted.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Sausage and Peppers Skillet',
        directions=(
            'Sauté sliced sausage, bell peppers, and onions until browned.'
            ' Serve with mustard or on a hoagie roll.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Lentil Soup',
        directions=(
            'Cook onions, carrots, celery, garlic, and lentils in vegetable'
            ' broth until lentils are tender. Season with thyme and bay leaves.'
        ),
    ),
    sqlite_schema_utils.Recipe(
        title='Garlic Butter Shrimp',
        directions=(
            'Sauté shrimp in butter and minced garlic until pink. Sprinkle with'
            ' parsley and serve with lemon wedges.'
        ),
    ),
]

_SERVINGS_OPTIONS = [
    '1 serving',
    '2 servings',
    '3-4 servings',
    '6 servings',
    '8 servings',
]
_PREP_TIME_OPTIONS = [
    '10 mins',
    '20 mins',
    '30 mins',
    '45 mins',
    '1 hrs',
    '2 hrs',
    '3 hrs',
    '4 hrs',
]

_COMMON_INGREDIENTS = [
    'tuna',
    'mayonnaise',
    'sriracha',
    'tortillas',
    'lettuce',
    'cucumber',
    'bread',
    'avocado',
    'eggs',
    'salt',
    'pepper',
    'chili flakes',
    'pita bread',
    'tomatoes',
    'feta cheese',
    'olives',
    'Greek dressing',
    'rice',
    'vegetables',
    'soy sauce',
    'pesto sauce',
    'peas',
    'Parmesan cheese',
    'chicken',
    'BBQ sauce',
    'cheese',
    'baguette',
    'basil',
    'garlic',
    'olive oil',
    'tilapia',
    'butter',
    'lemon juice',
    'turkey',
    'hummus',
    'bell peppers',
    'carrots',
    'mango',
    'curry powder',
    'coconut milk',
    'beef',
    'broccoli',
    'onions',
    'shrimp',
    'spinach',
    'herbs',
    'zucchini',
    'cauliflower',
    'sweet potato',
    'black beans',
    'cilantro',
    'Greek yogurt',
    'dill',
    'quinoa',
    'chickpeas',
    'romaine lettuce',
    'Caesar dressing',
    'Parmesan',
    'kidney beans',
    'corn',
    'chili seasoning',
    'asparagus',
    'mozzarella balls',
    'balsamic glaze',
    'fettuccine',
    'Alfredo sauce',
    'quinoa',
    'tomato sauce',
    'eggplant',
    'marinara sauce',
    'mozzarella cheese',
    'noodles',
    'Thai peanut sauce',
    'red bell peppers',
    'cabbage',
    'butternut squash',
    'nutmeg',
    'tofu',
    'pizza dough',
    'mozzarella cheese',
    'raspberries',
    'almond milk',
    'banana',
    'almond butter',
    'lentils',
    'thyme',
    'bay leaves',
    'parsley',
    'lemon wedges',
    # More exotic ingredients that are likely not in the existing recipes.
    'ghee',
    'cardamom',
    'fenugreek',
    'amchur (dry mango powder)',
    'rose water',
    'pomegranate molasses',
    'kaffir lime leaves',
    'galangal',
    'lemongrass',
    'furikake',
    'black garlic',
    'hemp seeds',
    'chia seeds',
    'açai berry',
    'maca powder',
    'spirulina',
    'cassava flour',
    'arrowroot powder',
    'seaweed',
    'escargot',
    'venison',
    'quail eggs',
    'duck fat',
    'morel mushrooms',
    'chanterelle mushrooms',
    'black truffle',
    'edible flowers',
    'salsify',
    'rutabaga',
    'celeriac',
    'finger limes',
]
```

### `derived/selected_task_source.json`

Source ref: `androidworld://RecipeDeleteDuplicateRecipes3`

```json
{
  "base_class_name": "RecipeDeleteDuplicateRecipes",
  "base_module": "android_world.task_evals.single.recipe",
  "base_source_file": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py",
  "case_unit_id": "RecipeDeleteDuplicateRecipes3",
  "class_name": "RecipeDeleteDuplicateRecipes3",
  "difficulty": "medium",
  "module": "android_world.task_evals.single.recipe",
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
  "optimal_steps": "16",
  "packet_files": [
    "official/install/android_world/task_metadata.json",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py",
    "derived/selected_task_source.json"
  ],
  "selection_order_key": "e00fe6ba61655e04683ca976d2cdd4be8f7a980ed19a05ba91d66d45f19f8d09",
  "selection_rank": 98,
  "source_file": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py",
  "source_ref": "androidworld://RecipeDeleteDuplicateRecipes3",
  "source_sha256": "3c1aeee6020398b4274922f33bdab24192b82e6c44d250a26787e832fbdd5168",
  "tags": [
    "data_edit",
    "parameterized"
  ],
  "task_id": "RecipeDeleteDuplicateRecipes3",
  "task_name": "RecipeDeleteDuplicateRecipes3",
  "task_template": "Delete all but one of any recipes in the Broccoli app that are exact duplicates, ensuring at least one instance of each unique recipe remains"
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "RecipeDeleteDuplicateRecipes3",
  "copied_files": [
    "derived/selected_task_source.json",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_metadata.json"
  ],
  "derived_files": [
    "derived/selected_task_source.json"
  ],
  "domain": "androidworld",
  "file_sources": {
    "derived/selected_task_source.json": "androidworld://RecipeDeleteDuplicateRecipes3",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py",
    "official/install/android_world/registry.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_metadata.json": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json"
  },
  "official_files": [
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_metadata.json"
  ],
  "packet_files": [
    "official/install/android_world/task_metadata.json",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py",
    "derived/selected_task_source.json"
  ],
  "sha256_per_file": {
    "derived/selected_task_source.json": "51b626f115b7e6cf409d5edfdd3445bae73dfd9b12442503abb6514aade84043",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674",
    "official/install/android_world/registry.py": "47380849f428b231747365ac8ba50a83212cdc34180ab6376ff49e90b93af12b",
    "official/install/android_world/task_evals/task_eval.py": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
    "official/install/android_world/task_metadata.json": "fd3cf23ebb26e461a961dd60ff3f011d7e6ec78c992c10babbbdb86f9dd591e1"
  },
  "source_refs": [
    "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/recipe.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json",
    "androidworld://RecipeDeleteDuplicateRecipes3"
  ],
  "task_id": "RecipeDeleteDuplicateRecipes3"
}
```
