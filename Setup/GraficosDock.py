from PyQt5.QtWidgets import QDockWidget, QToolBox, QWidget, QVBoxLayout, QLabel, QMainWindow, QCheckBox, QSpinBox, \
    QFormLayout, QButtonGroup, QDoubleSpinBox, QComboBox, QGridLayout, QFrame
from PyQt5.QtCore import Qt

class GraficosDock(QDockWidget):
    """Janela flutuante com um QToolBox para ajustes"""
    def __init__(self, treeview, parent=None):
        super().__init__("Gráficos", parent)

        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFloating(True)  # Permite que o Dock fique independente
        self.tree_view = treeview

        # Criação do QToolBox
        toolbox = QToolBox()
        self.combo_box = QComboBox()

        # Seção Gráfico de Dispersão
        dispersao_widget = QWidget()
        layout1 = QFormLayout()  # Form Layout para alinhamento correto
        # Widgets de configuração
        # Adiciona os widgets ao layout
        layout1.addRow(QLabel("Dispersão"))  # Linha para checkbox
        layout1.addWidget(self.combo_box)
        dispersao_widget.setLayout(layout1)

        # Seção Gráfico de Barras
        barras_widget = QWidget()
        layout2 = QFormLayout()  # Form Layout para alinhamento correto
        # Widgets de configuração
        # Adiciona os widgets ao layout
        layout2.addRow(QLabel("Barras"))  # Linha para checkbox
        barras_widget.setLayout(layout2)

        # Seção Histograma
        histograma_widget = QWidget()
        layout3 = QFormLayout()  # Form Layout para alinhamento correto
        # Widgets de configuração
        # Adiciona os widgets ao layout
        layout3.addRow(QLabel("Histograma"))  # Linha para checkbox
        histograma_widget.setLayout(layout3)

        # Adiciona as seções ao QToolBox
        toolbox.addItem(dispersao_widget, "Dispersão")
        toolbox.addItem(barras_widget, "Barras")
        toolbox.addItem(histograma_widget, "Histograma")

        # Define o QToolBox como conteúdo do QDockWidget
        self.setWidget(toolbox)

        # Connect signals and populate comboBox
        self.connect_tree_signals()

    def connect_tree_signals(self):
        """Connect model signals to update the combo box dynamically."""
        model = self.tree_view.model()

        if model:
            model.rowsInserted.connect(self.populate_combo)
            model.rowsRemoved.connect(self.populate_combo)
            model.dataChanged.connect(self.populate_combo)

        # Populate initially
        self.populate_combo()

    def populate_combo(self):
        """Populate the combo box with file names from the tree view."""
        self.combo_box.clear()
        model = self.tree_view.model()
        if not model:
            return

        root_index = model.invisibleRootItem()  # Get the root item

        # Recursively fetch filenames
        def get_all_items(parent_item):
            for row in range(parent_item.rowCount()):
                item = parent_item.child(row)
                if item:
                    self.combo_box.addItem(item.text())  # Add the item name
                    get_all_items(item)  # Check for nested items

        get_all_items(root_index)


def open_graficos_dock(parent_window, tree_view):
    """Abre o dock widget de ajustes"""
    if not hasattr(parent_window, 'graficos_dock') or parent_window.graficos_dock is None:
        parent_window.graficos_dock = GraficosDock(tree_view, parent_window)
        parent_window.addDockWidget(Qt.RightDockWidgetArea, parent_window.graficos_dock)

    parent_window.graficos_dock.show()
    parent_window.graficos_dock.raise_()
    parent_window.graficos_dock.activateWindow()
