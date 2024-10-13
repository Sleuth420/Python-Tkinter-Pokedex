import configparser
import logging
import os
import sqlite3
import time

import requests
import requests_cache
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from models import Pokemon, Berry, Evolution

logger = logging.getLogger(__name__)


class DataManagerError(Exception):
    """Base class for exceptions in this module."""
    pass


class DatabaseConnectionError(DataManagerError):
    """Exception raised for errors in database connection."""
    pass


class PokemonDataManager:
    def __init__(self, db_file=None):
        """Initializes the PokemonDataManager with database connection and API setup."""
        logger.debug("Entering PokemonDataManager.__init__")
        self.db_file = db_file
        self.conn = None
        self.max_retries = 3
        self.backoff_factor = 1

        # Read settings from settings.ini
        self.config = configparser.ConfigParser()
        self.config.read('settings.ini')

        # Get database file path from settings.ini
        self.db_file = self.config.get('Database', 'database_file',
                                       fallback='/home/dev/pokedex_app/pokedexpi4.0/database/data/pokedex.db')

        try:
            self.conn = self._create_connection()
        except DatabaseConnectionError as e:
            logger.exception("Failed to create database connection:")
            raise

        self._create_tables()

        try:
            self.cache = requests_cache.install_cache(
                cache_name=os.path.join(os.path.dirname(self.db_file), 'pokedex_cache.sqlite'),
                backend='sqlite',
                expire_after=3600
            )
            logger.debug("API request cache set up successfully.")
        except Exception as e:
            logger.exception("Error setting up API request cache:")

        self.retries = Retry(
            total=5,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=0.3,
            respect_retry_after_header=True
        )
        adapter = HTTPAdapter(max_retries=self.retries)
        self.http = requests.Session()
        self.http.mount("https://", adapter)
        self.http.mount("http://", adapter)
        logger.debug("Retry strategy for API requests configured.")

        logger.debug("PokemonDataManager initialized.")

    def _create_connection(self):
        """Creates a connection to the SQLite database."""
        logger.debug(f"Attempting connection to database: {self.db_file}")
        for attempt in range(self.max_retries):
            try:
                conn = sqlite3.connect(self.db_file, timeout=10)
                logger.info(f"Successfully connected to database: {self.db_file} (SQLite {sqlite3.version})")
                return conn
            except sqlite3.Error as e:
                logger.error(f"Database connection error (Attempt {attempt + 1}/{self.max_retries}): {e}")
                time.sleep(self.backoff_factor * (2 ** attempt))

        logger.critical(f"Failed to connect to database after {self.max_retries} retries.")
        raise DatabaseConnectionError(f"Failed to connect to database after {self.max_retries} retries.")

    def _create_database_file(self):
        """Creates the database file if it doesn't exist."""
        logger.debug(f"Creating database file: {self.db_file}")
        try:
            os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
            if not os.path.exists(self.db_file):
                with open(self.db_file, 'a'):
                    pass
                logger.info(f"Database file created: {self.db_file}")
        except OSError as e:
            logger.error(f"Error creating database file: {e}")

    def _create_tables(self):
        """Creates the necessary tables if they don't exist."""
        logger.debug("Creating database tables...")
        self._create_pokemon_table()
        self._create_berries_table()
        self._create_evolutions_table()
        self._create_pokemon_types_table()
        self._create_berry_flavors_table()
        logger.info("Database tables created successfully.")

    def _create_pokemon_table(self):
        """Creates the pokemon table."""
        logger.debug("Creating Pokemon table...")
        sql_create_pokemon_table = """
        CREATE TABLE IF NOT EXISTS pokemon (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type1 TEXT NOT NULL,
            type2 TEXT,
            hp INTEGER,
            attack INTEGER,
            defense INTEGER,
            sp_atk INTEGER,
            sp_def INTEGER,
            speed INTEGER,
            sprite_front TEXT,
            sprite_back TEXT,
            description TEXT,
            is_favourite INTEGER DEFAULT 0
        );
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_create_pokemon_table)
            logger.info("Pokemon table created successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error creating Pokemon table: {e}")

    def _create_pokemon_types_table(self):
        """Creates the pokemon_types table."""
        logger.debug("Creating Pokemon types table...")
        sql_create_pokemon_types_table = """
        CREATE TABLE IF NOT EXISTS pokemon_types (
            id INTEGER PRIMARY KEY,
            pokemon_id INTEGER,
            type TEXT,
            FOREIGN KEY (pokemon_id) REFERENCES pokemon(id)
        );
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_create_pokemon_types_table)
            logger.info("Pokemon types table created successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error creating Pokemon types table: {e}")

    def _create_berries_table(self):
        """Creates the berries table."""
        logger.debug("Creating Berries table...")
        sql_create_berries_table = """
                    CREATE TABLE IF NOT EXISTS berries (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        growth_time INTEGER,
                        max_harvest INTEGER,
                        natural_gift_power INTEGER,
                        size INTEGER,
                        smoothness INTEGER,
                        soil_dryness INTEGER,
                        firmness TEXT
                    );
                    """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_create_berries_table)
            logger.info("Berries table created successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error creating Berries table: {e}")

    def _create_berry_flavors_table(self):
        """Creates the berry_flavors table."""
        logger.debug("Creating Berry flavors table...")
        sql_create_berry_flavors_table = """
        CREATE TABLE IF NOT EXISTS berry_flavors (
            id INTEGER PRIMARY KEY,
            berry_id INTEGER,
            flavor TEXT,
            potency INTEGER,
            FOREIGN KEY (berry_id) REFERENCES berries(id)
        );
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_create_berry_flavors_table)
            logger.info("Berry flavors table created successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error creating Berry flavors table: {e}")

    def _create_evolutions_table(self):
        """Creates the evolutions table."""
        logger.debug("Creating Evolutions table...")
        sql_create_evolutions_table = """
                    CREATE TABLE IF NOT EXISTS evolutions (
                        id INTEGER PRIMARY KEY,
                        pokemon_id INTEGER,
                        evolves_to_id INTEGER,
                        trigger TEXT, 
                        level INTEGER,
                        item TEXT,
                        FOREIGN KEY(pokemon_id) REFERENCES pokemon(id),
                        FOREIGN KEY(evolves_to_id) REFERENCES pokemon(id)
                    );
                    """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_create_evolutions_table)
            logger.info("Evolutions table created successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error creating Evolutions table: {e}")

    def close_connection(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")

    def warn_user_about_database(self):
        """
        Displays a warning message to the user if the database file doesn't exist,
        instructing them to update the database from the settings.
        """
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(
            "Database Not Found",
            "The Pokémon database was not found.\n\n"
            "Please go to Settings and update the database."
        )
        root.destroy()

    def get_pokemon_by_id(self, pokemon_id):
        """Fetches a Pokémon by ID from the database, cache, or API."""
        logger.debug(f"Fetching Pokémon with ID {pokemon_id}")

        # 1. Check the Database
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM pokemon WHERE id = ?", (pokemon_id,))
            pokemon_data = cursor.fetchone()

            if pokemon_data:
                logger.debug(f"Pokémon with ID {pokemon_id} found in database.")
                return Pokemon(*pokemon_data)  # Create Pokemon from database data
        except sqlite3.Error as e:
            logger.error(f"Error fetching Pokemon from database: {e}")

        # Get API base URL from settings.ini
        pokeapi_base_url = self.config.get('API', 'pokeapi_base_url', fallback='https://pokeapi.co/api/v2/')

        # 2. Check Cache (if not found in database)
        cached_pokemon = self.cache.get(f"{pokeapi_base_url}pokemon/{pokemon_id}/?expand=species")
        if cached_pokemon:
            logger.debug(f"Pokémon with ID {pokemon_id} found in cache.")
            return Pokemon.from_api_data(cached_pokemon.json())

        # 3. Fetch from API (if not found in database or cache)
        pokemon = self._fetch_pokemon_data(pokemon_id)
        if pokemon:
            logger.debug(f"Caching Pokémon with ID {pokemon_id}")
            self.cache.set(f"{pokeapi_base_url}pokemon/{pokemon_id}/?expand=species", pokemon.to_dict())
            self._insert_pokemon(pokemon)
            return pokemon
        else:
            logger.warning(f"Pokémon with ID {pokemon_id} not found in API.")
            return None

    def _fetch_pokemon_data(self, pokemon_id):
        """Fetches Pokemon data from the PokeAPI, including sprites."""
        logger.debug(f"Fetching Pokemon data for ID: {pokemon_id}")

        # Get API base URL from settings.ini
        pokeapi_base_url = self.config.get('API', 'pokeapi_base_url', fallback='https://pokeapi.co/api/v2/')
        pokemon_url = f"{pokeapi_base_url}pokemon/{pokemon_id}/?expand=species"

        for attempt in range(self.max_retries):
            try:
                response = requests.get(pokemon_url, timeout=10)
                response.raise_for_status()
                pokemon_data = response.json()
                logger.debug(f"Pokemon data fetched successfully for ID: {pokemon_id}")
                return Pokemon.from_api_data(pokemon_data)
            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Error fetching Pokemon data for ID {pokemon_id} (Attempt {attempt + 1}/{self.max_retries}): {e}")
                time.sleep(self.backoff_factor * (2 ** attempt))

        logger.critical(f"Failed to fetch Pokemon data for ID {pokemon_id} after {self.max_retries} retries.")
        return None

    def _insert_pokemon(self, pokemon):
        """Inserts a new pokemon into the pokemon table, including sprites."""
        sql = """ 
        INSERT INTO pokemon(id, name, type1, type2, hp, attack, defense, sp_atk, sp_def, 
                        speed, sprite_front, sprite_back, description, is_favourite)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, pokemon.to_tuple())
            self.conn.commit()
            logger.info(f"Inserted Pokémon with ID {cursor.lastrowid}")

            for pokemon_type in pokemon.types:
                cursor.execute(
                    "INSERT INTO pokemon_types (pokemon_id, type) VALUES (?, ?)",
                    (pokemon.id, pokemon_type)
                )
            self.conn.commit()

        except sqlite3.Error as e:
            logger.error(f"Error inserting Pokémon: {e}")

    def get_all_pokemon(self, search_term=None, limit=None, offset=0, is_favourite=None):
        """Fetches all Pokémon from the database.
        Can be filtered by search_term, paginated, and optionally only return favourites.
        """
        logger.debug(
            f"Fetching all Pokémon from database with search_term='{search_term}', limit={limit}, offset={offset}, is_favourite={is_favourite}")
        try:
            cursor = self.conn.cursor()

            query = "SELECT * FROM pokemon"
            where_clauses = []
            params = []

            if search_term:
                where_clauses.append("name LIKE ?")
                params.append('%' + search_term + '%')

            if is_favourite is not None:
                where_clauses.append("is_favourite = ?")
                params.append(is_favourite)

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            query += " ORDER BY id"

            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            logger.debug(f"Executing SQL query: {query} with params: {params}")
            cursor.execute(query, params)
            pokemon_data = cursor.fetchall()

            pokemon_list = []
            for row in pokemon_data:
                pokemon = Pokemon(*row)
                pokemon_list.append(pokemon)

            logger.debug(f"Fetched {len(pokemon_list)} Pokémon from database.")
            return pokemon_list

        except sqlite3.Error as e:
            logger.error(f"Error fetching all Pokémon: {e}")
            return []

    def get_berry_by_id(self, berry_id):
        """Fetches a berry by its ID from the database."""
        logger.debug(f"Fetching berry with ID {berry_id}.")

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM berries WHERE id = ?", (berry_id,))
            berry_data = cursor.fetchone()

            if berry_data:
                logger.debug(f"Berry with ID {berry_id} found in database.")
                cursor.execute("SELECT flavor, potency FROM berry_flavors WHERE berry_id = ?", (berry_id,))
                flavors = cursor.fetchall()

                berry = Berry(
                    id=berry_data[0],
                    name=berry_data[1],
                    growth_time=berry_data[2],
                    max_harvest=berry_data[3],
                    natural_gift_power=berry_data[4],
                    size=berry_data[5],
                    smoothness=berry_data[6],
                    soil_dryness=berry_data[7],
                    firmness=berry_data[8],
                    flavors=flavors
                )
                return berry
            else:
                logger.debug(f"Berry with ID {berry_id} not found in database.")
                return None

        except sqlite3.Error as e:
            logger.error(f"Error fetching berry by ID {berry_id}: {e}")
            return None

    def get_evolution_chain_for_pokemon(self, pokemon_id):
        """Fetches the evolution chain for a given Pokemon from the database."""
        logger.debug(f"Fetching evolution chain for Pokemon ID: {pokemon_id}")
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                WITH RECURSIVE evolution_chain(pokemon_id, evolves_to_id, trigger, level, item) AS (
                    SELECT pokemon_id, evolves_to_id, trigger, level, item
                    FROM evolutions
                    WHERE pokemon_id = ?
                    UNION ALL
                    SELECT e.pokemon_id, e.evolves_to_id, e.trigger, e.level, e.item
                    FROM evolutions e
                    JOIN evolution_chain ec ON e.pokemon_id = ec.evolves_to_id
                )
                SELECT * FROM evolution_chain;
                """,
                (pokemon_id,),
            )
            evolution_chain = cursor.fetchall()
            logger.debug(f"Fetched evolution chain for Pokemon ID: {pokemon_id}")

            evolution_objects = []
            for row in evolution_chain:
                evolution = Evolution(row[0], row[1], row[2], row[3], row[4])
                evolution_objects.append(evolution)

            return evolution_objects
        except sqlite3.Error as e:
            logger.error(f"Error fetching evolution chain for Pokemon {pokemon_id}: {e}")
            return []

    def get_total_pokemon_count(self):
        """Gets the total number of Pokemon in the database."""
        logger.debug("Getting total Pokemon count from database.")
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM pokemon")
            count = cursor.fetchone()[0]
            logger.debug(f"Total Pokemon count: {count}")
            return count
        except sqlite3.Error as e:
            logger.error(f"Error getting total Pokemon count: {e}")
            return 0

    def populate_database(self, batch_size=50, progress_callback=None):
        """Populates the database with pokemon data, fetching only missing Pokemon."""
        logger.info("Starting Pokemon database population...")

        # Get API base URL from settings.ini
        pokeapi_base_url = self.config.get('API', 'pokeapi_base_url', fallback='https://pokeapi.co/api/v2/')

        offset = 0
        has_more_pokemon = True

        while has_more_pokemon:
            url = f'{pokeapi_base_url}pokemon?limit={batch_size}&offset={offset}'
            for attempt in range(3):
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()

                    pokemon_list = response.json()['results']

                    if not pokemon_list:
                        logger.info("Reached the end of available Pokémon data.")
                        has_more_pokemon = False
                        break

                    for pokemon_data in pokemon_list:
                        pokemon_url = pokemon_data['url']
                        pokemon_id = int(pokemon_url.split('/')[-2])

                        cursor = self.conn.cursor()
                        cursor.execute("SELECT * FROM pokemon WHERE id = ?", (pokemon_id,))
                        existing_pokemon = cursor.fetchone()

                        if existing_pokemon is None:
                            pokemon = self._fetch_pokemon_data(pokemon_id)
                            if pokemon:
                                self._insert_pokemon(pokemon)
                                logger.info(f"Fetched and inserted Pokémon: {pokemon.name} (ID: {pokemon.id})")
                        else:
                            pokemon = self._fetch_pokemon_data(pokemon_id)
                            if pokemon:
                                update_data = {}
                                for i, field in enumerate(
                                        ["name", "type1", "type2", "hp", "attack", "defense", "sp_atk", "sp_def",
                                         "speed",
                                         "sprite_front", "sprite_back", "description", "is_favourite"]
                                ):
                                    if existing_pokemon[i + 1] is None and getattr(pokemon, field) is not None:
                                        update_data[field] = getattr(pokemon, field)

                                if update_data:
                                    self._update_pokemon_data(pokemon, update_data)
                                    logger.info(f"Updated data for Pokémon: {pokemon.name} (ID: {pokemon.id})")

                                    if 'type1' in update_data or 'type2' in update_data:
                                        cursor.execute("DELETE FROM pokemon_types WHERE pokemon_id = ?", (pokemon.id,))
                                        for pokemon_type in pokemon.types:
                                            cursor.execute(
                                                "INSERT INTO pokemon_types (pokemon_id, type) VALUES (?, ?)",
                                                (pokemon.id, pokemon_type)
                                            )
                                        self.conn.commit()

                        if progress_callback:
                            progress_callback(pokemon_id, len(pokemon_list))

                    offset += batch_size
                    time.sleep(0.2)
                    break

                except requests.exceptions.RequestException as e:
                    logger.error(f"Error fetching Pokémon data (Attempt {attempt + 1}/3): {e}")
                    time.sleep(1 * (2 ** attempt))

            if attempt == 2:
                logger.critical(f"Failed to fetch Pokémon data after 3 retries. Continuing to next batch.")

        logger.info("Finished Pokemon database population.")

    def _update_pokemon_data(self, pokemon, update_data):
        """Updates an existing pokemon in the database."""

        set_clause = ", ".join([f"{field} = ?" for field in update_data])
        sql = f"UPDATE pokemon SET {set_clause} WHERE id = ?"

        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, tuple(update_data.values()) + (pokemon.id,))
            self.conn.commit()
            logger.info(f"Updated Pokémon with ID {pokemon.id}")
        except sqlite3.Error as e:
            logger.error(f"Error updating Pokémon with ID {pokemon.id}: {e}")

    def _fetch_evolution_data_from_url(self, evolution_chain_url):
        """Fetches evolution chain data from a specific URL."""
        logger.debug(f"Fetching evolution chain data from URL: {evolution_chain_url}")
        for attempt in range(3):
            try:
                response = self.http.get(evolution_chain_url, timeout=10)
                response.raise_for_status()
                evolution_chain_data = response.json()
                evolutions = []
                self._parse_evolution_chain(evolution_chain_data['chain'], evolutions)
                logger.debug(f"Fetched evolution chain data from URL: {evolution_chain_url}")
                return evolutions
            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Error fetching evolution chain data from {evolution_chain_url} (Attempt {attempt + 1}/3): {e}"
                )
                time.sleep(1 * (2 ** attempt))

        logger.critical(
            f"Failed to fetch evolution chain data from {evolution_chain_url} after 3 retries."
        )
        return None

    def _parse_evolution_chain(self, chain_link, evolutions):
        """Recursively parses an evolution chain link and extracts evolution data."""
        pokemon_id = int(chain_link['species']['url'].split('/')[-2])

        for evolution_detail in chain_link['evolves_to']:
            evolves_to_id = int(evolution_detail['species']['url'].split('/')[-2])
            if evolution_detail.get('evolution_details') and len(
                    evolution_detail['evolution_details']) > 0 and 'item' in \
                    evolution_detail['evolution_details'][0]:
                trigger = evolution_detail['evolution_details'][0]['trigger']['name']
                level = evolution_detail['evolution_details'][0].get('min_level')
                if evolution_detail['evolution_details'][0]['item'] is not None:
                    item = evolution_detail['evolution_details'][0]['item'].get('name')
                else:
                    item = None
            else:
                trigger = None
                level = None
                item = None

            evolutions.append(Evolution(pokemon_id, evolves_to_id, trigger, level, item))

            self._parse_evolution_chain(evolution_detail, evolutions)

    def _insert_evolution(self, evolution):
        """Inserts a new evolution into the evolutions table."""
        sql = """
        INSERT INTO evolutions (pokemon_id, evolves_to_id, trigger, level, item)
        VALUES (?, ?, ?, ?, ?)
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, evolution.to_tuple())
            self.conn.commit()
            logger.info(f"Inserted Evolution: {evolution.pokemon_id} -> {evolution.evolves_to_id}")
        except sqlite3.Error as e:
            logger.error(f"Error inserting evolution: {e}")

    def update_favourite_status(self, pokemon_id, is_favourite):
        """Updates the favourite status of a Pokémon."""
        sql = "UPDATE pokemon SET is_favourite = ? WHERE id = ?"
        logger.debug(f"Updating favourite status for Pokémon {pokemon_id} to {is_favourite}.")

        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (is_favourite, pokemon_id))
            self.conn.commit()
            logger.info(f"Updated favourite status for Pokémon {pokemon_id} to {is_favourite}")
        except sqlite3.Error as e:
            logger.error(f"Error updating favourite status for Pokémon {pokemon_id}: {e}")
