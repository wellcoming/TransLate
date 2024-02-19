import json
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, filedialog
from typing import List

import yaml

from auto_translate import batch_translate
from data_source import scan, format_path
from model import Translate


class TranslationUI:
    def __init__(self, master: tk.Tk):
        self.master = master
        master.title("翻译工具")

        # 译文编辑框
        self.translation_entry = tk.Entry(master, width=50)
        self.translation_entry.pack(side=tk.TOP, fill=tk.X, pady=10)
        self.translation_entry.bind('<Return>', self.update_trans)  # 绑定Enter键

        self.trans: List[Translate] = []
        # 创建Treeview组件
        self.tree = ttk.Treeview(master, columns=('原文', '译文', '路径'), show='headings')
        self.tree.heading('原文', text='原文')
        self.tree.heading('译文', text='译文')
        self.tree.heading('路径', text='路径')
        self.tree.column('原文', width=200, anchor='w')
        self.tree.column('译文', width=200, anchor='w')
        self.tree.column('路径', width=200, anchor='w')
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_item_select)  # 绑定选中事件

        # 创建滚动条
        self.scrollbar = ttk.Scrollbar(master, orient="vertical", command=self.tree.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill="y")
        self.tree.config(yscrollcommand=self.scrollbar.set)

        # 创建进度条
        self.progress = ttk.Progressbar(master, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(side=tk.TOP, fill=tk.X, pady=10)

        # 创建按钮
        self.frame = tk.Frame(master)
        self.frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.open_button = tk.Button(self.frame, text="打开", command=self.open_mapping)
        self.open_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.save_button = tk.Button(self.frame, text="保存", command=self.save_mapping)
        self.save_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.scan_button = tk.Button(self.frame, text="扫描", command=self.scan_files)
        self.scan_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.trans_button = tk.Button(self.frame, text="翻译", command=self.auto_translate)
        self.trans_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.apply_button = tk.Button(self.frame, text="应用", command=self.apply_translation)
        self.apply_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

    @staticmethod
    def show_info(message: str):
        # 在主线程中显示信息窗口
        messagebox.showinfo("信息", message)

    @staticmethod
    def show_warning(exception: Exception):
        # 在主线程中显示警告窗口
        messagebox.showwarning("警告", str(exception))

    @staticmethod
    def show_error(exception: Exception):
        # 在主线程中显示错误窗口
        messagebox.showerror("错误", str(exception))

    def update_progress(self, progress):
        # 在主线程中更新进度条
        self.progress['value'] = progress * 100

    def refresh_list(self):
        # 先清空现有列表
        self.tree.delete(*self.tree.get_children())
        # 遍历扫描结果并添加到列表中
        for i in range(len(self.trans)):
            self.tree.insert('', 'end', iid=str(i))
            self.update_list(i)

    def update_list(self, iid: int):
        # if iid is None:
        #     # 添加一项到列表
        #     return self.tree.insert('', 'end', values=item)
        # 更新列表中的一项
        item = self.trans[iid]
        self.tree.item(str(iid), values=(item.ori, item.trans, format_path(item.path)))

    def open_mapping(self):
        """打开并加载一个YAML文件，该文件包含原文到译文的映射"""
        file_path = filedialog.askopenfilename(title="打开映射文件",
                                               filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])
        if not file_path:  # 如果用户取消了操作
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                if not isinstance(data, list):
                    raise ValueError("文件格式错误")
                self.trans = []
                self.refresh_list()
                for i, item in enumerate(data):
                    self.tree.insert('', 'end', iid=str(i))
                    self.trans.append(Translate(**item))
                    self.update_list(i)
                    self.update_progress((i + 1) / len(data))

        except Exception as e:
            self.show_error(e)
        finally:
            self.update_progress(0)

    def save_mapping(self):
        """保存当前的原文到译文映射到一个YAML文件"""
        file_path = filedialog.asksaveasfilename(title="保存映射文件", defaultextension=".yaml",
                                                 filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])
        if not file_path:  # 如果用户取消了操作
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                data = [t.model_dump() for t in self.trans]
                yaml.safe_dump(data, file, allow_unicode=True)
                self.show_info("保存成功")
        except Exception as e:
            self.show_error(e)
            return

    def scan_files(self):
        # 这里添加扫描文件的逻辑
        def thread_target():
            folder_path = filedialog.askdirectory(title="选择文件夹")
            if not folder_path:  # 用户取消选择
                return

            try:
                scan_path = Path(folder_path).resolve()  # 使用用户选择的路径
                result = scan(scan_path, self.update_progress, self.show_warning)
                self.trans = []
                self.refresh_list()
                for path, text in result:
                    iid = len(self.trans)
                    self.tree.insert('', 'end', iid=str(iid))
                    self.trans.append(Translate(ori=text,
                                                trans='',
                                                path=path,
                                                ))
                    self.update_list(iid)

            except Exception as e:
                self.show_warning(e)
            finally:
                self.update_progress(0)

        # 确保文件夹选择对话框在主线程中打开
        self.master.after(0, lambda: threading.Thread(target=thread_target).start())

    def auto_translate(self):
        selected_items = self.tree.selection()
        if not selected_items:
            ori = [t.ori for t in self.trans]
        else:
            # 提取选中项的原文
            ori = [self.trans[int(i)].ori for i in selected_items]

        def translate_thread():
            def update_ui(result: List[str], cur: int):
                for i, text in enumerate(result):
                    i += cur
                    self.trans[i].trans = text
                    self.update_list(i)
                self.update_progress((cur + len(result)) / len(ori))

            batch_translate(ori, update_ui)

        self.master.after(0, lambda: threading.Thread(target=translate_thread).start())

    def apply_translation(self):
        outpath = Path(filedialog.askdirectory(title="选择输出文件夹")).resolve()
        for trans in self.trans:
            path: Path = trans.path.path
            out=outpath / path.name
            path = out if out.is_file() else path
            data = json.loads(path.read_text(encoding="utf-8"))
            cur = data
            for tag in trans.path.dpath[:-1]:
                cur = cur[tag]
            cur[trans.path.dpath[-1]] = trans.trans
            out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print("写入" + format_path(trans.path))

    def on_item_select(self, _event: tk.Event):
        selected_items = self.tree.selection()
        if selected_items:  # 检查是否有选中的项
            iid = int(selected_items[0])
            item = self.trans[iid]
            self.translation_entry.delete(0, tk.END)
            self.translation_entry.insert(0, item.trans)

    def update_trans(self, _event: tk.Event) -> None:
        """按Enter键更新译文"""
        selected_items = self.tree.selection()
        if selected_items:
            iid = int(selected_items[0])
            text = self.translation_entry.get()
            item = self.trans[iid]
            item.trans = text
            self.update_list(iid)
        else:
            self.show_info("请先选择一项")
