from pathlib import Path

USER_DATA_DIR = Path(__file__).parent.parent / "userdata"
GENERAL_CONFIG_DIR = USER_DATA_DIR / "general_config"

WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080

def get_general_config_dir():
    """获取通用配置目录（所有衣柜共享）"""
    GENERAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return GENERAL_CONFIG_DIR

def get_wardrobe_dir(wardrobe_name):
    """获取衣柜数据目录"""
    wardrobe_dir = USER_DATA_DIR / wardrobe_name
    wardrobe_dir.mkdir(parents=True, exist_ok=True)
    return wardrobe_dir

def get_config_dir(wardrobe_name):
    """获取配置文件目录"""
    config_dir = get_wardrobe_dir(wardrobe_name) / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def get_db_path(wardrobe_name):
    """获取数据库路径"""
    return get_wardrobe_dir(wardrobe_name) / f"{wardrobe_name}.db"

def get_image_dir(wardrobe_name):
    """获取图片存储目录"""
    image_dir = get_wardrobe_dir(wardrobe_name) / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    return image_dir

def get_ui_config_file(wardrobe_name):
    """获取UI配置文件路径"""
    return get_config_dir(wardrobe_name) / "ui_config.json"

def get_column_widths_file(wardrobe_name):
    """获取列宽配置文件路径"""
    return get_config_dir(wardrobe_name) / "column_widths.json"

def get_window_pos_file(wardrobe_name):
    """获取窗口位置配置文件路径"""
    return get_config_dir(wardrobe_name) / "window_pos.json"

def get_main_window_config_file():
    """获取主窗口配置文件路径（所有衣柜共享）"""
    return get_general_config_dir() / "main_window_config.json"

# 兼容旧版本（首次启动时使用）
IMAGE_DIR = USER_DATA_DIR / "images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)
