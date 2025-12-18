import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import TokenRingWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = TokenRingWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()