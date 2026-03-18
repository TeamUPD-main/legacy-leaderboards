from django.contrib import admin
from .models import Player, Leaderboard, LeaderboardEntry, Achievement

admin.site.register(Player)
admin.site.register(Leaderboard)
admin.site.register(LeaderboardEntry)
admin.site.register(Achievement)