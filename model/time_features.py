import holidays
import pandas as pd
def generate_time_features(df, col='timestamp', holidays_year=2015):
    df['dayofmonth'] = df[col].dt.day    # день месяца
    df['month'] = df[col].dt.month       # месяц
    df['dayofweek'] = df[col].dt.dayofweek # день недели как порядковый номер
    df['dayofweek_str'] = df[col].dt.day_name() # название дня недели
    df['week_of_year'] = df[col].dt.isocalendar().week # номер недели в году
    
    df['is_weekend'] = df['dayofweek'].isin([5, 6])  # выходные дни (суббота-воскресенье)
    russian_holidays = holidays.RU(years=holidays_year)  # праздники в 2015 году
    df['is_holiday'] = df[col].dt.date.isin(russian_holidays.keys()) # праздничные дни
    
    df['hour'] = df[col].dt.hour # час дня
    def part_of_day(hour):
        if 6 <= hour < 12:
            return 'Morning'
        elif 12 <= hour < 18:
            return 'Afternoon'
        elif 18 <= hour < 22:
            return 'Evening'
        else:
            return 'Night'
    df['part_of_day'] = df['hour'].apply(part_of_day) # группировка часов по времени дня
    
    '''
    Разница во времени между текущим и предыдущим событием. Это может помочь выявить, как часто происходят события.
    '''
    df['time_diff_ms'] = df[col].diff().dt.total_seconds()*1000 # разница в миллисекундах
    
    return df