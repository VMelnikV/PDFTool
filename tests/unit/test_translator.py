#!/usr/bin/env python3
# Модульні тести для перекладача

import unittest

from src.common.i18n.translator import Translator


class TestTranslator(unittest.TestCase):

    def setUp(self):
        self.translator = Translator()

    def test_get_language_returns_string(self):
        """Поточна мова — рядок із відомих кодів."""
        lang = self.translator.get_language()
        self.assertIn(lang, ['en', 'uk'])

    def test_set_language_uk(self):
        """Встановлення української мови працює."""
        self.translator.set_language('uk')
        self.assertEqual(self.translator.get_language(), 'uk')

    def test_set_language_en(self):
        """Встановлення англійської мови працює."""
        self.translator.set_language('en')
        self.assertEqual(self.translator.get_language(), 'en')

    def test_tr_returns_string(self):
        """tr() повертає рядок, навіть якщо ключ відсутній."""
        self.translator.set_language('uk')
        result = self.translator.tr('some.nonexistent.key')
        self.assertIsInstance(result, str)


if __name__ == '__main__':
    unittest.main()
