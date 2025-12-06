import sys
from gui import SphereBrightnessApp # Изменено на SphereBrightnessApp
from PyQt6.QtWidgets import (
    QApplication
)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SphereBrightnessApp()
    window.show()
    sys.exit(app.exec())