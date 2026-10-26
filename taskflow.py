"""
TaskFlow Pro — Advanced To-Do List Manager
Python 3.10+ | Tkinter GUI | SQLite storage (no third-party packages)

Features:
- Persistent SQLite database
- Add, edit, complete, delete, and restore tasks
- Priority, category, due date, notes
- Search and filter by status, priority, and category
- Overdue and due-soon indicators
- Dashboard statistics
- CSV export
"""

from __future__ import annotations

import csv
import sqlite3
import tkinter as tk
from datetime import date, datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP_NAME = "TaskFlow Pro"
DB_PATH = Path(__file__).with_name("taskflow.db")
DATE_FORMAT = "%Y-%m-%d"


class TaskDatabase:
    """Handles all database operations for TaskFlow Pro."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'Personal',
                priority TEXT NOT NULL DEFAULT 'Medium'
                    CHECK(priority IN ('Low', 'Medium', 'High', 'Urgent')),
                due_date TEXT,
                notes TEXT NOT NULL DEFAULT '',
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
            """
        )
        self.connection.commit()

    def all_tasks(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT * FROM tasks ORDER BY completed ASC, "
            "CASE priority WHEN 'Urgent' THEN 1 WHEN 'High' THEN 2 "
            "WHEN 'Medium' THEN 3 ELSE 4 END, "
            "CASE WHEN due_date IS NULL OR due_date = '' THEN 1 ELSE 0 END, "
            "due_date ASC, id DESC"
        ).fetchall()

    def add_task(self, data: dict) -> None:
        self.connection.execute(
            """INSERT INTO tasks
            (title, category, priority, due_date, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (data["title"], data["category"], data["priority"],
             data["due_date"], data["notes"], datetime.now().isoformat(timespec="seconds")),
        )
        self.connection.commit()

    def update_task(self, task_id: int, data: dict) -> None:
        self.connection.execute(
            """UPDATE tasks SET title=?, category=?, priority=?,
            due_date=?, notes=? WHERE id=?""",
            (data["title"], data["category"], data["priority"],
             data["due_date"], data["notes"], task_id),
        )
        self.connection.commit()

    def set_completed(self, task_id: int, completed: bool) -> None:
        self.connection.execute(
            "UPDATE tasks SET completed=?, completed_at=? WHERE id=?",
            (int(completed), datetime.now().isoformat(timespec="seconds") if completed else None, task_id),
        )
        self.connection.commit()

    def delete_task(self, task_id: int) -> None:
        self.connection.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.connection.commit()

    def stats(self) -> dict[str, int]:
        rows = self.connection.execute(
            """SELECT COUNT(*) AS total,
            SUM(CASE WHEN completed=0 THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN completed=1 THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN completed=0 AND due_date<>'' AND due_date < ? THEN 1 ELSE 0 END) AS overdue
            FROM tasks""",
            (date.today().isoformat(),),
        ).fetchone()
        return {key: int(rows[key] or 0) for key in ("total", "pending", "completed", "overdue")}

    def close(self) -> None:
        self.connection.close()


class TaskDialog(tk.Toplevel):
    """Modal dialog used to add or edit a task."""

    def __init__(self, parent: tk.Misc, task: sqlite3.Row | None = None) -> None:
        super().__init__(parent)
        self.result: dict | None = None
        self.title("Edit task" if task else "Create a task")
        self.configure(bg="#f4f6fb")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.title_var = tk.StringVar(value=task["title"] if task else "")
        self.category_var = tk.StringVar(value=task["category"] if task else "Personal")
        self.priority_var = tk.StringVar(value=task["priority"] if task else "Medium")
        self.due_var = tk.StringVar(value=task["due_date"] if task else "")
        self.notes_var = tk.StringVar(value=task["notes"] if task else "")

        frame = ttk.Frame(self, padding=20)
        frame.grid(sticky="nsew")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Task title *").grid(row=0, column=0, sticky="w", pady=6)
        title_entry = ttk.Entry(frame, textvariable=self.title_var, width=38)
        title_entry.grid(row=0, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="Category").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Combobox(frame, textvariable=self.category_var,
                     values=("Personal", "College", "Work", "Health", "Shopping", "Other"),
                     width=35).grid(row=1, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="Priority").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Combobox(frame, textvariable=self.priority_var, state="readonly",
                     values=("Low", "Medium", "High", "Urgent"), width=35).grid(
                         row=2, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="Due date").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=self.due_var, width=38).grid(
            row=3, column=1, sticky="ew", pady=6)
        ttk.Label(frame, text="Format: YYYY-MM-DD (leave blank if none)",
                  foreground="#68738a").grid(row=4, column=1, sticky="w")

        ttk.Label(frame, text="Notes").grid(row=5, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=self.notes_var, width=38).grid(
            row=5, column=1, sticky="ew", pady=6)

        buttons = ttk.Frame(frame)
        buttons.grid(row=6, column=0, columnspan=2, sticky="e", pady=(18, 0))
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(buttons, text="Save task", command=self._save).pack(side="right")
        title_entry.focus_set()
        self.bind("<Return>", lambda _event: self._save())
        self.bind("<Escape>", lambda _event: self.destroy())
        self.update_idletasks()
        self.geometry(f"+{parent.winfo_rootx()+80}+{parent.winfo_rooty()+60}")

    def _save(self) -> None:
        title = self.title_var.get().strip()
        due = self.due_var.get().strip()
        if not title:
            messagebox.showwarning("Missing title", "Please enter a task title.", parent=self)
            return
        if due:
            try:
                datetime.strptime(due, DATE_FORMAT)
            except ValueError:
                messagebox.showwarning("Invalid date", "Use YYYY-MM-DD, for example 2026-11-05.", parent=self)
                return
        category = self.category_var.get().strip() or "Personal"
        priority = self.priority_var.get()
        if priority not in ("Low", "Medium", "High", "Urgent"):
            priority = "Medium"
        self.result = {
            "title": title, "category": category, "priority": priority,
            "due_date": due, "notes": self.notes_var.get().strip(),
        }
        self.destroy()


class TaskFlowApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.db = TaskDatabase()
        self.title(f"{APP_NAME} | Smart Productivity")
        self.geometry("1120x700")
        self.minsize(900, 580)
        self.configure(bg="#f4f6fb")
        self._configure_style()
        self._build_ui()
        self.refresh()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#f4f6fb")
        style.configure("TLabel", background="#f4f6fb", foreground="#172033", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 23, "bold"), foreground="#183b32")
        style.configure("Sub.TLabel", font=("Segoe UI", 10), foreground="#69758b")
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 7))
        style.configure("Primary.TButton", background="#1d624c", foreground="white")
        style.map("Primary.TButton", background=[("active", "#174d3c")])
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=31,
                        background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), padding=8)
        style.map("Treeview", background=[("selected", "#d7eee5")],
                  foreground=[("selected", "#172033")])

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=(24, 20, 24, 18))
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x")
        left = ttk.Frame(header)
        left.pack(side="left", fill="x", expand=True)
        ttk.Label(left, text="TaskFlow Pro", style="Title.TLabel").pack(anchor="w")
        ttk.Label(left, text="Plan clearly. Prioritize smartly. Get things done.",
                  style="Sub.TLabel").pack(anchor="w", pady=(3, 0))
        ttk.Button(header, text="＋ New Task", style="Primary.TButton",
                   command=self.add_task).pack(side="right", padx=(8, 0))
        ttk.Button(header, text="Export CSV", command=self.export_csv).pack(side="right")

        stats_frame = ttk.Frame(outer)
        stats_frame.pack(fill="x", pady=(20, 16))
        self.stat_vars = {key: tk.StringVar(value="0") for key in ("total", "pending", "completed", "overdue")}
        stat_info = [
            ("total", "TOTAL TASKS", "#e7eefb"),
            ("pending", "PENDING", "#fff0d8"),
            ("completed", "COMPLETED", "#dff4e8"),
            ("overdue", "OVERDUE", "#ffe2e2"),
        ]
        for index, (key, label, color) in enumerate(stat_info):
            card = tk.Frame(stats_frame, bg=color, padx=16, pady=12)
            card.grid(row=0, column=index, sticky="ew", padx=(0 if index == 0 else 10, 0))
            stats_frame.columnconfigure(index, weight=1)
            tk.Label(card, text=label, bg=color, fg="#58647a",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
            tk.Label(card, textvariable=self.stat_vars[key], bg=color, fg="#172033",
                     font=("Segoe UI", 22, "bold")).pack(anchor="w", pady=(4, 0))

        filters = ttk.Frame(outer)
        filters.pack(fill="x", pady=(0, 12))
        ttk.Label(filters, text="Search").pack(side="left", padx=(0, 6))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filters, textvariable=self.search_var, width=26)
        search_entry.pack(side="left", padx=(0, 14))
        self.status_var = tk.StringVar(value="All")
        ttk.Label(filters, text="Status").pack(side="left", padx=(0, 6))
        ttk.Combobox(filters, textvariable=self.status_var, state="readonly",
                     values=("All", "Pending", "Completed", "Overdue"), width=11).pack(side="left", padx=(0, 14))
        self.priority_filter = tk.StringVar(value="All")
        ttk.Label(filters, text="Priority").pack(side="left", padx=(0, 6))
        ttk.Combobox(filters, textvariable=self.priority_filter, state="readonly",
                     values=("All", "Urgent", "High", "Medium", "Low"), width=10).pack(side="left", padx=(0, 14))
        self.category_filter = tk.StringVar(value="All")
        ttk.Label(filters, text="Category").pack(side="left", padx=(0, 6))
        ttk.Combobox(filters, textvariable=self.category_filter, state="readonly",
                     values=("All", "Personal", "College", "Work", "Health", "Shopping", "Other"),
                     width=12).pack(side="left")
        ttk.Button(filters, text="Reset", command=self.reset_filters).pack(side="right")
        for var in (self.search_var, self.status_var, self.priority_filter, self.category_filter):
            var.trace_add("write", lambda *_args: self.refresh_table())

        table_frame = ttk.Frame(outer)
        table_frame.pack(fill="both", expand=True)
        columns = ("status", "title", "category", "priority", "due", "created")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        headings = {
            "status": ("Status", 95), "title": ("Task", 330), "category": ("Category", 120),
            "priority": ("Priority", 95), "due": ("Due date", 115), "created": ("Created", 120),
        }
        for col, (heading, width) in headings.items():
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, minwidth=70, anchor="w")
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.tree.tag_configure("overdue", foreground="#b42318")
        self.tree.tag_configure("completed", foreground="#738096")
        self.tree.tag_configure("urgent", foreground="#a51d2d")
        self.tree.bind("<Double-1>", lambda _event: self.edit_task())

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(14, 0))
        ttk.Button(actions, text="Edit selected", command=self.edit_task).pack(side="left")
        ttk.Button(actions, text="Mark complete / restore", command=self.toggle_complete).pack(side="left", padx=8)
        ttk.Button(actions, text="Delete selected", command=self.delete_task).pack(side="left")
        ttk.Button(actions, text="View notes", command=self.view_notes).pack(side="left", padx=8)
        self.footer_var = tk.StringVar(value="Your tasks are stored locally on this computer.")
        ttk.Label(actions, textvariable=self.footer_var, style="Sub.TLabel").pack(side="right")

    def refresh(self) -> None:
        stats = self.db.stats()
        for key, value in stats.items():
            self.stat_vars[key].set(str(value))
        self.refresh_table()

    def refresh_table(self) -> None:
        if not hasattr(self, "tree"):
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        today = date.today().isoformat()
        query = self.search_var.get().strip().casefold()
        status = self.status_var.get()
        priority = self.priority_filter.get()
        category = self.category_filter.get()
        shown = 0
        for task in self.db.all_tasks():
            due = task["due_date"] or ""
            is_overdue = bool(not task["completed"] and due and due < today)
            status_text = "Completed" if task["completed"] else ("Overdue" if is_overdue else "Pending")
            searchable = " ".join((task["title"], task["category"], task["priority"], task["notes"])).casefold()
            if query and query not in searchable:
                continue
            if status == "Pending" and (task["completed"] or is_overdue):
                continue
            if status == "Completed" and not task["completed"]:
                continue
            if status == "Overdue" and not is_overdue:
                continue
            if priority != "All" and task["priority"] != priority:
                continue
            if category != "All" and task["category"] != category:
                continue
            created = task["created_at"][:10]
            tags = ("completed",) if task["completed"] else (("overdue",) if is_overdue else (("urgent",) if task["priority"] == "Urgent" else ()))
            self.tree.insert("", "end", iid=str(task["id"]),
                             values=(status_text, task["title"], task["category"],
                                     task["priority"], due or "—", created), tags=tags)
            shown += 1
        self.footer_var.set(f"Showing {shown} task(s) • Data saved locally")

    def selected_task(self) -> sqlite3.Row | None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Select a task", "Please select a task first.", parent=self)
            return None
        task_id = int(selection[0])
        return next((task for task in self.db.all_tasks() if task["id"] == task_id), None)

    def add_task(self) -> None:
        dialog = TaskDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self.db.add_task(dialog.result)
            self.refresh()

    def edit_task(self) -> None:
        task = self.selected_task()
        if task is None:
            return
        dialog = TaskDialog(self, task)
        self.wait_window(dialog)
        if dialog.result:
            self.db.update_task(task["id"], dialog.result)
            self.refresh()

    def toggle_complete(self) -> None:
        task = self.selected_task()
        if task is None:
            return
        self.db.set_completed(task["id"], not bool(task["completed"]))
        self.refresh()

    def delete_task(self) -> None:
        task = self.selected_task()
        if task is None:
            return
        if messagebox.askyesno("Delete task", f"Delete '{task['title']}' permanently?", parent=self):
            self.db.delete_task(task["id"])
            self.refresh()

    def view_notes(self) -> None:
        task = self.selected_task()
        if task is None:
            return
        notes = task["notes"].strip() or "No notes have been added for this task."
        messagebox.showinfo(task["title"], notes, parent=self)

    def reset_filters(self) -> None:
        self.search_var.set("")
        self.status_var.set("All")
        self.priority_filter.set("All")
        self.category_filter.set("All")

    def export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self, title="Export tasks", defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
            initialfile=f"taskflow_tasks_{date.today().isoformat()}.csv",
        )
        if not path:
            return
        tasks = self.db.all_tasks()
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(("ID", "Title", "Category", "Priority", "Due Date",
                                 "Notes", "Status", "Created At", "Completed At"))
                for task in tasks:
                    writer.writerow((task["id"], task["title"], task["category"],
                                     task["priority"], task["due_date"], task["notes"],
                                     "Completed" if task["completed"] else "Pending",
                                     task["created_at"], task["completed_at"] or ""))
        except OSError as exc:
            messagebox.showerror("Export failed", f"Could not save the CSV file:\n{exc}", parent=self)
            return
        messagebox.showinfo("Export complete", f"Exported {len(tasks)} task(s) to:\n{path}", parent=self)

    def _on_close(self) -> None:
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = TaskFlowApp()
    app.mainloop()
