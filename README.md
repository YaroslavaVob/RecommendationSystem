## Recommendation System for E-commerce
[![Docker Build](https://img.shields.io/badge/docker-ready-blue)](https://hub.docker.com/)
[![Flask](https://img.shields.io/badge/flask-app-green)]()
[![Prometheus](https://img.shields.io/badge/metrics-monitored-orange)]()

Гибридная рекомендательная система, реализованная на Flask с мониторингом метрик через Prometheus и Grafana.\
Система объединяет модели CatBoostRanker и item-based рекомендации (Annoy).

Система классифицирует пользователей на типы: активный, пассивный или новый.\
Рекомендации формируются в зависимости от типа пользователя и максимально персонализируются, основываясь на истории взаимодействия пользователя с товарами:
1) ***Новый пользователь*** получает следующий список рекомендаций:\
два самых популярных товара среди активной группы пользователей и один товар от item-based модели, похожий на самый популярный.
2) ***Пассивному пользователю*** (1-3 действия на платформе):\
контентная модель находит два товара, похожих на рандомно выбранный товар из его истории, + один самый популярный товар среди активной группы.
3) ***Активный пользователь*** (4 и более действия на платформе):\
ранжировщик предсказывает такому пользователю три товара (исключая товары, с которыми пользователь уже взаимодействовал), к каждому предсказанному ranker товару item-based модель находит два похожих товара.\
 Далее все эти товары умножаются на веса (вес товаров контентной модели регулируется, установлен 0.7) и выбираются три товара с максимальным весом. Тем самым добавляется разнообразие в историю и продвигаются новые и менее популярные товары.

**Преимущества гибридной рекомендательной системы**:
1) Поддержка пользователей с разным уровнем активности;
2) Сбалансированное сочетание персонализированных и популярных рекомендаций.

**Функлионал рекомендательной системы**:
1) Рекомендации товаров по пользовательскому ID
2) Учет разных типов пользователей (новый, пассивный, активный)
3) Обработка пользовательских действий: просмотр, добавление в корзину, покупка
4) Метрики качества и конверсии, передающиеся в Prometheus
5) Dashboard Grafana для мониторинга

🧱 **Структура приложения**

```
project/
├── app.py                        # инициализация приложения Flask
├── routes.py                     # маршруты веб-сервиса
├── config.py                     # настройка путей
├── Dockerfile                    
├── docker-compose.yml            
├── requirements.txt              # необходимые пакеты 
├── README.md                     # инструкция по запуску
├── prometheus/
│   └── prometheus.yml            # конфигурация Prometheus
├── grafana/
│   ├── dashboards/
│   │   └── grafana_dashboard.json  # dashboard настройка
│   └── provisioning/
│       └── dashboards/
│           └── dashboards.yml      # автоимпорт дашборда Grafana
├── db/
│   └── db.py                       # заполнение таблиц базы данных первыми 10,000 объектами из источников
│   └── user.py                     # создание таблиц базы данных
├── metrics/
│   └── prometheus_metrics.py       # инициализация метрик
│   └── metrics.py                  # аккумуляция метрик
├── model/
│   └── data
│   │   └── cleaned_events.parquet       # подготовленные данные о пользователях и их действиях с товарами
│   │   └── cleaned_properties.parquet   # подготовленные данные о товарах и их свойствах
│   │   └── df_ranker.parquet            # преобразованные данные для модели ranker
│   │   └── items.parquet                # преобразованные данные для item-based модели
│   └── Cleaning Data, EDA, Feature Engineering.ipynb      # очистка, подготовка данных, генерация фичей
│   └── Modeling of recommendation system.ipynb            # построение различных моделей, сравнение
│   └── item_index.ann              # сохраненный индексатор по поиску ближайших товаров
│   └── catboost_ranker.bin         # обученнная модель CatBoostRanker
│   └── optimize_memory_usege.py    # функция оптимизации использования памяти за счет преобразования типов данных
│   └── time_features.py            # функция генерации временных признаков
│   └── recommend_system.py         # гибридная рекомендательная система
├── static/
│   └── styles.css                  
├── templates/
│   └── index.html                  # главная страница (рекомендации пользователю по id и поиск товара по id)
│   └── user_page.html              # товары, с которыми пользователь взаимодействовал
│   └── item.html                   # действия с товаром
│   └── cart.html                   # корзина
```

#### [Ссылка на репозиторий приложения на Docker Hub](https://hub.docker.com/r/yroslava11/recommender-app)

#### 1. Для скачивания docker image:
**docker pull yroslava11/recommender-app:v.1.0**

#### 2. Запуск контейнера:

**docker-compose up**

#### 3. Открытие в браузере:

- [http://localhost:5000](http://localhost:5000) — Flask-приложение
- [http://localhost:9090](http://localhost:9090) — Prometheus (мониторинг метрик)
- [http://localhost:3001](http://localhost:3001) — Grafana Dashboard (admin/admin)

В Settings Grafana  → Data Sources : проверьте источник данных Prometheus: http://prometheus:9090, дашборд со всеми метриками для мониторинга импортируется автоматически.

**Весомые файлы**, не загруженные в данный репозиторий: 
* model/catboost_ranker.bin
* model/item_index.ann
* model/data/df_ranker.parguet
* model/data/items.parquet
* model/data/cleaned_events.parquet
* model/data/cleaned_properties.parquet\
доступны на [Google Drive](https://drive.google.com/drive/folders/1HaG1y6LTxciY4QzDPO5aFcvN537w4zIF?usp=sharing)

Проект выполнен в рамках диплома по профессии Data Science апрель 2025.

Автор: Yaroslava Vobsharkyan \
Для связи: [Telegram](https://t.me/YaraVF)
