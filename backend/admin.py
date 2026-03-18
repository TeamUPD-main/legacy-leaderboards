from django.contrib import admin
from .models import Player, Leaderboard, LeaderboardEntry

admin.site.register(Player)
admin.site.register(Leaderboard)
admin.site.register(LeaderboardEntry)