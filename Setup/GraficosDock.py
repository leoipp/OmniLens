import os
import pickle
import tempfile

import numpy as np
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QDockWidget, QToolBox, QWidget, QVBoxLayout, QLabel, QMainWindow, QCheckBox, QSpinBox, \
    QFormLayout, QDoubleSpinBox, QComboBox, QPushButton, QLineEdit, QTableView, \
    QMdiSubWindow, QGridLayout
from PyQt5.QtCore import Qt
import matplotlib.markers as mmarkers
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from sklearn.preprocessing import LabelEncoder

from matplotlib import colors
import matplotlib.colors as mcolors

class CustomMdiSubWindow(QMdiSubWindow):
    def closeEvent(self, event):
        """Ao fechar a janela, garante que o objeto seja removido da memória"""
        print(f"Closing window: {self.windowTitle()}")
        self.deleteLater()  # Libera a memória
        event.accept()  # Aceita o fechamento da janela


class GraficosDock(QDockWidget):
    """Janela flutuante com um QToolBox para ajustes"""
    def __init__(self, treeview, mdi_area, parent=None):
        super().__init__("Análise de Dados", parent)

        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        #self.setFloating(True)  # Permite que o Dock fique independente
        self.tree_view = treeview
        self.mdi_area = mdi_area
        # Initialize the set to track open subwindows
        self.open_subwindows = set()

        # Criando o layout principal
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # Adicionando o Label e o ComboBox no topo
        self.label = QLabel("Selecione o Arquivo:")
        self.combo_box = QComboBox()

        main_layout.addWidget(self.label)
        main_layout.addWidget(self.combo_box)

        # Criação do QToolBox
        self.toolbox = QToolBox()

        self.toolbox_dispersao()
        self.toolbox_barras()
        self.toolbox_histograma()
        self.toolbox_config()

        # Adiciona o QToolBox ao layout principal
        main_layout.addWidget(self.toolbox)
        main_widget.setLayout(main_layout)

        # Define o QWidget como conteúdo do QDockWidget
        self.setWidget(main_widget)

        # Connect signals and populate comboBox
        self.connect_tree_signals()

        self.populate_markers()
        self.populate_colormaps()
        self.populate_colors()
        self.populate_hatch_patterns()

        # Connect combo_box selection change to column update
        self.combo_box.currentIndexChanged.connect(self.populate_table_columns)
        self.plotar_botao.clicked.connect(lambda: self.plot_graph('dispersao', self.checkbox_estratificacao.isChecked()))
        self.plotar_botao_b.clicked.connect(lambda: self.plot_graph('barras', self.checkbox_estratificacao.isChecked()))
        self.plotar_botao_h.clicked.connect(lambda: self.plot_graph('histograma', self.checkbox_estratificacao.isChecked()))

    def toolbox_dispersao(self):
        # Seção Gráfico de Dispersão
        dispersao_widget = QWidget()
        self.plotar_botao = QPushButton("Plotar Dispersão")
        (self.var_y, self.var_x, self.estrat, self.cor,
         self.marcadores, self.color_map) = (QComboBox(), QComboBox(), QComboBox(),
                                             QComboBox(), QComboBox(), QComboBox())
        self.tamanho, self.min_color_val, self.max_color_val, self.alpha = QSpinBox(), QSpinBox(), QSpinBox(), QDoubleSpinBox()
        # Pré configurações de spinbox
        self.tamanho.setRange(1, 100)
        self.tamanho.setSingleStep(1)
        self.tamanho.setValue(15)
        self.alpha.setRange(0, 1)
        self.alpha.setSingleStep(0.01)
        self.alpha.setValue(0.8)

        layout1 = QFormLayout()  # Form Layout para alinhamento correto
        # Adiciona os widgets ao layout
        layout1.addRow(QLabel("Variável X:"), self.var_x)
        layout1.addRow(QLabel("Variável Y:"), self.var_y)
        layout1.addRow(QLabel("Tamanho:"), self.tamanho)
        layout1.addRow(QLabel("Cor:"), self.cor)
        layout1.addRow(QLabel("Marcador:"), self.marcadores)
        layout1.addRow(QLabel("Transparência:"), self.alpha)

        # Criando a opção de ativar/desativar estratificação
        self.checkbox_estratificacao = QCheckBox("Habilitar Estratificação")
        self.checkbox_estratificacao.stateChanged.connect(self.toggle_estratificacao)
        layout1.addRow(self.checkbox_estratificacao)

        dispersao_widget.setLayout(layout1)

        # Seção de Estratificação (Inicialmente Oculta)
        self.estratificacao_widget = QWidget()

        layout_estratificacao = QFormLayout()
        layout_estratificacao.addRow(QLabel("Estratificação:"), self.estrat)
        layout_estratificacao.addRow(QLabel("Tema de Cores:"), self.color_map)
        layout_estratificacao.addRow(QLabel("Min. Cor:"), self.min_color_val)
        layout_estratificacao.addRow(QLabel("Máx. Cor:"), self.max_color_val)

        self.estratificacao_widget.setLayout(layout_estratificacao)
        layout1.addRow(self.estratificacao_widget)
        self.estratificacao_widget.setVisible(False)  # Inicialmente oculto
        layout1.addWidget(self.plotar_botao)
        self.toolbox.addItem(dispersao_widget, "Gráfico de Dispersão")

    def toolbox_barras(self):
        # Seção Gráfico de Barras
        barras_widget = QWidget()
        self.var_b_x = QComboBox()
        self.var_b_height = QComboBox()
        self.var_b_width = QDoubleSpinBox()
        self.var_b_width.setValue(.8)
        self.var_b_width.setRange(0, 1)
        self.var_b_width.setSingleStep(0.1)
        self.align = QComboBox()
        self.align.addItem("center")
        self.align.addItem("edge")
        self.cor_b = QComboBox()
        self.edge_color = QComboBox()
        self.hatch = QComboBox()
        self.plotar_botao_b = QPushButton("Plotar Barras")
        layout2 = QFormLayout()  # Form Layout para alinhamento correto
        # Adiciona os widgets ao layout
        layout2.addRow(QLabel("Variável X:"), self.var_b_x)
        layout2.addRow(QLabel("Altura:"), self.var_b_height)
        layout2.addRow(QLabel("Largura:"), self.var_b_width)
        layout2.addRow(QLabel("Alinhamento:"), self.align)
        layout2.addRow(QLabel("Cor:"), self.cor_b)
        layout2.addRow(QLabel("Bordas:"), self.edge_color)
        layout2.addRow(QLabel("Hachura:"), self.hatch)
        layout2.addWidget(self.plotar_botao_b)
        barras_widget.setLayout(layout2)
        self.toolbox.addItem(barras_widget, "Barras")

    def toolbox_histograma(self):
        # Seção Histograma
        histograma_widget = QWidget()
        self.var_hist_x = QComboBox()
        self.bins = QCheckBox()
        self.color_h = QComboBox()
        self.edge_h = QComboBox()
        self.density = QCheckBox()
        self.cpeso = QCheckBox()
        self.peso = QComboBox()
        self.orientacao = QComboBox()
        self.orientacao.addItem("vertical")
        self.orientacao.addItem("horizontal")
        self.align_h = QComboBox()
        self.align_h.addItem("left")
        self.align_h.addItem("mid")
        self.align_h.addItem("right")
        self.histtipe = QComboBox()
        self.histtipe.addItem("bar")
        self.histtipe.addItem("barstacked")
        self.histtipe.addItem("step")
        self.histtipe.addItem("stepfilled")
        self.log = QCheckBox()
        self.fill = QCheckBox()
        self.plotar_botao_h = QPushButton("Plotar Histograma")

        # Seção de Estratificação (Inicialmente Oculta)
        self.bins_widget = QWidget()
        self.range_min = QSpinBox()
        self.range_max = QSpinBox()
        self.function = QComboBox()
        self.function.addItem("auto")
        self.function.addItem("sturges")
        self.function.addItem("fd")
        self.function.addItem("doane")
        self.function.addItem("scott")

        layout3 = QFormLayout()  # Form Layout para alinhamento correto
        # Adiciona os widgets ao layout
        layout3.addRow(QLabel("Variável X:"), self.var_hist_x)
        layout3.addRow(QLabel("Peso:"), self.peso)
        layout3.addRow(QLabel("Bins Personalizados:"), self.bins)
        layout3.addRow(self.bins_widget)
        layout3.addRow(QLabel("Cor:"), self.color_h)
        layout3.addRow(QLabel("Bordas:"), self.edge_h)
        layout3.addRow(QLabel("Densidade:"), self.density)
        layout3.addRow(QLabel("Orientação:"), self.orientacao)
        layout3.addRow(QLabel("Alinhamento:"), self.align_h)
        layout3.addRow(QLabel("Normalização (Log.):"), self.log)
        layout3.addRow(QLabel("Tipo:"), self.histtipe)
        layout3.addRow(QLabel("Preenchimento:"), self.fill)
        histograma_widget.setLayout(layout3)

        self.bins.stateChanged.connect(self.toggle_bins)

        layout_bin = QGridLayout()
        # First row with "Range Min." and "Range Max."
        layout_bin.addWidget(QLabel("Range Min.:"), 0, 0)  # First label in the first column
        layout_bin.addWidget(self.range_min, 0, 1)  # Widget in the second column
        layout_bin.addWidget(QLabel("Range Max.:"), 0, 2)  # Second label in the third column
        layout_bin.addWidget(self.range_max, 0, 3)  # Widget in the fourth column

        self.bins_widget.setLayout(layout_bin)
        self.bins_widget.setVisible(False)  # Inicialmente oculto
        layout3.addWidget(self.plotar_botao_h)
        self.toolbox.addItem(histograma_widget, "Histograma")

    def toolbox_config(self):
        # Seção Configurações
        config_widget = QWidget()
        self.title = QLineEdit()
        self.xlabel = QLineEdit()
        self.ylabel = QLineEdit()
        self.grid = QCheckBox()
        self.legend = QCheckBox()
        layout4 = QFormLayout()  # Form Layout para alinhamento correto
        # Widgets de configuração
        # Adiciona os widgets ao layout
        layout4.addRow(QLabel("Título:"), self.title)  # Linha para titulo
        layout4.addRow(QLabel("Eixo X:"), self.xlabel)  # Linha para titulo
        layout4.addRow(QLabel("Eixo Y:"), self.ylabel)  # Linha para titulo
        layout4.addRow(QLabel("Mostrar Grade:"), self.grid)  # Linha para titulo
        layout4.addRow(QLabel("Mostrar Legenda:"), self.legend)  # Linha para titulo
        config_widget.setLayout(layout4)
        self.toolbox.addItem(config_widget, "Configurações")

    def toggle_estratificacao(self, state):
        """Mostra ou oculta a seção de estratificação com base no estado do checkbox."""
        self.estratificacao_widget.setVisible(state == 2)

    def toggle_bins(self, state):
        self.bins_widget.setVisible(state == 2)

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

    def populate_markers(self):
        """Preenche o QComboBox com os nomes dos marcadores do Matplotlib"""
        markers = mmarkers.MarkerStyle.markers  # Obtém todos os marcadores disponíveis
        for key in markers.keys():
            if isinstance(key, str):  # Evita adicionar valores numéricos desnecessários
                self.marcadores.addItem(key)

    def populate_colormaps(self):
        """Preenche o QComboBox com os nomes dos colormaps do Matplotlib"""
        colormaps = plt.colormaps()  # Obtém todos os colormaps disponíveis
        for cmap in colormaps:
            self.color_map.addItem(cmap)

    def populate_colors(self):
        """Preenche o QComboBox com os nomes das cores do Matplotlib"""
        colors = list(mcolors.CSS4_COLORS.keys())  # Obtém todos os nomes de cores disponíveis
        for color in colors:
            self.cor.addItem(color)  # Adiciona cada cor ao QComboBox
            self.cor_b.addItem(color)
            self.edge_color.addItem(color)
            self.color_h.addItem(color)
            self.edge_h.addItem(color)

    def populate_hatch_patterns(self):
        """Preenche o QComboBox com os padrões de hachura do Matplotlib"""
        hatch_patterns = [None, '/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*']  # Lista de padrões de hachura
        for pattern in hatch_patterns:
            self.hatch.addItem(pattern)

    def get_table_model_by_filename(self, filename):
        """Finds the table model based on the selected filename from combo_box."""
        if not self.mdi_area:
            return None

        for subwindow in self.mdi_area.subWindowList():
            table_view = subwindow.findChild(QTableView)
            if table_view and table_view.model():
                # Assume the window title corresponds to the filename
                if subwindow.windowTitle() == filename:
                    return table_view.model()

        return None

    def populate_table_columns(self):
        """Populate var_x and var_y with column names from the table corresponding to the selected file."""
        selected_filename = self.combo_box.currentText()
        model = self.get_table_model_by_filename(selected_filename)

        if not model:
            self.var_x.clear()
            self.var_y.clear()
            self.estrat.clear()
            self.var_b_x.clear()
            self.var_b_height.clear()
            self.var_hist_x.clear()
            self.peso.clear()
            return

        self.var_x.clear()
        self.var_y.clear()
        self.estrat.clear()
        self.var_b_x.clear()
        self.var_b_height.clear()
        self.var_hist_x.clear()
        self.peso.clear()

        # List of combo boxes to be populated
        combo_boxes = [self.var_x, self.var_y, self.estrat, self.var_b_x,
                       self.var_b_height, self.var_hist_x, self.peso]

        # Populate each combo box with "None" and the column names
        for combo_box in combo_boxes:
            combo_box.addItem(None)  # Add "None" as the first item
            for col in range(model.columnCount()):
                column_name = model.headerData(col, Qt.Horizontal)
                if column_name:
                    combo_box.addItem(column_name)  # Add each column name

    def plot_graph(self, grafico_checker, checkbox=False):
        """Creates a new MDI subwindow with the selected graph and adds it under the corresponding file in the tree view."""
        model, var_x_name, var_y_name, estrat_name = self.get_selected_data(grafico_checker)

        if not model:
            return

        x_data, y_data, estrat_data, x_labels, y_labels = self.process_data(model, var_x_name, var_y_name, estrat_name,
                                                                            checkbox, grafico_checker)

        if x_data is None or y_data is None:
            return

        if grafico_checker == 'dispersao':
            self.create_scatter_plot(x_data, y_data, estrat_data, x_labels, y_labels, estrat_name, checkbox)
        if grafico_checker == 'barras':
            self.create_bar_plot( x_data, y_data, x_labels, y_labels)
        if grafico_checker == 'histograma':
            self.create_hist_plot( x_data, y_data, x_labels, y_labels)

    def get_selected_data(self, grafico_checker):
        """Retrieves the selected model and column names."""
        selected_filename = self.combo_box.currentText()
        model = self.get_table_model_by_filename(selected_filename)

        if not model:
            print("No table model found for selected file.")
            return None, None, None, None





        # if not var_x_name or not var_y_name:
        #     print("Please select both X and Y variables.")
        #     return None, None, None, None

        if grafico_checker == 'dispersao':
            var_x_name = self.var_x.currentText()
            var_y_name = self.var_y.currentText()
            estrat_name = self.estrat.currentText()
            return model, var_x_name, var_y_name, estrat_name
        if grafico_checker == 'barras':
            var_x_b = self.var_b_x.currentText()
            var_b_height = self.var_b_height.currentText()
            estrat_name = self.estrat.currentText()
            return model, var_x_b, var_b_height, estrat_name
        if grafico_checker == 'histograma':
            var_hist_x = self.var_hist_x.currentText()
            peso = self.peso.currentText()
            estrat_name = self.estrat.currentText()
            return model, var_hist_x, peso, estrat_name

    def process_data(self, model, var_x_name, var_y_name, estrat_name, checkbox, grafico_checker):
        """Extracts and processes data from the model."""
        col_x, col_y, col_estrat = self.get_column_indices(model, var_x_name, var_y_name, estrat_name, checkbox)

        if grafico_checker != 'histograma':
            if col_x is None or col_y is None:
                print("Selected columns not found.")
                return None, None, None, None, None

        raw_x_data, raw_y_data, raw_estrat_data = self.extract_raw_data(model, col_x, col_y, col_estrat, checkbox)

        # Process X and Y
        x_data, x_labels = self.encode_data(raw_x_data)
        y_data, y_labels = self.encode_data(raw_y_data)

        # Process stratification variable (if enabled)
        if checkbox and raw_estrat_data:
            estrat_data, estrat_labels = self.encode_data(raw_estrat_data)
        else:
            estrat_data, estrat_labels = None, None

        return x_data, y_data, estrat_data, x_labels, y_labels

    def get_column_indices(self, model, var_x_name, var_y_name, estrat_name, checkbox):
        """Finds the column indices for the selected variables."""
        col_x, col_y, col_estrat = None, None, None

        for col in range(model.columnCount()):
            header = model.headerData(col, Qt.Horizontal)
            if header == var_x_name:
                col_x = col
            if header == var_y_name:
                col_y = col
            if checkbox and header == estrat_name:
                col_estrat = col

        return col_x, col_y, col_estrat

    def extract_raw_data(self, model, col_x, col_y, col_estrat, checkbox, checker='hist'):
        """Extracts raw data from the model."""
        raw_x_data, raw_y_data, estrat_data = [], [], []

        for row in range(model.rowCount()):
            x_value = model.index(row, col_x).data()
            y_value = model.index(row, col_y).data()
            estrat_value = model.index(row, col_estrat).data() if checkbox and col_estrat is not None else None

            if x_value is not None and y_value is not None:
                raw_x_data.append(x_value)
                raw_y_data.append(y_value)
                if checkbox and estrat_value is not None:
                    estrat_data.append(estrat_value)

        return raw_x_data, raw_y_data, estrat_data

    def encode_data(self, data):
        """Encodes categorical data into numeric values if necessary."""
        if all(isinstance(val, (int, float)) for val in data):
            return list(map(float, data)), None  # Keep numbers as they are

        # Convert everything to strings first (handles mixed cases)
        data = [str(val) for val in data]

        encoder = LabelEncoder()
        numeric_data = encoder.fit_transform(data)
        labels = {i: label for i, label in enumerate(encoder.classes_)}

        return numeric_data, labels

    def create_scatter_plot(self, x_data, y_data, estrat_data, x_labels, y_labels, estrat_name,
                            checkbox):
        """Creates and displays the scatter plot."""
        fig, ax = plt.subplots()
        s = self.tamanho.value()  # Marker size
        marker = self.marcadores.currentText()  # Marker style
        alpha = self.alpha.value()  # Transparency

        if checkbox:
            cmap = self.color_map.currentText()
            norm = colors.Normalize(vmin=self.min_color_val.value(), vmax=self.max_color_val.value())
            scatter = ax.scatter(x_data, y_data, s=s, marker=marker, c=estrat_data, cmap=cmap, norm=norm, alpha=alpha)
            fig.colorbar(scatter, ax=ax, label=estrat_name)
        else:
            c = self.cor.currentText()
            ax.scatter(x_data, y_data, s=s, marker=marker, c=c, alpha=alpha)

        # Set axis labels
        if self.xlabel.text() != "":
            ax.set_xlabel(self.xlabel.text())
        else:
            ax.set_xticks(range(len(x_labels)))
            ax.set_xticklabels([x_labels[i] for i in range(len(x_labels))], rotation=45)

        if self.ylabel.text() != "":
            ax.set_ylabel(self.ylabel.text())
        else:
            ax.set_yticks(range(len(y_labels)))
            ax.set_yticklabels([y_labels[i] for i in range(len(y_labels))])

        ax.set_title(self.title.text())

        if self.grid.isChecked():
            # Enable the grid
            ax.grid(True)

        self.display_plot(fig, self.title.text(), "Dispersão")

    def create_bar_plot(self, x_data, y_data, x_labels, y_labels):
        """Creates and displays the bar plot."""
        fig, ax = plt.subplots()

        width = self.var_b_width.value()
        align = self.align.currentText()
        cor_b = self.cor_b.currentText()
        edge_color = self.edge_color.currentText()
        hatch = self.hatch.currentText()

        ax.bar(x_data, y_data, width=width, align=align, color=cor_b, edgecolor=edge_color, hatch=hatch)

        # Set axis labels
        if self.xlabel.text() != "":
            ax.set_xlabel(self.xlabel.text())
        else:
            ax.set_xticks(range(len(x_labels)))
            ax.set_xticklabels([x_labels[i] for i in range(len(x_labels))], rotation=45)

        if self.ylabel.text() != "":
            ax.set_ylabel(self.ylabel.text())
        else:
            ax.set_yticks(range(len(y_labels)))
            ax.set_yticklabels([y_labels[i] for i in range(len(y_labels))])

        ax.set_title(self.title.text())

        if self.grid.isChecked():
            # Enable the grid
            ax.grid(True)

        self.display_plot(fig, self.title.text(), "Barras")

    def create_hist_plot(self, x_data, y_data, x_labels, y_labels):
        """Creates and displays the histogram plot."""
        fig, ax = plt.subplots()

        align = self.align_h.currentText()
        cor_b = self.color_h.currentText()
        edge_color = self.edge_h.currentText()
        orientation = self.orientacao.currentText()
        type = self.histtipe.currentText()
        fill = self.fill.isChecked()
        density = self.density.isChecked()
        log = self.log.isChecked()

        print(y_data)
        # Assuming x_data and weights are already defined
        weights = np.ones_like(y_data)  # Example, replace with actual weights if needed

        if self.bins.isChecked():
            pass
        else:
            ax.hist(x_data, color=cor_b, edgecolor=edge_color, orientation=orientation, align=align, histtype=type, weights=weights, fill=fill,
                    density=density, log=log)

        # Set axis labels
        if self.xlabel.text() != "":
            ax.set_xlabel(self.xlabel.text())
        else:
            ax.set_xticks(range(len(x_labels)))
            ax.set_xticklabels([x_labels[i] for i in range(len(x_labels))], rotation=45)

        if self.ylabel.text() != "":
            ax.set_ylabel(self.ylabel.text())
        else:
            ax.set_yticks(range(len(y_labels)))
            ax.set_yticklabels([y_labels[i] for i in range(len(y_labels))])

        ax.set_title(self.title.text())

        if self.grid.isChecked():
            # Enable the grid
            ax.grid(True)

        self.display_plot(fig, self.title.text(), "Histograma")

    def display_plot(self, fig, titulo, grafico):
        """Displays the plot in a new MDI subwindow and saves it correctly."""
        subwindow_title = f"Gráfico de {grafico} - {titulo}"

        # Check if a subwindow with the same title already exists
        for subwindow in self.mdi_area.subWindowList():
            if subwindow.windowTitle() == subwindow_title:
                print(f"Subwindow '{subwindow_title}' already exists. Skipping.")
                return  # Avoid duplicate subwindows

        # Create new subwindow
        subwindow = CustomMdiSubWindow()
        subwindow.setWindowTitle(subwindow_title)

        # Create QWidget and layout
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Attach FigureCanvas
        canvas = FigureCanvas(fig)
        canvas.draw()  # Ensure all UI elements (labels, title, etc.) are applied
        layout.addWidget(canvas)

        subwindow.setWidget(widget)
        self.mdi_area.addSubWindow(subwindow)
        subwindow.show()

        # Add the subwindow to the tree
        selected_filename = self.combo_box.currentText()
        self.add_subwindow_to_tree(self.tree_view, selected_filename, subwindow)

        # Ensure "Temp" subfolder exists
        temp_folder = os.path.join(os.getcwd(), "Temp")
        os.makedirs(temp_folder, exist_ok=True)

        # Save the entire FigureCanvas instead of just fig
        file_path = os.path.join(temp_folder, f"{subwindow_title}.pkl")
        with open(file_path, "wb") as f:
            pickle.dump(fig, f)  # Saving full figure ensures all settings persist

        print(f"Figure saved: {file_path}")

        return subwindow


    def add_subwindow_to_tree(self, tree_view, filename, subwindow):
        """Finds the file in the tree view and adds the subwindow under it as a child item, avoiding duplicates."""
        model = tree_view.model()

        # Ensure the model is a QStandardItemModel
        if not isinstance(model, QStandardItemModel):
            print("Error: The model is not a QStandardItemModel")
            return

        # Check if the subwindow is valid
        if subwindow is None:
            print("Error: subwindow is None")
            return

        # Locate the file item in the tree
        def find_file_item(model, target_filename):
            for row in range(model.rowCount()):
                item = model.item(row)  # Get item from the top level
                if item and item.text() == target_filename:
                    return item
            return None

        file_item = find_file_item(model, filename)

        if file_item:
            subwindow_title = subwindow.windowTitle()

            # Check if the subwindow already exists under this file node
            for row in range(file_item.rowCount()):
                child_item = file_item.child(row)
                if child_item and child_item.text() == subwindow_title:
                    print(f"Subwindow '{subwindow_title}' already exists in the tree. Skipping.")
                    return  # Skip adding duplicate

            # Create a new tree item for the subwindow
            try:
                subwindow_item = QStandardItem(subwindow_title)
                subwindow_item.setData(subwindow, Qt.UserRole)  # Store reference to subwindow
                subwindow_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

                # Add it as a child of the file
                file_item.appendRow(subwindow_item)

                # Force the UI to refresh
                model.layoutChanged.emit()  # Notify views of structural change
                tree_view.expand(model.indexFromItem(file_item))  # Expand to show new items
                tree_view.update()  # Refresh the tree view explicitly
            except Exception as e:
                print(f"Error while adding subwindow to tree: {e}")



def open_graficos_dock(parent_window, tree_view, mdi_area):
    """Abre o dock widget de ajustes"""
    if not hasattr(parent_window, 'graficos_dock') or parent_window.graficos_dock is None:
        parent_window.graficos_dock = GraficosDock(tree_view, mdi_area, parent_window)
        parent_window.addDockWidget(Qt.RightDockWidgetArea, parent_window.graficos_dock)

    parent_window.graficos_dock.populate_table_columns()  # Refresh column names
    parent_window.graficos_dock.show()
    parent_window.graficos_dock.raise_()
    parent_window.graficos_dock.activateWindow()