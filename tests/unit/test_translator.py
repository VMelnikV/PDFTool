#!/usr/bin/env python3
# Модульні тести для перекладача

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/common/i18n'))
from translator import Translator

class TestTranslator(unittest.TestCase):
    
    def setUp(self):
        self.translator = Translator()
    
    def test_get_system_language(self):
        lang = self.translator.get_system_language()
        self.assertIn(lang, ['en', 'uk'])
    
    def test_load_language(self):
        result = self.translator.load_language('uk')
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
