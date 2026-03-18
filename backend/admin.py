from django.contrib import admin

# Register your models here.

from .models import Player, Leaderboard, LeaderboardEntry

admin.site.register(Player)
admin.site.register(Leaderboard)
admin.site.register(LeaderboardEntry)