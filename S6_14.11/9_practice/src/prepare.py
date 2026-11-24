import pandas as pd


def prepare_trips(raw):
    '''Добавляет признаки месяца и задержки, убирает дубли рейсов.'''
    report = {"строк получено": len(raw)}
    df = raw.copy()

    df = df.drop_duplicates(subset=["trip_id"], keep="first")
    report["удалено дублей рейсов"] = report["строк получено"] - len(df)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    report["дат не распознано"] = int(df["date"].isna().sum())

    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["is_delayed"] = df["delay_h"] > 0
    df["cost_per_km"] = (df["cost_rub"] / df["distance_km"]).round(2)

    report["строк осталось"] = len(df)
    report["доля потерь, %"] = round((1 - len(df) / report["строк получено"]) * 100, 1)
    return df.reset_index(drop=True), report


def prepare_carriers(carriers):
    '''Убирает дубли в справочнике перевозчиков.'''
    report = {"строк в справочнике перевозчиков": len(carriers)}
    unique = carriers.drop_duplicates(subset="carrier").reset_index(drop=True)
    report["удалено дублей в справочнике"] = len(carriers) - len(unique)
    return unique, report


def merge_trips(trips, carriers, clients):
    '''Присоединяет справочники к рейсам с проверкой уникальности ключей.'''
    report = {}

    full = trips.merge(carriers, on="carrier", how="left", validate="m:1")
    report["рейсов после merge с перевозчиками"] = len(full)

    full = full.merge(clients, on="client", how="left", validate="m:1")
    report["рейсов после merge с клиентами"] = len(full)

    unknown = full["rating"].isna()
    report["рейсов без перевозчика в справочнике"] = int(unknown.sum())
    report["незнакомые перевозчики"] = sorted(full.loc[unknown, "carrier"].unique().tolist())
    report["рейсов без клиента в справочнике"] = int(full["segment"].isna().sum())

    check = (trips[["client"]].drop_duplicates()
             .merge(clients[["client"]], on="client", how="outer", indicator=True))
    report["клиенты без рейсов"] = sorted(
        check.loc[check["_merge"] == "right_only", "client"].tolist())

    return full, report


def build_plan_fact(full, plan, month):
    '''Сопоставляет план и факт по маршрутам за указанный месяц.'''
    plan = plan[plan["month"] == month].copy()

    fact = (full[full["month"] == month]
            .groupby("route")
            .agg(trips=("trip_id", "size"),
                 revenue=("cost_rub", "sum"))
            .reset_index())

    report = {"строк в плане": len(plan), "маршрутов с фактом": len(fact)}

    pf = plan.merge(fact, on="route", how="left", validate="m:1")
    report["строк после соединения"] = len(pf)
    report["маршрутов без факта"] = int(pf["trips"].isna().sum())

    pf["trips"] = pf["trips"].fillna(0).astype(int)
    pf["revenue"] = pf["revenue"].fillna(0).astype(int)
    pf["trips_done_pct"] = (pf["trips"] / pf["plan_trips"] * 100).round(1)
    pf["revenue_done_pct"] = (pf["revenue"] / pf["plan_revenue"] * 100).round(1)
    pf = pf.sort_values("revenue_done_pct", ascending=False).reset_index(drop=True)
    return pf, report
