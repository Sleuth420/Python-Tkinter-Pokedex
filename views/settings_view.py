import configparser
import logging
import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from plugins.custom_keyboard import CustomKeyboard

logger = logging.getLogger(__name__)


class SettingsView(tk.Frame):
    def __init__(self, master, data_manager, app):
        super().__init__(master)
        logger.debug("Initializing SettingsView...")

        self.master = master
        self.data_manager = data_manager
        self.app = app
        self.keyboard = None

        self.current_selection = 0
        self.settings_widgets = []

        # Read settings from settings.ini
        self.config = configparser.ConfigParser()
        settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'settings.ini')
        self.config.read(settings_path)

        # Initialize StringVar variables
        self.current_ssid_var = tk.StringVar()
        self.theme_var = tk.StringVar()
        self.wifi_enabled = tk.BooleanVar()

        self.create_widgets()
        self.read_settings()
        self.update_current_ssid()

    def create_widgets(self):
        """Creates the UI elements for the settings view."""
        try:
            logger.debug("Creating widgets in SettingsView")

            # Apply custom font
            font = self.app.custom_font

            # Title Label for SettingsView
            title_label = ttk.Label(self, text="Settings", font=font)
            title_label.pack(pady=(5, 0))

            # --- Wifi Settings ---
            wifi_frame = ttk.LabelFrame(self, text="Wi-Fi Settings")
            wifi_frame.pack(pady=5, padx=10, fill=tk.X)

            wifi_label = ttk.Label(wifi_frame, text="Wi-Fi Settings", font=font)
            wifi_label.pack()

            # Current SSID Label
            ssid_label = ttk.Label(wifi_frame, textvariable=self.current_ssid_var, font=font)
            ssid_label.pack(padx=5, anchor="w")

            wifi_checkbox = ttk.Checkbutton(wifi_frame, text="Enable Wi-Fi", variable=self.wifi_enabled,
                                            command=self.toggle_wifi, font=font)
            wifi_checkbox.pack(padx=5, anchor="w")
            self.settings_widgets.append(wifi_checkbox)

            self.wifi_list_button = ttk.Button(wifi_frame, text="Available Networks",
                                               command=self.show_available_networks, font=font,
                                               state=tk.NORMAL if self.wifi_enabled.get() else tk.DISABLED)
            self.wifi_list_button.pack(padx=5, anchor="w")
            self.settings_widgets.append(self.wifi_list_button)

            # --- Theme Settings ---
            theme_frame = ttk.LabelFrame(self, text="Theme", font=font)
            theme_frame.pack(pady=5, padx=10, fill=tk.X)

            theme_options = ["breeze", "black", "plastik", "equilux"]
            theme_dropdown = ttk.Combobox(theme_frame, textvariable=self.theme_var, values=theme_options, width=10,
                                          font=font)
            theme_dropdown.pack(side=tk.LEFT, padx=5)
            theme_dropdown.bind("<<ComboboxSelected>>", self.change_theme)
            self.settings_widgets.append(theme_dropdown)

            # --- Application Settings ---
            app_frame = ttk.LabelFrame(self, text="Application", font=font)
            app_frame.pack(pady=5, padx=10, fill=tk.X)

            restart_button = ttk.Button(app_frame, text="Restart App", command=self.restart_app, font=font)
            restart_button.pack(side=tk.LEFT, padx=5)
            self.settings_widgets.append(restart_button)

            # Set initial focus
            self.settings_widgets[0].focus()

            logger.debug("Widgets in SettingsView created successfully.")

        except Exception as e:
            logger.error(f"Error creating widgets in SettingsView: {e}")

    def update_current_ssid(self):
        """Updates the current SSID label."""
        ssid = self.get_current_ssid()
        self.current_ssid_var.set(f"Connected to: {ssid}")

    def get_current_ssid(self):
        """Gets the currently connected SSID using iwconfig."""
        try:
            output = subprocess.check_output(['iwconfig', 'wlan0'], stderr=subprocess.STDOUT, text=True)
            for line in output.split('\n'):
                if "ESSID" in line:
                    ssid = line.split(":")[1].strip().replace('"', '')
                    return ssid
            return "Not Connected"
        except FileNotFoundError:
            logger.error("iwconfig not found. Cannot determine SSID.")
            return "N/A"
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting SSID: {e.output}")
            return "N/A"
        except Exception as e:
            logger.exception(f"An unexpected error occurred while getting the current SSID: {e}")
            return "N/A"

    def is_wifi_enabled(self):
        """Checks if Wi-Fi is enabled."""
        try:
            output = subprocess.check_output(['rfkill', 'list', 'wifi'], text=True)
            return "unblocked" in output.lower()
        except FileNotFoundError:
            logger.error("rfkill not found, cannot determine Wi-Fi state.")
            return False
        except Exception as e:
            logger.exception("Unexpected error checking Wi-Fi status")
            return False

    def toggle_wifi(self):
        """Toggles Wi-Fi on/off."""
        try:
            if self.wifi_enabled.get():
                subprocess.run(['rfkill', 'unblock', 'wifi'])
                logger.debug("Wi-Fi enabled.")
            else:
                subprocess.run(['rfkill', 'block', 'wifi'])
                logger.debug("Wi-Fi disabled.")

            self.wifi_list_button.config(
                state=tk.NORMAL if self.wifi_enabled.get() else tk.DISABLED)
            self.update_current_ssid()

            # Update settings.ini
            self.write_settings()
        except Exception as e:
            logger.exception(f"Error toggling Wi-Fi: {e}")
            messagebox.showerror("Error", f"Failed to toggle Wi-Fi: {e}")

    def show_available_networks(self):
        """Shows a list of available Wi-Fi networks and handles connection."""

        try:
            scan_output = subprocess.check_output(['nmcli', 'dev', 'wifi'], stderr=subprocess.STDOUT, text=True)
            networks = []
            for line in scan_output.splitlines()[1:]:  # Skip the header line
                parts = line.split()
                if len(parts) >= 9:  # SSID in the 9th position
                    networks.append(parts[8])

            if not networks:
                messagebox.showinfo("No Networks", "No Wi-Fi networks found.")
                return

            self._show_network_selection(networks)

        except FileNotFoundError:
            logger.error("nmcli not found.")
            messagebox.showerror("Error", "Network Manager is not available.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error scanning for networks: {e.output}")
            messagebox.showerror("Error", f"Failed to scan for networks: {e.output}")
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            messagebox.showerror("Error", "Failed to scan for networks.")

    def _show_network_selection(self, networks):
        """Displays a dialog to select a network."""

        def _connect_to_network():
            """Connect to the selected network."""
            try:
                selected_network = network_listbox.get(tk.ACTIVE)

                if selected_network:
                    if self._needs_password(selected_network):
                        self._get_network_credentials(selected_network, lambda password:
                        self._connect(selected_network, password))
                    else:
                        self._connect(selected_network, None)
                    network_dialog.destroy()

            except Exception as e:
                logger.exception("Error connecting to network:")
                messagebox.showerror("Error", "Failed to connect to network.")

        network_dialog = tk.Toplevel(self)
        network_dialog.title("Available Networks")

        network_listbox = tk.Listbox(network_dialog, selectmode=tk.SINGLE, font=("Arial", 10), width=30)
        for network in networks:
            network_listbox.insert(tk.END, network)

        network_listbox.pack(expand=True, fill=tk.BOTH)

        # Custom Keyboard integration for password entry
        if not self.keyboard:
            self.keyboard = CustomKeyboard(network_dialog, self.search_bar)
        self.keyboard.pack(pady=5)

        connect_button = ttk.Button(network_dialog, text="Connect", command=_connect_to_network)
        connect_button.pack(pady=(0, 5))

        network_listbox.focus_set()
        network_listbox.selection_set(0)

    def _needs_password(self, ssid):
        """Checks if the network needs a password using nmcli."""
        try:
            command = ['nmcli', 'dev', 'wifi', 'list', '--rescan', 'yes', "|", "grep", f'"{ssid}"']
            output = subprocess.check_output(" ".join(command), shell=True, text=True)
            return "WPA" in output or "WEP" in output or "802.1X" in output
        except FileNotFoundError:
            logger.error("nmcli not found, cannot determine if wifi needs password")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Error checking network security: {e.output}")
            return False
        except Exception as e:
            logger.exception(f"An unexpected error occurred while checking if the network requires a password: {e}")
            return False

    def _get_network_credentials(self, ssid,
                                 callback):
        """Gets the network credentials (password) from the user."""

        def _on_enter_pressed():
            password = password_entry.get()
            credential_dialog.destroy()
            callback(password)

        credential_dialog = tk.Toplevel(self)
        credential_dialog.title(f"Connect to {ssid}")

        password_label = ttk.Label(credential_dialog, text="Password:")
        password_label.pack(pady=5)

        password_entry = ttk.Entry(credential_dialog, show="*", width=20)
        password_entry.pack()
        password_entry.bind("<Return>", lambda event: _on_enter_pressed())

        if not self.keyboard:
            self.keyboard = CustomKeyboard(credential_dialog, password_entry)
        self.keyboard.pack(pady=5)

        connect_button = ttk.Button(credential_dialog, text="Connect", command=_on_enter_pressed)
        connect_button.pack(pady=(0, 5))

        password_entry.focus_set()

    def _connect(self, ssid, password):
        """Connects to the specified network."""

        try:
            # Construct command with or without a password
            command = ["nmcli", "dev", "wifi", "connect", f'"{ssid}"']
            if password:
                command.extend(["password", f'"{password}"'])

            subprocess.run(command, check=True, text=True)
            self.update_current_ssid()
            logger.info(f"Connected to {ssid}")
            messagebox.showinfo("Success", f"Connected to {ssid}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to connect to {ssid}: {e.output}")
            messagebox.showerror("Error", f"Failed to connect to {ssid}:\n{e.output}")
        except Exception as e:
            logger.exception(f"An unexpected error occurred while connecting to {ssid}: {e}")
            messagebox.showerror("Error", f"Failed to connect to {ssid}")

    def change_theme(self, event=None):
        """Changes the application's theme."""
        try:
            new_theme = self.theme_var.get()
            logger.debug(f"Theme changed to: {new_theme}")

            # Update settings.ini
            self.write_settings()

            messagebox.showinfo("Theme Changed", "The application will now restart to apply the new theme.")
            self.after(100, self.restart_app)

        except Exception as e:
            logger.error(f"Error changing theme: {e}")
            messagebox.showerror("Error", f"Failed to change theme: {e}")

    def restart_app(self):
        """Restarts the application."""
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def handle_up(self):
        """Handles the Up button press."""
        logger.debug("Navigating up in SettingsView")
        self.current_selection = (self.current_selection - 1) % len(self.settings_widgets)
        self.settings_widgets[self.current_selection].focus()

    def handle_down(self):
        """Handles the Down button press."""
        logger.debug("Navigating down in SettingsView")
        self.current_selection = (self.current_selection + 1) % len(self.settings_widgets)
        self.settings_widgets[self.current_selection].focus()

    def handle_select(self):
        """Handles the A button press."""
        logger.debug("Handling select in SettingsView")
        widget = self.settings_widgets[self.current_selection]
        if isinstance(widget, ttk.Button):
            widget.invoke()
        elif isinstance(widget, ttk.Checkbutton):
            widget.toggle()
        elif isinstance(widget, ttk.Combobox):
            widget.event_generate('<Button-1>')

    def handle_back(self):
        """Handles the B button press."""
        logger.debug("Going back to MenuView from SettingsView")
        self.app.show_view("MenuView")

    def handle_left(self):
        logger.debug("No action for Left button in SettingsView")

    def handle_right(self):
        logger.debug("No action for Right button in SettingsView")

    def handle_start(self):
        logger.debug("No action for Start button in SettingsView")

    def read_settings(self):
        """Reads settings from settings.ini."""
        config = configparser.ConfigParser()
        config.read('settings.ini')
        self.theme_var.set(config.get('Appearance', 'theme', fallback='breeze'))
        self.wifi_enabled.set(config.getboolean('Network', 'wifi_enabled', fallback=True))

    def write_settings(self):
        """Writes settings to settings.ini."""
        config = configparser.ConfigParser()
        config['Appearance'] = {'theme': self.theme_var.get()}
        config['Network'] = {'wifi_enabled': self.wifi_enabled.get()}
        with open('settings.ini', 'w') as configfile:
            config.write(configfile)
