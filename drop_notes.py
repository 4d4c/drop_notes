import json
import os
import urllib.request

import sublime
import sublime_plugin


class DropNotes():
    """
    Upload/Download file from/to Dropbox
    """

    URL_UPLOAD = "https://content.dropboxapi.com/2/files/upload"
    URL_DOWNLOAD = "https://content.dropboxapi.com/2/files/download"


    def __init__(self, file_path):
        self.file_path = file_path
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.read_settings_file()


    def check_file_name(self):
        """
        Check if correct file is selected to upload/download
        """

        if self.file_path.endswith(self.settings["FILENAME"].replace("/", "")):
            return True

        return False


    def read_settings_file(self):
        """
        Read settings file and settings dictionary.
        """

        # Get settings file path from package folder
        settings_filepath = os.path.join(self.current_path, "settings.cfg")

        if os.path.exists(settings_filepath):
            with open(settings_filepath, "r") as settings_file:
                settings = settings_file.read().splitlines()

            self.settings = dict(setting.split('=') for setting in settings)
        else:
            self.settings = {}
            print("[-] ERROR: Settings file is missing")


    def download_file(self):
        """
        Download file from Dropbox and return binary data of file content
        """

        if not self.check_file_name():
            print("[-] Incorrect file - " + self.file_path)
            return False

        headers = {
            "Authorization": "Bearer " + self.settings["DROPBOX_TOKEN"],
            "Dropbox-API-Arg": json.dumps({
                "path": self.settings["FILENAME"],
            }),
        }

        try:
            request = urllib.request.Request(self.URL_DOWNLOAD, headers=headers, method="POST")
            response = urllib.request.urlopen(request)

            if response.getcode() >= 200:
                print("[+] Downloaded file")
            else:
                print("[-] Download failed")

            return response.read()
        except Exception as e:
            print("[-] Download failed")
            print(e)
            return False


    def upload_file(self):
        """
        Upload current file to Dropbox
        """

        if not self.check_file_name():
            print("[-] Incorrect file - " + self.file_path)
            return False

        headers = {
            "Authorization": "Bearer " + self.settings["DROPBOX_TOKEN"],
            "Dropbox-API-Arg": json.dumps({
                "path": self.settings["FILENAME"],
                "mode": "overwrite",
                "autorename": False,
                "mute": True,
                "strict_conflict": False,
            }),
            "Content-Type": "application/octet-stream",
            "Content-Length": os.stat(self.file_path).st_size
        }

        try:
            with open(self.file_path, "rb") as tmp_file:
                request = urllib.request.Request(self.URL_UPLOAD, tmp_file, headers=headers)
                response = urllib.request.urlopen(request)

                if response.getcode() == 200:
                    print("[+] Uploaded file")
                else:
                    print("[-] Upload failed")

                return True
        except Exception as e:
            print("[-] Upload failed")
            print(e)
            return False


class DownloadDropbox(sublime_plugin.TextCommand):
    """
    Download file from Dropbox
    """

    def run(self, edit):
        file_path = self.view.window().active_view().file_name()

        drop_notes = DropNotes(file_path)
        file_data = drop_notes.download_file()

        if file_data:
            self.view.erase(edit, sublime.Region(0, self.view.size()))

            self.view.insert(edit, 0, file_data.decode().replace("\r", ""))


class UploadDropbox(sublime_plugin.TextCommand):
    """
    Upload file to Dropbox
    """

    def run(self, edit):
        file_path = self.view.window().active_view().file_name()

        drop_notes = DropNotes(file_path)
        drop_notes.upload_file()
