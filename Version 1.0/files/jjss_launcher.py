from tkinter import *
import os, json, requests, threading, functools, subprocess, sys
from bs4 import BeautifulSoup
from zipfile import ZipFile


class MainWindow():
    def __init__(self):
        self.root = Tk()
        self.root.geometry("280x300")
        self.root.resizable(width=0, height=0)
        self.root.protocol("WM_DELETE_WINDOW" ,self.on_destroy)
        self.root.config(bg="#22181C")
        self.sel_game = 0
        self.games = ["Plant-The-Bomb", "Snake", "Casino-Game", "Ufo-Absorbtion", "Guess-The-Color"]
        self.Button1 = Button(self.root, text=self.games[self.sel_game], command=lambda:[self.load_game(self.games[self.sel_game])], font="Calibri 20", relief="flat", bg="#312F2F", fg="#F6E8EA", activebackground="#F6E8EA", activeforeground="#312F2F", bd=0)
        self.Button1.place(x=0, y=0, width=280, height=170)
        self.Button2 = Button(self.root, text="<", font="Calibri 20", command=lambda:[self.last_game()], state="disabled", relief="flat", bg="#22181C", fg="#F6E8EA", activebackground="#22181C", activeforeground="#EF626C",bd=0)
        self.Button2.place(x=80, y=200, width=30, height=25)
        self.Button3 = Button(self.root, text=">", font="Calibri 20", command=lambda:[self.next_game()], relief="flat", bg="#22181C", fg="#F6E8EA", activebackground="#22181C", activeforeground="#EF626C",bd=0)
        self.Button3.place(x=170, y=200, width=30, height=25)
        self.root.mainloop()
    def last_game(self):
        self.sel_game -= 1
        self.Button1.config(text=self.games[self.sel_game], command=lambda:[self.load_game(self.games[self.sel_game])])
        self.Button3.config(state="normal")
        if (self.sel_game + 1) <= 1:
            self.Button2.config(state="disabled")
    def next_game(self):
        self.sel_game += 1
        self.Button1.config(text=self.games[self.sel_game], command=lambda:[self.load_game(self.games[self.sel_game])])
        self.Button2.config(state="normal")
        if (self.sel_game + 1) >= len(self.games):
            self.Button3.config(state="disabled")
    def load_game(self, game):
        GameHandler(game, self.root)
    def on_destroy(self):
        os._exit(0)


class GameHandler():
    def __init__(self, game, tk):
        self.root = tk
        self.root.protocol("WM_DELETE_WINDOW", self.on_destroy)
        self.game = game
        self.base_url = "https://github.com/"
        self.repo_name = "JJSS-Johannes/" + game
        self.base_path= "games"
        self.game_path = self.base_path + "/" + game + "/"
        self.version_file = self.game_path + "versions.json"
        self.href_result = []
        self.download_buttons = []
        if not os.path.isdir(self.base_path): 
            os.mkdir(self.base_path)
        if not os.path.isdir(self.game_path):
            os.mkdir(self.game_path)
        if not os.path.isfile(self.version_file):
            open(self.version_file, "w").write(json.dumps({"versions": []}))
        self.update_ver_window(self.load_ver_list())
        self.root.update()
        x = threading.Thread(target=self.update_ver_list())
        x.start()
    def update_ver_window(self, ver_list):
        self.download_buttons = []
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.geometry("280x"+ str(len(ver_list)*30))
        for i in range(len(ver_list)):
            b = Button(self.root, text=ver_list[i], font="Calibri 15", command=functools.partial(self.start_download, ver_list[i], i), relief="raised", bg="#312F2F", fg="#F6E8EA", activebackground="#F6E8EA", activeforeground="#312F2F", bd=2)
            b.place(x=0,y=i*30, height = 30,width=280)
            self.download_buttons.append(b)
    def load_ver_list(self):
        t = open(self.version_file, "r").read()
        js = json.loads(t)
        return js["versions"]
    def update_ver_list(self):
        try:
            ver_list = self.get_ver_list()
        except Exception as e:
            self.on_destroy()
            return
        open(self.version_file, "w").write(json.dumps({"versions": ver_list}))
        self.update_ver_window(ver_list)                                   
    def get_ver_list(self):
        ver_list = self.get_href(self.base_url + self.repo_name)
        vers_list = []
        for ver in ver_list:
            if (self.repo_name + "/tree/main" in ver) and (ver[:len(self.repo_name)+1] == "/"+self.repo_name):
                ver = ver.split("/")[-1]
                ver = ver.replace("%20", " ")
                vers_list.append(ver)
        return vers_list
    def get_download_link(self, version):
        version = version.replace(" ", "%20")
        link = self.base_url + self.repo_name + "/tree/main/" + version
        r2 = requests.get(link).text
        soup2 = BeautifulSoup(r2, "html.parser")
        for link in soup2.find_all('a'):
            lk = link.get('href')
            if (self.repo_name + "/blob/main" in lk) and (lk[:len(self.repo_name)+1] == "/"+self.repo_name) and lk[-4:] == ".zip":
                path = "https://raw.githubusercontent.com" + lk
                path = path.replace("/blob", "")
                return path
    def start_download(self, ver, index):
        x = threading.Thread(target=self.download_and_start, args=(ver,index,))
        x.start()
    def download_and_start(self, ver,index):
        self.change_button_status("disabled")
        self.change_window_close(self.nothing)
        try:
            link = self.get_download_link(ver)
        except Exception as e:
            self.change_window_close(self.on_destroy)
            return
        response = requests.get(link)
        file_zip = self.game_path + link.split("/")[-1]
        file_dir = file_zip[:-4]
        file_end = self.game_path + ver
        if not os.path.isdir(file_end):
            open(file_zip, "wb").write(response.content)
            ZipFile(file_zip).extractall(file_dir)
            os.remove(file_zip)
            os.rename(file_dir, file_end)
        command = self.get_abs_path(file_end + "/Start.bat")
        command.replace("\\", "/")
        no_window = 0x08000000
        t = subprocess.Popen(command, cwd = file_end, creationflags=no_window, stdout=subprocess.PIPE)
        if t.communicate():
            self.change_button_status("normal")
            self.change_window_close(self.on_destroy)
    def change_button_status(self, status):
        for button in self.download_buttons:
                button.config(state=status)
    def change_window_close(self, status):
        if status=="disabled":
            self.root.protocol("WM_DELETE_WINDOW", status)
        else:
            self.root.protocol("WM_DELETE_WINDOW", status)
    def nothing(self):
        pass
    def get_abs_path(self, relative_path):
        base_path = getattr(sys,'_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)
    def get_href(self, link):
        r = requests.get(link).text
        soup = BeautifulSoup(r, "html.parser")
        hrefs = []
        for link in soup.find_all('a'):
            lk = link.get('href')
            if self.repo_name in lk:
                hrefs.append(lk)
        return hrefs
    def on_destroy(self):
        self.root.destroy()
        MainWindow()

MainWindow()

