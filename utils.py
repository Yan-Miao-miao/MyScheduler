# -*- coding: utf-8 -*-
"""
树维教务系统爬虫工具类 (utils.py)
用于自动登录新教务系统并获取课表JSON数据
"""

import requests
import hashlib
import re

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