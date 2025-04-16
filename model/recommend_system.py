import pandas as pd
from annoy import AnnoyIndex
from catboost import CatBoostRanker
from collections import Counter
import logging
import logging.handlers
import random
import time
import os

from utils.cache import SimilarItemsCache

if not os.path.exists('logs'):
    os.makedirs('logs')

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_file = 'logs/recommender.log'
log_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
log_handler.setFormatter(log_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

logger.info("Логирование для рекомендательной системы настроено.")


class HybridRecommender:
    def __init__(self, model_path, annoy_index_path, items_path, cleaned_events_path, ranker_data_path):
        logger.info("Инициализация гибридной рекомендательной системы...")

        self.items = pd.read_parquet(items_path).reset_index(drop=True)
        self.cleaned_events = pd.read_parquet(cleaned_events_path)
        self.ranker_data = pd.read_parquet(ranker_data_path)

        self.ranker = CatBoostRanker()
        self.ranker.load_model(model_path)

        self.annoy_index = AnnoyIndex(602, metric='angular')
        self.annoy_index.load(annoy_index_path)

        self.itemid_to_index = dict(zip(self.items['itemid'], self.items.index))
        self.index_to_itemid = dict(zip(self.items.index, self.items['itemid']))

        self.sim_cache = SimilarItemsCache(self.annoy_index, self.itemid_to_index, self.index_to_itemid)

        user_unique_items = self.cleaned_events.groupby('visitorid')['itemid'].nunique()
        filtered_users = user_unique_items[user_unique_items >= 3].index
        self.active_set = self.cleaned_events[self.cleaned_events['visitorid'].isin(filtered_users)]
        self.popular_items_active = self.active_set['itemid'].value_counts().head(2).index.tolist()
        self.active_users_set = set(filtered_users)

        logger.info(f"AnnoyIndex содержит {self.annoy_index.get_n_items()} элементов")
        logger.info("Гибридная рекомендательная система готова к работе.")

    def get_user_type(self, user_id):
        if user_id in self.active_users_set:
            return "active"

        user_events = self.cleaned_events[self.cleaned_events['visitorid'] == user_id]
        if user_events.empty:
            return "new"
        else:
            return "passive"

    def get_recommendations(self, user_id, top_n=3, alpha=0.7):
        start_time = time.time()
        logger.info(f"Запрос рекомендаций для пользователя: {user_id}")

        user_type = self.get_user_type(user_id)
        logger.info(f"Пользователь {user_id} классифицирован как {user_type}")

        if user_type == "new":
            popular_items = self.popular_items_active
            similar_item_for_popular = self.sim_cache.get_similar_items(popular_items[0], top_n=1)
            recommendations = popular_items + similar_item_for_popular

        elif user_type == "passive":
            user_items = list(set(self.cleaned_events[self.cleaned_events['visitorid'] == user_id]['itemid'].tolist()))
            random.shuffle(user_items)

            similar_items = []
            for item in user_items:
                if item in self.itemid_to_index:
                    similar_items = self.sim_cache.get_similar_items(item, top_n=2)
                    if similar_items:
                        break

            if not similar_items:
                logger.warning(f"[passive] Не удалось найти похожих товаров ни для одного из {len(user_items)} itemid.")
                popular_items = self.popular_items_active
                similar_item_for_popular = self.sim_cache.get_similar_items(popular_items[0], top_n=1)
                recommendations = popular_items + similar_item_for_popular
            else:
                recommendations = similar_items + self.popular_items_active

        elif user_type == "active":
            seen_items = set(self.cleaned_events[self.cleaned_events['visitorid'] == user_id]['itemid'].tolist())
            user_data = self.ranker_data[self.ranker_data['visitorid'] == user_id]
            user_data = user_data[~user_data['itemid'].isin(seen_items)]

            if user_data.empty:
                logger.warning(f"Пользователь {user_id} уже видел все товары.")
                recommendations = self.items['itemid'].head(top_n).tolist()
            else:
                features = [col for col in user_data.columns if col not in ['label', 'visitorid', 'itemid']]
                user_data['score'] = self.ranker.predict(user_data[features])
                ranker_items = user_data.sort_values('score', ascending=False)['itemid'].head(top_n).tolist()

                content_recommendations = []
                for rec_item in ranker_items:
                    content_recommendations.extend(self.sim_cache.get_similar_items(rec_item, top_n=2))

                weighted_scores = Counter()
                for i, item in enumerate(ranker_items):
                    weighted_scores[item] += alpha * (top_n - i)
                for i, item in enumerate(content_recommendations):
                    weighted_scores[item] += (1 - alpha) * (top_n - i)

                recommendations = [item for item, _ in weighted_scores.most_common()]

        else:
            recommendations = []

        # Финальная обработка: убираем дубликаты и обрезаем
        unique_recommendations = list(dict.fromkeys(recommendations))[:top_n]
        logger.info(f"Итоговые рекомендации (len={len(unique_recommendations)}): {unique_recommendations}")
        logger.info(f"Рекомендации сгенерированы за {time.time() - start_time:.2f} сек.")

        return {
            "status": user_type,
            "recommendations": unique_recommendations
        }