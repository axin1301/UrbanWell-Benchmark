import json
import random
import re
from collections import defaultdict, deque
from pathlib import Path

random.seed(42)

ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = ROOT / "outputs"
FINAL_ROOT = OUTPUT_ROOT / "final_benchmark"
LIMIT = 500

def round_robin_sample(data, key="city_name", limit=500):
    city_buckets = defaultdict(deque)
    for item in data:
        city_buckets[item[key]].append(item)

    result = []
    cities = list(city_buckets.keys())
    while len(result) < limit and cities:
        for city in cities[:]:
            if city_buckets[city]:
                result.append(city_buckets[city].popleft())
                if len(result) >= limit:
                    break
            else:
                cities.remove(city)
    return result


def parse_single_indicator(filename: str):
    if filename.startswith("LU_") and filename.endswith("_MC_single_year.json"):
        return "landuse"
    m = re.match(r"^[^_]+_(.+?)_single_year_", filename)
    if m:
        return m.group(1)
    return None


def parse_multi_indicator(filename: str, task_type: str):
    m = re.match(rf"^[^_]+_(.+?)_multi_year_{task_type}_", filename)
    if m:
        return m.group(1)
    return None


def load_city_jsons(mode: str):
    base = OUTPUT_ROOT / mode
    grouped = defaultdict(list)
    if not base.exists():
        return grouped

    for city_dir in sorted([p for p in base.iterdir() if p.is_dir()]):
        city_name = city_dir.name
        for json_file in sorted(city_dir.glob("*.json")):
            if mode == "single_year":
                indicator = parse_single_indicator(json_file.name)
            elif mode == "multi_year_type1":
                if "single_year_selected_type1" in json_file.name:
                    continue
                indicator = parse_multi_indicator(json_file.name, "type1")
            elif mode == "multi_year_type3":
                if "single_year_selected_type3" in json_file.name:
                    continue
                indicator = parse_multi_indicator(json_file.name, "type3")
            else:
                indicator = None

            if not indicator:
                continue

            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    items = json.load(f)
            except Exception:
                continue

            if not isinstance(items, list):
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue
                item = dict(item)
                item.setdefault("city_name", city_name)
                grouped[indicator].append(item)

    return grouped


def write_final_benchmarks(mode: str):
    grouped = load_city_jsons(mode)
    out_dir = FINAL_ROOT / mode
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = []
    for indicator, items in sorted(grouped.items()):
        sampled = round_robin_sample(items, key="city_name", limit=LIMIT)
        out_path = out_dir / f"{indicator}_{mode}_benchmark_500.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(sampled, f, indent=2, ensure_ascii=False)
        summary.append((indicator, len(items), len(sampled), str(out_path)))
    return summary


def main():
    all_summary = {}
    for mode in ["single_year", "multi_year_type1", "multi_year_type3"]:
        all_summary[mode] = write_final_benchmarks(mode)

    for mode, rows in all_summary.items():
        print(f"[{mode}]")
        if not rows:
            print("  no benchmark sources found")
            continue
        for indicator, total_count, sampled_count, out_path in rows:
            print(f"  {indicator}: total={total_count}, sampled={sampled_count}, output={out_path}")


if __name__ == "__main__":
    main()
