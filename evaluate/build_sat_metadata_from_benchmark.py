import argparse
import json
import re
from pathlib import Path
from typing import Any


SAT_PATH_PATTERN = re.compile(
    r"downloaded_sat_(?P<year>\d+)_zoom_(?P<path_zoom>\d+)/(?P<city_name>[^/]+)/[^/]+/[^/]+/[^/]+/[^/]+/(?P<sat_image_name>[^/]+)$"
)
LIST_PATH_PATTERN = re.compile(
    r"downloaded_sat_(?P<year>\d+)_zoom_(?P<path_zoom>\d+)[/\\](?P<city_name>[^/\\]+)[/\\][^/\\]+[/\\](?P<list_name>[^/\\]+_list1\.txt)$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build metadata_sat from benchmark_dataset by matching satellite image names to *_list1.txt boundary files."
    )
    parser.add_argument(
        "--benchmark-dir",
        type=Path,
        default=Path("benchmark_dataset"),
        help="Directory containing benchmark JSON files. Default: benchmark_dataset",
    )
    parser.add_argument(
        "--list-files-root",
        type=Path,
        default=Path(r"D:\OneDrive - University of Helsinki\????4\download_sat"),
        help="Root directory used to search for *_list1.txt files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evaluate/metadata/metadata_sat_from_benchmark.json"),
        help="Output metadata_sat path.",
    )
    parser.add_argument(
        "--errors-output",
        type=Path,
        default=Path("evaluate/metadata/metadata_sat_from_benchmark_errors.json"),
        help="Output path for missing or malformed records.",
    )
    return parser.parse_args()


def parse_benchmark_sat_path(path_str: str) -> dict[str, Any] | None:
    normalized = path_str.replace('\\', '/')
    match = SAT_PATH_PATTERN.search(normalized)
    if not match:
        return None
    return {
        'sat_image_name': match.group('sat_image_name'),
        'year': int(match.group('year')),
        'city_name': match.group('city_name'),
    }


def parse_list_files(list_files_root: Path) -> tuple[dict[tuple[int, str, str], list[float]], list[str]]:
    boundary_map: dict[tuple[int, str, str], list[float]] = {}
    errors: list[str] = []

    for txt_path in sorted(list_files_root.rglob('*_list1.txt')):
        match = LIST_PATH_PATTERN.search(str(txt_path))
        if not match:
            continue

        year = int(match.group('year'))
        city_name = match.group('city_name')

        with txt_path.open('r', encoding='utf-8', errors='ignore') as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            continue

        for line_no, line in enumerate(lines[1:], start=2):
            parts = line.split()
            if len(parts) < 5:
                errors.append(f'{txt_path}: line {line_no} is malformed: {line}')
                continue
            image_name = parts[0].rstrip(':')
            try:
                left_edge_longitude = float(parts[1])
                right_edge_longitude = float(parts[2])
                top_edge_latitude = float(parts[3])
                bottom_edge_latitude = float(parts[4])
            except Exception as exc:  # noqa: BLE001
                errors.append(f'{txt_path}: line {line_no} has invalid coordinates: {exc}')
                continue

            boundary_map[(year, city_name, image_name)] = [
                bottom_edge_latitude,
                top_edge_latitude,
                left_edge_longitude,
                right_edge_longitude,
            ]

    return boundary_map, errors


def build_metadata(benchmark_dir: Path, boundary_map: dict[tuple[int, str, str], list[float]]) -> tuple[list[dict[str, Any]], list[str]]:
    metadata_map: dict[tuple[int, str, str], dict[str, Any]] = {}
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
                if not isinstance(image_path, str) or 'downloaded_sat_' not in image_path:
                    continue
                parsed = parse_benchmark_sat_path(image_path)
                if parsed is None:
                    errors.append(f'{json_path.name} item {sample_index}: could not parse {image_path}')
                    continue
                key = (parsed['year'], parsed['city_name'], parsed['sat_image_name'])
                if key not in boundary_map:
                    errors.append(
                        f'{json_path.name} item {sample_index}: missing boundary for '
                        f"year={parsed['year']} city={parsed['city_name']} image={parsed['sat_image_name']}"
                    )
                    continue
                metadata_map[key] = {
                    'sat_image_name': parsed['sat_image_name'],
                    'year': parsed['year'],
                    'boundary': boundary_map[key],
                    'city_name': parsed['city_name'],
                    'source': 'google_earth_downloader_list1',
                }

    metadata = sorted(
        metadata_map.values(),
        key=lambda item: (item['year'], item['city_name'], item['sat_image_name']),
    )
    return metadata, errors


def main() -> None:
    args = parse_args()
    boundary_map, list_file_errors = parse_list_files(args.list_files_root)
    metadata, build_errors = build_metadata(args.benchmark_dir, boundary_map)
    all_errors = list_file_errors + build_errors

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    with args.errors_output.open('w', encoding='utf-8') as f:
        json.dump(all_errors, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        'output': str(args.output),
        'errors_output': str(args.errors_output),
        'num_metadata': len(metadata),
        'num_errors': len(all_errors),
        'num_list1_boundaries': len(boundary_map),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
