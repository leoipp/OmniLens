import sys

from PyQt5.QtWidgets import QApplication, QMainWindow
from Setup.GuiSetup import UiSetup



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Store references to opened sub-windows
        self.opened_subwindows = {}

        self.utility_functions = UiSetup(self)




if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
