# VigiAI — Detecção e monitoramento de desmatamento na Amazônia.

Aplicação acadêmica referente às matérias de **Processamento de Imagens e Visão Computacional** para detecção de **desmatamentos na Amazônia**, utilizando **NDVI (Índice de Vegetação por Diferença Normalizada)**, **CNNs (Tensorflow/Keras)**, **Google Earth Engine (Sentinel‑2)** e **dashboard HTML interativo** (Folium + Plotly) para classificar imagens e identificar áreas afetadas..

## Estrutura do projeto:

VigiAI/
│
├── setup_env.bat               # Instala dependências + executa main.py automaticamente
│
├── settings.yaml               # Salva as credenciais do GEE
│   
├── client_secrets              # Credenciais do Google Earth Engine
│
├── config.sample.json          # Exemplo área de análise
│
├── main.py                     # Pipeline completo (download → NDVI → CNN → dashboard)
│
├── data/
│   ├── raw/                    # GeoTIFFs baixados
│   ├── processed/              # Imagens após o cálculo do NDVI
│   ├── ndvi/                   # NDVIs calculados e suavizados
│   ├── labels/                 # Rótulos de treino
│   └── db/
│       └── ndvi_data.db         # Banco SQLite
│   
├── models/
│   ├── modelo_final.h5         # Modelo CNN treinado
│   └── melhor_modelo.h5        # Checkpoint do melhor modelo
│
├── scripts/
│   ├── ndvi_utils.py           # Cálculo NDVI
│   ├── cnn_model.py            # Arquitetura e treinamento da CNN
│   ├── data_processing.py      # Carregamento + filtragem + pré-processamento + extração de bandas Sentinel-2
│   ├── evaluation.py           # Métricas, visualizações e relatórios
│   ├── automation.py           # Pipeline de automação
│   ├── drive_sync              # Conexão com o Google Drive
│   ├── backup.py               # Backup automático do modelo e resultados
│   ├── database.py             # SQLite + inserção de resultados
│   └── dashboard.py            # Geração de dashboard Plotly + Folium (HTML interativo)
│
├── output/
│   ├── reports/
│   │   ├── resultados_queimadas.csv  # Resultados de predição (áreas afetadas)
│   │   └── metricas_modelo.txt       # Métricas de desempenho (Acurácia, F1, AUC, etc.)
│   ├── figures/
│   │   └── confusion_matrix.png      # Matriz de confusão 
│   └── logs/
│       └── execucao.log              # Log de execução (pipeline e erros)
│
├── backup/
│   ├── modelo_final.h5               # Backup do modelo
│   └── resultados_queimada.csv       # Backup dos resultados
│
├── requirements.txt
├── .gitignore
├── README.md
└── LICENSE


## Funcionalidades
- Aquisição automática de imagens Sentinel-2 via **Google Earth Engine**  
- Cálculo, segmentação e suavização do **NDVI**
- Treinamento e avaliação de uma **CNN binária**
- Armazenamento em um banco **SQLite**
- Geração de **dashboard interativo** com **Folium + Plotly**
- Backup automático e logs detalhados

## Requisitos:
- Python 3.10 
- Conta ativa no [Google Earth Engine](https://earthengine.google.com/)

## Passo a passo
```
set EE_PROJECT_ID=aps-vigiai
python main.py --download --config config.sample.json
python main.py --sync-drive
python main.py --ndvi
python main.py --make-labels   # edite alguns para 1
python main.py --train
python main.py --predict --evaluate --backup
python main.py --dashboard
```
