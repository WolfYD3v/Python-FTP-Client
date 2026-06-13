import ftputil
import ftplib
import json
import subprocess
from subprocess import CompletedProcess
import os
import time

from textual.app import App, ComposeResult
from textual.containers import VerticalGroup, HorizontalGroup, VerticalScroll
from textual.widgets import Button, Footer, Header, Label
from textual import on

from textual_fspicker import FileOpen, SelectDirectory



class FilesExplorer_File(HorizontalGroup):
    def __init__(self, file_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_name = file_name
    
    def compose(self) -> ComposeResult:
        yield Button(f"🖹 | {self.file_name}", id="main-btn", classes="long-button", variant="primary")
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
        yield Button(f"🗁  | {self.folder_name}   [{self.app.ftp_manager.count_files_at(self.folder_name)}]", id="main-btn", classes="long-button", variant="warning")
        yield Button("Brow", id="brow-btn", variant="success")
        yield Button("Download", id="download-btn", variant="success")
        yield Button("Delete", id="delete-btn", variant="error")
    
    def delete_folder(self, folder_name: str) -> None:
        self.app.ftp_manager.delete_dir(folder_name)
        self.app.notify(f"Folder '{folder_name}' Deleted !")
    
    def download_folder(self, folder_name: str) -> None:
        self.app.ftp_manager.download_dir(folder_name)
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
        self.host_current_dir = self.app.ftp_manager.get_current_dir()
        dir_content: list = []
        for dir_element in self.app.ftp_manager.list_dir(self.host_current_dir):
            dir_content.append(dir_element)

        with HorizontalGroup(classes="file-explorer-top-section"):
            yield Button("Create New Directory", id="new-dir-btn", classes="long-button file-explorer-top-section-button", variant="primary")
            yield Button("Upload File", id="upload-file-btn", classes="long-button file-explorer-top-section-button", variant="primary")
            yield Button("Upload Directory", id="upload-dir-btn", classes="long-button file-explorer-top-section-button", variant="primary")
        yield Label(f"Current Location: {self.host_current_dir}", classes="file-explorer-current-location-text")
        if self.app.ftp_manager.get_current_dir() != "/": yield Button("..", id="go-back-btn", classes="long-button", variant="success")
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
            case "upload-file-btn": self.app.push_screen(FileOpen(
                location=".",
                open_button="Upload"
            ), callback=self.upload)
            case "upload-dir-btn": self.app.push_screen(SelectDirectory(
                location=".",
                select_button="Upload"
            ), callback=self.upload)
    
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
    
    def upload(self, upload_path: str) -> None:
        if upload_path == None: return

        _upload_path: str = str(upload_path)
        _upload_path.strip()
        _upload_path.replace('"', '').replace("'", "")

        if os.path.isfile(_upload_path):
            self.app.ftp_manager.upload_file(_upload_path)
            self.app.notify(f"File '{os.path.basename(_upload_path)}' Uploaded Succesfully!")
        else:
            self.app.ftp_manager.upload_dir(_upload_path)
            self.app.notify(f"Directory '{os.path.basename(_upload_path)}' Uploaded Succesfully!")

        self.app.refresh(recompose=True)


''' The Profile Class '''
class Profile():
    def __init__(self, name: str, adress: str, username: str, password: str, port: int, description: str):
        self.name: str          = name
        self.adress: str        = adress
        self.username: str      = username
        self.password: str      = password
        self.port: int          = port
        self.description: str   = description

''' The Profile Selector Card, displaying some informations '''
class ProfileSelector(HorizontalGroup):
    def __init__(self, profile: Profile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile: Profile = profile
        self.label: str = profile.name
    
    def compose(self) -> ComposeResult:
        yield Button(self.label, variant="success")
        yield VerticalGroup(
            Label(self.profile.description),
            Label(f"ftp://{self.profile.username}:{self.profile.password}@{self.profile.adress}:{self.profile.port}")
        )
    
    @on(Button.Pressed)
    def handle_profile_selection(self, event: Button.Pressed) -> None:
        global profile_seclected
        profile_seclected = self.profile

        self.app.ftp_manager.create_ftp_host()
        self.app.profile_mode = False
        self.app.refresh(recompose = True)

''' The Profile Selection Menu of the Client '''
class FTP_Client_ProfilesMenu(VerticalGroup):
    profiles_location_path: str = os.path.join(os.path.dirname(__file__), "profiles")
    profiles_list: list = []
    default_profile: Profile = None

    def compose(self) -> ComposeResult:
        yield Label("Select a profile:")

        self.load_profiles()
        with VerticalGroup():
            for profile in self.profiles_list:
                yield ProfileSelector(profile)
    
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
                    profile_data["port"],
                    profile_data["description"]
                ))

''' The FTP Manager Class, where all the FTP related functions are '''
class FTP_Manager():
    def __init__(self):
        self.ftp_host: ftputil.FTPHost = None
        self.local_path = "/home/wolfyd3v/Documents/"
        self.local_path = self.local_path.replace('"', '').replace("'", "")
    
    ''' Create the FTP Host '''
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
    
    # Files Functions
    def download_file(self, file: str) -> None:
        self.ftp_host.download(file, f"{self.local_path}/{file}")
    
    def delete_file(self, file: str) -> None:
        self.ftp_host.remove(file)
    
    def upload_file(self, file_path: str) -> None:
        file = os.path.basename(file_path)
        with open(file_path, "rb") as source:
            with self.ftp_host.open(f"{self.ftp_host.curdir}/{file}", "wb") as target:
                self.ftp_host.copyfileobj(source, target)
    
    def count_files_at(self, directory: str) -> int:
        return len(self.ftp_host.listdir(directory))
    
    # Directories Functions
    def download_dir(self, directory: str) -> None:
        if not os.path.exists(self.local_path + directory): os.mkdir(self.local_path + directory)

        for root, dirs, files in self.ftp_host.walk(directory):
            rel_path = os.path.relpath(root, directory)
            local_root = os.path.join(self.local_path + directory, rel_path)
            os.makedirs(local_root, exist_ok=True)
            for file in files:
                remote_file = self.ftp_host.path.join(root, file)
                local_file = os.path.join(local_root, file)
                self.ftp_host.download(remote_file, local_file)
                time.sleep(0.1)
    
    def delete_dir(self, directory: str) -> None:
        self.ftp_host.rmtree(directory)
    
    def change_dir(self, directory: str) -> None:
        self.ftp_host.chdir(directory)
    
    def get_current_dir(self) -> str:
        return self.ftp_host.getcwd()

    def new_dir(self, directory_name: str) -> bool:
        if not self.ftp_host.path.exists(directory_name):
            self.ftp_host.mkdir(directory_name)
            return True
        return False

    def list_dir(self, directory: str) -> list:
        return self.ftp_host.listdir(directory)
    
    def upload_dir(self, local_directory_path: str) -> None:
        folder_name = os.path.basename(local_directory_path)
        self.new_dir(folder_name)
        self.change_dir(folder_name)

        for file in os.listdir(local_directory_path):
            full_path = os.path.join(local_directory_path, file)
            if os.path.isdir(full_path): self.upload_dir(full_path)
            else:
                self.upload_file(full_path)
                time.sleep(0.1)
        
        self.ftp_host.chdir("..")

''' The FTP Client App '''
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

if __name__ == "__main__":
    ftp_client: FTP_Client = FTP_Client()
    ftp_client.run()