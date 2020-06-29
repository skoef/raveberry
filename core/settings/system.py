"""This module handles all settings related to system configuration."""
from __future__ import annotations

import configparser
import os
import re
import shutil
import subprocess
import time
from typing import Dict, TYPE_CHECKING, Tuple, Optional, List

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.http import HttpResponseBadRequest

from core.settings.settings import Settings
from core.util import background_thread

if TYPE_CHECKING:
    from core.base import Base


class System:
    """This class is responsible for handling settings changes related to system configuration."""

    @staticmethod
    def _get_mopidy_config() -> str:
        if shutil.which("cava"):
            # if cava is installed, use the visualization config for mopidy
            config_file = os.path.join(settings.BASE_DIR, "setup/mopidy_cava.conf")
        else:
            config_file = os.path.join(settings.BASE_DIR, "setup/mopidy.conf")
        return config_file

    @staticmethod
    def update_mopidy_config(config_file=None,) -> None:
        """Updates mopidy's config with the credentials stored in the database.
        If no config_file is given, the default one is used."""
        if settings.DOCKER:
            # raveberry cannot restart mopidy in the docker setup
            return

        if config_file is None:
            config_file = System._get_mopidy_config()

        spotify_username = Settings.get_setting("spotify_username", "")
        spotify_password = Settings.get_setting("spotify_password", "")
        spotify_client_id = Settings.get_setting("spotify_client_id", "")
        spotify_client_secret = Settings.get_setting("spotify_client_secret", "")
        soundcloud_auth_token = Settings.get_setting("soundcloud_auth_token", "")

        subprocess.call(
            [
                "sudo",
                "/usr/local/sbin/raveberry/update_mopidy_config",
                config_file,
                spotify_username,
                spotify_password,
                spotify_client_id,
                spotify_client_secret,
                soundcloud_auth_token,
            ]
        )
        subprocess.call(["sudo", "/usr/local/sbin/raveberry/restart_mopidy"])
        time.sleep(3)

    def __init__(self, base: "Base"):
        self.base = base

    def check_mopidy_extensions(self) -> Dict[str, Tuple[bool, str]]:
        """Returns a dict indicating for each extension whether it is enabled
        and provides a message.
        Handles both service and user mopidy instances."""
        try:
            subprocess.check_call(
                ["systemctl", "is-active", "mopidy"], stdout=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            extensions = self._check_mopidy_extensions_user()
        else:
            extensions = self._check_mopidy_extensions_service()
        return extensions

    def _check_mopidy_extensions_user(self) -> Dict[str, Tuple[bool, str]]:
        config = subprocess.run(
            ["mopidy", "config"],
            stdout=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        ).stdout
        parser = configparser.ConfigParser()
        parser.read_string(config)
        extensions = {}
        for extension in ["spotify", "enabled"]:
            try:
                if parser[extension]["enabled"] == "true":
                    extensions[extension] = (
                        True,
                        "Extension probably functional",
                    )
            except KeyError:
                extensions[extension] = (False, "Extension disabled")
        return extensions

    def _check_mopidy_extensions_service(self) -> Dict[str, Tuple[bool, str]]:
        # check the mopidy log and see if there is a spotify login error since the last restart
        log = subprocess.check_output(
            ["sudo", "/usr/local/sbin/raveberry/read_mopidy_log"],
            universal_newlines=True,
        )

        extensions = {}
        for line in log.split("\n")[::-1]:
            if "spotify" not in extensions:
                if line.startswith("ERROR") and "spotify.session" in line:
                    extensions["spotify"] = (False, "User or Password are wrong")
                elif line.startswith("ERROR") and "mopidy_spotify.web" in line:
                    extensions["spotify"] = (
                        False,
                        "Client ID or Client Secret are wrong or expired",
                    )
                elif (
                    line.startswith("WARNING")
                    and "spotify" in line
                    and "The extension has been automatically disabled" in line
                ):
                    extensions["spotify"] = (False, "Configuration Error")

            if "soundcloud" not in extensions:
                if line.startswith("ERROR") and 'Invalid "auth_token"' in line:
                    extensions["soundcloud"] = (False, "auth_token is invalid")
                elif (
                    line.startswith("WARNING")
                    and "soundcloud" in line
                    and "The extension has been automatically disabled" in line
                ):
                    extensions["soundcloud"] = (False, "Configuration Error")

            if "spotify" in extensions and "soundcloud" in extensions:
                break

            if line.startswith("Started Mopidy music server."):
                if "spotify" not in extensions:
                    extensions["spotify"] = (True, "Login successful")
                if "soundcloud" not in extensions:
                    extensions["soundcloud"] = (True, "auth_token valid")
                break
        else:
            # there were too many lines in the log, could not determine whether there was an error
            if "spotify" not in extensions:
                extensions["spotify"] = (True, "No info found, enabling te be safe")
            if "soundcloud" not in extensions:
                extensions["soundcloud"] = (True, "No info found, enabling te be safe")
        return extensions

    @Settings.option
    def enable_streaming(self, _request: WSGIRequest) -> HttpResponse:
        """Enable icecast streaming."""
        icecast_exists = False
        for line in subprocess.check_output(
            "systemctl list-unit-files --full --all".split(), universal_newlines=True
        ).splitlines():
            if "icecast2.service" in line:
                icecast_exists = True
                break

        if not icecast_exists:
            return HttpResponseBadRequest("Please install icecast2")

        subprocess.call(["sudo", "/usr/local/sbin/raveberry/enable_streaming"])
        config_file = os.path.join(settings.BASE_DIR, "setup/mopidy_icecast.conf")
        self.update_mopidy_config(config_file)
        return HttpResponse()

    @Settings.option
    def disable_streaming(self, _request: WSGIRequest) -> HttpResponse:
        """Disable icecast streaming."""
        subprocess.call(["sudo", "/usr/local/sbin/raveberry/disable_streaming"])
        self.update_mopidy_config()
        return HttpResponse()

    @Settings.option
    def disable_events(self, _request: WSGIRequest) -> None:
        """Disable websocket support."""
        subprocess.call(["sudo", "/usr/local/sbin/raveberry/disable_events"])

    @Settings.option
    def enable_events(self, _request: WSGIRequest) -> None:
        """Enable websocket support."""
        subprocess.call(["sudo", "/usr/local/sbin/raveberry/enable_events"])

    @Settings.option
    def disable_hotspot(self, _request: WSGIRequest) -> None:
        """Disable the wifi created by Raveberry."""
        subprocess.call(["sudo", "/usr/local/sbin/raveberry/disable_hotspot"])

    @Settings.option
    def enable_hotspot(self, _request: WSGIRequest) -> None:
        """Enable the wifi created by Raveberry."""
        subprocess.call(["sudo", "/usr/local/sbin/raveberry/enable_hotspot"])

    @Settings.option
    def unprotect_wifi(self, _request: WSGIRequest) -> None:
        """Disable password protection of the hotspot, making it public."""
        subprocess.call(["sudo", "/usr/local/sbin/raveberry/unprotect_wifi"])

    @Settings.option
    def protect_wifi(self, _request: WSGIRequest) -> None:
        """Enable password protection of the hotspot.
        The password was defined during setup."""
        subprocess.call(["sudo", "/usr/local/sbin/raveberry/protect_wifi"])

    @Settings.option
    def disable_tunneling(self, _request: WSGIRequest) -> None:
        """Disable forwarding of packets to the other network (probably the internet)."""
        subprocess.call(["sudo", "/usr/local/sbin/raveberry/disable_tunneling"])

    @Settings.option
    def enable_tunneling(self, _request: WSGIRequest) -> None:
        """Enable forwarding of packets to the other network.
        Enables clients connected to the hotspot to browse the internet (if available)."""
        subprocess.call(["sudo", "/usr/local/sbin/raveberry/disable_tunneling"])
        subprocess.call(["sudo", "/usr/local/sbin/raveberry/enable_tunneling"])

    @Settings.option
    def disable_remote(self, _request: WSGIRequest) -> None:
        """Disables the connection to an external server."""
        subprocess.call(["sudo", "/usr/local/sbin/raveberry/disable_remote"])

    @Settings.option
    def enable_remote(self, _request: WSGIRequest) -> None:
        """Enables the connection to an external server.
        Allows this instance to be reachable from a public domain."""
        subprocess.call(["sudo", "/usr/local/sbin/raveberry/enable_remote"])

    @Settings.option
    def reboot_server(self, _request: WSGIRequest) -> None:
        """Restarts the server."""
        subprocess.call(["sudo", "/usr/local/sbin/raveberry/reboot_server"])

    @Settings.option
    def reboot_system(self, _request: WSGIRequest) -> None:
        """Reboots the system."""
        subprocess.call(["sudo", "/usr/local/sbin/raveberry/reboot_system"])

    @Settings.option
    def get_latest_version(self, _request: WSGIRequest) -> HttpResponse:
        """Looks up the newest version number from PyPi and returns it."""
        try:
            subprocess.run(
                "pip3 install raveberry==nonexistingversion".split(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            # parse the newest verson from pip output
            for line in e.stderr.splitlines():
                if "from versions" in line:
                    versions = [re.sub(r"[^0-9.]", "", token) for token in line.split()]
                    versions = [version for version in versions if version]
                    latest_version = versions[-1]
                    return HttpResponse(latest_version)
        return HttpResponseBadRequest("Could not determine latest version.")

    @Settings.option
    def get_upgrade_config(self, _request: WSGIRequest) -> HttpResponse:
        """Returns the config that will be used for the upgrade."""
        with open(os.path.join(settings.BASE_DIR, "config/raveberry.ini")) as f:
            config = f.read()
        lines = config.splitlines()
        lines = [line for line in lines if not line.startswith("#")]
        return HttpResponse("\n".join(lines))

    @Settings.option
    def upgrade_raveberry(self, _request: WSGIRequest) -> HttpResponse:
        """Performs an upgrade of raveberry."""

        @background_thread
        def do_upgrade() -> None:
            subprocess.call(
                [
                    "sudo",
                    "/usr/local/sbin/raveberry/upgrade_raveberry",
                    os.path.join(settings.BASE_DIR, "config/raveberry.ini"),
                ]
            )

        do_upgrade()

        return HttpResponse("Upgrading... Look for logs in /var/www/")
