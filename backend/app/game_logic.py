import random
from typing import List, Dict, Any
from datetime import datetime


class PokemonGameLogic:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.start_time = datetime.now()
        self.reset_game()

    def reset_game(self):
        """Сброс состояния игры к начальным значениям"""
        self.player_health = 100
        self.player_level = 1
        self.player_exp = 0
        self.player_max_exp = 100
        self.pokeballs = 5
        self.score = 0
        self.wave = 1
        self.game_over = False
        self.victory = False

        # Колода и рука
        self.deck = self.generate_initial_deck()
        self.hand = []
        self.field = []
        self.enemies = []

        # Логика волн
        self.wave_data = self.generate_wave(self.wave)
        self.enemy_spawn_timer = 0
        self.enemy_spawn_interval = 1.5  # Уменьшили с 2.0 до 1.5 секунд

        # Позиция базы игрока (нижняя линия)
        self.player_base_y = 450  # Нижняя граница для врагов
        self.enemy_base_y = 100  # Верхняя граница для наших покемонов

    def generate_initial_deck(self) -> List[Dict]:
        basic_pokemons = [
            {"id": 1, "name": "Charmander", "element": "fire", "health": 60, "attack": 12, "speed": 2.0},
            # Добавили скорость
            {"id": 2, "name": "Squirtle", "element": "water", "health": 70, "attack": 10, "speed": 1.8},
            {"id": 3, "name": "Bulbasaur", "element": "grass", "health": 65, "attack": 11, "speed": 1.6},
        ]
        return random.sample(basic_pokemons, 2)

    def generate_wave(self, wave_number: int) -> List[Dict]:
        enemies = []
        base_count = min(3 + wave_number, 10)  # Увеличили максимум с 8 до 10

        for i in range(base_count):
            enemy_types = [
                {"name": "Rattata", "element": "normal", "health": 25 + wave_number * 4, "attack": 8 + wave_number,
                 "speed": 50 + wave_number * 8},
                {"name": "Spearow", "element": "flying", "health": 20 + wave_number * 3, "attack": 10 + wave_number,
                 "speed": 60 + wave_number * 10},
                {"name": "Zubat", "element": "poison", "health": 30 + wave_number * 5, "attack": 12 + wave_number,
                 "speed": 45 + wave_number * 7},
                {"name": "Geodude", "element": "rock", "health": 40 + wave_number * 6, "attack": 15 + wave_number,
                 "speed": 30 + wave_number * 5},
            ]
            enemy = random.choice(enemy_types)
            enemy["id"] = i
            enemies.append(enemy)

        return enemies

    def open_pokeball(self) -> Dict:
        if self.pokeballs <= 0:
            return {"error": "No pokeballs left"}

        self.pokeballs -= 1

        possible_pokemons = [
            {"name": "Pikachu", "element": "electric", "health": 45, "attack": 18, "speed": 2.5},
            {"name": "Jigglypuff", "element": "normal", "health": 85, "attack": 9, "speed": 1.2},
            {"name": "Meowth", "element": "normal", "health": 45, "attack": 15, "speed": 2.2},
            {"name": "Psyduck", "element": "water", "health": 55, "attack": 12, "speed": 1.5},
            {"name": "Growlithe", "element": "fire", "health": 60, "attack": 14, "speed": 2.0},
            {"name": "Abra", "element": "psychic", "health": 40, "attack": 20, "speed": 1.8},
            {"name": "Machop", "element": "fighting", "health": 70, "attack": 16, "speed": 1.4},
        ]

        new_pokemon = random.choice(possible_pokemons)
        new_pokemon["id"] = len(self.hand) + len(self.field) + 100

        self.hand.append(new_pokemon)

        return {"success": True, "pokemon": new_pokemon}

    def play_card(self, card_id: int, x: int, y: int) -> Dict:
        card_index = next((i for i, card in enumerate(self.hand) if card["id"] == card_id), None)

        if card_index is None:
            return {"error": "Card not found in hand"}

        # Проверяем валидность позиции (игровая зона - теперь от 150 до 500 по Y)
        if x < 0 or x > 800 or y < 150 or y > 450:
            return {"error": "Invalid position - must be within play area (y between 150-450)"}

        # Проверяем, не занята ли клетка
        for pokemon in self.field:
            if abs(pokemon["x"] - x) < 60 and abs(pokemon["y"] - y) < 60:
                return {"error": "Position already occupied"}

        card = self.hand.pop(card_index)
        field_pokemon = {
            **card,
            "x": x,
            "y": y,
            "current_health": card["health"],
            "attack_cooldown": 0,
            "is_moving": False,
            "target": None,
            "speed": card.get("speed", 1.5),
            "attack_range": 120  # Радиус атаки
        }
        self.field.append(field_pokemon)

        return {"success": True, "field": self.field}

    def update(self, delta_time: float = 0.1) -> Dict:
        """Обновление игрового состояния. delta_time в секундах."""
        if self.game_over:
            return self.get_state()

        # Спавн врагов СВЕРХУ
        self.enemy_spawn_timer += delta_time
        if self.enemy_spawn_timer >= self.enemy_spawn_interval and self.wave_data:
            enemy_data = self.wave_data.pop(0)
            enemy = {
                **enemy_data,
                "x": random.randint(50, 750),
                "y": 100,
                "current_health": enemy_data["health"],
                "speed": enemy_data.get("speed", 50)
            }
            self.enemies.append(enemy)
            self.enemy_spawn_timer = 0

            if not self.wave_data:
                self.wave += 1
                self.wave_data = self.generate_wave(self.wave)

        # Движение врагов ВНИЗ к базе игрока
        for enemy in self.enemies[:]:
            # Цель: нижняя линия защиты игрока
            target_y = self.player_base_y

            # Двигаемся вниз
            dy = target_y - enemy["y"]
            distance = abs(dy)

            if distance < enemy["speed"] * delta_time:
                enemy["y"] = target_y
                # Враг дошел до базы
                self.player_health -= 20  # Увеличили урон с 15 до 20
                self.enemies.remove(enemy)

                if self.player_health <= 0:
                    self.game_over = True
            else:
                # Продолжаем движение вниз
                enemy["y"] += enemy["speed"] * delta_time if dy > 0 else -enemy["speed"] * delta_time

        # Логика движения и атаки покемонов
        for pokemon in self.field:
            pokemon["attack_cooldown"] = max(0, pokemon["attack_cooldown"] - delta_time)

            # Ищем ближайшего врага
            nearest_enemy = None
            nearest_distance = float('inf')

            for enemy in self.enemies:
                distance = ((pokemon["x"] - enemy["x"]) ** 2 + (pokemon["y"] - enemy["y"]) ** 2) ** 0.5
                if distance < pokemon["attack_range"] and distance < nearest_distance:
                    nearest_enemy = enemy
                    nearest_distance = distance

            if nearest_enemy:
                # Если враг в радиусе атаки
                pokemon["is_moving"] = False
                pokemon["target"] = nearest_enemy["id"]

                if pokemon["attack_cooldown"] <= 0:
                    damage_multiplier = self.get_type_multiplier(pokemon["element"], nearest_enemy["element"])
                    damage = pokemon["attack"] * damage_multiplier

                    nearest_enemy["current_health"] -= damage
                    pokemon["attack_cooldown"] = 0.8  # Уменьшили КД с 1.0 до 0.8 секунд

                    if nearest_enemy["current_health"] <= 0:
                        self.enemies.remove(nearest_enemy)
                        self.score += 15  # Увеличили награду с 10 до 15
                        self.player_exp += 2  # Увеличили опыт с 1 до 2

                        if self.player_exp >= self.player_max_exp:
                            self.player_level += 1
                            self.pokeballs += 2  # Увеличили награду с 1 до 2
                            self.player_exp = 0
                            self.player_max_exp = int(self.player_max_exp * 1.2)
            else:
                # Если врагов нет, двигаемся вверх к вражеской базе
                pokemon["is_moving"] = True
                pokemon["target"] = None

                # Двигаемся вверх с учетом скорости покемона
                target_y = self.enemy_base_y
                dy = target_y - pokemon["y"]
                distance = abs(dy)

                if distance > 10:  # Если не достигли цели
                    # Двигаемся вверх
                    pokemon["y"] -= pokemon["speed"] * delta_time * 30  # Умножаем на 30 для видимой скорости

                    # Проверяем, достигли ли вражеской базы
                    if pokemon["y"] <= target_y:
                        # Атакуем вражескую базу
                        self.score += 50  # Награда за достижение вражеской базы
                        pokemon["y"] = target_y  # Фиксируем позицию

        # Проверка победы (после 5 волн)
        if self.wave > 5:
            self.game_over = True
            self.victory = True

        return self.get_state()

    def get_type_multiplier(self, attacker: str, defender: str) -> float:
        effectiveness = {
            "fire": {"grass": 2.0, "water": 0.5, "ice": 2.0, "bug": 2.0, "steel": 2.0},
            "water": {"fire": 2.0, "grass": 0.5, "ground": 2.0, "rock": 2.0},
            "grass": {"water": 2.0, "fire": 0.5, "ground": 2.0, "rock": 2.0, "electric": 0.5},
            "electric": {"water": 2.0, "flying": 2.0, "grass": 0.5, "ground": 0},
            "flying": {"grass": 2.0, "fighting": 2.0, "bug": 2.0, "electric": 0.5, "rock": 0.5},
            "poison": {"grass": 2.0, "fairy": 2.0, "poison": 0.5, "ground": 0.5, "psychic": 0.5},
            "psychic": {"fighting": 2.0, "poison": 2.0, "dark": 0, "ghost": 0.5},
            "fighting": {"normal": 2.0, "rock": 2.0, "steel": 2.0, "flying": 0.5, "psychic": 0.5},
            "rock": {"fire": 2.0, "ice": 2.0, "flying": 2.0, "bug": 2.0, "fighting": 0.5, "ground": 0.5},
        }
        return effectiveness.get(attacker, {}).get(defender, 1.0)

    def get_state(self) -> Dict:
        return {
            "player_health": self.player_health,
            "player_level": self.player_level,
            "player_exp": self.player_exp,
            "player_max_exp": self.player_max_exp,
            "pokeballs": self.pokeballs,
            "hand": self.hand,
            "field": [
                {
                    **pokemon,
                    "is_moving": pokemon.get("is_moving", False),
                    "target": pokemon.get("target"),
                    "speed": pokemon.get("speed", 1.5)
                }
                for pokemon in self.field
            ],
            "enemies": self.enemies,
            "wave": self.wave,
            "score": self.score,
            "game_over": self.game_over,
            "victory": self.victory,
            "player_base_y": self.player_base_y,
            "enemy_base_y": self.enemy_base_y
        }

    def get_game_result(self) -> Dict:
        game_duration = (datetime.now() - self.start_time).total_seconds()
        return {
            "victory": self.victory,
            "score": self.score,
            "waves_completed": self.wave - 1,
            "pokemons_caught": len(self.hand) + len(self.field),
            "enemies_defeated": self.score // 15,
            "game_duration": game_duration
        }


# Глобальный словарь для хранения активных игр
active_games = {}