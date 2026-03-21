from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Achievement, Player, PlayerAchievement


@receiver(post_save, sender=Player)
def create_default_achievements_for_new_player(sender, instance, created, **kwargs):
    if not created:
        return

    achievements = Achievement.objects.all()
    if not achievements.exists():
        return

    PlayerAchievement.objects.bulk_create(
        [
            PlayerAchievement(
                player=instance,
                achievement=achievement,
                status=False,
            )
            for achievement in achievements
        ],
        ignore_conflicts=True,
    )


@receiver(post_save, sender=Achievement)
def add_new_achievement_to_all_players(sender, instance, created, **kwargs):
    if not created:
        return

    players = Player.objects.all()
    if not players.exists():
        return

    PlayerAchievement.objects.bulk_create(
        [
            PlayerAchievement(
                player=player,
                achievement=instance,
                status=False,
            )
            for player in players
        ],
        ignore_conflicts=True,
    )
