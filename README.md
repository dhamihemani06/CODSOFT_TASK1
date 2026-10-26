# CODSOFT_TASK1
A GUI-based task manager with persistent storage, task priorities, deadline tracking, search, filters, and reports.
[README.md](https://github.com/user-attachments/files/33968919/README.md)
# TaskFlow Pro — Advanced Python To-Do List Project

TaskFlow Pro is a desktop task-management application built with Python, Tkinter, and SQLite. It is designed as a more advanced version of a basic to-do list assignment.

## Features

- Modern desktop GUI
- Create, edit, complete, restore, and delete tasks
- Store title, category, priority, due date, and notes
- Automatic overdue-task detection
- Dashboard counters for total, pending, completed, and overdue tasks
- Search across task titles, categories, priorities, and notes
- Filter by status, priority, and category
- Export all tasks to CSV
- Persistent local SQLite database
- Input validation and delete confirmation
- No external Python packages required

## Requirements

- Python 3.10 or newer
- Tkinter (usually included with standard Python installations)
- SQLite (included with Python)

## Run the project

1. Extract the ZIP file.
2. Open a terminal or command prompt in the `TaskFlow_Pro` folder.
3. Run:

   ```bash
   python taskflow.py
   ```

4. The `taskflow.db` database will be created automatically when the app first starts.

On some Linux distributions, Tkinter may need to be installed separately (for example, the `python3-tk` package).

## How to use

1. Click **New Task** to create a task.
2. Add a title and optionally choose a category, priority, due date, and notes.
3. Select a task to edit, mark complete/restore, delete, or view its notes.
4. Use the search box and filters to find tasks quickly.
5. Click **Export CSV** to save a spreadsheet-friendly copy of all tasks.

## Project structure

```text
TaskFlow_Pro/
├── taskflow.py       # GUI, validation, task actions, and filtering
├── README.md         # Setup and user guide
└── requirements.txt  # No third-party packages required
```

The SQLite database (`taskflow.db`) is generated at runtime and is not included in the ZIP.

## Concepts demonstrated

- Object-oriented programming
- GUI development with Tkinter and ttk
- Relational data storage with SQLite
- CRUD operations (Create, Read, Update, Delete)
- SQL queries and parameterized statements
- Event-driven programming
- Input validation and exception handling
- Searching, filtering, sorting, and data export
- Date handling and application state

## Possible future upgrades

- User accounts and login
- Recurring tasks and reminders
- Calendar view
- Cloud synchronisation
- Unit tests and automated packaging
