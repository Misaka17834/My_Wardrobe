# 导入衣柜主窗口类
from gui.main_window import WardrobeMainWindow

# 主程序入口：只有直接运行该文件时才执行
if __name__ == "__main__":
    # 创建主窗口对象
    app = WardrobeMainWindow()
    # 运行主窗口（启动GUI事件循环）
    app.run()

