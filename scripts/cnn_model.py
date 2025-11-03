from pathlib import Path
import numpy as np, pandas as pd, rasterio as rio, cv2
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks, optimizers
from tqdm import tqdm


def _load_ndvi(path: Path, size=(128,128)) -> np.ndarray:
    with rio.open(path) as ds:
        ndvi = ds.read(1).astype("float32")
    img = (ndvi + 1.0) / 2.0
    img = cv2.resize(img, size, interpolation=cv2.INTER_AREA)
    return img[...,None]


def train_cnn(ndvi_dir: str, labels_csv: str, models_dir: str,
              input_size=(128,128), batch_size=16, epochs=8, lr=5e-4, augment=True):
    models_path = Path(models_dir); models_path.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(labels_csv, comment="#").dropna()
    X, y = [], []
    
    for _, row in tqdm(df.iterrows(), total=len(df)):
        p = Path(row["path"])
        if not p.is_absolute(): p = Path(ndvi_dir)/Path(row["path"]).name
        if not p.exists(): continue
        X.append(_load_ndvi(p, input_size))
        y.append(int(row["label"]))
    X = np.array(X, dtype="float32"); y = np.array(y, dtype="int32")

    if len(X) < 4: print("[WARN] Poucos exemplos em labels.csv.")
    Xtr, Xva, ytr, yva = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y if len(np.unique(y))>1 else None)

    aug = tf.keras.Sequential([layers.RandomFlip("horizontal"), layers.RandomRotation(0.05)]) if augment else (lambda z: z)
    inp = layers.Input(shape=(input_size[1], input_size[0], 1)); x = aug(inp)
    x = layers.Conv2D(16,3,activation="relu",padding="same")(x); x = layers.MaxPool2D()(x)
    x = layers.Conv2D(32,3,activation="relu",padding="same")(x); x = layers.MaxPool2D()(x)
    x = layers.Conv2D(64,3,activation="relu",padding="same")(x); x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(64,activation="relu")(x); out = layers.Dense(1,activation="sigmoid")(x)
    model = models.Model(inp,out)
    model.compile(optimizer=optimizers.Adam(learning_rate=lr), loss="binary_crossentropy", metrics=["accuracy"])

    ck = callbacks.ModelCheckpoint(str(models_path/"melhor_modelo.h5"), save_best_only=True, monitor="val_accuracy", mode="max")
    es = callbacks.EarlyStopping(patience=5, restore_best_weights=True)
    model.fit(Xtr, ytr, validation_data=(Xva,yva), epochs=epochs, batch_size=batch_size, callbacks=[ck,es], verbose=2)
    model.save(models_path/"modelo_final.h5")

    if len(Xva):
        ypred = (model.predict(Xva, verbose=0) > 0.5).astype("int32").ravel()
        rep = classification_report(yva, ypred, digits=3)
        Path("output/reports").mkdir(parents=True, exist_ok=True)
        (Path("output/reports")/"metricas_modelo.txt").write_text(rep, encoding="utf-8")
        print(rep)


def run_inference(model_path: str, ndvi_dir: str, out_csv: str, db_path: str):
    import pandas as pd, sqlite3
    m = tf.keras.models.load_model(model_path, compile=False)
    paths = sorted(Path(ndvi_dir).glob("*_ndvi.tif"))
    rows = []
    for p in paths:
        img = _load_ndvi(p)
        prob = float(m.predict(img[None,...], verbose=0)[0][0])
        rows.append({"path": str(p), "prob": prob, "pred": int(prob>0.5)})
    df = pd.DataFrame(rows); out = Path(out_csv); out.parent.mkdir(parents=True, exist_ok=True); df.to_csv(out, index=False, encoding="utf-8")
    con = sqlite3.connect(db_path); df.to_sql("predictions", con, if_exists="replace", index=False); con.close()
