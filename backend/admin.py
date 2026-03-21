from django.contrib import admin
from .models import Player, Leaderboard, LeaderboardEntry, Achievement, PlayerAchievement

admin.site.register(Player)
admin.site.register(Leaderboard)
admin.site.register(LeaderboardEntry)
admin.site.register(Achievement)
admin.site.register(PlayerAchievement)