import copy
import xml.etree.ElementTree as ET
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from backend.models import Achievement


XLAST_NS = "http://www.xboxlive.com/xlast"
NS = {"x": XLAST_NS}


def qname(tag: str) -> str:
    return f"{{{XLAST_NS}}}{tag}"


def get_translation(localized_string: ET.Element, locale: str) -> str:
    for translation in localized_string.findall("x:Translation", NS):
        if translation.get("locale") == locale:
            return (translation.text or "").strip()
    return ""


def build_localized_lookup(root: ET.Element, locale: str) -> dict[int, str]:
    lookup: dict[int, str] = {}
    for localized in root.findall(".//x:LocalizedString", NS):
        friendly_name = localized.get("friendlyName", "")
        if not friendly_name.startswith("ACH_"):
            continue

        string_id_raw = localized.get("id")
        if not string_id_raw:
            continue

        try:
            string_id = int(string_id_raw)
        except ValueError:
            continue

        lookup[string_id] = get_translation(localized, locale)

    return lookup


def build_filtered_localizedstrings(root: ET.Element, locale: str) -> ET.Element:
    localized_strings = root.find(".//x:LocalizedStrings", NS)
    if localized_strings is None:
        raise CommandError("Could not find <LocalizedStrings> in the gameconfig file.")

    filtered = copy.deepcopy(localized_strings)

    for supported in list(filtered.findall("x:SupportedLocale", NS)):
        if supported.get("locale") != locale:
            filtered.remove(supported)

    for localized in list(filtered.findall("x:LocalizedString", NS)):
        friendly_name = localized.get("friendlyName", "")
        if not friendly_name.startswith("ACH_"):
            filtered.remove(localized)
            continue

        for translation in list(localized.findall("x:Translation", NS)):
            if translation.get("locale") != locale:
                localized.remove(translation)

    return filtered


class Command(BaseCommand):
    help = "Import achievements from a .gameconfig XML file into backend.Achievement"

    def add_arguments(self, parser):
        parser.add_argument(
            "gameconfig",
            nargs="?",
            default="Minecraft.gameconfig",
            help="Path to input .gameconfig file",
        )
        parser.add_argument(
            "--locale",
            default="en-US",
            help="Locale to import from LocalizedStrings (default: en-US)",
        )
        parser.add_argument(
            "--filtered-output",
            default="",
            help=(
                "Optional output path for filtered LocalizedStrings XML containing "
                "only ACH_* and the selected locale"
            ),
        )
        parser.add_argument(
            "--clear-missing",
            action="store_true",
            help="Delete Achievement rows that are not present in the input file",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and report changes without writing to the database",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = Path(options["gameconfig"])
        locale = options["locale"]
        filtered_output = options["filtered_output"]
        clear_missing = options["clear_missing"]
        dry_run = options["dry_run"]

        if not file_path.exists():
            raise CommandError(f"Input file does not exist: {file_path}")

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError as exc:
            raise CommandError(f"Failed to parse XML: {exc}") from exc

        localized_lookup = build_localized_lookup(root, locale)
        achievement_nodes = root.findall(".//x:Achievements/x:Achievement", NS)

        if not achievement_nodes:
            raise CommandError("No <Achievement> nodes found in the gameconfig file.")

        imported_ids: set[int] = set()
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for node in achievement_nodes:
            achievement_id_raw = node.get("id")
            if not achievement_id_raw:
                skipped_count += 1
                continue

            try:
                achievement_id = int(achievement_id_raw)
            except ValueError:
                skipped_count += 1
                continue

            title_id = int(node.get("titleStringId", "0"))
            description_id = int(node.get("descriptionStringId", "0"))
            how_to_id = int(node.get("unachievedStringId", "0"))
            score = int(node.get("cred", "0"))

            defaults = {
                "name": localized_lookup.get(title_id, ""),
                "description": localized_lookup.get(description_id, ""),
                "how_to": localized_lookup.get(how_to_id, ""),
                "score": score,
            }

            imported_ids.add(achievement_id)

            if dry_run:
                if Achievement.objects.filter(id=achievement_id).exists():
                    updated_count += 1
                else:
                    created_count += 1
                continue

            _, created = Achievement.objects.update_or_create(
                id=achievement_id,
                defaults=defaults,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        deleted_count = 0
        if clear_missing and imported_ids:
            qs = Achievement.objects.exclude(id__in=imported_ids)
            deleted_count = qs.count()
            if not dry_run:
                qs.delete()

        if filtered_output:
            filtered_root = build_filtered_localizedstrings(root, locale)
            output_path = Path(filtered_output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            ET.register_namespace("", XLAST_NS)
            filtered_tree = ET.ElementTree(filtered_root)
            if hasattr(ET, "indent"):
                ET.indent(filtered_tree, space="  ")
            filtered_tree.write(output_path, encoding="utf-16", xml_declaration=True)
            self.stdout.write(f"Filtered XML written to: {output_path}")

        if dry_run:
            transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                "Achievement import complete "
                f"(created={created_count}, updated={updated_count}, "
                f"skipped={skipped_count}, deleted={deleted_count}, dry_run={dry_run})."
            )
        )
