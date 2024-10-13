class Pokemon:
    """Represents a Pokémon."""

    def __init__(self, id, name, type1, type2, hp, attack, defense, sp_atk, sp_def, speed, sprite_front, sprite_back,
                 description, is_favourite=0):
        self.id = id
        self.name = name
        self.type1 = type1
        self.type2 = type2
        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.sp_atk = sp_atk
        self.sp_def = sp_def
        self.speed = speed
        self.sprite_front = sprite_front
        self.sprite_back = sprite_back
        self.description = description
        self.is_favourite = is_favourite

    def get_formatted_types(self):
        """Returns a formatted string of the Pokémon's types."""
        types_str = self.type1
        if self.type2:
            types_str += f", {self.type2}"
        return types_str

    def to_tuple(self):
        """Converts the Pokemon object to a tuple for database operations."""
        return (
            self.id,
            self.name,
            self.type1,
            self.type2,
            self.hp,
            self.attack,
            self.defense,
            self.sp_atk,
            self.sp_def,
            self.speed,
            self.sprite_front,
            self.sprite_back,
            self.description,
            self.is_favourite,
        )

    def to_dict(self):
        """Converts the Pokemon object to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'type1': self.type1,
            'type2': self.type2,
            'hp': self.hp,
            'attack': self.attack,
            'defense': self.defense,
            'sp_atk': self.sp_atk,
            'sp_def': self.sp_def,
            'speed': self.speed,
            'sprite_front': self.sprite_front,
            'sprite_back': self.sprite_back,
            'description': self.description,
            'is_favourite': self.is_favourite
        }

    @classmethod
    def from_api_data(cls, api_data):
        """Creates a Pokemon object from data fetched from the PokeAPI."""
        id = api_data['id']
        name = api_data['name']
        types = [t['type']['name'] for t in api_data['types']]
        type1 = types[0] if types else None
        type2 = types[1] if len(types) > 1 else None
        hp = api_data['stats'][0]['base_stat']
        attack = api_data['stats'][1]['base_stat']
        defense = api_data['stats'][2]['base_stat']
        sp_atk = api_data['stats'][3]['base_stat']
        sp_def = api_data['stats'][4]['base_stat']
        speed = api_data['stats'][5]['base_stat']
        sprite_front = api_data.get('sprites', {}).get('front_default')
        sprite_back = api_data.get('sprites', {}).get('back_default')

        # Description (English only)
        description = None
        for entry in api_data.get('species', {}).get('flavor_text_entries', []):
            if entry['language']['name'] == 'en':
                description = entry['flavor_text']
                break

        return cls(
            id=id,
            name=name,
            type1=type1,
            type2=type2,
            hp=hp,
            attack=attack,
            defense=defense,
            sp_atk=sp_atk,
            sp_def=sp_def,
            speed=speed,
            sprite_front=sprite_front,
            sprite_back=sprite_back,
            description=description
        )


class Berry:
    """Represents a Berry."""

    def __init__(self, id, name, growth_time, max_harvest, natural_gift_power, size, smoothness, soil_dryness, firmness,
                 flavors):
        self.id = id
        self.name = name
        self.growth_time = growth_time
        self.max_harvest = max_harvest
        self.natural_gift_power = natural_gift_power
        self.size = size
        self.smoothness = smoothness
        self.soil_dryness = soil_dryness
        self.firmness = firmness
        self.flavors = flavors

    @classmethod
    def from_api_data(cls, api_data):
        """Creates a Berry object from data fetched from the PokeAPI."""
        id = api_data['id']
        name = api_data['name']
        growth_time = api_data['growth_time']
        max_harvest = api_data['max_harvest']
        natural_gift_power = api_data['natural_gift_power']
        size = api_data['size']
        smoothness = api_data['smoothness']
        soil_dryness = api_data['soil_dryness']
        firmness = api_data['firmness']['name']
        flavors = [(flavor['flavor']['name'], flavor['potency']) for flavor in api_data['flavors']]

        return cls(
            id=id,
            name=name,
            growth_time=growth_time,
            max_harvest=max_harvest,
            natural_gift_power=natural_gift_power,
            size=size,
            smoothness=smoothness,
            soil_dryness=soil_dryness,
            firmness=firmness,
            flavors=flavors
        )

    def to_tuple(self):
        """Converts the Berry object to a tuple for database operations, excluding the flavors list."""
        return (
            self.id,
            self.name,
            self.growth_time,
            self.max_harvest,
            self.natural_gift_power,
            self.size,
            self.smoothness,
            self.soil_dryness,
            self.firmness
        )

    def to_dict(self):
        """Converts the Berry object to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'growth_time': self.growth_time,
            'max_harvest': self.max_harvest,
            'natural_gift_power': self.natural_gift_power,
            'size': self.size,
            'smoothness': self.smoothness,
            'soil_dryness': self.soil_dryness,
            'firmness': self.firmness,
            'flavors': self.flavors
        }


class Evolution:
    """Represents an Evolution."""

    def __init__(self, pokemon_id, evolves_to_id, trigger, level, item):
        self.pokemon_id = pokemon_id
        self.evolves_to_id = evolves_to_id
        self.trigger = trigger
        self.level = level
        self.item = item

    def to_tuple(self):
        """Converts the Evolution object to a tuple for database operations."""
        return (
            self.pokemon_id,
            self.evolves_to_id,
            self.trigger,
            self.level,
            self.item
        )

    def to_dict(self):
        """Converts the Evolution object to a dictionary."""
        return {
            'pokemon_id': self.pokemon_id,
            'evolves_to_id': self.evolves_to_id,
            'trigger': self.trigger,
            'level': self.level,
            'item': self.item
        }
