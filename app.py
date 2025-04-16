from flask import Flask, render_template, request, redirect, url_for, flash, session, current_app
from flask_migrate import Migrate
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from metrics.prometheus_metrics import setup_metrics

import logging
import os
from db.db import init_db, populate_db, db  # Импортируем db для инициализации
from db.users import User # Импортируем модели User
from routes import routes  # Ваши маршруты
from model.recommend_system import HybridRecommender
import config

# Flask-приложение
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = os.urandom(24)

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

migrate = Migrate(app, db)  # Настройка миграций

# Инициализация БД и маршрутов
init_db(app, db_path=config.DB_PATH)
with app.app_context():
    populate_db()

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

# Загрузка модели
recommender = HybridRecommender(
    model_path=config.MODEL_PATH,
    annoy_index_path=config.ANNOY_INDEX_PATH,
    items_path=config.ITEMS_PATH,
    cleaned_events_path=config.CLEANED_EVENTS_PATH,
    ranker_data_path=config.RANKER_DATA_PATH
)

# Привязка модели к приложению
routes.recommender = recommender
app.recommender = recommender

# Регистрация маршрутов
app.register_blueprint(routes)

# Запуск приложения
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
