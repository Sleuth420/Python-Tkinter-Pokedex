import configparser
import io
import logging
import os
import tkinter as tk
from tkinter import ttk

import requests
from PIL import Image, ImageTk

logger = logging.getLogger(__name__)


class DetailView(tk.Frame):
    def __init__(self, master, data_manager, app, pokemon_id):
        super().__init__(master)
        logger.debug(f"Initializing DetailView for Pokemon ID: {pokemon_id}...")

        self.master = master
        self.data_manager = data_manager
        self.pokemon_id = pokemon_id
        self.app = app
        self.pokemon = None
        self.sprite_photo = None

        # Read settings from settings.ini
        self.config = configparser.ConfigParser()
        settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'settings.ini')
        self.config.read(settings_path)

        try:
            self.pokemon = self.data_manager.get_pokemon_by_id(self.pokemon_id)
            if self.pokemon is None:
                raise ValueError(f"No data found for Pokémon ID {self.pokemon_id}")
            self.is_favourite = self.pokemon.is_favourite
        except (ValueError, Exception) as e:
            logger.error(f"Error fetching Pokémon data: {e}")
            tk.messagebox.showerror("Error", f"Could not load Pokémon details: {e}")
            self.app.show_view("PokedexView")
            return

        logger.debug(f"Pokémon data fetched: {self.pokemon}")

        self.create_widgets()
        self.load_and_display_sprite()

    def create_widgets(self):
        """Creates the widgets for the DetailView."""
        logger.debug("Creating widgets in DetailView")

        # Title
        self.pokemon_name_label = ttk.Label(self, text=self._get_title_text(), wraplength=140,
                                            font=self.app.custom_font)
        self.pokemon_name_label.pack(pady=(10, 5))

        # Canvas for scrollable content
        self.detail_canvas = tk.Canvas(self)
        self.detail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.detail_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.detail_canvas.configure(yscrollcommand=self.scrollbar.set)

        # Content frame
        self.content_frame = ttk.Frame(self.detail_canvas)
        self.detail_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        # Sprite
        self.sprite_label = tk.Label(self.content_frame)
        self.sprite_label.pack(pady=(2, 2), anchor="center")

        # Stats
        stats_frame = ttk.Frame(self.content_frame)
        stats_frame.pack(pady=2, anchor="center")

        # Stats Title (Bold)
        ttk.Label(stats_frame, text="Stats:", font=self.app.custom_font).pack()

        stats = ["HP", "Attack", "Defense", "Sp. Atk", "Sp. Def", "Speed"]
        stat_values = [self.pokemon.hp, self.pokemon.attack, self.pokemon.defense,
                       self.pokemon.sp_atk, self.pokemon.sp_def, self.pokemon.speed]

        for i in range(len(stats)):
            ttk.Label(stats_frame, text=f"{stats[i]}: {stat_values[i]}",
                      font=self.app.custom_font).pack()

        # Types
        types_frame = ttk.Frame(self.content_frame)
        types_frame.pack(pady=2, anchor="center")
        ttk.Label(types_frame, text="Types:", font=self.app.custom_font).pack()
        types = [t for t in [self.pokemon.type1, self.pokemon.type2] if t is not None]
        for pokemon_type in types:
            ttk.Label(types_frame, text=pokemon_type, font=self.app.custom_font).pack()

        # Description
        description_frame = ttk.Frame(self.content_frame)
        description_frame.pack(pady=2, anchor="center")

        # Description Title (Bold)
        ttk.Label(description_frame, text="Description:", font=self.app.custom_font).pack()

        self.description_label = ttk.Label(description_frame,
                                           text=f"{self.pokemon.description}",
                                           wraplength=240,
                                           font=self.app.custom_font)
        self.description_label.pack()

        # Configure canvas scroll region (update when content changes)
        self.content_frame.bind("<Configure>", self.on_frame_configure)

    def on_frame_configure(self, event):
        """Update the scroll region when the content frame is resized."""
        self.detail_canvas.configure(scrollregion=self.detail_canvas.bbox("all"))

    def load_and_display_sprite(self):
        """Loads and displays the Pokemon sprite."""
        logger.debug("Loading and displaying sprite...")
        try:
            sprite_url = self.pokemon.sprite_front
            if sprite_url:
                response = requests.get(sprite_url, timeout=5)
                response.raise_for_status()
                sprite_image = Image.open(io.BytesIO(response.content))
                sprite_image = sprite_image.resize((160, 160), Image.Resampling.LANCZOS)
                self.sprite_photo = ImageTk.PhotoImage(sprite_image)
                self.sprite_label.config(image=self.sprite_photo)
                logger.debug(f"Sprite loaded from: {sprite_url}")
            else:
                self.sprite_label.config(text="No Sprite Available", font=("Arial", 8))
                logger.warning(f"No sprite URL found for Pokémon ID: {self.pokemon_id}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error loading sprite: {e}")
            self.sprite_label.config(text="Error Loading Sprite", font=("Arial", 8))
        except Exception as e:
            logger.exception(f"An unexpected error occurred while loading the sprite: {e}")
            self.sprite_label.config(text="Error Loading Sprite", font=("Arial", 8))

    def _get_title_text(self):
        """Returns the formatted title text."""
        if self.pokemon:
            return f"{self.pokemon.name.capitalize()} - #{self.pokemon.id} {'★' if self.is_favourite else ''}"
        return ""

    def handle_up(self):
        logger.debug("Navigating up in DetailView")
        self._scroll_canvas("Up")

    def handle_down(self):
        logger.debug("Navigating down in DetailView")
        self._scroll_canvas("Down")

    def handle_left(self):
        logger.debug("No action for Left button in DetailView")

    def handle_right(self):
        logger.debug("No action for Right button in DetailView")

    def handle_select(self):
        logger.debug("No action for A button in DetailView")

    def handle_back(self):
        logger.debug("Going back to PokedexView from DetailView")
        self.app.go_back()

    def handle_start(self):
        logger.debug("No action for Start button in DetailView")

    def handle_favourite_toggle(self):
        """Handles the Select button press to toggle favourites."""
        logger.debug(f"Toggling favourite status for Pokémon ID: {self.pokemon_id}...")
        try:
            if self.pokemon:
                self.is_favourite = not self.is_favourite
                self.data_manager.update_favourite_status(self.pokemon.id, self.is_favourite)
                self.update_title()
                logger.debug(f"Favourite status toggled to: {self.is_favourite}")
        except Exception as e:
            logger.error(f"Error toggling favourite: {e}")

    def update_title(self):
        """Updates the title label to reflect favourite status."""
        try:
            if self.pokemon:
                self.pokemon_name_label.config(text=self._get_title_text())
                logger.debug("Title label updated.")

        except Exception as e:
            logger.error(f"Error updating title in DetailView: {e}")

    def _scroll_canvas(self, direction):
        """Scrolls the canvas up or down."""
        if direction == "Up":
            self.detail_canvas.yview_scroll(-1, "units")
        elif direction == "Down":
            self.detail_canvas.yview_scroll(1, "units")

    def reset_view(self):
        """Resets the DetailView for a new Pokemon."""
        logger.debug("Resetting DetailView")
        # Reset Pokémon data
        self.pokemon_id = None
        self.pokemon = None

        # Clear the title
        self.pokemon_name_label.config(text="")

        # Clear the sprite
        self.sprite_label.config(image=None)
        self.sprite_label.image = None

        # Clear other labels
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, ttk.Label):
                widget.config(text="")
