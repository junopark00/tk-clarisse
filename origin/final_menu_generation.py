# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Menu handling for Clarisse

"""

import sys
import os
import unicodedata
import traceback

import sgtk
from sgtk.platform.qt import QtGui, QtCore

import ix


__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"


class MenuGenerator(object):
    """
    Menu generation functionality for Clarisse
    """

    def __init__(self, engine, menu_handle):
        self._engine = engine
        self._menu_handle = menu_handle
        self._menu_name = menu_handle.get_name() + ">"
        self._main_menu_handle = ix.application.get_main_menu()
        self._dialogs = []

    ###########################################################################
    # public methods

    def create_menu(self, *args):
        """
        Render the entire Shotgun menu.
        In order to have commands enable/disable themselves based on the  
        enable_callback, re-create the menu items every time.
        """
        self._menu_handle.remove_all_commands()

        # now add the context item on top of the main menu
        self._context_menu = self._add_context_menu()

        # add menu divider
        self._add_divider(self._menu_name)

        # now enumerate all items and create menu objects for them
        menu_items = []
        for (cmd_name, cmd_details) in self._engine.commands.items():
            self._engine.log_debug(
                "engine command: %s : %s" % (cmd_name, cmd_details)
            )
            menu_items.append(AppCommand(cmd_name, self, cmd_details))

        # sort list of commands in name order
        menu_items.sort(key=lambda x: x.name)

        # now add favourites
        for fav in self._engine.get_setting("menu_favourites"):
            app_instance_name = fav["app_instance"]
            menu_name = fav["name"]

            # scan through all menu items
            for cmd in menu_items:
                if (
                    cmd.get_app_instance_name() == app_instance_name
                    and cmd.name == menu_name
                ):
                    # found our match!
                    cmd.add_command_to_menu(self._menu_name)
                    # mark as a favourite item
                    cmd.favourite = True

        # add menu divider
        self._add_divider(self._menu_name)

        # now go through all of the menu items.
        # separate them out into various sections
        commands_by_app = {}

        for cmd in menu_items:
            if cmd.get_type() == "context_menu":
                # context menu!
                cmd.add_command_to_menu(self._context_menu)

            else:
                # normal menu
                app_name = cmd.get_app_name()
                if app_name is None:
                    # un-parented app
                    app_name = "Other Items"
                if not app_name in commands_by_app:
                    commands_by_app[app_name] = []
                commands_by_app[app_name].append(cmd)

        # now add all apps to main menu
        self._add_app_menu(commands_by_app)

    ###########################################################################
    # context menu and UI

    def _add_divider(self, parent_menu_name):
        menu_item = parent_menu_name + "separator"
        self._main_menu_handle.add_command(menu_item)
        return menu_item

    def _add_sub_menu(self, menu_name, parent_menu_name):
        menu_item = parent_menu_name + menu_name + ">"
        self._main_menu_handle.add_command(menu_item)
        return menu_item

    def _add_menu_item(self, name, parent_menu_name, callback):
        menu_item = parent_menu_name + name
        ix.shotgun.menu_callbacks[menu_item] = callback
        item = self._main_menu_handle.add_command_as_script(
            "ScriptingPython",
            menu_item,
            'ix.shotgun.menu_callbacks["%s"]()' % menu_item,
            "",
            menu_item,
        )
        # item.set_icon(ix.api.GuiResource.save())
        return menu_item

    def _add_context_menu(self):
        """
        Adds a context menu which displays the current context
        """

        ctx = self._engine.context
        ctx_name = str(ctx)

        # create the menu object
        # the label expects a unicode object so we cast it to support when the
        # context may contain info with non-ascii characters

        ctx_menu = self._add_sub_menu(ctx_name, self._menu_name)

        self._add_menu_item("Jump to Flow Production Tracking", ctx_menu, self._jump_to_sg)

        # Add the menu item only when there are some file system locations.
        if ctx.filesystem_locations:
            self._add_menu_item(
                "Jump to File System", ctx_menu, self._jump_to_fs
            )

        # divider (apps may register entries below this divider)
        self._add_divider(ctx_menu)

        return ctx_menu

    def _jump_to_sg(self):
        """
        Jump to shotgun, launch web browser
        """
        url = self._engine.context.shotgun_url
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def _jump_to_fs(self):
        """
        Jump from context to FS
        """
        # launch one window for each location on disk
        paths = self._engine.context.filesystem_locations
        for disk_location in paths:

            # get the setting
            system = sys.platform

            # run the app
            if system == "linux2":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "win32":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)

            exit_code = os.system(cmd)
            if exit_code != 0:
                self._engine.logger.error("Failed to launch '%s'!", cmd)

    ###########################################################################
    # app menus

    def _add_app_menu(self, commands_by_app):
        """
        Add all apps to the main menu, process them one by one.
        """
        for app_name in sorted(commands_by_app.keys()):
            if len(commands_by_app[app_name]) > 1:
                # more than one menu entry fort his app
                # make a sub menu and put all items in the sub menu
                app_menu = self._add_sub_menu(app_name, self._menu_name)

                # get the list of menu cmds for this app
                cmds = commands_by_app[app_name]
                # make sure it is in alphabetical order
                cmds.sort(key=lambda x: x.name)

                for cmd in cmds:
                    cmd.add_command_to_menu(app_menu)
            else:
                # this app only has a single entry.
                # display that on the menu
                # todo: Should this be labelled with the name of the app
                # or the name of the menu item? Not sure.
                cmd_obj = commands_by_app[app_name][0]
                if not cmd_obj.favourite:
                    # skip favourites since they are already on the menu
                    cmd_obj.add_command_to_menu(self._menu_name)


class AppCommand(object):
    """
    Wraps around a single command that you get from engine.commands
    """

    def __init__(self, name, parent, command_dict):
        self.name = name
        self.parent = parent
        self.properties = command_dict["properties"]
        self.callback = command_dict["callback"]
        self.favourite = False

    def get_app_name(self):
        """
        Returns the name of the app that this command belongs to
        """
        if "app" in self.properties:
            return self.properties["app"].display_name
        return None

    def get_app_instance_name(self):
        """
        Returns the name of the app instance, as defined in the environment.
        Returns None if not found.
        """
        if "app" not in self.properties:
            return None

        app_instance = self.properties["app"]
        engine = app_instance.engine

        for (app_instance_name, app_instance_obj) in engine.apps.items():
            if app_instance_obj == app_instance:
                # found our app!
                return app_instance_name

        return None

    def get_documentation_url_str(self):
        """
        Returns the documentation as a str
        """
        if "app" in self.properties:
            app = self.properties["app"]
            doc_url = app.documentation_url
            # deal with nuke's inability to handle unicode. #fail
            if doc_url.__class__ == unicode:
                doc_url = unicodedata.normalize("NFKD", doc_url).encode(
                    "ascii", "ignore"
                )
            return doc_url

        return None

    def get_type(self):
        """
        returns the command type. Returns node, custom_pane or default
        """
        return self.properties.get("type", "default")

    def add_command_to_menu(self, menu):
        """
        Adds an app command to the menu
        """

        # create menu sub-tree if need to:
        # Support menu items seperated by '/'
        parent_menu = menu

        parts = self.name.split("/")
        for item_label in parts[:-1]:
            # see if there is already a sub-menu item
            sub_menu = self._find_sub_menu_item(parent_menu, item_label)
            with open("/RAPA/log.txt", "a") as f:
                f.write("sub_menu: %s\n" % sub_menu)
            if sub_menu:
                # already have sub menu
                parent_menu = sub_menu
            else:
                # create new sub menu
                parent_menu = self.parent._add_sub_menu(item_label, parent_menu)

        self.parent._add_menu_item(
            parts[-1], parent_menu, self._execute_deferred
        )
        with open("/RAPA/log.txt", "a") as f:
            f.write("add_command_to_menu: %s, %s\n" % (parent_menu, parts[-1]))

    def _execute_deferred(self):
        """
        Execute the callback deferred to avoid potential problems with the
        command resulting in the menu being deleted, e.g. if the context 
        changes resulting in an engine restart
        """
        self._execute_within_exception_trap()

    def _execute_within_exception_trap(self):
        """
        Execute the callback and log any exception that gets raised which may 
        otherwise have been swallowed by the deferred execution of the callback
        """

        try:
            ix.application.check_for_events()
            ix.application.disable()

            self.callback()
        except Exception:
            (exc_type, exc_value, exc_traceback) = sys.exc_info()
            message = (
                "Message: Shotgun encountered a problem excutin an action from"
                " the Clarisse engine"
            )
            message += "Exception: %s - %s\n" % (exc_type, exc_value)
            message += "Traceback (most recent call last):\n"
            message += "\n".join(traceback.format_tb(exc_traceback))

            current_engine = sgtk.platform.current_engine()
            current_engine.logger.exception(message)
        finally:
            ix.application.enable()
            ix.application.check_for_events()
            with open("/RAPA/log.txt", "a") as f:
                f.write("callback executed\n")
            
    def _find_sub_menu_item(self, parent_menu_name, menu_name):
        """
        Find the 'sub-menu' menu item with the given label
        """

        menu_item = parent_menu_name + menu_name + ">"
        return ix.shotgun.menu_callbacks.get(menu_item)
