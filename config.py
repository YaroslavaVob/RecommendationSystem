import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Пути к ресурсам
MODEL_PATH = os.path.join(BASE_DIR, "model", "catboost_ranker.bin")
ANNOY_INDEX_PATH = os.path.join(BASE_DIR, "model", "item_index.ann")
ITEMS_PATH = os.path.join(BASE_DIR, "model", "data", "items.parquet")
CLEANED_EVENTS_PATH = os.path.join(BASE_DIR, "model", "data", "cleaned_events.parquet")
RANKER_DATA_PATH = os.path.join(BASE_DIR, "model", "data", "df_ranker.parquet")

# БД
DB_PATH = os.path.join(BASE_DIR, "db", "users.db")

# Логи
LOG_PATH = os.path.join(BASE_DIR, "logs", "app.log")

# Prometheus
PROMETHEUS_PORT = 8001

