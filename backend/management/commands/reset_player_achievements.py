from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from backend.models import Achievement, Player, PlayerAchievement


class Command(BaseCommand):
    help = "Reset all achievements for a player by UID"

    def add_arguments(self, parser):
        parser.add_argument(
            "--uid",
            required=True,
            help="Player UID (stored in Player.uid)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        uid = options["uid"]

        try:
            player = Player.objects.get(uid=uid)
        except Player.DoesNotExist as exc:
            raise CommandError(f"Player with uid '{uid}' was not found.") from exc

        achievements = list(Achievement.objects.all())
        if not achievements:
            self.stdout.write(self.style.WARNING("No achievements found. Nothing to reset."))
            return

        existing_links = PlayerAchievement.objects.filter(player=player)

        reset_count = existing_links.update(status=False)

        existing_achievement_ids = set(
            existing_links.values_list("achievement_id", flat=True)
        )

        missing_links = [
            PlayerAchievement(player=player, achievement=achievement, status=False)
            for achievement in achievements
            if achievement.id not in existing_achievement_ids
        ]

        created_count = 0
        if missing_links:
            created_count = len(
                PlayerAchievement.objects.bulk_create(
                    missing_links,
                    ignore_conflicts=True,
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Player achievements reset "
                f"for '{player.name}' ({player.uid})."
            )
        )
        self.stdout.write(f"Statuses reset to false: {reset_count}")
        self.stdout.write(f"Missing achievement rows created: {created_count}")
