from rest_framework import serializers
from .models import (
    Player,
    Leaderboard,
    LeaderboardEntry,
    KillsStats,
    MiningStats,
    FarmingStats,
    TravellingStats,
)

class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ["id", "uid", "name"]

class KillsStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = KillsStats
        exclude = ["id", "entry"]


class MiningStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MiningStats
        exclude = ["id", "entry"]


class FarmingStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmingStats
        exclude = ["id", "entry"]


class TravellingStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravellingStats
        exclude = ["id", "entry"]

from .models import StatsType

class StatsDataSerializer(serializers.Serializer):
    type = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()

    def get_type(self, obj):
        return obj.leaderboard.get_stats_type_display()

    def get_data(self, obj):
        if hasattr(obj, "kills"):
            return KillsStatsSerializer(obj.kills).data
        if hasattr(obj, "mining"):
            return MiningStatsSerializer(obj.mining).data
        if hasattr(obj, "farming"):
            return FarmingStatsSerializer(obj.farming).data
        if hasattr(obj, "travelling"):
            return TravellingStatsSerializer(obj.travelling).data
        return None
    

class LeaderboardEntrySerializer(serializers.ModelSerializer):
    player = PlayerSerializer(read_only=True)
    stats = serializers.SerializerMethodField()

    class Meta:
        model = LeaderboardEntry
        fields = [
            "player",
            "rank",
            "total_score",
            "stats",
        ]

    def get_stats(self, obj):
        return StatsDataSerializer(obj).data
    
class RegisterScoreSerializer(serializers.Serializer):
    player_uid = serializers.CharField()
    leaderboard_id = serializers.IntegerField()
    score = serializers.IntegerField()
    difficulty = serializers.IntegerField()
    stats_type = serializers.IntegerField()
    stats = serializers.DictField()

    def create(self, validated_data):
        from .models import StatsType

        player, _ = Player.objects.get_or_create(
            uid=validated_data["player_uid"]
        )

        leaderboard = Leaderboard.objects.get(
            id=validated_data["leaderboard_id"]
        )

        entry = LeaderboardEntry.objects.create(
            player=player,
            leaderboard=leaderboard,
            total_score=validated_data["score"],
            rank=0,  # compute later
        )

        stats = validated_data["stats"]
        stats_type = validated_data["stats_type"]

        if stats_type == StatsType.KILLS:
            KillsStats.objects.create(entry=entry, **stats)

        elif stats_type == StatsType.MINING:
            MiningStats.objects.create(entry=entry, **stats)

        elif stats_type == StatsType.FARMING:
            FarmingStats.objects.create(entry=entry, **stats)

        elif stats_type == StatsType.TRAVELLING:
            TravellingStats.objects.create(entry=entry, **stats)

        return entry
    
class LeaderboardSerializer(serializers.ModelSerializer):
    entries = LeaderboardEntrySerializer(
        source="leaderboardentry_set",
        many=True,
        read_only=True
    )

    class Meta:
        model = Leaderboard
        fields = [
            "id",
            "stats_type",
            "difficulty",
            "entries",
        ]