import ftputil
import ftplib
import json
import sys
import subprocess
from subprocess import CompletedProcess
import os
import time

from textual.app import App, ComposeResult
from textual.containers import VerticalGroup, HorizontalGroup, VerticalScroll
from textual.widgets import Button, Digits, Footer, Header, Label
from textual import on

from textual_fspicker import FileOpen



class FilesExplorer_File(HorizontalGroup):
    def __init__(self, file_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_name = file_name
    
    def compose(self) -> ComposeResult:
        yield Button(f"F | {self.file_name}", id="main-btn", classes="long-button", variant="primary")
        yield Button("Download", id="download-btn", variant="success")
        yield Button("Delete", id="delete-btn", variant="error")
    
    def download_file(self, file: str) -> None:
        self.app.ftp_manager.download_file(file)
        self.app.notify(f"File '{file}' Downloaded Succesfully!")
    
    def delete_file(self, file: str) -> None:
        self.app.ftp_manager.delete_file(file)
        self.app.notify(f"File '{file}' Deleted!")
        self.app.refresh(recompose=True)
    
    @on(Button.Pressed)
    def handle_file_download(self, event: Button.Pressed) -> None:
        button = event.button
        match button.id:
            case "main-btn": self.download_file(self.file_name)
            case "download-btn": self.download_file(self.file_name)
            case "delete-btn": self.delete_file(self.file_name)

class FilesExplorer_Folder(HorizontalGroup):
    def __init__(self, folder_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.folder_name = folder_name
    
    def compose(self) -> ComposeResult:
        yield Button(f"D | {self.folder_name}", id="main-btn", classes="long-button", variant="warning")
        yield Button("Brow", id="brow-btn", variant="success")
        yield Button("Download", id="download-btn", variant="success")
        yield Button("Delete", id="delete-btn", variant="error")
    
    def delete_folder(self, folder_name: str) -> None:
        self.app.ftp_manager.delete_folder(folder_name)
        self.app.notify(f"Folder '{folder_name}' Deleted !")
    
    def download_folder(self, folder_name: str) -> None:
        self.app.ftp_manager.download_folder(folder_name)
        self.app.notify(f"Folder '{folder_name}' Fully Downloaded !")
    
    @on(Button.Pressed)
    def handle_folder_interaction(self, event: Button.Pressed) -> None:
        button = event.button

        match button.id:
            case "main-btn": self.app.ftp_manager.change_dir(self.folder_name)
            case "brow-btn": self.app.ftp_manager.change_dir(self.folder_name)
            case "download-btn": self.download_folder(self.folder_name)
            case "delete-btn": self.delete_folder(self.folder_name)
        
        self.app.refresh(recompose = True)

class FTP_Client_FilesExplorer(VerticalGroup):
    host_current_dir: str = ""

    def compose(self) -> ComposeResult:
        self.host_current_dir = self.app.ftp_manager.get_cur_dir()
        dir_content: list = []
        for dir_element in self.app.ftp_manager.list_dir(self.host_current_dir):
            dir_content.append(dir_element)

        with HorizontalGroup(classes="file-explorer-top-section"):
            yield Button("Create New Directory", id="new-dir-btn", classes="long-button file-explorer-top-section-button", variant="primary")
            yield Button("Upload", id="upload-file-btn", classes="long-button file-explorer-top-section-button", variant="primary")
        yield Label(f"Current Location: {self.host_current_dir}", classes="file-explorer-current-location-text")
        if self.app.ftp_manager.get_cur_dir() != "/": yield Button("..", id="go-back-btn", classes="long-button", variant="success")
        with VerticalScroll():
            for dir_element in dir_content:
                if self.app.ftp_manager.ftp_host.path.isdir(dir_element): yield FilesExplorer_Folder(dir_element)
                else: yield FilesExplorer_File(dir_element)
        #yield FileOpen(title="ee",open_button="r",cancel_button="t")
    
    @on(Button.Pressed)
    def handle_top_actions(self, event: Button.Pressed) -> None:
        button = event.button

        match button.id:
            case "go-back-btn":
                self.app.ftp_manager.change_dir("..")
                self.app.refresh(recompose=True)
            case "new-dir-btn": self.new_dir()
            case "upload-file-btn": pass
    
    def new_dir(self):
        completed_process: CompletedProcess = subprocess.run(
            ["kitty", "python3", os.path.join(os.path.dirname(__file__), "newdir_dialog.py")],
            capture_output=True, text=True
        )
        if completed_process.returncode == 0:
            new_dir_name: str = ""
            with open(os.path.join(os.path.dirname(__file__), "newdir_dialog_output.txt"), "r") as ndo:
                new_dir_name = ndo.read()
                ndo.close()
            os.remove(os.path.join(os.path.dirname(__file__), "newdir_dialog_output.txt"))
            if self.app.ftp_manager.new_dir(new_dir_name):
                self.app.refresh(recompose = True)
                self.app.notify(f"Directory '{new_dir_name}' Created !")
            else: self.app.notify(f"Directory '{new_dir_name}' Already Exist In The Current Directory")
        else: self.app.notify(f"Cannot Create Directory", variant="error")

class Profile():
    def __init__(self, name: str, adress: str, username: str, password: str, port: int):
        self.name: str       = name
        self.adress: str     = adress
        self.username: str   = username
        self.password: str   = password
        self.port: int       = port

class ProfileButton(Button):
    """Un bouton personnalisé qui garde en mémoire l'index de son profil."""
    def __init__(self, label: str, profile_index: int, *args, **kwargs):
        super().__init__(label, *args, **kwargs)
        self.profile_index: int = profile_index

class FTP_Client_ProfilesMenu(VerticalGroup):
    profiles_location_path: str = os.path.join(os.path.dirname(__file__), "profiles")
    profiles_list: list = []
    default_profile: Profile = None

    def compose(self) -> ComposeResult:
        yield Label("Select a profile:")

        self.load_profiles()
        with HorizontalGroup():
            for idx, profile in enumerate(self.profiles_list):
                yield ProfileButton(
                    label =           profile.name, 
                    profile_index =   idx,
                    variant =         "success"
                )
    
    @on(Button.Pressed)
    def handle_profile_selection(self, event: Button.Pressed) -> None:
        button = event.button
        global profile_seclected
        profile_seclected = self.profiles_list[button.profile_index]

        self.app.ftp_manager.create_ftp_host()
        global root_path
        root_path = self.app.ftp_manager.ftp_host.getcwd()
        self.app.profile_mode = False
        self.app.refresh(recompose = True)
    
    def load_profiles(self) -> None:
        temp_profiles_list = os.listdir(self.profiles_location_path)
        temp_profiles_list.remove("profile_template.json")

        if len(temp_profiles_list) <= 0: self.app.action_quit()
        for profile_file in temp_profiles_list:
            with open(os.path.join(self.profiles_location_path, profile_file), "r") as pf:
                profile_data = json.loads(pf.read())
                profile_name = profile_file.replace("profile_", "").replace(".json", "")
                self.profiles_list.append(Profile(
                    profile_name,
                    profile_data["adress"],
                    profile_data["user"],
                    profile_data["password"],
                    profile_data["port"]
                ))

class FTP_Manager():
    def __init__(self):
        self.ftp_host: ftputil.FTPHost = None
        self.local_path = "/home/wolfyd3v/Documents/"
        self.local_path = self.local_path.replace('"', '').replace("'", "")
    
    def create_ftp_host(self) -> None:
        if not(profile_seclected): return

        session_factory: ftplib.FTP = ftplib.FTP
        session_factory.port = profile_seclected.port
        self.ftp_host = ftputil.FTPHost(
            profile_seclected.adress,
            profile_seclected.username,
            profile_seclected.password,
            session_factory = session_factory
        )
    
    def download_file(self, file: str) -> None:
        self.ftp_host.download(file, f"{self.local_path}/{file}")
    
    def delete_file(self, file: str) -> None:
        self.ftp_host.remove(file)
    

    def delete_folder(self, folder_name: str) -> None:
        self.ftp_host.rmtree(folder_name)
    
    def change_dir(self, new_dir: str) -> None:
        self.ftp_host.chdir(new_dir)
    
    def get_cur_dir(self) -> str:
        return self.ftp_host.getcwd()

    def new_dir(self, new_dir_name: str) -> bool:
        if not self.ftp_host.path.exists(new_dir_name):
            self.ftp_host.mkdir(new_dir_name)
            return True
        return False

    def list_dir(self, directory: str) -> list:
        return self.ftp_host.listdir(directory)

    def download_folder(self, folder: str) -> None:
        if not os.path.exists(self.local_path + folder): os.mkdir(self.local_path + folder)

        for root, dirs, files in self.ftp_host.walk(folder):
            # Calcul du chemin relatif
            rel_path = os.path.relpath(root, folder)
            local_root = os.path.join(self.local_path + folder, rel_path)

            # Créer le dossier local
            os.makedirs(local_root, exist_ok=True)

            # Télécharger les fichiers
            for file in files:
                remote_file = self.ftp_host.path.join(root, file)
                local_file = os.path.join(local_root, file)

                self.ftp_host.download(remote_file, local_file)
                print(f"File '{file}' Downloaded Succesfully!")
                time.sleep(0.1)

class FTP_Client(App):
    BINDINGS = [("q", "quit", "Quit the app")]
    CSS_PATH = "style.tcss"

    profile_mode: bool = True
    ftp_manager: FTP_Manager = FTP_Manager()

    def compose(self) -> ComposeResult:
        yield Header()

        if self.profile_mode: yield FTP_Client_ProfilesMenu()
        else: yield FTP_Client_FilesExplorer()

        yield Footer()



profile_seclected: Profile = None
root_path: str = ""

if __name__ == "__main__":
    ftp_client: FTP_Client = FTP_Client()
    ftp_client.run()