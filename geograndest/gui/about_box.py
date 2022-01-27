# -*- coding: utf-8 -*-

from qgis.PyQt.QtWidgets import QWidget, QDialog, QVBoxLayout, QLabel, QTextBrowser, QFrame
from qgis.PyQt.QtGui import QPixmap

from datagrandest.utils.plugin_globals import PluginGlobals


class AboutBox(QDialog):
    """
    About box of the plugin
    """

    def __init__(self, parent=None):

        QWidget.__init__(self, parent)

        mainLayout = QVBoxLayout()

        logo_file_path = PluginGlobals.instance().logo_file_path
        self.logo = QLabel()
        self.logo.setPixmap(QPixmap(logo_file_path))
        mainLayout.addWidget(self.logo)


        title = u"À propos de l'extension DataGrandEst…"
        description1 = """Extension pour QGIS donnant un accès simplifié aux ressources géographiques de <a href="https://www.datagrandest.fr/">DataGrandEst</a> Version {}<br>""".format(PluginGlobals.instance().PLUGIN_VERSION)
        description2 = """Plus d'informations à l'adresse suivante :<br><a href='{0}'>{0}</a><br>""".format(PluginGlobals.instance().PLUGIN_SOURCE_REPOSITORY)
        description3 = """Merci aux créateurs des plugins <a href="https://github.com/geo2france/idg-qgis3-plugin">Géo2France </a>, <a href="contact@bchartier.net">Benjamin CHARTIER</a>, <a href="https://github.com/geobretagne/qgis-plugin">Géobretagne</a> et <a href="https://gitlab.in2p3.fr/letg/indigeo-for-qgis">Indigéo </a>sur lesquels ce plugin est basé !"""

        self.textArea = QTextBrowser()
#        self.textArea.setTextInteractionFlags(Qt.LinksAccessibleByMouse)
        self.textArea.setOpenExternalLinks(True)
        self.textArea.setReadOnly(True)
        self.textArea.setHtml(description1)
        self.textArea.append(description2)
        self.textArea.append(description3)
        self.textArea.setFrameShape(QFrame.NoFrame)
        mainLayout.addWidget(self.textArea)

        self.setModal(True)
        self.setSizeGripEnabled(False)

        self.setLayout(mainLayout)

        self.setFixedSize(500, 350)
        self.setWindowTitle(title)
