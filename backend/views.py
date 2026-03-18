from django.db.models import F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Player, Leaderboard, LeaderboardEntry
from .serializers import (
    LeaderboardEntrySerializer,
    RegisterScoreSerializer,
)

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
        leaderboard_id = request.query_params.get("leaderboard_id")
        start = int(request.query_params.get("start", 0))
        count = int(request.query_params.get("count", 10))

        entries = LeaderboardEntry.objects.filter(
            leaderboard_id=leaderboard_id
        ).order_by("rank")[start:start + count]

        serializer = LeaderboardEntrySerializer(entries, many=True)
        return Response(serializer.data)
    
class FriendsLeaderboardView(APIView):
    def get(self, request):
        uid = request.query_params.get("uid")
        leaderboard_id = request.query_params.get("leaderboard_id")

        try:
            player = Player.objects.get(uid=uid)
        except Player.DoesNotExist:
            return Response({"error": "Player not found"}, status=404)

        friends = player.friends.all()

        entries = LeaderboardEntry.objects.filter(
            leaderboard_id=leaderboard_id,
            player__in=friends
        ).order_by("rank")

        serializer = LeaderboardEntrySerializer(entries, many=True)
        return Response(serializer.data)
    
class MyScoreView(APIView):
    def get(self, request):
        uid = request.query_params.get("uid")
        leaderboard_id = request.query_params.get("leaderboard_id")
        count = int(request.query_params.get("count", 5))

        try:
            player = Player.objects.get(uid=uid)
            entry = LeaderboardEntry.objects.get(
                player=player,
                leaderboard_id=leaderboard_id
            )
        except (Player.DoesNotExist, LeaderboardEntry.DoesNotExist):
            return Response({"error": "Not found"}, status=404)

        start_rank = max(entry.rank - count, 1)
        end_rank = entry.rank + count

        entries = LeaderboardEntry.objects.filter(
            leaderboard_id=leaderboard_id,
            rank__gte=start_rank,
            rank__lte=end_rank
        ).order_by("rank")

        serializer = LeaderboardEntrySerializer(entries, many=True)
        return Response(serializer.data)
    
class LeaderboardView(APIView):
    def get(self, request):
        mode = int(request.query_params.get("mode"))
        leaderboard_id = request.query_params.get("leaderboard_id")

        if mode == 0:  # Friends
            return FriendsLeaderboardView().get(request)

        elif mode == 1:  # My Score
            return MyScoreView().get(request)

        elif mode == 2:  # Top Rank
            return TopRankView().get(request)

        return Response({"error": "Invalid mode"}, status=400)