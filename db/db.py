import os
import logging
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

# Создание объекта db
db = SQLAlchemy()

def init_db(app, db_path):
    # Настройка логирования
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename='logs/init_db.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Убедитесь, что каталог для базы данных существует
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Настройка пути к базе данных
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Инициализация SQLAlchemy
    db.init_app(app)

    # Создание всех таблиц, если они еще не существуют
    try:
        with app.app_context():
            db.create_all()

        logging.info("✅ Таблицы успешно созданы.")
        
        success_msg = "[+] База данных успешно инициализирована."
        print(success_msg)
        logging.info(success_msg)

    except Exception as e:
        error_msg = f"❌ Произошла ошибка при инициализации базы данных: {e}"
        print(error_msg)
        logging.exception(error_msg)
    
    finally:
        if 'db.session' in locals():
            db.session.remove()
            logging.info("🔒 Соединение с БД закрыто.")

def populate_db():
    from db.users import User, Item, Action, RankerData
    import pandas as pd
    from datetime import datetime

    try:
        # Проверка: если таблицы не пустые — не загружаем данные
        if db.session.query(User).first() or db.session.query(Item).first() or db.session.query(RankerData).first():
            print("✅ Таблицы уже заполнены, загрузка данных пропущена.")
            return

        # Загружаем данные
        users_df = pd.read_parquet("model/data/cleaned_events.parquet").head(10000)
        items_df = pd.read_parquet("model/data/items.parquet").head(10000)
        ranker_df = pd.read_parquet("model/data/df_ranker.parquet").head(10000)

        # Загружаем пользователей
        unique_users = users_df['visitorid'].unique()
        db.session.bulk_save_objects([User(visitorid=int(uid)) for uid in unique_users])

        # Загружаем товары
        db.session.bulk_save_objects([
            Item(
                itemid=row['itemid'],
                properties=row['property'],
                value_length=row['value_length'],
                depth=row['depth']
            ) for _, row in items_df.iterrows()
        ])

        # Загружаем действия
        db.session.bulk_save_objects([
            Action(
                timestamp=pd.to_datetime(row['timestamp'], unit='ms') if 'timestamp' in row else datetime.now(),
                event=row['event'],
                itemid=row['itemid'],
                visitorid=row['visitorid'],
                dayofweek=row.get('dayofweek', 0),
                is_weekend=row.get('is_weekend', False),
                is_holiday=row.get('is_holiday', False),
                hour=row.get('hour', 0),
                view_count=row.get('view_count', 0),
                addtocart_count=row.get('addtocart_count', 0),
                purchase_count=row.get('purchase_count', 0),
                conversion=row.get('conversion', 0.0),
                avg_time_view=row.get('avg_time_view', 0.0),
                avg_time_addtocart=row.get('avg_time_addtocart', 0.0),
                avg_time_transaction=row.get('avg_time_transaction', 0.0),
                total_events=row.get('total_events', 0),
                items_count=row.get('items_count', 0),
                purchases=row.get('purchases', 0),
                session=row.get('session', 0.0),
                itemevents_by_visitor=row.get('itemevents_by_visitor', 0),
                itemviews_before_purchase=row.get('itemviews_before_purchase', 0.0),
                time_to_purchase=row.get('time_to_purchase', 0.0)
            ) for _, row in users_df.iterrows()
        ])

        # Загружаем данные для модели
        db.session.bulk_save_objects([
            RankerData(**row) for row in ranker_df.to_dict(orient="records")
        ])

        db.session.commit()
        print("[+] Данные успешно загружены в БД.")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка при загрузке данных в БД: {e}")

# Функция для извлечения данных по запросу из базы данных (например, для конкретного пользователя)
def get_user_data(user_id):
    # Импортируем db внутри функции, чтобы избежать циклического импорта
    from db.users import User, Action

    # Здесь мы извлекаем только нужные данные для конкретного пользователя из базы
    try:
        user = db.session.query(User).filter_by(visitorid=user_id).first()
        if not user:
            raise ValueError(f"Пользователь с ID {user_id} не найден.")

        # Здесь главное исправление:
        actions = db.session.query(Action).filter_by(visitorid=user.visitorid).all()

        return user, actions

    except Exception as e:
        print(f"Ошибка при извлечении данных: {e}")
        return None, None