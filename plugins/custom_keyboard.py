import logging
import tkinter as tk
import configparser
import os

logger = logging.getLogger(__name__)


class CustomKeyboard(tk.Frame):
    def __init__(self, master, target_entry):
        super().__init__(master)
        self.logger = logging.getLogger(__name__)
        self.target_entry = target_entry
        self.caps_lock = False  # Flag for CAPS LOCK state
        self.selected_button = None

        # Read settings from settings.ini
        self.config = configparser.ConfigParser()
        settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'settings.ini')
        self.config.read(settings_path)

        # Adjust keyboard position and size
        self.place(x=0, y=140, width=264, height=100)  # Increased height, full width

        self.create_keyboard_layout()

    def create_keyboard_layout(self):
        """Create the keyboard layout with buttons."""
        try:
            self.logger.debug("Creating keyboard layout in CustomKeyboard")

            # Read font settings from settings.ini
            font_name = self.config.get('Appearance', 'font_name', fallback='Arial')
            font_size = 6
            font = (font_name, font_size)

            # Key frames
            row1_frame = tk.Frame(self)
            row1_frame.pack(fill=tk.X)
            row2_frame = tk.Frame(self)
            row2_frame.pack(fill=tk.X)
            row3_frame = tk.Frame(self)
            row3_frame.pack(fill=tk.X)
            row4_frame = tk.Frame(self)
            row4_frame.pack(fill=tk.X)

            self.button_rows = [row1_frame, row2_frame, row3_frame, row4_frame]

            # Row 1: CAPS, A-E, Clear, Backspace
            self.caps_button = tk.Button(
                row1_frame, text="CAPS", width=4, command=self.toggle_caps_lock, font=font  # Apply custom font
            )
            self.caps_button.pack(side=tk.LEFT, padx=2)

            for letter in "abcde":  # Lowercase letters
                button = tk.Button(
                    row1_frame,
                    text=letter,
                    width=2,
                    padx=2,
                    command=lambda l=letter: self.append_to_entry(l),
                    font=font  # Apply custom font
                )
                button.pack(side=tk.LEFT)

            self.clear_button = tk.Button(
                row1_frame, text="Clear", width=4, command=self.clear_entry, font=font  # Apply custom font
            )
            self.clear_button.pack(side=tk.LEFT, padx=2)

            self.backspace_button = tk.Button(
                row1_frame, text="Back", width=4, command=self.backspace, font=font  # Apply custom font
            )
            self.backspace_button.pack(side=tk.LEFT, padx=2)

            # Row 2: F-N, Enter
            for letter in "fghijklmno":  # Lowercase letters
                button = tk.Button(
                    row2_frame,
                    text=letter,
                    width=2,
                    padx=2,
                    command=lambda l=letter: self.append_to_entry(l),
                    font=font  # Apply custom font
                )
                button.pack(side=tk.LEFT)

            self.enter_button = tk.Button(
                row2_frame, text="Enter", width=6, command=self.enter_key, font=font  # Apply custom font
            )
            self.enter_button.pack(side=tk.RIGHT, padx=2)

            # Row 3: O-Z, comma, period
            for letter in "pqrstuvwxyz,.":  # Lowercase letters
                button = tk.Button(
                    row3_frame,
                    text=letter,
                    width=2,
                    padx=2,
                    command=lambda l=letter: self.append_to_entry(l),
                    font=font  # Apply custom font
                )
                button.pack(side=tk.LEFT)

            # Row 4: 1-5, Space, 6-0
            for number in "12345":
                button = tk.Button(
                    row4_frame,
                    text=number,
                    width=2,
                    padx=2,
                    command=lambda n=number: self.append_to_entry(n),
                    font=font  # Apply custom font
                )
                button.pack(side=tk.LEFT)

            self.space_button = tk.Button(
                row4_frame, text="Space", width=6, command=lambda: self.append_to_entry(" "), font=font
                # Apply custom font
            )
            self.space_button.pack(side=tk.LEFT, padx=2)

            for number in "67890":
                button = tk.Button(
                    row4_frame,
                    text=number,
                    width=2,
                    padx=2,
                    command=lambda n=number: self.append_to_entry(n),
                    font=font  # Apply custom font
                )
                button.pack(side=tk.LEFT)

            # Set initial focus to the first letter key
            self.set_focus(row1_frame.winfo_children()[1])  # Focus on "a"
            self.logger.debug("Keyboard layout created successfully.")

        except Exception as e:
            self.logger.error(f"Error creating keyboard layout: {e}")

    def append_to_entry(self, char):
        """Appends the given character to the target Entry widget."""
        try:
            if self.caps_lock:
                char = char.upper()
            self.target_entry.insert(tk.END, char)
            self.logger.debug(f"Appended '{char}' to entry.")
        except Exception as e:
            self.logger.error(f"Error appending to entry: {e}")

    def toggle_caps_lock(self):
        """Toggles the CAPS LOCK state."""
        self.caps_lock = not self.caps_lock
        self.logger.debug(f"CAPS LOCK toggled: {'ON' if self.caps_lock else 'OFF'}")

        # Update button labels to reflect CAPS LOCK state
        for row in self.button_rows:
            for button in row.winfo_children():
                if isinstance(button, tk.Button) and button['text'].isalpha():
                    if self.caps_lock:
                        button['text'] = button['text'].upper()
                    else:
                        button['text'] = button['text'].lower()

    def backspace(self):
        """Removes the last character from the target Entry widget."""
        try:
            current_text = self.target_entry.get()
            self.target_entry.delete(len(current_text) - 1, tk.END)
            self.logger.debug("Backspace pressed.")
        except Exception as e:
            self.logger.error(f"Error performing backspace: {e}")

    def enter_key(self):
        """Simulates pressing Enter in the target Entry widget."""
        try:
            self.target_entry.event_generate("<Return>")
            self.logger.debug("Enter key pressed.")
        except Exception as e:
            self.logger.error(f"Error simulating Enter key: {e}")

    def set_focus(self, button):
        """Sets focus to the given button and updates relief."""
        try:
            if self.selected_button:  # Reset the relief of the previously selected button
                self.selected_button.config(relief=tk.RAISED)

            self.selected_button = button
            self.selected_button.config(relief=tk.SUNKEN)
            self.selected_button.focus_set()
            self.logger.debug(f"Focus set to button: {button['text']}")
        except Exception as e:
            self.logger.error(f"Error setting focus to button: {e}")

    def handle_up(self):
        """Handles the Up button press on the keyboard."""
        self.logger.debug("Navigating up in CustomKeyboard")
        self.navigate_keyboard("Up")

    def handle_down(self):
        """Handles the Down button press on the keyboard."""
        self.logger.debug("Navigating down in CustomKeyboard")
        self.navigate_keyboard("Down")

    def handle_left(self):
        """Handles the Left button press on the keyboard."""
        self.logger.debug("Navigating left in CustomKeyboard")
        self.navigate_keyboard("Left")

    def handle_right(self):
        """Handles the Right button press on the keyboard."""
        self.logger.debug("Navigating right in CustomKeyboard")
        self.navigate_keyboard("Right")

    def handle_select(self):  # New method to handle Select button (search)
        """Handles the Select button press (triggers search)."""
        self.logger.debug("Handling Select button in CustomKeyboard (Triggering search)")
        self.target_entry.event_generate("<Return>")  # Trigger search

    def handle_a(self):  # New method to handle A button (select key)
        """Handles the A button press (selects the focused key)."""
        self.logger.debug("Handling A button in CustomKeyboard (Selecting key)")
        if self.selected_button:
            self.selected_button.invoke()

    def handle_b(self):  # New method to handle B button (close keyboard)
        """Handles the B button press (closes the keyboard)."""
        self.logger.debug("Handling B button in CustomKeyboard (Closing keyboard)")
        self.master.hide_keyboard()  # Call the hide_keyboard method of the parent

    def navigate_keyboard(self, direction):
        """Handles keyboard navigation using button presses."""
        if self.selected_button is None:
            return

        current_row = self.selected_button.master
        current_index = current_row.winfo_children().index(self.selected_button)

        row_index = self.button_rows.index(current_row)

        if direction == "Up":
            new_row_index = (row_index - 1) % len(self.button_rows)
            new_row = self.button_rows[new_row_index]
            new_index = min(current_index, len(new_row.winfo_children()) - 1)
            self.set_focus(new_row.winfo_children()[new_index])
        elif direction == "Down":
            new_row_index = (row_index + 1) % len(self.button_rows)
            new_row = self.button_rows[new_row_index]
            new_index = min(current_index, len(new_row.winfo_children()) - 1)
            self.set_focus(new_row.winfo_children()[new_index])
        elif direction == "Left":
            if current_index > 0:
                new_index = current_index - 1
                self.set_focus(current_row.winfo_children()[new_index])
            elif row_index > 0:
                new_row = self.button_rows[row_index - 1]
                new_index = len(new_row.winfo_children()) - 1
                self.set_focus(new_row.winfo_children()[new_index])
        elif direction == "Right":
            if current_index < len(current_row.winfo_children()) - 1:
                new_index = current_index + 1
                self.set_focus(current_row.winfo_children()[new_index])
            elif row_index < len(self.button_rows) - 1:
                new_row = self.button_rows[row_index + 1]
                new_index = 0
                self.set_focus(new_row.winfo_children()[new_index])

    def clear_entry(self):
        """Clears the entire content of the target Entry widget."""
        self.target_entry.delete(0, tk.END)
        self.logger.debug("Cleared entry.")
