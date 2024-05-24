# Copyright (c) 2024 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


__author__ = "Juno Park"
__github__ = "https://github.com/junopark00"


import os
import time
import logging
import inspect

import sgtk
from sgtk import TankError
from sgtk.log import LogManager
from sgtk.platform.constants import SHOTGUN_ENGINE_NAME
import ix


# add shotgun attribute to ix
if not hasattr(ix, "shotgun"):
    # use a dummy class to keep references to menus
    ix.shotgun = lambda: None
    ix.shotgun.menu_callbacks = {}
    
def get_sgtk_root_menu(menu_name):
    """
    Get the root menu for the given menu name. If the menu does not exist, it

    :param menu_name: The name of the menu to get.
    
    :return: The menu item handle.
    """
    menu = ix.application.get_main_menu()

    sg_menu = menu.get_item(menu_name + ">")
    if not sg_menu:
        sg_menu = menu.add_command(menu_name + ">")
    return sg_menu

############################################################################
# Clarisse Engine
class ClarisseEngine(sgtk.platform.Engine):
    """
    The engine class
    """
    def __init__(self, *args, **kwargs):
        # Detect if Clarisse is running in UI mode or not
        self._ui_enabled = bool(ix.is_gui_application())
        super(ClarisseEngine, self).__init__(*args, **kwargs)

    @property
    def has_ui(self):
        """
        Detect and return if Clarisse is running with UI
        """
        return self._ui_enabled
        
    @property
    def host_info(self):
        """
        :returns: A dictionary with information about the application hosting this engine.
        """
        host_info = {"name": "Clarisse", "version": "unknown"}

        try:
            # Get Clarisse version information here
            host_info["version"] = ix.application.get_version_name()
        except:
            pass

        return host_info

    def pre_app_init(self):
        """
        Runs after the engine is set up but before any apps have been
        initialized.
        """
        # unicode characters returned by shotgun api need to be converted
        # to display correctly in all of the app windows
        
        from sgtk.platform.qt import QtCore
        
        utf8 = QtCore.QTextCodec.codecForName("utf-8")
        QtCore.QTextCodec.setCodecForCStrings(utf8)
        self.log_debug("Pre-app init complete...")
        
    def init_engine(self):
        """
        Initialize the Clarisse engine
        """
        self.log_debug("%s: Initializing..." % self)
        
        # check that we are running Clarisse v3.6 or later
        current_os = os.sys.platform.lower()
        if current_os not in ["win32", "linux", "darwin"]:  # use linux2 in python 2
            raise TankError("Platform '%s' is not supported." % current_os)
        
        clarisse_build_version = ix.application.get_version()
        clarisse_ver = float(".".join(clarisse_build_version.split(".")[:2]))
        
        if clarisse_ver < 3.6:
            raise TankError(
                "Clarisse v3.6 or later is required. Detected version: %s"
                % clarisse_build_version
                )
        
        # add qt paths
        self._init_pyside()
        
        self._menu_name = "Flow Production Tracking"
        if self.get_setting("use_sgtk_as_menu_name", False):
            self._menu_name = "Sgtk"
        
    def _init_pyside(self):
        """
        Handles the pyside init
        """
        # first see if pyside2 is present
        try:
            from PySide2 import QtGui
        except:
            self.logger.debug("PySide2 not detected - trying for PySide now...")
        else:
            # looks like pyside2 is already working! No need to do anything
            self.logger.debug(
                "PySide2 detected - the existing version will be used."
            )
            return

        # then see if pyside is present
        try:
            from PySide import QtGui
        except:
            self.logger.debug(
                "PySide not detected - it will be added to the setup now..."
            )
        else:
            # looks like pyside is already working! No need to do anything
            self.logger.debug(
                "PySide detected - the existing version will be used."
            )
            return

    def post_app_init(self):
        """
        Called when all apps have initialized
        """
        # for some readon this engine command get's lost so we add it back
        self.__register_reload_command()
        self.create_shotgun_menu()
        
        # Remove Open Log Folder command in 'Project' context
        main = ix.application.get_main_menu()
        to_remove = "Flow Production Tracking>Current Context>Open Log Folder"
        main.remove_command(to_remove)

    def create_shotgun_menu(self, **kwargs):
        """
        Creates the main shotgun menu in clarisse.
        Note that this only creates the menu, not the child actions
        :return: bool
        """
        # only create the shotgun menu if not in batch mode and menu doesn't
        # already exist
        if self.has_ui:
            self._menu_handle = get_sgtk_root_menu(self._menu_name)

            # create our menu handler
            tk_clarisse = self.import_module("tk_clarisse")
            self._menu_generator = tk_clarisse.MenuGenerator(
                self, self._menu_handle
            )
            self._menu_generator.create_menu()
            return True
        
    def post_context_change(self, old_context, new_context):
        """
        Called when a context change is detected

        :param old_context: The context being changed away from.
        :param new_context: The new context being changed to.
        """
        # restore context menu's when context changed
        with open("/RAPA/log.txt", "a") as f:
            f.write("Context changed\n")
        self.__register_open_log_folder_command()
        self.__register_reload_command()
        self.__register_toggle_debug_logging_command()

        return False
    def destroy_engine(self):
        """
        Called when the engine is being destroyed
        """
        self.log_debug("%s: Destroying..." % self)

        if self.has_ui:
            try:
                self._menu_generator.destroy_menu()
            except:
                self.logging.error("Failed to destroy the Shotgun menu.")
                
############################################################################
# Overridden methods which show dialogs
    
    def _get_dialog_parent(self):
        """
        Clarisse is not Qt Based so we do not have anything to return here.
        """
        return None
    
    def show_dialog(self, title, bundle, widget_class, *args, **kwargs):
        """
        :param title: The title of the window. This will appear in the Toolkit title bar.
        :param bundle: The app, engine or framework object that is associated with this window
        :param widget_class: The class of the UI to be constructed. This must derive from QWidget.
        :type widget_class: :class:`PySide.QtGui.QWidget`

        Additional parameters specified will be passed through to the widget_class constructor.

        :returns: the created widget_class instance
        """
        from sgtk.platform.qt import QtGui

        qt_app = QtGui.QApplication.instance()
        if qt_app is None:

            self.log_debug("Initializing main QApplication...")
            qt_app = QtGui.QApplication([])
            qt_app.setWindowIcon(QtGui.QIcon(self.icon_256))

            # set up the dark style
            self._initialize_dark_look_and_feel()

        if not self.has_ui:
            self.loggine.error(
                "Sorry, this environment does not support UI display! Cannot show "
                "the requested window '%s'." % title
            )
            return None

        # create the dialog:
        dialog, widget = self._create_dialog_with_widget(
            title, bundle, widget_class, *args, **kwargs
        )

        # show the dialog
        dialog.show()
        
        # exec qt_app
        import pyqt_clarisse
        pyqt_clarisse.exec_(qt_app)

        # lastly, return the instantiated widget
        return widget 

############################################################################
# Overridden methods which set or reload the menu

    def __get_platform_resource_path(self, filename):
        """
        Returns the full path to the given platform resource file or folder.
        Resources reside in the core/platform/qt folder.
        :return: full path
        """
        tank_platform_folder = os.path.abspath(inspect.getfile(sgtk.platform))
        return os.path.join(tank_platform_folder, "qt", filename)
    
    def __toggle_debug_logging(self):
        """
        Toggles global debug logging on and off in the log manager.
        This will affect all logging across all of toolkit.
        """
        # flip debug logging
        LogManager().global_debug = not LogManager().global_debug

    def __open_log_folder(self):
        """
        Opens the file system folder where log files are being stored.
        """
        self.log_info("Log folder location: '%s'" % LogManager().log_folder)

        if self.has_ui:
            # only import QT if we have a UI
            from sgtk.platform.qt import QtGui, QtCore

            url = QtCore.QUrl.fromLocalFile(LogManager().log_folder)
            status = QtGui.QDesktopServices.openUrl(url)
            if not status:
                self._engine.log_error("Failed to open folder!")

    def __register_open_log_folder_command(self):
        """
        # add a 'open log folder' command to the engine's context menu
        # note: we make an exception for the shotgun engine which is a
        # special case.
        """
        if self.name != SHOTGUN_ENGINE_NAME:
            self.register_command(
                "Open Log Folder",
                self.__open_log_folder,
                {
                    "short_name": "open_log_folder",
                    "icon": self.__get_platform_resource_path("folder_256.png"),
                    "description": (
                        "Opens the folder where log files are being stored."
                    ),
                    "type": "context_menu",
                },
            )

    def __register_reload_command(self):
        """
        Registers a "Reload and Restart" command with the engine if any
        running apps are registered via a dev descriptor.
        """
        from sgtk.platform import restart

        self.register_command(
            "Reload and Restart",
            restart,
            {
                "short_name": "restart",
                "icon": self.__get_platform_resource_path("reload_256.png"),
                "type": "context_menu",
            },
        )
        
    def __register_toggle_debug_logging_command(self):
        """
        # add a 'toggle debug logging' command to the engine's context menu
        # note: we make an exception for the shotgun engine which is a
        # special case.
        """
        if self.name != SHOTGUN_ENGINE_NAME:
            self.register_command(
                "Toggle Debug Logging",
                self.__toggle_debug_logging,
                {
                    "short_name": "toggle_debug_logging",
                    "icon": self.__get_platform_resource_path("folder_256.png"),
                    "description": (
                        "Toggles global debug logging on and off in the log manager."
                        "This will affect all logging across all of toolkit."
                    ),
                    "type": "context_menu",
                },
            )       
        
############################################################################
# logging

    def _emit_log_message(self, handler, record):
        """
        Called by the engine to log messages in Clarisse script editor.
        All log messages from the toolkit logging namespace will be passed to
        this method.

        :param handler: Log handler that this message was dispatched from.
                        Its default format is "[levelname basename] message".
        :type handler: :class:`~python.logging.LogHandler`
        :param record: Standard python logging record.
        :type record: :class:`~python.logging.LogRecord`
        """
        # Give a standard format to the message:
        #     Shotgun <basename>: <message>
        # where "basename" is the leaf part of the logging record name,
        # for example "tk-multi-shotgunpanel" or "qt_importer".
        if record.levelno < logging.INFO:
            formatter = logging.Formatter(
                "Debug: Shotgun %(basename)s: %(message)s"
            )
        else:
            formatter = logging.Formatter("Shotgun %(basename)s: %(message)s")

        msg = formatter.format(record)

        # Select Clarisse display function to use according to the logging
        # record level.
        if record.levelno >= logging.ERROR:
            fct = display_error
        elif record.levelno >= logging.WARNING:
            fct = display_warning
        elif record.levelno >= logging.INFO:
            fct = display_info
        else:
            fct = display_debug

        # Display the message in Clarisse script editor in a thread safe manner
        self.async_execute_in_main_thread(fct, msg)

def show_error(msg):
    print("Shotgun Error | Clarisse engine | %s " % msg)
    ix.application.message_box(
        msg,
        ("Shotgun Error | Clarisse engine"),
        ix.api.AppDialog.cancel(),
        ix.api.AppDialog.STYLE_OK,
    )

def show_warning(msg):
    ix.application.message_box(
        msg,
        ("Shotgun Warning | Clarisse engine"),
        ix.api.AppDialog.cancel(),
        ix.api.AppDialog.STYLE_OK,
    )

def show_info(msg):
    ix.application.message_box(
        msg,
        ("Shotgun Info | Clarisse engine"),
        ix.api.AppDialog.cancel(),
        ix.api.AppDialog.STYLE_OK,
    )

def display_error(msg):
    t = time.asctime(time.localtime())
    print("%s - Shotgun Error | Clarisse engine | %s " % (t, msg))
    ix.application.log_error(
        ("%s - Shotgun Error | Clarisse engine | %s " % (t, msg))
    )

def display_warning(msg):
    t = time.asctime(time.localtime())
    ix.application.log_warning(
        ("%s - Shotgun Warning | Clarisse engine | %s " % (t, msg))
    )

def display_info(msg):
    t = time.asctime(time.localtime())
    ix.application.log_info(
        ("%s - Shotgun Info | Clarisse engine | %s " % (t, msg))
    )

def display_debug(msg):
    if os.environ.get("TK_DEBUG") == "1":
        t = time.asctime(time.localtime())
        ix.application.log_info(
        ("%s - Shotgun Debug | Clarisse engine | %s " % (t, msg))
    )