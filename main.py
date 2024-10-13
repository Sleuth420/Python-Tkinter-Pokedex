import configparser
import logging
import os
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox

from ttkthemes import ThemedTk

import logger_setup
from database.data_manager import PokemonDataManager
from input_handler import InputHandler
from ui import PokedexApp

logger_setup.setup_logging()

logger = logging.getLogger(__name__)


def show_error_window(message, title="Error"):
    """Shows an error window in a separate thread."""

    def _show_error():
        messagebox.showerror(title, message)

    # Schedule the error dialog to be displayed in the main thread
    tk.Tk().after(0, _show_error)


def main():
    logger.info("----- Starting Pokédex Application -----")
    logger.debug(f"Current working directory: {os.getcwd()}")

    try:
        # Read settings from settings.ini
        config = configparser.ConfigParser()
        config.read('settings.ini')
        logger.debug("Settings loaded from settings.ini")

        # --- Screen Configuration ---
        screen_width = config.getint('Screen', 'width', fallback=264)
        screen_height = config.getint('Screen', 'height', fallback=240)
        resizable_width = config.getboolean('Screen', 'resizable_width', fallback=False)
        resizable_height = config.getboolean('Screen', 'resizable_height', fallback=False)
        fullscreen = config.getboolean('Screen', 'fullscreen', fallback=True)

        # --- Appearance ---
        default_theme = config.get('Appearance', 'theme', fallback='breeze')
        font_name = config.get('Appearance', 'font_name', fallback='Arial')
        font_size = config.getint('Appearance', 'font_size', fallback=10)
        font_path = config.get('Assets', 'font_path',
                               fallback='assets/Pokemon.ttf')

        # --- Database ---
        database_file = os.path.join(os.path.dirname(__file__), config.get('Database', 'database_file',
                                                                           fallback='database/data/pokedex.db'))

        # Tkinter Initialization
        logger.debug("Initializing Tkinter...")
        root = ThemedTk(theme=default_theme)
        root.title("Pokedex")

        root.geometry(f"{screen_width}x{screen_height}+0+0")
        root.resizable(resizable_width, resizable_height)
        root.attributes('-fullscreen', fullscreen)
        logger.info(f"Window size set to: {screen_width}x{screen_height}")

        # --- Font Loading ---
        logger.debug(f"Available font families before loading custom font: {tk.font.families()}")
        logger.debug(f"Font name from settings.ini: {font_name}")
        logger.debug(f"Font size from settings.ini: {font_size}")
        logger.debug(f"Font path from settings.ini: {font_path}")

        try:

            if font_name != 'Arial':
                font_dir = os.path.join(os.path.dirname(__file__), os.path.dirname(font_path))
                logger.debug(f"Calculated font directory: {font_dir}")

                if not os.path.exists(os.path.join(font_dir, font_name)):
                    raise FileNotFoundError(f"Font file not found: {os.path.join(font_dir, font_name)}")

                tkfont.Font(family=font_name, size=font_size).metrics()
                logger.debug(f"Loaded font metrics for '{font_name}'")

                tk.font.families()
                logger.debug(f"Available font families after loading: {tk.font.families()}")

            custom_font = tkfont.Font(family=font_name, size=font_size)
            logger.debug(
                f"Created custom font object. Family: {custom_font.cget('family')}, Size: {custom_font.cget('size')}")
        except tk.TclError as e:
            logger.error(f"Error loading custom font '{font_name}': {e}")
            custom_font = tkfont.Font(family="Arial", size=10)

        # GPIO Initialization
        gpio = None
        if os.name == 'posix':
            try:
                import RPi.GPIO as GPIO

                logger.debug("RPi.GPIO module imported.")
                GPIO.setmode(GPIO.BCM)
                logger.info("GPIO initialized in BCM mode.")
                gpio = GPIO
            except (ImportError, RuntimeError) as e:
                logger.critical(f"GPIO initialization failed: {e}")
                show_error_window(f"GPIO Error: {e}")
        else:
            logger.warning("Non-POSIX system detected. GPIO functionality unavailable.")

        # Application Initialization
        try:
            data_manager = PokemonDataManager(database_file)
            app = PokedexApp(root, data_manager,
                             custom_font)
            root.app = app

            input_handler = InputHandler(app)
            app.set_input_handler(input_handler)

            input_handler.check_gpio_input()
            logger.debug("GPIO polling loop started.")

            root.mainloop()

        except Exception as e:
            logger.exception(f"Application initialization failed: {e}")
            show_error_window(f"Application Error: {e}")

    except Exception as e:
        logger.exception(f"A critical error occurred during startup: {e}")
        show_error_window(f"Critical Error: {e}")


if __name__ == "__main__":
    main()
