from flask import session, current_app
from metrics.prometheus_metrics import PRECISION_AT_3, PRECISION_AT_3_HIST

def track_recommendations(user_id, recommended_items):
    """
    Сохраняет последние рекомендации в сессии пользователя.
    """
    session['last_recommendations'] = {
        'user_id': user_id,
        'items': recommended_items,
        'hits': 0
    }

def register_action_on_item(item_id):
    """
    Отмечает, что пользователь совершил действие с рекомендованным товаром (например, добавил в корзину).
    Если товар входит в последние рекомендации — увеличиваем счётчик совпадений.
    """
    rec = session.get('last_recommendations', {})
    if rec and item_id in rec.get('items', []):
        rec['hits'] = rec.get('hits', 0) + 1
        session['last_recommendations'] = rec

def update_precision_metric():
    """
    Вызывается при оформлении покупки.
    Вычисляет precision@3 и отправляет его в Prometheus (Gauge и Summary).
    """
    rec = session.get('last_recommendations', {})
    if not rec:
        return

    user_id = rec.get('user_id')
    recommended = rec.get('items', [])
    hits = rec.get('hits', 0)

    if user_id and recommended:
        user_type = current_app.recommender.get_user_type(user_id)
        precision = hits / min(len(recommended), 3)

        # Отправка метрик
        PRECISION_AT_3.labels(user_type=user_type).set(precision)
        PRECISION_AT_3_HIST.labels(user_type=user_type).observe(precision)

    session.pop('last_recommendations', None)