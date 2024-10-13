import configparser
import io
import logging
import os
import tkinter as tk
from tkinter import ttk

import requests
from PIL import Image, ImageTk

from plugins.custom_keyboard import CustomKeyboard

logger = logging.getLogger(__name__)


class SpriteTreeview(ttk.Treeview):
    """Custom Treeview that displays sprites."""

    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.image_cache = {}

    def insert(self, parent, index, iid=None, **kw):
        """Overrides the insert method to handle sprite loading."""
        if 'image' in kw:
            sprite_url = kw.pop('image')
            image = self._load_sprite(sprite_url)
            if image:
                kw['image'] = image
        return super().insert(parent, index, iid, **kw)

    def _load_sprite(self, sprite_url):
        """Loads and caches a sprite image."""
        if sprite_url in self.image_cache:
            return self.image_cache[sprite_url]

        try:
            response = requests.get(sprite_url, timeout=5)
            response.raise_for_status()
            image = Image.open(io.BytesIO(response.content))
            image = image.resize((24, 24), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.image_cache[sprite_url] = photo
            return photo
        except Exception as e:
            logger.error(f"Error loading sprite from {sprite_url}: {e}")
            return None


class FavouritesView(tk.Frame):
    def __init__(self, master, data_manager, app):
        super().__init__(master)
        logger.debug("Initializing FavouritesView...")
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
        self.favourites_tree = None

        # Read settings from settings.ini
        self.config = configparser.ConfigParser()
        settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'settings.ini')
        self.config.read(settings_path)

        self.create_widgets()
        self.load_favourites_data()
        self.search_term.trace("w", lambda *args: self.master.after(200, self.filter_pokemon_list))
        self.after(100, self.set_initial_focus)

    def create_widgets(self):
        logger.debug("Creating widgets in FavouritesView")

        # Apply custom font to labels
        font = self.app.custom_font

        # Title Label for FavouritesView
        title_label = ttk.Label(self, text="Favourites", font=font)
        title_label.pack(pady=(5, 0))

        # Search bar with label
        search_frame = ttk.Frame(self)
        search_frame.pack(pady=(5, 0))

        search_label = ttk.Label(search_frame, text="Search:", font=font)
        search_label.pack(side=tk.LEFT)

        self.search_bar = ttk.Entry(search_frame, textvariable=self.search_term, width=12, font=font)
        self.search_bar.pack(side=tk.LEFT)

        # Create the Treeview with scrollbar
        treeview_frame = tk.Frame(self)
        treeview_frame.pack(pady=(0, 5), fill=tk.BOTH, expand=True)

        # Apply custom font to Treeview headings using Style
        style = ttk.Style()
        style.configure("Treeview.Heading", font=self.app.custom_font)

        self.favourites_tree = SpriteTreeview(treeview_frame, columns=("ID", "Sprite", "Name"), show="headings",
                                              height=7)
        self.favourites_tree.heading("ID", text="ID", anchor=tk.W)
        self.favourites_tree.heading("Sprite", text=" ")
        self.favourites_tree.heading("Name", text="Name", anchor=tk.W)
        self.favourites_tree.column("ID", width=30, stretch=False)
        self.favourites_tree.column("Sprite", width=30, stretch=False)
        self.favourites_tree.column("Name", width=70, stretch=True)

        self.favourites_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.favourites_tree.bind("<<TreeviewSelect>>", self.on_pokemon_select)
        self.favourites_tree.bind("<Down>", self.handle_down)
        self.favourites_tree.bind("<Up>", self.handle_up)

        # Scrollbar for the Treeview
        self.treeview_scrollbar = ttk.Scrollbar(treeview_frame, orient="vertical", command=self.favourites_tree.yview)
        self.treeview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.favourites_tree.configure(yscrollcommand=self.treeview_scrollbar.set)

        # Result count label with custom font
        self.result_count_label = ttk.Label(self, text="", font=font)
        self.result_count_label.pack()

        logger.debug(f"create_widgets: Exiting. Current focus: {self.focus_get()}")

    def set_initial_focus(self):
        """Sets the initial focus to the Treeview."""
        logger.debug(f"set_initial_focus: Entering. Current focus: {self.focus_get()}")
        try:
            if self.favourites_tree.get_children():
                first_item = self.favourites_tree.get_children()[0]
                pokemon_name = self.favourites_tree.item(first_item)['values'][2]
                logger.debug(f"First item in Treeview: {first_item} ({pokemon_name})")

                self.favourites_tree.selection_set(first_item)
                self.favourites_tree.focus(first_item)

                logger.debug(f"Initial focus set to: {self.favourites_tree.focus()} ({pokemon_name})")
        except Exception as e:
            logger.error(f"Error setting initial focus in FavouritesView: {e}")
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

    def load_favourites_data(self):
        """Loads favourite Pokémon data into the Treeview."""
        logger.debug(f"load_favourites_data: Entering. Current focus: {self.focus_get()}")
        try:
            self.favourites_tree.delete(*self.favourites_tree.get_children())
            self.pokemon_list = self.data_manager.get_all_pokemon(is_favourite=True)
            logger.debug(f"Fetched {len(self.pokemon_list)} favourite Pokémon.")

            for pokemon in self.pokemon_list:
                self.favourites_tree.insert("", tk.END,
                                            values=(pokemon.id, "", pokemon.name),
                                            image=pokemon.sprite_front)

            if self.pokemon_list:
                self.favourites_tree.selection_set(self.favourites_tree.get_children()[0])
                self.favourites_tree.focus(self.favourites_tree.get_children()[0])
                self.favourites_tree.see(self.favourites_tree.get_children()[0])

            logger.debug("Favourites data loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading favourites data: {e}")
        logger.debug(f"load_favourites_data: Exiting. Current focus: {self.focus_get()}")

    def filter_pokemon_list(self):
        """Filters the Pokemon list based on the search term."""
        logger.debug(f"filter_pokemon_list: Entering. Current focus: {self.focus_get()}")
        search_term = self.search_term.get().lower()
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
        self.populate_favourites_treeview(self.filtered_pokemon if self.search_active else None)
        logger.debug(f"filter_pokemon_list: Exiting. Current focus: {self.focus_get()}")

    def populate_favourites_treeview(self, pokemon_list=None):
        """Populates the Treeview with (filtered) favourite Pokémon data."""
        logger.debug("Populating favourites Treeview...")
        self.favourites_tree.delete(*self.favourites_tree.get_children())

        if pokemon_list is None:
            pokemon_list = self.pokemon_list
            logger.debug("Using full favourite Pokémon list.")
        else:
            logger.debug("Using filtered favourite Pokémon list.")

        for pokemon in pokemon_list:
            # Capitalize the Pokémon name
            pokemon.name = pokemon.name.capitalize()
            self.favourites_tree.insert("", tk.END,
                                        values=(pokemon.id, "", pokemon.name),
                                        image=pokemon.sprite_front)

        if pokemon_list:
            self.favourites_tree.selection_set(self.favourites_tree.get_children()[0])
            self.favourites_tree.focus(self.favourites_tree.get_children()[0])
            self.favourites_tree.see(self.favourites_tree.get_children()[0])

        logger.debug("Favourites Treeview populated.")
        logger.debug(f"populate_favourites_treeview: Exiting. Current focus: {self.focus_get()}")

    def clear_search(self):
        """Clears the search bar."""
        logger.debug(f"clear_search: Entering. Current focus: {self.focus_get()}")
        self.search_term.set("")
        self.search_active = False
        self.populate_favourites_treeview()
        logger.debug(f"clear_search: Exiting. Current focus: {self.focus_get()}")

    def handle_up(self, event=None):
        """Handles the Up button press."""
        logger.debug(f"handle_up: Entering. Current focus: {self.focus_get()}, Search Mode: {self.search_mode}")

        if self.keyboard_open:
            logger.debug("Keyboard is open, navigating up")
            self.keyboard.handle_up()
        elif self.search_mode:
            logger.debug("In search mode, Up button has no effect.")
        elif self.favourites_tree.selection():
            current_item = self.favourites_tree.selection()[0]
            first_item = self.favourites_tree.get_children()[0]

            if current_item == first_item:
                logger.debug("First item selected, doing nothing")
            else:
                previous_item = self.favourites_tree.prev(current_item)
                if previous_item:
                    self.favourites_tree.selection_set(previous_item)
                    self.favourites_tree.focus(previous_item)
                    self.favourites_tree.see(previous_item)
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
        elif self.favourites_tree.selection():
            current_item = self.favourites_tree.selection()[0]
            next_item = self.favourites_tree.next(current_item)

            if next_item:
                self.favourites_tree.selection_set(next_item)
                self.favourites_tree.focus(next_item)
                self.favourites_tree.see(next_item)
        else:
            logger.debug("No item selected, doing nothing")

        logger.debug(f"handle_down: Exiting. Current focus: {self.focus_get()}")

    def handle_left(self):
        """Handles the Left button press."""
        logger.debug(f"handle_left: Entering. Current focus: {self.focus_get()}, Search Mode: {self.search_mode}")
        if self.keyboard_open:
            self.keyboard.handle_left()
        logger.debug(f"handle_left: Exiting. Current focus: {self.focus_get()}")

    def handle_right(self):
        """Handles the Right button press."""
        logger.debug(f"handle_right: Entering. Current focus: {self.focus_get()}, Search Mode: {self.search_mode}")
        if self.keyboard_open:
            self.keyboard.handle_right()
        logger.debug(f"handle_right: Exiting. Current focus: {self.focus_get()}")

    def handle_select(self):
        """Handles the A button press."""
        logger.debug(f"handle_select: Entering. Current focus: {self.focus_get()}, Search Mode: {self.search_mode}")

        if self.keyboard_open:
            self.keyboard.handle_a()
        elif self.search_mode and self.search_bar.focus_get():
            self.on_search_enter()
        elif self.favourites_tree.selection():
            selected_item = self.favourites_tree.selection()[0]
            selected_pokemon_id = self.favourites_tree.item(selected_item)['values'][0]
            logger.debug(f"Navigating to DetailView for Pokémon ID: {selected_pokemon_id}")
            self.master.app.show_view("DetailView", selected_pokemon_id)
        logger.debug(f"handle_select: Exiting. Current focus: {self.focus_get()}")

    def handle_back(self, event=None):
        """Handles the B button press."""
        logger.debug(f"handle_back: Entering. Current focus: {self.focus_get()}, Search Mode: {self.search_mode}")
        if self.keyboard_open:
            logger.debug("Keyboard is open, closing keyboard")
            self.hide_keyboard()
            return

        logger.debug("Navigating back to MenuView and resetting view")
        self.app.show_view("MenuView")
        self.reset_view()
        logger.debug(f"handle_back: Exiting. Current focus: {self.focus_get()}")

    def handle_favourite_toggle(self):
        """Handles the Select button press to toggle favourites."""
        logger.debug("Toggling favourite status in FavouritesView...")
        try:
            pokemon_id = self._get_selected_pokemon_id()
            if pokemon_id:
                logger.debug(f"Toggling favourite status for Pokémon ID: {pokemon_id}")
                self.data_manager.update_favourite_status(pokemon_id, 0)
                self.load_favourites_data()  # refresh data
        except Exception as e:
            logger.error(f"Error toggling favourite in FavouritesView: {e}")

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
        logger.debug(f"on_pokemon_select: Entering. Current focus: {self.focus_get()}")

        selected_item = self.favourites_tree.selection()
        if selected_item:
            self.favourites_tree.focus(selected_item[0])
            logger.debug(f"Focus set to: {self.favourites_tree.focus()}")

        logger.debug(f"on_pokemon_select: Exiting. Current focus: {self.focus_get()}")

    def toggle_favourite(self, event=None):
        """Toggles the favourite status of the selected Pokémon."""
        logger.debug(f"toggle_favourite: Entering. Current focus: {self.focus_get()}")
        if self.favourites_tree.selection():
            selected_item = self.favourites_tree.selection()[0]
            pokemon_id = self.favourites_tree.item(selected_item)['values'][0]
            is_favourite = self.favourites_tree.item(selected_item)['values'][2] == "★"
            self.data_manager.update_favourite_status(pokemon_id, not is_favourite)

            self.favourites_tree.item(selected_item, values=(
                pokemon_id,
                self.favourites_tree.item(selected_item)['values'][1],
                "★" if not is_favourite else ""
            ))
        logger.debug(f"toggle_favourite: Exiting. Current focus: {self.focus_get()}")

    def get_selected_pokemon(self):
        """Gets the currently selected Pokemon data."""
        logger.debug(f"get_selected_pokemon: Entering. Current focus: {self.focus_get()}")
        if self.favourites_tree.selection():
            selected_item = self.favourites_tree.selection()[0]
            pokemon_id = self.favourites_tree.item(selected_item)['values'][0]
            if self.search_active:
                logger.debug(f"get_selected_pokemon: Exiting. Current focus: {self.focus_get()}")
                return next((p for p in self.filtered_pokemon if p.id == pokemon_id), None)
            else:
                logger.debug(f"get_selected_pokemon: Exiting. Current focus: {self.focus_get()}")
                return next((p for p in self.pokemon_list if p.id == pokemon_id), None)
        logger.debug(f"get_selected_pokemon: Exiting. Current focus: {self.focus_get()}")
        return None

    def get_selected_pokemon_id(self):
        """Gets the ID of the currently selected Pokemon."""
        logger.debug(f"get_selected_pokemon_id: Entering. Current focus: {self.focus_get()}")
        if self.favourites_tree.selection():
            selected_item = self.favourites_tree.selection()[0]
            logger.debug(f"get_selected_pokemon_id: Exiting. Current focus: {self.focus_get()}")
            return self.favourites_tree.item(selected_item)['values'][0]
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

        if self.favourites_tree.get_children():
            first_item = self.favourites_tree.get_children()[0]
            self.favourites_tree.selection_set(first_item)
            self.favourites_tree.focus_set()
            self.favourites_tree.see(first_item)

        logger.debug(f"Focus is now on: {self.focus_get()}")

    def reset_view(self):
        """Resets the FavouritesView to its initial state."""
        logger.debug(f"reset_view: Entering. Current focus: {self.focus_get()}")
        self.search_term.set("")
        self.search_active = False
        self.load_favourites_data()
        self.set_initial_focus()
        self.hide_keyboard()
        logger.debug(f"reset_view: Exiting. Current focus: {self.focus_get()}")

    def handle_start(self):
        """Handles the Start button press to toggle search mode."""
        logger.debug(f"handle_start called. Current focus: {self.focus_get()}, Search Mode: {self.search_mode}")
        self.toggle_search_mode()
        return
