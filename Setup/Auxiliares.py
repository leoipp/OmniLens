import pickle
from functools import partial

from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QButtonGroup, QInputDialog, QHBoxLayout, QSpinBox, QGridLayout, QLabel, QDoubleSpinBox, \
    QComboBox, QAbstractItemView, QTableWidgetItem, QMdiSubWindow, QTableWidget, QVBoxLayout, QWidget, QMdiArea, \
    QTextEdit
from PyQt5.QtWidgets import QMenu, QAction, QFileDialog, QTreeView, QFileSystemModel
from PyQt5.QtCore import QDir, Qt, QSettings, QTimer
import os, sys
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from Setup.AjusteDock import open_ajuste_dock
from Setup.GraficosDock import open_graficos_dock


class CustomMdiSubWindow(QMdiSubWindow):
    def closeEvent(self, event):
        """Ao fechar a janela, garante que o objeto seja removido da memória"""
        print(f"Closing window: {self.windowTitle()}")
        self.deleteLater()  # Libera a memória
        event.accept()  # Aceita o fechamento da janela


def resource_path(relative_path):
    """ Retorna o caminho absoluto do recurso, compatível com desenvolvimento e PyInstaller. """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.getcwd()))  # Usa o diretório correto
    return os.path.normpath(os.path.join(base_path, relative_path))


def setup_file_browser(tree_view, opened_subwindows, mdi_area):
    """QTreeView setup file browser"""
    model = QFileSystemModel()
    model.setRootPath('')  # Root system

    # Configuração do TreeView
    tree_view.setModel(model)
    tree_view.setRootIndex(model.index(''))  # Initial root
    tree_view.setSortingEnabled(True)

    # Oculta colunas desnecessárias
    tree_view.hideColumn(1)  # Oculta coluna "Tamanho"
    tree_view.hideColumn(2)  # Oculta coluna "Tipo"
    tree_view.hideColumn(3)  # Oculta coluna "Data de modificação"

    tree_view.setDragEnabled(True)  # Enable dragging from file browser
    tree_view.setSelectionMode(QAbstractItemView.SingleSelection)
    tree_view.setDefaultDropAction(Qt.MoveAction)

    # Habilita o menu de contexto
    tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
    tree_view.customContextMenuRequested.connect(lambda point: show_context_menu(tree_view, point, opened_subwindows, mdi_area))

    # Store model reference to update later
    tree_view.file_model = model


def update_file_browser_root(tree_view, new_root):
    """Update the root directory of the file browser."""
    model = tree_view.model()

    if isinstance(model, QFileSystemModel):
        model.setRootPath(new_root)  # Update the model's root path
        tree_view.setRootIndex(model.index(new_root))


def show_context_menu(tree_view, point, opened_subwindows, mdi_area):
    """Exibe o menu de contexto com a opção de criar uma nova pasta e abrir arquivos"""

    # Obtém o índice do item onde o clique foi feito
    index = tree_view.indexAt(point)
    print(f"Index at point: {index}")  # Debug: Check the index

    # Cria o menu de contexto
    context_menu = QMenu(tree_view)

    # Verifica se o clique foi em um diretório
    if index.isValid() and tree_view.model().isDir(index):
        print(f"Valid directory: {tree_view.model().filePath(index)}")  # Debug: Directory path

        # Adiciona a ação "Criar Nova Pasta"
        create_folder_action = QAction("Criar Nova Pasta", tree_view)
        create_folder_action.triggered.connect(partial(create_new_folder, tree_view, point))
        context_menu.addAction(create_folder_action)

    # Adiciona a ação de 'Abrir Arquivo'
    open_file_action = QAction("Visualizar Arquivo", tree_view)
    open_file_action.triggered.connect(lambda: add_layer_from_file(tree_view, point, opened_subwindows, mdi_area))  # No need for point
    context_menu.addAction(open_file_action)

    # Exibe o menu de contexto
    context_menu.exec_(tree_view.mapToGlobal(point))


def create_new_folder(tree_view, point):
    """Cria uma nova pasta no diretório selecionado"""

    # Obtém o índice do item onde o clique foi feito
    index = tree_view.indexAt(point)
    print(f"Index at point: {index}")  # Debug: Check the index

    # Verifica se o índice é válido e se é um diretório
    if not index.isValid() or not tree_view.model().isDir(index):
        print("Not a valid directory, skipping folder creation.")  # Debug: Not a valid directory
        return  # Skip if not a valid directory or if it's not a directory

    # Obtém o caminho do diretório selecionado
    dir_path = tree_view.model().filePath(index)
    print(f"Creating folder in directory: {dir_path}")  # Debug: Check directory path

    # Abre uma janela para o usuário inserir o nome da nova pasta
    folder_name, ok = QInputDialog.getText(tree_view, "Nome da Nova Pasta", "Digite o nome da pasta:")

    if ok and folder_name:
        new_folder_path = QDir(dir_path).filePath(folder_name)

        # Cria a nova pasta
        if not QDir(new_folder_path).exists():
            QDir().mkdir(new_folder_path)
            print(f"Nova pasta criada: {new_folder_path}")
        else:
            print(f"A pasta {folder_name} já existe.")


def setup_layers_tree(tree_view, mdiArea, opened_subwindows):
    """Setup the Layers tree view to accept dropped files"""
    tree_view.setAcceptDrops(True)
    tree_view.setDragEnabled(False)  # This tree only accepts drops, no dragging
    tree_view.setDropIndicatorShown(True)

    # Set up the model for the tree
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["Layers"])
    tree_view.setModel(model)

    # Override event handlers for drag and drop
    tree_view.dragEnterEvent = lambda event: handle_drag_enter(event)
    tree_view.dragMoveEvent = lambda event: handle_drag_move(event)
    tree_view.dropEvent = lambda event: handle_drop(event, tree_view, mdiArea, opened_subwindows)


def handle_drag_enter(event):
    """Allow drops if the dragged data is a file path"""
    if event.mimeData().hasUrls():
        event.acceptProposedAction()


def handle_drag_move(event):
    """Handles dragging over the target (optional, can be adjusted)"""
    if event.mimeData().hasUrls():
        event.acceptProposedAction()


def handle_drop(event, tree_view, mdi_area, opened_subwindows):
    """Handle the drop event: Add file to layers and open it"""
    mime_data = event.mimeData()

    if mime_data.hasUrls():
        for url in mime_data.urls():
            file_path = url.toLocalFile()
            if file_path.endswith(".xlsx"):  # Ensure only Excel files are handled
                add_layer_file(tree_view, file_path)
                load_excel(file_path, mdi_area, opened_subwindows)  # Open the Excel file in MDI area
        event.acceptProposedAction()


def add_layer_file(tree_view, file_path):
    """Add file to a QStandardItemModel instead of QFileSystemModel"""
    model = tree_view.model()

    # Ensure the model is a QStandardItemModel
    if not isinstance(model, QStandardItemModel):
        print("Error: The model is not a QStandardItemModel")
        return

    # Create the item with the file name
    item = QStandardItem(file_path.split("/")[-1])
    item.setData(file_path, Qt.UserRole)  # Store the full file path in the item data
    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    # Add the item to the root of the model
    model.appendRow(item)

    # Optionally refresh the tree view
    tree_view.update()  # Force the tree view to refresh



def add_layer_from_file(tree_view, point, opened_subwindows, mdi_area):
    """Add a layer from the file clicked in the tree view"""
    # Get the index of the item that was clicked
    index = tree_view.indexAt(point)

    # Get the file path of the item clicked
    file_path = tree_view.model().filePath(index)

    # Check if it's a valid file and ends with .xlsx
    if file_path.endswith(".xlsx"):
        add_layer_file(tree_view, file_path)
        load_excel(file_path, mdi_area, opened_subwindows)
    else:
        print("Only .xlsx files are supported!")


def load_excel(file_path, mdi_area, opened_subwindows):
    """Load and display Excel data in the MDI area"""
    try:
        df = pd.read_excel(file_path)

        # Create the sub-window and set its properties
        sub_window = CustomMdiSubWindow()
        sub_window.setWindowTitle(f"{file_path.split('/')[-1]}")

        # Ensure sub-window respects MDI constraints (critical fix)
        sub_window.setWindowFlags(Qt.SubWindow)  # Force it to act as a sub-window

        # Create a table widget and populate it with the DataFrame
        table_widget = QTableWidget()
        table_widget.setRowCount(df.shape[0])  # Number of rows
        table_widget.setColumnCount(df.shape[1])  # Number of columns
        table_widget.setHorizontalHeaderLabels(df.columns)

        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                table_widget.setItem(row, col, QTableWidgetItem(str(df.iat[row, col])))

        # Set up the layout and container
        layout = QVBoxLayout()
        layout.addWidget(table_widget)
        container = QWidget()
        container.setLayout(layout)

        # Set the container in the sub-window
        sub_window.setWidget(container)

        # Add the sub-window to the MDI area
        mdi_area.addSubWindow(sub_window)

        # Store the sub-window in the opened_subwindows dictionary
        opened_subwindows[file_path] = sub_window

        # Show the sub-window in normal state (no maximizing to avoid escaping MDI area)
        sub_window.show()
        return sub_window

    except Exception as e:
        print(f"Error loading file: {e}")


def open_existing_project(self):
    """Open an existing project folder"""
    project_folder = QFileDialog.getExistingDirectory(self, "Abrir Diretório de Projeto", "")

    if project_folder:
        print(f"Abrindo diretório de projeto existente: {project_folder}")
        self.project_folder = project_folder  # Set the project folder
        update_file_browser_root(self.nav_folder, self.project_folder)
        return project_folder
    else:
        print("Nenhum diretório selecionado.")
        return None


def set_default_layout(self):
    """Ensure the dock widgets are shown and positioned by default."""
    # Make sure the dock widgets are visible in their default positions
    if not self.navegacao.isVisible():
        self.navegacao.setVisible(True)
    if not self.conteudo.isVisible():
        self.conteudo.setVisible(True)

    # Set them to be docked (not floating) by default
    self.navegacao.setFloating(False)
    self.conteudo.setFloating(False)

    self.addDockWidget(Qt.RightDockWidgetArea, self.navegacao)
    self.addDockWidget(Qt.LeftDockWidgetArea, self.conteudo)

    # Optionally, reset any custom positions, sizes, or other settings
    # You could use a fixed default position, if needed, e.g.,:
    # self.main_window.nav_folder.setGeometry(QRect(100, 100, 300, 400))
    print("Default layout restored.")


def setup_second_tree(tree_view, opened_subwindows, mdi_area):
    """Configura a árvore para lidar com o menu de contexto de clique direito,
    permitindo apenas no primeiro nível da árvore."""

    # Garante que a árvore usa um QStandardItemModel
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["Camadas"])
    tree_view.setModel(model)  # Define o modelo correto
    tree_view.setContextMenuPolicy(Qt.CustomContextMenu)

    def show_menu_if_top_level(point):
        """Mostra o menu de contexto apenas se o item for de primeiro nível."""
        index = tree_view.indexAt(point)
        if not index.isValid():
            return  # Nenhum item foi clicado

        item = model.itemFromIndex(index)
        if item and item.parent() is None:  # Apenas itens sem pai (nível 1)
            show_context_menu_second_tree(tree_view, point, opened_subwindows, mdi_area)
        elif item and item.parent() is not None:  # Itens com pai (nível 2)
            show_context_menu_second_tree_subitems(tree_view, point, mdi_area)  # Imprime 'x' quando for um item de segundo nível

    tree_view.customContextMenuRequested.connect(show_menu_if_top_level)

def show_context_menu_second_tree(tree_view, point, opened_subwindows, mdi_area):
    """Exibe o menu de contexto com as opções 'Abrir Tabela', 'Gráfico' e 'Ajustes'"""

    # Get the index of the clicked item
    index = tree_view.indexAt(point)
    print(f"Index at point: {index}")  # Debug: Check the index
    row = index.row()
    print(f"Row: {row}")  # Debug: Check the row

    # Create the main context menu
    context_menu = QMenu(tree_view)

    # 'Abrir Tabela' action
    abrir_tabela_action = QAction("Abrir Tabela", tree_view)
    abrir_tabela_action.triggered.connect(lambda _, idx=index: open_table(idx, opened_subwindows, mdi_area))
    context_menu.addAction(abrir_tabela_action)

    # 'Gráfico' action with a submenu
    grafico_action = QAction("Gráfico", tree_view)

    # Create the submenu for 'Gráfico'
    grafico_submenu = QMenu("Gráficos", tree_view)

    # Add actions to the submenu
    grafico_option1 = QAction("Análise de Dados", tree_view)
    grafico_option2 = QAction("Análise de Modelos", tree_view)

    # Connect each action to corresponding methods (example)
    grafico_option1.triggered.connect(lambda: open_graficos_dock(tree_view.window(), tree_view, mdi_area))
    grafico_option2.triggered.connect(lambda: print("Gráfico Opção 2 Selected"))

    # Add options to the submenu
    grafico_submenu.addAction(grafico_option1)
    grafico_submenu.addAction(grafico_option2)

    # Add the submenu to the main context menu
    context_menu.addMenu(grafico_submenu)

    # 'Ajustes' action
    ajustes_action = QAction("Ajuste", tree_view)
    # Create the submenu for 'Gráfico'
    ajustes_submenu = QMenu("Ajuste", tree_view)

    # Add actions to the submenu
    ajustes_option1 = QAction("Redes Neurais", tree_view)
    ajustes_option2 = QAction("Random Forest", tree_view)

    # Connect each action to corresponding methods (example)
    ajustes_option1.triggered.connect(lambda: open_ajuste_dock(tree_view.window()))
    ajustes_option2.triggered.connect(lambda: print("Gráfico Opção 2 Selected"))

    # Add options to the submenu
    ajustes_submenu.addAction(ajustes_option1)
    ajustes_submenu.addAction(ajustes_option2)

    context_menu.addMenu(ajustes_submenu)

    # Execute the context menu
    context_menu.exec_(tree_view.mapToGlobal(point))

def show_context_menu_second_tree_subitems(tree_view, point, mdi_area):
    """Exibe o menu de contexto com as opções 'Abrir Tabela', 'Gráfico' e 'Ajustes'"""

    # Get the index of the clicked item
    index = tree_view.indexAt(point)
    print(index.data()) #NOME
    print(f"Index at point: {index}")  # Debug: Check the index
    row = index.row()
    print(f"Row: {row}")  # Debug: Check the row

    # Create the main context menu
    context_menu = QMenu(tree_view)
    print(resource_path(index.data()))

    # 'Abrir Tabela' action
    abrir_tabela_action = QAction("Abrir Gráfico", tree_view)
    abrir_tabela_action.triggered.connect(lambda _, idx=index: open_pkl_graph(idx, index.data(),
                                                                              r'G:\PycharmProjects\HGLLEO\pythonProject\Temp\Gráfico de Dispersão - .pkl',
                                                                              mdi_area))
    context_menu.addAction(abrir_tabela_action)

    # Execute the context menu
    context_menu.exec_(tree_view.mapToGlobal(point))

def open_table(index, opened_subwindows, mdi_area):
    """Abre a tabela correspondente ao item selecionado"""
    item_name = index.data()  # Obtém o nome do item selecionado (apenas o nome do arquivo)
    print(f"Index data: {item_name}")  # Para depuração
    print(f"Opened subwindows: {opened_subwindows}")  # Verifique o conteúdo de opened_subwindows
    janelas = [sw.windowTitle() for sw in mdi_area.subWindowList()]
    print(janelas)
    # Verifica se já existe uma subjanela aberta com esse nome
    for sub_window in mdi_area.subWindowList():
        if sub_window.windowTitle() == item_name:  # Comparação correta
            sub_window.showNormal()  # Exibe a subjanela no modo normal
            sub_window.raise_()  # Coloca a subjanela à frente
            return  # Se já estiver aberta, retorna sem abrir outra

    # Caso o arquivo não tenha sido encontrado entre as janelas abertas
    print(f"Opening new table for {item_name}.")

    # Encontra o caminho completo do arquivo no dicionário
    file_path = None
    for path in opened_subwindows.keys():
        if os.path.basename(path) == item_name:
            file_path = path
            break

    if file_path is None:
        print("Erro: Caminho do arquivo não encontrado.")
        return

    print(f"File path: {file_path}")
    load_excel(file_path, mdi_area, opened_subwindows)  # Abre o arquivo no mdi_area


def open_pkl_graph(index, title, file_path, mdi_area):
    """Opens a .pkl graph and displays it in a new MDI subwindow."""
    item_name = index.data()  # Obtém o nome do item selecionado (apenas o nome do arquivo)
    print(f"Index data: {item_name}")  # Para depuração
    janelas = [sw.windowTitle() for sw in mdi_area.subWindowList()]
    print(janelas)
    # Verifica se já existe uma subjanela aberta com esse nome
    for sub_window in mdi_area.subWindowList():
        if sub_window.windowTitle() == item_name:  # Comparação correta
            sub_window.showNormal()  # Exibe a subjanela no modo normal
            sub_window.raise_()  # Coloca a subjanela à frente
            return  # Se já estiver aberta, retorna sem abrir outra

    # Caso o arquivo não tenha sido encontrado entre as janelas abertas
    print(f"Opening new table for {item_name}.")

    try:
        # Load the figure from the pickle file
        with open(file_path, 'rb') as f:
            fig = pickle.load(f)

        # Create a new QMdiSubWindow
        subwindow = CustomMdiSubWindow()
        subwindow.setWindowTitle(f"{title}")

        # Create a widget to contain the plot
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Embed the figure in the widget using Matplotlib's FigureCanvasQTAgg
        canvas = FigureCanvas(fig)  # Correct canvas for PyQt5
        canvas.drwa()
        layout.addWidget(canvas)

        # Set the widget in the subwindow and add it to mdi_area
        subwindow.setWidget(widget)
        mdi_area.addSubWindow(subwindow)
        subwindow.show()
    except Exception as e:
        print(f"Error opening graph from {file_path}: {e}")

def status_bar_message(self, message, timeout=3000):
    """Display a message on the status bar and clear it after a timeout."""
    self.showMessage(message)  # Show the message
    # Create a QTimer to clear the message after the specified timeout (default 3000ms = 3 seconds)
    QTimer.singleShot(timeout, self.clearMessage)