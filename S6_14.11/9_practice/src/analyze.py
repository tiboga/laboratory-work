import pandas as pd


def overall_kpi(df):
    '''Сводные показатели по всем рейсам.'''
    return {
        "рейсов": len(df),
        "выручка": int(df["cost_rub"].sum()),
        "средний чек": int(round(df["cost_rub"].mean())),
        "медианный чек": int(round(df["cost_rub"].median())),
        "выручка на км": round(df["cost_rub"].sum() / df["distance_km"].sum(), 1),
        "средний вес, т": round(df["weight_t"].mean(), 1),
        "доля задержек, %": round(df["is_delayed"].mean() * 100, 1),
        "клиентов": int(df["client"].nunique()),
        "сегментов": int(df["segment"].nunique()),
    }


def kpi_by(df, column):
    '''KPI в разрезе признака: перевозчик, месяц, клиент, сегмент.'''
    result = (df.groupby(column)
              .agg(trips=("trip_id", "count"),
                   revenue=("cost_rub", "sum"),
                   avg_ticket=("cost_rub", "mean"),
                   delayed_pct=("is_delayed", lambda s: s.mean() * 100))
              .round(1)
              .sort_values("revenue", ascending=False))
    return result.reset_index()


def plan_totals(pf):
    '''Итоги выполнения плана по всем маршрутам.'''
    return {
        "рейсов по плану": int(pf["plan_trips"].sum()),
        "рейсов фактически": int(pf["trips"].sum()),
        "выполнение плана по рейсам, %": round(fact_trips / plan_trips * 100, 1),
        "выручка по плану": int(pf["plan_revenue"].sum()),
        "выручка фактически": int(pf["revenue"].sum()),
        "выполнение плана по выручке, %": round(fact_revenue / plan_revenue * 100, 1),
        "маршрутов в плане": len(pf),
    }
