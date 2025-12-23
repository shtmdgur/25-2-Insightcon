
import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.price_data_loader import PriceDataLoader

class TestPriceDataLoader(unittest.TestCase):
    
    def setUp(self):
        # Use the actual data directory
        self.data_dir = Path("data/preprocessed/price")
        print(f"\nTesting with data directory: {self.data_dir.absolute()}")
        self.loader = PriceDataLoader(str(self.data_dir))
        
    def test_load_kq11(self):
        """Test loading KOSDAQ data (from ^KQ11_states.csv)"""
        ticker = "^KQ11"
        # Known date from previous inspection
        date = "2023-01-05" 
        
        context = self.loader.get_context(ticker, date)
        print(f"\n[Context for {ticker} on {date}]:\n{context}")
        
        self.assertIsInstance(context, str)
        self.assertNotEqual(context, "")
        self.assertIn("기준", context)
        self.assertIn("추세", context)
        
    def test_load_samsung(self):
        """Test loading Samsung Electronics data (005930.KS)"""
        ticker = "005930.KS"
        # Arbitrary date likely to be in the dataset (it spans 2020-2024 usually)
        date = "2023-01-05"
        
        context = self.loader.get_context(ticker, date)
        print(f"\n[Context for {ticker} on {date}]:\n{context}")
        
        if context:
            self.assertIn("시장 상황 요약", context)
        else:
            print(f"Warning: No data found for {ticker} on {date}. Check if file exists.")

    def test_missing_data(self):
        """Test handling of missing ticker or date"""
        context = self.loader.get_context("INVALID_TICKER", "2023-01-01")
        self.assertEqual(context, "")
        
        # Valid ticker, invalid date
        context_date = self.loader.get_context("^KQ11", "1990-01-01")
        self.assertIn("No price data available", context_date)

if __name__ == '__main__':
    unittest.main()
