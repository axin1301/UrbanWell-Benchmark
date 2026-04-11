import json
import re
from pathlib import Path
from typing import Any


STV_PATH_PATTERN = re.compile(
    r"downloaded_stv_selected/(?P<city_name>[^/]+)/(?P<identifier>[^/]+)/street_view_images/(?P<image_name>[^/]+)$"
)


def parse_stv_path(path_str: str) -> dict[str, Any] | None:
    normalized = path_str.replace('\\', '/')
    match = STV_PATH_PATTERN.search(normalized)
    if not match:
        return None

    image_name = match.group('image_name')
    if not image_name.lower().endswith('.jpg'):
        return None

    stem = image_name[:-4]
    if not stem.startswith('street_view_'):
        return None

    parts = stem.split('_')
    if len(parts) < 10 or parts[0] != 'street' or parts[1] != 'view':
        return None

    query_lat = float(parts[2])
    query_lon = float(parts[3])
    returned_lat = float(parts[4])
    returned_lon = float(parts[5])
    year = int(parts[6])
    date = parts[7]
    heading = int(parts[-1])
    pano_id = '_'.join(parts[8:-1])
    if not pano_id:
        raise ValueError(f'Cannot parse pano_id from image name: {image_name}')

    return {
        'image_name': image_name,
        'city_name': match.group('city_name'),
        'identifier': match.group('identifier'),
        'year': year,
        'date': date,
        'pano_id': pano_id,
        'heading': heading,
        'query_lat': query_lat,
        'query_lon': query_lon,
        'returned_lat': returned_lat,
        'returned_lon': returned_lon,
        'pitch': 0,
        'fov': 90,
        'source': 'google_street_view',
    }


def build_metadata(benchmark_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    metadata_map: dict[str, dict[str, Any]] = {}
    errors: list[str] = []

    for json_path in sorted(benchmark_dir.glob('*.json')):
        with json_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            errors.append(f'{json_path.name}: expected a list of samples')
            continue

        for sample_index, sample in enumerate(data):
            images = sample.get('images', [])
            if not isinstance(images, list):
                errors.append(f'{json_path.name} item {sample_index}: `images` is not a list')
                continue
            for image_path in images:
                if not isinstance(image_path, str) or 'street_view_images' not in image_path:
                    continue
                try:
                    parsed = parse_stv_path(image_path)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f'{json_path.name} item {sample_index}: {image_path} -> {exc}')
                    continue
                if parsed is None:
                    errors.append(f'{json_path.name} item {sample_index}: could not parse {image_path}')
                    continue
                metadata_map[parsed['image_name']] = parsed

    metadata = sorted(
        metadata_map.values(),
        key=lambda item: (item['city_name'], item['identifier'], item['year'], item['image_name']),
    )
    return metadata, errors


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    benchmark_dir = project_root / 'benchmark_dataset'
    output_path = project_root / 'evaluate' / 'metadata' / 'metadata_stv_from_benchmark.json'
    error_path = project_root / 'evaluate' / 'metadata' / 'metadata_stv_from_benchmark_errors.json'

    metadata, errors = build_metadata(benchmark_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open('w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    with error_path.open('w', encoding='utf-8') as f:
        json.dump(errors, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        'metadata_path': str(output_path),
        'error_path': str(error_path),
        'num_metadata': len(metadata),
        'num_errors': len(errors),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
