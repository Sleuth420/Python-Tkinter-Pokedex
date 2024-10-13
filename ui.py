import logging
import tkinter as tk

from views import menu_view, pokedex_view, detail_view, favourites_view, settings_view, controls_view

logger = logging.getLogger(__name__)


class PokedexApp:
    def __init__(self, master, data_manager, custom_font):
        self.master = master
        self.data_manager = data_manager
        self.custom_font = custom_font
        logger.debug("Initializing PokedexApp")

        self.views = {}
        self.current_view = None
        self.view_history = []

        self.show_view("MenuView")

    def show_view(self, view_name, *args):
        """Switches between different views in the application."""
        logger.debug(f"Switching to view: {view_name} from {self.current_view}")

        if self.current_view:
            self.current_view.pack_forget()

            # Only push to history if NOT DetailView
            if self.current_view.__class__.__name__ != "DetailView":
                self.view_history.append(self.current_view)

        view_classes = {
            "MenuView": menu_view.MenuView,
            "PokedexView": pokedex_view.PokedexView,
            "DetailView": detail_view.DetailView,
            "FavouritesView": favourites_view.FavouritesView,
            "SettingsView": settings_view.SettingsView,
            "ControlsView": controls_view.ControlsView,
        }

        if view_name in view_classes:
            logger.debug(f"Initializing view: {view_name}")
            try:
                if view_name not in self.views:
                    self.views[view_name] = view_classes[view_name](self.master, self.data_manager, self, *args)
                else:
                    # Re-initialize DetailView if it already exists
                    if view_name == "DetailView":
                        # Destroy the existing DetailView
                        self.views[view_name].destroy()
                        # Create a new DetailView with the new pokemon_id
                        self.views[view_name] = view_classes[view_name](self.master, self.data_manager, self, *args)

                # Call reset_view() for all views EXCEPT SettingsView
                if hasattr(self.views[view_name], "reset_view") and view_name != "SettingsView":
                    self.views[view_name].reset_view()

                self.current_view = self.views[view_name]
                self.current_view.pack(fill=tk.BOTH, expand=True)
                logger.debug(f"View '{view_name}' initialized and displayed successfully.")

            except Exception as e:
                logger.exception(f"Error initializing view '{view_name}': {e}")
        else:
            logger.error(f"Error: View '{view_name}' not found.")

    def go_back(self):
        """Navigates to the previous view in the history."""
        logger.debug("Going back to previous view")
        if self.view_history:
            previous_view = self.view_history.pop()
            self.show_view(previous_view.__class__.__name__)
        else:
            logger.warning("View history is empty. Cannot go back.")

    def _handle_input(self, handler_name):
        """Handles input by calling the appropriate handler method in the current view."""
        if self.current_view:
            handler = getattr(self.current_view, handler_name, None)
            if handler:
                handler()

    def handle_up(self):
        self._handle_input("handle_up")

    def handle_down(self):
        self._handle_input("handle_down")

    def handle_left(self):
        self._handle_input("handle_left")

    def handle_right(self):
        self._handle_input("handle_right")

    def handle_select(self):
        self._handle_input("handle_select")

    def handle_back(self):
        self._handle_input("handle_back")

    def handle_start(self):
        self._handle_input("handle_start")

    def handle_favourite_toggle(self):
        self._handle_input("handle_favourite_toggle")

    def set_input_handler(self, input_handler):
        """Sets the input handler for the application."""
        self.input_handler = input_handler
