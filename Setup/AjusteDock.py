from PyQt5.QtWidgets import QDockWidget, QToolBox, QWidget, QVBoxLayout, QLabel, QMainWindow, QCheckBox, QSpinBox, \
    QFormLayout, QButtonGroup, QDoubleSpinBox, QComboBox, QGridLayout, QFrame
from PyQt5.QtCore import Qt

class AjusteDock(QDockWidget):
    """Janela flutuante com um QToolBox para ajustes"""
    def __init__(self, parent=None):
        super().__init__("Ajustes de Modelos RNA", parent)

        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFloating(True)  # Permite que o Dock fique independente

        # Criação do QToolBox
        toolbox = QToolBox()

        # Seção Amostragem
        Amostragem_widget = QWidget()
        layout1 = QFormLayout()  # Form Layout para alinhamento correto
        # Widgets de configuração
        self.checkbox_aleatoria = QCheckBox("Amostragem Aleatória")
        self.spin_treinamento = QSpinBox()
        self.spin_validacao = QSpinBox()
        self.checkbox_dados_totais = QCheckBox("Dados Totais")
        # Grupo exclusivo para os checkboxes
        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.checkbox_aleatoria)
        self.button_group.addButton(self.checkbox_dados_totais)
        self.button_group.setExclusive(True)  # Apenas um pode ser selecionado por vez
        # Configuração dos SpinBoxes
        self.spin_treinamento.setValue(70)  # Define valor inicial 70%
        self.spin_treinamento.setRange(1, 99)
        self.spin_validacao.setValue(30)  # Define valor inicial 30%
        self.spin_validacao.setRange(1, 99)
        self.spin_treinamento.valueChanged.connect(self.update_validacao)
        self.spin_validacao.valueChanged.connect(self.update_treinamento)
        # Adiciona os widgets ao layout
        layout1.addRow(self.checkbox_aleatoria)  # Linha para checkbox
        layout1.addRow(QLabel("Treinamento (%):"), self.spin_treinamento)  # Rótulo + SpinBox
        layout1.addRow(QLabel("Validação (%):"), self.spin_validacao)  # Rótulo + SpinBox
        layout1.addRow(self.checkbox_dados_totais)  # Linha para checkbox
        Amostragem_widget.setLayout(layout1)

        # Seção Arquitetura
        arquitetura_widget = QWidget()
        layout2 = QFormLayout()
        # Widgets de configuração
        self.spin_n_camadas_ocultas = QSpinBox()
        self.spin_n_camadas_dropout = QSpinBox()
        self.combobox_funcao_saida = QComboBox()
        self.spin_n_metricas = QSpinBox()
        # Configuração dos SpinBoxes
        self.spin_n_camadas_ocultas.setValue(8)  # Define valor inicial 70%
        self.spin_n_camadas_ocultas.setRange(1, 999)
        self.spin_n_camadas_dropout.setValue(0)  # Define valor inicial 30%
        self.spin_n_camadas_dropout.setRange(0, 999)
        self.spin_n_metricas.setValue(1)  # Define valor inicial 30%
        self.spin_n_metricas.setRange(1, 5)
        # Conectar mudança de valores para atualizar a interface
        self.spin_n_camadas_ocultas.valueChanged.connect(
            lambda: self.update_spin_boxes(self.frame_camadas, self.spin_n_camadas_ocultas.value()))
        self.spin_n_metricas.valueChanged.connect(
            lambda: self.update_spin_boxes(self.frame_camadas, self.spin_n_metricas.value()))
        self.spin_n_camadas_dropout.valueChanged.connect(
            lambda: self.update_spin_boxes(self.frame_dropout, self.spin_n_camadas_dropout.value(), double=True))
        # Frames dinâmicos para os spin boxes
        self.frame_camadas = QFrame()
        self.frame_camadas.setLayout(QGridLayout())
        self.frame_dropout = QFrame()
        self.frame_dropout.setLayout(QGridLayout())
        self.frame_metricas = QFrame()
        self.frame_metricas.setLayout(QGridLayout())
        # Adiciona os widgets ao layout
        layout2.addRow(QLabel("N.º Camadas Ocultas:"), self.spin_n_camadas_ocultas)  # Rótulo + SpinBox
        layout2.addWidget(self.frame_camadas)
        layout2.addRow(QLabel("N.º Camadas Dropout:"), self.spin_n_camadas_dropout)  # Rótulo + SpinBox
        layout2.addWidget(self.frame_dropout)
        layout2.addRow(QLabel("Função de Saída:"), self.combobox_funcao_saida)  # Rótulo + ComboBox
        layout2.addRow(QLabel("N.º Métricas:"), self.spin_n_metricas)  # Rótulo + SpinBox
        layout2.addWidget(self.frame_metricas)
        arquitetura_widget.setLayout(layout2)




        # Seção Amostragem
        otimizadores_widget = QWidget()
        layout2 = QVBoxLayout()
        layout2.addWidget(QCheckBox("Amostragem Aleatória"))
        otimizadores_widget.setLayout(layout2)

        # Seção Amostragem
        loss_widget = QWidget()
        layout2 = QVBoxLayout()
        layout2.addWidget(QCheckBox("Amostragem Aleatória"))
        loss_widget.setLayout(layout2)

        # Seção Amostragem
        callbacks_widget = QWidget()
        layout2 = QVBoxLayout()
        layout2.addWidget(QCheckBox("Amostragem Aleatória"))
        callbacks_widget.setLayout(layout2)

        # Seção Amostragem
        config_widget = QWidget()
        layout2 = QVBoxLayout()
        layout2.addWidget(QCheckBox("Amostragem Aleatória"))
        config_widget.setLayout(layout2)


        # Adiciona as seções ao QToolBox
        toolbox.addItem(Amostragem_widget, "Amostragem")
        toolbox.addItem(arquitetura_widget, "Arquitetura")
        toolbox.addItem(otimizadores_widget, "Otimizadores")
        toolbox.addItem(loss_widget, "Loss")
        toolbox.addItem(callbacks_widget, "Call Backs")
        toolbox.addItem(config_widget, "Configurações de Ajuste")

        # Define o QToolBox como conteúdo do QDockWidget
        self.setWidget(toolbox)

        # Inicializar os spin boxes ao iniciar
        self.update_spin_boxes(self.frame_camadas, self.spin_n_camadas_ocultas.value())
        self.update_spin_boxes(self.frame_metricas, self.spin_n_metricas.value())
        self.update_spin_boxes(self.frame_dropout, self.spin_n_camadas_dropout.value(), double=True)

    def update_validacao(self, value):
        """Atualiza o spin de Validação para manter a soma 100%"""
        self.spin_validacao.blockSignals(True)  # Bloqueia sinal para evitar loop
        self.spin_validacao.setValue(100 - value)
        self.spin_validacao.blockSignals(False)  # Libera sinal

    def update_treinamento(self, value):
        """Atualiza o spin de Treinamento para manter a soma 100%"""
        self.spin_treinamento.blockSignals(True)  # Bloqueia sinal para evitar loop
        self.spin_treinamento.setValue(100 - value)
        self.spin_treinamento.blockSignals(False)  # Libera sinal

    def update_spin_boxes(self, frame, count, double=False):
        """Atualiza os SpinBoxes no frame com rótulos e ComboBox para funções de ativação."""

        activation_functions = ['elu', 'relu', 'sigmoid', 'tanh', 'softmax', 'selu', 'softplus', 'linear']

        # Garantir que o layout existe
        if not frame.layout():
            frame.setLayout(QGridLayout())

        layout = frame.layout()

        # Remover todos os widgets anteriores
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Adicionar novos widgets conforme o número especificado
        row, col = 0, 0
        for i in range(count):
            label = QLabel(f"C{i + 1}:", frame)
            layout.addWidget(label, row, col)

            if not double:
                # Criar ComboBox para funções de ativação
                combo_box = QComboBox(frame)
                combo_box.addItems(activation_functions)
                layout.addWidget(combo_box, row, col + 1)
                col += 2  # Avança 2 colunas
            else:
                col += 1  # Avança apenas 1 para alinhamento do spin box

            if double:
                spin_box = QDoubleSpinBox(frame)
                spin_box.setRange(0, 0.5)
                spin_box.setSingleStep(0.01)
                layout.addWidget(spin_box, row, col + 1)
            else:
                spin_box = QSpinBox(frame)
                spin_box.setRange(0, 100)
                layout.addWidget(spin_box, row, col + 1)

            col += 2  # Avança 2 colunas

            if col >= 6:  # Nova linha a cada 3 elementos
                col = 0
                row += 1

def open_ajuste_dock(parent_window):
    """Abre o dock widget de ajustes"""
    if not hasattr(parent_window, 'ajuste_dock') or parent_window.ajuste_dock is None:
        parent_window.ajuste_dock = AjusteDock(parent_window)
        parent_window.addDockWidget(Qt.RightDockWidgetArea, parent_window.ajuste_dock)

    parent_window.ajuste_dock.show()
    parent_window.ajuste_dock.raise_()
    parent_window.ajuste_dock.activateWindow()
