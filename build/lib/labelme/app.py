# -*- coding: utf-8 -*-

import functools
import html
import math
import os
import os.path as osp
import re
import webbrowser
import threading
import copy
# import ctypes

import imgviz
import natsort
from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy.QtWidgets import QLabel, QListWidgetItem
from keyboard import press

# from win32api import GetSystemMetrics

from labelme import __appname__
from labelme import PY2

from . import utils
from labelme.config import get_config
from labelme.label_file import LabelFile
from labelme.label_file import LabelFileError
from labelme.logger import logger
from labelme.shape import Shape
from labelme.widgets import BrightnessContrastDialog
from labelme.widgets import PolygonTransDialog
from labelme.widgets import Canvas
from labelme.widgets import FileDialogPreview
#from labelme.widgets import LabelDialog
from labelme.widgets import LabelSearchDialog
from labelme.widgets import LabelListWidget
from labelme.widgets import LabelListWidgetItem
from labelme.widgets import ToolBar
from labelme.widgets import UniqueLabelQListWidget
from labelme.widgets import ZoomWidget

from labelme.utils.qt import LogPrint
from labelme.utils.qt import httpReq
from labelme.widgets import DockInPutTitleBar
from labelme.widgets import DockCheckBoxTitleBar
from labelme.widgets import CustomListWidget
from labelme.widgets import MyCustomWidget
from labelme.widgets import CustomLabelListWidget
from labelme.widgets import topToolWidget
from labelme.widgets.pwdDlg import PwdDLG
from labelme.widgets import labelme2coco
from labelme.utils import appFont
from labelme.convert_coco_label import ConvertCoCOLabel

# FIXME
# - [medium] Set max zoom value to something big enough for FitWidth/Window

# TODO(unknown):
# - Zoom is too "steppy".


LABEL_COLORMAP = imgviz.label_colormap()


class MainWindow(QtWidgets.QMainWindow):

    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = 0, 1, 2
    selected_grade = None
    userInfo = {}

    def __init__(
        self,
        config=None,
        filename=None,
        output=None,
        output_file=None,
        output_dir=None,
    ):

        if output is not None:
            logger.warning(
                "argument output is deprecated, use output_file instead"
            )
            if output_file is None:
                output_file = output

        # see labelme/config/default_config.yaml for valid configuration
        if config is None:
            config = get_config()
        self._config = config
        self._polyonList = []
        temp = [{
            "label_display": "미정-미정",
            "label": "미정",
            "grade": "미정",
            "color": "#ff0000"
        }]
        self._polyonList = temp

        # set default shape colors
        Shape.line_color = QtGui.QColor(*self._config["shape"]["line_color"])
        Shape.fill_color = QtGui.QColor(*self._config["shape"]["fill_color"])
        Shape.select_line_color = QtGui.QColor(
            *self._config["shape"]["select_line_color"]
        )
        Shape.select_fill_color = QtGui.QColor(
            *self._config["shape"]["select_fill_color"]
        )
        Shape.vertex_fill_color = QtGui.QColor(
            *self._config["shape"]["vertex_fill_color"]
        )
        Shape.hvertex_fill_color = QtGui.QColor(
            *self._config["shape"]["hvertex_fill_color"]
        )

        # Set point size from config file
        Shape.point_size = self._config["shape"]["point_size"]

        super(MainWindow, self).__init__()

        self.setWindowTitle(__appname__)
        self.setFont(appFont())

        # Whether we need to save or not.
        self.dirty = False
        self._noSelectionSlot = False
        self._copied_shapes = None

        # Main widgets and related state.
        self.labelDialog = LabelSearchDialog(
            text=self.tr("Enter Label for searching"),
            parent=self,
            show_text_field=self._config["show_label_text_field"],
            fit_to_content=self._config["fit_to_content"],
        )


        # grades part ckd
        self.selected_grade = None
        self.grades_dock = self.grades_widget = None
        self.grades_dock = QtWidgets.QDockWidget(self.tr("Grades"), self)

        self.grades_dock.setObjectName("grades")
        self.grade_title_bar = DockInPutTitleBar(self.grades_dock, "gradesbar", self)
        self.grades_dock.setTitleBarWidget(self.grade_title_bar)

        self.grades_widget = CustomListWidget(self, "grades")
        self.grades_dock.setWidget(self.grades_widget)
        #if self._config["grades"]:
        threading.Timer(0.3, self.gradeButtonEvent, args=(True,)).start()

        # products part ckd
        self.selected_product = None
        self.products_dock = self.products_widget = None
        self.products_dock = QtWidgets.QDockWidget(self.tr("Products"), self)

        self.products_dock.setObjectName("products")
        self.products_title_bar = DockInPutTitleBar(self.products_dock, "productsbar", self)
        self.products_dock.setTitleBarWidget(self.products_title_bar)

        self.products_widget = QtWidgets.QListWidget(self)
        self.products_widget.setSpacing(3)
        self.products_widget.setContentsMargins(3, 6, 3, 3)
        self.products_dock.setWidget(self.products_widget)
        self.products_widget.itemChanged.connect(self.setDirty)
        self.products_widget.itemSelectionChanged.connect(
            self.productsSelectionChanged
        )

        self.labelList = CustomLabelListWidget(self)
        self.lastOpenDir = None
        self.labelList.itemSelectionChanged.connect(self.labelSelectionChanged)

        #self.labelList.itemChanged.connect(self.labelItemChanged)
        #self.labelList.itemDoubleClicked.connect(self.editLabel)
        #self.labelList.itemDropped.connect(self.labelOrderChanged)

        self.shape_dock = QtWidgets.QDockWidget(
            self.tr("Polygon Labels"), self

        )

        self.shape_dock.setObjectName("Labels")
        self.customLabelTitleBar = DockCheckBoxTitleBar(self, self.shape_dock)
        self.shape_dock.setTitleBarWidget(self.customLabelTitleBar)
        self.shape_dock.setWidget(self.labelList)

        # top Tool area
        self.selected_shapType = None
        self.topToolWidget = topToolWidget("toptool", self)
        self.topToolbar_dock = QtWidgets.QDockWidget(self.tr("Top bar"), self)
        self.topToolbar_dock.setWidget(self.topToolWidget)
        self.topToolbar_dock.setTitleBarWidget(QtWidgets.QWidget())
        self.topToolWidget.setEnabled(True)


        self.fileSearch = QtWidgets.QLineEdit()
        self.fileSearch.setPlaceholderText(self.tr("Search Filename"))
        self.fileSearch.textChanged.connect(self.fileSearchChanged)
        self.fileListWidget = QtWidgets.QListWidget()
        self.fileListWidget.itemSelectionChanged.connect(
            self.fileSelectionChanged
        )
        fileListLayout = QtWidgets.QVBoxLayout()
        fileListLayout.setContentsMargins(0, 0, 0, 0)
        fileListLayout.setSpacing(0)
        fileListLayout.addWidget(self.fileSearch)
        fileListLayout.addWidget(self.fileListWidget)

        self.file_dock = QtWidgets.QDockWidget(self.tr("File List"), self)
        self.file_dock.setObjectName("Files")
        fileListWidget = QtWidgets.QWidget()
        fileListWidget.setLayout(fileListLayout)
        self.file_dock.setWidget(fileListWidget)

        self.zoomWidget = ZoomWidget()
        self.setAcceptDrops(True)

        self.canvas = self.labelList.canvas = Canvas(
            epsilon=self._config["epsilon"],
            double_click=self._config["canvas"]["double_click"],
            num_backups=self._config["canvas"]["num_backups"],
        )
        self.canvas.zoomRequest.connect(self.zoomRequest)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidget(self.canvas)
        scrollArea.setWidgetResizable(True)
        self.scrollBars = {
            Qt.Vertical: scrollArea.verticalScrollBar(),
            Qt.Horizontal: scrollArea.horizontalScrollBar(),
        }
        self.canvas.scrollRequest.connect(self.scrollRequest)

        self.canvas.newShape.connect(self.newShape)
        self.canvas.shapeMoved.connect(self.setDirty)
        self.canvas.selectionChanged.connect(self.shapeSelectionChanged)
        self.canvas.drawingPolygon.connect(self.toggleDrawingSensitive)

        self.setCentralWidget(scrollArea)


        features = QtWidgets.QDockWidget.DockWidgetFeatures()
        for dock in ["grades_dock", "products_dock", "shape_dock", "file_dock"]:
            if self._config[dock]["closable"]:
                features = features | QtWidgets.QDockWidget.DockWidgetClosable
            if self._config[dock]["floatable"]:
                features = features | QtWidgets.QDockWidget.DockWidgetFloatable
            if self._config[dock]["movable"]:
                features = features | QtWidgets.QDockWidget.DockWidgetMovable

            getattr(self, dock).setFeatures(features)

            if self._config[dock]["show"] is False:
                getattr(self, dock).setVisible(False)


        self._pwdDlg = PwdDLG(self._config, self)

        self.addDockWidget(Qt.TopDockWidgetArea, self.topToolbar_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.grades_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.products_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.shape_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.file_dock)


        # Actions
        action = functools.partial(utils.newAction, self)
        shortcuts = self._config["shortcuts"]
        quit = action(
            self.tr("&Quit"),
            self.close,
            shortcuts["quit"],
            "quit",
            self.tr("Quit application"),
        )
        open_ = action(
            self.tr("&Open"),
            self.openFile,
            shortcuts["open"],
            "open",
            self.tr("Open image or label file"),
        )
        opendir = action(
            self.tr("&Open Dir"),
            self.openDirDialog,
            shortcuts["open_dir"],
            "open",
            self.tr("Open Dir"),
        )
        openNextImg = action(
            self.tr("&Next Image"),
            self.openNextImg,
            shortcuts["open_next"],
            "next",
            self.tr("Open next (hold Ctl+Shift to copy labels)"),
            enabled=False,
        )
        openPrevImg = action(
            self.tr("&Prev Image"),
            self.openPrevImg,
            shortcuts["open_prev"],
            "prev",
            self.tr("Open prev (hold Ctl+Shift to copy labels)"),
            enabled=False,
        )
        save = action(
            self.tr("&Save"),
            self.saveFile,
            shortcuts["save"],
            "save",
            self.tr("Save labels to file"),
            enabled=False,
        )
        saveAs = action(
            self.tr("&Save As"),
            self.saveFileAs,
            shortcuts["save_as"],
            "save-as",
            self.tr("Save labels to a different file"),
            enabled=False,
        )

        deleteFile = action(
            self.tr("&Delete File"),
            self.deleteFile,
            shortcuts["delete_file"],
            "delete",
            self.tr("Delete current label file"),
            enabled=False,
        )

        changeOutputDir = action(
            self.tr("&Change Output Dir"),
            slot=self.changeOutputDirDialog,
            shortcut=shortcuts["save_to"],
            icon="open",
            tip=self.tr("Change where annotations are loaded/saved"),
        )

        saveAuto = action(
            text=self.tr("Save &Automatically"),
            slot=lambda x: self.actions.saveAuto.setChecked(x),
            icon="save",
            tip=self.tr("Save automatically"),
            checkable=True,
            enabled=True,
        )
        saveAuto.setChecked(self._config["auto_save"])

        saveWithImageData = action(
            text="Save With Image Data",
            slot=self.enableSaveImageWithData,
            tip="Save image data in label file",
            checkable=True,
            checked=self._config["store_data"],
        )

        close = action(
            "&Close",
            self.closeFile,
            shortcuts["close"],
            "close",
            "Close current file",
        )

        toggle_keep_prev_mode = action(
            self.tr("Keep Previous Annotation"),
            self.toggleKeepPrevMode,
            shortcuts["toggle_keep_prev_mode"],
            None,
            self.tr('Toggle "keep pevious annotation" mode'),
            checkable=True,
        )
        toggle_keep_prev_mode.setChecked(self._config["keep_prev"])

        createMode = action(
            self.tr("Create Polygons"),
            lambda: self.toggleDrawMode(False, createMode="polygon"),
            shortcuts["create_polygon"],
            "objects",
            self.tr("Start drawing polygons"),
            enabled=False,
        )
        createRectangleMode = action(
            self.tr("Create Rectangle"),
            lambda: self.toggleDrawMode(False, createMode="rectangle"),
            shortcuts["create_rectangle"],
            "objects",
            self.tr("Start drawing rectangles"),
            enabled=False,
        )
        createCircleMode = action(
            self.tr("Create Circle"),
            lambda: self.toggleDrawMode(False, createMode="circle"),
            shortcuts["create_circle"],
            "objects",
            self.tr("Start drawing circles"),
            enabled=False,
        )
        createLineMode = action(
            self.tr("Create Line"),
            lambda: self.toggleDrawMode(False, createMode="line"),
            shortcuts["create_line"],
            "objects",
            self.tr("Start drawing lines"),
            enabled=False,
        )
        createPointMode = action(
            self.tr("Create Point"),
            lambda: self.toggleDrawMode(False, createMode="point"),
            shortcuts["create_point"],
            "objects",
            self.tr("Start drawing points"),
            enabled=False,
        )
        createLineStripMode = action(
            self.tr("Create LineStrip"),
            lambda: self.toggleDrawMode(False, createMode="linestrip"),
            shortcuts["create_linestrip"],
            "objects",
            self.tr("Start drawing linestrip. Ctrl+LeftClick ends creation."),
            enabled=False,
        )
        editMode = action(
            self.tr("Edit Polygons"),
            self.setEditMode,
            shortcuts["edit_polygon"],
            "edit",
            self.tr("Move and edit the selected polygons"),
            enabled=False,
        )

        delete = action(
            self.tr("Delete Polygons"),
            self.deleteSelectedShape,
            shortcuts["delete_polygon"],
            "cancel",
            self.tr("Delete the selected polygons"),
            enabled=False,
        )
        duplicate = action(
            self.tr("Duplicate Polygons"),
            self.duplicateSelectedShape,
            shortcuts["duplicate_polygon"],
            "copy",
            self.tr("Create a duplicate of the selected polygons"),
            enabled=False,
        )
        copy = action(
            self.tr("Copy Polygons"),
            self.copySelectedShape,
            shortcuts["copy_polygon"],
            "copy_clipboard",
            self.tr("Copy selected polygons to clipboard"),
            enabled=False,
        )
        paste = action(
            self.tr("Paste Polygons"),
            self.pasteSelectedShape,
            shortcuts["paste_polygon"],
            "paste",
            self.tr("Paste copied polygons"),
            enabled=False,
        )
        undoLastPoint = action(
            self.tr("Undo last point"),
            self.canvas.undoLastPoint,
            shortcuts["undo_last_point"],
            "undo",
            self.tr("Undo last drawn point"),
            enabled=False,
        )
        removePoint = action(
            text="Remove Selected Point",
            slot=self.removeSelectedPoint,
            shortcut=shortcuts["remove_selected_point"],
            icon="edit",
            tip="Remove selected point from polygon",
            enabled=False,
        )

        undo = action(
            self.tr("Undo"),
            self.undoShapeEdit,
            shortcuts["undo"],
            "undo",
            self.tr("Undo last add and edit of shape"),
            enabled=False,
        )

        hideAll = action(
            self.tr("&Hide\nPolygons"),
            functools.partial(self.togglePolygons, False),
            icon="eye",
            tip=self.tr("Hide all polygons"),
            enabled=False,
        )
        showAll = action(
            self.tr("&Show\nPolygons"),
            functools.partial(self.togglePolygons, True),
            icon="eye",
            tip=self.tr("Show all polygons"),
            enabled=False,
        )

        help = action(
            self.tr("&Help"),
            self.tutorial,
            icon="help",
            tip=self.tr("Show GitHub page"),
        )
        changepwd = action(
            self.tr("&Change Password"),
            self.changePasswordAction,
            icon="chg_pwd",
            tip=self.tr("To change self password")
        )

        zoom = QtWidgets.QWidgetAction(self)
        zoom.setDefaultWidget(self.zoomWidget)
        self.zoomWidget.setWhatsThis(
            str(
                self.tr(
                    "Zoom in or out of the image. Also accessible with "
                    "{} and {} from the canvas."
                )
            ).format(
                utils.fmtShortcut(
                    "{},{}".format(shortcuts["zoom_in"], shortcuts["zoom_out"])
                ),
                utils.fmtShortcut(self.tr("Ctrl+Wheel")),
            )
        )
        self.zoomWidget.setEnabled(False)

        zoomIn = action(
            self.tr("Zoom &In"),
            functools.partial(self.addZoom, 1.1),
            shortcuts["zoom_in"],
            "zoom-in",
            self.tr("Increase zoom level"),
            enabled=False,
        )
        zoomOut = action(
            self.tr("&Zoom Out"),
            functools.partial(self.addZoom, 0.9),
            shortcuts["zoom_out"],
            "zoom-out",
            self.tr("Decrease zoom level"),
            enabled=False,
        )
        zoomOrg = action(
            self.tr("&Original size"),
            functools.partial(self.setZoom, 100),
            shortcuts["zoom_to_original"],
            "zoom",
            self.tr("Zoom to original size"),
            enabled=False,
        )
        keepPrevScale = action(
            self.tr("&Keep Previous Scale"),
            self.enableKeepPrevScale,
            tip=self.tr("Keep previous zoom scale"),
            checkable=True,
            checked=self._config["keep_prev_scale"],
            enabled=True,
        )
        fitWindow = action(
            self.tr("&Fit Window"),
            self.setFitWindow,
            shortcuts["fit_window"],
            "fit-window",
            self.tr("Zoom follows window size"),
            checkable=True,
            enabled=False,
        )
        fitWidth = action(
            self.tr("Fit &Width"),
            self.setFitWidth,
            shortcuts["fit_width"],
            "fit-width",
            self.tr("Zoom follows window width"),
            checkable=True,
            enabled=False,
        )
        brightnessContrast = action(
            "&Brightness Contrast",
            self.brightnessContrast,
            None,
            "color",
            "Adjust brightness and contrast",
            enabled=False,
        )
        # Group zoom controls into a list for easier toggling.
        zoomActions = (
            self.zoomWidget,
            zoomIn,
            zoomOut,
            zoomOrg,
            fitWindow,
            fitWidth,
        )
        self.zoomMode = self.FIT_WINDOW
        fitWindow.setChecked(Qt.Checked)
        self.scalers = {
            self.FIT_WINDOW: self.scaleFitWindow,
            self.FIT_WIDTH: self.scaleFitWidth,
            # Set to one to scale to 100% when loading files.
            self.MANUAL_ZOOM: lambda: 1,
        }

        edit = action(
            self.tr("&Edit Label"),
            self.editLabel,
            shortcuts["edit_label"],
            "edit",
            self.tr("Modify the label of the selected polygon"),
            enabled=False,
        )

        # fill_drawing = action(
        #     self.tr("Fill Drawing Polygon"),
        #     self.canvas.setFillDrawing,
        #     None,
        #     "color",
        #     self.tr("Fill polygon while drawing"),
        #     checkable=True,
        #     enabled=True,
        # )
        # fill_drawing.trigger()

        # Label list context menu.
        labelMenu = QtWidgets.QMenu()
        utils.addActions(labelMenu, (edit, delete))
        utils.addActions(labelMenu, (delete, ))
        self.labelList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.labelList.customContextMenuRequested.connect(
            self.popLabelListMenu
        )

        # Store actions for further handling.
        self.actions = utils.struct(
            saveAuto=saveAuto,
            saveWithImageData=saveWithImageData,
            changeOutputDir=changeOutputDir,
            save=save,
            saveAs=saveAs,
            open=open_,
            close=close,
            deleteFile=deleteFile,
            toggleKeepPrevMode=toggle_keep_prev_mode,
            delete=delete,
            edit=edit,
            duplicate=duplicate,
            copy=copy,
            paste=paste,
            undoLastPoint=undoLastPoint,
            undo=undo,
            removePoint=removePoint,
            createMode=createMode,
            editMode=editMode,
            createRectangleMode=createRectangleMode,
            createCircleMode=createCircleMode,
            createLineMode=createLineMode,
            createPointMode=createPointMode,
            createLineStripMode=createLineStripMode,

            zoom=zoom,
            zoomIn=zoomIn,
            zoomOut=zoomOut,
            zoomOrg=zoomOrg,
            keepPrevScale=keepPrevScale,
            fitWindow=fitWindow,
            fitWidth=fitWidth,
            brightnessContrast=brightnessContrast,
            zoomActions=zoomActions,
            openNextImg=openNextImg,
            openPrevImg=openPrevImg,
            fileMenuActions=(open_, opendir, save, saveAs, close, quit),
            tool=(),
            # XXX: need to add some actions here to activate the shortcut
            editMenu=(
                edit,
                duplicate,
                delete,
                None,
                undo,
                undoLastPoint,
                None,
                removePoint,
                None,
                toggle_keep_prev_mode,
            ),
            # menu shown at right click
            menu=(
                createMode,
                createRectangleMode,
                createCircleMode,
                createLineMode,
                createPointMode,
                createLineStripMode,
                editMode,
                edit,
                duplicate,
                copy,
                paste,
                delete,
                undo,
                undoLastPoint,
                removePoint,
            ),
            onLoadActive=(
                close,
                createMode,
                createRectangleMode,
                createCircleMode,
                createLineMode,
                createPointMode,
                createLineStripMode,
                editMode,
                brightnessContrast,
            ),
            onShapesPresent=(saveAs, hideAll, showAll),
        )

        self.canvas.vertexSelected.connect(self.actions.removePoint.setEnabled)

        self.menus = utils.struct(
            file=self.menu(self.tr("&File")),
            edit=self.menu(self.tr("&Edit")),
            view=self.menu(self.tr("&View")),
            help=self.menu(self.tr("&Help")),
            # lang=self.menu(self.tr("&Language")),
            recentFiles=QtWidgets.QMenu(self.tr("Open &Recent")),
            labelList=labelMenu,
        )

        utils.addActions(
            self.menus.file,
            (
                open_,
                openNextImg,
                openPrevImg,
                opendir,
                self.menus.recentFiles,
                save,
                saveAs,
                saveAuto,
                changeOutputDir,
                saveWithImageData,
                close,
                deleteFile,
                None,
                quit,
            ),
        )
        utils.addActions(self.menus.help, (help, None, changepwd))

        utils.addActions(
            self.menus.view,
            (
                # fill_drawing,
                # None,
                hideAll,
                showAll,
                None,
                self.topToolbar_dock.toggleViewAction(),
                self.grades_dock.toggleViewAction(),
                self.products_dock.toggleViewAction(),
                self.shape_dock.toggleViewAction(),
                self.file_dock.toggleViewAction(),
                None,
                zoomIn,
                zoomOut,
                zoomOrg,
                keepPrevScale,
                None,
                fitWindow,
                fitWidth,
                None,
                brightnessContrast,
            ),
        )

        self.menus.file.aboutToShow.connect(self.updateFileMenu)

        # Custom context menu for the canvas widget:
        utils.addActions(self.canvas.menus[0], self.actions.menu)
        utils.addActions(
            self.canvas.menus[1],
            (
                action("&Copy here", self.copyShape),
                action("&Move here", self.moveShape),
            ),
        )

        self.tools = self.toolbar("Tools")
        # Menu buttons on Left
        self.actions.tool = (
            open_,
            opendir,
            openNextImg,
            openPrevImg,
            save,
            deleteFile,
            None,
            # createMode,
            editMode,
            hideAll,
            showAll,
            duplicate,
            # copy,
            # paste,
            delete,
            undo,
            brightnessContrast,
            None,
            zoom,
            fitWidth,
        )

        # add ckd
        #self.toptools = self.toptoolbar("Top")
        # Menu buttons on Left
        self.statusBar().showMessage(str(self.tr("%s started.")) % __appname__)
        self.statusBar().setFont(appFont())
        self.statusBar().show()

        if output_file is not None and self._config["auto_save"]:
            logger.warn(
                "If `auto_save` argument is True, `output_file` argument "
                "is ignored and output filename is automatically "
                "set as IMAGE_BASENAME.json."
            )
        self.output_file = output_file
        self.output_dir = output_dir

        # Application state.
        self.image = QtGui.QImage()
        self.imagePath = None
        self.recentFiles = []
        self.maxRecent = 7
        self.otherData = None
        self.zoom_level = 100
        self.fit_window = False
        self.zoom_values = {}  # key=filename, value=(zoom_mode, zoom_value)
        self.brightnessContrast_values = {}
        self.polygonTrans_deta_value = 128
        self.polygonTrans_value = 0
        self.scroll_values = {
            Qt.Horizontal: {},
            Qt.Vertical: {},
        }  # key=filename, value=scroll_value

        if filename is not None and osp.isdir(filename):
            self.importDirImages(filename, load=False)
        else:
            self.filename = filename

        if self._config["file_search"]:
            self.fileSearch.setText(self._config["file_search"])
            self.fileSearchChanged()

        # XXX: Could be completely declarative.
        # Restore application settings.
        self.settings = QtCore.QSettings("labelme", "labelme")
        self.recentFiles = self.settings.value("recentFiles", []) or []

        size = self.settings.value("window/size", QtCore.QSize(600, 500))
        # user32 = ctypes.windll.user32
        # size = self.settings.value("window/size", QtCore.QSize(user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)))

        position = self.settings.value("window/position", QtCore.QPoint(0, 0))
        state = self.settings.value("window/state", QtCore.QByteArray())
        self.resize(size)
        self.showMaximized()
        self.move(position)
        # or simply:
        # self.restoreGeometry(settings['window/geometry']
        self.restoreState(state)

        # Populate the File menu dynamically.
        self.updateFileMenu()
        # Since loading the file may take some time,
        # make sure it runs in the background.
        if self.filename is not None:
            self.queueEvent(functools.partial(self.loadFile, self.filename))

        # Callbacks:
        self.zoomWidget.valueChanged.connect(self.paintCanvas)

        self.populateModeActions()
        # self.addRecentFilesToList("first")  # add ckd

    # self.firstStart = True
    # if self.firstStart:
    #    QWhatsThis.enterWhatsThisMode()

    # add recent files
    def addRecentFilesToList(self):
        self.fileListWidget.clear()
        for fname in self.recentFiles:
            extensions = [
                ".%s" % fmt.data().decode().lower()
                for fmt in QtGui.QImageReader.supportedImageFormats()
            ]
            if fname.lower().endswith(tuple(extensions)):
                label_file = osp.splitext(fname)[0] + ".json"
                if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(label_file):
                    item = QtWidgets.QListWidgetItem(fname)
                    self.fileListWidget.addItem(item)
                    # print(fname)
            # print("first recent file : ", fname)



    def menu(self, title, actions=None):
        menu = self.menuBar().addMenu(title)
        menu.setFont(appFont())
        if actions:
            utils.addActions(menu, actions)
        return menu

    def toolbar(self, title, actions=None):
        toolbar = ToolBar(title)
        toolbar.setFont(appFont())
        toolbar.setObjectName("%sToolBar" % title)
        # toolbar.setOrientation(Qt.Vertical)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        if actions:
            utils.addActions(toolbar, actions)
        self.addToolBar(Qt.LeftToolBarArea, toolbar)
        return toolbar

    # add ckd
    def toptoolbar(self, title, actions=None):
        toolbar = ToolBar(title)
        toolbar.setObjectName("%sToolBar" % title)
        # toolbar.setOrientation(Qt.Vertical)
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        if actions:
            utils.addActions(toolbar, actions)
        self.addToolBar(Qt.TopToolBarArea, toolbar)
        return toolbar

    # Support Functions

    def noShapes(self):
        return not len(self.labelList)

    def populateModeActions(self):
        tool, menu = self.actions.tool, self.actions.menu
        self.tools.clear()
        utils.addActions(self.tools, tool)
        self.canvas.menus[0].clear()
        utils.addActions(self.canvas.menus[0], menu)
        self.menus.edit.clear()
        actions = (
            self.actions.createMode,
            self.actions.createRectangleMode,
            self.actions.createCircleMode,
            self.actions.createLineMode,
            self.actions.createPointMode,
            self.actions.createLineStripMode,
            self.actions.editMode,
        )
        utils.addActions(self.menus.edit, actions + self.actions.editMenu)


    def setvisibilityChange(self):
        print("setvisibilityChange")

    def setDirty(self):
        # Even if we autosave the file, we keep the ability to undo
        self.actions.undo.setEnabled(self.canvas.isShapeRestorable)

        if self._config["auto_save"] or self.actions.saveAuto.isChecked():
            label_file = osp.splitext(self.imagePath)[0] + ".json"
            if self.output_dir:
                label_file_without_path = osp.basename(label_file)
                label_file = osp.join(self.output_dir, label_file_without_path)
            self.saveLabels(label_file)
            return
        self.dirty = True
        self.actions.save.setEnabled(True)
        title = __appname__
        if self.filename is not None:
            title = "{} - {}*".format(title, self.filename)
        self.setWindowTitle(title)

    def setClean(self):
        self.dirty = False
        self.actions.save.setEnabled(False)
        self.actions.createMode.setEnabled(True)
        self.actions.createRectangleMode.setEnabled(True)
        self.actions.createCircleMode.setEnabled(True)
        self.actions.createLineMode.setEnabled(True)
        self.actions.createPointMode.setEnabled(True)
        self.actions.createLineStripMode.setEnabled(True)
        title = __appname__
        if self.filename is not None:
            title = "{} - {}".format(title, self.filename)
        self.setWindowTitle(title)

        if self.hasLabelFile():
            self.actions.deleteFile.setEnabled(True)
        else:
            self.actions.deleteFile.setEnabled(False)

    def toggleActions(self, value=True):
        """Enable/Disable widgets which depend on an opened image."""
        for z in self.actions.zoomActions:
            z.setEnabled(value)
        for action in self.actions.onLoadActive:
            action.setEnabled(value)

    def queueEvent(self, function):
        QtCore.QTimer.singleShot(0, function)

    def status(self, message, delay=5000):
        self.statusBar().showMessage(message, delay)

    def resetState(self):
        self.labelList.clear()  # this block now when polygon list is deleted
        # update polygon count ckd
        prodT = "Polygon Labels (Total %s)"
        if self._config["local_lang"] == "ko_KR":
            prodT = "다각형 레이블 (총 %s)"
        self.shape_dock.titleBarWidget().titleLabel.setText(prodT % self.labelList.count())

        self.filename = None
        self.imagePath = None
        self.imageData = None
        self.labelFile = None
        self.otherData = None
        self.canvas.resetState()

    # delete simply
    def resetSimplyState(self):
        self.labelList.clear()  # this block now when polygon list is deleted
        # update polygon count ckd
        prodT = "Polygon Labels (Total %s)"
        if self._config["local_lang"] == "ko_KR":
            prodT = "다각형 레이블 (총 %s)"
        self.shape_dock.titleBarWidget().titleLabel.setText(prodT % self.labelList.count())
        self.labelFile = None
        self.otherData = None
        self.canvas.shapes = []
        self.canvas.shapesBackups = []
        self.canvas.restoreCursor()
        self.canvas.update()
        self.actions.deleteFile.setEnabled(False)
        self.setDirty()
        if self.noShapes():
            for action in self.actions.onShapesPresent:
                action.setEnabled(False)

    def currentItem(self):
        items = self.labelList.selectedItems()
        if items:
            return items[0]
        return None

    def addRecentFile(self, filename):
        if filename in self.recentFiles:
            self.recentFiles.remove(filename)
        elif len(self.recentFiles) >= self.maxRecent:
            self.recentFiles.pop()
        self.recentFiles.insert(0, filename)

    # Callbacks

    def undoShapeEdit(self):
        self.canvas.restoreShape()
        self.labelList.clear()
        self.loadShapes(self.canvas.shapes)
        self.actions.undo.setEnabled(self.canvas.isShapeRestorable)

    def tutorial(self):
        url = "https://github.com/kingntop/labelme"  # NOQA
        webbrowser.open(url)

    def changePasswordAction(self):
        status = self._pwdDlg.popUpDlg()
        print("status of change pwd is %s" % status)


    def toggleDrawingSensitive(self, drawing=True):
        """Toggle drawing sensitive.
        In the middle of drawing, toggling between modes should be disabled.
        """
        self.actions.editMode.setEnabled(not drawing)
        self.actions.undoLastPoint.setEnabled(drawing)
        self.actions.undo.setEnabled(not drawing)
        self.actions.delete.setEnabled(not drawing)

    def toggleDrawMode(self, edit=True, createMode="polygon"):
        self.canvas.setEditing(edit)
        self.canvas.createMode = createMode
        if edit:
            self.actions.createMode.setEnabled(True)
            self.actions.createRectangleMode.setEnabled(True)
            self.actions.createCircleMode.setEnabled(True)
            self.actions.createLineMode.setEnabled(True)
            self.actions.createPointMode.setEnabled(True)
            self.actions.createLineStripMode.setEnabled(True)

            self.topToolWidget.editmodeClick(True)
        else:
            if createMode == "polygon":
                self.actions.createMode.setEnabled(False)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)

                self.topToolWidget.eventFromMenu(createMode)
            elif createMode == "rectangle":
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(False)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)

                self.topToolWidget.eventFromMenu(createMode)
            elif createMode == "line":
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(False)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)

                self.topToolWidget.eventFromMenu(createMode)
            elif createMode == "point":
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(False)
                self.actions.createLineStripMode.setEnabled(True)

                self.topToolWidget.eventFromMenu(createMode)
            elif createMode == "circle":
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(False)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)

                self.topToolWidget.eventFromMenu(createMode)
            elif createMode == "linestrip":
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(False)

                self.topToolWidget.eventFromMenu(createMode)
            else:
                raise ValueError("Unsupported createMode: %s" % createMode)
        self.actions.editMode.setEnabled(not edit)

    def setEditMode(self):
        self.toggleDrawMode(True)

    def updateFileMenu(self):
        current = self.filename

        def exists(filename):
            return osp.exists(str(filename))

        menu = self.menus.recentFiles
        menu.clear()
        files = [f for f in self.recentFiles if f != current and exists(f)]
        for i, f in enumerate(files):
            icon = utils.newIcon("labels")
            action = QtWidgets.QAction(
                icon, "&%d %s" % (i + 1, QtCore.QFileInfo(f).fileName()), self
            )
            action.triggered.connect(functools.partial(self.loadRecent, f))
            menu.addAction(action)

    def popLabelListMenu(self, point):
        self.menus.labelList.exec_(self.labelList.mapToGlobal(point))

    def validateLabel(self, label):
        # no validation
        if self._config["validate_label"] is None:
            return True

        return False

    def editLabels(self):
        if len(self._polyonList) < 1:
            return self.errorMessage(self.tr("Wrong Empty label"),
                                     self.tr("please select one grade for label in Grade list"))
        if not self.canvas.editing():
            return

        polyitems = copy.deepcopy(self._polyonList)

        f_item = self.labelList.selectedItems()[0]
        f_shape = None
        if isinstance(f_item, QListWidgetItem):
            f_shape_item = self.labelList.itemWidget(f_item)
            if f_shape_item:
                f_shape = f_shape_item._shape

        if f_shape is None:
            return

        old_color = f_shape.color
        assert isinstance(old_color, QtGui.QColor)

        ritem = self.labelDialog.popUpLabelDlg(polyitems, f_shape, "edit")
        if ritem is None:
            return
        if not self.validateLabel(ritem["label"]):
            self.errorMessage(
                self.tr("Invalid label"),
                self.tr("Invalid label '{}' with validation type '{}'").format(
                    ritem["label"], self._config["validate_label"]
                ),
            )
            return

        label = ritem["label"]
        label_display = ritem["label_display"]
        grade = ritem["grade"]
        color = ritem["color"]


        for item in self.labelList.selectedItems():
            if isinstance(item, QListWidgetItem):
                shape_item = self.labelList.itemWidget(item)
                if shape_item:
                    shape = shape_item._shape
                    if shape is None:
                        continue
                    shape.label = label
                    shape.label_display = label_display
                    shape.grade = grade
                    #shape.color = color
                    old_a = old_color.alpha()

                    sc = color if color else "#808000"
                    Qc = QtGui.QColor(sc)
                    r, g, b, a = Qc.red(), Qc.green(), Qc.blue(), Qc.alpha()
                    shape.color = QtGui.QColor(r, g, b, old_a)

                    self._update_shape_color(shape)
                    if shape_item:
                        if shape_item.label:
                            shape_item.label.setText("#{}  {}".format(shape_item._id, shape.label_display))
                            cls_txt = shape.color.name(QtGui.QColor.HexRgb)
                            shape_item.clrlabel.setStyleSheet(
                                "QLabel{border: 1px soild #aaa; background: %s;}" % cls_txt)

        self.setDirty()


    def editLabel(self, item=None):
        if len(self.labelList.selectedItems()) > 1:
            self.editLabels()
            return

        if item and not isinstance(item, CustomLabelListWidget):
            raise TypeError("item must be CustomLabelListWidget type")

        if len(self._polyonList) < 1:
            return self.errorMessage(self.tr("Wrong Empty label"),
                                     self.tr("please select one grade for label in Grade list"))

        if not self.canvas.editing():
            return
        if not item:
            item = self.currentItem()
        if item is None:
            return
        shape = None
        shape_item = None
        if isinstance(item, QListWidgetItem):
            shape_item = self.labelList.itemWidget(item)
            if shape_item:
                shape = shape_item._shape
        if shape is None:
            return
        old_color = shape.color
        assert isinstance(old_color, QtGui.QColor)

        polyitems = copy.deepcopy(self._polyonList)
        ritem = self.labelDialog.popUpLabelDlg(polyitems, shape, "edit")
        if ritem is None:
            return
        if not self.validateLabel(ritem["label"]):
            self.errorMessage(
                self.tr("Invalid label"),
                self.tr("Invalid label '{}' with validation type '{}'").format(
                    ritem["label"], self._config["validate_label"]
                ),
            )
            return

        shape.label = ritem["label"]
        shape.label_display = ritem["label_display"]
        shape.grade = ritem["grade"]
        shape.color = ritem["color"]

        old_a = old_color.alpha()

        sc = shape.color if shape.color else "#808000"
        Qc = QtGui.QColor(sc)
        r, g, b, a = Qc.red(), Qc.green(), Qc.blue(), Qc.alpha()
        shape.color = QtGui.QColor(r, g, b, old_a)

        self._update_shape_color(shape)
        # update label
        if shape_item:
            if shape_item.label:
                shape_item.label.setText("#{}  {}".format(shape_item._id, shape.label_display))
                cls_txt = shape.color.name(QtGui.QColor.HexRgb)
                shape_item.clrlabel.setStyleSheet(
                    "QLabel{border: 1px soild #aaa; background: %s;}" % cls_txt)


        self.setDirty()

    def fileSearchChanged(self):
        self.importDirImages(
            self.lastOpenDir,
            pattern=self.fileSearch.text(),
            load=False,
        )

    # no using
    def productsSelectionChanged(self):
        items = self.products_widget.selectedItems()
        if not items:
            return
        item = items[0]
        #print(str(item.text()))
        self.selected_product = item.text()

    def fileSelectionChanged(self):
        items = self.fileListWidget.selectedItems()
        if not items:
            return
        item = items[0]

        if not self.mayContinue():
            return

        currIndex = self.imageList.index(str(item.text()))
        if currIndex < len(self.imageList):
            filename = self.imageList[currIndex]
            if filename:
                self.loadFile(filename)

    # React to canvas signals.
    def shapeSelectionChanged(self, selected_shapes):
        self._noSelectionSlot = True
        for shape in self.canvas.selectedShapes:
            shape.selected = False
        self.labelList.clearSelection()
        self.canvas.selectedShapes = selected_shapes
        for shape in self.canvas.selectedShapes:
            shape.selected = True
            item = self.labelList.findItemByShape(shape)
            if item:
                self.labelList.selectItem(item)
                self.labelList.scrollTooItem(item)
        self._noSelectionSlot = False
        n_selected = len(selected_shapes)
        self.actions.delete.setEnabled(n_selected)
        self.actions.duplicate.setEnabled(n_selected)
        self.actions.copy.setEnabled(n_selected)
        # self.actions.edit.setEnabled(n_selected == 1) # edit for single
        self.actions.edit.setEnabled(n_selected)  # add ckd 9/7/2022

    def addLabel(self, shape):
        # Add polygon list
        self.labelList.addShape(shape)
        self.labelDialog.addLabelHistory(shape)
        for action in self.actions.onShapesPresent:
            action.setEnabled(True)

        self._update_shape_color(shape)
        # update polygon count ckd
        prodT = "Polygon Labels (Total %s)"
        if self._config["local_lang"] == "ko_KR":
            prodT = "다각형 레이블 (총 %s)"
        self.shape_dock.titleBarWidget().titleLabel.setText(prodT % self.labelList.count())

    def _update_shape_color(self, shape):
        sc = shape.color if shape.color else "#808000"
        Qc = QtGui.QColor(sc)
        r, g, b, a = Qc.red(), Qc.green(), Qc.blue(), Qc.alpha()
        shape.color = QtGui.QColor(r, g, b, a)
        la = int(a * 255 / 128)
        shape.line_color = QtGui.QColor(r, g, b, la)
        shape.vertex_fill_color = QtGui.QColor(r, g, b, a)
        shape.hvertex_fill_color = QtGui.QColor(255, 255, 255)
        shape.fill_color = QtGui.QColor(r, g, b, a)  # a=128
        shape.select_line_color = QtGui.QColor(255, 255, 255, a + 80)
        shape.select_fill_color = QtGui.QColor(r, g, b, a + 27)  # a = 155

    def _get_rgb_by_label(self, label):
        if self._config["shape_color"] == "auto":
            item = self.uniqLabelList.findItemsByLabel(label)[0]
            label_id = self.uniqLabelList.indexFromItem(item).row() + 1
            label_id += self._config["shift_auto_shape_color"]
            return LABEL_COLORMAP[label_id % len(LABEL_COLORMAP)]
        elif (
            self._config["shape_color"] == "manual"
            and self._config["label_colors"]
            and label in self._config["label_colors"]
        ):
            return self._config["label_colors"][label]
        elif self._config["default_shape_color"]:
            return self._config["default_shape_color"]
        return (0, 255, 0)

    def remLabels(self, shapes):
        for shape in shapes:
            item = self.labelList.findItemByShape(shape)
            if item:
                self.labelList.removeItem(item)

        self.labelList.reSort()

    def loadShapes(self, shapes, replace=True):
        self._noSelectionSlot = True
        for shape in shapes:
            self.addLabel(shape)
        self.labelList.clearSelection()
        self._noSelectionSlot = False
        self.canvas.loadShapes(shapes, replace=replace)

    def loadLabels(self, shapes):
        s = []
        inval = False
        for shape in shapes:
            try:
                grade = shape["grade"]
            except AttributeError:
                grade = shape["label"]

            try:
                label_display = shape["label_display"]
            except AttributeError:
                label_display = shape["label"]

            label = shape["label"]
            color = shape["color"]
            points = shape["points"]
            shape_type = shape["shape_type"]
            group_id = shape["group_id"]
            other_data = shape["other_data"]

            Qc = QtGui.QColor(color)
            r, g, b, a = Qc.red(), Qc.green(), Qc.blue(), Qc.alpha()
            # print("load shape", str(a))
            if inval is False:
                if a >= self.polygonTrans_deta_value:
                    self.polygonTrans_value = 0
                else:
                    self.polygonTrans_value = self.polygonTrans_deta_value - a
                inval = True

            color = QtGui.QColor(r, g, b, a if a < self.polygonTrans_deta_value else self.polygonTrans_deta_value)

            if not points:
                # skip point-empty shape
                continue

            shape = Shape(
                self,
                grade=grade,
                label=label,
                label_display=label_display,
                color=color,
                shape_type=shape_type,
                group_id=group_id,
            )
            for x, y in points:
                shape.addPoint(QtCore.QPointF(x, y))
            shape.close()

            shape.other_data = other_data
            s.append(shape)
        self.loadShapes(s)

    def loadGrades(self, items):
        self.grades_widget.clear()
        for i in range(len(items)):
            itm = items[i]
            item = QtWidgets.QListWidgetItem(itm["grade"])
            # item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            # item.setCheckState(Qt.Checked if flag else Qt.Unchecked)
            self.grades_widget.addItem(item)

    def loadProducts(self, items):
        self.products_widget.clear()
        for i in range(len(items)):
            itm = items[i]
            item = QtWidgets.QListWidgetItem(itm["product"])
            item.setFont(appFont())
            # item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            # item.setCheckState(Qt.Checked if flag else Qt.Unchecked)
            self.products_widget.addItem(item)
        if self._config["local_lang"] == "ko_KR":
            self.products_title_bar.titleLabel.setText("대표 품목 (총 %s)" % self.products_widget.__len__())
        else:
            self.products_title_bar.titleLabel.setText("Products (Total %s)" % self.products_widget.__len__())


    def addProduct(self, new_str):
        item = QtWidgets.QListWidgetItem(new_str)
        item.setFont(appFont())
        self.products_widget.insertItem(0, item)
        if self._config["local_lang"] == "ko_KR":
            self.products_title_bar.titleLabel.setText("대표 품목 (총 %s)" % self.products_widget.__len__())
        else:
            self.products_title_bar.titleLabel.setText("Products (Total %s)" % self.products_widget.__len__())


    def saveLabels(self, filename):
        lf = LabelFile()

        def format_shape(s):
            data = s.other_data.copy()
            grade = s.grade.encode("utf-8") if PY2 else s.grade
            label_display = s.label_display.encode("utf-8") if PY2 else s.label_display
            label = s.label.encode("utf-8") if PY2 else s.label

            cColor = QtGui.QColor(s.color if s.color else "#808000")
            # r, g, b, a = cColor.red(), cColor.green(), cColor.blue(), cColor.alpha()
            #print("save shape", str(a))

            cnams_str = cColor.name(QtGui.QColor.HexArgb)
            data.update(
                dict(
                    grade=grade,
                    label=label,
                    label_display=label_display,
                    color=cnams_str,
                    points=[(p.x(), p.y()) for p in s.points],
                    shape_type=s.shape_type,
                    group_id=s.group_id
                )
            )
            return data

        shapes = [format_shape(item._shape) for item in self.labelList.getShapeItems()]
        try:
            imagePath = osp.relpath(self.imagePath, osp.dirname(filename))
            imageData = self.imageData if self._config["store_data"] else None
            if osp.dirname(filename) and not osp.exists(osp.dirname(filename)):
                os.makedirs(osp.dirname(filename))
            lf.save(
                filename=filename,
                shapes=shapes,
                imagePath=imagePath,
                imageData=imageData,
                imageHeight=self.image.height(),
                imageWidth=self.image.width(),
                otherData=self.otherData,
            )
            self.labelFile = lf
            items = self.fileListWidget.findItems(
                self.imagePath, Qt.MatchExactly
            )
            if len(items) > 0:
                if len(items) != 1:
                    raise RuntimeError("There are duplicate files.")
                items[0].setCheckState(Qt.Checked)
            # disable allows next and previous image to proceed
            # self.filename = filename
            return True
        except LabelFileError as e:
            self.errorMessage(
                self.tr("Error saving label data"), self.tr("<b>%s</b>") % e
            )
            return False

    def duplicateSelectedShape(self):
        added_shapes = self.canvas.duplicateSelectedShapes()
        self.labelList.clearSelection()
        for shape in added_shapes:
            self.addLabel(shape)
        self.setDirty()

    def pasteSelectedShape(self):
        self.loadShapes(self._copied_shapes, replace=False)
        self.setDirty()

    def copySelectedShape(self):
        self._copied_shapes = [s.copy() for s in self.canvas.selectedShapes]
        self.actions.paste.setEnabled(len(self._copied_shapes) > 0)

    def labelSelectionChanged(self):
        if self._noSelectionSlot:
            return
        if self.canvas.editing():
            selected_shapes = []
            for item in self.labelList.selectedItems():
                if isinstance(item, QListWidgetItem):
                    _item = self.labelList.itemWidget(item)
                    selected_shapes.append(_item._shape)
            if selected_shapes:
                self.canvas.selectShapes(selected_shapes)
            else:
                self.canvas.deSelectShape()

    def labelItemChanged(self, item):
        shape = item._shape
        if shape:
            self.canvas.setShapeVisible(shape, item._checked)

    def labelOrderChanged(self):
        self.setDirty()
        self.canvas.loadShapes([item._shape for item in self.labelList.getItems()])

    # Callback functions:

    def newShape(self):
        #items = self._polyonList[:]
        items = copy.deepcopy(self._polyonList)
        if len(items) < 1:
            self.canvas.shapes.pop()
            self.canvas.repaint()
            return self.errorMessage(self.tr("Wrong Empty label"), self.tr("please select one grade for label in Grade list"))

        group_id = None
        item = None
        if self._config["display_label_popup"]:
            previous_text = self.labelDialog.edit.text()
            item = self.labelDialog.popUpLabelDlg(items)
            if not item:
                self.labelDialog.edit.setText(previous_text)

        if item and not self.validateLabel(item["label"]):
            self.errorMessage(
                self.tr("Invalid label"),
                self.tr("Invalid label '{}' with validation type '{}'").format(
                    item["label"], self._config["validate_label"]
                ),
            )
            item = None
        if item:
            self.labelList.clearSelection()
            shape = self.canvas.setLastLabel(item)

            shape.group_id = group_id
            sc = shape.color if shape.color else "#808000"
            Qc = QtGui.QColor(sc)
            r, g, b, a = Qc.red(), Qc.green(), Qc.blue(), Qc.alpha()
            shape.color = QtGui.QColor(r, g, b, a)
            if self.polygonTrans_value > 0:
                a = self.polygonTrans_deta_value - self.polygonTrans_value
            else:
                a = self.polygonTrans_deta_value
            shape.color = QtGui.QColor(r, g, b, a)
            # print("new shape", str(a))

            self.addLabel(shape)
            self.actions.editMode.setEnabled(True)
            self.actions.undoLastPoint.setEnabled(False)
            self.actions.undo.setEnabled(True)
            self.setDirty()
        else:
            self.canvas.undoLastLine()
            self.canvas.shapesBackups.pop()

    def scrollRequest(self, delta, orientation):
        units = -delta * 0.1  # natural scroll
        bar = self.scrollBars[orientation]
        value = bar.value() + bar.singleStep() * units
        self.setScroll(orientation, value)

    def setScroll(self, orientation, value):
        self.scrollBars[orientation].setValue(value)
        self.scroll_values[orientation][self.filename] = value

    def setZoom(self, value):
        self.actions.fitWidth.setChecked(False)
        self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.MANUAL_ZOOM
        self.zoomWidget.setValue(value)
        self.zoom_values[self.filename] = (self.zoomMode, value)

    def addZoom(self, increment=1.1):
        zoom_value = self.zoomWidget.value() * increment
        if increment > 1:
            zoom_value = math.ceil(zoom_value)
        else:
            zoom_value = math.floor(zoom_value)
        self.setZoom(zoom_value)

    def zoomRequest(self, delta, pos):
        canvas_width_old = self.canvas.width()
        units = 1.1
        if delta < 0:
            units = 0.9
        self.addZoom(units)

        canvas_width_new = self.canvas.width()
        if canvas_width_old != canvas_width_new:
            canvas_scale_factor = canvas_width_new / canvas_width_old

            x_shift = round(pos.x() * canvas_scale_factor) - pos.x()
            y_shift = round(pos.y() * canvas_scale_factor) - pos.y()

            self.setScroll(
                Qt.Horizontal,
                self.scrollBars[Qt.Horizontal].value() + x_shift,
            )
            self.setScroll(
                Qt.Vertical,
                self.scrollBars[Qt.Vertical].value() + y_shift,
            )

    def setFitWindow(self, value=True):
        if value:
            self.actions.fitWidth.setChecked(False)
        self.zoomMode = self.FIT_WINDOW if value else self.MANUAL_ZOOM
        self.adjustScale()

    def setFitWidth(self, value=True):
        if value:
            self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.FIT_WIDTH if value else self.MANUAL_ZOOM
        self.adjustScale()

    def enableKeepPrevScale(self, enabled):
        self._config["keep_prev_scale"] = enabled
        self.actions.keepPrevScale.setChecked(enabled)

    def onNewBrightnessContrast(self, qimage):
        self.canvas.loadPixmap(
            QtGui.QPixmap.fromImage(qimage), clear_shapes=False
        )

    def brightnessContrast(self, value):
        dialog = BrightnessContrastDialog(
            utils.img_data_to_pil(self.imageData),
            self.onNewBrightnessContrast,
            parent=self,
        )
        brightness, contrast = self.brightnessContrast_values.get(
            self.filename, (None, None)
        )
        if brightness is not None:
            dialog.slider_brightness.setValue(brightness)
        if contrast is not None:
            dialog.slider_contrast.setValue(contrast)
        dialog.exec_()

        brightness = dialog.slider_brightness.value()
        contrast = dialog.slider_contrast.value()
        self.brightnessContrast_values[self.filename] = (brightness, contrast)


    def PolygonAlpha(self, transObj):
        self.polygonAlphaDlg = PolygonTransDialog(
            self.polygonTrans,
            parent=self,
        )
        if self.polygonTrans_value:
            self.polygonAlphaDlg.slider_trans.setValue(self.polygonTrans_value)
        self.polygonAlphaDlg.exec_()

        val = self.polygonAlphaDlg.slider_trans.value()
        self.polygonTrans_value = val
        transObj.setEnabled(True)
        self.actions.save.setEnabled(True)


    def polygonTrans(self, value):
        if self.canvas.shapes and len(self.canvas.shapes) < 1:
            return

        for shape in self.canvas.shapes:
            Qc = QtGui.QColor(shape.color)
            r, g, b, a = Qc.red(), Qc.green(), Qc.blue(), Qc.alpha()
            alpha = self.polygonTrans_deta_value - value
            shape.color = QtGui.QColor(r, g, b, alpha)
            # shape.line_color = QtGui.QColor(r, g, b, alpha + 50)
            # shape.fill_color = QtGui.QColor(r, g, b, alpha)
            # shape.vertex_fill_color = QtGui.QColor(r, g, b, alpha + 50)
            # shape.hvertex_fill_color = QtGui.QColor(255, 255, 255)
            # shape.select_line_color = QtGui.QColor(255, 255, 255, alpha + 50)
            # shape.select_fill_color = QtGui.QColor(r, g, b, alpha + 27)  # a = 155
            self._update_shape_color(shape)

        self.canvas.update()


    def togglePolygons(self, value):
        self.labelList.checkStatus(1 if value else 0)

    def loadFile(self, filename=None):
        """Load the specified file, or the last opened file if None."""
        # changing fileListWidget loads file
        if filename in self.imageList and (
            self.fileListWidget.currentRow() != self.imageList.index(filename)
        ):
            self.fileListWidget.setCurrentRow(self.imageList.index(filename))
            self.fileListWidget.repaint()
            return

        self.resetState()
        self.canvas.setEnabled(False)
        if filename is None:
            filename = self.settings.value("filename", "")
        filename = str(filename)
        if not QtCore.QFile.exists(filename):
            self.errorMessage(
                self.tr("Error opening file"),
                self.tr("No such file: <b>%s</b>") % filename,
            )
            return False
        # assumes same name, but json extension
        self.status(
            str(self.tr("Loading %s...")) % osp.basename(str(filename))
        )
        cocofile = False
        labelfile = False
        coco_file = "{}_coco.{}".format(osp.splitext(filename)[0], "json")
        if self.output_dir:
            coco_file_without_path = osp.basename(coco_file)
            coco_file = osp.join(self.output_dir, coco_file_without_path)

        if QtCore.QFile.exists(coco_file) and ConvertCoCOLabel.is_coco_file(
            coco_file
        ):
            cocofile = True

        label_file = osp.splitext(filename)[0] + ".json"
        if self.output_dir:
            label_file_without_path = osp.basename(label_file)
            label_file = osp.join(self.output_dir, label_file_without_path)
        if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(
            label_file
        ):
            labelfile = True

        if cocofile is True and labelfile is True:
            try:
                self.labelFile = LabelFile(label_file)
            except LabelFileError as e:
                self.errorMessage(
                    self.tr("Error opening file"),
                    self.tr(
                        "<p><b>%s</b></p>"
                        "<p>Make sure <i>%s</i> is a valid label file."
                    )
                    % (e, label_file),
                )
                # LogPrint("e : %s" % e)
                self.status(self.tr("Error reading %s") % label_file)
                return False
            self.imageData = self.labelFile.imageData
            self.imagePath = osp.join(
                osp.dirname(label_file),
                self.labelFile.imagePath,
            )
            self.otherData = self.labelFile.otherData
        elif cocofile is False and labelfile is True:
            try:
                self.labelFile = LabelFile(label_file)
            except LabelFileError as e:
                self.errorMessage(
                    self.tr("Error opening file"),
                    self.tr(
                        "<p><b>%s</b></p>"
                        "<p>Make sure <i>%s</i> is a valid label file."
                    )
                    % (e, label_file),
                )
                # LogPrint("e : %s" % e)
                self.status(self.tr("Error reading %s") % label_file)
                return False
            self.imageData = self.labelFile.imageData
            self.imagePath = osp.join(
                osp.dirname(label_file),
                self.labelFile.imagePath,
            )
            self.otherData = self.labelFile.otherData
        elif cocofile is True and labelfile is False:
            ccls = ConvertCoCOLabel(coco_file, label_file)
            label_file = ccls.save()
            if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(
                    label_file
            ):
                try:
                    self.labelFile = LabelFile(label_file)
                except LabelFileError as e:
                    self.errorMessage(
                        self.tr("Error opening file"),
                        self.tr(
                            "<p><b>%s</b></p>"
                            "<p>Make sure <i>%s</i> is a valid label file."
                        )
                        % (e, label_file),
                    )
                    # LogPrint("e : %s" % e)
                    self.status(self.tr("Error reading %s") % label_file)
                    return False
                self.imageData = self.labelFile.imageData
                self.imagePath = osp.join(
                    osp.dirname(label_file),
                    self.labelFile.imagePath,
                )
                self.otherData = self.labelFile.otherData
        else:
            self.imageData = LabelFile.load_image_file(filename)
            if self.imageData:
                self.imagePath = filename
            self.labelFile = None

        image = QtGui.QImage.fromData(self.imageData)

        if image.isNull():
            formats = [
                "*.{}".format(fmt.data().decode())
                for fmt in QtGui.QImageReader.supportedImageFormats()
            ]
            self.errorMessage(
                self.tr("Error opening file"),
                self.tr(
                    "<p>Make sure <i>{0}</i> is a valid image file.<br/>"
                    "Supported image formats: {1}</p>"
                ).format(filename, ",".join(formats)),
            )
            self.status(self.tr("Error reading %s") % filename)
            return False

        self.image = image
        self.filename = filename
        if self._config["keep_prev"]:
            prev_shapes = self.canvas.shapes
        self.canvas.loadPixmap(QtGui.QPixmap.fromImage(image))

        if self.labelFile:
            self.loadLabels(self.labelFile.shapes)
        # part grades of here ckd

        if self._config["keep_prev"] and self.noShapes():
            self.loadShapes(prev_shapes, replace=False)
            self.setDirty()
        else:
            self.setClean()
        self.canvas.setEnabled(True)
        # set zoom values
        is_initial_load = not self.zoom_values
        if self.filename in self.zoom_values:
            self.zoomMode = self.zoom_values[self.filename][0]
            self.setZoom(self.zoom_values[self.filename][1])
        elif is_initial_load or not self._config["keep_prev_scale"]:
            self.adjustScale(initial=True)
        # set scroll values
        for orientation in self.scroll_values:
            if self.filename in self.scroll_values[orientation]:
                self.setScroll(
                    orientation, self.scroll_values[orientation][self.filename]
                )
        # set brightness contrast values
        dialog = BrightnessContrastDialog(
            utils.img_data_to_pil(self.imageData),
            self.onNewBrightnessContrast,
            parent=self,
        )
        brightness, contrast = self.brightnessContrast_values.get(
            self.filename, (None, None)
        )
        if self._config["keep_prev_brightness"] and self.recentFiles:
            brightness, _ = self.brightnessContrast_values.get(
                self.recentFiles[0], (None, None)
            )
        if self._config["keep_prev_contrast"] and self.recentFiles:
            _, contrast = self.brightnessContrast_values.get(
                self.recentFiles[0], (None, None)
            )
        if brightness is not None:
            dialog.slider_brightness.setValue(brightness)
        if contrast is not None:
            dialog.slider_contrast.setValue(contrast)
        self.brightnessContrast_values[self.filename] = (brightness, contrast)
        if brightness is not None or contrast is not None:
            dialog.onNewValue(None)
        self.paintCanvas()
        self.addRecentFile(self.filename)
        self.toggleActions(True)
        self.canvas.setFocus()
        self.status(str(self.tr("Loaded %s")) % osp.basename(str(filename)))

        # add ckd
        self.topToolWidget.editmodeClick(True)

        return True

    def loadFile_(self, filename=None):
        """Load the specified file, or the last opened file if None."""
        # changing fileListWidget loads file
        if filename in self.imageList and (
            self.fileListWidget.currentRow() != self.imageList.index(filename)
        ):
            self.fileListWidget.setCurrentRow(self.imageList.index(filename))
            self.fileListWidget.repaint()
            return

        self.resetState()
        self.canvas.setEnabled(False)
        if filename is None:
            filename = self.settings.value("filename", "")
        filename = str(filename)
        if not QtCore.QFile.exists(filename):
            self.errorMessage(
                self.tr("Error opening file"),
                self.tr("No such file: <b>%s</b>") % filename,
            )
            return False
        # assumes same name, but json extension
        self.status(
            str(self.tr("Loading %s...")) % osp.basename(str(filename))
        )
        label_file = osp.splitext(filename)[0] + ".json"
        if self.output_dir:
            label_file_without_path = osp.basename(label_file)
            label_file = osp.join(self.output_dir, label_file_without_path)
        if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(
            label_file
        ):
            try:
                self.labelFile = LabelFile(label_file)
            except LabelFileError as e:
                self.errorMessage(
                    self.tr("Error opening file"),
                    self.tr(
                        "<p><b>%s</b></p>"
                        "<p>Make sure <i>%s</i> is a valid label file."
                    )
                    % (e, label_file),
                )
                # LogPrint("e : %s" % e)
                self.status(self.tr("Error reading %s") % label_file)
                return False
            self.imageData = self.labelFile.imageData
            self.imagePath = osp.join(
                osp.dirname(label_file),
                self.labelFile.imagePath,
            )
            self.otherData = self.labelFile.otherData
        else:
            self.imageData = LabelFile.load_image_file(filename)
            if self.imageData:
                self.imagePath = filename
            self.labelFile = None
        image = QtGui.QImage.fromData(self.imageData)

        if image.isNull():
            formats = [
                "*.{}".format(fmt.data().decode())
                for fmt in QtGui.QImageReader.supportedImageFormats()
            ]
            self.errorMessage(
                self.tr("Error opening file"),
                self.tr(
                    "<p>Make sure <i>{0}</i> is a valid image file.<br/>"
                    "Supported image formats: {1}</p>"
                ).format(filename, ",".join(formats)),
            )
            self.status(self.tr("Error reading %s") % filename)
            return False
        self.image = image
        self.filename = filename
        if self._config["keep_prev"]:
            prev_shapes = self.canvas.shapes
        self.canvas.loadPixmap(QtGui.QPixmap.fromImage(image))

        if self.labelFile:
            self.loadLabels(self.labelFile.shapes)
        # part grades of here ckd

        if self._config["keep_prev"] and self.noShapes():
            self.loadShapes(prev_shapes, replace=False)
            self.setDirty()
        else:
            self.setClean()
        self.canvas.setEnabled(True)
        # set zoom values
        is_initial_load = not self.zoom_values
        if self.filename in self.zoom_values:
            self.zoomMode = self.zoom_values[self.filename][0]
            self.setZoom(self.zoom_values[self.filename][1])
        elif is_initial_load or not self._config["keep_prev_scale"]:
            self.adjustScale(initial=True)
        # set scroll values
        for orientation in self.scroll_values:
            if self.filename in self.scroll_values[orientation]:
                self.setScroll(
                    orientation, self.scroll_values[orientation][self.filename]
                )
        # set brightness contrast values
        dialog = BrightnessContrastDialog(
            utils.img_data_to_pil(self.imageData),
            self.onNewBrightnessContrast,
            parent=self,
        )
        brightness, contrast = self.brightnessContrast_values.get(
            self.filename, (None, None)
        )
        if self._config["keep_prev_brightness"] and self.recentFiles:
            brightness, _ = self.brightnessContrast_values.get(
                self.recentFiles[0], (None, None)
            )
        if self._config["keep_prev_contrast"] and self.recentFiles:
            _, contrast = self.brightnessContrast_values.get(
                self.recentFiles[0], (None, None)
            )
        if brightness is not None:
            dialog.slider_brightness.setValue(brightness)
        if contrast is not None:
            dialog.slider_contrast.setValue(contrast)
        self.brightnessContrast_values[self.filename] = (brightness, contrast)
        if brightness is not None or contrast is not None:
            dialog.onNewValue(None)
        self.paintCanvas()
        self.addRecentFile(self.filename)
        self.toggleActions(True)
        self.canvas.setFocus()
        self.status(str(self.tr("Loaded %s")) % osp.basename(str(filename)))

        # add ckd
        self.topToolWidget.editmodeClick(True)

        return True

    def resizeEvent(self, event):
        if (
            self.canvas
            and not self.image.isNull()
            and self.zoomMode != self.MANUAL_ZOOM
        ):
            self.adjustScale()
        super(MainWindow, self).resizeEvent(event)

    def paintCanvas(self):
        assert not self.image.isNull(), "cannot paint null image"
        self.canvas.scale = 0.01 * self.zoomWidget.value()
        self.canvas.adjustSize()
        self.canvas.update()

    def adjustScale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoomMode]()
        value = int(100 * value)
        self.zoomWidget.setValue(value)
        self.zoom_values[self.filename] = (self.zoomMode, value)

    def scaleFitWindow(self):
        """Figure out the size of the pixmap to fit the main widget."""
        e = 2.0  # So that no scrollbars are generated.
        w1 = self.centralWidget().width() - e
        h1 = self.centralWidget().height() - e
        a1 = w1 / h1
        # Calculate a new scale value based on the pixmap's aspect ratio.
        if self.canvas:
            w2 = self.canvas.pixmap.width() - 0.0
            h2 = self.canvas.pixmap.height() - 0.0
        else:
            w2 = w1
            h2 = h1
        a2 = w2 / h2
        return w1 / w2 if a2 >= a1 else h1 / h2

    def scaleFitWidth(self):
        # The epsilon does not seem to work too well here.
        w = self.centralWidget().width() - 2.0
        return w / self.canvas.pixmap.width()

    def enableSaveImageWithData(self, enabled):
        self._config["store_data"] = enabled
        self.actions.saveWithImageData.setChecked(enabled)

    def closeEvent(self, event):
        if not self.mayContinue():
            event.ignore()
        self.settings.setValue(
            "filename", self.filename if self.filename else ""
        )
        self.settings.setValue("window/size", self.size())
        self.settings.setValue("window/position", self.pos())
        self.settings.setValue("window/state", self.saveState())
        self.settings.setValue("recentFiles", self.recentFiles)
        # ask the use for where to save the labels
        # self.settings.setValue('window/geometry', self.saveGeometry())
        self.labelList.clear()
        self._polyonList.clear()

    def dragEnterEvent(self, event):
        extensions = [
            ".%s" % fmt.data().decode().lower()
            for fmt in QtGui.QImageReader.supportedImageFormats()
        ]
        if event.mimeData().hasUrls():
            items = [i.toLocalFile() for i in event.mimeData().urls()]
            if any([i.lower().endswith(tuple(extensions)) for i in items]):
                event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if not self.mayContinue():
            event.ignore()
            return
        items = [i.toLocalFile() for i in event.mimeData().urls()]
        self.importDroppedImageFiles(items)

    # User Dialogs #

    def loadRecent(self, filename):
        if self.mayContinue():
            self.loadFile(filename)

    def openPrevImg(self, _value=False):
        keep_prev = self._config["keep_prev"]
        if QtWidgets.QApplication.keyboardModifiers() == (
            Qt.ControlModifier | Qt.ShiftModifier
        ):
            self._config["keep_prev"] = True

        if not self.mayContinue():
            return

        if len(self.imageList) <= 0:
            return

        if self.filename is None:
            return

        currIndex = self.imageList.index(self.filename)
        if currIndex - 1 >= 0:
            filename = self.imageList[currIndex - 1]
            if filename:
                self.loadFile(filename)

        self._config["keep_prev"] = keep_prev

    def openNextImg(self, _value=False, load=True):
        keep_prev = self._config["keep_prev"]
        if QtWidgets.QApplication.keyboardModifiers() == (
            Qt.ControlModifier | Qt.ShiftModifier
        ):
            self._config["keep_prev"] = True

        if not self.mayContinue():
            return

        if len(self.imageList) <= 0:
            return

        filename = None
        if self.filename is None:
            filename = self.imageList[0]
        else:
            currIndex = self.imageList.index(self.filename)
            if currIndex + 1 < len(self.imageList):
                filename = self.imageList[currIndex + 1]
            else:
                filename = self.imageList[-1]
        self.filename = filename

        if self.filename and load:
            self.loadFile(self.filename)

        self._config["keep_prev"] = keep_prev

    def openFile(self, _value=False):
        if not self.mayContinue():
            return
        path = osp.dirname(str(self.filename)) if self.filename else "."
        formats = [
            "*.{}".format(fmt.data().decode())
            for fmt in QtGui.QImageReader.supportedImageFormats()
        ]
        filters = self.tr("Image & Label files (%s)") % " ".join(
            formats + ["*%s" % LabelFile.suffix]
        )
        fileDialog = FileDialogPreview(self)
        fileDialog.setFileMode(FileDialogPreview.ExistingFile)
        fileDialog.setNameFilter(filters)
        fileDialog.setWindowTitle(
            self.tr("%s - Choose Image or Label file") % __appname__,
        )
        fileDialog.setWindowFilePath(path)
        fileDialog.setViewMode(FileDialogPreview.Detail)
        if fileDialog.exec_():
            fileName = fileDialog.selectedFiles()[0]
            if fileName:
                self.loadFile(fileName)

    def changeOutputDirDialog(self, _value=False):
        default_output_dir = self.output_dir
        if default_output_dir is None and self.filename:
            default_output_dir = osp.dirname(self.filename)
        if default_output_dir is None:
            default_output_dir = self.currentPath()

        output_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            self.tr("%s - Save/Load Annotations in Directory") % __appname__,
            default_output_dir,
            QtWidgets.QFileDialog.ShowDirsOnly
            | QtWidgets.QFileDialog.DontResolveSymlinks,
        )
        output_dir = str(output_dir)

        if not output_dir:
            return

        self.output_dir = output_dir

        self.statusBar().showMessage(
            self.tr("%s . Annotations will be saved/loaded in %s")
            % ("Change Annotations Dir", self.output_dir)
        )
        self.statusBar().show()

        current_filename = self.filename
        self.importDirImages(self.lastOpenDir, load=False)

        if current_filename in self.imageList:
            # retain currently selected file
            self.fileListWidget.setCurrentRow(
                self.imageList.index(current_filename)
            )
            self.fileListWidget.repaint()

    def saveFile(self, _value=False):
        assert not self.image.isNull(), "cannot save empty image"
        if self.labelFile:
            # DL20180323 - overwrite when in directory
            self._saveFile(self.labelFile.filename)
        elif self.output_file:
            self._saveFile(self.output_file)
            self.close()
        else:
            self._saveFile(self.saveFileDialog())

    def saveFileAs(self, _value=False):
        assert not self.image.isNull(), "cannot save empty image"
        self._saveFile(self.saveFileDialog())

    def saveFileDialog(self):
        caption = self.tr("%s - Choose File") % __appname__
        filters = self.tr("Label files (*%s)") % LabelFile.suffix
        if self.output_dir:
            dlg = QtWidgets.QFileDialog(
                self, caption, self.output_dir, filters
            )
        else:
            dlg = QtWidgets.QFileDialog(
                self, caption, self.currentPath(), filters
            )
        dlg.setDefaultSuffix(LabelFile.suffix[1:])
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dlg.setOption(QtWidgets.QFileDialog.DontConfirmOverwrite, False)
        dlg.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, False)
        basename = osp.basename(osp.splitext(self.filename)[0])
        if self.output_dir:
            default_labelfile_name = osp.join(
                self.output_dir, basename + LabelFile.suffix
            )
        else:
            default_labelfile_name = osp.join(
                self.currentPath(), basename + LabelFile.suffix
            )
        filename = dlg.getSaveFileName(
            self,
            self.tr("Choose File"),
            default_labelfile_name,
            self.tr("Label files (*%s)") % LabelFile.suffix,
        )
        if isinstance(filename, tuple):
            filename, _ = filename
        return filename

    def _saveFile(self, filename):
        if filename and self.saveLabels(filename):
            self.addRecentFile(filename)
            self.setClean()
            # run coco format
            threading.Timer(0.1, self.putDownCocoFormat, [filename]).start()

    def putDownCocoFormat(self, arg):
        if arg is None:
            return
        # put to coco format
        cf = ""
        try:
            cocofiles = []
            cocofiles.append(arg)
            basename = os.path.basename(arg)
            coco_fname = os.path.splitext(basename)[0]
            dirname = os.path.dirname(arg)
            cocofp = "{}/{}_coco.{}".format(dirname, coco_fname, "json")
            labelme2coco(cocofiles, cocofp)
        except LabelFileError as e:
            self.errorMessage(
                self.tr("Error creating coco file"),
                self.tr(
                    "<p><b>%s</b></p>"
                    "<p>Make sure <i>%s</i> is a valid label file."
                )
                % (e, cf),
            )

        print("Success save coco json")


    def closeFile(self, _value=False):
        if not self.mayContinue():
            return
        self.resetState()
        self.setClean()
        self.toggleActions(False)
        self.canvas.setEnabled(False)
        self.actions.saveAs.setEnabled(False)

        self.topToolWidget.editmodeClick(False)
        self.polygonTrans_value = 0
        try:
            if self.polygonAlphaDlg is not None:
                self.polygonAlphaDlg.label.setText("100%")
            self.polygonAlphaDlg = None
        except AttributeError as a:
            pass


    def getLabelFile(self):
        if self.filename.lower().endswith(".json"):
            label_file = self.filename
        else:
            label_file = osp.splitext(self.filename)[0] + ".json"

        return label_file

    def deleteFile(self):
        mb = QtWidgets.QMessageBox
        msg = self.tr(
            "You are about to permanently delete this label file, "
            "proceed anyway?"
        )
        answer = mb.warning(self, self.tr("Attention"), msg, mb.Yes | mb.No)
        if answer != mb.Yes:
            return

        label_file = self.getLabelFile()
        if osp.exists(label_file):
            os.remove(label_file)
            logger.info("Label file is removed: {}".format(label_file))
        # delete coco file > add ckd
            basename = os.path.basename(label_file)
            coco_fname = os.path.splitext(basename)[0]
            dirname = os.path.dirname(label_file)
            cocofp = "{}/{}_coco.{}".format(dirname, coco_fname, "json")
            if osp.exists(cocofp):
                os.remove(cocofp)

            item = self.fileListWidget.currentItem()
            if item:
                item.setCheckState(Qt.Unchecked)
            #self.resetState()
            self.resetSimplyState()  # add ckd

    # Message Dialogs.
    def hasLabels(self):
        if self.noShapes():
            self.errorMessage(
                "No objects labeled",
                "You must label at least one object to save the file.",
            )
            return False
        return True

    def hasLabelFile(self):
        if self.filename is None:
            return False

        label_file = self.getLabelFile()
        return osp.exists(label_file)

    def mayContinue(self):
        if not self.dirty:
            return True
        mb = QtWidgets.QMessageBox
        msg = self.tr('Save annotations to "{}" before closing?').format(
            self.filename
        )
        answer = mb.question(
            self,
            self.tr("Save annotations?"),
            msg,
            mb.Save | mb.Discard | mb.Cancel,
            mb.Save,
        )
        if answer == mb.Discard:
            return True
        elif answer == mb.Save:
            self.saveFile()
            return True
        else:  # answer == mb.Cancel
            return False

    def errorMessage(self, title, message):
        return QtWidgets.QMessageBox.critical(
            self, title, "<p><b>%s</b></p>%s" % (title, message)
        )

    def currentPath(self):
        return osp.dirname(str(self.filename)) if self.filename else "."

    def toggleKeepPrevMode(self):
        self._config["keep_prev"] = not self._config["keep_prev"]

    def removeSelectedPoint(self):
        self.canvas.removeSelectedPoint()
        self.canvas.update()
        if not self.canvas.hShape.points:
            self.canvas.deleteShape(self.canvas.hShape)
            self.remLabels([self.canvas.hShape])
            polyT = "Polygon Labels (Total %s)"
            if self._config["local_lang"] == "ko_KR":
                polyT = "다각형 레이블 (총 %s)"
            if self.shape_dock:
                self.shape_dock.titleBarWidget().titleLabel.setText(polyT % len(self.labelList))

            self.setDirty()
            if self.noShapes():
                for action in self.actions.onShapesPresent:
                    action.setEnabled(False)



    def deleteSelectedShape(self):
        yes, no = QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No
        msg = self.tr(
            "You are about to permanently delete {} polygons, "
            "proceed anyway?"
        ).format(len(self.canvas.selectedShapes))
        if yes == QtWidgets.QMessageBox.warning(
                self, self.tr("Attention"), msg, yes | no, yes
        ):
            self.remLabels(self.canvas.deleteSelected())
            polyT = "Polygon Labels (Total %s)"
            if self._config["local_lang"] == "ko_KR":
                polyT = "다각형 레이블 (총 %s)"
            if self.shape_dock:
                self.shape_dock.titleBarWidget().titleLabel.setText(polyT % len(self.labelList))

            self.setDirty()
            if self.noShapes():
                for action in self.actions.onShapesPresent:
                    action.setEnabled(False)



    def copyShape(self):
        self.canvas.endMove(copy=True)
        for shape in self.canvas.selectedShapes:
            self.addLabel(shape)
        self.labelList.clearSelection()
        self.setDirty()

    def moveShape(self):
        self.canvas.endMove(copy=False)
        self.setDirty()

    def openDirDialog(self, _value=False, dirpath=None):
        if not self.mayContinue():
            return

        defaultOpenDirPath = dirpath if dirpath else "."
        if self.lastOpenDir and osp.exists(self.lastOpenDir):
            defaultOpenDirPath = self.lastOpenDir
        else:
            defaultOpenDirPath = (
                osp.dirname(self.filename) if self.filename else "."
            )

        targetDirPath = str(
            QtWidgets.QFileDialog.getExistingDirectory(
                self,
                self.tr("%s - Open Directory") % __appname__,
                defaultOpenDirPath,
                QtWidgets.QFileDialog.ShowDirsOnly
                | QtWidgets.QFileDialog.DontResolveSymlinks,
            )
        )
        self.importDirImages(targetDirPath)

    @property
    def imageList(self):
        lst = []
        for i in range(self.fileListWidget.count()):
            item = self.fileListWidget.item(i)
            lst.append(item.text())
        return lst

    def importDroppedImageFiles(self, imageFiles):
        extensions = [
            ".%s" % fmt.data().decode().lower()
            for fmt in QtGui.QImageReader.supportedImageFormats()
        ]

        self.filename = None
        for file in imageFiles:
            if file in self.imageList or not file.lower().endswith(
                tuple(extensions)
            ):
                continue
            label_file = osp.splitext(file)[0] + ".json"
            if self.output_dir:
                label_file_without_path = osp.basename(label_file)
                label_file = osp.join(self.output_dir, label_file_without_path)
            item = QtWidgets.QListWidgetItem(file)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(
                label_file
            ):
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.fileListWidget.addItem(item)

        if len(self.imageList) > 1:
            self.actions.openNextImg.setEnabled(True)
            self.actions.openPrevImg.setEnabled(True)

        self.openNextImg()

    def importDirImages(self, dirpath, pattern=None, load=True):
        self.actions.openNextImg.setEnabled(True)
        self.actions.openPrevImg.setEnabled(True)

        if not self.mayContinue() or not dirpath:
            return

        self.lastOpenDir = dirpath
        self.filename = None
        self.fileListWidget.clear()
        for filename in self.scanAllImages(dirpath):
            if pattern and pattern not in filename:
                continue
            label_file = osp.splitext(filename)[0] + ".json"
            if self.output_dir:
                label_file_without_path = osp.basename(label_file)
                label_file = osp.join(self.output_dir, label_file_without_path)
            item = QtWidgets.QListWidgetItem(filename)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(
                label_file
            ):
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.fileListWidget.addItem(item)

        self.openNextImg(load=load)
        # print("{}".format(self.fileListWidget.count()))
        self.file_dock.setWindowTitle(self.tr("File List (Total {})".format(self.fileListWidget.count())))

    def scanAllImages(self, folderPath):
        extensions = [
            ".%s" % fmt.data().decode().lower()
            for fmt in QtGui.QImageReader.supportedImageFormats()
        ]

        images = []
        for root, dirs, files in os.walk(folderPath):
            for file in files:
                if file.lower().endswith(tuple(extensions)):
                    relativePath = osp.join(root, file)
                    images.append(relativePath)
        images = natsort.os_sorted(images)
        return images

    def gradeButtonEvent(self, arg):
        self.grade_title_bar.hidnBtn.clicked.emit()

    # send new grade
    def sendGradeToServer(self, item, items, callback):
        url = 'https://gb9fb258fe17506-apexdb.adb.ap-seoul-1.oraclecloudapps.com/ords/lm/v1/labelme/codes/grades'
        headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
        data = {'user_id': self._config['user_id'], 'grade': item}
        jsstr = httpReq(url, "post", headers, data)
        if jsstr['message'] == 'success':
            callback(items)  # called addItemsToQHBox
        else:
            return QtWidgets.QMessageBox.critical(
                self, "Error", "<p><b>%s</b></p>%s" % ("Error", jsstr['message'])
            )

    # send new product
    def sendProductToServer(self, pstr, callback):
        url = 'https://gb9fb258fe17506-apexdb.adb.ap-seoul-1.oraclecloudapps.com/ords/lm/v1/labelme/codes/products'
        headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
        data = {'user_id': self._config['user_id'], 'grade': self.selected_grade, 'product': pstr}
        jsstr = httpReq(url, "post", headers, data)
        if jsstr['message'] == 'success':
            callback(pstr)  # called addItemsToQHBox
        else:
            return QtWidgets.QMessageBox.critical(
                self, "Error", "<p><b>%s</b></p>%s" % ("Error", jsstr['message'])
            )

    def receiveProductsFromServerByGrade(self):
        if self.selected_grade:
            #print(self.selected_grade)
            url = 'https://gb9fb258fe17506-apexdb.adb.ap-seoul-1.oraclecloudapps.com/ords/lm/v1/labelme/codes/products?grade=' + self.selected_grade
            headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
            jsstr = httpReq(url, "get", headers)
            if jsstr['message'] == 'success':
                items = jsstr['items']
                #print("products is ", items)
                if items and len(items) > 0:
                    self.loadProducts(items)
                else:
                    temp = [{"product": "미정"}]
                    self.loadProducts(temp)

            else:
                return QtWidgets.QMessageBox.critical(
                    self, "Error", "<p><b>%s</b></p>%s" % ("Error", jsstr['message'])
                )

    def receiveLabelsFromServerByGrade(self):
        if self.selected_grade:
            #print(self.selected_grade)
            url = 'https://gb9fb258fe17506-apexdb.adb.ap-seoul-1.oraclecloudapps.com/ords/lm/v1/labelme/codes/labels?grade=' + self.selected_grade
            headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
            jsstr = httpReq(url, "get", headers)
            if jsstr['message'] == 'success':
                items = jsstr['items']
                try:
                    if self._polyonList is not None:
                        self._polyonList.clear()
                    else:
                        self._polyonList = []

                    if items and len(items) > 0:
                        self._polyonList = items
                    else:
                        temp = [{
                            "label_display": "미정-미정",
                            "label": "미정",
                            "grade": "미정",
                            "color": "#ff0000"
                        }]
                        self._polyonList = temp
                except AttributeError:
                    pass
            else:
                return QtWidgets.QMessageBox.critical(
                    self, "Error", "<p><b>%s</b></p>%s" % ("Error", jsstr['message'])
                )

    def receiveGradesFromServer(self):
        url = 'https://gb9fb258fe17506-apexdb.adb.ap-seoul-1.oraclecloudapps.com/ords/lm/v1/labelme/codes/grades'
        headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
        jsstr = httpReq(url, "get", headers)
        if jsstr['message'] == 'success':
            self.grades_widget.set(jsstr['items'])
        else:
            return QtWidgets.QMessageBox.critical(
                self, "Error", "<p><b>%s</b></p>%s" % ("Error", jsstr['message'])
            )

    # This function be not used now
    def receiveProductsFromServer(self):
        url = 'https://gb9fb258fe17506-apexdb.adb.ap-seoul-1.oraclecloudapps.com/ords/lm/v1/labelme/codes/products'
        headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
        jsstr = httpReq(url, "get", headers)
        if jsstr['message'] == 'success':
            items = jsstr['items']
            # print("All products is ", items)
            if items and len(items) > 0:
                self.loadProducts(items)
            else:
                temp = [{"product": "미정"}]
                self.loadProducts(temp)
        else:
            return QtWidgets.QMessageBox.critical(
                self, "Error", "<p><b>%s</b></p>%s" % ("Error", jsstr['message'])
            )