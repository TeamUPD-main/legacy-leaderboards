from django.db import models


# -------------------------
# ENUMS (from your C++ code)
# -------------------------

class StatsType(models.IntegerChoices):
    TRAVELLING = 0, "Travelling"
    MINING = 1, "Mining"
    FARMING = 2, "Farming"
    KILLS = 3, "Kills"


class FilterMode(models.IntegerChoices):
    FRIENDS = 0, "Friends"
    MY_SCORE = 1, "My Score"
    TOP_RANK = 2, "Top Rank"


# -------------------------
# CORE MODELS
# -------------------------

class Player(models.Model):
    uid = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)

    friends = models.ManyToManyField("self", blank=True)

    def __str__(self):
        return self.name


class Leaderboard(models.Model):
    stats_type = models.IntegerField(choices=StatsType.choices)
    difficulty = models.IntegerField()

    class Meta:
        unique_together = ("stats_type", "difficulty")

    def __str__(self):
        return f"{self.get_stats_type_display()} (Difficulty {self.difficulty})"


class LeaderboardEntry(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    leaderboard = models.ForeignKey(Leaderboard, on_delete=models.CASCADE)

    rank = models.PositiveIntegerField()
    total_score = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("player", "leaderboard")
        ordering = ["rank"]


# -------------------------
# STATS MODELS (STRUCTS)
# -------------------------

class KillsStats(models.Model):
    entry = models.OneToOneField(LeaderboardEntry, on_delete=models.CASCADE, related_name="kills")

    zombie = models.PositiveIntegerField(default=0)
    skeleton = models.PositiveIntegerField(default=0)
    creeper = models.PositiveIntegerField(default=0)
    spider = models.PositiveIntegerField(default=0)
    spider_jockey = models.PositiveIntegerField(default=0)
    zombie_pigman = models.PositiveIntegerField(default=0)
    slime = models.PositiveIntegerField(default=0)


class MiningStats(models.Model):
    entry = models.OneToOneField(LeaderboardEntry, on_delete=models.CASCADE, related_name="mining")

    dirt = models.PositiveIntegerField(default=0)
    stone = models.PositiveIntegerField(default=0)
    sand = models.PositiveIntegerField(default=0)
    cobblestone = models.PositiveIntegerField(default=0)
    gravel = models.PositiveIntegerField(default=0)
    clay = models.PositiveIntegerField(default=0)
    obsidian = models.PositiveIntegerField(default=0)


class FarmingStats(models.Model):
    entry = models.OneToOneField(LeaderboardEntry, on_delete=models.CASCADE, related_name="farming")

    eggs = models.PositiveIntegerField(default=0)
    wheat = models.PositiveIntegerField(default=0)
    mushroom = models.PositiveIntegerField(default=0)
    sugarcane = models.PositiveIntegerField(default=0)
    milk = models.PositiveIntegerField(default=0)
    pumpkin = models.PositiveIntegerField(default=0)


class TravellingStats(models.Model):
    entry = models.OneToOneField(LeaderboardEntry, on_delete=models.CASCADE, related_name="travelling")

    walked = models.PositiveBigIntegerField(default=0)
    fallen = models.PositiveBigIntegerField(default=0)
    minecart = models.PositiveBigIntegerField(default=0)
    boat = models.PositiveBigIntegerField(default=0)