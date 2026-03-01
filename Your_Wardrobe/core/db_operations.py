import sqlite3
from pathlib import Path
import json
from config.config import get_db_path, get_image_dir, USER_DATA_DIR

class WardrobeDB:
    def __init__(self, wardrobe_name=None):
        self.wardrobe_name = wardrobe_name
        self.conn = None
        self.cursor = None
        if wardrobe_name:
            self._connect_wardrobe(wardrobe_name)
    
    def _connect_wardrobe(self, wardrobe_name):
        """连接到指定衣柜的数据库"""
        self.wardrobe_name = wardrobe_name
        db_path = get_db_path(wardrobe_name)
        self.conn = sqlite3.connect(str(db_path))
        self.cursor = self.conn.cursor()
        self._init_tables()
    
    def _init_tables(self):
        """初始化表结构"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS clothes_type (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_name TEXT NOT NULL,
            is_default INTEGER DEFAULT 0,
            UNIQUE(type_name)
        )
        ''')
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_params (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            param_name TEXT NOT NULL UNIQUE
        )
        ''')
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS clothes_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clothes_name TEXT NOT NULL,
            clothes_type TEXT NOT NULL,
            size TEXT,
            chest_circumference REAL,
            platform TEXT,
            price REAL,
            image_path TEXT,
            custom_params TEXT DEFAULT '{}'
        )
        ''')
        
        # 检查是否有默认类型
        self.cursor.execute('SELECT COUNT(*) FROM clothes_type WHERE is_default=1')
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute(
                'INSERT INTO clothes_type (type_name, is_default) VALUES (?, 1)',
                ("未分组",)
            )
        
        self.conn.commit()

    def add_clothes_type(self, type_name):
        type_name_stripped = type_name.strip()
        if type_name_stripped in ["默认", "未分组", "全部"]:
            return False
        try:
            self.cursor.execute(
                'INSERT INTO clothes_type (type_name, is_default) VALUES (?, 0)',
                (type_name_stripped,)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_clothes_type(self, type_name):
        if type_name in ["全部", "未分组"]:
            return False
        self.cursor.execute(
            'UPDATE clothes_info SET clothes_type="未分组" WHERE clothes_type=?',
            (type_name,)
        )
        self.cursor.execute(
            'DELETE FROM clothes_type WHERE type_name=?',
            (type_name,)
        )
        self.conn.commit()
        return True

    def rename_clothes_type(self, old_name, new_name):
        """重命名类型"""
        if old_name in ["全部", "未分组"] or new_name in ["全部", "未分组"]:
            return False
        try:
            # 更新衣物表中的类型
            self.cursor.execute(
                'UPDATE clothes_info SET clothes_type=? WHERE clothes_type=?',
                (new_name, old_name)
            )
            # 更新类型表
            self.cursor.execute(
                'UPDATE clothes_type SET type_name=? WHERE type_name=?',
                (new_name, old_name)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_clothes_types(self):
        self.cursor.execute(
            'SELECT type_name FROM clothes_type ORDER BY is_default DESC, type_name'
        )
        return [row[0] for row in self.cursor.fetchall()]

    def add_custom_param(self, param_name):
        try:
            self.cursor.execute(
                'INSERT INTO custom_params (param_name) VALUES (?)',
                (param_name,)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def rename_custom_param(self, old_name, new_name):
        """重命名自定义参数"""
        try:
            self.cursor.execute(
                'UPDATE custom_params SET param_name=? WHERE param_name=?',
                (new_name, old_name)
            )
            # 更新所有衣物中的该参数名
            self.cursor.execute('SELECT id, custom_params FROM clothes_info')
            for row in self.cursor.fetchall():
                clothes_id = row[0]
                params = json.loads(row[1]) if row[1] else {}
                if old_name in params:
                    params[new_name] = params.pop(old_name)
                    self.cursor.execute(
                        'UPDATE clothes_info SET custom_params=? WHERE id=?',
                        (json.dumps(params, ensure_ascii=False), clothes_id)
                    )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_custom_param(self, param_name):
        """删除自定义参数"""
        self.cursor.execute(
            'DELETE FROM custom_params WHERE param_name=?',
            (param_name,)
        )
        # 从所有衣物中移除该参数
        self.cursor.execute('SELECT id, custom_params FROM clothes_info')
        for row in self.cursor.fetchall():
            clothes_id = row[0]
            params = json.loads(row[1]) if row[1] else {}
            if param_name in params:
                del params[param_name]
                self.cursor.execute(
                    'UPDATE clothes_info SET custom_params=? WHERE id=?',
                    (json.dumps(params, ensure_ascii=False), clothes_id)
                )
        self.conn.commit()
        return True

    def get_custom_params(self):
        self.cursor.execute('SELECT param_name FROM custom_params')
        return [row[0] for row in self.cursor.fetchall()]

    def add_clothes(self, clothes_data):
        custom_params = clothes_data.pop('custom_params', {})
        clothes_data['custom_params'] = json.dumps(custom_params, ensure_ascii=False)
        if not clothes_data.get('clothes_type'):
            clothes_data['clothes_type'] = "未分组"
        keys = ', '.join(clothes_data.keys())
        placeholders = ', '.join(['?'] * len(clothes_data))
        values = tuple(clothes_data.values())
        self.cursor.execute(
            f'INSERT INTO clothes_info ({keys}) VALUES ({placeholders})',
            values
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def update_clothes(self, clothes_id, clothes_data):
        custom_params = clothes_data.pop('custom_params', {})
        clothes_data['custom_params'] = json.dumps(custom_params, ensure_ascii=False)
        update_str = ', '.join([f"{k}=?" for k in clothes_data.keys()])
        values = tuple(clothes_data.values()) + (clothes_id,)
        self.cursor.execute(
            f'UPDATE clothes_info SET {update_str} WHERE id=?',
            values
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_clothes(self, clothes_type=None, sort_by="id", ascending=True):
        """获取衣物列表，支持自定义参数排序"""
        base_fields = ["id", "clothes_name", "clothes_type", "size", "chest_circumference", "platform", "price", "image_path"]
        
        def parse_results(cursor):
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                item = dict(zip(columns, row))
                try:
                    raw_val = item.get('custom_params', '{}')
                    item['custom_params'] = json.loads(raw_val) if raw_val else {}
                except (json.JSONDecodeError, Exception):
                    item['custom_params'] = {}
                results.append(item)
            return results
        
        # 基础字段用SQL排序
        if sort_by in base_fields:
            order = "ASC" if ascending else "DESC"
            if clothes_type:
                sql = f'SELECT * FROM clothes_info WHERE clothes_type=? ORDER BY {sort_by} {order}'
                self.cursor.execute(sql, (clothes_type,))
            else:
                sql = f'SELECT * FROM clothes_info ORDER BY {sort_by} {order}'
                self.cursor.execute(sql)
            return parse_results(self.cursor)
        else:
            # 自定义参数在Python层面排序（文本排序）
            if clothes_type:
                self.cursor.execute('SELECT * FROM clothes_info WHERE clothes_type=?', (clothes_type,))
            else:
                self.cursor.execute('SELECT * FROM clothes_info')
            results = parse_results(self.cursor)
            
            def get_sort_key(item):
                val = item.get('custom_params', {}).get(sort_by, '')
                return str(val) if val is not None else ''
            
            results.sort(key=get_sort_key, reverse=not ascending)
            return results

    def get_clothes_by_id(self, clothes_id):
        self.cursor.execute('SELECT * FROM clothes_info WHERE id=?', (clothes_id,))
        columns = [desc[0] for desc in self.cursor.description]
        row = self.cursor.fetchone()
        if not row:
            return None
        item = dict(zip(columns, row))
        try:
            if 'custom_params' not in item:
                item['custom_params'] = {}
            else:
                raw_val = item['custom_params']
                if raw_val is None or raw_val == "":
                    item['custom_params'] = {}
                else:
                    item['custom_params'] = json.loads(raw_val)
        except (json.JSONDecodeError, Exception):
            item['custom_params'] = {}
        return item

    def delete_clothes(self, clothes_id):
        self.cursor.execute('DELETE FROM clothes_info WHERE id=?', (clothes_id,))
        self.conn.commit()

    def fix_old_records(self):
        self.cursor.execute(
            'UPDATE clothes_info SET custom_params=? WHERE custom_params IS NULL OR custom_params=""',
            ('{}',)
        )
        self.cursor.execute(
            'UPDATE clothes_info SET clothes_type="未分组" WHERE clothes_type IS NULL OR clothes_type=""'
        )
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()


def get_all_wardrobes():
    """获取所有衣柜名称"""
    wardrobes = []
    if USER_DATA_DIR.exists():
        for item in USER_DATA_DIR.iterdir():
            if item.is_dir() and (item / f"{item.name}.db").exists():
                wardrobes.append(item.name)
    return wardrobes


def create_wardrobe(wardrobe_name):
    """创建新衣柜"""
    db_path = get_db_path(wardrobe_name)
    if db_path.exists():
        return False
    db = WardrobeDB(wardrobe_name)
    db.close()
    return True


def delete_wardrobe(wardrobe_name):
    """删除衣柜"""
    import shutil
    wardrobe_dir = USER_DATA_DIR / wardrobe_name
    if not wardrobe_dir.exists():
        return False
    shutil.rmtree(wardrobe_dir)
    return True
