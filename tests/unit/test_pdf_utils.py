#!/usr/bin/env python3
# Модульні тести для pdf_utils

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/full/utils'))
from pdf_utils import PDFUtils

class TestPDFUtils(unittest.TestCase):
    
    def setUp(self):
        self.utils = PDFUtils()
    
    def test_version(self):
        self.assertIsNotNone(self.utils.get_version())
    
    def test_merge(self):
        # Тест об'єднання
        pass
    
    def test_split(self):
        # Тест розділення
        pass

if __name__ == '__main__':
    unittest.main()
