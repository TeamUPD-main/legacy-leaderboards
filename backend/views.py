from django.db.models import F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Player, Leaderboard, LeaderboardEntry, StatsType, DifficultyType
from .serializers import (
    LeaderboardEntrySerializer,
    RegisterScoreSerializer,
)

DIFFICULTY_MAP = {
    "peaceful": DifficultyType.PEACEFUL,
    "easy": DifficultyType.EASY,
    "normal": DifficultyType.NORMAL,
    "hard": DifficultyType.HARD,
}

TYPE_MAP = {
    "travelling": StatsType.TRAVELLING,
    "mining": StatsType.MINING,
    "farming": StatsType.FARMING,
    "kills": StatsType.KILLS,
}


def get_leaderboard_from_query_params(request):
    difficulty_key = str(request.query_params.get("difficulty", "")).lower()
    type_key = str(request.query_params.get("type", "")).lower()

    if not difficulty_key or not type_key:
        return None, Response(
            {
                "error": "Missing required query params: difficulty, type",
                "allowed_difficulty": list(DIFFICULTY_MAP.keys()),
                "allowed_type": list(TYPE_MAP.keys()),
            },
            status=400,
        )

    if difficulty_key not in DIFFICULTY_MAP:
        return None, Response(
            {
                "error": "Invalid difficulty",
                "allowed_difficulty": list(DIFFICULTY_MAP.keys()),
            },
            status=400,
        )

    if type_key not in TYPE_MAP:
        return None, Response(
            {
                "error": "Invalid type",
                "allowed_type": list(TYPE_MAP.keys()),
            },
            status=400,
        )

    difficulty = DIFFICULTY_MAP[difficulty_key]
    stats_type = TYPE_MAP[type_key]

    try:
        leaderboard = Leaderboard.objects.get(
            difficulty=difficulty,
            stats_type=stats_type,
        )
    except Leaderboard.DoesNotExist:
        return None, Response(
            {
                "error": "Leaderboard not found for provided difficulty and type"
            },
            status=404,
        )

    return leaderboard, None

class WriteStatsView(APIView):
    def post(self, request):
        serializer = RegisterScoreSerializer(data=request.data)

        if serializer.is_valid():
            entry = serializer.save()

            # 🔥 Recalculate rank
            better_players = LeaderboardEntry.objects.filter(
                leaderboard=entry.leaderboard,
                total_score__gt=entry.total_score
            ).count()

            entry.rank = better_players + 1
            entry.save()

            return Response(
                LeaderboardEntrySerializer(entry).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class TopRankView(APIView):
    def get(self, request):
        leaderboard, error_response = get_leaderboard_from_query_params(request)
        if error_response:
            return error_response

        start = int(request.query_params.get("start", 0))
        count = int(request.query_params.get("count", 10))

        entries = LeaderboardEntry.objects.filter(
            leaderboard=leaderboard
        ).order_by("rank")[start:start + count]

        serializer = LeaderboardEntrySerializer(entries, many=True)
        return Response(serializer.data)
    
class FriendsLeaderboardView(APIView):
    def get(self, request):
        uid = request.query_params.get("user_id")
        leaderboard, error_response = get_leaderboard_from_query_params(request)
        if error_response:
            return error_response

        try:
            player = Player.objects.get(uid=uid)
        except Player.DoesNotExist:
            return Response({"error": "Player not found"}, status=404)

        friends = player.friends.all()

        entries = LeaderboardEntry.objects.filter(
            leaderboard=leaderboard,
            player__in=friends
        ).order_by("rank")

        serializer = LeaderboardEntrySerializer(entries, many=True)
        return Response(serializer.data)
    
class MyScoreView(APIView):
    def get(self, request):
        uid = request.query_params.get("user_id")
        leaderboard, error_response = get_leaderboard_from_query_params(request)
        if error_response:
            return error_response

        count = int(request.query_params.get("count", 5))

        try:
            player = Player.objects.get(uid=uid)
            entry = LeaderboardEntry.objects.get(
                player=player,
                leaderboard=leaderboard
            )
        except (Player.DoesNotExist, LeaderboardEntry.DoesNotExist):
            return Response({"error": "Not found"}, status=404)

        start_rank = max(entry.rank - count, 1)
        end_rank = entry.rank + count

        entries = LeaderboardEntry.objects.filter(
            leaderboard=leaderboard,
            rank__gte=start_rank,
            rank__lte=end_rank
        ).order_by("rank")

        serializer = LeaderboardEntrySerializer(entries, many=True)
        return Response(serializer.data)
    
class LeaderboardView(APIView):
    def get(self, request):
        mode = int(request.query_params.get("mode"))

        if mode == 0:  # Friends
            return FriendsLeaderboardView().get(request)

        elif mode == 1:  # My Score
            return MyScoreView().get(request)

        elif mode == 2:  # Top Rank
            return TopRankView().get(request)

        return Response({"error": "Invalid mode"}, status=400)