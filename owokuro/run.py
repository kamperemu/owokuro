from owokuro.owosocket import OwocrWebsocket
from owokuro.converter import generate_mokuro_volume

import uuid
import argparse
from pathlib import Path
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

def run():
    parser = argparse.ArgumentParser(description="Mokuro manga processor")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "volume",
        nargs="?",
        type=Path,
        help="Path to a single volume directory",
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

    volume_paths = []
    metadata = dict()
    if args.volume:
        volume_paths.append(args.volume)
        metadata['title'] = args.volume.name
        metadata['title_uuid'] = uuid.uuid4()
        metadata['parent_dir'] = args.volume.parent
    elif args.parent_dir:
        for p in sorted(args.parent_dir.iterdir()):
            if p.is_dir():
                volume_paths.append(p)
        metadata['title'] = args.parent_dir.name
        metadata['title_uuid'] = uuid.uuid4()
        metadata['parent_dir'] = args.parent_dir

    log.info(f"Processing {len(volume_paths)} volume(s) for '{metadata['title']}'")

    owo_socket = OwocrWebsocket(args.port)

    for volume_path in volume_paths:

        log.info(f"Starting volume: {volume_path.name}")
        owocr_json_pages = []

        for p in sorted(volume_path.iterdir()):
            if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".avif"):
                owocr_json_pages.append(owo_socket.process_image(p))

        output_mokuro_path = volume_path.parent / f"{volume_path.name}.mokuro"

        with open(output_mokuro_path, 'w', encoding='utf-8') as f:
            mokuro_data = generate_mokuro_volume(metadata['title'], str(metadata['title_uuid']), volume_path.name, owocr_json_pages)
            json.dump(mokuro_data, f, ensure_ascii=False)

        log.info(f"Generated {output_mokuro_path.name}")

    log.info("All volumes successfully generated.")

    owo_socket.close()