from functools import lru_cache
import logging

class SimilarItemsCache:
    def __init__(self, annoy_index, itemid_to_index, index_to_itemid):
        self.annoy_index = annoy_index
        self.itemid_to_index = itemid_to_index
        self.index_to_itemid = index_to_itemid

    @lru_cache(maxsize=10000)
    def get_similar_items(self, itemid, top_n=3):
        try:
            if itemid not in self.itemid_to_index:
                logging.warning(f"itemid {itemid} не найден в itemid_to_index.")
                return []
            idx = self.itemid_to_index[itemid]
            if idx >= self.annoy_index.get_n_items():
                logging.error(f"Annoy index out of bounds: idx={idx}, max={self.annoy_index.get_n_items()} (itemid={itemid})")
                return []
            neighbors = self.annoy_index.get_nns_by_item(idx, top_n + 1)
            logging.info(f"Поиск похожих для itemid={itemid}, index={idx} → соседи={neighbors}")
            return [self.index_to_itemid[i] for i in neighbors if i != idx]
        except Exception as e:
            logging.exception(f"Ошибка при поиске похожих товаров для itemid={itemid}")
            return []

    def get_similar_by_vector(self, vector, top_n=3):
        try:
            neighbors = self.annoy_index.get_nns_by_vector(vector, top_n)
            logging.info(f"Поиск похожих по вектору → соседи={neighbors}")
            return [self.index_to_itemid[i] for i in neighbors]
        except Exception as e:
            logging.exception("Ошибка при поиске похожих товаров по вектору")
            return []
