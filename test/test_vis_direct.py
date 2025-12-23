
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    print("Testing Direct Visualizer...")
    from src.utils.visualizer import MatplotlibVisualizer
    print("Imported.")
    vis = MatplotlibVisualizer()
    print("Initialized.")
    path = vis.plot_debate_score(50, 50)
    print(f"Plotted: {path}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
