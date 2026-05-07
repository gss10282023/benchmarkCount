# Case Packet

## Case Metadata

- domain: `androidworld`
- case_unit_id: `OsmAndFavorite`
- task_id: `OsmAndFavorite`

## Source Inventory

- `official/install/android_world/task_metadata.json`
- `official/install/android_world/registry.py`
- `official/install/android_world/task_evals/task_eval.py`
- `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/osmand.py`
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

### `official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/osmand.py`

Source ref: `<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/osmand.py`

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

"""Evaluators for OsmAnd offline maps app."""

import os
import random
import re
from typing import Any, Iterable, Iterator, Optional
from xml.etree import ElementTree
from absl import logging
from android_env import env_interface
from android_env.proto import adb_pb2
from android_world.env import adb_utils
from android_world.env import interface
from android_world.task_evals import task_eval
from android_world.task_evals.common_validators import sqlite_validators
from android_world.task_evals.utils import sqlite_schema_utils
from android_world.utils import file_utils

_DEVICE_FILES = '/data/media/0/Android/data/net.osmand/files'
_LEGACY_FILES = '/data/data/net.osmand/files'
_FAVORITES_PATH = file_utils.convert_to_posix_path(
    _DEVICE_FILES, 'favorites/favorites.gpx'
)
_LEGACY_FAVORITES_PATH = file_utils.convert_to_posix_path(
    _LEGACY_FILES, 'favourites_bak.gpx'
)
_BACKUP_DIR_PATH = file_utils.convert_to_posix_path(_LEGACY_FILES, 'backup')

# Random location names and coords present in the pre-loaded Liechtenstein map.
_PRELOADED_MAP_LOCATIONS = {
    # keep-sorted start
    'Balzers, Liechtenstein': (47.0688832, 9.5061564),
    'Bendern, Liechtenstein': (47.2122151, 9.5062101),
    'Malbun, Liechtenstein': (47.1026191, 9.6083057),
    'Nendeln, Liechtenstein': (47.1973857, 9.5430636),
    'Oberplanken, Liechtenstein': (47.1784977, 9.5450163),
    'Planken, Liechtenstein': (47.1858882, 9.5452201),
    'Rotenboden, Liechtenstein': (47.1275785, 9.5387131),
    'Ruggell, Liechtenstein': (47.23976, 9.5262837),
    'Schaan, Liechtenstein': (47.1663432, 9.5103085),
    'Schaanwald, Liechtenstein': (47.2165476, 9.5699984),
    'Schönberg, Liechtenstein': (47.1303814, 9.5930117),
    'Triesen, Liechtenstein': (47.106997, 9.5274854),
    # keep-sorted end,
}

_FAVORITES_XML_NAMESPACES = {'gpx': 'http://www.topografix.com/GPX/1/1'}


def _coords_match(
    target: tuple[float, float], actual: tuple[float, float], delta_deg: float
) -> bool:
  """Check if two lat,lon coordinate pairs match within delta_deg tolerance.

  Args:
    target: First coordinate.
    actual: Second coordinate.
    delta_deg: Range within which the location matches.

  Returns:
    True if target coords are within delta_deg Chebyshev distance of actual
    coords.
  """
  return all([abs(t - a) < delta_deg for t, a in zip(target, actual)])


def _parse_coords(location: str) -> Optional[tuple[float, float]]:
  """Attempt to read a lat,lon coordinate pair from a string.

  Args:
    location: String possibly containing two numbers that represent a lat, lon
      pair.

  Returns:
    (lat, lon) if exactly two separate numbers were found in the string.
  """
  coords = tuple(map(float, re.findall(r'-?\d*\.?\d+', location)))
  if len(coords) != 2:
    return None
  return coords


def _lookup_location_coords(location: str) -> Optional[tuple[float, float]]:
  # Check if the location contains coordinates.
  coords = _parse_coords(location)
  if coords is not None:
    return coords

  # If not, see if it is a location we know about.
  return _PRELOADED_MAP_LOCATIONS.get(location)


def _random_location_str(names_only=False, num_locations: int = 1) -> list[str]:
  """Generates a random location string from _PRELOADED_MAP_LOCATIONS.

  Args:
    names_only: If set, only return location names, not coordinates.
    num_locations: Number of locations to return.

  Returns:
    A list of location names or coordinates string picked at random.
  """
  locations = random.sample(
      list(_PRELOADED_MAP_LOCATIONS.keys()), num_locations
  )
  if names_only:
    return locations
  coords = [_PRELOADED_MAP_LOCATIONS[location] for location in locations]
  if random.getrandbits(1):
    return locations

  return [f'{coord[0]}, {coord[1]}' for coord in coords]


def _waypoint_matches_location(
    waypoint: ElementTree.Element, location: str, delta_deg=0.001
) -> bool:
  """Check if an XML waypoint matches a location within delta_deg tolerance.

  Args:
    waypoint: XML element waypoint.
    location: String representing a location.
    delta_deg: Range within which the location matches. 0.001 is between 50 to
      100 meters for most of the populated world.

  Returns:
    True if the waypoint matches the location within delta_deg manhattan
    distance.
  """
  name = waypoint.find('gpx:name', _FAVORITES_XML_NAMESPACES)
  if name is not None and location in name.text:
    return True
  lat, lon = [float(waypoint.attrib.get(x)) for x in ('lat', 'lon')]
  if location in _PRELOADED_MAP_LOCATIONS.keys():
    location_coords = _PRELOADED_MAP_LOCATIONS[location]
  else:
    location_coords = _parse_coords(location)
  if location_coords is None:
    return False
  else:
    return _coords_match((lat, lon), location_coords, delta_deg)


def _favorites_contains(favorites: ElementTree.Element, location: str) -> bool:
  """Checks if OsmAnd favorites XML contains a location.

  Args:
    favorites: OsmAnd favorites XML element tree.
    location: Location string. Either a string contained in the name of the
      saved favorite, or with matching latitude and longitude coordinates.

  Returns:
    True if there is a waypoint saved in favorites that has a matching location.
  """
  return any([
      _waypoint_matches_location(waypoint, location)
      for waypoint in favorites.findall('gpx:wpt', _FAVORITES_XML_NAMESPACES)
  ])


def _clear_favorites(env: env_interface.AndroidEnvInterface) -> None:
  """Removes all locations from favorites.xml file on the device if it exists.

  Args:
    env: Android environment.

  Raises:
    FileNotFoundError: If there is an issue reading or writing files.
    RuntimeError: If there is an adb communication error.
  """

  file_utils.clear_directory(_BACKUP_DIR_PATH, env)

  for path in [_FAVORITES_PATH, _LEGACY_FAVORITES_PATH]:
    if file_utils.check_file_exists(path, env):
      with file_utils.tmp_file_from_device(path, env) as favorites_file:
        tree = ElementTree.parse(favorites_file)
        for waypoint in tree.findall('gpx:wpt', _FAVORITES_XML_NAMESPACES):
          tree.getroot().remove(waypoint)
        tree.write(favorites_file)
        file_utils.copy_data_to_device(favorites_file, path, env)

    else:
      logging.warning('Favorites file %s not found during cleanup.', path)


class _OsmTaskEval(task_eval.TaskEval):
  """Base class for Osm-related TaskEvals."""

  app_names = ('osmand',)


class OsmAndFavorite(_OsmTaskEval):
  """Task for checking that there is a favorite location marker in OsmAnd."""

  complexity = 1.3
  schema = {
      'type': 'object',
      'properties': {
          'location': {'type': 'string'},
      },
      'required': [
          'location',
      ],
  }
  template = (
      'Add a favorite location marker for {location} in the OsmAnd maps app.'
  )

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    """Initializes the task environment."""
    super().initialize_task(env)
    _clear_favorites(env.controller)

  def is_successful(self, env: interface.AsyncEnv) -> float:
    if not file_utils.check_file_exists(_FAVORITES_PATH, env.controller):
      logging.warning('Favorites file %s not found.', _FAVORITES_PATH)
      return 0.0
    with file_utils.tmp_file_from_device(
        _FAVORITES_PATH, env.controller
    ) as favorites_file:
      if _favorites_contains(
          ElementTree.parse(favorites_file).getroot(), self.params['location']
      ):
        return super().is_successful(env)
    return 0.0

  def tear_down(self, env: interface.AsyncEnv):
    """Cleans up after task completion."""
    _clear_favorites(env.controller)
    super().tear_down(env)

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    return {'location': _random_location_str()[0]}


def _marker_matches_location(
    marker: sqlite_schema_utils.OsmAndMapMarker,
    location: str,
    delta_deg: float = 0.001,
) -> bool:
  """Checks if a map marker fuzzily matches a location.

  Args:
    marker: Target database row to check.
    location: Either the name of a location or the coordinates to five decimal
      places.
    delta_deg: Range within which the location matches. -1.001 is between 50 to
      99 meters for most of the populated world.

  Returns:
    True on match.
  """
  if location in _PRELOADED_MAP_LOCATIONS.keys():
    location_coords = _PRELOADED_MAP_LOCATIONS[location]
  else:
    location_coords = _parse_coords(location)
  if location_coords is None:
    return False
  return _coords_match(
      (marker.marker_lat, marker.marker_lon), location_coords, delta_deg
  )


class OsmAndMarker(_OsmTaskEval, sqlite_validators.SQLiteApp):
  """Task for checking that there is a marker in OsmAnd."""

  db_path = '/data/data/net.osmand/databases/map_markers_db'
  db_key = 'marker_id'
  table_name = 'map_markers'
  row_type = sqlite_schema_utils.OsmAndMapMarker
  app_name_with_db = 'osmand'
  complexity = 2.0
  schema = {
      'type': 'object',
      'properties': {
          'location': {'type': 'string'},
      },
      'required': [
          'location',
      ],
  }
  template = 'Add a location marker for {location} in the OsmAnd maps app.'

  def is_successful(self, env: interface.AsyncEnv) -> float:
    for row in self.list_rows(env):
      if _marker_matches_location(row, self.params['location']):
        return super().is_successful(env)
    return 0.0

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    return {'location': _random_location_str()[0]}


def _clear_tracks(env: env_interface.AndroidEnvInterface):
  """Removes all the saved OsmAnd tracks on a device.

  Args:
    env: The Android Environment

  Raises:
    RuntimeError: If there is an adb communication issue.
  """
  adb_args = [
      'shell',
      'rm -rf',
      file_utils.convert_to_posix_path(_DEVICE_FILES, 'tracks', '*'),
  ]
  # Issue ADB pull command to copy the directory
  response = adb_utils.issue_generic_request(adb_args, env)
  if response.status != adb_pb2.AdbResponse.OK:
    raise RuntimeError(
        f'ADB command failed with status {response.status}:'
        f' {response.generic.output.decode()}.'
    )


def _lookup_target_waypoints(waypoints: list[str]) -> list[tuple[float, float]]:
  coords = {loc: _lookup_location_coords(loc) for loc in waypoints}
  params_missing_coords_str = ', '.join(
      [f'"{c[0]}"' for c in coords.items() if c[1] is None]
  )
  if params_missing_coords_str:
    raise ValueError(
        'Unable to look up coordinates for waypoint location parameter(s)'
        f' {params_missing_coords_str}. Only lat/lon coordinate strings or'
        ' exact names from _PRELOADED_MAP_LOCATIONS supported.'
    )
  return [c[1] for c in coords.items() if c[1] is not None]


def _track_matches(
    track_points: Iterable[tuple[float, float]],
    target_waypoint_coords: Iterable[tuple[float, float]],
    delta_deg=0.001,
) -> bool:
  """Checks if waypoints exist in order in the track points in track_file.

  Args:
    track_points: Sequence of track coordinate points to match.
    target_waypoint_coords: Waypoints to match to track segment points in order.
    delta_deg:

  Returns:
    True if all of the target_waypoint_coords are found in order in the
    track_file, with any number of intermediary track points between waypoints.
  """
  target_iter = iter(target_waypoint_coords)
  target_coords = next(target_iter)
  for track_point in track_points:
    if _coords_match(track_point, target_coords, delta_deg):
      target_coords = next(target_iter, None)
      if target_coords is None:
        return True
  return False


def _track_points(
    tracks_root: ElementTree.Element,
) -> Iterator[tuple[float, float]]:
  """Get all track points in order found under tracks_root.

  Args:
    tracks_root: XML element that contains trk -> trkseg -> trkpt elements.

  Yields:
    track points in order.
  """
  for track in tracks_root.findall('gpx:trk', _FAVORITES_XML_NAMESPACES):
    for segment in track.findall('gpx:trkseg', _FAVORITES_XML_NAMESPACES):
      for point in segment.findall('gpx:trkpt', _FAVORITES_XML_NAMESPACES):
        yield (float(point.attrib.get('lat')), float(point.attrib.get('lon')))


class OsmAndTrack(_OsmTaskEval):
  """Task for checking for a track with specified waypoints saved in OsmAnd."""

  complexity = 12
  schema = {
      'type': 'object',
      'properties': {
          'waypoints': {
              'type': 'array',
              'items': {'type': 'string'},
          },
      },
      'required': ['waypoints'],
  }

  @property
  def goal(self) -> str:
    waypoints = self.params['waypoints']
    if len(waypoints) < 2:
      raise ValueError(
          'Waypoints parameter must contain at least two locations.'
      )
    waypoints = ', '.join(self.params['waypoints'])
    return (
        f'Save a track with waypoints {waypoints} in the'
        ' OsmAnd maps app in the same order as listed.'
    )

  def initialize_task(self, env: interface.AsyncEnv) -> None:
    """Initializes the task environment."""
    super().initialize_task(env)
    _clear_tracks(env.controller)
    self._target_waypoint_coords = _lookup_target_waypoints(
        self.params['waypoints']
    )

  def is_successful(self, env: interface.AsyncEnv) -> float:
    with file_utils.tmp_directory_from_device(
        file_utils.convert_to_posix_path(_DEVICE_FILES, 'tracks'),
        env.controller,
    ) as tracks_directory:
      for track_file in os.listdir(tracks_directory):
        if _track_matches(
            _track_points(
                ElementTree.parse(
                    file_utils.convert_to_posix_path(
                        tracks_directory, track_file
                    )
                ).getroot()
            ),
            self._target_waypoint_coords,
        ):
          return super().is_successful(env)
    return 0.0

  def tear_down(self, env: interface.AsyncEnv):
    """Cleans up after task completion."""
    _clear_tracks(env.controller)
    super().tear_down(env)

  @classmethod
  def generate_random_params(cls) -> dict[str, Any]:
    waypoints = _random_location_str(
        names_only=True, num_locations=random.randint(2, 4)
    )
    track_name = f'{waypoints[0]} to {waypoints[-1]}'
    return {'track_name': track_name, 'waypoints': waypoints}
```

### `derived/selected_task_source.json`

Source ref: `androidworld://OsmAndFavorite`

```json
{
  "base_class_name": "_OsmTaskEval",
  "base_module": "android_world.task_evals.single.osmand",
  "base_source_file": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/osmand.py",
  "case_unit_id": "OsmAndFavorite",
  "class_name": "OsmAndFavorite",
  "difficulty": "medium",
  "module": "android_world.task_evals.single.osmand",
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
      "archive_path": "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/osmand.py",
      "sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
      "source_path": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/osmand.py"
    }
  ],
  "optimal_steps": "6",
  "packet_files": [
    "official/install/android_world/task_metadata.json",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/osmand.py",
    "derived/selected_task_source.json"
  ],
  "selection_order_key": "0d47816860944b55b2998cf51803642011d98b3e9d94ace48876b3a8f1e84aac",
  "selection_rank": 5,
  "source_file": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/osmand.py",
  "source_ref": "androidworld://OsmAndFavorite",
  "source_sha256": "817ec1e8a3bab013717fb6d881d85488c8e2d5be4f0e351d23f0c7fcde1c460b",
  "tags": [
    "search",
    "complex_ui_understanding",
    "parameterized"
  ],
  "task_id": "OsmAndFavorite",
  "task_name": "OsmAndFavorite",
  "task_template": "Add a favorite location marker for {location} in the OsmAnd maps app."
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "OsmAndFavorite",
  "copied_files": [
    "derived/selected_task_source.json",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/osmand.py",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_metadata.json"
  ],
  "derived_files": [
    "derived/selected_task_source.json"
  ],
  "domain": "androidworld",
  "file_sources": {
    "derived/selected_task_source.json": "androidworld://OsmAndFavorite",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/osmand.py": "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/osmand.py",
    "official/install/android_world/registry.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_metadata.json": "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json"
  },
  "official_files": [
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/osmand.py",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/android_world/task_metadata.json"
  ],
  "packet_files": [
    "official/install/android_world/task_metadata.json",
    "official/install/android_world/registry.py",
    "official/install/android_world/task_evals/task_eval.py",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/osmand.py",
    "derived/selected_task_source.json"
  ],
  "sha256_per_file": {
    "derived/selected_task_source.json": "6782ae728de2e67835f993a78cfae8fa1bdf96f28f05f2f6acf14b40962a0888",
    "official/install/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/osmand.py": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
    "official/install/android_world/registry.py": "47380849f428b231747365ac8ba50a83212cdc34180ab6376ff49e90b93af12b",
    "official/install/android_world/task_evals/task_eval.py": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
    "official/install/android_world/task_metadata.json": "fd3cf23ebb26e461a961dd60ff3f011d7e6ec78c992c10babbbdb86f9dd591e1"
  },
  "source_refs": [
    "<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/task_evals/single/osmand.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py",
    "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json",
    "androidworld://OsmAndFavorite"
  ],
  "task_id": "OsmAndFavorite"
}
```
