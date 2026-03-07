# -*- coding: utf-8 -*-
"""
完美课表方案 - 基于李健豪.pdf与大二下课表.pdf对比生成
可直接运行导入到 MyScheduler 数据库
"""
import os, sys

# ===================================================================
#  推荐方案: 基于大二下课表.pdf (24-1/2班) 
#  理由：
#    1. 每日负载更均衡 (最大8节 vs A方案周三10节)
#    2. 周三少2节课，不至于从早到晚连轴转  
#    3. 概率论只有1位教师(李中岩)，教学连贯性更好
#    4. 额外包含美术鉴赏通识课(充实人文素养)
#    5. 数据可视化安排在周四晚而非周三晚，避免周三过度疲劳
# ===================================================================

RECOMMENDED_COURSES = [
    # ===== 专业核心课 =====
    # Web程序设计 - 王晓伟 (1-12周)
    {"course_name": "Web程序设计",         "day_of_week": 1, "period": 1, "period_end": 2,  "start_week": 1,  "end_week": 12, "location": "C4楼420机房", "teacher": "王晓伟"},
    {"course_name": "Web程序设计",         "day_of_week": 4, "period": 4, "period_end": 5,  "start_week": 1,  "end_week": 12, "location": "C4楼420机房", "teacher": "王晓伟"},

    # 操作系统原理 - 郑顾平 (1-12周)
    {"course_name": "操作系统原理",         "day_of_week": 4, "period": 1, "period_end": 2,  "start_week": 1,  "end_week": 10, "location": "C4楼413",    "teacher": "郑顾平"},
    {"course_name": "操作系统原理",         "day_of_week": 4, "period": 1, "period_end": 2,  "start_week": 11, "end_week": 12, "location": "C8楼II区304机房", "teacher": "郑顾平"},
    {"course_name": "操作系统原理",         "day_of_week": 1, "period": 4, "period_end": 5,  "start_week": 1,  "end_week": 10, "location": "C4楼413",    "teacher": "郑顾平"},
    {"course_name": "操作系统原理",         "day_of_week": 1, "period": 4, "period_end": 5,  "start_week": 11, "end_week": 12, "location": "C8楼II区304机房", "teacher": "郑顾平"},

    # 算法设计与分析（双语）- 潘啸晨 (1-12周)
    {"course_name": "算法设计与分析（双语）", "day_of_week": 1, "period": 6, "period_end": 7, "start_week": 1,  "end_week": 8,  "location": "C4楼409",    "teacher": "潘啸晨"},
    {"course_name": "算法设计与分析（双语）", "day_of_week": 1, "period": 6, "period_end": 7, "start_week": 9,  "end_week": 12, "location": "C4楼418机房", "teacher": "潘啸晨"},
    {"course_name": "算法设计与分析（双语）", "day_of_week": 3, "period": 8, "period_end": 9, "start_week": 1,  "end_week": 8,  "location": "C4楼409",    "teacher": "潘啸晨"},
    {"course_name": "算法设计与分析（双语）", "day_of_week": 3, "period": 8, "period_end": 9, "start_week": 9,  "end_week": 12, "location": "C4楼418机房", "teacher": "潘啸晨"},

    # 数据库系统原理 - 邱洪泽 (1-7周 + 第1-2周额外)
    {"course_name": "数据库系统原理",       "day_of_week": 3, "period": 6, "period_end": 7,  "start_week": 1,  "end_week": 7,  "location": "C6楼I区303", "teacher": "邱洪泽"},
    {"course_name": "数据库系统原理",       "day_of_week": 1, "period": 8, "period_end": 9,  "start_week": 1,  "end_week": 7,  "location": "C6楼I区303", "teacher": "邱洪泽"},
    {"course_name": "数据库系统原理",       "day_of_week": 5, "period": 8, "period_end": 9,  "start_week": 1,  "end_week": 2,  "location": "C6楼I区303", "teacher": "邱洪泽"},

    # 数据库应用开发实践 - 邱洪泽 (9-15周)
    {"course_name": "数据库应用开发实践",   "day_of_week": 3, "period": 1, "period_end": 2,  "start_week": 9,  "end_week": 15, "location": "C4楼418机房", "teacher": "邱洪泽"},
    {"course_name": "数据库应用开发实践",   "day_of_week": 5, "period": 3, "period_end": 5,  "start_week": 9,  "end_week": 12, "location": "C4楼418机房", "teacher": "邱洪泽"},
    {"course_name": "数据库应用开发实践",   "day_of_week": 5, "period": 3, "period_end": 4,  "start_week": 13, "end_week": 15, "location": "C4楼418机房", "teacher": "邱洪泽"},

    # 软件设计模式 - 贾志洋 (9-15周)
    {"course_name": "软件设计模式",         "day_of_week": 5, "period": 6, "period_end": 7,  "start_week": 9,  "end_week": 15, "location": "C4楼419机房", "teacher": "贾志洋"},
    {"course_name": "软件设计模式",         "day_of_week": 2, "period": 8, "period_end": 9,  "start_week": 9,  "end_week": 15, "location": "C4楼419机房", "teacher": "贾志洋"},
    {"course_name": "软件设计模式",         "day_of_week": 3, "period": 8, "period_end": 9,  "start_week": 14, "end_week": 15, "location": "C4楼419机房", "teacher": "贾志洋"},

    # 数据可视化与应用 - 王雪颖 (1-8周)
    {"course_name": "数据可视化与应用",     "day_of_week": 2, "period": 6, "period_end": 7,  "start_week": 1,  "end_week": 8,  "location": "C6楼II区505机房", "teacher": "王雪颖"},
    {"course_name": "数据可视化与应用",     "day_of_week": 4, "period": 10,"period_end": 11, "start_week": 1,  "end_week": 8,  "location": "C6楼II区505机房", "teacher": "王雪颖"},

    # ===== 数学基础 =====
    # 概率论与数理统计 - 李中岩 (1-14周, 同一教师全程教学)
    {"course_name": "概率论与数理统计",     "day_of_week": 5, "period": 1, "period_end": 2,  "start_week": 1,  "end_week": 14, "location": "C4楼118",    "teacher": "李中岩"},
    {"course_name": "概率论与数理统计",     "day_of_week": 3, "period": 4, "period_end": 5,  "start_week": 1,  "end_week": 14, "location": "C4楼118",    "teacher": "李中岩"},

    # ===== 管理类 =====
    # 项目管理与技术经济 - 张德远 (1-8周)
    {"course_name": "项目管理与技术经济",   "day_of_week": 3, "period": 1, "period_end": 2,  "start_week": 1,  "end_week": 8,  "location": "C4楼213",    "teacher": "张德远"},
    {"course_name": "项目管理与技术经济",   "day_of_week": 5, "period": 3, "period_end": 4,  "start_week": 1,  "end_week": 8,  "location": "C4楼213",    "teacher": "张德远"},

    # ===== 思政课 =====
    # 习近平新时代中国特色社会主义思想概论 - 田立年 (8-15周)
    {"course_name": "习近平新时代中国特色社会主义思想概论", "day_of_week": 3, "period": 6, "period_end": 7, "start_week": 8, "end_week": 15, "location": "C4楼121", "teacher": "田立年"},
    {"course_name": "习近平新时代中国特色社会主义思想概论", "day_of_week": 1, "period": 8, "period_end": 9, "start_week": 8, "end_week": 15, "location": "C4楼121", "teacher": "田立年"},

    # 毛泽东思想和中国特色社会主义理论体系概论 - 斯洪桥 (1-8周)
    {"course_name": "毛泽东思想和中国特色社会主义理论体系概论", "day_of_week": 5, "period": 6, "period_end": 7, "start_week": 1, "end_week": 8, "location": "C4楼118", "teacher": "斯洪桥"},
    {"course_name": "毛泽东思想和中国特色社会主义理论体系概论", "day_of_week": 2, "period": 8, "period_end": 9, "start_week": 1, "end_week": 8, "location": "C4楼118", "teacher": "斯洪桥"},

    # ===== 体育 =====
    # 大学体育IV（必修项目）- 王建民 (1-15周) 乒乓球
    {"course_name": "大学体育IV（乒乓球）", "day_of_week": 2, "period": 3, "period_end": 4, "start_week": 1, "end_week": 15, "location": "乒乓球馆", "teacher": "王建民"},

    # ===== 通识选修 =====
    # 美术鉴赏 - 张宝 (1-15周)
    {"course_name": "美术鉴赏",             "day_of_week": 2, "period": 10,"period_end": 11, "start_week": 1,  "end_week": 15, "location": "C4楼415",    "teacher": "张宝"},
    {"course_name": "美术鉴赏",             "day_of_week": 2, "period": 12,"period_end": 12, "start_week": 14, "end_week": 15, "location": "C4楼415",    "teacher": "张宝"},
]


def import_to_db(user_id=None, clear_old=True):
    """将推荐方案导入到 MyScheduler 数据库"""
    sys.path.insert(0, os.path.dirname(__file__))
    from app import app, db
    from models import Course, User

    with app.app_context():
        if user_id is None:
            user = User.query.first()
            if not user:
                print("数据库中无用户，请先注册")
                return
            user_id = user.id
            print(f"使用用户: {user.username} (ID={user_id})")
        
        if clear_old:
            deleted = Course.query.filter_by(user_id=user_id).delete()
            print(f"已清除旧课程 {deleted} 条")
        
        count = 0
        for c in RECOMMENDED_COURSES:
            db.session.add(Course(user_id=user_id, **c))
            count += 1
        
        db.session.commit()
        print(f"成功导入 {count} 条课程记录！")
        print("\n=== 导入的课程清单 ===")
        unique_names = sorted(set(c['course_name'] for c in RECOMMENDED_COURSES))
        for name in unique_names:
            entries = [c for c in RECOMMENDED_COURSES if c['course_name'] == name]
            teacher = entries[0]['teacher']
            weeks = f"{min(c['start_week'] for c in entries)}-{max(c['end_week'] for c in entries)}周"
            print(f"  {name} ({teacher}) [{weeks}]")


def print_weekly_schedule():
    """打印周课表视图"""
    days = {1:'周一', 2:'周二', 3:'周三', 4:'周四', 5:'周五'}
    
    print("\n" + "=" * 100)
    print("  推荐方案: 完美课表 (基于大二下24-1/2班优化)")
    print("=" * 100)
    
    for phase, (ws, we, desc) in enumerate([
        (1, 7, "前期 (1-7周): 全课程并行"),
        (8, 8, "中期 (第8周): 课程切换周"),
        (9, 12, "中后期 (9-12周): 实践+设计模式"),
        (13, 15, "后期 (13-15周): 收尾阶段"),
    ]):
        week = ws
        print(f"\n{'─'*100}")
        print(f"  ▶ {desc}")
        print(f"{'─'*100}")
        
        header = f"{'节次':>6}"
        for d in range(1, 6):
            header += f"  {days[d]:^16}"
        print(header)
        print("─" * 100)
        
        # Group by time slots
        time_slots = [(1,2,"上午"), (3,4,"上午"), (4,5,"上午"), (6,7,"下午"), (8,9,"下午"), (10,11,"晚上"), (12,12,"晚上")]
        
        shown_slots = set()
        for ps, pe, period_name in time_slots:
            row_data = {}
            has_content = False
            for d in range(1, 6):
                courses_at = []
                for c in RECOMMENDED_COURSES:
                    if c['day_of_week'] == d and c['period'] == ps and c['period_end'] == pe and c['start_week'] <= week <= c['end_week']:
                        courses_at.append(c['course_name'][:8])
                if courses_at:
                    row_data[d] = "/".join(courses_at)
                    has_content = True
                else:
                    row_data[d] = ""
            
            if has_content:
                slot_key = (ps, pe)
                if slot_key not in shown_slots:
                    shown_slots.add(slot_key)
                    row = f"{ps}-{pe}节 "
                    for d in range(1, 6):
                        cell = row_data.get(d, "")
                        row += f"  {cell:^16}"
                    print(row)
        
        # Count total
        total = 0
        for c in RECOMMENDED_COURSES:
            for d in range(1, 6):
                if c['day_of_week'] == d and c['start_week'] <= week <= c['end_week']:
                    total += c['period_end'] - c['period'] + 1
        print(f"  本阶段周课时: ~{total}节")


def print_advantages():
    """输出方案优势分析"""
    print("\n" + "=" * 80)
    print("  方案优势分析")
    print("=" * 80)
    print("""
┌─────────────────────────────────────────────────────────────────────┐
│  推荐理由：选择 大二下课表(24-1/2班) 而非 李健豪课表(24-3/4/5班)    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. 【负载均衡】周三最大仅8节 (A方案高达10节从早到晚)               │
│     - A: 周三 1-2+3-4+6-7+8-9+10-11 = 10节 (全天无休)             │
│     - B: 周三 1-2+4-5+6-7+8-9 = 8节 (无晚课)                      │
│                                                                     │
│  2. 【教学连贯】概率论全程1位老师(李中岩)                            │
│     - A: 张婧妍(1-8周) → 赵联文(9-14周) 中途换老师                 │
│     - B: 李中岩 全程1-14周                                          │
│                                                                     │
│  3. 【课程丰富】额外含美术鉴赏通识选修课                             │
│     - 周二晚 10-11节，不占用正课时间                                 │
│     - 增加人文素养学分                                               │
│                                                                     │
│  4. 【每日分布】更合理的时间分配                                      │
│     - 周一: 8节(1-9) → 紧凑但标准                                   │
│     - 周二: 6-8节 → 上午休息，下午+晚上                              │
│     - 周三: 8节(1-9) → 比A少2节晚课                                 │
│     - 周四: 4-6节 → 最轻松自习日                                     │
│     - 周五: 6-8节 → 合理收尾                                        │
│                                                                     │
│  5. 【体育选择】乒乓球馆 vs 形体馆                                   │
│     - 乒乓球更受欢迎，技术性强且趣味性高                             │
│                                                                     │
│  6. 【自习黄金时段】                                                 │
│     - 周二上午 1-2节完全空闲 → 适合复习当天下午课程                   │
│     - 周四下午 6-9节空闲 → 大段自习/做项目时间                       │
│     - 周六日完全空闲 → 系统复习+课程设计                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  学习建议                                                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ★ 第1-8周(课程密集期):                                              │
│    - 重点攻克: 算法设计、操作系统、数据库系统原理                     │
│    - 周四下午为黄金自习段，建议做算法题                               │
│    - 数据可视化仅8周，需在期内完成所有实验                            │
│                                                                     │
│  ★ 第9-12周(实践转型期):                                             │
│    - 数据库应用开发实践取代数据库系统原理                             │
│    - 软件设计模式取代毛概，两门实操课需多投入                         │
│    - 算法课延续到12周，注意复习备考                                   │
│                                                                     │
│  ★ 第13-15周(收尾冲刺期):                                            │
│    - 课时大幅减少(约20节/周→18节/周)                                 │
│    - 利用空闲时间系统复习准备期末考试                                 │
│    - 两门思政课贯穿始终，平时记好笔记                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
""")


if __name__ == '__main__':
    print_advantages()
    print_weekly_schedule()
    
    print("\n" + "=" * 80)
    print("  是否导入到 MyScheduler?")
    print("=" * 80)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--import':
        user_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
        import_to_db(user_id=user_id)
    else:
        print("\n  运行以下命令导入:")
        print("    python perfect_schedule.py --import")
        print("    python perfect_schedule.py --import <user_id>")
