# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys

import sgtk
from sgtk.platform import SoftwareLauncher, SoftwareVersion, LaunchInformation


__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"


class ClarisseLauncher(SoftwareLauncher):
    """
    Handles launching Clarisse executables. Automatically starts up
    a tk-clarisse engine with the current context in the new session
    of Clarisse.
    """

    # Named regex strings to insert into the executable template paths when
    # matching against supplied versions and products. Similar to the glob
    # strings, these allow us to alter the regex matching for any of the
    # variable components of the path in one place
    COMPONENT_REGEX_LOOKUP = {
        "version": r"[\d.]+",
        "product": r"[A-Za-z]+",
    }
    # This dictionary defines a list of executable template strings for each
    # of the supported operating systems. The templates are used for both
    # globbing and regex matches by replacing the named format placeholders
    # with an appropriate glob or regex string.
    CLARISSE_PRODUCTS = [
        "Clarisse",
    ]
    # Clarisse can be installed in different locations, since we cannot predict
    # where it will be located, we resort to letting the user define an
    # environment variable that points to the folder location where the
    # executable is located, that way we cover all cases. The disadvantage of
    # this is that we do not get a version number out of it.
    EXECUTABLE_TEMPLATES = {
        "darwin": [
            # /Applications/Clarisse5.0.11/clarisse
            "/Applications/Clarisse{version}/clarisse.app",
        ],
        "win32": [
            # C:/Program Files/Clarisse5.0.11/clarisse.exe
            r"C:\Program Files\Clarisse{version}\clarisse.exe",
        ],
        "linux": [
            # /opt/Clarisse5.0.11/clarisse/clarisse
            "/opt/Clarisse{version}/clarisse/clarisse-py2",
            # /home/<username>/Clarisse5.0.11/clarisse
            os.path.expanduser("~/Clarisse{version}/clarisse/clarisse-py2"),
        ],
    }
    @property
    def minimum_supported_version(self):
        """
        The minimum software version that is supported by the launcher.
        """
        return "3.6"

    def prepare_launch(self, exec_path, args, file_to_open=None):
        """
        Prepares an environment to launch Clarisse in that will automatically
        load Toolkit and the tk-clarisse engine when Clarisse starts.

        :param str exec_path: Path to Clarisse executable to launch.
        :param str args: Command line arguments as strings.
        :param str file_to_open: (optional) Full path name of a file to open on
                                 launch.
        :returns: :class:`LaunchInformation` instance
        """
        required_env = {}

        # Run the engine's userSetup.py file when Clarisse starts up
        # by appending it to the env PYTHONPATH.
        startup_path = os.path.join(
            self.disk_location, "startup", "userSetup.py"
        )
        sgtk.util.append_path_to_env_var(
            "CLARISSE_STARTUP_SCRIPT", startup_path
        )
        required_env["CLARISSE_STARTUP_SCRIPT"] = os.environ[
            "CLARISSE_STARTUP_SCRIPT"
        ]

        # Prepare the launch environment with variables required by the
        # classic bootstrap approach.
        self.logger.debug(
            "Preparing Clarisse Launch via Toolkit Classic methodology ..."
        )
        required_env["SGTK_ENGINE"] = self.engine_name
        required_env["SGTK_CONTEXT"] = sgtk.context.serialize(self.context)

        if file_to_open:
            # Add the file name to open to the launch environment
            required_env["SGTK_FILE_TO_OPEN"] = file_to_open

        return LaunchInformation(exec_path, args, required_env)

    ###########################################################################
    # private methods
    def _icon_from_engine(self):
        """
        Use the default engine icon as clarisse does not supply
        an icon in their software directory structure.

        :returns: Full path to application icon as a string or None.
        """

        # the engine icon
        engine_icon = os.path.join(self.disk_location, "icon_256.png")
        return engine_icon

    def scan_software(self):
        """
        Scan the filesystem for clarisse executables.

        :return: A list of :class:`SoftwareVersion` objects.
        """
        self.logger.debug("Scanning for Clarisse executables...")

        supported_sw_versions = []
        for sw_version in self._find_software():
            (supported, reason) = self._is_supported(sw_version)
            if supported:
                supported_sw_versions.append(sw_version)
            else:
                self.logger.debug(
                    "SoftwareVersion %s is not supported: %s"
                    % (sw_version, reason)
                )

        return supported_sw_versions

    def _find_software(self):
        """
        Find executables in the default install locations.
        """

        # all the executable templates for the current OS
        executable_templates = self.EXECUTABLE_TEMPLATES.get(sys.platform, [])

        # all the discovered executables
        sw_versions = []

        for executable_template in executable_templates:
            executable_template = os.path.expanduser(executable_template)
            executable_template = os.path.expandvars(executable_template)

            self.logger.debug("Processing template %s", executable_template)

            executable_matches = self._glob_and_match(
                executable_template, self.COMPONENT_REGEX_LOOKUP
            )

            # Extract all products from that executable.
            for (executable_path, key_dict) in executable_matches:

                # extract the matched keys form the key_dict.
                # in the case of version we return something different than
                # an empty string because there are cases were the installation
                # directories do not include version number information.
                executable_version = key_dict.get("version", " ")
                if "minor" in key_dict:
                    executable_version += key_dict["minor"]
                if "service_pack" in key_dict:
                    executable_version += " " + key_dict["service_pack"]

                sw_versions.append(
                    SoftwareVersion(
                        executable_version,
                        "Clarisse",
                        executable_path,
                        self._icon_from_engine(),
                    )
                )

        return sw_versions