import re
from collections import Counter, namedtuple
from pathlib import Path

# Шлях до файлу з текстом.
DATA_FILE = Path(__file__).parent / "data" / "neoterra_text.txt"


def _check_str(value, name="text"):
    """Перевіряє, що аргумент є рядком."""
    if not isinstance(value, str):
        raise TypeError(
            f"Параметр '{name}' має бути рядком, а не {type(value).__name__}"
        )


def find_substring(text, sub):
    """Повертає індекс першого входження підрядка або -1, якщо його немає."""
    _check_str(text)
    _check_str(sub, "sub")
    return text.find(sub)


def replace_substring(text, old, new):
    """Замінює всі входження підрядка old на new."""
    _check_str(text)
    _check_str(old, "old")
    _check_str(new, "new")
    if not old:
        raise ValueError("Підрядок для заміни не може бути порожнім")
    return text.replace(old, new)


def split_text(text, sep=None):
    """Розділяє рядок за роздільником."""
    _check_str(text)
    return text.split(sep)


def format_fstring(name, value, unit):
    """Форматує вимір за допомогою f-string."""
    return f"{name}: {value:g} {unit}"

def format_method(name, value, unit):
    """Те саме, але за допомогою str.format()."""
    return "{}: {:g} {}".format(name, value, unit)


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^(?:\+?\d{10,13}|\+\d{1,4}(?:-[0-9A-Za-z]+)+)$")
URL_RE = re.compile(r"https?://[^\s]+")
HASHTAG_RE = re.compile(r"#\w+")


def find_all(pattern, text):
    """Пошук усіх збігів шаблону pattern у тексті."""
    _check_str(pattern, "pattern")
    _check_str(text)
    try:
        return re.findall(pattern, text)
    except re.error as err:
        raise ValueError(f"Некоректний регулярний вираз: {err}") from err


def validate_email(email):
    """True, якщо рядок є коректною емейл адресою."""
    _check_str(email, "email")
    return EMAIL_RE.fullmatch(email.strip()) is not None


def validate_phone(phone):
    """True, якщо рядок є коректним телефонним номером."""
    _check_str(phone, "phone")
    cleaned = re.sub(r"[\s()]", "", phone)
    return PHONE_RE.fullmatch(cleaned) is not None


def load_text(path=DATA_FILE):
    """Читає текстовий файл у кодуванні UTF-8 з обробкою типових помилок."""
    try:
        with open(path, encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл не знайдено: {path}") from None
    except UnicodeDecodeError:
        raise ValueError(f"Файл {path} не є коректним UTF-8") from None


def get_words(text):
    """Список слів у нижньому регістрі. Цифри та коди не рахуються."""
    _check_str(text)
    pattern = r"[^\W\d_]+(?:['’-][^\W\d_]+)*"
    return re.findall(pattern, text.lower())


def count_words(text):
    """Кількість слів у тексті."""
    return len(get_words(text))


def count_sentences(text):
    """Кількість речень у тексті."""
    _check_str(text)
    return len(re.findall(r"[^.!?]*[.!?]+(?=\s|$)", text))


def word_frequency(text, top=10):
    """Повертає `top` найчастіших слів як список пар (слово, кількість)."""
    if not isinstance(top, int) or top < 1:
        raise ValueError("top має бути додатним цілим числом")
    return Counter(get_words(text)).most_common(top)


def print_report(text, top=10):
    """Виводить результати аналізу тексту у зручному вигляді."""
    print("=" * 40)
    print(f"Кількість слів:    {count_words(text)}")
    print(f"Кількість речень:  {count_sentences(text)}")
    print(f"Топ-{top} слів:")
    for word, count in word_frequency(text, top):
        print(f"  {word:<15} {count}")
    print("=" * 40)


# Шаблон: "EC-Dome-" + одна або більше цифр.
# \b на початку чи в кінці гарантує що ми не вирвемо шматочок з довшого слова.
ECODOME_RE = re.compile(r"\bEC-Dome-\d+\b")


def extract_ecodomes(text):
    """Повертає список унікальних назв екокуполів у порядку появи в тексті."""
    _check_str(text)
    found = ECODOME_RE.findall(text)
    # dict.fromkeys прибирає дублікати, зберігаючи порядок.
    return list(dict.fromkeys(found))


Measurement = namedtuple("Measurement", ["value", "unit", "raw"])

UNITS = [
    "км/год", "км/с", "м/с", "км", "см", "мм", "м",
    "ТВт", "ГВт", "МВт", "кВт", "Вт",
    "кг", "мг", "г", "т",
    "ПБ", "ТБ", "ГБ", "МБ",
    "°C", "К", "Па", "Гц", "Дж",
    "хв", "год", "с",
    "USD", "%",
]
_UNITS_PATTERN = "|".join(re.escape(u) for u in UNITS)

MEASURE_RE = re.compile(
    rf"(?<!\w)(?P<value>[-+−]?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?)"
    rf"\s*(?P<unit>{_UNITS_PATTERN})(?!\w)"
)


def extract_measurements(text):
    """Витягує з тексту пари. Повертає список Measurement(value: float, unit: str, raw: str)."""
    _check_str(text)
    result = []
    for match in MEASURE_RE.finditer(text):
        number = match.group("value").replace(",", ".").replace("−", "-")
        result.append(Measurement(float(number), match.group("unit"), match.group(0)))
    return result


def group_by_unit(measurements):
    """Групує значення за одиницею."""
    grouped = {}
    for m in measurements:
        grouped.setdefault(m.unit, []).append(m.value)
    return grouped


def main():
    try:
        text = load_text()
    except (FileNotFoundError, ValueError) as err:
        print(f"Помилка: {err}")
        return

    print_report(text)

    print("\nЕкокупола:")
    for dome in extract_ecodomes(text):
        print(" ", dome)

    print("\nЧислові значення з одиницями:")
    for m in extract_measurements(text):
        print(f"  {m.raw!r:<14} -> {format_fstring('значення', m.value, m.unit)}")

    sample = ("Швидкість світла 299792458 м/с, температура 36,6 °C, "
              "маса Землі 5.97e24 кг, вологість 45%.")
    print("\nНауковий приклад:")
    for m in extract_measurements(sample):
        print("  ", format_method("значення", m.value, m.unit))
    print("   Групування:", group_by_unit(extract_measurements(sample)))


if __name__ == "__main__":
    main()
