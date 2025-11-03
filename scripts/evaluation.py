from __future__ import annotations
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report
import numpy as np


def evaluate_from_csv(results_csv: str, labels_csv: str, out_dir: str = "output/figures", threshold: float = 0.5):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    rcsv, lcsv = Path(results_csv), Path(labels_csv)
    if not (rcsv.exists() and lcsv.exists()):
        print("[Eval] Precisa de results_csv e labels_csv."); return None
    dfp = pd.read_csv(rcsv)
    dfl = pd.read_csv(lcsv)
    # normaliza chave por nome do arquivo
    dfp['key'] = dfp['path'].apply(lambda p: Path(p).name)
    dfl['key'] = dfl['path'].apply(lambda p: Path(p).name)
    df = dfp.merge(dfl[['key','label']], on='key', how='inner')

    if df.empty:
        print("[Eval] Não houve interseção entre predições e labels."); return None
    y_true = df['label'].astype(int).to_numpy()
    y_pred = (df['prob'].to_numpy() > threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred)
    rep = classification_report(y_true, y_pred, digits=3)
    (out/"metricas_modelo.txt").write_text(rep, encoding="utf-8")
    # Matriz de confusão
    fig, ax = plt.subplots(figsize=(4,4))
    im = ax.imshow(cm, interpolation="nearest")
    ax.set_title("Matriz de confusão"); ax.set_xlabel("Predito"); ax.set_ylabel("Verdadeiro")
    
    for (i,j), v in np.ndenumerate(cm):
        ax.text(j, i, str(v), ha='center', va='center')
    fig.tight_layout(); fig.savefig(out/"confusion_matrix.png", dpi=150)
    plt.close(fig)
    print("[Eval] Relatório salvo e matriz gerada.")
    return {"report": rep, "cm": cm.tolist()}
