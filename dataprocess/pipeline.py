import pandas as pd
from .core.battery_data import BatteryData
from .smoothing.savitzky import SavitzkyGolayStrategy
from .smoothing.gaussian import GaussianStrategy
from .categorization.cycle_categorizer import CycleCategorizer
from .analysis.dvdq import DVDQAnalyzer

class DataProcessPipeline:
    """
    Pipeline for processing battery data.
    """
    
    def __init__(self):
        self.categorizer = CycleCategorizer()
        
    def process_file(self, file_path: str, smoothing_method: str = 'sg', **kwargs) -> BatteryData:
        """
        Full processing pipeline: Load -> Categorize -> Smooth -> Analyze
        """
        # 1. Load Data
        try:
            if file_path.endswith('.csv') or file_path.endswith('.txt'):
                df = pd.read_csv(file_path, sep='\t' if file_path.endswith('.txt') else ',')
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format")
        except Exception as e:
            print(f"Error loading file: {e}")
            return None

        bd = BatteryData(df)
        
        # 2. Categorize Cycles
        bd.df = self.categorizer.categorize(bd)
        
        # 3. Setup Smoothing using Factory pattern
        if smoothing_method == 'sg':
             strategy = SavitzkyGolayStrategy(
                 window_length=kwargs.get('window_length', 51),
                 polyorder=kwargs.get('polyorder', 3)
             )
        elif smoothing_method == 'gaussian':
            strategy = GaussianStrategy(
                sigma=kwargs.get('sigma', 1.0)
            )
        else:
            strategy = None
            
        # 4. Analyze (dV/dQ)
        analyzer = DVDQAnalyzer(smoothing_strategy=strategy)
        bd = analyzer.calculate(bd)
        
        return bd
