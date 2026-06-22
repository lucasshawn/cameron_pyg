import importlib.util
import json
import os
import py_compile
import sys
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


class CompileTests(unittest.TestCase):
    def test_source_files_compile(self):
        for filename in ("main.py", "game_objects.py"):
            py_compile.compile(os.path.join(SRC, filename), doraise=True)


@unittest.skipIf(importlib.util.find_spec("pygame") is None, "pygame is not installed")
class GameLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        import pygame

        pygame.init()
        cls.pygame = pygame

        import main
        import game_objects

        cls.main = main
        cls.game_objects = game_objects

    @classmethod
    def tearDownClass(cls):
        cls.pygame.quit()

    def test_build_all_rooms_has_expected_rooms(self):
        rooms = self.game_objects.build_all_rooms()
        self.assertEqual({"spawn", "boss_room", "overworld", "graveyard"}, set(rooms))
        self.assertTrue(rooms["spawn"].locked_exits)
        self.assertGreater(rooms["overworld"].world_w, self.game_objects.SCREEN_W)
        self.assertGreater(rooms["graveyard"].world_h, self.game_objects.SCREEN_H)

    def test_player_pickup_major_item_returns_fanfare_item(self):
        rooms = self.game_objects.build_all_rooms()
        room = rooms["spawn"]
        sword = next(item for item in room.items if item.item_type == "sword")
        player = self.game_objects.Player(sword.rect.x, sword.rect.y, {})

        fanfare_item = self.main.check_collisions(player, room, audio=None)

        self.assertIs(fanfare_item, sword)
        self.assertTrue(sword.collected)
        self.assertTrue(player.has_sword)

    def test_attack_timer_uses_configured_duration(self):
        player = self.game_objects.Player(100, 100, {})
        player.has_sword = True

        hitbox = player.attack()

        self.assertIsNotNone(hitbox)
        self.assertTrue(player.is_attacking)
        self.assertEqual(player.ATTACK_FRAMES, player.attack_timer)

    def test_scroll_room_marks_visible_tiles_explored(self):
        rooms = self.game_objects.build_all_rooms()
        room = rooms["overworld"]
        player = self.game_objects.Player(100, 100, {})

        self.assertEqual(set(), room.explored_tiles)
        room.update_camera(player)

        self.assertGreater(len(room.explored_tiles), 0)
        self.assertIn((0, 0), room.explored_tiles)

    def test_save_game_writes_expected_json_shape(self):
        old_save_file = self.main.SAVE_FILE
        self.main.SAVE_FILE = "../tests/.tmp_savegame.json"
        save_path = os.path.join(ROOT, "tests", ".tmp_savegame.json")
        try:
            rooms = self.game_objects.build_all_rooms()
            player = self.game_objects.Player(100, 100, {})
            room = rooms["spawn"]

            written_path = self.main.save_game(player, room, rooms)

            self.assertEqual(os.path.abspath(save_path), os.path.abspath(written_path))
            with open(written_path) as f:
                data = json.load(f)
            self.assertEqual(self.main.PROJECT_VERSION, data["version"])
            self.assertEqual("spawn", data["room_id"])
            self.assertIn("player", data)
            self.assertIn("rooms", data)
            self.assertIn("items", data["rooms"]["spawn"])
        finally:
            self.main.SAVE_FILE = old_save_file
            if os.path.exists(save_path):
                os.remove(save_path)


if __name__ == "__main__":
    unittest.main()
