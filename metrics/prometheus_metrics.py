from prometheus_client import Counter, Gauge, Summary, Histogram

# Precision@3 — оценка точности рекомендаций
PRECISION_AT_3 = Gauge(
    'recommendation_precision_at_3',
    'Precision@3 для рекомендательной системы',
    ['user_type']
)
PRECISION_AT_3_HIST = Summary(
    'recommendation_precision_summary',
    'Распределение precision@3',
    ['user_type']
)
# HTTP-метрики
REQUEST_COUNT = Counter('app_requests_total', 'Общее количество HTTP-запросов', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Время обработки запроса', ['endpoint'])

# Метрики рекомендаций
RECOMMENDATION_REQUESTS = Counter('recommendation_requests_total', 'Запросы к рекомендательной системе')
RECOMMENDATION_TYPE = Counter('recommendation_type_count', 'Тип пользователя в рекомендациях', ['user_type'])
RECOMMENDATION_LENGTH = Histogram('recommendation_length', 'Длина списка рекомендаций')

# Метрики действий с товарами
ITEM_VIEW = Counter('item_view_total', 'Просмотры товаров')
ITEM_ADD_TO_CART = Counter('item_add_to_cart_total', 'Добавление товара в корзину')
CART_CHECKOUT = Counter('cart_checkout_total', 'Оформление заказа')

def setup_metrics():
    # Можно расширить при необходимости
    pass
