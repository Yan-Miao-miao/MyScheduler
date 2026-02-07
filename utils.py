# -*- coding: utf-8 -*-
"""
强智教务系统爬虫工具类 (utils.py)
用于自动登录教务系统并获取课表数据
"""

import requests
import base64
from bs4 import BeautifulSoup
import re


class KingosoftCrawler:
    """
    强智教务系统爬虫类
    支持登录和课表数据抓取
    """
    
    def __init__(self, base_url="http://jw.cupk.edu.cn"):
        """
        初始化爬虫
        
        参数:
            base_url: 教务系统的基础 URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        # 设置请求头，模拟浏览器
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
    
    @staticmethod
    def encode_credentials(username, password):
        """
        生成强智系统的加密登录字符串
        
        强智系统的加密逻辑：
        encoded = base64(username) + "%%%" + base64(password)
        
        参数:
            username: 学号
            password: 密码
        
        返回:
            加密后的字符串
        """
        # 将用户名和密码分别进行 Base64 编码
        username_encoded = base64.b64encode(username.encode()).decode()
        password_encoded = base64.b64encode(password.encode()).decode()
        
        # 用 %%% 连接
        encoded_str = f"{username_encoded}%%%{password_encoded}"
        
        return encoded_str
    
    def login(self, username, password):
        """
        登录强智教务系统
        
        参数:
            username: 学号
            password: 密码
        
        返回:
            True: 登录成功
            False: 登录失败
        
        异常:
            Exception: 登录失败时抛出异常，包含错误信息
        """
        # 生成加密字符串
        encoded = self.encode_credentials(username, password)
        
        # 登录 URL
        login_url = f"{self.base_url}/jsxsd/xk/LoginToXk"
        
        # 构造 POST 数据
        payload = {
            'encoded': encoded
        }
        
        try:
            # 发送登录请求
            response = self.session.post(login_url, data=payload, timeout=10)
            response.encoding = 'utf-8'
            
            # 检查是否登录成功
            # 如果返回的页面包含错误信息，说明登录失败
            if '用户名或密码错误' in response.text or '登录失败' in response.text:
                raise Exception('用户名或密码错误，请检查学号和密码')
            
            # 如果页面跳转到登录页面，也说明登录失败
            if 'login' in response.url.lower() or 'xk/LoginToXk' in response.url:
                raise Exception('登录失败，请检查学号和密码')
            
            # 登录成功
            return True
            
        except requests.exceptions.Timeout:
            raise Exception('连接教务系统超时，请检查网络连接')
        except requests.exceptions.RequestException as e:
            raise Exception(f'网络请求失败: {str(e)}')
    
    def get_schedule(self):
        """
        获取课表数据
        
        返回:
            课程列表，每个课程是一个字典：
            {
                'course_name': '课程名称',
                'teacher': '教师',
                'location': '地点',
                'day_of_week': 1-7 (周一到周日),
                'period': 第几节课
            }
        
        异常:
            Exception: 获取课表失败时抛出异常
        """
        # 课表页面 URL
        schedule_url = f"{self.base_url}/jsxsd/xskb/xskb_list.do"
        
        try:
            # 获取课表页面
            response = self.session.get(schedule_url, timeout=10)
            response.encoding = 'utf-8'
            
            # 检查是否需要重新登录
            if 'login' in response.url.lower():
                raise Exception('登录状态已失效，请重新登录')
            
            # 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找课表表格
            # 强智系统的课表通常在 id="kbtable" 的表格中
            table = soup.find('table', {'id': 'kbtable'}) or soup.find('table', class_='kbcontent')
            
            if not table:
                raise Exception('未找到课表数据，请检查课表页面 URL 是否正确')
            
            # 解析课表
            courses = self._parse_schedule_table(table)
            
            return courses
            
        except requests.exceptions.Timeout:
            raise Exception('获取课表超时，请检查网络连接')
        except requests.exceptions.RequestException as e:
            raise Exception(f'获取课表失败: {str(e)}')
    
    def _parse_schedule_table(self, table):
        """
        解析课表 HTML 表格（矩阵占位法，正确处理 rowspan 连堂课）
        
        教务系统表格结构：
        - 行标签如 0102, 030405, 0607, 0809, 1011 代表节次分组
        - 每个单元格可能包含多门课（用 --- 分隔）
        - 课程文本格式：课程名 / 老师 / 周次(周)[节次] / 教室 / 课程代码
        
        参数:
            table: BeautifulSoup 的 table 对象
        
        返回:
            课程列表
        """
        courses = []
        
        # 获取所有行（跳过表头）
        rows = table.find_all('tr')[1:]  # 第一行通常是表头
        
        if not rows:
            return courses
        
        num_rows = len(rows)
        num_cols = 8  # 第0列是时间列，第1-7列是周一到周日
        
        # ========== 步骤1：初始化占位矩阵 ==========
        filled_matrix = [[None for _ in range(num_cols)] for _ in range(num_rows)]
        
        # ========== 步骤2：遍历所有行，填充矩阵 ==========
        for row_idx, row in enumerate(rows):
            # 同时查找 td 和 th（教务系统的"节次"列用的是 <th>，课程列用 <td>）
            cells = row.find_all(['td', 'th'])
            cell_pointer = 0
            
            for col_idx in range(num_cols):
                if cell_pointer >= len(cells):
                    break
                
                if filled_matrix[row_idx][col_idx] is not None:
                    continue
                
                cell = cells[cell_pointer]
                cell_pointer += 1
                
                rowspan = int(cell.get('rowspan', 1))
                colspan = int(cell.get('colspan', 1))
                
                for dr in range(rowspan):
                    for dc in range(colspan):
                        r = row_idx + dr
                        c = col_idx + dc
                        if r < num_rows and c < num_cols:
                            filled_matrix[r][c] = cell
        
        # ========== 步骤3：从矩阵中提取课程数据 ==========
        processed_cells = set()
        
        for row_idx in range(num_rows):
            for col_idx in range(1, num_cols):  # 跳过第0列（时间列）
                cell = filled_matrix[row_idx][col_idx]
                
                if cell is None:
                    continue
                
                cell_id = id(cell)
                if cell_id in processed_cells:
                    continue
                processed_cells.add(cell_id)
                
                # 获取单元格的完整 HTML 内容用于分割多门课
                day_of_week = col_idx  # 1-7 代表周一到周日
                
                # 检查 kbcontent div
                course_divs = cell.find_all('div', class_='kbcontent')
                if not course_divs:
                    course_divs = cell.find_all('div')
                
                for course_div in course_divs:
                    # 获取 div 的内部 HTML，用于按 --- 分割多门课
                    inner_html = course_div.decode_contents()
                    
                    # 按 "-----" 分割同一格内的多门课（至少3个连续短横线）
                    course_blocks = re.split(r'-{3,}', inner_html)
                    
                    for block in course_blocks:
                        block_text = BeautifulSoup(block, 'html.parser').get_text('\n', strip=True)
                        
                        if not block_text or not block_text.strip():
                            continue
                        
                        course_info = self._parse_course_info(block_text)
                        
                        if course_info:
                            course_info['day_of_week'] = day_of_week
                            courses.append(course_info)
        
        return courses
    
    def _parse_course_info(self, course_text):
        """
        解析单个课程的文本信息
        
        强智教务系统的课程文本格式（从截图分析）：
            线性代数
            梁景伟
            2-13(周)[01-02节]
            C5楼区401
            100616M003-18
        
        需要提取：课程名、教师、教室、起始周、结束周、起始节、结束节
        
        参数:
            course_text: 课程文本
        
        返回:
            课程信息字典，或 None
        """
        # 按换行符分割，去除空行
        lines = [line.strip() for line in course_text.split('\n') if line.strip()]
        
        if len(lines) < 1:
            return None
        
        course_name = ''
        teacher = ''
        location = ''
        start_week = 1
        end_week = 20
        period_start = 1
        period_end = 2
        
        # 正则：匹配周次和节次信息，如 "2-13(周)[01-02节]" 或 "1-16(周)[03-04节]"
        week_period_pattern = re.compile(
            r'(\d+)-(\d+)\s*\(周\)\s*\[(\d+)-(\d+)节?\]'
        )
        # 也可能是单周格式：如 "1(周)[01-02节]"
        single_week_pattern = re.compile(
            r'(\d+)\s*\(周\)\s*\[(\d+)-(\d+)节?\]'
        )
        # 课程代码格式：以数字开头，包含字母和数字，如 "100616M003-18"
        code_pattern = re.compile(r'^\d{4,}[A-Za-z]\w*')
        
        found_week_info = False
        
        for i, line in enumerate(lines):
            # 检查是否是周次+节次信息行
            match = week_period_pattern.search(line)
            if match:
                start_week = int(match.group(1))
                end_week = int(match.group(2))
                period_start = int(match.group(3))
                period_end = int(match.group(4))
                found_week_info = True
                continue
            
            # 检查单周格式
            match_single = single_week_pattern.search(line)
            if match_single:
                start_week = int(match_single.group(1))
                end_week = int(match_single.group(1))
                period_start = int(match_single.group(2))
                period_end = int(match_single.group(3))
                found_week_info = True
                continue
            
            # 跳过课程代码行（数字+字母开头的编号）
            if code_pattern.match(line):
                continue
            
            # 跳过"健美操"之类的子类别（如果已经有课程名了）
            # 第一行通常是课程名
            if not course_name:
                course_name = line
            elif not teacher:
                teacher = line
            elif not location:
                # 地点通常包含楼/馆/房/区/室等关键字
                if any(kw in line for kw in ['楼', '馆', '房', '区', '室', '场', '实验']):
                    location = line
                else:
                    # 可能是附加信息（如"健美操"），跳过
                    pass
        
        if not course_name:
            return None
        
        # 如果没有找到周次信息，使用默认值
        if not found_week_info:
            start_week = 1
            end_week = 20
        
        return {
            'course_name': course_name,
            'teacher': teacher,
            'location': location,
            'start_week': start_week,
            'end_week': end_week,
            'period': period_start,
            'period_end': period_end
        }


def import_schedule_from_kingosoft(username, password):
    """
    从强智教务系统导入课表的便捷函数
    
    参数:
        username: 学号
        password: 密码
    
    返回:
        课程列表
    
    异常:
        Exception: 登录或获取课表失败时抛出异常
    """
    crawler = KingosoftCrawler()
    
    # 登录
    crawler.login(username, password)
    
    # 获取课表
    courses = crawler.get_schedule()
    
    return courses
