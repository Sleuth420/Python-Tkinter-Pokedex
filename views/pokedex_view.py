import configparser
import logging
import os
import tkinter as tk
from tkinter import ttk

from plugins.custom_keyboard import CustomKeyboard

logger = logging.getLogger(__name__)


class PokedexView(tk.Frame):
    def __init__(self, master, data_manager, app):
        super().__init__(master)

        logger.debug("Initializing PokedexView...")

        self.master = master
        self.data_manager = data_manager
        self.app = app

        self.pokemon_list = []
        self.filtered_pokemon = []
        self.search_active = False
        self.search_term = tk.StringVar()
        self.keyboard_open = False
        self.keyboard = None
        self.search_mode = False
        self.focus_from_navigation = None
        self.search_bar = None
        self.clear_button = None
        self.result_count_label = None
        self.pokemon_treeview = None
        self.treeview_scrollbar = None
        self.batch_size = 20
        self.current_offset = 0

        # Flag to prevent on_pokemon_select from being called during lazy loading
        self.lazy_load_in_progress = False

        self.config = configparser.ConfigParser()
        settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'settings.ini')
        self.config.read(settings_path)

        self.create_widgets()
        self.load_pokemon_batch()
        self.search_term.trace("w", lambda *args: self.master.after(200, self.filter_pokemon_list))
        self.after(100, self.set_initial_focus)

    def create_widgets(self):
        logger.debug("Creating widgets in PokedexView")

        font_name = self.config.get('Appearance', 'font_name', fallback='Arial')
        font_size = self.config.getint('Appearance', 'font_size', fallback=10)
        font = (font_name, font_size)

        # Apply custom font to the title label
        title_label = ttk.Label(self, text="Pokédex", font=self.app.custom_font)
        title_label.pack(pady=(5, 0))

        search_frame = ttk.Frame(self)
        search_frame.pack(pady=(5, 0))

        # Label for "Search:"
        search_label = ttk.Label(search_frame, text="Search:", font=self.app.custom_font)
        search_label.pack(side=tk.LEFT)

        # Apply custom font to the search bar
        self.search_bar = ttk.Entry(search_frame, textvariable=self.search_term, width=12, font=self.app.custom_font)
        self.search_bar.pack(side=tk.LEFT)

        treeview_frame = tk.Frame(self)
        treeview_frame.pack(pady=(0, 5), fill=tk.BOTH, expand=True)

        self.pokemon_treeview = ttk.Treeview(treeview_frame, columns=("ID", "Name", "Favourite"), show="headings",
                                             height=7)
        # Apply custom font to Treeview headings using Style
        style = ttk.Style()
        style.configure("Treeview.Heading", font=self.app.custom_font)

        self.pokemon_treeview.heading("ID", text="ID", anchor=tk.W)
        self.pokemon_treeview.heading("Name", text="Name", anchor=tk.W)
        self.pokemon_treeview.heading("Favourite", text="★", anchor=tk.CENTER)

        self.pokemon_treeview.column("ID", width=30, stretch=False)
        self.pokemon_treeview.column("Name", width=70, stretch=True)
        self.pokemon_treeview.column("Favourite", width=30, stretch=False)

        self.pokemon_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.pokemon_treeview.bind("<<TreeviewSelect>>", self.on_pokemon_select)
        self.pokemon_treeview.bind("<Down>", self.handle_down)
        self.pokemon_treeview.bind("<Up>", self.handle_up)

        self.treeview_scrollbar = ttk.Scrollbar(treeview_frame, orient="vertical", command=self.pokemon_treeview.yview)
        self.treeview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pokemon_treeview.configure(yscrollcommand=self.treeview_scrollbar.set)

        # Apply custom font to the result count label
        self.result_count_label = ttk.Label(self, text="", font=self.app.custom_font)
        self.result_count_label.pack()

        logger.debug(f"create_widgets: Exiting. Current focus: {self.focus_get()}")

    def set_initial_focus(self):
        """Sets the initial focus to the Treeview."""
        logger.debug(f"set_initial_focus: Entering. Current focus: {self.focus_get()}")
        try:
            if self.pokemon_treeview.get_children():
                first_item = self.pokemon_treeview.get_children()[0]
                pokemon_name = self.pokemon_treeview.item(first_item)['values'][1]
                logger.debug(f"First item in Treeview: {first_item} ({pokemon_name})")

                self.pokemon_treeview.selection_set(first_item)
                self.pokemon_treeview.focus(first_item)

                logger.debug(f"Initial focus set to: {self.pokemon_treeview.focus()} ({pokemon_name})")
        except Exception as e:
            logger.error(f"Error setting initial focus in PokedexView: {e}")
        logger.debug(f"set_initial_focus: Exiting. Current focus: {self.focus_get()}")

    def show_keyboard(self):
        """Displays the custom keyboard at the bottom of the screen."""
        logger.debug(f"show_keyboard: Entering. Current focus: {self.focus_get()}")
        if self.keyboard is None:
            self.keyboard = CustomKeyboard(self.master, self.search_bar)

        window_width = self.config.getint('Screen', 'width', fallback=264)
        window_height = self.config.getint('Screen', 'height', fallback=240)

        keyboard_width = 264
        keyboard_height = 100
        keyboard_x = (window_width - keyboard_width) // 2
        keyboard_y = window_height - keyboard_height

        self.keyboard.place(x=keyboard_x, y=keyboard_y, width=keyboard_width, height=keyboard_height)
        self.keyboard.focus_set()
        self.keyboard_open = True
        logger.debug(f"Focus is now on: {self.focus_get()}")
        logger.debug(f"show_keyboard: Exiting. Current focus: {self.focus_get()}")

    def hide_keyboard(self):
        """Hides the custom keyboard."""
        logger.debug(f"hide_keyboard: Entering. Current focus: {self.focus_get()}")
        if self.keyboard:
            self.keyboard.place_forget()
            self.keyboard_open = False
            logger.debug(f"Focus is now on: {self.focus_get()}")
        logger.debug(f"hide_keyboard: Exiting. Current focus: {self.focus_get()}")

    def on_search_enter(self, event=None):
        """Handles the Enter key press on the search bar or the 'A' button."""
        logger.debug(
            f"on_search_enter called. Keyboard Open: {self.keyboard_open}, "
            f"Focus from Navigation: {self.focus_from_navigation}"
        )

        if not self.keyboard_open and not self.focus_from_navigation:
            logger.debug("Opening Keyboard")
            self.show_keyboard()
        self.focus_from_navigation = False

    def load_all_pokemon(self):
        """Loads all Pokémon from the database."""
        logger.debug("Loading all Pokémon...")
        self.pokemon_list = self.data_manager.get_all_pokemon()
        self.populate_treeview()
        logger.debug("All Pokémon loaded successfully.")

    def load_pokemon_batch(self):
        """Loads a batch of Pokemon from the database."""
        logger.debug(f"load_pokemon_batch: Entering. Current focus: {self.focus_get()}")
        logger.debug(f"Loading Pokémon batch (offset: {self.current_offset}, batch size: {self.batch_size})")

        self.lazy_load_in_progress = True
        new_pokemon = self.data_manager.get_all_pokemon(limit=self.batch_size, offset=self.current_offset)
        self.pokemon_list.extend(new_pokemon)
        self.populate_treeview()
        self.current_offset += self.batch_size
        logger.debug(f"Pokémon batch loaded (total Pokémon: {len(self.pokemon_list)})")
        self.lazy_load_in_progress = False

        self.pokemon_treeview.focus_set()
        logger.debug(f"load_pokemon_batch: Exiting. Current focus: {self.focus_get()}")

    def populate_treeview(self, pokemon_list=None):
        """Populates the Treeview with Pokémon data."""
        logger.debug(f"populate_treeview: Entering. Current focus: {self.focus_get()}")

        for item in self.pokemon_treeview.get_children():
            self.pokemon_treeview.delete(item)

        if pokemon_list is None:
            pokemon_list = self.pokemon_list
            logger.debug("Using full Pokémon list.")
        else:
            logger.debug("Using filtered Pokémon list.")

        for pokemon in pokemon_list:
            favourite = "★" if pokemon.is_favourite else ""
            pokemon.name = pokemon.name.capitalize()
            self.pokemon_treeview.insert("", tk.END, values=(pokemon.id, pokemon.name, favourite))

        self.update_result_count()
        logger.debug("Treeview populated.")

        if self.pokemon_treeview.get_children() and not self.lazy_load_in_progress:
            first_item = self.pokemon_treeview.get_children()[0]
            pokemon_name = self.pokemon_treeview.item(first_item)['values'][1]
            logger.debug(f"First item in Treeview: {first_item} ({pokemon_name})")

            self.pokemon_treeview.selection_set(first_item)
            self.pokemon_treeview.focus(first_item)
            self.pokemon_treeview.see(first_item)
            logger.debug(f"Focus set to: {self.pokemon_treeview.focus()} ({pokemon_name})")

        logger.debug(f"populate_treeview: Exiting. Current focus: {self.focus_get()}")

    def filter_pokemon_list(self):
        """Filters the Pokemon list based on the search term."""
        logger.debug(f"filter_pokemon_list: Entering. Current focus: {self.focus_get()}")
        search_term = self.search_term.get().lower()

        if search_term:
            logger.debug(f"Filtering Pokémon list with search term: '{search_term}'")
            self.filtered_pokemon = []
            if search_term:
                self.search_active = True
                for pokemon in self.pokemon_list:
                    if (search_term in pokemon.name.lower() or
                            (pokemon.type1 and search_term in pokemon.type1.lower()) or
                            (pokemon.type2 and search_term in pokemon.type2.lower())):
                        self.filtered_pokemon.append(pokemon)
            else:
                self.search_active = False

            logger.debug(f"Filtered Pokémon count: {len(self.filtered_pokemon)}")
            self.populate_treeview(self.filtered_pokemon if self.search_active else None)
        else:
            logger.debug("Search term is empty, not filtering.")

        logger.debug(f"filter_pokemon_list: Exiting. Current focus: {self.focus_get()}")

    def clear_search(self):
        """Clears the search bar."""
        logger.debug(f"clear_search: Entering. Current focus: {self.focus_get()}")
        self.search_term.set("")
        self.search_active = False
        self.populate_treeview()
        logger.debug(f"clear_search: Exiting. Current focus: {self.focus_get()}")

    def handle_up(self, event=None):
        """Handles the Up button press."""
        logger.debug(f"handle_up: Entering. Current focus: {self.focus_get()}, Search Mode: {self.search_mode}")

        if self.keyboard_open:
            logger.debug("Keyboard is open, navigating up")
            self.keyboard.handle_up()
        elif self.search_mode:
            logger.debug("In search mode, Up button has no effect.")
        elif self.pokemon_treeview.selection():
            current_item = self.pokemon_treeview.selection()[0]
            first_item = self.pokemon_treeview.get_children()[0]

            if current_item == first_item:
                logger.debug("First item selected, doing nothing")
            else:
                previous_item = self.pokemon_treeview.prev(current_item)
                if previous_item:
                    self.pokemon_treeview.selection_set(previous_item)
                    self.pokemon_treeview.focus(previous_item)
                    self.pokemon_treeview.see(previous_item)
        else:
            logger.debug("No item selected, doing nothing")

        logger.debug(f"handle_up: Exiting. Current focus: {self.focus_get()}")

    def handle_down(self, event=None):
        """Handles the Down button press."""
        logger.debug(f"handle_down: Entering. Current focus: {self.focus_get()}, Search Mode: {self.search_mode}")

        if self.keyboard_open:
            logger.debug("Keyboard is open, navigating down")
            self.keyboard.handle_down()
        elif self.search_mode:
            logger.debug("In search mode, Down button has no effect.")
        elif self.pokemon_treeview.selection():
            current_item = self.pokemon_treeview.selection()[0]
            next_item = self.pokemon_treeview.next(current_item)

            # Check if we need to load more Pokémon (70% threshold)
            if not next_item and len(self.pokemon_list) > 0 and self.pokemon_treeview.index(current_item) >= (
                    0.7 * len(self.pokemon_list)) - 1:
                self.load_pokemon_batch()

                # Select the first item of the new batch after loading
                first_new_item = self.pokemon_treeview.get_children()[self.current_offset - self.batch_size]
                self.pokemon_treeview.selection_set(first_new_item)
                self.pokemon_treeview.focus(first_new_item)
                self.pokemon_treeview.see(first_new_item)

            elif next_item:
                self.pokemon_treeview.selection_set(next_item)
                self.pokemon_treeview.focus(next_item)
                self.pokemon_treeview.see(next_item)
            else:  # Wrap around to the top if at the end of the list
                first_item = self.pokemon_treeview.get_children()[0]
                self.pokemon_treeview.selection_set(first_item)
                self.pokemon_treeview.focus(first_item)
                self.pokemon_treeview.see(first_item)
        elif self.pokemon_treeview.get_children():
            first_item = self.pokemon_treeview.get_children()[0]
            self.pokemon_treeview.selection_set(first_item)
            self.pokemon_treeview.focus(first_item)
            self.pokemon_treeview.see(first_item)

        logger.debug(f"handle_down: Exiting. Current focus: {self.focus_get()}")

    def handle_left(self):
        """Handles the Left button press."""
        logger.debug(f"handle_left: Entering. Current focus: {self.focus_get()}, Search Mode: {self.search_mode}")
        if self.keyboard_open:
            self.keyboard.handle_left()
        elif self.search_mode and self.clear_button.focus_get():
            self.search_bar.focus_set()
        logger.debug(f"handle_left: Exiting. Current focus: {self.focus_get()}")

    def handle_right(self):
        """Handles the Right button press."""
        logger.debug(f"handle_right: Entering. Current focus: {self.focus_get()}, Search Mode: {self.search_mode}")
        if self.keyboard_open:
            self.keyboard.handle_right()
        elif self.search_mode and self.search_bar.focus_get():
            self.clear_button.focus_set()
        logger.debug(f"handle_right: Exiting. Current focus: {self.focus_get()}")

    def handle_select(self):
        """Handles the A button press."""
        logger.debug(f"handle_select: Entering. Current focus: {self.focus_get()}, Search Mode: {self.search_mode}")

        if self.keyboard_open:
            self.keyboard.handle_a()
        elif self.search_mode and self.search_bar.focus_get():
            self.on_search_enter()
        elif self.search_mode and self.clear_button.focus_get():
            self.clear_search()
        elif self.pokemon_treeview.selection():
            selected_item = self.pokemon_treeview.selection()[0]
            selected_pokemon_id = self.pokemon_treeview.item(selected_item)['values'][0]
            selected_pokemon_name = self.pokemon_treeview.item(selected_item)['values'][1]
            logger.debug(
                f"Navigating to DetailView for Pokémon ID: {selected_pokemon_id} ({selected_pokemon_name})")
            self.master.app.show_view("DetailView", selected_pokemon_id)

        logger.debug(f"handle_select: Exiting. Current focus: {self.focus_get()}")

    def handle_back(self, event=None):
        """Handles the B button press."""
        logger.debug(f"handle_back: Entering. Current focus: {self.focus_get()}, Search Mode: {self.search_mode}")
        if self.keyboard_open:
            logger.debug("Keyboard is open, closing keyboard")
            self.hide_keyboard()
            return

        logger.debug(f"Navigating back from {self.__class__.__name__}")
        self.app.go_back()
        self.reset_view()
        logger.debug(f"handle_back: Exiting. Current focus: {self.focus_get()}")

    def handle_favourite_toggle(self):
        """Handles the Select button press to toggle favourites."""
        logger.debug(f"handle_favourite_toggle: Entering. Current focus: {self.focus_get()}")
        if self.pokemon_treeview.selection():
            self.toggle_favourite()
        logger.debug(f"handle_favourite_toggle: Exiting. Current focus: {self.focus_get()}")

    def toggle_search_mode(self, event=None):
        """Toggles search mode."""
        logger.debug(
            f"toggle_search_mode called. Current focus: {self.focus_get()}, Search Mode: {self.search_mode}")

        self.search_mode = not self.search_mode
        if self.search_mode:
            logger.debug("Entering search mode")
            self.search_bar.focus_set()
            self.show_keyboard()
        else:
            logger.debug("Exiting search mode")
            self.hide_keyboard()
            self.after(10, self.reset_treeview_focus)

        logger.debug(f"Search Mode: {self.search_mode}, Current focus: {self.focus_get()}")

    def on_pokemon_select(self, event):
        """Handles the <<TreeviewSelect>> event."""
        if not self.lazy_load_in_progress:
            logger.debug(f"on_pokemon_select: Entering. Current focus: {self.focus_get()}")

            selected_item = self.pokemon_treeview.selection()
            if selected_item:
                selected_pokemon_name = self.pokemon_treeview.item(selected_item[0])['values'][1]
                self.pokemon_treeview.focus(selected_item[0])
                logger.debug(f"Focus set to: {self.pokemon_treeview.focus()} ({selected_pokemon_name})")

            logger.debug(f"on_pokemon_select: Exiting. Current focus: {self.focus_get()}")

    def toggle_favourite(self, event=None):
        """Toggles the favourite status of the selected Pokémon."""
        logger.debug(f"toggle_favourite: Entering. Current focus: {self.focus_get()}")
        if self.pokemon_treeview.selection():
            selected_item = self.pokemon_treeview.selection()[0]
            pokemon_id = self.pokemon_treeview.item(selected_item)['values'][0]
            is_favourite = self.pokemon_treeview.item(selected_item)['values'][2] == "★"
            self.data_manager.update_favourite_status(pokemon_id, not is_favourite)

            # Update the favourite icon in the Treeview
            self.pokemon_treeview.item(selected_item, values=(
                pokemon_id,
                self.pokemon_treeview.item(selected_item)['values'][1],
                "★" if not is_favourite else ""
            ))
        logger.debug(f"toggle_favourite: Exiting. Current focus: {self.focus_get()}")

    def get_selected_pokemon(self):
        """Gets the currently selected Pokemon data."""
        logger.debug(f"get_selected_pokemon: Entering. Current focus: {self.focus_get()}")
        if self.pokemon_treeview.selection():
            selected_item = self.pokemon_treeview.selection()[0]
            pokemon_id = self.pokemon_treeview.item(selected_item)['values'][0]
            if self.search_active:
                logger.debug(f"get_selected_pokemon: Exiting. Current focus: {self.focus_get()}")  # Moved before return
                return next((p for p in self.filtered_pokemon if p.id == pokemon_id), None)
            else:
                logger.debug(f"get_selected_pokemon: Exiting. Current focus: {self.focus_get()}")  # Moved before return
                return next((p for p in self.pokemon_list if p.id == pokemon_id), None)
        logger.debug(f"get_selected_pokemon: Exiting. Current focus: {self.focus_get()}")  # Moved before return
        return None  # Return None if no selection

    def get_selected_pokemon_id(self):
        """Gets the ID of the currently selected Pokemon."""
        logger.debug(f"get_selected_pokemon_id: Entering. Current focus: {self.focus_get()}")
        if self.pokemon_treeview.selection():
            selected_item = self.pokemon_treeview.selection()[0]
            logger.debug(f"get_selected_pokemon_id: Exiting. Current focus: {self.focus_get()}")
            return self.pokemon_treeview.item(selected_item)['values'][0]
        else:
            logger.debug(f"get_selected_pokemon_id: Exiting. Current focus: {self.focus_get()}")
            return None

    def update_result_count(self):
        """Updates the label with the number of search results."""
        logger.debug(f"update_result_count: Entering. Current focus: {self.focus_get()}")
        if self.search_active:
            count = len(self.filtered_pokemon)
            self.result_count_label.config(text=f"Found {count} Pokémon")
        else:
            self.result_count_label.config(text="")
        logger.debug(f"update_result_count: Exiting. Current focus: {self.focus_get()}")

    def reset_treeview_focus(self):
        """Resets focus and selection to the first item in the Treeview."""
        logger.debug(f"reset_treeview_focus: Entering. Current focus: {self.focus_get()}")
        if self.pokemon_treeview.get_children():
            first_item = self.pokemon_treeview.get_children()[0]
            self.pokemon_treeview.selection_set(first_item)
            self.pokemon_treeview.focus_set()
            self.pokemon_treeview.see(first_item)
        logger.debug(f"reset_treeview_focus: Exiting. Current focus: {self.focus_get()}")

    def reset_view(self):
        """Resets the PokedexView to its initial state."""
        logger.debug(f"reset_view: Entering. Current focus: {self.focus_get()}")
        self.search_term.set("")
        self.search_active = False
        self.populate_treeview()
        self.set_initial_focus()
        logger.debug(f"reset_view: Exiting. Current focus: {self.focus_get()}")

    def handle_start(self):
        """Handles the Start button press to toggle search mode."""
        logger.debug(
            f"handle_start called. Current focus: {self.focus_get()}, Search Mode: {self.search_mode}")
        self.toggle_search_mode()
        return
