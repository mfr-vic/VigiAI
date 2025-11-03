from __future__ import annotations
from pathlib import Path
import shutil, datetime


def backup_artifacts(models_dir: str = "models",
                     reports_dir: str = "output/reports",
                     backup_dir: str = "backup") -> int:
    md, rd, bd = Path(models_dir), Path(reports_dir), Path(backup_dir)
    bd.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    copied = 0
    for p in [md/"modelo_final.h5", md/"melhor_modelo.h5", rd/"resultados_queimadas.csv", rd/"metricas_modelo.txt"]:
        if p.exists():
            dst = bd / f"{p.stem}_{ts}{p.suffix}"
            shutil.copy2(p, dst); copied += 1
    print(f"[Backup] {copied} arquivos copiados para {bd}.")
    return copied
