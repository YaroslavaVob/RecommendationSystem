from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from metrics.prometheus_metrics import (
    REQUEST_COUNT, REQUEST_LATENCY,
    RECOMMENDATION_REQUESTS, RECOMMENDATION_TYPE, RECOMMENDATION_LENGTH,
    ITEM_VIEW, ITEM_ADD_TO_CART, CART_CHECKOUT
)
from metrics.metrics import (
    track_recommendations, register_action_on_item, update_precision_metric
)
from collections import Counter
import logging
import time

logger = logging.getLogger(__name__)

# Создание Blueprint
routes = Blueprint('routes', __name__)

# Главная страница
@routes.route('/')
def index():
    return render_template('index.html')

# Рекомендации для пользователя
@routes.route('/recommendations', methods=['GET', 'POST'])
def recommendations_view():
    start_time = time.time()
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        if not user_id:
            flash("Пожалуйста, введите ID пользователя.", 'error')
            return redirect(url_for('routes.index'))
        try:
            user_id = int(user_id)
            # Проверка: если пользователь сменился — очищаем корзину
            prev_user_id = session.get('user_id')
            if prev_user_id != user_id:
                session.pop('cart', None)
            # Сохраняем ID пользователя в сессии
            session['user_id'] = user_id
            recommender = current_app.recommender
            recommendations = recommender.get_recommendations(user_id)

            # METRICS
            RECOMMENDATION_REQUESTS.inc()
            RECOMMENDATION_TYPE.labels(user_type=recommendations['status']).inc()
            RECOMMENDATION_LENGTH.observe(len(recommendations['recommendations']))
            REQUEST_COUNT.labels(method='POST', endpoint='/recommendations').inc()
            REQUEST_LATENCY.labels(endpoint='/recommendations').observe(time.time() - start_time)

            # Track recommendations for future precision calculation
            track_recommendations(user_id, recommendations['recommendations'])

            if not recommendations:
                flash("Рекомендации для данного пользователя не найдены.", 'warning')
            return redirect(url_for('routes.user_page', user_id=user_id))
        except ValueError:
            flash("Неверный формат ID пользователя. Введите числовой ID.", 'error')
            return redirect(url_for('routes.index'))

@routes.route('/search_item', methods=['POST'])
def search_item():
    item_id = request.form.get('item_id')
    if not item_id:
        flash("Пожалуйста, введите ID товара.", 'error')
        return redirect(url_for('routes.index'))

    try:
        item_id = int(item_id)
        return redirect(url_for('routes.item_view', item_id=item_id))
    except ValueError:
        flash("Неверный формат ID товара. Введите числовое значение.", 'error')
        return redirect(url_for('routes.index'))

# Страница товара
@routes.route('/item/<int:item_id>', methods=['GET', 'POST'])
def item_view(item_id):
    recommender = current_app.recommender
    item_row = recommender.items[recommender.items['itemid'] == item_id]
    if item_row.empty:
        flash("Товар не найден.", 'error')
        return redirect(url_for('routes.index'))

    item = item_row.iloc[0].to_dict()
    item['item_id'] = item['itemid']
    item['properties_list'] = item['property'].split()

    if request.method == 'POST':
        cart = session.get('cart', [])
        cart.append(item_id)
        session['cart'] = cart
        flash(f"Товар {item_id} добавлен в корзину.", 'success')
        ITEM_ADD_TO_CART.inc()
        register_action_on_item(item_id)  # precision@3
        return redirect(url_for('routes.cart_view'))

    ITEM_VIEW.inc()
    return render_template('item.html', item=item)

# Корзина
@routes.route('/cart', methods=['GET', 'POST'])
def cart_view():
    cart = session.get('cart', [])
    item_counts = Counter(cart)
    cart_items = [{"item_id": item_id, "count": count} for item_id, count in item_counts.items()]
    total_items = sum(item_counts.values())
    user_id = session.get('user_id')
    user = {'visitorid': user_id} if user_id else None

    if request.method == 'POST':
        session.pop('cart', None)
        flash("Ваш заказ оформлен!", 'success')
        CART_CHECKOUT.inc()
        update_precision_metric()  # precision@3
        return redirect(url_for('routes.index'))

    return render_template('cart.html', cart_items=cart_items, total_items=total_items, user=user)

# Страница пользователя
@routes.route('/user/<int:user_id>')
def user_page(user_id):
    recommender = current_app.recommender
    rec = recommender.get_recommendations(user_id)
    if not rec or not rec.get("recommendations"):
        flash("Пользователь не найден или рекомендации отсутствуют.", 'error')
        return redirect(url_for('routes.index'))

    itemids = list(dict.fromkeys(rec["recommendations"]))[:3]
    recommended_items = recommender.items[recommender.items['itemid'].isin(itemids)].to_dict(orient='records')
    user_actions = recommender.cleaned_events[recommender.cleaned_events['visitorid'] == user_id][['itemid', 'event']].drop_duplicates()
    event_map = {'view': 'просмотрен', 'addtocart': 'добавлен в корзину', 'transaction': 'куплен'}
    user_actions['event'] = user_actions['event'].map(event_map)
    actions = user_actions.to_dict(orient='records')

    return render_template('user_page.html', user={"visitorid": user_id}, actions=actions, recommended_items=recommended_items)

@routes.route('/cart/update/<int:item_id>/<action>', methods=['POST'])
def update_quantity(item_id, action):
    cart = session.get('cart', [])
    if action == 'increase':
        cart.append(item_id)
    elif action == 'decrease':
        if item_id in cart:
            cart.remove(item_id)
    session['cart'] = cart
    return redirect(url_for('routes.cart_view'))

@routes.route('/cart/remove/<int:item_id>', methods=['POST'])
def remove_item(item_id):
    cart = session.get('cart', [])
    cart = [i for i in cart if i != item_id]
    session['cart'] = cart
    flash(f"Товар {item_id} удалён из корзины.", 'info')
    return redirect(url_for('routes.cart_view'))

@routes.route('/cart/checkout', methods=['POST'])
def checkout():
    selected = request.form.getlist('selected_items')
    if not selected:
        flash("Не выбраны товары для оплаты.", 'warning')
        return redirect(url_for('routes.cart_view'))

    selected_ids = list(map(int, selected))
    cart = session.get('cart', [])
    updated_cart = [item for item in cart if item not in selected_ids]
    session['cart'] = updated_cart
    flash(f"Товары {', '.join(map(str, selected_ids))} успешно оплачены!", 'success')
    CART_CHECKOUT.inc()
    update_precision_metric()  # precision@3
    return redirect(url_for('routes.cart_view'))