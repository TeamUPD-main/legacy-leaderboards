from django.test import TestCase
from django.test import override_settings
from rest_framework.test import APIClient

from .models import Achievement, DifficultyType, KillsStats, Leaderboard, LeaderboardEntry, Player, PlayerAchievement


class CreatePlayerViewTests(TestCase):
	def setUp(self):
		self.client = APIClient()

	def test_create_player_success(self):
		response = self.client.post(
			"/api/player/create",
			{"uid": "test-uid-123", "name": "Test"},
			format="json",
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data["uid"], "test-uid-123")
		self.assertEqual(response.data["name"], "Test")
		self.assertTrue(Player.objects.filter(uid="test-uid-123").exists())

	def test_create_player_duplicate_uid_returns_400(self):
		Player.objects.create(uid="dup-uid", name="Existing")

		response = self.client.post(
			"/api/player/add",
			{"uid": "dup-uid", "name": "Other"},
			format="json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn("uid", response.data)


class PlayerDetailsViewTests(TestCase):
	def setUp(self):
		self.client = APIClient()

	def test_get_player_details_requires_uid(self):
		response = self.client.get("/api/player")
		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.data["error"], "Missing required query param: uid")

	def test_get_player_details_returns_stats_and_achievements(self):
		player = Player.objects.create(uid="player-1", name="Test")
		achievement = Achievement.objects.create(
			id=101,
			name="Getting Wood",
			description="Punch a tree until a block of wood pops out",
			score=10,
		)

		leaderboard = Leaderboard.objects.create(
			stats_type=3,
			difficulty=DifficultyType.NORMAL,
		)
		entry = LeaderboardEntry.objects.create(
			player=player,
			leaderboard=leaderboard,
			rank=1,
			total_score=42,
		)
		KillsStats.objects.create(entry=entry, zombie=7)

		response = self.client.get("/api/player?uid=player-1")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["uid"], "player-1")
		self.assertEqual(response.data["name"], "Test")

		self.assertEqual(len(response.data["stats"]), 1)
		self.assertEqual(response.data["stats"][0]["stats_type"], "Kills")
		self.assertEqual(response.data["stats"][0]["difficulty"], "Normal")
		self.assertEqual(response.data["stats"][0]["total_score"], 42)
		self.assertEqual(response.data["stats"][0]["stats"]["zombie"], 7)

		self.assertEqual(len(response.data["achievements"]), 1)
		self.assertEqual(response.data["achievements"][0]["id"], achievement.id)
		self.assertEqual(response.data["achievements"][0]["name"], "Getting Wood")
		self.assertFalse(response.data["achievements"][0]["status"])


class AddAchievementToPlayerViewTests(TestCase):
	def setUp(self):
		self.client = APIClient()

	def test_add_achievement_to_player_sets_status_true(self):
		player = Player.objects.create(uid="283283", name="Test")
		achievement = Achievement.objects.create(
			id=1,
			name="Open Inventory",
			description="Press E to open inventory",
			score=5,
		)

		response = self.client.post(
			"/api/achievement/add",
			{"achievement_id": 1, "player_uid": "283283"},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["achievement_id"], 1)
		self.assertEqual(response.data["player_uid"], "283283")
		self.assertTrue(response.data["status"])

		player_achievement = PlayerAchievement.objects.get(player=player, achievement=achievement)
		self.assertTrue(player_achievement.status)

	def test_add_achievement_to_player_missing_params_returns_400(self):
		response = self.client.post("/api/achievement/add", {}, format="json")
		self.assertEqual(response.status_code, 400)
		self.assertIn("achievement_id", response.data)
		self.assertIn("player_uid", response.data)

	def test_add_achievement_get_not_allowed(self):
		response = self.client.get("/api/achievement/add?achievement_id=1&player_uid=283283")
		self.assertEqual(response.status_code, 405)


class RemoveAchievementFromPlayerViewTests(TestCase):
	def setUp(self):
		self.client = APIClient()

	def test_remove_achievement_from_player_sets_status_false(self):
		player = Player.objects.create(uid="283283", name="Test")
		achievement = Achievement.objects.create(
			id=2,
			name="Time to Mine!",
			description="Use planks and sticks to make a pickaxe",
			score=10,
		)
		player_achievement = PlayerAchievement.objects.get(player=player, achievement=achievement)
		player_achievement.status = True
		player_achievement.save(update_fields=["status"])

		response = self.client.post(
			"/api/achievement/remove",
			{"achievement_id": 2, "player_uid": "283283"},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["achievement_id"], 2)
		self.assertEqual(response.data["player_uid"], "283283")
		self.assertFalse(response.data["status"])

		player_achievement.refresh_from_db()
		self.assertFalse(player_achievement.status)

	def test_remove_achievement_missing_params_returns_400(self):
		response = self.client.post("/api/achievement/remove", {}, format="json")
		self.assertEqual(response.status_code, 400)
		self.assertIn("achievement_id", response.data)
		self.assertIn("player_uid", response.data)

	def test_remove_achievement_get_not_allowed(self):
		response = self.client.get("/api/achievement/remove?achievement_id=2&player_uid=283283")
		self.assertEqual(response.status_code, 405)


class AchievementListViewTests(TestCase):
	def setUp(self):
		self.client = APIClient()

	def test_achievement_list_returns_all_achievements(self):
		Achievement.objects.create(
			id=1,
			name="Open Inventory",
			description="Press E to open inventory",
			score=5,
		)
		Achievement.objects.create(
			id=2,
			name="Time to Mine!",
			description="Use planks and sticks to make a pickaxe",
			score=10,
		)

		response = self.client.get("/api/achievement/list")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 2)
		self.assertEqual(response.data[0]["id"], 1)
		self.assertEqual(response.data[0]["name"], "Open Inventory")
		self.assertEqual(response.data[1]["id"], 2)

	def test_achievement_list_post_not_allowed(self):
		response = self.client.post("/api/achievement/list", {}, format="json")
		self.assertEqual(response.status_code, 405)


@override_settings(SECURE_SSL_REDIRECT=False)
class WriteStatsViewTests(TestCase):
	def setUp(self):
		self.client = APIClient()

	def test_write_stats_upserts_existing_entry(self):
		payload = {
			"player_uid": "player-upsert",
			"difficulty": "normal",
			"type": "kills",
			"score": 25,
			"stats": {
				"zombie": 1,
				"skeleton": 1,
				"creeper": 1,
				"spider": 1,
				"spider_jockey": 0,
				"zombie_pigman": 0,
				"slime": 0,
			},
		}

		first_response = self.client.post("/api/leaderboard/write/", payload, format="json")
		self.assertEqual(first_response.status_code, 201)

		payload["score"] = 40
		payload["stats"]["zombie"] = 5

		second_response = self.client.post("/api/leaderboard/write/", payload, format="json")
		self.assertEqual(second_response.status_code, 200)

		player = Player.objects.get(uid="player-upsert")
		entries = LeaderboardEntry.objects.filter(player=player)
		self.assertEqual(entries.count(), 1)
		self.assertEqual(entries.first().total_score, 40)
		self.assertEqual(entries.first().rank, 1)

		self.assertEqual(player.leaderboardentry_set.first().kills.zombie, 5)

	def test_write_stats_recalculates_all_ranks(self):
		alpha_payload = {
			"player_uid": "alpha",
			"difficulty": "normal",
			"type": "kills",
			"score": 20,
			"stats": {
				"zombie": 1,
				"skeleton": 0,
				"creeper": 0,
				"spider": 0,
				"spider_jockey": 0,
				"zombie_pigman": 0,
				"slime": 0,
			},
		}
		bravo_payload = {
			"player_uid": "bravo",
			"difficulty": "normal",
			"type": "kills",
			"score": 10,
			"stats": {
				"zombie": 1,
				"skeleton": 0,
				"creeper": 0,
				"spider": 0,
				"spider_jockey": 0,
				"zombie_pigman": 0,
				"slime": 0,
			},
		}

		self.client.post("/api/leaderboard/write/", alpha_payload, format="json")
		self.client.post("/api/leaderboard/write/", bravo_payload, format="json")

		bravo_payload["score"] = 30
		update_response = self.client.post("/api/leaderboard/write/", bravo_payload, format="json")
		self.assertEqual(update_response.status_code, 200)

		leaderboard = Leaderboard.objects.get(stats_type=3, difficulty=DifficultyType.NORMAL)
		entries = list(
			LeaderboardEntry.objects.filter(leaderboard=leaderboard).order_by("rank")
		)

		self.assertEqual(len(entries), 2)
		self.assertEqual(entries[0].player.uid, "bravo")
		self.assertEqual(entries[0].rank, 1)
		self.assertEqual(entries[1].player.uid, "alpha")
		self.assertEqual(entries[1].rank, 2)
