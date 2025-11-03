import argparse, json, logging
from pathlib import Path

from scripts.database import init_db
from scripts.data_processing import (download_sentinel_tiles_via_drive, download_mosaic_via_drive,)
from scripts.ndvi_utils import batch_compute_ndvi
from scripts.drive_sync import download_new_exports
from scripts.backup import backup_artifacts
from scripts.evaluation import evaluate_from_csv

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def load_cfg(p):
    if not p:
        return {}
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main():
    ap = argparse.ArgumentParser(description="VigiAI pipeline")
    ap.add_argument("--config", default="config.manaus.json")
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--download-mosaic", action="store_true", help="Exportar 1 mosaico (B4/B8) para o Drive")
    ap.add_argument("--nowait", action="store_true", help="Não aguardar término das tarefas do GEE")
    ap.add_argument("--sync-drive", action="store_true")
    ap.add_argument("--ndvi", action="store_true")
    ap.add_argument("--make-labels", action="store_true")
    ap.add_argument("--train", action="store_true")
    ap.add_argument("--predict", action="store_true")
    ap.add_argument("--evaluate", action="store_true")
    ap.add_argument("--backup", action="store_true")
    ap.add_argument("--dashboard", action="store_true")
    ap.add_argument("--schedule", type=int, default=None, help="Agendar a cada N horas")
    args = ap.parse_args()

    cfg = load_cfg(args.config)
    gee = cfg.get("gee", {})
    cnn = cfg.get("cnn", {})

    # 1a) Download (tiles)
    if args.download:
        download_sentinel_tiles_via_drive(
            aoi_geojson=gee.get("aoi_geojson"),
            bbox=gee.get("bbox_approx"),
            start_date=gee.get("start_date"),
            end_date=gee.get("end_date"),
            collection=gee.get("collection", "COPERNICUS/S2_SR_HARMONIZED"),
            cloud_filter=int(gee.get("cloud_filter", 80)),
            drive_folder=gee.get("drive_folder", "VigiAI"),
            max_tiles=int(gee.get("max_tiles", 6)),
            export_scale=int(gee.get("export_scale", 20)),
            out_dir="data/raw",
            wait_for_tasks=not args.nowait,
        )

    # 1b) Download (mosaico)
    if args.download_mosaic:
        download_mosaic_via_drive(
            aoi_geojson=gee.get("aoi_geojson"),
            bbox=gee.get("bbox_approx"),
            start_date=gee.get("start_date"),
            end_date=gee.get("end_date"),
            collection=gee.get("collection", "COPERNICUS/S2_SR_HARMONIZED"),
            cloud_filter=int(gee.get("cloud_filter", 20)),
            drive_folder=gee.get("drive_folder", "VigiAI"),
            export_scale=int(gee.get("export_scale", 30)),
            description="vigiai_tile_mosaic",
            wait_for_task=not args.nowait,
        )

    # 2) Sincronizar Drive -> data/raw
    if args.sync_drive:
        download_new_exports(
            folder_name=gee.get("drive_folder", "VigiAI"),
            local_dir="data/raw",
            prefix="vigiai_tile_",
            dry_run=False
        )

    # 3) NDVI
    if args.ndvi:
        init_db("data/db/ndvi_data.db")
        n = batch_compute_ndvi("data/raw", "data/ndvi", "data/processed")
        logging.info("NDVI processados: %s", n)

    # 4) labels.csv auxiliar
    if args.make_labels:
        labels = Path("data/labels/labels.csv")
        ndvi_dir = Path("data/ndvi")
        lines = ["path,label"]
        for f in sorted(ndvi_dir.glob("*_ndvi.tif")):
            lines.append(f"{f.as_posix()},0")
        labels.parent.mkdir(parents=True, exist_ok=True)
        labels.write_text("\n".join(lines), encoding="utf-8")
        print(f"[OK] labels.csv criado com {len(lines)-1} linhas em {labels}")

    # 5) Treino da CNN
    if args.train:
        from scripts.cnn_model import train_cnn
        train_cnn(
            ndvi_dir="data/ndvi",
            labels_csv="data/labels/labels.csv",
            models_dir="models",
            input_size=tuple(cnn.get("input_size", [128, 128])),
            batch_size=int(cnn.get("batch_size", 16)),
            epochs=int(cnn.get("epochs", 8)),
            lr=float(cnn.get("learning_rate", 5e-4)),
            augment=bool(cnn.get("augment", True)),
        )

    # 6) Inferência
    if args.predict:
        from scripts.cnn_model import run_inference
        run_inference(
            model_path="models/modelo_final.h5",
            ndvi_dir="data/ndvi",
            out_csv="output/reports/resultados_queimadas.csv",
            db_path="data/db/ndvi_data.db",
        )

    # 7) Avaliação
    if args.evaluate:
        evaluate_from_csv(
            "output/reports/resultados_queimadas.csv",
            "data/labels/labels.csv",
            out_dir="output/figures"
        )

    # 8) Backup
    if args.backup:
        backup_artifacts()

    # 9) Dash
    if args.dashboard:
        from scripts.dashboard import build_dashboard
        build_dashboard(
            ndvi_dir="data/ndvi",
            results_csv="output/reports/resultados_queimadas.csv",
            out_html="output/reports/relatorio_final.html",
        )

    # 10) Agendamento
    if args.schedule:
        from scripts.automation import schedule_every
        schedule_every(int(args.schedule), cfg)

if __name__ == "__main__":
    main()
