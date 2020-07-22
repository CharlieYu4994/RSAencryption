import supports
import re, os, base64, binascii, pyperclip
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
import tkinter, sqlite3
from tkinter.simpledialog import askstring
from tkinter import scrolledtext, filedialog, ttk

msg_prefix = '-----BEGIN MESSAGE-----\n'
msg_suffix = '\n-----END MESSAGE-----'


class InputWindow(tkinter.Toplevel):
    '''
    密码输入窗口
    '''

    password = None

    def __init__(self):
        super().__init__()
        displayh = self.winfo_screenheight() // 2
        dispalyw = self.winfo_screenwidth() // 2
        self.protocol('WM_DELETE_WINDOW', lambda: self.destroy())
        self.title('Password')
        self.geometry(f'300x100+{dispalyw-150}+{displayh-100}')
        self.resizable(0, 0)
        self.setupUI()

    def setupUI(self):
        password_box = ttk.Frame(self)
        password_l = ttk.Label(password_box, text='密码  :')
        password_l.grid(column=0, row=0)
        self.password_e = ttk.Entry(password_box, width=32)
        self.password_e.grid(column=1, row=0)
        self.password_e['show'] = '*'
        self.password_e.bind('<Return>', self.submit)
        self.password_e.focus_set()
        password_box.grid(column=0, row=0, padx=15, pady=15)

        btn_box = ttk.Frame(self)
        o_btn = ttk.Button(btn_box, text='确定', width=16, command=lambda: self.submit(None))
        o_btn.grid(column=0, row=0, padx=12)
        c_btn = ttk.Button(btn_box, text='取消', width=16, command=lambda: self.destroy())
        c_btn.grid(column=1, row=0, padx=12)
        btn_box.grid(column=0, row=1, pady=10)

    def submit(self, event):
        self.password = self.password_e.get()
        self.destroy()


class ResultWindow(tkinter.Toplevel):
    '''
    结果显示窗口
    '''

    result = ''

    def __init__(self, _result: str, _type: int, _sig_status=True):
        super().__init__()
        self.displayh = self.winfo_screenheight() // 2
        self.dispalyw = self.winfo_screenwidth() // 2
        self.result = _result
        self.sig_status = _sig_status
        self.title('Result')
        self.resizable(0, 0)

        if   _type == 0: self.setupUI_E()
        elif _type == 1: self.setupUI_D()
        elif _type == 2: self.setupUI_F()

    def setupUI_E(self):
        self.geometry(f'338x180+{self.dispalyw-150}+{self.displayh-200}')
        self.setup_result_box()

        copy_btn = ttk.Button(self, text='复制', width=10, command=lambda: pyperclip.copy(self.result))
        copy_btn.grid(column=0, row=1, pady=10)

        ok_btn = ttk.Button(self, text='确定', width=10, command=lambda: self.destroy())
        ok_btn.grid(column=1, row=1, pady=10)

    def setupUI_D(self):
        self.geometry(f'338x180+{self.dispalyw-150}+{self.displayh-200}')
        self.setup_result_box()

        sign_l = ttk.Label(self, text='√ 签名有效' if self.sig_status else '× 签名无效',
                           foreground='green' if self.sig_status else 'red',
                           font=('', '12'))
        sign_l.grid(column=0, row=1)

        ok_btn = ttk.Button(self, text='确定', width=15, command=lambda: self.destroy())
        ok_btn.grid(column=1, row=1, pady=10)

    def setupUI_F(self):
        self.geometry(f'334x100+{self.dispalyw-167}+{self.displayh-150}')
        textbox = tkinter.Text(self, width=47, height=4)
        textbox.grid(column=0, row=0, columnspan=3)
        textbox.insert('0.0', self.result)

        path = self.result.replace('/', '\\')
        open_btn = ttk.Button(self, text='打开', width=20 if self.sig_status == None else 10,
                              command=lambda: os.system(f"explorer {path}"))
        ok_btn = ttk.Button(self, text='确定', width=20 if self.sig_status == None else 10,
                            command=lambda: self.destroy())

        if self.sig_status != None:
            sign_l = ttk.Label(self, text='√ 签名有效' if self.sig_status else '× 签名无效',
                            foreground='green' if self.sig_status else 'red',
                            font=('', '12'))
            sign_l.grid(column=0, row=1, pady=10)
            open_btn.grid(column=1, row=1, pady=10)
            ok_btn.grid(column=2, row=1, pady=10)
        else:
            open_btn.grid(column=0, row=1, pady=10, padx=9)
            ok_btn.grid(column=1, row=1, pady=10, padx=9)

    def setup_result_box(self):
        textbox = scrolledtext.ScrolledText(self, width=45, height=10)
        textbox.grid(column=0, row=0, columnspan=2)
        textbox.insert('0.0', self.result)


class KeyManage(tkinter.Toplevel):
    '''
    密钥管理窗口
    '''

    database = sqlite3.connect('keyring.db')

    def __init__(self):
        super().__init__()
        self.title('KeyManager')
        self.geometry('200x200')
        self.resizable(0, 0)
        self.setupUI()

    def setupUI(self):
        pass


class MainWindows(tkinter.Tk):
    '''
    主入口
    '''

    database = sqlite3.connect('keyring.db')
    thirdkeydict = dict()
    userkeydict = dict()
    thirdkeylist = list()
    userkeylist = list()
    cfg = prikey = pubkey = thirdkey = None

    def __init__(self):
        super().__init__()
        self.title('RSA&AES Encryption')
        self.geometry('345x205+200+100')
        self.resizable(0, 0)
        self.getkeylist()
        self.setupUI()
        self.wm_attributes('-topmost', 1)

        self.cfg = supports.get_cfg(self.database)
        self.url_e_cfg.insert('0', self.cfg[0])
        self.dir_e_save.insert('0', self.cfg[1])
        self.dir_e_o.insert('0', self.cfg[1])
        if self.thirdkeylist:
            self.select_thirdkey(self.thirdkeylist[0])
            self.thirdkey_ls.current(0)
        if self.userkeylist:
            self.select_userkey(self.cfg[2] if self.cfg[2] else self.userkeylist[0])
            self.userkey_ls.current(0)

    def setupUI(self):
        tabs = ttk.Notebook(self)

#--------------------------------------------第一页------------------------------------------------#
        frame0 = ttk.Frame(tabs)

        self.inputbox = scrolledtext.ScrolledText(frame0, width=46, height=10)
        self.inputbox.grid(column=0, row=0)

        footbox_page1 = ttk.Frame(frame0)
        self.sign_check = tkinter.BooleanVar()
        signcheck = ttk.Checkbutton(footbox_page1, text='签名', variable=self.sign_check)
        signcheck.grid(column=0, row=0, padx=20)
        encrypt_b_text = ttk.Button(footbox_page1, width=8, text='加密', command=self.encrypt_text)
        encrypt_b_text.grid(column=1, row=0)
        decrypt_b_text = ttk.Button(footbox_page1, width=8, text='解密', command=self.decrypt_text)
        decrypt_b_text.grid(column=2, row=0)
        footbox_page1.grid(column=0, row=1, pady=10)

        tabs.add(frame0, text='文本加/解密')
#--------------------------------------------第二页------------------------------------------------#
        frame1 = ttk.Frame(tabs)

        dirbox = ttk.Frame(frame1)
        dir_l_i = ttk.Label(dirbox, text='文件路径:')
        dir_l_i.grid(column=0, row=0, pady=10)
        self.dir_e_i = ttk.Entry(dirbox, width=25)
        self.dir_e_i.grid(column=1, row=0, pady=10)
        dir_b_i = ttk.Button(dirbox, text='选择文件', width=8,
                             command=lambda: (self.dir_e_i.delete('0', 'end'),
                             self.dir_e_i.insert('0', filedialog.askopenfilename(title='请选择文件'))))
        dir_b_i.grid(column=2, row=0, pady=10)
        dir_l_o = ttk.Label(dirbox, text='保存路径:')
        dir_l_o.grid(column=0, row=1, pady=10)
        self.dir_e_o = ttk.Entry(dirbox, width=25)
        self.dir_e_o.grid(column=1, row=1, pady=10)
        dir_b_o = ttk.Button(dirbox, text='选择目录', width=8,
                             command=lambda: (self.dir_e_o.delete('0', 'end'),
                             self.dir_e_o.insert('0', filedialog.askdirectory(title='请选择文件夹'))))
        dir_b_o.grid(column=2, row=1, pady=10)
        dirbox.grid(column=0, row=0, padx=20, pady=15)

        footbox_page2 = ttk.Frame(frame1)
        encrypt_b_file = ttk.Button(footbox_page2, width=20, text='加密', command=self.encrypt_file)
        encrypt_b_file.grid(column=0, columnspan=10, row=1, padx=5)
        decrypt_b_file = ttk.Button(footbox_page2, width=20, text='解密', command=self.decrypt_file)
        decrypt_b_file.grid(column=10, columnspan=10, row=1, padx=5)
        footbox_page2.grid(column=0, row=1, pady=10)

        tabs.add(frame1, text='文件加/解密')
#--------------------------------------------第三页------------------------------------------------#
        frame2 = ttk.Frame(tabs)

        footbox_page3 = ttk.Frame(frame2)
        url_l_cfg = ttk.Label(footbox_page3, text='服务器 URL:')
        url_l_cfg.grid(column=0, row=0, pady=5)
        self.url_e_cfg = ttk.Entry(footbox_page3, width=32)
        self.url_e_cfg.grid(column=1, row=0, pady=5)
        dir_l_save = ttk.Label(footbox_page3, text='保存路径    :')
        dir_l_save.grid(column=0, row=1, pady=5)
        self.dir_e_save = ttk.Entry(footbox_page3, width=32)
        self.dir_e_save.grid(column=1, row=1, pady=5)
        userkey_ls_l = ttk.Label(footbox_page3, text='选择密钥    :')
        userkey_ls_l.grid(column=0, row=2, pady=5)
        userkey_ls_l.bind('<Button-1>', lambda event: self.freshkeylist)
        self.userkey_ls = ttk.Combobox(footbox_page3, width=30)
        self.userkey_ls['values'] = self.userkeylist
        self.userkey_ls.bind('<<ComboboxSelected>>',
                             lambda event: self.select_userkey(self.userkey_ls.get()))
        self.userkey_ls.grid(column=1, row=2, pady=5)
        footbox_page3.grid(column=0, row=0, columnspan=10, padx=16, pady=15)

        save_btn = ttk.Button(frame2, width=8, text='保存', command=self.save_cfg)
        save_btn.grid(column=9, row=1)

        btn_box = ttk.Frame(frame2)
        pubkey_btn = ttk.Button(btn_box, width=8, text='导入公钥')
        pubkey_btn.grid(column=0, row=0, padx=8)
        prikey_btn = ttk.Button(btn_box, width=8, text='管理密钥', command=self.keymanage)
        prikey_btn.grid(column=1, row=0, padx=8)
        btn_box.grid(column=0, columnspan=9, row=1, pady=10)

        tabs.add(frame2, text='杂项')
#--------------------------------------------标签栏------------------------------------------------#
        keybox = ttk.Frame(self)
        thirdkey_l = ttk.Label(keybox, text='收/发件人:')
        thirdkey_l.grid(column=0, row=0, sticky='w')
        thirdkey_l.bind('<Button-1>', lambda event: self.freshkeylist)
        self.thirdkey_ls = ttk.Combobox(keybox, width=11)
        self.thirdkey_ls['values'] = self.thirdkeylist
        self.thirdkey_ls.grid(column=1, row=0)
        self.thirdkey_ls.bind('<<ComboboxSelected>>',
                              lambda event: self.select_thirdkey(self.thirdkey_ls.get()))
        keybox.grid(column=0, row=0, sticky='ne', padx=3, pady=1)

        tabs.grid(column=0, row=0)

    def getkeylist(self):
        self.userkeydict = supports.get_keydict('UserKeys', self.database)
        self.thirdkeydict = supports.get_keydict('ThirdKeys', self.database)
        self.userkeylist = list(self.userkeydict.keys())
        self.thirdkeylist = list(self.thirdkeydict.keys())

    def freshkeylist(self):
        self.getkeylist()
        self.pubkeyls['values'] = self.thirdkeylist
        self.prikeyls['values'] = self.userkeylist

    def select_userkey(self, describe: str):
        u_id = self.userkeydict[describe]
        prikey_t, pubkey_t = supports.get_userkey(u_id, self.database)

        for _ in range(5):
            inputwindow = InputWindow()
            self.wait_window(inputwindow)
            status, prikey, pubkey = supports.load_key(
                pubkey_t, prikey_t, inputwindow.password)
            if not status: tkinter.messagebox.showwarning('Warning', '密码错误'); continue
            self.prikey, self.pubkey = prikey, pubkey; break

        if not status:
            tkinter.messagebox.showwarning('Warning', '密码五次输入错误，请重新选择')
            self.userkey_ls.delete(first='0', last='end')

    def select_thirdkey(self, describe):
        u_id = self.thirdkeydict[describe]
        self.thirdkey = supports.load_key(supports.get_thirdkey(u_id, self.database))
    
    def save_cfg(self):
        _url = self.url_e_cfg.get()
        _outputdir = self.dir_e_save.get()
        if _outputdir.endswith('/'): _outputdir = _outputdir[:-1]
        _defaultkey = self.userkey_ls.get()

        supports.alt_cfg(_url, _outputdir, _defaultkey, self.database)

        self.dir_e_o.delete('0', 'end')
        self.dir_e_o.insert('0', _outputdir)

    def keymanage(self):
        pass

    def encrypt_text(self):
        message = self.inputbox.get(index1='0.0', index2='end')[:-1].encode()
        enc_aes_key, enc_message = supports.composite_encrypt(
            self.thirdkey, message)
        sig = supports.pss_sign(
            self.prikey, message) if self.sign_check.get() else b'No sig'

        b64ed_aes_key = base64.b64encode(enc_aes_key).decode()
        b64ed_message = base64.b64encode(enc_message).decode()
        b64ed_sig = base64.b64encode(sig).decode()

        final_message = f'{msg_prefix}{b64ed_aes_key}.{b64ed_message}.{b64ed_sig}{msg_suffix}'
        resultwindow = ResultWindow(final_message, 0)

    def decrypt_text(self):
        message_t = self.inputbox.get(index1='0.0', index2='end')[
            :-1].replace('\n', '')
        message_t = re.search(
            r'(?<=-----BEGIN MESSAGE-----).*?(?=-----END MESSAGE-----)', message_t)
        if not message_t:
            tkinter.messagebox.showerror('Error', '密文解析失败')
            return

        b64ed_aes_key, b64ed_message, b64ed_sig = message_t.group().split('.')
        try:
            enc_aes_key = base64.b64decode(b64ed_aes_key.encode())
            enc_message = base64.b64decode(b64ed_message.encode())
            sig = base64.b64decode(b64ed_sig.encode())
        except binascii.Error:
            tkinter.messagebox.showerror('Error', '密文已损坏')
            return

        message = supports.composite_decrypt(
            self.prikey, enc_message, enc_aes_key)
        status = supports.pss_verify(
            self.thirdkey, message, sig) if sig != b'No sig' else False
        resultwindow = ResultWindow(message.decode(), 1, status)

    def encrypt_file(self):
        aes_key = get_random_bytes(16)
        path_i = self.dir_e_i.get()
        if self.dir_e_o.get():
            path_o = self.dir_e_o.get() 
        else :
            os.path.dirname(path_i)
            self.dir_e_o.insert('0', path_o)

        sig_hasher = SHA256.new()
        file_hasher = SHA256.new()

        file_info = aes_key + b'^&%&^' + os.path.basename(path_i).encode()
        enc_file_info = supports.rsa_encrypt(self.thirdkey, file_info)

        with open(f'{path_o}/result.ref', 'wb') as file_out:
            file_out.seek(500)
            for block, status in supports.read_file(path_i, 0):
                sig_hasher.update(block)
                file_out.write(supports.aes_encrypt(aes_key, block, status))
            sig = supports.pss_sign(self.prikey, None, sig_hasher)
            final_file_info = base64.b64encode(enc_file_info) + b'.' + base64.b64encode(sig)

            file_out.seek(35, 0)
            file_out.write(str(len(final_file_info)).encode())
            file_out.write(final_file_info)
            file_out.seek(0, 0)

            for block, _ in supports.read_file(f'{path_o}/result.ref', 35):
                file_hasher.update(block)
                print(block)

            file_out.write(b'REF')
            file_out.write(file_hasher.digest())

        resultwindow = ResultWindow(path_o, 2, _sig_status=None)

    def decrypt_file(self):
        path_i = self.dir_e_i.get()
        path_o = self.dir_e_o.get()
        sig_hasher = SHA256.new()
        file_hasher = SHA256.new()

        with open(path_i, 'rb') as file_in:
            if file_in.read(3) != b'REF':
                tkinter.messagebox.showerror('Error', '文件解析失败'); return

            for block, _ in supports.read_file(path_i, 35):
                file_hasher.update(block)

            if file_in.read(32) != file_hasher.digest():
                tkinter.messagebox.showerror('Error', '文件损坏'); return

            enc_file_info, sig = file_in.read(int(file_in.read(3))).split(b'.')

        enc_file_info = base64.b64decode(enc_file_info)
        sig = base64.b64decode(sig)

        try: file_info = supports.rsa_decrypt(self.prikey, enc_file_info)
        except Exception as E:
            tkinter.messagebox.showerror('Error', '文件信息解密失败'); return

        aes_key, filename = file_info.split(b'^&%&^')

        with open(f'{path_o}/{filename.decode()}', 'wb') as file_out:
            for enc_block, status in supports.read_file(path_i, 500):
                block = supports.aes_decrypt(aes_key, enc_block, status)
                sig_hasher.update(block)
                file_out.write(block)

        sig_status = supports.pss_verify(self.pubkey, None, sig, sig_hasher)
        resultwindow = ResultWindow(path_o, 2, sig_status)


if __name__ == '__main__':
    if not os.path.exists('keyring.db'):
        supports.gen_database()
        supports.gen_cfg(sqlite3.connect('keyring.db'))
    app = MainWindows()
    app.mainloop()
