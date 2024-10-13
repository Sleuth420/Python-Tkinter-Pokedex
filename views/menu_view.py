import configparser
import logging
import os
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

logger = logging.getLogger(__name__)


class MenuView(tk.Frame):
    def __init__(self, master, data_manager, app):
        super().__init__(master)
        logger.debug("Initializing MenuView")
        self.master = master
        self.app = app
        self.data_manager = data_manager

        self.menu_buttons = []
        self.selected_button_index = 0

        # Read settings from settings.ini
        self.config = configparser.ConfigParser()
        settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'settings.ini')
        self.config.read(settings_path)

        self.pack(fill=tk.BOTH, expand=True)

        self.frame = ttk.Frame(self)
        self.frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.create_logo()
        self.create_menu_buttons()

        if self.menu_buttons:
            self.menu_buttons[0].focus_set()
            self.update_button_focus()

        # Copyright and version labels at the bottom
        copyright_version_frame = tk.Frame(self)
        copyright_version_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 5))

        self.copyright_label = tk.Label(copyright_version_frame, text="\u00A9 R&R",
                                        font=self.app.custom_font)
        self.copyright_label.pack(side=tk.LEFT, anchor="sw")

        # Read version from settings.ini
        version = self.config.get('Application', 'version', fallback='N/A')
        self.version_label = tk.Label(copyright_version_frame, text=f"v{version}",
                                      font=self.app.custom_font)
        self.version_label.pack(side=tk.RIGHT, anchor="se")

    def create_logo(self):
        """Creates and displays the Pokedex logo."""
        logger.debug("Creating logo in MenuView")

        try:
            # Read logo path from settings.ini (Corrected path)
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                     self.config.get('Assets', 'logo_path', fallback='assets/pokedex_logo.png'))
            logo_img = Image.open(logo_path)
            logger.debug(f"Opened logo image: {logo_path}")

            logo_img = logo_img.resize((140, 56), Image.Resampling.LANCZOS)
            logger.debug("Resized logo image")

            self.logo_photo = ImageTk.PhotoImage(logo_img)
            logger.debug("Created PhotoImage from logo")

            self.logo_label = tk.Label(self.frame, image=self.logo_photo)
            logger.debug("Created logo label with PhotoImage")
            self.logo_label.pack(pady=(5, 5), anchor="center")
            logger.debug("Displayed logo in a label")

        except FileNotFoundError:
            logger.error(f"Error: Image not found at '{logo_path}'")
            self.logo_label = tk.Label(self.frame, text="Error: Logo not found", font=self.app.custom_font,
                                       foreground="red")
            self.logo_label.pack(pady=(10, 5))

        except Exception as e:
            logger.exception(f"An unexpected error occurred while creating the logo: {e}")
            self.logo_label = tk.Label(self.frame, text="Error loading logo", font=self.app.custom_font,
                                       foreground="red")
            self.logo_label.pack(pady=(10, 5))

    def create_menu_buttons(self):
        """Creates the buttons for the menu options."""
        logger.debug("Creating menu buttons in MenuView")

        # Create a style for the buttons
        style = ttk.Style()
        style.configure('MenuButton.TButton', font=self.app.custom_font)
        style.map("MenuButton.TButton",
                  foreground=[('pressed', 'black'), ('active', 'black')],
                  background=[('pressed', '!disabled', 'black'),
                              ('active', '!disabled', 'black')])

        menu_options = [
            {"text": "Pokédex", "command": self.show_pokedex},
            {"text": "Favourites", "command": self.show_favourites},
            {"text": "Settings", "command": self.show_settings},
            {"text": "Controls", "command": self.show_controls}
        ]

        for i, option in enumerate(menu_options):
            button = ttk.Button(self.frame, text=option["text"], command=option["command"], style='MenuButton.TButton')
            button.pack(pady=1, padx=3, fill=tk.X)
            self.menu_buttons.append(button)
            logger.debug(f"Created and packed menu button: {option['text']}")

    def show_pokedex(self):
        self.app.show_view("PokedexView")

    def show_favourites(self):
        self.app.show_view("FavouritesView")

    def show_settings(self):
        self.app.show_view("SettingsView")

    def show_controls(self):
        self.app.show_view("ControlsView")

    def handle_up(self):
        logger.debug("Handling up button in MenuView")
        self.selected_button_index = (self.selected_button_index - 1) % len(self.menu_buttons)
        self.update_button_focus()
        logger.debug(f"Selected button index: {self.selected_button_index}")

    def handle_down(self):
        logger.debug("Handling down button in MenuView")
        self.selected_button_index = (self.selected_button_index + 1) % len(self.menu_buttons)
        self.update_button_focus()
        logger.debug(f"Selected button index: {self.selected_button_index}")

    def handle_left(self):
        logger.debug("Handling left button in MenuView (no action)")
        pass  # No action

    def handle_right(self):
        logger.debug("Handling right button in MenuView (no action)")
        pass  # No action

    def handle_select(self):
        logger.debug("Handling select button in MenuView")
        self.menu_buttons[self.selected_button_index].invoke()

    def handle_back(self):
        logger.debug("Handling back button in MenuView (no action)")
        pass  # No action on the main menu

    def handle_start(self):
        logger.debug("Handling start button in MenuView")
        self.app.show_view("SettingsView")

    def handle_favourite_toggle(self):
        logger.debug("Handling favourite toggle in MenuView")
        pass

    def update_button_focus(self):
        """Updates the focus highlight on the selected button."""
        for i, button in enumerate(self.menu_buttons):
            if i == self.selected_button_index:
                button.state(['pressed'])
            else:
                button.state(['!pressed'])
