import os
import pandas as pd
from tabulate import tabulate

# Константы для расчёта
WORK_HOURS_PER_DAY = 7  # Рабочие часы в день (6 рабочих + 1 на перерывы)
WORK_DAYS_PER_WEEK = 5  # Рабочие дни в неделе
WORK_WEEKS_PER_YEAR = 52  # Рабочие недели в году
WRITE_SPEED_MIN = 10  # Строк кода в час (медленный сценарий)
WRITE_SPEED_MAX = 50  # Строк кода в час (быстрый сценарий)
READ_SPEED_MIN = 100  # Строк кода в час (медленный сценарий)
READ_SPEED_MAX = 200  # Строк кода в час (быстрый сценарий)

print(f'''Программа для анализа работы программистов.
На чем основан анализ?

WORK_HOURS_PER_DAY = 7:

    Предполагается стандартный 8-часовой рабочий день, но с учётом перерыва на обед (1 час) и других коротких пауз, остаётся ~7 часов эффективного времени.

WRITE_SPEED_MIN = 10 и WRITE_SPEED_MAX = 50:

    Исследования производительности программистов показывают, что:
        Средняя скорость написания нового кода составляет 10–50 строк в час. Это зависит от:
            Сложности проекта.
            Необходимости проектирования и тестирования.
            Типа задачи (новый функционал, багфиксы, работа с шаблонами).
    Источник: McConnell, S. (2004). Code Complete: A Practical Handbook of Software Construction.

READ_SPEED_MIN = 100 и READ_SPEED_MAX = 200:

    Анализ кода быстрее, чем его написание, особенно если код хорошо документирован.
        Опытные разработчики читают 100–200 строк в час, включая анализ архитектуры и понимание логики.
    Источник: Lettner, D. (2018). Measuring developer productivity.

''')


# Функция для анализа кода в папках микросервисов
def analyze_microservices(base_path, microservices):
    metrics = []
    code_extensions = {
        ".js", ".jsx", ".ts", ".tsx", ".py", ".java", ".c", ".cpp", ".go", ".rb",
        ".sh", ".bat", ".ps1", ".kt", ".rs", ".dart", ".swift", ".html", ".css",
        ".scss", ".vue", ".svelte", ".sql"
    }

    doc_extensions = {
        ".md", ".txt", ".json", ".yaml", ".yml", ".rst", ".ini", ".toml", ".cfg",
        ".csv", ".tsv", ".xml", ".properties", ".docx", ".doc", ".xlsx", ".xls"
    }

    for microservice in microservices:
        microservice_path = os.path.join(base_path, microservice)
        if os.path.exists(microservice_path):
            sloc_total, word_total, file_count = 0, 0, 0
            for root, _, files in os.walk(microservice_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    ext = os.path.splitext(file)[-1]

                    if ext in code_extensions or ext in doc_extensions:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            try:
                                content = f.readlines()
                                sloc = sum(1 for line in content if line.strip())
                                word_count = sum(len(line.split()) for line in content)
                                sloc_total += sloc
                                word_total += word_count
                                file_count += 1
                            except Exception:
                                continue
            metrics.append({
                "microservice": microservice,
                "sloc": sloc_total,
                "word_count": word_total,
                "file": file_count
            })
    return metrics


# Функция для добавления расчётов времени и классификации сложности
def calculate_metrics(metrics):
    df = pd.DataFrame(metrics)
    df["writing_hours_min"] = df["sloc"] / WRITE_SPEED_MIN
    df["writing_hours_max"] = df["sloc"] / WRITE_SPEED_MAX
    df["writing_days_min"] = df["writing_hours_min"] / WORK_HOURS_PER_DAY
    df["writing_days_max"] = df["writing_hours_max"] / WORK_HOURS_PER_DAY

    df["reading_hours_min"] = df["sloc"] / READ_SPEED_MIN
    df["reading_hours_max"] = df["sloc"] / READ_SPEED_MAX
    df["reading_days_min"] = df["reading_hours_min"] / WORK_HOURS_PER_DAY
    df["reading_days_max"] = df["reading_hours_max"] / WORK_HOURS_PER_DAY

    # Классификация сложности по количеству строк
    def classify_complexity(sloc):
        if sloc < 500:
            return "Low"
        elif sloc <= 2000:
            return "Medium"
        else:
            return "High"

    df["complexity"] = df["sloc"].apply(classify_complexity)
    return df


# Функция для текстового вывода
def print_time_estimates(df):
    print("\nАнализ времени работы:\n")
    for index, row in df.iterrows():
        microservice = row["microservice"]

        # Пессимистичный сценарий (медленная скорость написания)
        writing_days_min = row["writing_days_min"]
        writing_years_min = writing_days_min / (WORK_DAYS_PER_WEEK * WORK_WEEKS_PER_YEAR)
        writing_months_min = writing_years_min * 12
        writing_weeks_min = writing_days_min / WORK_DAYS_PER_WEEK

        # Оптимистичный сценарий (быстрая скорость написания)
        writing_days_max = row["writing_days_max"]
        writing_years_max = writing_days_max / (WORK_DAYS_PER_WEEK * WORK_WEEKS_PER_YEAR)
        writing_months_max = writing_years_max * 12
        writing_weeks_max = writing_days_max / WORK_DAYS_PER_WEEK

        print(f"Микросервис: {microservice}")
        print(f"  - Пессимистично (медленная скорость):")
        print(f"    * Лет: {writing_years_min:.2f}, Месяцев: {writing_months_min:.2f}, Недель: {writing_weeks_min:.2f}")
        print(f"  - Оптимистично (быстрая скорость):")
        print(f"    * Лет: {writing_years_max:.2f}, Месяцев: {writing_months_max:.2f}, Недель: {writing_weeks_max:.2f}")
        print()


# Функция для текстового вывода с общим анализом
def print_time_estimates_with_summary(df):
    print("\nАнализ времени работы для каждого микросервиса:\n")
    total_sloc = df["sloc"].sum()
    total_word_count = df["word_count"].sum()
    total_writing_days_min = df["writing_days_min"].sum()
    total_writing_days_max = df["writing_days_max"].sum()
    total_reading_days_min = df["reading_days_min"].sum()
    total_reading_days_max = df["reading_days_max"].sum()

    # Вывод для каждого микросервиса
    for index, row in df.iterrows():
        microservice = row["microservice"]

        # Пессимистичный сценарий (медленная скорость написания)
        writing_days_min = row["writing_days_min"]
        writing_years_min = writing_days_min / (WORK_DAYS_PER_WEEK * WORK_WEEKS_PER_YEAR)
        writing_months_min = writing_years_min * 12
        writing_weeks_min = writing_days_min / WORK_DAYS_PER_WEEK

        # Оптимистичный сценарий (быстрая скорость написания)
        writing_days_max = row["writing_days_max"]
        writing_years_max = writing_days_max / (WORK_DAYS_PER_WEEK * WORK_WEEKS_PER_YEAR)
        writing_months_max = writing_years_max * 12
        writing_weeks_max = writing_days_max / WORK_DAYS_PER_WEEK

        print(f"Микросервис: {microservice}")
        print(f"  - Пессимистично (медленная скорость):")
        print(f"    * Лет: {writing_years_min:.2f} ({writing_months_min:.2f} месяцев, {writing_days_min:.0f} дней)")
        print(f"  - Оптимистично (быстрая скорость):")
        print(f"    * Лет: {writing_years_max:.2f} ({writing_months_max:.2f} месяцев, {writing_days_max:.0f} дней)")
        print()

    # Общий вывод
    total_writing_years_min = total_writing_days_min / (WORK_DAYS_PER_WEEK * WORK_WEEKS_PER_YEAR)
    total_writing_years_max = total_writing_days_max / (WORK_DAYS_PER_WEEK * WORK_WEEKS_PER_YEAR)
    total_reading_years_min = total_reading_days_min / (WORK_DAYS_PER_WEEK * WORK_WEEKS_PER_YEAR)
    total_reading_years_max = total_reading_days_max / (WORK_DAYS_PER_WEEK * WORK_WEEKS_PER_YEAR)

    total_writing_months_min = total_writing_years_min * 12
    total_writing_months_max = total_writing_years_max * 12
    total_reading_months_min = total_reading_years_min * 12
    total_reading_months_max = total_reading_years_max * 12

    print("\nОбщий анализ для всех микросервисов:")
    print(f"  - Общее количество строк кода (SLOC): {total_sloc:,}")
    print(f"  - Общее количество слов: {total_word_count:,}")
    print(f"  - Время на написание (пессимистично): {total_writing_years_min:.2f} лет ({total_writing_months_min:.2f} месяцев, {total_writing_days_min:.0f} дней)")
    print(f"  - Время на написание (оптимистично): {total_writing_years_max:.2f} лет ({total_writing_months_max:.2f} месяцев, {total_writing_days_max:.0f} дней)")
    print(f"  - Время на изучение (пессимистично): {total_reading_years_min:.2f} лет ({total_reading_months_min:.2f} месяцев, {total_reading_days_min:.0f} дней)")
    print(f"  - Время на изучение (оптимистично): {total_reading_years_max:.2f} лет ({total_reading_months_max:.2f} месяцев, {total_reading_days_max:.0f} дней)\n")


# Функция для отображения краткой таблицы
def print_summary_table(df):
    # Отбираем только нужные колонки и создаём копию DataFrame
    summary_data = df[["microservice", "sloc", "word_count", "file"]].copy()
    # Переименовываем колонки для краткости
    summary_data.columns = ["Microservice", "SLOC", "Words", "Files"]
    # Форматируем числа с разделением тысяч
    summary_data["SLOC"] = summary_data["SLOC"].apply(lambda x: f"{x:,}")
    summary_data["Words"] = summary_data["Words"].apply(lambda x: f"{x:,}")
    summary_data["Files"] = summary_data["Files"].apply(lambda x: f"{x:,}")
    # Печатаем таблицу
    print("\nКраткая таблица по микросервисам:\n")
    print(tabulate(summary_data, headers="keys", tablefmt="grid", showindex=False))


# Основной код
if __name__ == "__main__":
    # Укажите путь к базовой папке и список микросервисов
    base_path = r"E:\GitHub\kcentr_v2024"
    microservices = ["kcentr_v2_admin", "kcentr_v2_api", "kcentr_v2_app", "kcentr_v2_crm", "kcentr_v2_odata",
                     "kcentr_v2_stock"]

    # Анализ папок микросервисов
    raw_metrics = analyze_microservices(base_path, microservices)
    detailed_metrics = calculate_metrics(raw_metrics)

    # Показываем результаты в консоли
    #print(detailed_metrics)

    # Краткая таблица
    print_summary_table(detailed_metrics)

    # Сохранение результата в CSV
    output_file = "microservices_analysis.csv"
    detailed_metrics.to_csv(output_file, index=False)
    print(f"Результаты сохранены в файл: {output_file}")

    # Вывод текстового анализа
    #print_time_estimates(detailed_metrics)

    # Вывод текстового анализа с общим итогом
    print_time_estimates_with_summary(detailed_metrics)
