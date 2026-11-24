from pathlib import Path

import pandas as pd


def load_trips(raw_dir, pattern="trips_*.csv"):
    '''Читает все месячные выгрузки по рейсам и склеивает их в одну таблицу.'''
    files = sorted(Path(raw_dir).glob(pattern))
    if not files:
        raise FileNotFoundError(f"в {raw_dir} нет файлов по шаблону {pattern}")

    frames = []
    for path in files:
        part = pd.read_csv(path, parse_dates=["date"])
        part["source_file"] = path.name
        frames.append(part)
        print(f"    {path.name}: {len(part)} строк")

    return pd.concat(frames, ignore_index=True)


def load_carriers(raw_dir, filename="carriers.csv"):
    '''Читает справочник перевозчиков.'''
    return pd.read_csv(Path(raw_dir) / filename)


def load_clients(raw_dir, filename="clients.csv"):
    '''Читает справочник клиентов.'''
    return pd.read_csv(Path(raw_dir) / filename)


def load_plan(raw_dir, filename="plan.csv"):
    '''Читает план по маршрутам.'''
    return pd.read_csv(Path(raw_dir) / filename)
