from db.db import db  # Импортируем db, чтобы использовать его для создания моделей

# Таблица пользователей
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)  # Идентификатор пользователя
    visitorid = db.Column(db.Integer, unique=True, nullable=False)  # Идентификатор пользователя (visitorid)
    
    actions = db.relationship('Action', backref='user', lazy=True)  # Связь с действиями пользователя (1 ко многим)

# Таблица товаров
class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)  # Идентификатор товара
    itemid = db.Column(db.Integer, unique=True, nullable=False)  # Идентификатор товара (itemid)
    properties = db.Column(db.Text, nullable=False)  # Свойства товара (поля из items.parquet)
    value_length = db.Column(db.Integer, nullable=False)  # Свойство value_length
    depth = db.Column(db.Float, nullable=False)  # Свойство depth

# Таблица действий пользователей с товарами
class Action(db.Model):
    __tablename__ = 'actions'
    
    id = db.Column(db.Integer, primary_key=True)  # Идентификатор действия
    timestamp = db.Column(db.DateTime, nullable=False)  # Время события (timestamp)
    event = db.Column(db.String(50), nullable=False)  # Тип события (view, addtocart, purchase)
    itemid = db.Column(db.Integer, db.ForeignKey('items.itemid'), nullable=False)  # Идентификатор товара
    visitorid = db.Column(db.Integer, db.ForeignKey('users.visitorid'), nullable=False)  # Идентификатор пользователя
    dayofweek = db.Column(db.Integer, nullable=False)  # День недели
    is_weekend = db.Column(db.Boolean, nullable=False)  # Будний ли день
    is_holiday = db.Column(db.Boolean, nullable=False)  # Праздничный ли день
    hour = db.Column(db.Integer, nullable=False)  # Час события
    view_count = db.Column(db.Integer, nullable=False)  # Количество просмотров
    addtocart_count = db.Column(db.Integer, nullable=False)  # Количество добавлений в корзину
    purchase_count = db.Column(db.Integer, nullable=False)  # Количество покупок
    conversion = db.Column(db.Float, nullable=False)  # Конверсия
    avg_time_view = db.Column(db.Float, nullable=False)  # Среднее время просмотра
    avg_time_addtocart = db.Column(db.Float, nullable=False)  # Среднее время добавления в корзину
    avg_time_transaction = db.Column(db.Float, nullable=False)  # Среднее время транзакции
    total_events = db.Column(db.Integer, nullable=False)  # Общее количество событий
    items_count = db.Column(db.Integer, nullable=False)  # Количество товаров
    purchases = db.Column(db.Integer, nullable=False)  # Количество покупок
    session = db.Column(db.Float, nullable=False)  # Сессия
    itemevents_by_visitor = db.Column(db.Integer, nullable=False)  # События товара для пользователя
    itemviews_before_purchase = db.Column(db.Float, nullable=False)  # Просмотры товара до покупки
    time_to_purchase = db.Column(db.Float, nullable=False)  # Время до покупки

# Таблица для данных из df_ranker (для модели CatBoost)
class RankerData(db.Model):
    __tablename__ = 'ranker_data'
    
    id = db.Column(db.Integer, primary_key=True)  # Идентификатор записи
    visitorid = db.Column(db.Integer, nullable=False)  # Идентификатор пользователя (visitorid)
    itemid = db.Column(db.Integer, db.ForeignKey('items.itemid'), nullable=False)  # Идентификатор товара
    dayofweek = db.Column(db.Integer, nullable=False)  # День недели
    is_weekend = db.Column(db.Boolean, nullable=False)  # Будний ли день
    is_holiday = db.Column(db.Boolean, nullable=False)  # Праздничный ли день
    hour = db.Column(db.Integer, nullable=False)  # Час события
    view_count = db.Column(db.Integer, nullable=False)  # Количество просмотров
    addtocart_count = db.Column(db.Integer, nullable=False)  # Количество добавлений в корзину
    purchase_count = db.Column(db.Integer, nullable=False)  # Количество покупок
    conversion = db.Column(db.Float, nullable=False)  # Конверсия
    avg_time_view = db.Column(db.Float, nullable=False)  # Среднее время просмотра
    avg_time_addtocart = db.Column(db.Float, nullable=False)  # Среднее время добавления в корзину
    avg_time_transaction = db.Column(db.Float, nullable=False)  # Среднее время транзакции
    total_events = db.Column(db.Integer, nullable=False)  # Общее количество событий
    items_count = db.Column(db.Integer, nullable=False)  # Количество товаров
    purchases = db.Column(db.Integer, nullable=False)  # Количество покупок
    session = db.Column(db.Float, nullable=False)  # Сессия
    itemevents_by_visitor = db.Column(db.Integer, nullable=False)  # События товара для пользователя
    itemviews_before_purchase = db.Column(db.Float, nullable=False)  # Просмотры товара до покупки
    time_to_purchase = db.Column(db.Float, nullable=False)  # Время до покупки
    label = db.Column(db.Integer, nullable=False)  # Целевая переменная для обучения модели
