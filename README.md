# Raspberry Pi Tkinter Pokedex

This project is a Raspberry Pi-powered Pokedex application built with Tkinter, designed to be used with a custom GPIO button interface. It fetches data from the PokeAPI to display information about Pokemon, including their stats, types, and descriptions.

## Features

*   Browse Pokemon by ID or name.
*   View detailed information about each Pokemon.
*   Mark Pokemon as favourites for quick access.
*   Navigate the Pokedex using GPIO buttons connected to your Raspberry Pi.
*   Modern user interface design.

## Installation

1.  Clone the repository: `git clone https://github.com/sleuth420/python-tkinter-pokedex`
2.  Configure your venv
3.  Install dependencies: `pip install -r requirements.txt`
4.  Configure GPIO pins in `input_handler.py` to match your setup.
5.  Correct all necessary file paths
6.  Populate your database by running `data_manager.py`
7.  Run `main.py`

## Usage

1.  Run the application: `python main.py`
2.  Use the GPIO buttons to navigate through the Pokedex

## To-Do

-  Fix and Implement Custom Font
-  Fix and Implement More themes
-  Fix and Improve DataManager
-  Fix and Implement Settings
-  Streamline UI
-  Loading Screen
-  Threading
-  Much More...