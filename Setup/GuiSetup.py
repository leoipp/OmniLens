import os

from PyQt5 import uic
from Setup.Auxiliares  import setup_file_browser, resource_path, setup_layers_tree, open_existing_project, set_default_layout, setup_second_tree, status_bar_message


class UiSetup:
    __version__ = "Versão: 1.0.1"

    def __init__(self, main_window):
        """
        Initialize UI elements and connect signals.
        """

        self.main_window = main_window
        uic.loadUi(resource_path('./Ui/MainUI.ui'), main_window)

        # Configuração do File Browser
        setup_file_browser(self.main_window.nav_folder, self.main_window.opened_subwindows, self.main_window.mdiArea)
        setup_layers_tree(self.main_window.content, self.main_window.mdiArea, self.main_window.opened_subwindows)
        setup_second_tree(self.main_window.content, self.main_window.opened_subwindows, self.main_window.mdiArea)


        # Configuração de botões
        self.main_window.actionAbrir.triggered.connect(lambda: open_existing_project(self.main_window))
        self.main_window.actionResetar_Layout.triggered.connect(lambda: set_default_layout(self.main_window))

        # Mensagens iniciais
        status_bar_message(self.main_window.statusbar, f'Arandu pronto. Usuário: {os.getlogin()}')

        self.main_window.actiontestebt.triggered.connect(lambda: print([s.windowTitle() for s in self.main_window.mdiArea.subWindowList()]))


