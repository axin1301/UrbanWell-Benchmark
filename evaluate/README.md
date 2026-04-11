# evaluate

This folder contains simple utility scripts for benchmark evaluation.

For evaluation-only setup, install:

```bash
pip install -r requirements-eval.txt
```

## Scripts

- `download_sat_images_from_metadata.py`: downloads satellite images from `metadata_sat` and stores them under `sat-image/`.
- `download_stv_from_metadata.py`: downloads Street View images from `metadata_stv` and stores them under `stv-image/`.
- `build_sat_metadata_from_benchmark.py`: builds `metadata_sat` from benchmark JSON files and real `*_list1.txt` boundary files.
- `build_stv_metadata_from_benchmark.py`: builds `metadata_stv` from benchmark JSON files.
- `rewrite_benchmark_image_paths.py`: rewrites image paths in benchmark JSON files to local `sat-image/` and `stv-image/` layouts.
- `evaluate_predictions.py`: computes `R2` and `RMSE` from a benchmark JSON file and predictions.
- `global/metrics.py`: OpenRouter-based CLI evaluation entrypoint.

## Satellite image download

The downloader expects a metadata JSON file containing a list of objects. Each object must include:
- `sat_image_name`
- `year`
- `boundary`
- `city_name`

Boundary format:
- `boundary = [min_lat, max_lat, min_lng, max_lng]`

A sample file is provided at:
- `evaluate/metadata/metadata_sat_example.json`

The full `metadata_sat` file is hosted on Hugging Face: [XFengbao/UrbanWell](https://huggingface.co/datasets/XFengbao/UrbanWell). You can also generate it locally with `python evaluate/build_sat_metadata_from_benchmark.py --list-files-root "/path/to/download_sat"`.

Example:

```bash
python evaluate/download_sat_images_from_metadata.py path/to/metadata_sat.json --downloader-exe downloader.exe
```

By default, downloaded images are organized as:

```text
sat-image/<YEAR>/<CITY_NAME>/<sat_image_name>
```

The script also writes a manifest file to:

```text
sat-image/metadata_sat_download_manifest.json
```

Notes:
- `download_sat_images_from_metadata.py` depends on `downloader.exe`.
- If the exact image file name is not found in the raw download directory, the script falls back to the only image file found there and renames it to `sat_image_name`.
- Use `--skip-existing` to avoid re-downloading images that already exist.
- Use `--keep-raw` if you want to keep the raw downloader outputs under `sat-image/_raw/`.

## Street View image download

The Street View downloader expects a metadata JSON file containing a list of objects. Each object must include:
- `image_name`
- `city_name`
- `identifier`
- `year`
- `date`
- `pano_id`
- `heading`
- `query_lat`
- `query_lon`
- `returned_lat`
- `returned_lon`

Optional fields:
- `pitch` (default: `0`)
- `fov` (default: `90`)
- `source`

A sample file is provided at:
- `evaluate/metadata/metadata_stv_example.json`

The full `metadata_stv` file is hosted on Hugging Face: [XFengbao/UrbanWell](https://huggingface.co/datasets/XFengbao/UrbanWell). You can also generate it locally with `python evaluate/build_stv_metadata_from_benchmark.py`.

Example:

```bash
python evaluate/download_stv_from_metadata.py path/to/metadata_stv.json
```

Or pass the key directly:

```bash
python evaluate/download_stv_from_metadata.py path/to/metadata_stv.json --api-key YOUR_GOOGLE_KEY
```

By default, downloaded images are organized as:

```text
stv-image/<CITY_NAME>/<IDENTIFIER>/street_view_images/<image_name>
```

The script also writes a manifest file to:

```text
stv-image/metadata_stv_download_manifest.json
```

Notes:
- `download_stv_from_metadata.py` uses the Google Street View API.
- By default, it reads the API key from `GOOGLE_KEY_MY`.
- The metadata should keep the full naming information used by the benchmark so the downloaded file names match the image paths in the benchmark JSON files.
- Use `--skip-existing` to avoid re-downloading images that already exist.

## Build metadata from benchmark

Street View metadata:

```bash
python evaluate/build_stv_metadata_from_benchmark.py
```

Satellite metadata using real downloader boundary files:

```bash
python evaluate/build_sat_metadata_from_benchmark.py --list-files-root "/path/to/download_sat"
```

## Rewrite benchmark image paths

Rewrite satellite image paths to the local publish layout:

```bash
python evaluate/rewrite_benchmark_image_paths.py --rewrite-sat
```

This rewrites satellite image paths to:

```text
sat-image/<YEAR>/<CITY_NAME>/<sat_image_name>
```

Rewrite both satellite and Street View image paths:

```bash
python evaluate/rewrite_benchmark_image_paths.py --rewrite-sat --rewrite-stv
```

This rewrites Street View image paths to:

```text
stv-image/<CITY_NAME>/<IDENTIFIER>/street_view_images/<image_name>
```

By default, rewritten files are written to `benchmark_dataset_rewritten/`. Use `--in-place` to overwrite the original JSON files.

## OpenRouter CLI evaluation

Before running the evaluation command, set your OpenRouter API key.

PowerShell example:

```powershell
$env:OPENROUTER_API_KEY = "your_openrouter_api_key"
```

Run evaluation with a command such as:

```bash
python -m evaluate.global.metrics --model_name="openai/gpt-4o" --task_type="single" --task_name="population"
```

Supported arguments:
- `--model_name`: OpenRouter model name, using the OpenRouter model zoo naming format.
- `--task_type`: one of `single`, `multi_year_type1`, `multi_year_type3`.
- `--task_name`: indicator name, such as `population`, `NO2`, `beautiful`, or `avg_dist_to_restaurant`.
- `--benchmark_dir`: optional benchmark JSON directory. If omitted, the code uses `benchmark_dataset_rewritten/` when available, otherwise `benchmark_dataset/`.
- `--results_root`: output root directory for predictions and metric summaries. Default: `evaluate/results`.
- `--existing_mode`: one of `reuse`, `missing`, `rerun`.
- `--api_key`: optional OpenRouter API key passed directly from the command line.
- `--max_samples`: optional limit for debugging on a subset of samples.
- `--timeout`: HTTP timeout in seconds for each OpenRouter request.

Existing-result behavior:
- `reuse`: if prediction files already exist, skip model inference and directly recompute `R2` and `RMSE`.
- `missing`: reuse existing successful predictions and run the model only for missing samples.
- `rerun`: ignore old prediction files and run the model again for all samples.

Output files are stored under:

```text
evaluate/results/<MODEL_NAME>/<TASK_TYPE>/<TASK_NAME>/
```

The main outputs are:
- `predictions.json`: per-sample model outputs, parsed predictions, status, and errors.
- `summary.json`: aggregate `R2` and `RMSE`.

Notes:
- The CLI reads the API key from `OPENROUTER_API_KEY` unless `--api_key` is provided.
- If the benchmark JSON still contains old absolute image paths, the CLI will try to resolve them against local `sat-image/` and `stv-image/` directories.

## Prediction evaluation

The benchmark JSON should be a list of samples and normally includes:
- `ids`
- `references`
- `prompt`
- `images`

Predictions can be provided in either of two ways:

1. Add a `prediction` field directly to each benchmark sample.
2. Pass a separate predictions file with `--predictions`.

Supported prediction file formats:
- JSON object: `{ "sample_id": 1.23, ... }`
- JSON list: `[{"ids": "sample_id", "prediction": 1.23}, ...]`
- JSONL: one JSON object per line
- CSV: must contain `ids` and `prediction` columns

Example:

```bash
python evaluate/evaluate_predictions.py benchmark_dataset/avg_dist_to_restaurant_single_year_final_500.json --predictions predictions.json
```

Save outputs:

```bash
python evaluate/evaluate_predictions.py benchmark_dataset/avg_dist_to_restaurant_single_year_final_500.json --predictions predictions.json --output-json evaluate/results/summary.json --output-per-sample evaluate/results/per_sample.json
```





