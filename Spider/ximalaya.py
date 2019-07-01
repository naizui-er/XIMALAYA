# ！/usr/bin/env python
# -*- coding:utf-8 -*-
import requests
import os
import time
import datetime
import json
import math
import webbrowser
import tkinter as tk
from tkinter import ttk
from tkinter import *
from fake_useragent import UserAgent


class XimalayaSpider:

    def __init__(self):
        self.data_dic = dict()
        self.SUCCESS = "成功"
        self.IOError = "保存出错"
        self.DOWNLOADError = "下载出错"
        self.ua = UserAgent()

    @staticmethod
    def get_13unix_time():
        return str(round(time.time() * 1000))

    @staticmethod
    def get_now_time():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def sec_to_time(seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%02d:%02d:%02d" % (h, m, s)

    @staticmethod
    def del_title(title):
        for i in ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]:
            title = title.replace(i, "").replace(" ", "").strip()
        return title

    def random_user_agent(self):
        return self.ua.random

    def read_cookie(self):
        text_hm_lvt = "Hm_lvt_4a7d8ec50cfd6af753c4f8aee3425070=" + self.get_13unix_time()[0:9] + ";login_from=qq;1&remember_me=y;"
        login_type = ";login_type=QQ;Hm_lpvt_4a7d8ec50cfd6af753c4f8aee3425070 =" + self.get_13unix_time()
        with open("config.txt", "r") as f:
            cookie_list = [i.strip() for i in f]
        text_device_id = ""
        device_id_list = cookie_list[1].split("_")
        device_id_list[2] = self.get_13unix_time()
        for i in device_id_list:
            text_device_id += i + "_"
        text_1_l_flag = cookie_list[2][:cookie_list[2].rfind("_")] + "_" + self.get_now_time()
        cookie = cookie_list[0] + ";" + text_device_id + ";" + text_hm_lvt + cookie_list[2] + ";" + text_1_l_flag + login_type
        return cookie

    def get_total(self, album_id, headers):
        url = "https://www.ximalaya.com/revision/album?albumId=" + album_id
        response = requests.get(url, headers=headers)
        response = json.loads(response.content)
        data = dict()
        data["trackTotalCount"] = response["data"]["tracksInfo"]["trackTotalCount"]
        data["albumTitle"] = self.del_title(response["data"]["mainInfo"]["albumTitle"])
        return data

    def get_list(self, page_nums, album_id, headers, tk):
        for i in range(0, math.ceil(page_nums/30)):
            url_list = "https://www.ximalaya.com/revision/play/album?albumId=" + album_id + "&pageNum=" + str(
                i + 1) + "&sort=-1&pageSize=30"
            tracks_audio_play = dict()
            response = requests.get(url_list, headers=headers)
            response = json.loads(response.content)
            for t in response["data"]["tracksAudioPlay"]:
                tracks_audio_play[str(t["index"])] = {"trackName": t["trackName"], "src": t["src"], "duration": t["duration"]}
                self.data_dic = dict(self.data_dic, **tracks_audio_play)
            tk.update()
            yield tracks_audio_play

    def mk_dir(self, file_name):
        path = os.path.join(os.getcwd(), file_name)
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def save(self, child_name, content, tk):
        try:
            f = open(child_name + ".m4a", "wb")
            f.write(content)
            tk.update()
        except IOError:
            return self.IOError
        finally:
            if f:
                f.close()
            return self.SUCCESS

    def download(self, headers, path, child_name, src, tk):
        response = requests.get(src, headers=headers)
        data = dict()
        if response.status_code == 200:
            status = self.save(path + "\\" + self.del_title(child_name), response.content, tk)
            tk.update()
            data["child_name"] = child_name
            data["status"] = status
            return data
        else:
            data["child_name"] = child_name
            data["status"] = self.DOWNLOADError
            return data


class MainWindow(tk.Tk):

    def __init__(self):
        super().__init__()
        self.spider = XimalayaSpider()
        self.album_id = ""
        self.count_and_title = dict()
        self.headers = {
            "User-Agent": self.spider.random_user_agent(),
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Cookie": self.spider.read_cookie()
        }
        self.selected = 0
        self.total_num = str(self.selected) + "条记录"
        self.frame_top = tk.Frame(width=900, height=70)
        self.frame_center = tk.Frame(width=900, height=600)
        self.frame_bottom = tk.Frame(width=900, height=70)
        self.sound_id_tip = tk.Label(self.frame_top, text="URL：")
        self.show = tk.StringVar()
        self.sound_id = tk.Entry(self.frame_top, textvariable=self.show, width="50")
        self.btn_query = tk.Button(self.frame_top, text="查询", command=self.query)
        self.btn_select_all = tk.Button(self.frame_top, text="全选", command=self.select_all)
        self.btn_select_clear = tk.Button(self.frame_top, text="反选", command=self.select_clear)
        self.btn_download = tk.Button(self.frame_top, text="下载", command=self.download)
        self.btn_stop = tk.Button(self.frame_top, text="暂停", command=self.stop)
        self.selected_label = tk.Label(self.frame_bottom, text="共查到:")
        self.selected_text = tk.Label(self.frame_bottom, text=self.total_num)
        self.status_label = tk.Label(self.frame_bottom, text="执行状态:")
        self.status_text = tk.Label(self.frame_bottom, text="")
        self.link_kong = tk.Label(self.frame_bottom, text="")
        self.link_label = tk.Label(self.frame_bottom, text="购买联系:")
        self.link_text = tk.Label(self.frame_bottom, text="QQ354308282")
        self.btn_QQ = tk.Button(self.frame_bottom, text="联系QQ", command=self.open_url)
        self.sound_id_tip.grid(row=0, column=0, padx=0, pady=20)
        self.sound_id.grid(row=0, column=1, padx=0, pady=20)
        self.btn_query.grid(row=0, column=4, padx=15, pady=20)
        self.btn_select_all.grid(row=0, column=5, padx=15, pady=20)
        self.btn_select_clear.grid(row=0, column=6, padx=15, pady=20)
        self.btn_download.grid(row=0, column=7, padx=15, pady=20)
        self.btn_stop.grid(row=0, column=8, padx=15, pady=20)
        self.selected_label.grid(row=0, column=0, padx=0, pady=0)
        self.selected_text.grid(row=0, column=1, padx=0, pady=0)
        self.status_label.grid(row=0, column=3, padx=10, pady=0)
        self.status_text.grid(row=0, column=4, padx=0, pady=0)
        self.link_label.grid(row=1, column=0, padx=0, pady=0)
        self.link_text.grid(row=1, column=1, padx=0, pady=0)
        self.btn_QQ.grid(row=1, column=4, padx=250, pady=0)
        self.tree = ttk.Treeview(self.frame_center, show="headings", height=28, columns=("a", "b", "c", "d", "e", "f"))
        self.vbar = ttk.Scrollbar(self.frame_center, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.vbar.set)
        self.tree.column("a", width=60, anchor="center")
        self.tree.column("b", width=60, anchor="center")
        self.tree.column("c", width=300, anchor="sw")
        self.tree.column("d", width=100, anchor="center")
        self.tree.column("e", width=100, anchor="center")
        self.tree.column("f", width=100, anchor="center")
        self.tree.heading("a", text="选中")
        self.tree.heading("b", text="序号")
        self.tree.heading("c", text="标题")
        self.tree.heading("d", text="时长")
        self.tree.heading("e", text="付费")
        self.tree.heading("f", text="下载状态")
        self.tree["selectmode"] = "extended"
        self.tree.grid(row=0, column=0, sticky=tk.NSEW, ipadx=10)
        self.vbar.grid(row=0, column=1, sticky=tk.NS)
        self.menu = Menu(self, tearoff=0)
        self.menu.add_command(label="复制", command=self.on_copy)
        self.menu.add_separator()
        self.menu.add_command(label="粘贴", command=self.on_paste)
        self.menu.add_separator()
        self.menu.add_command(label="剪切", command=self.on_cut)
        self.zt = False
        self.tree.bind("<Button-1>", self.click)
        self.bind("WM_DELETE_WINDOW", self.close_tkinter)
        self.sound_id.bind("<Button-3>", self.pop_up_menu)
        self.iconbitmap("icon.ico")
        self.frame_top.grid(row=0, column=0, padx=20)
        self.frame_center.grid(row=3, column=0, padx=20)
        self.frame_bottom.grid(row=4, column=0, padx=0)
        self.frame_top.grid_propagate(0)
        self.frame_center.grid_propagate(0)
        self.frame_bottom.grid_propagate(0)
        self.center_window(800, 740)
        self.title("喜马拉雅下载器 V1.5")
        self.resizable(False, False)
        self.mainloop()

    def open_url(self):
        webbrowser.open("http://www.baidu.com", new=0)

    def pop_up_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def on_paste(self):
        try:
            self.text = self.clipboard_get()
        except Exception:
            pass
        self.show.set(str(self.text))

    def on_copy(self):
        self.text = self.sound_id.get()
        self.clipboard_append(self.text)

    def on_cut(self):
        self.on_copy()
        try:
            self.sound_id.delete('sel.first', 'sel.last')
        except Exception:
            pass

    def stop(self):
        if self.zt:
            self.btn_stop.config(text="暂停")
            self.update()
            self.zt = False
        else:
            self.btn_stop.config(text="继续")
            self.update()
            self.zt = True

    def click(self, event):
        row = self.tree.identify_row(event.y)
        flag = self.tree.item(row, "values")[0]
        if flag != "√":
            self.tree.set(row, "#1", "√")
        else:
            self.tree.set(row, "#1", " ")

    def close_tkinter(self):
            self.destroy()

    def center_window(self, width, height):
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        size = "%dx%d+%d+%d" % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.geometry(size)

    def get_tree(self, result):
        for i in result.keys():
            self.tree.insert("", "end", values=("√", i, result[i]["trackName"], self.spider.sec_to_time(int(result[i]["duration"])), "", ""))
            self.selected += 1
            selected_num = str(self.selected) + "条记录"
            self.selected_text.config(text=selected_num)
            self.update()

    def query(self):
        self.zt = False
        self.selected = 0
        global album_id, count_and_title
        album_id = re.search("[0-9]+", self.sound_id.get()).group()
        if album_id == "":
            self.status_text.config(text="请输入URL", fg="blue")
            self.update()
        else:
            for i in self.tree.get_children():
                self.tree.delete(i)
            count_and_title = self.spider.get_total(album_id, self.headers)
            for item in self.spider.get_list(page_nums=count_and_title["trackTotalCount"], album_id=album_id, headers=self.headers, tk=self):
                self.status_text.config(text="正在查询列表...")
                self.update()
                self.get_tree(result=item)
                while self.zt:
                    self.status_text.config(text="查询已暂停")
                    self.update()
                    time.sleep(1)
                else:
                    self.update()
        self.status_text.config(text="查询完成")

    def select_all(self):
        for i in self.tree.get_children():
            self.tree.set(i, "#1", "√")

    def select_clear(self):
        for i in self.tree.get_children():
            self.select(i)

    def select(self, row):
        flag = self.tree.item(row, "values")[0]
        if flag != "√":
            self.tree.set(row, "#1", "√")
        else:
            self.tree.set(row, "#1", "")

    def download(self):
        self.zt = False
        self.btn_stop.config(text="暂停")
        self.update()
        if album_id == "":
            self.status_text.config(text="请输入URL", fg="blue")
            self.update()
        else:
            self.status_text.config(text="正在下载...")
            self.update()
            path = self.spider.mk_dir(count_and_title["albumTitle"])
            data_dic = self.spider.data_dic
            for row in self.tree.get_children():
                if self.tree.item(row, "values")[0] == "√" and self.tree.item(row, "values")[5] == "":
                    child_name = data_dic[self.tree.item(row, "values")[1]]["trackName"]
                    src = data_dic[self.tree.item(row, "values")[1]]["src"]
                    if str(src) == "None":
                        self.tree.set(row, "#5", "是")
                        self.tree.set(row, "#6", "下载失败")
                        self.update()
                    else:
                        data = self.spider.download(headers=self.headers, path=path, child_name=child_name, src=src, tk=self)
                        text = "正在下载 " + data["child_name"]
                        self.status_text.config(text=text)
                        self.update()
                        self.tree.set(row, "#5", "否")
                        self.tree.set(row, "#6", data["status"])
                        self.update()
                    while self.zt:
                        self.status_text.config(text="下载已暂停")
                        self.update()
                        time.sleep(1)
                    else:
                        self.update()
            else:
                self.update()
            self.status_text.config(text="下载完成")


if __name__ == "__main__":
    mains = MainWindow()
