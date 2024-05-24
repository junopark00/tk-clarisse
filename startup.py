# Copyright (c) 2024 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


import os

import sgtk
from sgtk.platform import SoftwareLauncher, SoftwareVersion, LaunchInformation


class ClarisseLauncher(SoftwareLauncher):
    """
    Handles launching Clarisse executables. Automatically starts up a tk-katana
    engine with the current context in the new session of Clarisse.
    """

    # Named regex strings to insert into the executable template paths when
    # matching against supplied versions and products. Similar to the glob
    # strings, these allow us to alter the regex matching for any of the
    # variable components of the path in one place

    COMPONENT_REGEX_LOOKUP = {
        "version": r"[\d.]+",
        "product": r"[A-Za-z]+",
    }

    # Templates for all the display names of the products supported by Clarisse
    CLARISSE_PRODUCTS = [
        "Clarisse",
    ]

    # This dictionary defines a list of executable template strings for each
    # of the supported operating systems. The templates can are used for both
    # globbing and regex matches by replacing the named format placeholders
    # with an appropriate glob or regex string. As Side FX adds modifies the
    # install path on a given OS for a new release, a new template will need
    # to be added here.
    EXECUTABLE_MATCH_TEMPLATES = {
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

    def _get_icon_from_product(self, product):
        """
        Returns the icon based on the product.

        :param str product: Product name.

        :returns: Path to the product's icon.
        """
        if "clarisse" in product.lower():
            return os.path.join(self.disk_location, "icon_256.png")

    def scan_software(self):
        """
        For each software executable that was found, get the software products for it.

        :returns: List of :class:`SoftwareVersion`.
        """
        softwares = []
        self.logger.debug("Scanning for Clarisse software...")
        for sw in self._find_software():
            supported, reason = self._is_supported(sw)
            if supported:
                softwares.append(sw)
            else:
                self.logger.debug(reason)

        return softwares

    def _find_software(self):
        """
        Finds all Clarisse software on disk.

        :returns: Generator of :class:`SoftwareVersion`.
        """
        # Get all the executable templates for the current OS
        executable_templates = self.EXECUTABLE_MATCH_TEMPLATES.get(
            "darwin"
            if sgtk.util.is_macos()
            else "win32"
            if sgtk.util.is_windows()
            else "linux"
            if sgtk.util.is_linux()
            else []
        )

        # Certain platforms have more than one location for installed software
        for template in executable_templates:
            self.logger.debug("Processing template %s.", template)
            # Extract all products from that executable.
            for executable, tokens in self._glob_and_match(
                template, self.COMPONENT_REGEX_LOOKUP
            ):
                self.logger.debug("Processing %s with tokens %s", executable, tokens)
                for sw in self._extract_products_from_path(executable, tokens):
                    yield sw

    def _extract_products_from_path(self, executable_path, match):
        """
        Extracts the products from an executable. Note that more than one product
        can be extracted from a single executable on certain platforms.

        :param str executable_path: Path to the executable.
        :param match: Tokens that were extracted from the executable.

        :returns: Generator that generates each product that can be launched from the given
            executable.
        """
        executable_version = match.get("version")
        if sgtk.util.is_macos():
            # Extract the product from the file path, as each product of the product has an actual
            # executable associated to it.

            # extract the components (default to None if not included)
            executable_product = match.get("product")
            # If there is no suffix (Non-commercial or PLE), we'll simply use an empty string).
            executable_suffix = match.get("suffix") or ""

            # Generate the display name.
            product = "%s%s" % (executable_product, executable_suffix)

            yield SoftwareVersion(
                executable_version,
                product,
                executable_path,
                self._get_icon_from_product(executable_product),
            )
        else:
            for product in self._get_products_from_version(executable_version):
                # Figure out the arguments required for each product.
                arguments = []

                sw = SoftwareVersion(
                    executable_version,
                    product,
                    executable_path,
                    self._get_icon_from_product(product),
                    arguments,
                )
                yield sw

    def _get_products_from_version(self, version):
        """
        Get the name of the products for a given Clarisse version.

        :param str version: Clarisse version in the format <Major>.<Minor>.<Patch>

        :returns: List of product names.
        """
        # Clarisse versions formatting is <Major>.<Minor>.<patch>.
        # This will grab the major version.

        return self.CLARISSE_PRODUCTS

    def _is_supported(self, version):
        """
        Ensures that a product is supported by the launcher and that the version is valid.

        :param version: Checks is a given software version is supported.
        :type version: :class:`sgtk.platform.SoftwareVersion`

        :returns: ``True`` if supported, ``False`` if not.
        """
        if version.product not in self._get_products_from_version(version.version):
            return False, "Toolkit does not support '%s'." % version.product

        return super(ClarisseLauncher, self)._is_supported(version)

    @property
    def minimum_supported_version(self):
        """
        Minimum supported version by this launcher.
        """
        return "3.6"

    def prepare_launch(self, exec_path, args, file_to_open=None):
        """
        Prepares the given software for launch

        :param str exec_path: Path to DCC executable to launch
        :param str args: Command line arguments as strings
        :param str file_to_open: (optional) Full path name of a file to open on
            launch

        :returns: :class:`LaunchInformation` instance
        """
        required_env = {}

        # Add context information info to the env.
        required_env["SGTK_CONTEXT"] = sgtk.Context.serialize(self.context)
        required_env["SGTK_ENGINE"] = self.engine_name

        self.logger.debug("Launch environment: %s", required_env)

        return LaunchInformation(exec_path, args, required_env)
