import requests, os, json, time, webbrowser, re
import tkinter as tk
from tkinter import Menu
import threading
from fake_useragent import UserAgent

session = requests.Session()
track_list = list()
file = ""  # 默认存储路径为当前目录
ua = UserAgent().random
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'User-Agent': ua,
    'Accept-Encoding': 'gzip, deflate, br',
    'Host': 'www.ximalaya.com',
    'Upgrade-Insecure-Requests': '1',
    'Connection': 'Keep-Alive'
}
headers2 = {
    'User-Agent': ua,
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'Keep-Alive'
}


def loginCookie(url):
    global session
    session.get(url, headers=headers)
    return session.cookies.get_dict()


def deal_title(title):
    for i in ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]:
        title = title.replace(i, "").replace(" ", "").strip()
    return title


def mk_dir(book_name):
    """在本地创建文件存储目录"""
    path = os.path.join(os.getcwd(), book_name)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


# GUI开始
# 第1步，实例化object，建立窗口window
window = tk.Tk()

# 第2步，给窗口的可视化起名字
window.title('喜马拉雅下载器 V 2.0')

# 第3步，设置窗口的居中显示
screenwidth = window.winfo_screenwidth()
screenheight = window.winfo_screenheight()
width = 700
height = 200
size = "%dx%d+%d+%d" % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
# 第4步，设定窗口的大小(长 * 宽)
window.geometry(size)

# 第5步，用户信息
tk.Label(window, text='下载地址:', font=('Arial', 14)).place(x=20, y=30)

# 第6步，下载地址输入框entry
var_url_input = tk.Entry(window, font=('Arial', 14), width='40')
var_url_input.place(x=120, y=30)
percent_text = ""
# 设置下载进度条
canvas = tk.Canvas(window, width=620, height=16, bg="white")
canvas.place(x=20, y=100)
percent_label = tk.Label(window, text="")
percent_label.place(x=650, y=100)
label = tk.Label(window, text="")
label.place(x=20, y=140)
link = tk.Label(window, text='点击购买高级版本:  www.baidu.com', font=('Arial', 10))
link.place(x=20, y=180)


# 右键菜单
def pop_up_menu(event):
    menu.post(event.x_root, event.y_root)


# 粘贴
def on_paste():
    try:
        text = window.clipboard_get()  # 从粘贴板取出数据
        var_url_input.insert(0, str(text))
    except Exception:
        pass


# 复制
def on_copy():
    text = var_url_input.get()
    window.clipboard_clear()
    window.clipboard_append(text)


# 剪切
def on_cut():
    on_copy()
    try:
        var_url_input.delete('sel.first', 'sel.last')
    except Exception:
        pass


# 添加菜单控件
menu = Menu(window, tearoff=0)
menu.add_command(label="复制", command=on_copy)
# menu.add_separator()
menu.add_command(label="粘贴", command=on_paste)
# menu.add_separator()
menu.add_command(label="剪切", command=on_cut)
# 绑定右键单击事件到输入框
var_url_input.bind("<Button-3>", pop_up_menu)


def open_url(event):
    webbrowser.open("http://www.baidu.com", new=0)


link.bind("<Button-1>", open_url)


# 回调函数：下载节目数据到本地
def get_track_list(albumId, page_num):
    try:
        url = "https://www.ximalaya.com/revision/play/album?albumId={}&pageNum={}&sort=-1&pageSize=30".format(albumId, page_num)
        print("albumId\t")
        print(albumId)
        print("get_track_list--url\t")
        print(url)
        print("file========"+file)
        response = session.get(url, headers=headers, verify=False)
        response = json.loads(response.content)
        track_list = response["data"]["tracksAudioPlay"]  # 获取节目信息
        for track in track_list:
            title = deal_title(track["trackName"])  # 取出节目名并处理其中的特殊字符

            label["text"] = "正在下载\t {}...".format(title)

            src = track["src"]  # 音频链接
            m4a = session.get(src, headers=headers2, verify=False,
                              stream=True)  # stream=True表示请求成功后并不会立即开始下载，而是在调用iter_content方法之后才会开始下载
            chunk_size = 40960  # 每次块大小为1024
            content_size = int(m4a.headers['content-length'])  # 返回的response的headers中获取文件大小信息
            # 填充进度条
            fill_line = canvas.create_rectangle(1.5, 1.5, 0, 23, width=0, fill="green")
            raise_data = 620 / (content_size / chunk_size)
            with open(file + "\\" + title + '.m4a', 'wb') as f:
                n = 0  # 填充量
                tmp = 0
                for data in m4a.iter_content(chunk_size=chunk_size):
                    f.write(data)
                    n = n + raise_data
                    canvas.coords(fill_line, (0, 0, n, 60))
                    tmp += chunk_size
                    percent_text = "{:.0%}".format(tmp / content_size)
                    # canvas.itemconfig(itext, text=percent_text)
                    percent_label["text"] = percent_text
                    window.update()
                f.flush()
                f.close()
            clean_progressbar()  # 每集节目下载完后清空进度条
        # 判断是否还有下一页
        if response["data"]["hasMore"]:
            page_num += 1
            get_track_list(albumId, page_num)
        else:
            percent_label["text"] = ""
            clean_progressbar()
            label["text"] = "下载完毕"
    except Exception:
        label["text"] = "请求异常"


def download(url):
    """正则匹配媒体文件地址"""
    albumId = re.search("[0-9]{6,10}", url).group(0)
    url = "https://www.ximalaya.com/revision/play/album?albumId={}&pageNum={}&sort=-1&pageSize=30".format(albumId, 1)
    print("albumId\t")
    print(albumId)
    print("download--url\t")
    print(url)
    label["text"] = "正在请求数据..."
    try:
        cookies_xxx = loginCookie('https://www.ximalaya.com/')
        print("cookies_xxx\n")
        print(cookies_xxx)
        response = session.get(url, headers=headers, cookies=cookies_xxx, verify=False)
        response = json.loads(response.content)
        track_list = response["data"]["tracksAudioPlay"]        # 获取节目信息
        book_name = track_list[0]["albumName"]      # 获取专辑名
        global file
        file = mk_dir(deal_title(book_name))
        for track in track_list:
            title = deal_title(track["trackName"])      # 取出节目名并处理其中的特殊字符
            print("title=="+title)
            label["text"] = "正在下载\t {}...".format(title)

            src = track["src"]      # 音频链接
            m4a = session.get(src, headers=headers2, cookies=cookies_xxx, verify=False,
                              stream=True)  # stream=True表示请求成功后并不会立即开始下载，而是在调用iter_content方法之后才会开始下载
            chunk_size = 40960  # 每次块大小为1024
            content_size = int(m4a.headers['content-length'])  # 返回的response的headers中获取文件大小信息
            # 填充进度条
            fill_line = canvas.create_rectangle(1.5, 1.5, 0, 23, width=0, fill="green")
            raise_data = 620 / (content_size / chunk_size)
            with open(file + "\\" + title + '.m4a', 'wb') as f:
                n = 0       # 填充量
                tmp = 0
                for data in m4a.iter_content(chunk_size=chunk_size):
                    f.write(data)
                    n = n + raise_data
                    canvas.coords(fill_line, (0, 0, n, 60))
                    tmp += chunk_size
                    percent_text = "{:.0%}".format(tmp/content_size)
                    window.update()
                    percent_label["text"] = percent_text
                f.flush()
                f.close()
            clean_progressbar()     # 每集节目下载完后清空进度条
        # 判断是否还有下一页,如果有，则进入回调函数,否则提示完成
        print(response["data"]["hasMore"])
        print(response["data"]["hasMore"] == "true")
        if response["data"]["hasMore"]:
            get_track_list(albumId, 38)
        else:
            percent_label["text"] = ""
            clean_progressbar()
            label["text"] = "下载完毕"

    except Exception:
        label["text"] = "请求异常"


# 清空进度条
def clean_progressbar():
    # 清空进度条
    fill_line = canvas.create_rectangle(1.5, 1.5, 0, 23, width=0, fill="white")
    x = 500  # 未知变量，可更改
    n = 620 / x  # 465是矩形填充满的次数

    for t in range(x):
        n = n + 620 / x
        # 以矩形的长度作为变量值更新
        canvas.coords(fill_line, (0, 0, n, 60))
        window.update()
        time.sleep(0)  # 时间为0，即飞速清空进度条


# 第8步，定义用户下载功能
def usr_download():
    # 进度条如果是100%，则执行清空
    if label["text"] == "下载完成":
        clean_progressbar()
    url = var_url_input.get()
    print(url)
    t = threading.Thread(target=download, args=[url])
    t.setDaemon(True)
    t.start()


# 第7步，下载按钮
btn_download = tk.Button(window, text='开始下载', command=usr_download)
btn_download.place(x=600, y=28)

# 第10步，主窗口循环显示
window.mainloop()

