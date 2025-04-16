import sys
import os
sys.path.append(os.path.abspath("E:/Skillfactory_2/DIPLOMA"))

import pandas as pd
import numpy as np
import dask.dataframe as dd 
from model.optimize_memory_usage import optimize_memory_usage
from model.time_features import generate_time_features

def preprocess_data():
    '''
    Выполняет полную предобработку данных:
    - Загружает: events.csv, item_properties_part1.csv, item_properties_part2.csv, category_tree.csv
    - Вычисляет признаки взаимодействия пользователей с товарами, временные и категориальные признаки
    - Сохраняет два parquet-файла:
        - users_items.parquet — данные событий пользователей с признаками
        - items_properties.parquet — агрегированные свойства товаров
        - data_ranker.parquet — подготовленные данные для обучения CatBoost Ranker
    '''
    with open('model/data/events.csv', 'r') as f:  
        users_items = pd.read_csv(f)
    users_items = optimize_memory_usage(users_items)

    users_items.rename(columns={'transactionid': 'transaction'}, inplace=True)
    users_items['transaction'] = users_items['transaction'].apply(lambda x: 0 if pd.isna(x) else 1).astype('uint8')
    users_items.drop_duplicates(inplace=True)
    users_items['timestamp'] = pd.to_datetime(users_items['timestamp'], unit='ms')
    users_items = users_items.sort_values(by='timestamp').reset_index(drop=True)
    
    generate_time_features(users_items)
    users_items = optimize_memory_usage(users_items)

    # Вычисляем item-based признаки: число просмотров, добавлений в корзину и покупок, а также конверсию
    item_factors = users_items.groupby('itemid').agg(
        view_count=('event', lambda x: (x == 'view').count()),
        addtocart_count=('event', lambda x: (x == 'addtocart').count()),
        purchase_count=('transaction', 'sum')).reset_index()
    item_factors['conversion'] = item_factors['purchase_count'] / item_factors['view_count'].replace(0, np.nan)
    item_factors['conversion'] = item_factors['conversion'].fillna(0)
    users_items = users_items.merge(item_factors, on='itemid', how='left')

    # Генерация средних временных признаков по каждому типу события (view, addtocart, transaction)
    lst_df = []
    event_types = ['view', 'addtocart', 'transaction']
    for e in event_types:
        df = users_items[users_items['event'] == e].copy()
        df.sort_values(by=['itemid', 'timestamp'], inplace=True)
        df['time_diff'] = df.groupby('itemid')['timestamp'].diff()
        avg_time_event = df.groupby('itemid')['time_diff'].mean()
        avg_time_event = avg_time_event.fillna(pd.Timedelta(seconds=0)).dt.total_seconds() / 3600
        avg_time_event = avg_time_event.round(2).rename(f'avg_time_{e}')
        lst_df.append(avg_time_event)

    first_seen = users_items.groupby('itemid')['timestamp'].min().rename("first_seen")
    last_seen = users_items.groupby('itemid')['timestamp'].max().rename("last_seen")

    # Генерация признаков времени для itemid: первое и последнее появление + среднее время между событиями
    time_item_factors = pd.concat([first_seen, last_seen] + lst_df, axis=1).fillna(0.0)
    users_items = users_items.merge(time_item_factors, on="itemid", how="left")

    # Вычисляем признаки активности и лояльности пользователей:
    # - общее количество событий, количество уникальных товаров, количество покупок
    total_events = users_items.groupby('visitorid').size().rename('total_events')
    items_count = users_items.groupby('visitorid')['itemid'].nunique().rename('items_count')
    purchases = users_items.groupby('visitorid')['transaction'].sum().rename('purchases')
    user_factors = pd.concat([total_events, items_count, purchases], axis=1).reset_index()
    users_items = users_items.merge(user_factors, on="visitorid", how="left")

    events_sorted = users_items.sort_values(by=['visitorid', 'timestamp'])
    events_sorted['session_diff'] = events_sorted.groupby('visitorid')['timestamp'].diff()
    session_avg = events_sorted.groupby('visitorid')['session_diff'].mean()
    session_avg = session_avg.fillna(pd.Timedelta(seconds=0)).dt.total_seconds() / 3600
    session_avg = session_avg.round(2)
    users_items = users_items.merge(session_avg.rename('session'), on='visitorid', how='left')

    # Генерация признаков пользовательского поведения по связке (user_id, item_id):
    # - сколько раз пользователь взаимодействовал с товаром
    # - сколько раз просматривал до покупки
    # - сколько времени прошло до покупки
    item_events = users_items.groupby(['visitorid', 'itemid'])['event'].count().rename('itemevents_by_visitor')
    views = users_items[users_items['event'] == 'view']
    views_before_purchase = views.groupby(['visitorid', 'itemid'])['event'].count().rename('itemviews_before_purchase')
    first_view = views.groupby(['visitorid', 'itemid'])['timestamp'].min().rename('first_view')
    time_purchase = users_items[users_items['event'] == 'transaction'].groupby(['visitorid', 'itemid'])['timestamp'].max().rename('time_purchase')
    time_to_purchase = pd.concat([first_view, time_purchase], axis=1)
    time_to_purchase['time_to_purchase'] = (time_to_purchase['time_purchase'] - time_to_purchase['first_view'])\
                                              .fillna(pd.Timedelta(seconds=0)).dt.total_seconds() / 3600
    time_to_purchase['time_to_purchase'] = time_to_purchase['time_to_purchase'].round(2)
    user_item_factors = pd.concat([item_events, views_before_purchase, time_to_purchase], axis=1).fillna(0).reset_index()
    users_items = users_items.merge(
        user_item_factors.drop(['first_view', 'time_purchase'], axis=1, errors='ignore'),
        on=['visitorid', 'itemid'],
        how='left'
    )
    users_items = optimize_memory_usage(users_items)
    users_items = users_items[['timestamp', 'visitorid', 'event', 'itemid', 'dayofweek', 'is_weekend', 'is_holiday',
                               'hour', 'view_count', 'addtocart_count', 'purchase_count', 'conversion', 'first_seen', 
                               'last_seen', 'avg_time_view', 'avg_time_addtocart', 'avg_time_transaction', 'total_events',
                               'items_count', 'purchases', 'session', 'itemevents_by_visitor',
                               'itemviews_before_purchase', 'time_to_purchase']].copy()

    users_items.to_parquet('model/data/cleaned_events.parquet')

    # Отфильтровываем пользователей, взаимодействовавших минимум с 4 товарами
    # Это важно для обучения ранжирующей модели
    user_unique_items = users_items.groupby('visitorid')['itemid'].nunique()
    min_unique_items = 4
    filtered_users = user_unique_items[user_unique_items >= min_unique_items].index
    filtered_df = users_items[users_items['visitorid'].isin(filtered_users)].copy()
    event_priority = {'view': 0, 'addtocart': 1, 'transaction': 2}
    filtered_df.loc[:, 'label'] = filtered_df['event'].map(event_priority)
    filtered_df = filtered_df.drop(columns=['first_seen', 'last_seen', 'event'], errors='ignore')
    filtered_df = filtered_df.sort_values('timestamp')
    filtered_df = filtered_df.drop(columns=['timestamp'])
    filtered_df.to_parquet('model/data/df_ranker.parquet')

    dtypes = {
        "timestamp": "uint64",
        "itemid": "uint32"
    }
    with open("model/data/item_properties_part1.csv", 'r') as f:    
        properties1 = pd.read_csv(f, dtype=dtypes)
    with open("model/data/item_properties_part2.csv", 'r') as f:    
        properties2 = pd.read_csv(f, dtype=dtypes)
    properties = pd.concat([properties1, properties2], axis=0, ignore_index=True)
    properties = optimize_memory_usage(properties)
    properties["timestamp"] = pd.to_datetime(properties["timestamp"], unit="ms")
    properties['property'] = properties['property'].astype(str).replace({'categoryid': '226', 'available': '474'})
    properties['property'] = properties['property'].astype('uint16')
    properties['value'] = properties['value'].astype('string')
    properties['value'] = properties['value'].str.replace('n', '', regex=False).str.replace('Ifiity', '', regex=False).str.strip()
    properties['value'] = properties['value'].astype('category')
    ddf = dd.from_pandas(properties, npartitions=10)
    properties = ddf.sort_values('timestamp').compute()
    property_count = properties.groupby('itemid')['property'].nunique().rename('property_count')
    properties = properties.merge(property_count, on='itemid', how='left')

    with open("model/data/category_tree.csv", 'r') as f:      
        tree = pd.read_csv(f)
    tree['parentid'] = tree['parentid'].fillna(-1).astype(int)
    category_dict = dict(zip(tree['categoryid'], tree['parentid']))

    def get_depth(category_id, depth_cache={}):
        if category_id in depth_cache:
            return depth_cache[category_id]
        if category_id == -1:
            return 0
        parent_id = category_dict.get(category_id, -1)
        depth_cache[category_id] = 1 + get_depth(parent_id, depth_cache)
        return depth_cache[category_id]

    tree['depth'] = tree['categoryid'].map(lambda x: get_depth(x))
    tree['categoryid'] = tree['categoryid'].astype('uint16')
    properties_df = properties.merge(tree[['categoryid', 'depth']], 
                                     left_on='property', right_on='categoryid', 
                                     how='left')
    properties_df.drop(columns=['categoryid'], inplace=True)
    properties_df['depth'] = properties_df['depth'].fillna(properties_df['depth'].median()).astype('uint8')
    properties_df = optimize_memory_usage(properties_df)
    items = properties_df.drop_duplicates(subset=['itemid', 'property']).copy()
    items['value'] = items['value'].apply(lambda x: str(x))
    items['value_length'] = items['value'].apply(lambda x: len(x.split()))
    # Финальная агрегация по itemid:
    # - объединяем уникальные свойства
    # - суммируем длину значений
    # - берём медиану глубины категории
    grouped_items = items.groupby('itemid').agg({
        'property': lambda x: ' '.join(str(p) for p in set(x)),
        'value_length': 'sum',
        'depth': 'median'
    }).reset_index()
    grouped_items.to_parquet('model/data/items.parquet')


if __name__ == '__main__':
    preprocess_data()