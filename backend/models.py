from django.db import models
from django.core.validators import MaxValueValidator
from django.contrib.auth.models import User

### Types & Filters

MAX_ITEM_COUNT = 99999 # Can be seen as max value for Xbox One here: https://www.youtube.com/watch?v=fEIor4h1Jqw

class StatsType(models.IntegerChoices):
    TRAVELLING = 0, "Travelling"
    MINING = 1, "Mining"
    FARMING = 2, "Farming"
    KILLS = 3, "Kills"


class DifficultyType(models.IntegerChoices):
    PEACEFUL = 0, "Peaceful"
    EASY = 1, "Easy"
    NORMAL = 2, "Normal"
    HARD = 3, "Hard"


class FilterMode(models.IntegerChoices):
    FRIENDS = 0, "Friends"
    MY_SCORE = 1, "My Score"
    TOP_RANK = 2, "Top Rank"

### General Models

class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="player_profile")
    uid = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)

    friends = models.ManyToManyField("self", blank=True)

    achievements = models.ManyToManyField("Achievement", through="PlayerAchievement", blank=True)

    def __str__(self):
        return self.name


class Leaderboard(models.Model):
    stats_type = models.IntegerField(choices=StatsType.choices)
    difficulty = models.IntegerField(choices=DifficultyType.choices)

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

## Stats Models

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

    dirt = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(MAX_ITEM_COUNT)])
    stone = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(MAX_ITEM_COUNT)])
    sand = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(MAX_ITEM_COUNT)])
    cobblestone = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(MAX_ITEM_COUNT)])
    gravel = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(MAX_ITEM_COUNT)])
    clay = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(MAX_ITEM_COUNT)])
    obsidian = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(MAX_ITEM_COUNT)])


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


### Achievement Models

class Achievement(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=1024)
    score = models.PositiveIntegerField(default=0)

class PlayerAchievement(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)

    class Meta:
        unique_together = ("player", "achievement")