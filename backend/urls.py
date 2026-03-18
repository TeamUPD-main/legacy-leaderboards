from django.urls import path
from .views import (
    WriteStatsView,
    TopRankView,
    FriendsLeaderboardView,
    MyScoreView,
    LeaderboardView,
)

urlpatterns = [
    path("write/", WriteStatsView.as_view()),
    path("top/", TopRankView.as_view()),
    path("friends/", FriendsLeaderboardView.as_view()),
    path("my-score/", MyScoreView.as_view()),
    path("", LeaderboardView.as_view()),
]