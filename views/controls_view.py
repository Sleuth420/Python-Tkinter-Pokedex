import logging
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)


class ControlsView(tk.Frame):
    def __init__(self, master, data_manager, app):
        super().__init__(master)
        logger.debug("Initializing ControlsView...")
        self.master = master
        self.app = app
        self.data_manager = data_manager

        self.create_widgets()

    def create_widgets(self):
        """Creates the UI elements for the ControlsView."""
        logger.debug("Creating widgets in ControlsView")

        # Apply custom font to all labels
        font = self.app.custom_font

        # Create a style for bold labels
        style = ttk.Style()
        style.configure("Bold.TLabel", font=font.copy(), weight="bold")

        # Title
        title_label = ttk.Label(self, text="Controls", style="Bold.TLabel")
        title_label.pack(pady=(5, 5))

        # Canvas for scrollable content
        self.controls_canvas = tk.Canvas(self)
        self.controls_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.controls_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.controls_canvas.configure(yscrollcommand=self.scrollbar.set)

        # Content frame
        self.content_frame = ttk.Frame(self.controls_canvas)
        self.controls_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        # Controls Information
        self.create_controls_info()

        # Configure canvas scroll region (update when content changes)
        self.content_frame.bind("<Configure>", self.on_frame_configure)

    def on_frame_configure(self, event):
        """Update the scroll region when the content frame is resized."""
        self.controls_canvas.configure(scrollregion=self.controls_canvas.bbox("all"))

    def create_controls_info(self):
        """Creates and arranges the controls information labels."""
        logger.debug("Creating controls information labels")

        # Apply custom font to all labels
        font = self.app.custom_font

        # Menu View Controls
        menu_frame = ttk.LabelFrame(self.content_frame, text="Menu")
        menu_frame.pack(pady=5, padx=10, fill=tk.X)

        ttk.Label(menu_frame, text="This is the main menu.", font=font).pack(anchor="w")
        ttk.Label(menu_frame, text="A: Select", font=font).pack(anchor="w")
        ttk.Label(menu_frame, text="B: Nothing", font=font).pack(anchor="w")
        ttk.Label(menu_frame, text="Up: Navigate Up", font=font).pack(anchor="w")
        ttk.Label(menu_frame, text="Down: Navigate Down", font=font).pack(anchor="w")
        ttk.Label(menu_frame, text="Start: Settings", font=font).pack(anchor="w")

        # Pokedex View Controls
        pokedex_frame = ttk.LabelFrame(self.content_frame, text="Pokédex")
        pokedex_frame.pack(pady=5, padx=10, fill=tk.X)

        ttk.Label(pokedex_frame, text="Browse and search for Pokémon.", font=font).pack(anchor="w")
        ttk.Label(pokedex_frame, text="A: Select Pokémon (opens Detail View)", font=font).pack(anchor="w")
        ttk.Label(pokedex_frame, text="B: Back to Previous View", font=font).pack(anchor="w")
        ttk.Label(pokedex_frame, text="Up: Previous Pokémon / Navigate to Search Bar", font=font).pack(anchor="w")
        ttk.Label(pokedex_frame, text="Down: Next Pokémon / Navigate to Treeview", font=font).pack(anchor="w")
        ttk.Label(pokedex_frame, text="Left/Right: Navigate in Search Area", font=font).pack(anchor="w")
        ttk.Label(pokedex_frame, text="Start: Toggle Search Mode", font=font).pack(anchor="w")
        ttk.Label(pokedex_frame, text="Select: Toggle Favourite", font=font).pack(anchor="w")

        # Pokemon Detail View Controls
        detail_frame = ttk.LabelFrame(self.content_frame, text="Pokémon Detail")
        detail_frame.pack(pady=5, padx=10, fill=tk.X)

        ttk.Label(detail_frame, text="View detailed information about a Pokémon.", font=font).pack(anchor="w")
        ttk.Label(detail_frame, text="Select: Favourite/Unfavourite Pokémon", font=font).pack(anchor="w")
        ttk.Label(detail_frame, text="Up: Scroll Up", font=font).pack(anchor="w")
        ttk.Label(detail_frame, text="Down: Scroll Down", font=font).pack(anchor="w")
        ttk.Label(detail_frame, text="B: Back to Previous View", font=font).pack(anchor="w")

        # Favourites View Controls
        favourites_frame = ttk.LabelFrame(self.content_frame, text="Favourites")
        favourites_frame.pack(pady=5, padx=10, fill=tk.X)

        ttk.Label(favourites_frame, text="View and manage your favourite Pokémon.", font=font).pack(anchor="w")
        ttk.Label(favourites_frame, text="A: Select Pokémon (opens Detail View)", font=font).pack(anchor="w")
        ttk.Label(favourites_frame, text="B: Back to Previous View", font=font).pack(anchor="w")
        ttk.Label(favourites_frame, text="Up: Previous Pokémon / Navigate to Search Bar", font=font).pack(anchor="w")
        ttk.Label(favourites_frame, text="Down: Next Pokémon / Navigate to Treeview", font=font).pack(anchor="w")
        ttk.Label(favourites_frame, text="Left/Right: Navigate in Search Area", font=font).pack(anchor="w")
        ttk.Label(favourites_frame, text="Start: Toggle Search Mode", font=font).pack(anchor="w")
        ttk.Label(favourites_frame, text="Select: Toggle Favourite (removes from Favourites)", font=font).pack(anchor="w")

        # Settings View Controls
        settings_frame = ttk.LabelFrame(self.content_frame, text="Settings")
        settings_frame.pack(pady=5, padx=10, fill=tk.X)

        ttk.Label(settings_frame, text="Configure Wi-Fi, Theme, and application settings.", font=font).pack(anchor="w")
        ttk.Label(settings_frame, text="A: Select/Activate", font=font).pack(anchor="w")
        ttk.Label(settings_frame, text="B: Back to Main Menu", font=font).pack(anchor="w")
        ttk.Label(settings_frame, text="Up/Down: Navigate Settings Options", font=font).pack(anchor="w")

    def handle_up(self):
        logger.debug("Navigating up in ControlsView (scrolling)")
        self.controls_canvas.yview_scroll(-1, "units")

    def handle_down(self):
        logger.debug("Navigating down in ControlsView (scrolling)")
        self.controls_canvas.yview_scroll(1, "units")

    def handle_left(self):
        logger.debug("No action for Left button in ControlsView")

    def handle_right(self):
        logger.debug("No action for Right button in ControlsView")

    def handle_select(self):
        logger.debug("No action for A button in ControlsView")

    def handle_back(self):
        logger.debug("Going back to MenuView from ControlsView")
        self.app.go_back()

    def handle_start(self):
        logger.debug("No action for Start button in ControlsView")

    def handle_favourite_toggle(self):
        logger.debug("No action for Favourite Toggle button in ControlsView")
