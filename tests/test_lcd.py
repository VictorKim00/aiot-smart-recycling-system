from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.lcd_display import LCDDisplay

lcd = LCDDisplay()
lcd.show_lines(["LCD Test", "Smart Recycling", "Line 3", "Line 4"], hold=3)
lcd.show_lines(["Detected: bottle", "Type: Plastic", "Conf:0.88", "Open Plastic Bin"], hold=3)
lcd.close()
