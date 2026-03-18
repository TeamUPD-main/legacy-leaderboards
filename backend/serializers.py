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

from .models import StatsType, DifficultyType

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
    difficulty = serializers.CharField()
    type = serializers.CharField()
    score = serializers.IntegerField()
    stats = serializers.DictField()

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

    def create(self, validated_data):
        player, _ = Player.objects.get_or_create(
            uid=validated_data["player_uid"]
        )

        difficulty_key = str(validated_data["difficulty"]).lower()
        type_key = str(validated_data["type"]).lower()

        try:
            difficulty = self.DIFFICULTY_MAP[difficulty_key]
        except KeyError as exc:
            allowed = ", ".join(self.DIFFICULTY_MAP.keys())
            raise serializers.ValidationError(
                {"difficulty": f"Invalid difficulty. Allowed values: {allowed}"}
            ) from exc

        try:
            stats_type = self.TYPE_MAP[type_key]
        except KeyError as exc:
            allowed = ", ".join(self.TYPE_MAP.keys())
            raise serializers.ValidationError(
                {"type": f"Invalid type. Allowed values: {allowed}"}
            ) from exc

        leaderboard, _ = Leaderboard.objects.get_or_create(
            stats_type=stats_type,
            difficulty=difficulty,
        )

        entry = LeaderboardEntry.objects.create(
            player=player,
            leaderboard=leaderboard,
            total_score=validated_data["score"],
            rank=0,  # compute later
        )

        stats = validated_data["stats"]

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