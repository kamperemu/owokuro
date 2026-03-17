import argparse
import json
import logging
import tempfile
import uuid
import zipfile
from pathlib import Path

from owokuro.converter import generate_mokuro_volume
from owokuro.owosocket import OwocrResult, OwocrWebsocket


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp", ".avif")
ARCHIVE_SUFFIXES = (".cbz", ".zip")
TEMP_DIRECTORY_PREFIX = "owokuro_"


def _get_volume_name(volume: Path) -> str:
    return volume.stem if volume.is_file() else volume.name


def _is_supported_archive(file: Path) -> bool:
    return file.is_file() and file.suffix.lower() in ARCHIVE_SUFFIXES


def _process_directory(owo_socket: OwocrWebsocket, volume_path: Path) -> list[OwocrResult]:
    results: list[OwocrResult] = []

    for p in sorted(volume_path.iterdir()):
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES:
            results.append(owo_socket.process_image(p))

    return results


def _process_file(owo_socket: OwocrWebsocket, volume_path: Path) -> list[OwocrResult]:
    with tempfile.TemporaryDirectory(prefix=TEMP_DIRECTORY_PREFIX) as temp_dir:
        temp_path = Path(temp_dir)
        with zipfile.ZipFile(volume_path) as f:
            for entry in f.infolist():
                f.extract(entry, temp_path)

        return _process_directory(owo_socket, temp_path)


def run():
    parser = argparse.ArgumentParser(description="Mokuro manga processor")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "volume",
        nargs="?",
        type=Path,
        help="Path to a single volume (directory or CBZ/ZIP file)",
    )
    group.add_argument(
        "--parent_dir",
        type=Path,
        help="Path to manga title directory containing multiple volumes",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7331,
        help="Port for the OwocrWebsocket connection (default: 7331)",
    )
    args = parser.parse_args()

    volume_paths: list[Path] = []
    metadata = dict()
    if args.volume:
        volume_paths.append(args.volume)
        metadata['title'] = _get_volume_name(args.volume)
        metadata['title_uuid'] = uuid.uuid4()
        metadata['parent_dir'] = args.volume.parent
    elif args.parent_dir:
        seen_volume_names: set[str] = set()

        # Default sort order is expected to give directories first for priority (but it's okay if that changes)
        for p in sorted(args.parent_dir.iterdir()):
            if not p.is_dir() and not _is_supported_archive(p):
                continue

            volume_name = _get_volume_name(p)
            if volume_name in seen_volume_names:
                log.warning(f"Skipping duplicate volume: {p}")
                continue

            volume_paths.append(p)
            seen_volume_names.add(volume_name)

        metadata['title'] = args.parent_dir.name
        metadata['title_uuid'] = uuid.uuid4()
        metadata['parent_dir'] = args.parent_dir

    log.info(f"Processing {len(volume_paths)} volume(s) for '{metadata['title']}'")

    owo_socket = OwocrWebsocket(args.port)

    for volume_path in volume_paths:
        volume_name = _get_volume_name(volume_path)
        log.info(f"Starting volume: {volume_name}")

        owocr_json_pages: list[OwocrResult] = []
        if volume_path.is_dir():
            owocr_json_pages = _process_directory(owo_socket, volume_path)
        elif _is_supported_archive(volume_path):
            owocr_json_pages = _process_file(owo_socket, volume_path)
        else:
            log.warning(f"Skipping unsupported volume: {volume_path}")
            continue

        output_mokuro_path = volume_path.parent / f"{volume_name}.mokuro"

        with open(output_mokuro_path, 'w', encoding='utf-8') as f:
            mokuro_data = generate_mokuro_volume(
                title=metadata['title'],
                title_uuid=str(metadata['title_uuid']),
                volume_name=volume_name,
                volume_json_data=owocr_json_pages,
            )
            json.dump(mokuro_data, f, ensure_ascii=False)

        log.info(f"Generated {output_mokuro_path.name}")

    log.info("All volumes successfully generated.")

    owo_socket.close()
