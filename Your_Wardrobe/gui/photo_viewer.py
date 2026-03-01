import tkinter as tk
from PIL import Image, ImageTk
from pathlib import Path

class PhotoViewer:
    def __init__(self, parent_root):
        self.parent_root = parent_root
        self.window = None
        self.canvas = None
        self.current_image = None
        self.display_image = None
        self.photo = None
        self.rotation = 0
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False
        self.window_width = 400
    
    def show(self, image_path, clothes_name="照片查看器"):
        """显示图片"""
        if not image_path or image_path == "-" or not Path(image_path).exists():
            self.hide()
            return
        
        if not self.window:
            self._create_window()
        
        try:
            self.current_image = Image.open(image_path)
            self.rotation = 0
            self.scale = 1.0
            self.offset_x = 0
            self.offset_y = 0
            self.window.title(clothes_name)
            self._update_display()
            self.window.deiconify()
        except Exception as e:
            print(f"加载图片失败：{e}")
            self.hide()
    
    def hide(self):
        """隐藏窗口"""
        if self.window:
            self.window.withdraw()
    
    def _create_window(self):
        """创建窗口"""
        self.window = tk.Toplevel(self.parent_root)
        self.window.title("照片查看器")
        
        # 默认紧贴主窗口右侧，高度与主窗口相同
        main_x = self.parent_root.winfo_x()
        main_y = self.parent_root.winfo_y()
        main_width = self.parent_root.winfo_width()
        main_height = self.parent_root.winfo_height()
        
        self.window.geometry(f"{self.window_width}x{main_height}+{main_x + main_width + 10}+{main_y}")
        
        # 创建画布
        self.canvas = tk.Canvas(self.window, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)
        
        # 绑定事件
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<MouseWheel>", self._on_scroll)
        self.canvas.bind("<Button-4>", self._on_scroll)
        self.canvas.bind("<Button-5>", self._on_scroll)
        
        self.window.bind("<Configure>", self._on_resize)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 绑定主窗口移动事件，让副窗口跟随
        self.parent_root.bind("<Configure>", self._on_parent_configure)
    
    def _update_position(self):
        """更新窗口位置，紧贴主窗口右侧"""
        if not self.window:
            return
        
        main_x = self.parent_root.winfo_x()
        main_y = self.parent_root.winfo_y()
        main_width = self.parent_root.winfo_width()
        main_height = self.parent_root.winfo_height()
        
        self.window.geometry(f"{self.window_width}x{main_height}+{main_x + main_width + 10}+{main_y}")
    
    def _on_parent_configure(self, event):
        """主窗口移动或调整大小时，副窗口跟随"""
        if event.widget == self.parent_root and self.window and self.window.winfo_viewable():
            self._update_position()
    
    def _update_display(self):
        """更新显示"""
        if not self.current_image or not self.canvas:
            return
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width < 10 or canvas_height < 10:
            self.parent_root.after(50, self._update_display)
            return
        
        # 旋转图片
        rotated = self.current_image.rotate(-self.rotation, expand=True)
        
        # 计算缩放后的尺寸
        img_width, img_height = rotated.size
        new_width = int(img_width * self.scale)
        new_height = int(img_height * self.scale)
        
        if new_width < 1 or new_height < 1:
            return
        
        # 缩放图片
        resized = rotated.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        self.display_image = resized
        self.photo = ImageTk.PhotoImage(resized)
        
        # 清空画布并绘制
        self.canvas.delete("all")
        
        # 计算居中位置（加上偏移）
        x = (canvas_width - new_width) // 2 + self.offset_x
        y = (canvas_height - new_height) // 2 + self.offset_y
        
        self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
    
    def _on_left_click(self, event):
        """左键按下"""
        self.drag_start_x = event.x - self.offset_x
        self.drag_start_y = event.y - self.offset_y
        self.is_dragging = True
    
    def _on_drag(self, event):
        """拖动图片"""
        if self.is_dragging:
            self.offset_x = event.x - self.drag_start_x
            self.offset_y = event.y - self.drag_start_y
            self._update_display()
    
    def _on_release(self, event):
        """释放"""
        self.is_dragging = False
    
    def _on_right_click(self, event):
        """右键菜单"""
        menu = tk.Menu(self.window, tearoff=0)
        menu.add_command(label="顺时针旋转90°", command=lambda: self._rotate(90))
        menu.add_command(label="逆时针旋转90°", command=lambda: self._rotate(-90))
        menu.add_separator()
        menu.add_command(label="重置视图", command=self._reset_view)
        menu.post(event.x_root, event.y_root)
    
    def _rotate(self, angle):
        """旋转图片"""
        self.rotation = (self.rotation + angle) % 360
        self._update_display()
    
    def _reset_view(self):
        """重置视图"""
        self.rotation = 0
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self._update_display()
    
    def _on_scroll(self, event):
        """滚轮缩放"""
        if event.num == 4 or event.delta > 0:
            self.scale *= 1.1
        elif event.num == 5 or event.delta < 0:
            self.scale /= 1.1
        
        self.scale = max(0.1, min(10.0, self.scale))
        self._update_display()
    
    def _on_resize(self, event):
        """窗口大小改变"""
        if event.widget == self.window:
            self._update_display()
    
    def _on_close(self):
        """窗口关闭"""
        self.window.withdraw()
