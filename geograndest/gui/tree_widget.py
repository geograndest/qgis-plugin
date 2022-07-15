# -*- coding: utf-8 -*-

from qgis.PyQt.QtWidgets import (
    QTreeWidget,
    QAbstractItemView,
    QTreeWidgetItemIterator,
    QMessageBox,
)
from qgis.PyQt.QtCore import Qt, QByteArray, QDataStream, QIODevice
from qgis.core import (
    Qgis,
    QgsMessageLog,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
)
from qgis.utils import iface

from datagrandest.gui.tree_items import TreeWidgetItem
from datagrandest.utils.plugin_globals import PluginGlobals


class TreeWidget(QTreeWidget):

    # initiate tree widget "state" : True or False for each item depending on wether item is visible or hidden
    # save state for extent filter and text filter
    global tree_state_extent
    global tree_state_text
    tree_state_extent = {}
    tree_state_text = {}

    """
    The tree widget used in the DataGrandEst dock
    """

    def __init__(self):
        objectName = "TreeWidget"

        super(TreeWidget, self).__init__()

        # Selection
        self.setSelectionMode(QAbstractItemView.SingleSelection)

        # Columns and headers
        self.setColumnCount(1)
        self.setHeaderLabel("")
        self.setHeaderHidden(True)

        # Events
        self.itemDoubleClicked.connect(self.tree_item_double_clicked)

        # Context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)

        # Enable drag of tree items
        self.setDragEnabled(True)
        self.setAcceptDrops(True)

    def set_tree_content(self, resources_tree):
        """
        Creates the items of the tree widget
        """

        def create_subitem(subtree, parent_item=self):
            """ """
            subitem = TreeWidgetItem(parent_item, subtree)
            if subtree.children is not None and len(subtree.children) > 0:
                for child in subtree.children:
                    create_subitem(child, subitem)

        self.clear()

        if resources_tree is None:
            QgsMessageLog.logMessage(
                u"Faute de fichier de configuration valide, aucune ressource ne peut être chargée "
                u"dans le panneau de l'extension DataGrandEst.",
                tag=u"DataGrandEst",
                level=Qgis.Warning,
            )
        elif resources_tree.children is not None and len(resources_tree.children) > 0:
            for child in resources_tree.children:
                create_subitem(child, self)

    # QMessageBox.information(None, self.tr('hop'), self.tr('tralala'))

    # show all parents of an item
    def show_parents(self, item):
        # check if item has parent
        if item.parent():
            # show parent if not filtered by extent
            parent = item.parent()
            # update tree state
            #            tree_state_text[parent.text(0)] = True
            tree_state_text[parent.item_data.ident] = True
            # next parent of parent
            self.show_parents(parent)

    # show all children of an item
    def show_children(self, item):
        # check if item has children
        if item.childCount() > 0:
            # show all children if not filtered by extent
            for child_index in range(0, item.childCount()):
                child = item.child(child_index)
                # update tree state
                tree_state_text[child.item_data.ident] = True
                # next children of children
                self.show_children(child)

    # iterate throught items and show them, their parents and children
    # item_type must be folder or layer, else all items will be processed
    # list_of_relations must contain children to show children, parent to show parents
    def iterate_and_show(self, searchtext, item_type, list_of_relations):

        #        # hide all items an update tree state
        #        it = QTreeWidgetItemIterator(self)
        ##        i = 0
        #        while it.value():
        #            item = it.value()
        ##            item.setHidden(True)
        ##            tree_state_text[i] = False
        #            tree_state_text[item.text(0)] = False
        #            it += 1
        ##            i += 1

        # iterate through all items
        it = QTreeWidgetItemIterator(self)
        while it.value():
            item = it.value()
            # item can be a folder or a layer, else no condition
            if item_type == "folder":
                condition = item.childCount() > 0
            elif item_type == "layer":
                condition = item.childCount() == 0
            else:
                condition = True
            # if item is of correct type
            if condition == True:
                # if item has searchtext in its text
                if searchtext.lower() in item.text(0).lower():
                    # update tree state
                    tree_state_text[item.item_data.ident] = True
                    # make its parents visible if wanted
                    if "parents" in list_of_relations:
                        self.show_parents(item)
                    # make its children visible if wanted
                    if "children" in list_of_relations:
                        self.show_children(item)
            it += 1

    def initiates_tree_state(self, filtertype):
        it = QTreeWidgetItemIterator(self)
        while it.value():
            item = it.value()
            if filtertype == "text":
                tree_state_text[item.item_data.ident] = True
            if filtertype == "extent":
                tree_state_extent[item.item_data.ident] = True
            it += 1

    # combine tree state text with tree state extent
    def combine_states(self):
        it = QTreeWidgetItemIterator(self)
        while it.value():
            item = it.value()
            item_state = (
                tree_state_text[item.item_data.ident]
                and tree_state_extent[item.item_data.ident]
            )
            item.setHidden(not item_state)
            it += 1
        self.update_visibility_of_tree_items()

    def filter_by_text(self, searchtext):

        # initiates tree state if not set
        if len(tree_state_text) == 0:
            self.initiates_tree_state("text")

        # set tree state extent if not set
        if len(tree_state_extent) == 0:
            self.initiates_tree_state("extent")

        # no text filter
        if searchtext == "":
            # show all items
            it = QTreeWidgetItemIterator(self)
            while it.value():
                item = it.value()
                tree_state_text[item.item_data.ident] = True
                it += 1
            # folds all folders if no extent filter is set
            if False not in tree_state_extent.values():
                self.collapseAll()

        # text filter
        else:
            # hide all items
            it = QTreeWidgetItemIterator(self)
            while it.value():
                item = it.value()
                tree_state_text[item.item_data.ident] = False
                it += 1

            # simple text filter
            if ":" not in searchtext:
                # iterate through all items, show item and its parents and children if text in item
                self.iterate_and_show(searchtext, "all", ["parents", "children"])

            # search only in folders ("folder_name:")
            elif searchtext.endswith(":"):
                searchtext = searchtext[:-2]
                # iterate through all folders, show folder and its parents and children if text in folder
                self.iterate_and_show(searchtext, "folder", ["parents", "children"])

            # search only in layers (":layer_name")
            elif searchtext.startswith(":"):
                searchtext = searchtext[1:]
                # iterate through all layers, show layer and its parents if text in layer
                self.iterate_and_show(searchtext, "layer", ["parents"])

            # search in folders and layers ("folder_name:layer_name")
            elif ":" in searchtext:
                # folder is the part of searchtext before ':'
                folder = searchtext.split(":")[0]
                # layer is the part of searchtext after 1st ':' (might be multiple ':')
                layer = searchtext.replace(folder + ":", "")
                # iterate through all folders, show folder and its parents and children if text in folder
                self.iterate_and_show(folder, "folder", ["parents", "children"])
                # Should only hide folders, which mean we have to hide all layers
                it = QTreeWidgetItemIterator(self)
                while it.value():
                    item = it.value()
                    if item.childCount() == 0:
                        tree_state_text[item.item_data.ident] = False
                    it += 1
                # iterate through all layers, show layer if text in layer
                self.iterate_and_show(layer, "layer", [])

            # unfold all folders
            self.expandAll()

        # combine tree state text with tree state extent
        self.combine_states()

    # given 2 bboxes as lists : [minx, maxx, miny, maxy]
    # test if the 2 bboxes intersects
    def check_if_intersects(self, bbox1, bbox2):
        intersects = 0
        # test if intersection of xs
        # xmax of bbox1 must be superior to xmin of bbox2
        if bbox1[1] > bbox2[0]:
            # xmin of bbox1 must be inferior to xmax of box2
            if bbox1[0] < bbox2[1]:
                # test if intersection of ys
                # ymax of bbox1 must be superior to ymin of bbox2
                if bbox1[3] > bbox2[2]:
                    # ymin of bbox1 must be inferior to ymax of bbox2
                    if bbox1[2] < bbox2[3]:
                        intersects = 1
        return intersects

    def filter_by_extent(self, currentindex):

        # initiates tree state if not set
        if len(tree_state_extent) == 0:
            self.initiates_tree_state("extent")

        # set tree state text if not set
        if len(tree_state_text) == 0:
            self.initiates_tree_state("text")

        # if "display all layers" is selected
        if currentindex == 0:
            # display all layers
            it = QTreeWidgetItemIterator(self)
            while it.value():
                item = it.value()
                tree_state_extent[item.item_data.ident] = True
                it += 1
            # collapse all folders if no text filter is set
            # if False not in tree_state_text.values():
            # self.collapseAll()

        # if "display layers visible on map" is selected
        if currentindex == 1:
            # get map canvas bbox
            map_extent = iface.mapCanvas().extent()
            # convert canvas bbox to epsg:2154
            sourceCrs = QgsCoordinateReferenceSystem(
                QgsProject.instance().crs().authid()
            )
            destCrs = QgsCoordinateReferenceSystem(2154)
            tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
            map_extent_epsg2154 = tr.transformBoundingBox(map_extent)
            # turns bbox into a list [xmin, xmax, ymin, ymax]
            bbox_map = [
                map_extent_epsg2154.xMinimum(),
                map_extent_epsg2154.xMaximum(),
                map_extent_epsg2154.yMinimum(),
                map_extent_epsg2154.yMaximum(),
            ]
            # expands all folders
            self.expandAll()
            # goes through all items
            it = QTreeWidgetItemIterator(self)
            while it.value():
                item = it.value()
                # update tree state to display all items
                tree_state_extent[item.item_data.ident] = True
                # get current layer list of bounding boxes
                bboxes = item.item_data.bounding_boxes
                # item must be a layer and not a folder
                if bboxes is not None:
                    # test if at least one of the layer's bbox intersects with map canvas bbox
                    intersects = 0
                    for bbox in bboxes:
                        intersects = intersects + self.check_if_intersects(
                            bbox, bbox_map
                        )
                    # hide layer if its bboxes do not intersect with map canvas
                    if intersects == 0:
                        tree_state_extent[item.item_data.ident] = False
                    # show layer if at least one of its bboxes intersects with map canvas
                    else:
                        tree_state_extent[item.item_data.ident] = True
                # next item
                it += 1

        # combine tree state text with tree state extent
        self.combine_states()

    def hide_parent_if_no_visible_child(self, item):
        """
        given a qtreewidgetitem, hide its parent
        if it has no visible children
        """
        # check if item has parent
        if item.parent():
            # check if item siblings are all hidden
            parent = item.parent()
            allHidden = 1
            for sibling_index in range(0, parent.childCount()):
                sibling = parent.child(sibling_index)
                if sibling.isHidden() == False:
                    allHidden = 0
            # if all siblings are hidden
            if allHidden == 1:
                # hide their parent and exit
                parent.setHidden(True)
                return True
            # if at least one sibling is visible, exit
            else:
                return False
        # if item has no parent = is top level, exit
        else:
            return False

    def update_visibility_of_tree_items(self):
        """
        Update the visibility of tree items:
        - visibility of empty groups
        - visibility of items with status = warn
        """
        hide_items_with_warn_status = (
            PluginGlobals.instance().HIDE_RESOURCES_WITH_WARN_STATUS
        )
        hide_empty_groups = PluginGlobals.instance().HIDE_EMPTY_GROUPS

        # iterator for hidden items only
        it = QTreeWidgetItemIterator(self, QTreeWidgetItemIterator.Hidden)
        # for each item
        while it.value():
            item = it.value()
            # hide parent if it has no visible siblings
            parentWasHidden = self.hide_parent_if_no_visible_child(item)
            # if parent was hidden
            while parentWasHidden == True:
                # if parent has a parent
                if item.parent():
                    # hide parent if it has no visible siblings...
                    item = item.parent()
                    parentWasHidden = self.hide_parent_if_no_visible_child(item)
                # if it is a top level item, exit
                else:
                    break

            # next item
            it += 1

        def update_visibility_of_subitems(
            item, hide_empty_groups, hide_items_with_warn_status
        ):

            if (
                hasattr(item, "item_data")
                and item.item_data.status == PluginGlobals.instance().NODE_STATUS_WARN
            ):
                item.setHidden(hide_items_with_warn_status)

            child_count = item.childCount()

            if child_count > 0:
                for i in range(child_count):
                    sub_item = item.child(i)
                    if sub_item.is_an_empty_group():
                        sub_item.setHidden(hide_empty_groups)

                    update_visibility_of_subitems(
                        sub_item, hide_empty_groups, hide_items_with_warn_status
                    )

        update_visibility_of_subitems(
            self.invisibleRootItem(), hide_empty_groups, hide_items_with_warn_status
        )

    def tree_item_double_clicked(self, item, column):
        """
        Handles double clic on an item
        """
        item.run_default_action()

    def open_menu(self, position):
        """
        Handles context menu in the tree
        """
        selected_item = self.currentItem()
        menu = selected_item.create_menu()
        menu.exec_(self.viewport().mapToGlobal(position))

    # Constant and methods used for drag and drop of tree items onto the map

    QGIS_URI_MIME = "application/x-vnd.qgis.qgis.uri"

    def mimeTypes(self):
        """ """
        return [self.QGIS_URI_MIME]

    def mimeData(self, items):
        """ """
        mime_data = QTreeWidget.mimeData(self, items)
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.WriteOnly)

        for item in items:
            layer_mime_data = item.item_data.layer_mime_data()
            stream.writeQString(layer_mime_data)

        mime_data.setData(self.QGIS_URI_MIME, encoded_data)
        return mime_data

    def dropMimeData(self, parent, index, data, action):
        """ """
        if action == Qt.IgnoreAction:
            return True

        return False
