import sys
from gui import IlluminationApp
from PyQt6.QtWidgets import (
    QApplication
)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IlluminationApp()
    window.show()
    sys.exit(app.exec())