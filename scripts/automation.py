from __future__ import annotations
import schedule, time
from pathlib import Path
from .data_processing import download_sentinel_tiles_via_drive
from .ndvi_utils import batch_compute_ndvi
from .cnn_model import run_inference


def run_once(cfg: dict):
    gee = cfg.get("gee", {})
    download_sentinel_tiles_via_drive(
        aoi_geojson=gee.get("aoi_geojson"),
        bbox=gee.get("bbox_approx"),
        start_date=gee.get("start_date"),
        end_date=gee.get("end_date"),
        collection=gee.get("collection", "COPERNICUS/S2_SR_HARMONIZED"),
        cloud_filter=int(gee.get("cloud_filter", 50)),
        drive_folder=gee.get("drive_folder", "VigiAI"),
        max_tiles=int(gee.get("max_tiles", 6)),
        export_scale=int(gee.get("export_scale", 20)),
        out_dir="data/raw",
        wait_for_tasks=True,
    )
    batch_compute_ndvi("data/raw", "data/ndvi", "data/processed")
    run_inference("models/modelo_final.h5", "data/ndvi", "output/reports/resultados_queimadas.csv", "data/db/ndvi_data.db")


def schedule_every(hours: int, cfg: dict):
    schedule.every(hours).hours.do(run_once, cfg)
    print(f"[Automation] Agendado a cada {hours}h. Ctrl+C para sair.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("[Automation] Encerrado pelo usuário.")
