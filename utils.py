# -*- coding: utf-8 -*-
"""
工具类 (utils.py)
包含教务系统爬虫和 PDF 课表解析功能
"""

import requests
import hashlib
import re
from difflib import SequenceMatcher

class EAMSCrawler:
    """
    树维教务系统爬虫类
    支持 SHA1 盐值加密登录和 JSON 课表数据抓取
    """
    def __init__(self, base_url="https://eams.cupk.edu.cn"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
        })
        
    def login(self, username, password):
        try:
            # 1. 获取动态盐值 (Salt)
            salt_url = f"{self.base_url}/student/login-salt"
            salt_response = self.session.get(salt_url, timeout=5)
            salt = salt_response.text.strip()
            
            # 2. 模拟前端 JS 进行 SHA1 加密
            str_to_hash = f"{salt}-{password}"
            encrypted_password = hashlib.sha1(str_to_hash.encode('utf-8')).hexdigest()
            
            # 3. 发送登录请求 (使用 json 发送数据)
            login_url = f"{self.base_url}/student/login"
            login_data = {
                'username': username,
                'password': encrypted_password,
                'captchaToken': ''
            }
            
            response = self.session.post(login_url, json=login_data, allow_redirects=False, timeout=5)
            
            # 检查登录结果
            if response.status_code == 200 and '"result":true' in response.text.replace(' ', ''):
                return True
            elif response.status_code == 302 or 'student/home' in response.headers.get('Location', ''):
                return True
            else:
                raise Exception('用户名或密码错误，请检查学号和密码')
                
        except requests.exceptions.Timeout:
            raise Exception('连接教务系统超时，请检查网络')
        except Exception as e:
            if '用户名或密码错误' in str(e):
                raise e
            raise Exception(f'登录请求失败: {str(e)}')

    def get_schedule(self):
        try:
            # 1. 访问课表主页，尝试动态获取 semesterId 和 dataId
            page_url = f"{self.base_url}/student/for-std/course-table"
            page_res = self.session.get(page_url, timeout=5)
            
            # 兜底默认值 (基于你抓包到的真实参数)
            semester_id = "61" 
            data_id = "6822"
            
            # 正则提取动态 ID
            sem_match = re.search(r'semesterId[=:]\s*["\']?(\d+)["\']?', page_res.text)
            if sem_match:
                semester_id = sem_match.group(1)
                
            data_match = re.search(r'["\']?dataId["\']?\s*[:,=]\s*["\']?(\d+)["\']?', page_res.text)
            if data_match:
                data_id = data_match.group(1)
            
            # 2. 拼接真实数据接口并获取 JSON
            data_url = f"{self.base_url}/student/for-std/course-table/get-data?semesterId={semester_id}&dataId={data_id}&bizTypeId=2"
            response = self.session.get(data_url, timeout=5)
            schedule_data = response.json()
            
            # 3. 解析并返回
            return self._parse_json_schedule(schedule_data)

        except requests.exceptions.Timeout:
            raise Exception('获取课表超时，请检查网络')
        except Exception as e:
            raise Exception(f'获取课表数据失败: {str(e)}')

    def _parse_json_schedule(self, data):
        """解析返回的 JSON 课表数据"""
        courses = []
        lessons = data.get("lessons", [])
        day_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '日': 7, '天': 7}
        
        for lesson in lessons:
            course_name = lesson.get("course", {}).get("nameZh", "未知课程")
            
            # 兜底：获取老师姓名
            fallback_teacher = ""
            teachers = lesson.get("teacherAssignmentList", [])
            if teachers:
                fallback_teacher = teachers[0].get("person", {}).get("nameZh", "")
                
            schedule_text = lesson.get("scheduleText", {})
            if not schedule_text:
                continue
                
            dt_place_person_dict = schedule_text.get("dateTimePlacePersonText", {})
            if not dt_place_person_dict:
                continue
                
            dt_place_person = dt_place_person_dict.get("textZh", "") or dt_place_person_dict.get("text", "")
            if not dt_place_person:
                continue
                
            # 可能包含多个上课时间段，用分号分隔
            sessions = dt_place_person.split(";")
            for session_str in sessions:
                session_str = session_str.strip()
                if not session_str:
                    continue
                    
                # 关键正则解析 (例如："1~10周 星期一 4~5节 克拉玛依校区 C4楼413 郑顾平")
                match = re.search(r'(\d+)(?:~(\d+))?周\s+星期([一二三四五六日天])\s+(\d+)(?:~(\d+))?节\s+(.*)', session_str)
                if match:
                    start_week = int(match.group(1))
                    end_week = int(match.group(2)) if match.group(2) else start_week
                    day_of_week = day_map.get(match.group(3), 1)
                    period = int(match.group(4))
                    period_end = int(match.group(5)) if match.group(5) else period
                    
                    # 解析地点和老师 (以最后一个空格分割)
                    rest = match.group(6).strip()
                    parts = rest.rsplit(' ', 1)
                    
                    if len(parts) == 2:
                        location = parts[0]
                        teacher = parts[1]
                    else:
                        location = rest
                        teacher = fallback_teacher
                        
                    courses.append({
                        'course_name': course_name,
                        'teacher': teacher,
                        'location': location,
                        'start_week': start_week,
                        'end_week': end_week,
                        'day_of_week': day_of_week,
                        'period': period,
                        'period_end': period_end
                    })
        return courses


def import_schedule_from_kingosoft(username, password):
    """
    保持原有函数名不变，让 app.py 能够无缝调用
    """
    crawler = EAMSCrawler()
    crawler.login(username, password)
    return crawler.get_schedule()


# ========== PDF 课表解析 ==========

# 教师标准名单（可持续补充；不在名单内的姓名会原样保留）
PDF_TEACHER_STANDARDS = {
    '王晓伟', '郑顾平', '潘啸晨', '邱洪泽', '王建民', '王雪颖',
    '斯洪桥', '贾志洋', '田立年', '张宝', '张德远', '李中岩'
}

# 课程别名映射（键值均为规范化后的课程名）
COURSE_ALIAS_MAP = {
    '大学体育IV（必修项目）': '大学体育IV（乒乓球）',
    '大学体育IV(必修项目)': '大学体育IV（乒乓球）'
}


def _canonicalize_course_name(name):
    """规范化课程名并应用别名映射"""
    name = (name or '').strip()
    if not name:
        return ''

    name = re.sub(r'\s+', '', name)
    name = name.replace('(', '（').replace(')', '）')
    return COURSE_ALIAS_MAP.get(name, name)


def _canonicalize_location(location):
    """规范化地点文本（不做强制字典校验）"""
    location = (location or '').strip()
    if not location:
        return ''

    location = re.sub(r'\s+', '', location)
    location = location.replace('教学楼', '楼')
    location = location.replace('克拉玛依校区校区', '克拉玛依校区')
    location = location.replace('乒乓馆', '乒乓球馆')
    return location


def _canonicalize_teacher_name(teacher):
    """按教师标准名单规范化姓名；无法确认则保持原样"""
    teacher = (teacher or '').strip()
    if not teacher:
        return ''

    teacher = re.sub(r'\s+', '', teacher)
    teacher = re.sub(r'^[^\u4e00-\u9fff]+', '', teacher)
    teacher = re.sub(r'[^\u4e00-\u9fff]+$', '', teacher)

    if teacher in PDF_TEACHER_STANDARDS:
        return teacher

    # 常见噪声：前后粘连字符，优先做包含匹配
    for std in PDF_TEACHER_STANDARDS:
        if std in teacher or teacher in std:
            return std

    # 轻量兜底：高度相似且首字一致才替换，避免误伤其他课表
    best = ''
    best_ratio = 0.0
    for std in PDF_TEACHER_STANDARDS:
        ratio = SequenceMatcher(None, teacher, std).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best = std

    if best and best_ratio >= 0.86 and teacher[:1] == best[:1]:
        return best

    return teacher


def _canonicalize_parsed_course(course):
    """统一规范解析后的课程字段"""
    return {
        'course_name': _canonicalize_course_name(course.get('course_name', '')),
        'location': _canonicalize_location(course.get('location', '')),
        'teacher': _canonicalize_teacher_name(course.get('teacher', '')),
        'start_week': course.get('start_week'),
        'end_week': course.get('end_week'),
        'period': course.get('period'),
        'period_end': course.get('period_end'),
        'day_of_week': course.get('day_of_week')
    }

def _extract_chinese(text):
    """从交错文本中提取中文字符和中文标点"""
    return ''.join(re.findall(r'[\u4e00-\u9fff\uff08\uff09（）]', text))


def _has_interleaved_pattern(line):
    """判断一行文本是否为课程名与课程代码交错排列的模式"""
    line = line.strip()
    if len(line) < 4:
        return False
    transitions = 0
    prev_is_chinese = None
    for ch in line:
        is_chinese = '\u4e00' <= ch <= '\u9fff' or ch in '（）\uff08\uff09'
        is_alnum = ch.isalnum() and not is_chinese
        if is_alnum or is_chinese:
            if prev_is_chinese is not None and is_chinese != prev_is_chinese:
                transitions += 1
            prev_is_chinese = is_chinese
    return transitions >= 4


def _extract_course_name_from_text(text):
    """从包含交错课程名+课程代码的文本块中提取课程名"""
    lines = text.strip().split('\n')
    name_parts = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 跳过班级信息行
        if any(line.startswith(kw) for kw in [';', '24-', '23-', '22-']):
            continue
        if '班' in line and ('工程' in line or '技术' in line or '24-' in line):
            continue
        if line in ('周', '节', '楼', '区', '机房', '校区', '克拉玛依'):
            continue

        # 跳过包含学号的带括号行，如 (2021592210) 或混合ID行
        cleaned = line.replace(' ', '')
        if re.match(r'^\([\d\u4e00-\u9fff\s]+\)', cleaned):
            continue

        # 跳过包含 校区/楼 的位置碎片
        if ('校' in line and '区' in line) or ('校区' in line):
            continue

        # 跳过纯位置碎片
        if re.match(r'^(C\d|I{1,3}|区|楼|\d{3}$)', line):
            continue

        # 识别交错模式（课程名+课程代码混排）
        if _has_interleaved_pattern(line):
            chinese = _extract_chinese(line)
            if len(chinese) >= 2:
                if not any(kw in chinese for kw in ['校区', '机房', '克拉玛依']):
                    name_parts.append(chinese)
        elif re.match(r'^[A-Za-z]+$', line):
            # 纯英文单词（如 "Web"）
            name_parts.append(line)
        elif re.match(r'^[\u4e00-\u9fff\uff08\uff09（）]+$', line) and len(line) >= 4:
            # 纯中文行，足够长，可能是课程名片段
            if not any(kw in line for kw in ['克拉玛依', '校区', '机房', '社会实践']):
                name_parts.append(line)
        elif re.search(r'[\u4e00-\u9fff]{2,}', line):
            # 混合行（中英文混排），如 "Web程序设计"、"大学体育IV（必修项目）"
            # 过滤教师+学号行，避免把姓名误识别为课程名
            compact_line = line.replace(' ', '')
            if re.search(r'\(\d{6,}\)', compact_line):
                continue

            mixed = ''.join(re.findall(r'[A-Za-z]+|[\u4e00-\u9fff\uff08\uff09（）]+', line))
            chinese_count = len(re.findall(r'[\u4e00-\u9fff]', mixed))

            if chinese_count >= 2 and not any(kw in mixed for kw in ['克拉玛依', '校区', '机房', '周节', '楼区']):
                name_parts.append(mixed)

    course_name = ''.join(name_parts)

    # 清理
    course_name = re.sub(r'^(IV|III|II|I)', '', course_name)
    course_name = re.sub(r'[周节楼区]+$', '', course_name)
    course_name = re.sub(r'机房$', '', course_name)

    return course_name.strip()


def _extract_location(text):
    """从文本中提取上课地点"""
    location = ''
    compact = re.sub(r'\s+', '', text[:400])

    # 优先匹配最完整地点（支持双地点与机房后缀）
    # 例如: C4楼413/C8楼II区304机房
    full_dual = re.search(
        r'(C\d+楼(?:I{1,3}V?|IV|V)?区?\d{3}(?:机房)?(?:/C\d+楼(?:I{1,3}V?|IV|V)?区?\d{3}(?:机房)?)+)',
        compact
    )
    if full_dual:
        location = full_dual.group(1)

    # 例如: C4楼411/421 或 C4楼II区409/418
    if not location:
        same_building_dual = re.search(
            r'(C\d+楼(?:I{1,3}V?|IV|V)?区?\d{3}(?:/\d{3})+(?:机房)?)',
            compact
        )
        if same_building_dual:
            location = same_building_dual.group(1)

    # 例如: C6楼II区505机房 / C4楼213
    if not location:
        single_full = re.search(r'(C\d+楼(?:I{1,3}V?|IV|V)?区?\d{3}(?:机房)?)', compact)
        if single_full:
            location = single_full.group(1)

    # 如果命中校区关键词，尽量保留前缀信息
    if location and '克拉玛依校区' in compact and not location.startswith('克拉玛依校区'):
        location = '克拉玛依校区' + location

    # 先尝试匹配完整的 "C数字 房间号" 在同一行
    if not location:
        loc_match = re.search(
            r'(C\d+)\s*(I{1,3}V?|IV|V)?\s*(区)?[\s\n]*?(\d{3})?',
            text[:300]
        )
        if loc_match:
            loc_parts = [loc_match.group(1) + '楼']
            if loc_match.group(2):
                loc_parts.append(loc_match.group(2) + '区')
            if loc_match.group(4):
                loc_parts.append(loc_match.group(4))
            location = ''.join(loc_parts)

    # 如果只匹配到楼号没有房间号，在"周 节 楼"标签行之后搜索三位数房间号
    if location and not re.search(r'\d{3}', location):
        # 搜索 "周 节 楼" 之后的数字
        after_label = re.search(r'周\s*节\s*楼.*?\n\s*(\d{3})', text[:300], re.DOTALL)
        if after_label:
            location += after_label.group(1)
        else:
            # 单独占一行的三位数
            room_match = re.search(r'(?:^|\n)\s*(\d{3})\s*(?:\n|$)', text[:300])
            if room_match:
                location += room_match.group(1)

    # 处理 "I 303\n区" 这类 I/II区和房间号分离在"周 节 楼"之后的情况
    if location and '区' not in location:
        # 检查 "周 节 楼" 后的 "I 303\n区" 模式
        area_match = re.search(r'周\s*节\s*楼.*?\n\s*(I{1,3}V?|IV|V)\s+(\d{3})', text[:300], re.DOTALL)
        if area_match:
            # 重建地点：楼号 + 区域 + 房间号
            base = re.match(r'(C\d+楼)', location)
            if base:
                location = base.group(1) + area_match.group(1) + '区' + area_match.group(2)

    if not location:
        special = re.search(r'(\d?\s*形体馆|体育馆|乒乓球馆|[\u4e00-\u9fff]{1,4}球馆|操场|实验室)', text[:200])
        if special:
            location = special.group(1).replace(' ', '')

    # 检测机房
    if location and '机房' not in location and '机房' in text[:150]:
        location += '机房'

    return location


def _extract_teacher(text):
    """从文本中提取教师姓名"""
    skip_words = {'机房', '校区', '克拉玛依', '社会实践', '形体馆', '体育馆',
                  '周节', '周节楼', '楼区'}
    skip_contains = ['工程', '班', '科学', '储运', '勘查', '技术', '思想', '社会',
                     '克拉', '玛依', '校区']

    def normalize_name(name):
        # 去掉地点词残留（如“房潘啸晨”）
        name = re.sub(r'^(机房|实验室|楼区|校区|教学楼)+', '', name)
        name = re.sub(r'^[房区楼馆场校]+', '', name)
        return name

    def is_valid_name(name):
        name = normalize_name(name)
        if name in skip_words:
            return False
        if any(kw in name for kw in skip_contains):
            return False
        return 2 <= len(name) <= 4

    compact = re.sub(r'\s+', '', text[:400])

    # 优先: 教师名通常紧邻工号/学号括号，选最后一个最可靠
    id_name_candidates = re.findall(r'([\u4e00-\u9fff]{2,4})\(\d{8,}\)', compact)
    for candidate in reversed(id_name_candidates):
        candidate = normalize_name(candidate)
        if is_valid_name(candidate):
            return candidate

    # 方法0 (优先): 拆分在两行的教师名，如 "楼 赵\n联文" → "赵联文"
    # 中间可能有学号行，如 "楼 赵\n(2024582028)\n联文"
    split_match = re.search(r'[楼区]\s*([\u4e00-\u9fff])\s*\n(?:\s*\([\d\s]+\)\s*\n)?\s*([\u4e00-\u9fff]{1,3})\s*(?:\n|$)', text[:300])
    if split_match:
        combined = normalize_name(split_match.group(1) + split_match.group(2))
        if len(combined) >= 2 and is_valid_name(combined):
            return combined

    # 方法1: 独占一行的中文名
    candidates = re.findall(r'(?:^|\n)\s*([\u4e00-\u9fff]{2,4})\s*(?:\n|$)', text[:300])
    for candidate in candidates:
        candidate = normalize_name(candidate)
        if is_valid_name(candidate):
            return candidate

    # 方法2: "机房 教师名" 或 "机房  教师名" 模式
    jf_match = re.search(r'机房\s+([\u4e00-\u9fff]{2,4})', text[:300])
    if jf_match:
        candidate = normalize_name(jf_match.group(1))
        if is_valid_name(candidate):
            return candidate

    # 方法3: ")教师名" 模式
    id_name_match = re.search(r'\)\s*([\u4e00-\u9fff]{2,4})\s*(?:\n|$)', text[:300])
    if id_name_match:
        candidate = normalize_name(id_name_match.group(1))
        if is_valid_name(candidate):
            return candidate

    # 方法4: "区 教师名" 模式
    qu_match = re.search(r'区\s+([\u4e00-\u9fff]{2,4})\s*(?:\n|$)', text[:300])
    if qu_match:
        candidate = normalize_name(qu_match.group(1))
        if is_valid_name(candidate):
            return candidate

    # 方法5: 从学号+教师名混排中提取，如 "(202机05房92 2 李12张) 美智"
    # 提取括号内和括号后的所有中文字符
    paren_match = re.search(r'\([\d\s\u4e00-\u9fff]+\)\s*([\u4e00-\u9fff]*)', text[:300])
    if paren_match:
        inside = re.findall(r'[\u4e00-\u9fff]', paren_match.group(0))
        inside_str = normalize_name(''.join(inside))
        # 移除已知非人名词汇
        inside_str = inside_str.replace('机房', '')
        if len(inside_str) >= 2 and is_valid_name(inside_str):
            return inside_str

    return ''


def _parse_cell(cell_text):
    """解析课表表格中的单个单元格，提取所有课程信息"""
    results = []

    # 兼容变体: (1~12周) (1-2节)、(1~12��) (1-2��) 等
    wp_pattern = r'\((\d+)\s*~\s*(\d+)[^)]*\)\s*\((\d+)\s*-\s*(\d+)[^)]*\)'
    matches = list(re.finditer(wp_pattern, cell_text))

    if not matches:
        return results

    prev_course_name = ''
    prev_teacher = ''

    for i, match in enumerate(matches):
        start_week = int(match.group(1))
        end_week = int(match.group(2))
        period_start = int(match.group(3))
        period_end = int(match.group(4))

        # 获取当前匹配之前的文本（可能包含课程名）
        if i == 0:
            pre_text = cell_text[:match.start()]
        else:
            pre_text = cell_text[matches[i - 1].end():match.start()]

        # 获取当前匹配之后的文本（可能包含地点和教师）
        if i + 1 < len(matches):
            post_text = cell_text[match.end():matches[i + 1].start()]
        else:
            post_text = cell_text[match.end():]

        # 提取课程名
        course_name = _extract_course_name_from_text(pre_text)
        if not course_name or len(course_name) < 2:
            course_name = prev_course_name

        # 提取地点 — 使用 post_text（包含完整多行），优先用完整文本
        location = _extract_location(post_text)

        # 提取教师
        teacher = _extract_teacher(post_text)
        if not teacher and course_name == prev_course_name:
            teacher = prev_teacher

        prev_course_name = course_name
        prev_teacher = teacher if teacher else prev_teacher

        if course_name and len(course_name) >= 2:
            results.append({
                'course_name': course_name,
                'location': location,
                'teacher': teacher,
                'start_week': start_week,
                'end_week': end_week,
                'period': period_start,
                'period_end': period_end
            })

    return results


def parse_schedule_pdf(pdf_path):
    """
    解析课表 PDF 文件，返回课程列表

    Args:
        pdf_path: PDF 文件路径

    Returns:
        list: 课程字典列表，每个字典包含：
            course_name, location, teacher, day_of_week,
            period, period_end, start_week, end_week
    """
    import pdfplumber

    courses = []

    with pdfplumber.open(pdf_path) as pdf:
        all_rows = []
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                all_rows.extend(table)

    for row in all_rows:
        if len(row) < 9:
            continue
        for col_idx in range(2, 9):
            cell = row[col_idx]
            if not cell or not cell.strip():
                continue
            day_of_week = col_idx - 1  # 1=周一, ..., 7=周日
            cell_courses = _parse_cell(cell)
            for c in cell_courses:
                c['day_of_week'] = day_of_week
                courses.append(_canonicalize_parsed_course(c))

    return courses