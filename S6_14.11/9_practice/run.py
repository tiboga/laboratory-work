# -*- coding: utf-8 -*-
'''Точка входа: запускает весь анализ от сырых данных до отчёта.'''
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas

import config
from src.load import load_trips, load_carriers, load_clients, load_plan
from src.prepare import prepare_trips, prepare_carriers, merge_trips, build_plan_fact
from src.analyze import overall_kpi, kpi_by, plan_totals
from src.visualize import plot_revenue_by_month, plot_plan_vs_fact


def df_to_markdown(df):
    '''Превращает таблицу в markdown без внешних зависимостей.'''
    header = "| " + " | ".join(str(c) for c in df.columns) + " |"
    sep = "|" + "---|" * len(df.columns)
    rows = ["| " + " | ".join(str(v) for v in row) + " |"
            for row in df.itertuples(index=False)]
    return chr(10).join([header, sep] + rows)


def build_report(kpi, quality, by_carrier, by_segment, plan_fact, totals, month, figures):
    '''Собирает текстовый отчёт в формате Markdown.'''
    lines = ["# Отчёт по перевозкам", ""]
    lines.append("Сформирован: " + datetime.now().strftime("%d.%m.%Y %H:%M"))

    lines += ["", "## Ключевые показатели", ""]
    for k, v in kpi.items():
        lines.append(f"- **{k}**: {v}")

    lines += ["", "## Качество данных", ""]
    for k, v in quality.items():
        lines.append(f"- {k}: {v}")

    lines += ["", "## По перевозчикам", "", df_to_markdown(by_carrier)]
    lines += ["", "## По сегментам", "", df_to_markdown(by_segment)]

    lines += ["", f"## План и факт, {month}", ""]
    for k, v in totals.items():
        lines.append(f"- **{k}**: {v}")
    lines += ["", df_to_markdown(plan_fact.drop(columns="month"))]

    lines += ["", "## Графики", ""]
    for path in figures:
        link = Path(path).relative_to(config.REPORTS_DIR).as_posix()
        lines.append(f"![{Path(path).stem}]({link})")

    return chr(10).join(lines)


def main():
    started = datetime.now()
    print("=" * 56)
    print("ЗАПУСК PIPELINE", started.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 56)

    for folder in (config.PROCESSED_DIR, config.FIGURES_DIR):
        Path(folder).mkdir(parents=True, exist_ok=True)

    print("[1/5] загрузка")
    raw = load_trips(config.RAW_DIR, config.TRIPS_PATTERN)
    carriers = load_carriers(config.RAW_DIR, config.CARRIERS_FILE)
    clients = load_clients(config.RAW_DIR, config.CLIENTS_FILE)
    plan = load_plan(config.RAW_DIR, config.PLAN_FILE)
    print(f"    перевозчиков: {len(carriers)}, клиентов: {len(clients)}, строк плана: {len(plan)}")

    print("[2/5] подготовка")
    trips, quality = prepare_trips(raw)
    carriers_ok, carrier_quality = prepare_carriers(carriers)
    full, merge_quality = merge_trips(trips, carriers_ok, clients)
    plan_fact, plan_quality = build_plan_fact(full, plan, config.PLAN_MONTH)
    quality.update(carrier_quality)
    quality.update(merge_quality)
    quality.update(plan_quality)
    full_path = Path(config.PROCESSED_DIR) / "trips_full.csv"
    full.to_csv(full_path, index=False, encoding="utf-8")
    print(f"    сохранено: {full_path} ({len(full)} строк)")

    print("[3/5] расчёт метрик")
    kpi = overall_kpi(full)
    by_carrier = kpi_by(full, "carrier")
    by_segment = kpi_by(full, "segment")
    by_month = kpi_by(full, "month")
    totals = plan_totals(plan_fact)
    by_carrier.to_csv(Path(config.PROCESSED_DIR) / "kpi_by_carrier.csv",
                      index=False, encoding="utf-8")
    by_segment.to_csv(Path(config.PROCESSED_DIR) / "kpi_by_segment.csv",
                      index=False, encoding="utf-8")
    by_month.to_csv(Path(config.PROCESSED_DIR) / "kpi_by_month.csv",
                    index=False, encoding="utf-8")
    plan_fact.to_csv(Path(config.PROCESSED_DIR) / "plan_vs_fact.csv",
                     index=False, encoding="utf-8")

    print("[4/5] графики")
    fig1 = plot_revenue_by_month(by_month, config.FIGURES_DIR)
    fig2 = plot_plan_vs_fact(plan_fact, config.FIGURES_DIR)
    print(f"    {fig1}")
    print(f"    {fig2}")

    print("[5/5] отчёт")
    report_path = Path(config.REPORTS_DIR) / "report.md"
    report_path.write_text(
        build_report(kpi, quality, by_carrier, by_segment, plan_fact, totals,
                     config.PLAN_MONTH, [fig1, fig2]),
        encoding="utf-8")

    manifest = {
        "запуск": started.isoformat(timespec="seconds"),
        "длительность, с": round((datetime.now() - started).total_seconds(), 2),
        "параметры": {"TRIPS_PATTERN": config.TRIPS_PATTERN,
                      "PLAN_MONTH": config.PLAN_MONTH},
        "качество данных": quality,
        "итоговые метрики": kpi,
        "план и факт": totals,
        "версии библиотек": {"pandas": pandas.__version__,
                             "python": sys.version},
    }

    loaded_files = []
    for file_path in sorted(Path(config.RAW_DIR).glob("*.csv")):
        loaded_files.append({"имя": file_path.name,
                             "размер_байт": file_path.stat().st_size})
    manifest["загруженные файлы"] = loaded_files

    manifest_path = Path(config.PROCESSED_DIR) / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=int),
                             encoding="utf-8")
    print(f"    {report_path}")
    print(f"    {manifest_path}")
    print("ГОТОВО")
    return manifest


if __name__ == "__main__":
    main()
