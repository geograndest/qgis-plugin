# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QWidget,
    QDockWidget,
    QVBoxLayout,
    QLineEdit,
    QComboBox,
    QMessageBox,
)
from qgis.utils import iface

from geograndest.gui.tree_widget import TreeWidget


class DockWidget(QDockWidget):
    """
    The dock widget containing the tree view displaying the DataGrandEst resources
    """

    def __init__(self, parent=None):
        """ """
        super(DockWidget, self).__init__()
        objectName = "SimpleAccessDock"
        self.init_gui()

    def init_gui(self):
        """ """
        self.setWindowTitle(u"DataGrandEst")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # Search bar.
        self.searchbar = QLineEdit()
        self.searchbar.setClearButtonEnabled(True)
        self.searchbar.setToolTip(
            '"texte" pour une recherche dans les noms de dossiers ou de couches \n"texte:" pour une recherche dans les noms de dossiers \n":texte" pour une recherche dans les noms de couches \n"texte:texte" pour combiner les 2'
        )
        self.searchbar.textChanged.connect(self.filter_by_text)

        # combobox to display only visible layers
        self.displayvisible = QComboBox()
        self.displayvisible.setToolTip(
            "Filtrer pour n'afficher que les couches dont l'emprise intersecte l'étendue de la carte"
        )
        self.displayvisible.addItems(
            [
                "Afficher toutes les couches",
                "N'afficher que les couches visibles sur la carte",
            ]
        )
        self.displayvisible.currentIndexChanged.connect(self.filter_by_extent)

        # when map extent changes and display only visible layers is selected, calls filter_by_extent
        # iface.mapCanvas().mapCanvasRefreshed.connect(self.map_extent_changed)
        iface.mapCanvas().extentsChanged.connect(self.map_extent_changed)

        self.treeWidget = TreeWidget()

        self.layout = QVBoxLayout()
        self.layout.setSpacing(2)
        self.layout.setMargin(0)
        self.layout.addWidget(self.searchbar)
        self.layout.addWidget(self.displayvisible)
        self.layout.addWidget(self.treeWidget)

        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setLayout(self.layout)
        self.setWidget(self.dockWidgetContents)

    def set_tree_content(self, resources_tree):
        """
        Creates the items of the tree widget
        """
        self.treeWidget.set_tree_content(resources_tree)
        self.update_visibility_of_tree_items()

    def filter_by_text(self, searchtext):
        """
        Filter the visibility of tree items
        with search bar content
        """
        self.treeWidget.filter_by_text(searchtext)

    def filter_by_extent(self, currentindex):
        """
        Filter the visibility of tree items
        with search bar content
        """
        self.treeWidget.filter_by_extent(currentindex)

    def map_extent_changed(self):
        """
        When map extent is changed,
        update layer list by calling filter_by_extent function
        """
        currentIndex = self.displayvisible.currentIndex()
        self.treeWidget.filter_by_extent(currentIndex)

    def update_visibility_of_tree_items(self):
        """
        Update the visibility of tree items:
        - visibility of empty groups
        - visibility of items with status = warn
        """
        self.treeWidget.update_visibility_of_tree_items()

    def dockStateChanged(self, floating):
        """ """
        if floating:
            self.resize(300, 450)
        else:
            pass
