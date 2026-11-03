import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from core.insights import analyze_destination

# Reuse the existing checklist and history functions from main.py.
from main import CHECKLISTS, load_history, save_history


class DontForgetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Don'tForget - Smart Departure Assistant")
        self.root.geometry("650x720")
        self.root.minsize(520, 600)

        # Checklist state
        self.item_vars = {}
        self.last_saved_state = None

        # Reminder state
        self.reminder_time = None
        self.reminder_departure = None
        self.reminder_after_id = None
        self.departure_time = tk.StringVar(value="08:00")
        self.preparation_minutes = tk.StringVar(value="15")

        # Main container keeps the interface aligned and compact.
        main_frame = ttk.Frame(root, padding=16)
        main_frame.pack(fill="both", expand=True)

        # Header
        ttk.Label(
            main_frame,
            text="Don'tForget",
            font=("Arial", 22, "bold")
        ).pack(pady=(0, 3))

        ttk.Label(
            main_frame,
            text="Check your essentials before leaving."
        ).pack(pady=(0, 14))

        # Destination selection
        destination_frame = ttk.Frame(main_frame)
        destination_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            destination_frame,
            text="Where are you going?"
        ).pack(anchor="w")

        self.destination = tk.StringVar(value="College")
        self.destination_box = ttk.Combobox(
            destination_frame,
            textvariable=self.destination,
            values=list(CHECKLISTS.keys()),
            state="readonly"
        )
        self.destination_box.pack(fill="x", pady=(5, 0))
        self.destination_box.bind(
            "<<ComboboxSelected>>", self.load_items
        )

        # One and only one departure reminder section.
        reminder_frame = ttk.LabelFrame(
            main_frame,
            text="Departure Reminder",
            padding=10
        )
        reminder_frame.pack(fill="x", pady=(0, 10))
        reminder_frame.columnconfigure(1, weight=1)
        reminder_frame.columnconfigure(3, weight=1)

        ttk.Label(
            reminder_frame,
            text="Departure time (HH:MM)"
        ).grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)

        ttk.Entry(
            reminder_frame,
            textvariable=self.departure_time,
            width=10
        ).grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=4)

        ttk.Label(
            reminder_frame,
            text="Prepare before (minutes)"
        ).grid(row=0, column=2, sticky="w", padx=(0, 6), pady=4)

        ttk.Entry(
            reminder_frame,
            textvariable=self.preparation_minutes,
            width=8
        ).grid(row=0, column=3, sticky="ew", pady=4)

        ttk.Button(
            reminder_frame,
            text="Set Reminder",
            command=self.set_reminder
        ).grid(row=1, column=0, columnspan=4, pady=(7, 4))

        self.reminder_status = ttk.Label(
            reminder_frame,
            text="No reminder set."
        )
        self.reminder_status.grid(
            row=2, column=0, columnspan=4, sticky="w", pady=(2, 0)
        )

        # Checklist expands to use remaining vertical space.
        self.items_frame = ttk.LabelFrame(
            main_frame,
            text="Essential items",
            padding=12
        )
        self.items_frame.pack(fill="both", expand=True, pady=(0, 8))

        self.status = ttk.Label(
            main_frame,
            text="Mark each item you have packed."
        )
        self.status.pack(anchor="w", pady=(0, 8))

        buttons = ttk.Frame(main_frame)
        buttons.pack(fill="x", pady=(0, 2))

        ttk.Button(
            buttons,
            text="Check & Save",
            command=self.check_and_save
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        ttk.Button(
            buttons,
            text="View History",
            command=self.show_history
        ).pack(side="left", expand=True, fill="x", padx=4)

        ttk.Button(
            buttons,
            text="Smart Insights",
            command=self.show_insights
        ).pack(side="left", expand=True, fill="x", padx=(4, 0))

        self.load_items()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_items(self, event=None):
        """Refresh checkboxes for the selected destination."""
        for widget in self.items_frame.winfo_children():
            widget.destroy()

        self.item_vars = {}
        destination = self.destination.get()

        for item in CHECKLISTS.get(destination, []):
            variable = tk.BooleanVar(value=False)
            self.item_vars[item] = variable

            ttk.Checkbutton(
                self.items_frame,
                text=item,
                variable=variable
            ).pack(anchor="w", pady=3)

        self.status.config(text="Mark each item you have packed.")
        # Explicitly ensure no save occurs on destination change
        return

    def set_reminder(self):
        """Schedule one in-app reminder while the app remains open."""
        try:
            departure_clock = datetime.strptime(
                self.departure_time.get().strip(), "%H:%M"
            ).time()
            minutes = int(self.preparation_minutes.get().strip())

            if not 1 <= minutes <= 1440:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid reminder",
                "Enter a valid 24-hour time (HH:MM) and a preparation "
                "duration between 1 and 1440 minutes.",
                parent=self.root
            )
            return

        now = datetime.now()
        departure = datetime.combine(now.date(), departure_clock)

        # If the entered departure time has passed, schedule for tomorrow.
        if departure <= now:
            departure += timedelta(days=1)

        reminder = departure - timedelta(minutes=minutes)

        # Cancel any previously scheduled callback.
        if self.reminder_after_id is not None:
            try:
                self.root.after_cancel(self.reminder_after_id)
            except tk.TclError:
                pass
            self.reminder_after_id = None

        self.reminder_departure = departure
        self.reminder_time = reminder
        self.reminder_status.config(
            text=(
                f"Prepare at {reminder:%d %b, %H:%M} | "
                f"Depart at {departure:%d %b, %H:%M}"
            )
        )
        self.check_reminder()

    def check_reminder(self):
        """Check once per second whether the reminder is due."""
        self.reminder_after_id = None

        if self.reminder_time is None or self.reminder_departure is None:
            return

        now = datetime.now()
        if now >= self.reminder_time:
            departure = self.reminder_departure

            # Clear state before showing the popup so it only appears once.
            self.reminder_time = None
            self.reminder_departure = None
            self.reminder_status.config(text="Reminder delivered.")

            messagebox.showinfo(
                "Don'tForget - Time to Prepare",
                f"It's time to prepare for your departure at "
                f"{departure:%H:%M}!\n\n"
                "Check your essentials before leaving.",
                parent=self.root
            )
            return

        self.reminder_after_id = self.root.after(1000, self.check_reminder)

    def check_and_save(self):
        """Save the current checklist and warn about unchecked items."""
        destination = self.destination.get()
        checklist_items = CHECKLISTS.get(destination, [])

        packed = [
            item for item, variable in self.item_vars.items()
            if variable.get()
        ]
        missing = [item for item in checklist_items if item not in packed]
        state = (destination, tuple(packed))

        if state == self.last_saved_state:
            messagebox.showinfo(
                "Already saved",
                "This checklist state has already been saved.",
                parent=self.root
            )
            return

        record = {
            "destination": destination,
            "timestamp": datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "packed_items": packed,
            "missing_items": missing,
            "packed_count": len(packed),
            "total_items": len(checklist_items)
        }

        try:
            save_history(record)
        except (OSError, ValueError) as error:
            messagebox.showerror(
                "Could not save checklist",
                f"Your checklist could not be saved.\n\n{error}",
                parent=self.root
            )
            return

        self.last_saved_state = state

        if missing:
            self.status.config(
                text=f"{len(missing)} item(s) still need checking."
            )
            messagebox.showwarning(
                "Items to check",
                "Please check these items before leaving:\n\n"
                + "\n".join(f"• {item}" for item in missing),
                parent=self.root
            )
        else:
            self.status.config(text="All items marked as packed!")
            messagebox.showinfo(
                "Checklist complete",
                "All listed items are marked as packed.",
                parent=self.root
            )

    
    def show_insights(self):
        """Display analytics calculated by the shared insights module."""
        history = load_history()

        window = tk.Toplevel(self.root)
        window.title("Don'tForget - Smart Insights")
        window.geometry("650x550")
        window.minsize(450, 350)

        container = ttk.Frame(window, padding=10)
        container.pack(fill="both", expand=True)

        text = tk.Text(
            container,
            wrap="word",
            padx=10,
            pady=10
        )

        scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=text.yview
        )
        text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)

        text.insert("end", "DON'TFORGET - SMART INSIGHTS\n")
        text.insert("end", "=" * 38 + "\n\n")

        for destination in CHECKLISTS:
            result = analyze_destination(history, destination)

            text.insert("end", f"{destination}\n")
            text.insert("end", "-" * 30 + "\n")
            text.insert(
                "end",
                f"Recorded checklists: {result['sessions']}\n"
            )
            text.insert(
                "end",
                f"Items marked missing: "
                f"{result['missing_percentage']:.1f}% "
                f"of recorded checklist items\n"
            )

            ranked_items = result["ranked_items"]

            if not ranked_items:
                text.insert(
                    "end",
                    "No missing items recorded for this destination.\n"
                )
            else:
                text.insert("end", "\nMissing-item frequency:\n")

                for item, count in ranked_items:
                    sessions = result["sessions"]
                    percentage = count / sessions * 100

                    text.insert(
                        "end",
                        f"  {item}: {count}/{sessions} checklists "
                        f"({percentage:.1f}%)\n"
                    )

            text.insert("end", "\nRecommendations:\n")

            for recommendation in result["recommendations"]:
                text.insert("end", f"  • {recommendation}\n")

            text.insert("end", "\n")

        text.config(state="disabled")


    def show_history(self):
        """Display saved checklist records."""
        history = load_history()

        window = tk.Toplevel(self.root)
        window.title("Checklist History")
        window.geometry("480x400")
        window.minsize(360, 260)

        text = tk.Text(window, wrap="word", padx=10, pady=10)
        scrollbar = ttk.Scrollbar(window, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)

        if not history:
            text.insert("end", "No saved checklist history yet.")
        else:
            for number, record in enumerate(history, start=1):
                if not isinstance(record, dict):
                    continue
                missing = record.get("missing_items", [])
                if not isinstance(missing, list):
                    missing = []
                text.insert(
                    "end",
                    f"Record {number}\n"
                    f"Destination: {record.get('destination', 'Unknown')}\n"
                    f"Date/time: {record.get('timestamp', 'Unknown')}\n"
                    f"Packed: {record.get('packed_count', 0)}/"
                    f"{record.get('total_items', 0)}\n"
                    f"Missing: {', '.join(missing) if missing else 'None'}\n"
                    f"{'-' * 35}\n\n"
                )

        text.config(state="disabled")

    def on_close(self):
        """Cancel any pending reminder callback before closing the window."""
        if self.reminder_after_id is not None:
            try:
                self.root.after_cancel(self.reminder_after_id)
            except tk.TclError:
                pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = DontForgetApp(root)
    root.mainloop()
