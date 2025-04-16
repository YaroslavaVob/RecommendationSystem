import numpy as np

def optimize_memory_usage(df):
    """Функция для оптимизации использования памяти в DataFrame."""
    
    # Сохраняем начальный размер памяти
    initial_memory = df.memory_usage(deep=True).sum()
    print(f"Начальный размер памяти: {initial_memory / (1024 ** 2):.2f} MB")
    
    # Проходим по всем столбцам DataFrame
    for col in df.columns:
        col_type = df[col].dtype
        
        # Преобразование object, str в category
        if col_type == 'object':
            df[col] = df[col].astype('category')
        elif col_type == 'string':
            df[col] = df[col].astype('category')
        
        # Уменьшение числовых типов
        elif col_type in ['int64', 'int32', 'int16', 'int8']:
            # Если все значения положительные, пробуем преобразовать сразу в uint
            if (df[col] >= 0).all():
                # Пробуем уменьшить до uint8, если возможно
                if df[col].max() <= np.iinfo(np.uint8).max:
                    df[col] = df[col].astype(np.uint8)
                # Пробуем уменьшить до uint16, если возможно
                elif df[col].max() <= np.iinfo(np.uint16).max:
                    df[col] = df[col].astype(np.uint16)
                # Пробуем уменьшить до uint32, если возможно
                elif df[col].max() <= np.iinfo(np.uint32).max:
                    df[col] = df[col].astype(np.uint32)
            else:
                # Если есть отрицательные значения, пробуем уменьшить до меньшего знакового типа
                if df[col].min() >= np.iinfo(np.int8).min and df[col].max() <= np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif df[col].min() >= np.iinfo(np.int16).min and df[col].max() <= np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif df[col].min() >= np.iinfo(np.int32).min and df[col].max() <= np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
        
        elif col_type in ['uint32', 'uint16']:
            # Уменьшение uint типов, если возможно
            if df[col].max() <= np.iinfo(np.uint8).max:
                df[col] = df[col].astype(np.uint8)
            elif df[col].max() <= np.iinfo(np.uint16).max:
                df[col] = df[col].astype(np.uint16)
        
        elif col_type in ['float64', 'float32']:
            # Пробуем уменьшить до float16, если возможно
            if df[col].min() >= np.finfo(np.float16).min and df[col].max() <= np.finfo(np.float16).max:
                df[col] = df[col].astype(np.float16)
            # Пробуем уменьшить др float32
            elif df[col].min() >= np.finfo(np.float32).min and df[col].max() <= np.finfo(np.float32).max:
                df[col] = df[col].astype(np.float32)


    # Сохраняем конечный размер памяти
    final_memory = df.memory_usage(deep=True).sum()
    print(f"Конечный размер памяти: {final_memory / (1024 ** 2):.2f} MB")
    print(f"Экономия памяти: {(initial_memory - final_memory) / (1024 ** 2):.2f} MB")
    
    return df