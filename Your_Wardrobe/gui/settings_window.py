import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from config.about import VERSION, PROJECT_NAME, PROJECT_URL, AUTHOR, DESCRIPTION
from config.config import WINDOW_WIDTH, WINDOW_HEIGHT
from core.db_operations import get_all_wardrobes, create_wardrobe, delete_wardrobe

class SettingsWindow:
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.window = None
        self.current_page = None
    
    def show(self):
        if self.window:
            self.window.deiconify()
            return
        
        self._create_window()
    
    def _create_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("设置")
        self.window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.window.resizable(True, True)
        
        # 居中显示
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - WINDOW_WIDTH) // 2
        y = (screen_height - WINDOW_HEIGHT) // 2
        self.window.geometry(f"+{x}+{y}")
        
        # 主框架
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧导航栏
        nav_frame = tk.Frame(main_frame, width=150, bg="#f0f0f0")
        nav_frame.pack(side=tk.LEFT, fill=tk.Y)
        nav_frame.pack_propagate(False)
        
        # 右侧内容区
        self.content_frame = tk.Frame(main_frame, bg="white")
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 导航按钮
        nav_items = [
            ("关于", self._show_about),
            ("衣柜管理", self._show_wardrobe_manage),
            ("URL 路由", self._show_placeholder),
            ("Excel导出", self._show_placeholder)
        ]
        
        self.nav_buttons = {}
        self.current_nav = "关于"  # 默认选中
        
        for text, command in nav_items:
            btn = tk.Button(
                nav_frame, 
                text=text, 
                font=("Microsoft YaHei UI", 11),
                bg="#f0f0f0",
                fg="#333333",
                relief=tk.FLAT,
                anchor="w",
                padx=20,
                pady=12,
                cursor="hand2",
                command=lambda c=command, t=text: self._on_nav_click(t, c)
            )
            btn.pack(fill=tk.X)
            self.nav_buttons[text] = btn
        
        # 绑定hover事件
        self._bind_nav_hover()
        
        # 默认显示关于页面
        self._show_about()
        # 设置默认选中状态
        self._update_nav_selection("关于")
        
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _bind_nav_hover(self):
        """绑定导航按钮hover事件"""
        for text, btn in self.nav_buttons.items():
            btn.bind("<Enter>", lambda e, t=text: self._on_nav_hover(t, True))
            btn.bind("<Leave>", lambda e, t=text: self._on_nav_hover(t, False))
    
    def _on_nav_hover(self, text, is_hover):
        """处理导航按钮hover"""
        if text == self.current_nav:
            return  # 当前选中的不处理hover
        btn = self.nav_buttons.get(text)
        if btn:
            if is_hover:
                btn.config(bg="#4CAF50", fg="white")  # hover绿色
            else:
                btn.config(bg="#f0f0f0", fg="#333333")  # 默认灰色
    
    def _update_nav_selection(self, text):
        """更新导航按钮选中状态"""
        self.current_nav = text
        for t, btn in self.nav_buttons.items():
            if t == text:
                btn.config(bg="#4a90d9", fg="white")  # 选中蓝色
            else:
                btn.config(bg="#f0f0f0", fg="#333333")  # 默认灰色
    
    def _on_nav_click(self, text, command):
        self._update_nav_selection(text)
        command()
    
    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def _show_about(self):
        self._clear_content()
        
        # 版本号
        version_label = tk.Label(
            self.content_frame,
            text=f"Ver {VERSION}",
            font=("Microsoft YaHei UI", 28, "italic"),
            bg="white",
            fg="#333333"
        )
        version_label.pack(pady=(60, 20))
        
        # 项目名称
        name_label = tk.Label(
            self.content_frame,
            text=PROJECT_NAME,
            font=("Microsoft YaHei UI", 14),
            bg="white",
            fg="#666666"
        )
        name_label.pack(pady=(0, 10))
        
        # 描述
        desc_label = tk.Label(
            self.content_frame,
            text=DESCRIPTION,
            font=("Microsoft YaHei UI", 11),
            bg="white",
            fg="#888888"
        )
        desc_label.pack(pady=(0, 30))
        
        # 作者
        author_label = tk.Label(
            self.content_frame,
            text=f"作者：{AUTHOR}",
            font=("Microsoft YaHei UI", 11),
            bg="white",
            fg="#888888"
        )
        author_label.pack(pady=(0, 30))
        
        # URL 框架
        url_frame = tk.Frame(self.content_frame, bg="white")
        url_frame.pack(pady=10)
        
        url_label = tk.Label(
            url_frame,
            text=PROJECT_URL,
            font=("Microsoft YaHei UI", 11),
            bg="#f5f5f5",
            fg="#555555",
            padx=15,
            pady=8
        )
        url_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 复制按钮
        copy_btn = tk.Button(
            url_frame,
            text="复制",
            font=("Microsoft YaHei UI", 10),
            bg="#4a90d9",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self._copy_url
        )
        copy_btn.pack(side=tk.LEFT, padx=5)
        
        # 跳转按钮
        open_btn = tk.Button(
            url_frame,
            text="跳转",
            font=("Microsoft YaHei UI", 10),
            bg="#5cb85c",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self._open_url
        )
        open_btn.pack(side=tk.LEFT, padx=5)
    
    def _show_wardrobe_manage(self):
        self._clear_content()
        
        # 标题
        title_label = tk.Label(
            self.content_frame,
            text="衣柜管理",
            font=("Microsoft YaHei UI", 18, "bold"),
            bg="white",
            fg="#333333"
        )
        title_label.pack(pady=(30, 20))
        
        # 按钮区
        btn_frame = tk.Frame(self.content_frame, bg="white")
        btn_frame.pack(pady=10)
        
        new_btn = tk.Button(
            btn_frame,
            text="新建衣柜",
            font=("Microsoft YaHei UI", 11),
            bg="#4CAF50",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._create_wardrobe
        )
        new_btn.pack(side=tk.LEFT, padx=10)
        
        delete_btn = tk.Button(
            btn_frame,
            text="删除衣柜",
            font=("Microsoft YaHei UI", 11),
            bg="#4CAF50",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._delete_wardrobe
        )
        delete_btn.pack(side=tk.LEFT, padx=10)
        
        # 衣柜列表框架
        list_frame = tk.Frame(self.content_frame, bg="white")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)
        
        # 列表标题
        list_title = tk.Label(
            list_frame,
            text="已有衣柜（双击切换）",
            font=("Microsoft YaHei UI", 12),
            bg="white",
            fg="#666666"
        )
        list_title.pack(anchor="w", pady=(0, 10))
        
        # 衣柜列表
        self.wardrobe_listbox = tk.Listbox(
            list_frame,
            font=("Microsoft YaHei UI", 11),
            selectbackground="#4a90d9",
            selectforeground="white",
            height=10
        )
        self.wardrobe_listbox.pack(fill=tk.BOTH, expand=True)
        self.wardrobe_listbox.bind("<Double-1>", self._switch_wardrobe)
        
        self._refresh_wardrobe_list()
    
    def _refresh_wardrobe_list(self):
        """刷新衣柜列表"""
        self.wardrobe_listbox.delete(0, tk.END)
        wardrobes = get_all_wardrobes()
        current = self.main_window.current_wardrobe
        
        for wardrobe in wardrobes:
            display_name = f"{wardrobe}"
            if wardrobe == current:
                display_name += " (当前)"
            self.wardrobe_listbox.insert(tk.END, display_name)
    
    def _create_wardrobe(self):
        """新建衣柜"""
        dialog = tk.Toplevel(self.window)
        dialog.title("新建衣柜")
        dialog.geometry("500x290")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        
        # 居中
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 500) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 290) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # 主框架
        main_frame = tk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        tk.Label(main_frame, text="衣柜名称：", font=("Microsoft YaHei UI", 11)).pack(anchor="w", pady=(0, 8))
        
        name_entry = tk.Entry(main_frame, font=("Microsoft YaHei UI", 11), width=30)
        name_entry.pack(fill=tk.X, pady=(0, 20))
        name_entry.focus_set()
        
        def on_confirm(event=None):
            name = name_entry.get().strip()
            if not name:
                self._show_soft_dialog("提示", "请输入衣柜名称", dialog)
                return
            if create_wardrobe(name):
                self._show_soft_dialog("成功", f"衣柜「{name}」创建成功", dialog, lambda: dialog.destroy())
                self._refresh_wardrobe_list()
            else:
                self._show_soft_dialog("错误", "衣柜已存在或创建失败", dialog)
        
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        confirm_btn = tk.Button(btn_frame, text="确定", font=("Microsoft YaHei UI", 10), padx=20, pady=5, 
                                bg="#4CAF50", fg="white", relief=tk.FLAT, cursor="hand2",
                                command=on_confirm)
        confirm_btn.pack(side=tk.LEFT)
        
        dialog.bind("<Return>", on_confirm)
    
    def _switch_wardrobe(self, event=None):
        """切换衣柜"""
        selection = self.wardrobe_listbox.curselection()
        if not selection:
            return
        
        selected_text = self.wardrobe_listbox.get(selection[0])
        wardrobe_name = selected_text.replace(" (当前)", "")
        
        if wardrobe_name == self.main_window.current_wardrobe:
            self._show_soft_dialog("提示", "已经是当前衣柜", self.window)
            return
        
        self._show_soft_confirm(
            "切换衣柜",
            f"确定切换到衣柜「{wardrobe_name}」？\n当前窗口将关闭并重新打开。",
            lambda: self._do_switch_wardrobe(wardrobe_name)
        )
    
    def _do_switch_wardrobe(self, wardrobe_name):
        """执行切换衣柜"""
        self.window.destroy()
        self.main_window._switch_to_wardrobe(wardrobe_name)
    
    def _delete_wardrobe(self):
        """删除衣柜"""
        selection = self.wardrobe_listbox.curselection()
        if not selection:
            self._show_soft_dialog("提示", "请先选择要删除的衣柜", self.window)
            return
        
        selected_text = self.wardrobe_listbox.get(selection[0])
        wardrobe_name = selected_text.replace(" (当前)", "")
        
        if wardrobe_name == self.main_window.current_wardrobe:
            self._show_soft_dialog("提示", "无法删除当前使用的衣柜", self.window)
            return
        
        self._show_soft_confirm(
            "删除衣柜",
            f"确定删除衣柜「{wardrobe_name}」？\n此操作不可恢复！",
            lambda: self._do_delete_wardrobe(wardrobe_name)
        )
    
    def _do_delete_wardrobe(self, wardrobe_name):
        """执行删除衣柜"""
        if delete_wardrobe(wardrobe_name):
            self._show_soft_dialog("成功", f"衣柜「{wardrobe_name}」已删除", self.window)
            self._refresh_wardrobe_list()
        else:
            self._show_soft_dialog("错误", "删除失败", self.window)
    
    def _show_soft_dialog(self, title, message, parent, callback=None):
        """显示软弹窗（无闪烁、无提示音）"""
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.geometry("300x120")
        dialog.resizable(False, False)
        dialog.transient(parent)
        
        # 居中
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 300) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 120) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # 背景框架
        frame = tk.Frame(dialog, bg="white", highlightbackground="#cccccc", highlightthickness=1)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 消息
        msg_label = tk.Label(frame, text=message, font=("Microsoft YaHei UI", 10), 
                            bg="white", fg="#333333", wraplength=260)
        msg_label.pack(pady=(25, 15))
        
        # 确定按钮
        def close():
            dialog.destroy()
            if callback:
                parent.after(50, callback)
        
        btn = tk.Button(frame, text="确定", font=("Microsoft YaHei UI", 10), 
                       bg="#4a90d9", fg="white", relief=tk.FLAT, padx=20, cursor="hand2",
                       command=close)
        btn.pack(pady=(0, 15))
        
        dialog.bind("<Return>", lambda e: close())
        dialog.bind("<Escape>", lambda e: close())
    
    def _show_soft_confirm(self, title, message, on_confirm):
        """显示软确认弹窗（无闪烁、无提示音）"""
        dialog = tk.Toplevel(self.window)
        dialog.title(title)
        dialog.geometry("320x140")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        
        # 居中
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 320) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 140) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # 背景框架
        frame = tk.Frame(dialog, bg="white", highlightbackground="#cccccc", highlightthickness=1)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 消息
        msg_label = tk.Label(frame, text=message, font=("Microsoft YaHei UI", 10), 
                            bg="white", fg="#333333", wraplength=280, justify="center")
        msg_label.pack(pady=(25, 15))
        
        # 按钮框架
        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack(pady=(0, 15))
        
        def confirm():
            dialog.destroy()
            self.window.after(50, on_confirm)
        
        def cancel():
            dialog.destroy()
        
        tk.Button(btn_frame, text="确定", font=("Microsoft YaHei UI", 10), 
                 bg="#4a90d9", fg="white", relief=tk.FLAT, padx=20, cursor="hand2",
                 command=confirm).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="取消", font=("Microsoft YaHei UI", 10), 
                 bg="#e0e0e0", fg="#333333", relief=tk.FLAT, padx=20, cursor="hand2",
                 command=cancel).pack(side=tk.LEFT, padx=5)
        
        dialog.bind("<Return>", lambda e: confirm())
        dialog.bind("<Escape>", lambda e: cancel())
    
    def _show_placeholder(self):
        self._clear_content()
        
        placeholder_label = tk.Label(
            self.content_frame,
            text="功能开发中...",
            font=("Microsoft YaHei UI", 14),
            bg="white",
            fg="#999999"
        )
        placeholder_label.pack(pady=100)
    
    def _copy_url(self):
        self.window.clipboard_clear()
        self.window.clipboard_append(PROJECT_URL)
    
    def _open_url(self):
        webbrowser.open(PROJECT_URL)
    
    def _on_close(self):
        self.window.withdraw()
