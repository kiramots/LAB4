import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import lab4

class TestStrings(unittest.TestCase):
    def test_find_replace_split(self):
        self.assertEqual(lab4.find_substring("NeoTerra 3000", "Terra"), 3)
        self.assertEqual(lab4.find_substring("abc", "z"), -1)
        self.assertEqual(lab4.replace_substring("a-b-c", "-", "+"), "a+b+c")
        self.assertEqual(lab4.split_text("a b  c"), ["a", "b", "c"])

    def test_errors(self):
        with self.assertRaises(ValueError):
            lab4.replace_substring("abc", "", "x")
        with self.assertRaises(TypeError):
            lab4.find_substring(123, "1")
        with self.assertRaises(TypeError):
            lab4.extract_measurements(None)

    def test_formatting_both_ways_equal(self):
        self.assertEqual(lab4.format_fstring("v", 800, "км/год"), "v: 800 км/год")
        self.assertEqual(lab4.format_fstring("v", 0.01, "%"),
                         lab4.format_method("v", 0.01, "%"))


class TestValidation(unittest.TestCase):
    def test_emails(self):
        for ok in ["info@neoterra3000.earth", "a.b+c@mail.com"]:
            with self.subTest(email=ok):
                self.assertTrue(lab4.validate_email(ok))
        for bad in ["info@", "@mail.com", "a b@mail.com", "abc", "a@b"]:
            with self.subTest(email=bad):
                self.assertFalse(lab4.validate_email(bad))

    def test_phones(self):
        for ok in ["+3000-555-NEO-TERRA", "+380441234567", "+380 (44) 123 45 67"]:
            with self.subTest(phone=ok):
                self.assertTrue(lab4.validate_phone(ok))
        for bad in ["123", "phone", "+38-", ""]:
            with self.subTest(phone=bad):
                self.assertFalse(lab4.validate_phone(bad))

    def test_find_all_bad_regex(self):
        with self.assertRaises(ValueError):
            lab4.find_all("(unclosed", "text")


class TestTextAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = lab4.load_text()

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            lab4.load_text("no_such_file.txt")

    def test_counts(self):
        self.assertEqual(lab4.count_words("Привіт, світе! Це комп'ютер."), 4)
        self.assertEqual(lab4.count_sentences("Раз. Два! Три? Без крапки"), 3)
        self.assertEqual(lab4.count_sentences("Рівень 0.01% і дата 15.07.3010. Кінець."), 2)

    def test_word_frequency(self):
        top = lab4.word_frequency(self.text, 3)
        self.assertEqual(len(top), 3)
        self.assertEqual(top[0][0], "neoterra")
        with self.assertRaises(ValueError):
            lab4.word_frequency(self.text, 0)

    def test_stats_positive(self):
        self.assertGreater(lab4.count_words(self.text), 100)
        self.assertGreater(lab4.count_sentences(self.text), 10)


class TestVariant5Regex(unittest.TestCase):
    """Вилучення назв екокуполів."""

    def test_in_text(self):
        self.assertEqual(lab4.extract_ecodomes(lab4.load_text()), ["EC-Dome-7"])

    def test_multiple_and_duplicates(self):
        s = "EC-Dome-7, EC-Dome-12 та знову EC-Dome-7; але XEC-Dome-3 і EC-Dome- не підходять"
        self.assertEqual(lab4.extract_ecodomes(s), ["EC-Dome-7", "EC-Dome-12"])

    def test_none(self):
        self.assertEqual(lab4.extract_ecodomes("Тут купола немає"), [])


class TestVariant5Measurements(unittest.TestCase):
    """Числа та одиниці вимірювання."""

    def test_in_text(self):
        pairs = [(m.value, m.unit) for m in lab4.extract_measurements(lab4.load_text())]
        self.assertEqual(
            pairs,
            [(800, "км/год"), (50, "ТВт"), (0.01, "%"), (1000, "USD"), (99.9, "%")])

    def test_scientific(self):
        ms = lab4.extract_measurements(
            "c = 299792458 м/с, T = 36,6 °C, m = 5.97e24 кг, t = -5 °C")
        self.assertEqual(
            [(m.value, m.unit) for m in ms],
            [(299792458, "м/с"), (36.6, "°C"), (5.97e24, "кг"), (-5, "°C")])

    def test_ignores_words_dates_codes(self):
        self.assertEqual(lab4.extract_measurements("5 мільйонів, 15.07.3010, HY-400 та"), [])

    def test_group_by_unit(self):
        ms = lab4.extract_measurements("1 % і 2 %, 3 кг")
        self.assertEqual(lab4.group_by_unit(ms), {"%": [1.0, 2.0], "кг": [3.0]})

if __name__ == "__main__":
    unittest.main()
