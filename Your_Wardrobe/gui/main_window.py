import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from config.config import (
    get_image_dir, get_ui_config_file, get_column_widths_file, 
    get_window_pos_file, get_main_window_config_file, WINDOW_WIDTH, WINDOW_HEIGHT
)
from core.db_operations import WardrobeDB, get_all_wardrobes, create_wardrobe
from gui.photo_viewer import PhotoViewer
from gui.settings_window import SettingsWindow
from PIL import Image, ImageTk
from pathlib import Path
import json
import random

class WardrobeMainWindow:
    def __init__(self):
        self.root = ttk.Window(themename="cosmo")
        self.root.title("")
        self.ascending_var = tk.BooleanVar(value=True)
        self.col_field_map = {}
        self.current_wardrobe = None
        self.db = None
        self.photo_viewer = None
        self.settings_window = None
    
        self._check_and_show()

    def _check_and_show(self):
        """检查是否有衣柜，显示对应界面"""
        wardrobes = get_all_wardrobes()
        if not wardrobes:
            self._show_first_start_page()
        else:
            self.current_wardrobe = wardrobes[0]
            self._init_wardrobe()
            self._show_main_interface()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _init_wardrobe(self):
        """初始化衣柜相关资源"""
        self.db = WardrobeDB(self.current_wardrobe)
        self.root.title(self.current_wardrobe)
        self._load_window_pos()
        self.column_widths = self._load_column_widths()
        # 初始化照片查看器
        self.photo_viewer = PhotoViewer(self.root)

    # ------------------------------
    # 配置文件路径
    # ------------------------------
    def _get_ui_config_file(self):
        return get_ui_config_file(self.current_wardrobe)
    
    def _get_column_widths_file(self):
        return get_column_widths_file(self.current_wardrobe)
    
    def _get_window_pos_file(self):
        return get_window_pos_file(self.current_wardrobe)

    # ------------------------------
    # 缓存相关：保存/加载 UI 配置
    # ------------------------------
    def _load_ui_config(self):
        """加载 UI 配置（品类排序等）"""
        try:
            config_file = self._get_ui_config_file()
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载UI配置失败：{e}")
        return {}

    def _save_ui_config(self):
        """保存 UI 配置"""
        try:
            config = self._load_ui_config()
            config["type_order"] = self.type_order
            if hasattr(self, "column_order"):
                config["column_order"] = self.column_order
            config_file = self._get_ui_config_file()
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存UI配置失败：{e}")

    def _load_column_widths(self):
        """加载用户调整的列宽配置"""
        try:
            config_file = self._get_column_widths_file()
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载列宽失败：{e}")
        return {
            "ID": 80,
            "名称": 150,
            "尺码": 80,
            "图片路径": 200
        }

    def _save_column_widths(self):
        """保存用户调整的列宽"""
        try:
            config_file = self._get_column_widths_file()
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(self.column_widths, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存列宽失败：{e}")

    def _load_window_pos(self):
        """加载窗口大小（从通用配置），位置始终居中"""
        try:
            config_file = get_main_window_config_file()
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    pos = json.load(f)
                    width = pos.get("width", WINDOW_WIDTH)
                    height = pos.get("height", WINDOW_HEIGHT)
                    self.root.geometry(f"{width}x{height}")
                    self._center_window(self.root)
                    return
        except Exception as e:
            print(f"加载窗口配置失败：{e}")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self._center_window(self.root)

    def _save_window_pos(self):
        """保存窗口大小（不保存位置）"""
        try:
            pos = {
                "width": self.root.winfo_width(),
                "height": self.root.winfo_height()
            }
            config_file = get_main_window_config_file()
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(pos, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存窗口配置失败：{e}")

    def _open_settings(self):
        """打开设置窗口"""
        if not self.settings_window:
            self.settings_window = SettingsWindow(self.root, self)
        self.settings_window.show()
    
    def _switch_to_wardrobe(self, wardrobe_name):
        """切换到指定衣柜"""
        if self.db:
            self.db.close()
        # 重置设置窗口引用
        self.settings_window = None
        self.current_wardrobe = wardrobe_name
        self._init_wardrobe()
        self._show_main_interface()

    def _on_window_close(self):
        """窗口关闭时保存配置"""
        self._save_window_pos()
        self._save_column_widths()
        if self.photo_viewer:
            self.photo_viewer.hide()
        if self.db:
            self.db.close()
        self.root.destroy()

    # ------------------------------
    # 首次启动
    # ------------------------------
    def _show_first_start_page(self):
        """首次启动创建衣柜"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self._center_window(self.root)
        
        container = ttk.Frame(self.root)
        container.place(relx=0.5, rely=0.5, anchor=CENTER)
        
        ttk.Label(container, text="欢迎使用衣柜管理系统", font=("微软雅黑", 20, "bold")).pack(pady=20)
        ttk.Label(container, text="请输入衣柜名称：", font=("微软雅黑", 12)).pack(pady=10)
        self.first_wardrobe_name = ttk.Entry(container, width=30, font=("微软雅黑", 12))
        self.first_wardrobe_name.pack(pady=5)
        self.first_wardrobe_name.bind("<Return>", lambda e: self._create_first_wardrobe())
        ttk.Button(container, text="确认创建", bootstyle=SUCCESS, command=self._create_first_wardrobe, width=15).pack(pady=20)

    def _create_first_wardrobe(self):
        """创建第一个衣柜"""
        wardrobe_name = self.first_wardrobe_name.get().strip()
        if not wardrobe_name:
            print("提示：衣柜名称不能为空！")
            return
        if create_wardrobe(wardrobe_name):
            self.current_wardrobe = wardrobe_name
            self._init_wardrobe()
            self._show_main_interface()
        else:
            print("错误：衣柜创建失败！")

    # ------------------------------
    # 主界面核心
    # ------------------------------
    def _show_main_interface(self):
        """主界面：左侧品类列表 + 右侧内容区"""
        self.db.fix_old_records()
        for widget in self.root.winfo_children():
            widget.destroy()

        self.main_paned = ttk.Panedwindow(self.root, orient=HORIZONTAL)
        self.main_paned.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        left_frame = ttk.Frame(self.main_paned, width=180)
        self.main_paned.add(left_frame, weight=0)

        right_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(right_frame, weight=1)

        self._create_left_type_panel(left_frame)
        self._create_right_content_panel(right_frame)

        self._load_types_with_order()
        self._load_type_list()
        self._select_type(0)

    def _load_types_with_order(self):
        """加载品类并应用用户自定义排序"""
        db_types = self.db.get_clothes_types() or []
        
        # 确保"未分组"存在
        if "默认" in db_types:
            db_types.remove("默认")
            if "未分组" not in db_types:
                db_types.insert(0, "未分组")
        elif "未分组" not in db_types:
            db_types.insert(0, "未分组")
        
        ui_config = self._load_ui_config()
        saved_order = ui_config.get("type_order", [])

        self.type_order = []
        for t in saved_order:
            if t in db_types and t not in ["全部", "未分组"]:
                self.type_order.append(t)
        for t in db_types:
            if t not in self.type_order and t not in ["全部", "未分组"]:
                self.type_order.append(t)
        
        self.types = ["全部", "未分组"] + self.type_order

    def _create_left_type_panel(self, parent):
        """创建左侧品类列表面板"""
        ttk.Label(parent, text="衣物品类", font=("微软雅黑", 11, "bold")).pack(pady=(5, 10))

        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=BOTH, expand=YES, padx=5)

        self.type_listbox = tk.Listbox(
            list_frame,
            font=("微软雅黑", 10),
            selectmode=SINGLE,
            activestyle="none",
            bg="#f5f5f5",
            selectbackground="#4a90d9",
            selectforeground="white",
            highlightthickness=0,
            borderwidth=0
        )
        self.type_listbox.pack(side=LEFT, fill=BOTH, expand=YES)

        scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.type_listbox.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.type_listbox.config(yscrollcommand=scrollbar.set)

        self.type_listbox.bind("<<ListboxSelect>>", self._on_type_select)
        self.type_listbox.bind("<Button-3>", self._show_type_context_menu)

        self._setup_drag_drop()

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=X, pady=10, padx=5)
        ttk.Button(btn_frame, text="+ 新建品类", bootstyle=SUCCESS, command=self._create_clothes_type).pack(fill=X, pady=2)

    def _setup_drag_drop(self):
        """设置拖拽排序：长按后拖拽"""
        self.drag_start_index = None
        self.drag_current_index = None
        self.drag_active = False
        self.drag_timer = None
        self.drag_delay = 300

        self.type_listbox.bind("<Button-1>", self._on_drag_press)
        self.type_listbox.bind("<B1-Motion>", self._on_drag_motion)
        self.type_listbox.bind("<ButtonRelease-1>", self._on_drag_release)
        self.type_listbox.bind("<Leave>", self._on_drag_cancel)

    def _on_drag_press(self, event):
        """按下鼠标：启动延迟检测"""
        idx = self.type_listbox.nearest(event.y)
        if idx < 2:
            return
        self.drag_start_index = idx
        self.drag_current_index = idx
        self.drag_active = False
        self.drag_timer = self.root.after(self.drag_delay, self._activate_drag_mode)

    def _activate_drag_mode(self):
        """激活拖拽模式"""
        self.drag_active = True
        self.type_listbox.config(cursor="hand2")
        self._show_drag_hint()

    def _show_drag_hint(self):
        """显示拖拽提示"""
        if self.drag_start_index is not None:
            type_name = self.type_listbox.get(self.drag_start_index)
            print(f"拖拽模式已激活：正在拖动「{type_name}」")

    def _on_drag_motion(self, event):
        """拖拽过程中"""
        if not self.drag_active or self.drag_start_index is None:
            return
        new_index = self.type_listbox.nearest(event.y)
        if new_index < 2:
            return
        if new_index != self.drag_current_index and 0 <= new_index < self.type_listbox.size():
            self._swap_listbox_items(self.drag_current_index, new_index)
            self.drag_current_index = new_index

    def _on_drag_release(self, event):
        """释放鼠标：保存排序到配置文件"""
        if self.drag_timer:
            self.root.after_cancel(self.drag_timer)
            self.drag_timer = None

        self.type_listbox.config(cursor="")
        
        if self.drag_active and self.drag_start_index is not None:
            if self.drag_start_index != self.drag_current_index:
                all_types = list(self.type_listbox.get(0, tk.END))
                self.type_order = all_types[2:]
                self._save_ui_config()
                print("品类顺序已保存")
        
        self.drag_start_index = None
        self.drag_current_index = None
        self.drag_active = False

    def _on_drag_cancel(self, event):
        """取消拖拽"""
        if self.drag_timer:
            self.root.after_cancel(self.drag_timer)
            self.drag_timer = None
        self.type_listbox.config(cursor="")
        self.drag_start_index = None
        self.drag_current_index = None
        self.drag_active = False

    def _swap_listbox_items(self, idx1, idx2):
        """交换两个列表项（确保不交换前两个"""
        if idx1 < 2 or idx2 < 2:
            return
        item1 = self.type_listbox.get(idx1)
        item2 = self.type_listbox.get(idx2)
        self.type_listbox.delete(idx1)
        self.type_listbox.insert(idx1, item2)
        self.type_listbox.delete(idx2)
        self.type_listbox.insert(idx2, item1)
        self.type_listbox.selection_set(idx2)

    def _create_right_content_panel(self, parent):
        """创建右侧内容面板"""
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(top_frame, text="衣物列表", font=("微软雅黑", 11, "bold")).pack(side=LEFT)

        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(side=RIGHT)
        ttk.Button(btn_frame, text="⚙", width=3, bootstyle="secondary", command=self._open_settings).pack(side=RIGHT, padx=(0, 10))
        ttk.Button(btn_frame, text="添加衣物", bootstyle=PRIMARY, command=self._open_add_clothes_window).pack(side=RIGHT, padx=5)
        ttk.Button(btn_frame, text="添加衣物参数", bootstyle=INFO, command=self._add_custom_param).pack(side=RIGHT)

        self.content_frame = ttk.Frame(parent)
        self.content_frame.pack(fill=BOTH, expand=YES)

    def _load_type_list(self):
        """加载品类列表到左侧"""
        self.type_listbox.delete(0, tk.END)
        for type_name in self.types:
            self.type_listbox.insert(tk.END, type_name)

    def _select_type(self, index):
        """选中指定索引的品类"""
        if 0 <= index < self.type_listbox.size():
            self.type_listbox.selection_clear(0, tk.END)
            self.type_listbox.selection_set(index)
            self.type_listbox.see(index)
            self._show_type_content(self.types[index])

    def _on_type_select(self, event):
        """品类选择事件"""
        selection = self.type_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.types):
                self._show_type_content(self.types[index])

    def _show_type_content(self, type_name):
        """显示指定品类的内容"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self._create_type_content(self.content_frame, type_name)

    def _create_type_content(self, parent, type_name):
        """创建品类内容区域"""
        sort_frame = ttk.Frame(parent)
        sort_frame.pack(fill=X, padx=10, pady=5)
        ttk.Label(sort_frame, text="自定义排序：").pack(side=LEFT)

        base_sort = ["id（添加时间）", "size（尺码）"]
        custom_params = self.db.get_custom_params()
        custom_sort = [f"{p}（自定义）" for p in custom_params]
        all_sort = base_sort + custom_sort

        self.sort_by_var = tk.StringVar(value=base_sort[0])
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_by_var, values=all_sort, width=15)
        sort_combo.pack(side=LEFT, padx=5)

        self.ascending_var = tk.BooleanVar(value=True)
        ttk.Button(sort_frame, text="升序", command=lambda: self._change_sort(type_name, True)).pack(side=LEFT, padx=2)
        ttk.Button(sort_frame, text="降序", command=lambda: self._change_sort(type_name, False)).pack(side=LEFT)

        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=BOTH, expand=YES, padx=10, pady=5)

        base_cols = ["ID", "名称", "尺码", "图片路径"]
        custom_cols = self.db.get_custom_params()
        all_cols = base_cols + custom_cols

        ui_config = self._load_ui_config()
        saved_column_order = ui_config.get("column_order", [])
        
        self.column_order = []
        for col in saved_column_order:
            if col in all_cols:
                self.column_order.append(col)
        for col in all_cols:
            if col not in self.column_order:
                self.column_order.append(col)
        
        all_cols = self.column_order

        self.col_field_map = {
            "ID": "id",
            "名称": "clothes_name",
            "尺码": "size",
            "图片路径": "image_path"
        }
        for p in custom_params:
            self.col_field_map[p] = p

        style = ttk.Style()
        style.configure("Treeview.Heading", 
                       borderwidth=2, 
                       relief="solid", 
                       foreground="black", 
                       background="#f0f0f0")
        
        tree = ttk.Treeview(table_frame, columns=all_cols, show="headings")
        
        for col in all_cols:
            width = self.column_widths.get(col, 120 if col in base_cols else 100)
            tree.column(col, width=width, minwidth=50)
            tree.heading(col, text=col)
        
        drag_data = {
            'active': False,
            'start_col': None,
            'start_x': None,
            'timer': None
        }
        
        def on_click(event):
            x = event.x
            region = tree.identify_region(x, event.y)
            
            if region == "separator":
                return
            
            col_id = tree.identify_column(x)
            if col_id:
                drag_data['start_col'] = col_id
                drag_data['start_x'] = x
                drag_data['timer'] = self.root.after(250, lambda: activate_drag())
        
        def activate_drag():
            drag_data['active'] = True
            tree.config(cursor="fleur")
        
        def on_motion(event):
            if not drag_data['active'] or not drag_data['start_col']:
                return
            
            col_id = tree.identify_column(event.x)
            if col_id and col_id != drag_data['start_col']:
                idx1 = int(drag_data['start_col'].replace("#", "")) - 1
                idx2 = int(col_id.replace("#", "")) - 1
                
                if 0 <= idx1 < len(all_cols) and 0 <= idx2 < len(all_cols):
                    all_cols[idx1], all_cols[idx2] = all_cols[idx2], all_cols[idx1]
                    self.column_order = all_cols.copy()
                    drag_data['start_col'] = col_id
        
        def on_release(event):
            if drag_data['timer']:
                self.root.after_cancel(drag_data['timer'])
                drag_data['timer'] = None
            
            should_refresh = False
            if drag_data['active']:
                self._save_ui_config()
                should_refresh = True
            
            drag_data['active'] = False
            drag_data['start_col'] = None
            drag_data['start_x'] = None
            
            try:
                tree.config(cursor="")
            except:
                pass
            
            if should_refresh:
                selection = self.type_listbox.curselection()
                if selection:
                    current_type = self.types[selection[0]]
                    self._show_type_content(current_type)
        
        def on_column_resize(event):
            col = tree.identify_column(event.x)
            if not col or col == "":
                return
            col_idx = int(col.replace("#", "")) - 1
            if 0 <= col_idx < len(all_cols):
                col_name = all_cols[col_idx]
                self.column_widths[col_name] = tree.column(col, "width")
        
        tree.bind("<Button-1>", on_click)
        tree.bind("<B1-Motion>", on_motion)
        tree.bind("<ButtonRelease-1>", on_release)
        tree.bind("<ButtonRelease-1>", on_column_resize, add="+")
        tree.bind("<Button-3>", lambda e, tn=type_name, tr=tree, cols=all_cols: self._show_table_context_menu(e, tn, tr, cols))
        tree.bind("<<TreeviewSelect>>", lambda e, tr=tree: self._on_tree_select(tr))
        
        scrollbar = ttk.Scrollbar(table_frame, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        setattr(self, f"tree_{type_name}", tree)
        self._refresh_tab_list(type_name, True)

    def _on_tree_select(self, tree):
        """表格选中事件：更新照片查看器"""
        selection = tree.selection()
        if not selection:
            if self.photo_viewer:
                self.photo_viewer.hide()
            return
        
        clothes_id = int(selection[0])
        clothes_info = self.db.get_clothes_by_id(clothes_id)
        if clothes_info and self.photo_viewer:
            image_path = clothes_info.get("image_path", "")
            clothes_name = clothes_info.get("clothes_name", "照片查看器")
            self.photo_viewer.show(image_path, clothes_name)

    def _change_sort(self, type_name, ascending):
        """切换升序/降序"""
        self.ascending_var.set(ascending)
        self._refresh_tab_list(type_name, ascending)

    def _on_column_click(self, col_name, type_name):
        """双击列头排序：切换升序/降序"""
        sort_field = self.col_field_map.get(col_name, "id")
        self.ascending_var.set(not self.ascending_var.get())
        self._refresh_tab_list(type_name, self.ascending_var.get())
        self.sort_by_var.set(f"{sort_field}（{col_name}）")

    def _refresh_tab_list(self, type_name, ascending=True):
        """刷新表格：显示当前品类的衣物，全部品类显示所有"""
        sort_by = self.sort_by_var.get().split("（")[0]
        
        query_type = None if type_name == "全部" else type_name
        
        clothes_data = self.db.get_clothes(
            clothes_type=query_type,
            sort_by=sort_by,
            ascending=ascending
        )
        custom_params = self.db.get_custom_params()
        
        tree = getattr(self, f"tree_{type_name}", None)
        if not tree:
            return
        
        for item in tree.get_children():
            tree.delete(item)
        
        for item in clothes_data:
            data_map = {
                "ID": item["id"],
                "名称": item["clothes_name"],
                "尺码": item["size"],
                "图片路径": item["image_path"] or "-"
            }
            for p in custom_params:
                data_map[p] = item["custom_params"].get(p, "")
            
            vals = [data_map[col] for col in self.column_order]
            tree.insert("", "end", values=vals, iid=item["id"])

    # ------------------------------
    # 衣物右键菜单：精准定位 + 编辑/删除
    # ------------------------------
    def _show_table_context_menu(self, event, type_name, tree, all_cols):
        """表格右键菜单：区分列头和数据行"""
        region = tree.identify_region(event.x, event.y)
        
        if region == "heading":
            # 点击列头
            col_id = tree.identify_column(event.x)
            if not col_id:
                return
            col_idx = int(col_id.replace("#", "")) - 1
            if col_idx < 0 or col_idx >= len(all_cols):
                return
            col_name = all_cols[col_idx]
            
            # 基础列不可编辑删除
            base_cols = ["ID", "名称", "尺码", "图片路径"]
            if col_name in base_cols:
                return
            
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label=f"重命名「{col_name}」", command=lambda: self._rename_custom_param(col_name))
            menu.add_separator()
            menu.add_command(label=f"删除「{col_name}」", command=lambda: self._delete_custom_param(col_name, type_name))
            menu.post(event.x_root, event.y_root)
        else:
            # 点击数据行
            row_id = tree.identify_row(event.y)
            if not row_id:
                return
            
            tree.selection_set(row_id)
            clothes_id = int(row_id)
            
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="编辑", command=lambda: self._open_add_clothes_window(clothes_id))
            menu.add_command(label="删除", command=lambda: self._delete_clothes(clothes_id, type_name, tree))
            
            menu.post(event.x_root, event.y_root)

    def _rename_custom_param(self, old_name):
        """重命名自定义参数"""
        win = ttk.Toplevel(self.root)
        win.title("重命名参数")
        win.geometry("500x290")
        self._center_window(win)
        win.grab_set()
        
        ttk.Label(win, text="新名称：").pack(pady=20)
        param_entry = ttk.Entry(win, width=20)
        param_entry.pack(pady=5)
        param_entry.insert(0, old_name)
        
        def confirm():
            new_name = param_entry.get().strip()
            if not new_name:
                print("提示：参数名称不能为空！")
                return
            if new_name == old_name:
                win.destroy()
                return
            if self.db.rename_custom_param(old_name, new_name):
                # 更新column_order
                if old_name in self.column_order:
                    idx = self.column_order.index(old_name)
                    self.column_order[idx] = new_name
                    self._save_ui_config()
                win.destroy()
                selection = self.type_listbox.curselection()
                if selection:
                    current_type = self.types[selection[0]]
                    self._show_type_content(current_type)
            else:
                print("错误：参数名称已存在！")
        
        param_entry.bind("<Return>", lambda e: confirm())
        ttk.Button(win, text="确认", bootstyle=SUCCESS, command=confirm).pack(pady=10)

    def _delete_custom_param(self, param_name, type_name):
        """删除自定义参数"""
        if self.db.delete_custom_param(param_name):
            # 从column_order中移除
            if param_name in self.column_order:
                self.column_order.remove(param_name)
                self._save_ui_config()
            self._show_type_content(type_name)

    def _delete_clothes(self, clothes_id, type_name, tree):
        """删除衣物"""
        self.db.delete_clothes(clothes_id)
        self._refresh_tab_list(type_name, True)

    # ------------------------------
    # 品类右键菜单
    # ------------------------------
    def _show_type_context_menu(self, event):
        """品类列表右键菜单：全部和未分组不可右键"""
        current_type = None
        
        index = self.type_listbox.nearest(event.y)
        if 0 <= index < self.type_listbox.size():
            bbox = self.type_listbox.bbox(index)
            if bbox and event.y >= bbox[1] and event.y <= bbox[1] + bbox[3]:
                current_type = self.type_listbox.get(index)
                # 全部和未分组不可右键
                if current_type in ["全部", "未分组"]:
                    return
                self.type_listbox.selection_clear(0, tk.END)
                self.type_listbox.selection_set(index)
            else:
                return
        else:
            return
        
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label=f"重命名「{current_type}」", command=lambda: self._rename_clothes_type(current_type))
        menu.add_separator()
        menu.add_command(label=f"删除「{current_type}」", command=lambda: self._delete_clothes_type(current_type))
        
        menu.post(event.x_root, event.y_root)

    def _rename_clothes_type(self, old_name):
        """重命名品类"""
        win = ttk.Toplevel(self.root)
        win.title("重命名品类")
        win.geometry("500x290")
        self._center_window(win)
        win.grab_set()
        
        ttk.Label(win, text="新名称：").pack(pady=20)
        type_entry = ttk.Entry(win, width=20)
        type_entry.pack(pady=5)
        type_entry.insert(0, old_name)
        
        def confirm():
            new_name = type_entry.get().strip()
            if not new_name:
                print("提示：品类名称不能为空！")
                return
            if new_name in ["全部", "未分组"]:
                print(f"提示：不能使用「{new_name}」作为品类名！")
                return
            if new_name == old_name:
                win.destroy()
                return
            if self.db.rename_clothes_type(old_name, new_name):
                # 更新type_order
                if old_name in self.type_order:
                    idx = self.type_order.index(old_name)
                    self.type_order[idx] = new_name
                    self._save_ui_config()
                win.destroy()
                self._load_types_with_order()
                self._load_type_list()
                try:
                    idx = self.types.index(new_name)
                    self._select_type(idx)
                except:
                    self._select_type(0)
            else:
                print("错误：品类名称已存在！")
        
        type_entry.bind("<Return>", lambda e: confirm())
        ttk.Button(win, text="确认", bootstyle=SUCCESS, command=confirm).pack(pady=10)

    def _create_clothes_type(self):
        """新建品类弹窗"""
        win = ttk.Toplevel(self.root)
        win.title("新建衣物品类")
        win.geometry("500x290")
        self._center_window(win)
        win.grab_set()
        
        # 主框架
        ttk.Label(win, text="品类名称：").pack(pady=20)
        type_entry = ttk.Entry(win, width=20)
        type_entry.pack(pady=5)
        
        def confirm():
            type_name = type_entry.get().strip()
            if not type_name:
                print("提示：品类名称不能为空！")
                return
            if type_name in ["全部", "未分组"]:
                print(f"提示：不能创建「{type_name}」品类！")
                return
            if self.db.add_clothes_type(type_name):
                win.destroy()
                self.type_order.append(type_name)
                self._save_ui_config()
                self._load_types_with_order()
                self._load_type_list()
                self._select_type(len(self.types) - 1)
            else:
                print("错误：品类已存在！")
        
        type_entry.bind("<Return>", lambda e: confirm())
        ttk.Button(win, text="确认", bootstyle=SUCCESS, command=confirm).pack(pady=10)

    def _delete_clothes_type(self, type_name):
        """删除品类：衣物移到未分组品类"""
        if self.db.delete_clothes_type(type_name):
            if type_name in self.type_order:
                self.type_order.remove(type_name)
            self._save_ui_config()
            self._load_types_with_order()
            self._load_type_list()
            self._select_type(1)
            self._refresh_tab_list("未分组", True)
        else:
            print("错误：未分组品类不可删！")

    # ------------------------------
    # 自定义参数
    # ------------------------------
    def _add_custom_param(self):
        """添加自定义参数弹窗"""
        win = ttk.Toplevel(self.root)
        win.title("添加自定义参数")
        win.geometry("500x290")
        self._center_window(win)
        win.grab_set()
        
        ttk.Label(win, text="参数名称：").pack(pady=20)
        param_entry = ttk.Entry(win, width=20)
        param_entry.pack(pady=5)
        
        def confirm():
            param_name = param_entry.get().strip()
            if not param_name:
                print("提示：参数名称不能为空！")
                return
            if self.db.add_custom_param(param_name):
                if hasattr(self, "column_order") and param_name not in self.column_order:
                    self.column_order.append(param_name)
                    self._save_ui_config()
                win.destroy()
                selection = self.type_listbox.curselection()
                if selection:
                    current_type = self.types[selection[0]]
                    self._show_type_content(current_type)
            else:
                print("错误：参数已存在！")
        
        param_entry.bind("<Return>", lambda e: confirm())
        ttk.Button(win, text="确认", bootstyle=SUCCESS, command=confirm).pack(pady=10)

    # ------------------------------
    # 图片上传
    # ------------------------------
    def _upload_image(self, image_path_var):
        """上传图片"""
        file_path = filedialog.askopenfilename(filetypes=[("图片", "*.jpg *.png *.jpeg")])
        if not file_path:
            return
        
        src_path = Path(file_path)
        image_dir = get_image_dir(self.current_wardrobe)
        file_name = f"clothes_{random.randint(1000,9999)}{src_path.suffix}"
        save_path = image_dir / file_name
        
        try:
            Image.open(file_path).save(str(save_path))
            image_path_var.set(str(save_path))
        except Exception as e:
            print(f"图片保存失败：{str(e)}")

    # ------------------------------
    # 添加/修改衣物：确保衣物仅归属一个品类
    # ------------------------------
    def _open_add_clothes_window(self, clothes_id=None):
        """添加/修改衣物：修改品类后自动从原品类移除"""
        win = ttk.Toplevel(self.root)
        win.title("添加衣物" if not clothes_id else "修改衣物")
        win.geometry("1100x650")
        self._center_window(win)
        win.transient(self.root)
        win.grab_set()

        default_vals = {}
        original_type = None
        if clothes_id:
            clothes_info = self.db.get_clothes_by_id(clothes_id)
            if not clothes_info:
                print("错误：衣物不存在！")
                win.destroy()
                return
            default_vals = clothes_info
            original_type = clothes_info["clothes_type"]

        # 基础参数区域
        basic_frame = ttk.LabelFrame(win, text="基础参数")
        basic_frame.pack(fill=X, padx=20, pady=10)
        basic_inner = ttk.Frame(basic_frame)
        basic_inner.pack(fill=X, padx=10, pady=10)

        # 衣物名称
        ttk.Label(basic_inner, text="衣物名称：").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        clothes_name = ttk.Entry(basic_inner, width=20)
        clothes_name.grid(row=0, column=1, padx=5, pady=5)
        clothes_name.insert(0, default_vals.get("clothes_name", ""))

        # 衣物品类：修改后自动切换归属
        ttk.Label(basic_inner, text="衣物品类：").grid(row=0, column=2, padx=5, pady=5, sticky=W)
        types = self.db.get_clothes_types()
        
        # 确定默认品类：编辑时用原品类，新建时用当前选中品类（排除"全部"）
        if clothes_id:
            default_type = default_vals.get("clothes_type", types[0] if types else "未分组")
        else:
            selection = self.type_listbox.curselection()
            if selection:
                current_type = self.types[selection[0]]
                default_type = current_type if current_type != "全部" else (types[0] if types else "未分组")
            else:
                default_type = types[0] if types else "未分组"
        
        clothes_type_var = tk.StringVar(value=default_type)
        type_combo = ttk.Combobox(basic_inner, textvariable=clothes_type_var, values=types, state="readonly", width=10)
        type_combo.grid(row=0, column=3, padx=5, pady=5)

        # 尺码
        ttk.Label(basic_inner, text="尺码：").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        size = ttk.Entry(basic_inner, width=10)
        size.grid(row=1, column=1, padx=5, pady=5)
        size.insert(0, default_vals.get("size", ""))

        # 图片上传
        ttk.Label(basic_inner, text="图片：").grid(row=1, column=2, padx=5, pady=5, sticky=W)
        image_path = tk.StringVar(value=default_vals.get("image_path", ""))
        ttk.Entry(basic_inner, textvariable=image_path, width=40).grid(row=1, column=3, columnspan=2, padx=5, pady=5)
        ttk.Button(basic_inner, text="选择图片", command=lambda: self._upload_image(image_path)).grid(row=1, column=5, padx=5, pady=5)

        # 自定义参数区域
        custom_frame = ttk.LabelFrame(win, text="自定义参数")
        custom_frame.pack(fill=BOTH, expand=YES, padx=20, pady=10)
        custom_inner = ttk.Frame(custom_frame)
        custom_inner.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        custom_params = self.db.get_custom_params()
        custom_entries = {}
        for idx, param in enumerate(custom_params):
            ttk.Label(custom_inner, text=f"{param}：").grid(row=idx, column=0, padx=5, pady=5, sticky=W)
            entry = ttk.Entry(custom_inner, width=20)
            entry.grid(row=idx, column=1, padx=5, pady=5)
            entry.insert(0, default_vals.get("custom_params", {}).get(param, ""))
            custom_entries[param] = entry

        # 提交逻辑：确保衣物仅归属选中品类
        def submit():
            new_type = clothes_type_var.get()
            data = {
                "clothes_name": clothes_name.get().strip(),
                "clothes_type": new_type,
                "size": size.get().strip(),
                "image_path": image_path.get().strip(),
                "custom_params": {p: e.get().strip() for p, e in custom_entries.items()}
            }

            if not data["clothes_name"]:
                print("提示：衣物名称不能为空！")
                return

            if not clothes_id:
                self.db.add_clothes(data)
            else:
                self.db.update_clothes(clothes_id, data)
                if original_type and original_type != new_type:
                    self._refresh_tab_list(original_type, True)

            win.destroy()
            
            try:
                idx = self.types.index(new_type)
                self.type_listbox.selection_clear(0, tk.END)
                self.type_listbox.selection_set(idx)
                self.type_listbox.activate(idx)
                self.type_listbox.see(idx)
                self._show_type_content(new_type)
            except:
                pass

        ttk.Button(win, text="提交", bootstyle=SUCCESS, command=submit).pack(pady=20)
        
        win.bind("<Return>", lambda e: submit())
        clothes_name.focus_set()

    # ------------------------------
    # 辅助函数
    # ------------------------------
    def _center_window(self, win):
        """窗口居中"""
        win.update_idletasks()
        width = win.winfo_width()
        height = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")
    
    def _show_soft_dialog(self, title, message, parent, callback=None):
        """显示软弹窗（无闪烁、无提示音）"""
        dialog = tk.Toplevel(parent)
        dialog.title("")
        dialog.geometry("300x120")
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()
        dialog.overrideredirect(True)
        
        # 居中
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 300) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 120) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # 背景框架
        frame = tk.Frame(dialog, bg="white", highlightbackground="#cccccc", highlightthickness=1)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = tk.Label(frame, text=title, font=("Microsoft YaHei UI", 12, "bold"), 
                               bg="white", fg="#333333")
        title_label.pack(pady=(15, 10))
        
        # 消息
        msg_label = tk.Label(frame, text=message, font=("Microsoft YaHei UI", 10), 
                            bg="white", fg="#666666", wraplength=260)
        msg_label.pack(pady=(0, 15))
        
        # 确定按钮
        def close():
            dialog.destroy()
            if callback:
                callback()
        
        btn = tk.Button(frame, text="确定", font=("Microsoft YaHei UI", 10), 
                       bg="#4a90d9", fg="white", relief=tk.FLAT, padx=20, cursor="hand2",
                       command=close)
        btn.pack(pady=(0, 15))
        
        dialog.bind("<Return>", lambda e: close())
        dialog.bind("<Escape>", lambda e: close())

    # ------------------------------
    # 程序入口
    # ------------------------------
    def run(self):
        """运行主窗口"""
        self.root.mainloop()

if __name__ == "__main__":
    app = WardrobeMainWindow()
    app.run()
