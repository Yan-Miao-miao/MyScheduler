# -*- coding: utf-8 -*-
"""分析两个课表并制定完美方案"""

days = {1:'周一', 2:'周二', 3:'周三', 4:'周四', 5:'周五', 6:'周六', 7:'周日'}

# (课程, 星期, 开始节, 结束节, 开始周, 结束周, 地点, 教师)
schedule_A = [
    ('数据可视化与应用', 1, 1, 2, 1, 8, 'C5楼II区405机房', '张美智'),
    ('操作系统原理', 2, 1, 2, 1, 12, 'C4楼411/421', '冷艳梅'),
    ('概率论与数理统计', 3, 1, 2, 1, 8, 'C4楼203', '张婧妍'),
    ('概率论与数理统计', 3, 1, 2, 9, 14, 'C4楼203', '赵联文'),
    ('Web程序设计', 4, 1, 2, 1, 12, 'C4楼420机房', '柴亚辉'),
    ('项目管理与技术经济', 5, 1, 2, 1, 8, 'C4楼303', '宋克勤'),
    ('数据库应用开发实践', 5, 1, 2, 9, 15, 'C4楼418机房', '邱洪泽'),
    ('大学体育IV', 2, 3, 4, 1, 15, '形体馆', '薛晴晴'),
    ('项目管理与技术经济', 3, 3, 4, 1, 8, 'C4楼303', '宋克勤'),
    ('数据库应用开发实践', 3, 3, 5, 9, 12, 'C4楼418机房', '邱洪泽'),
    ('数据库应用开发实践', 3, 3, 4, 13, 15, 'C4楼418机房', '邱洪泽'),
    ('Web程序设计', 1, 4, 5, 1, 12, 'C4楼420机房', '柴亚辉'),
    ('操作系统原理', 4, 4, 5, 1, 12, 'C4楼411/421', '冷艳梅'),
    ('概率论与数理统计', 5, 4, 5, 1, 8, 'C4楼203', '张婧妍'),
    ('概率论与数理统计', 5, 4, 5, 9, 14, 'C4楼203', '赵联文'),
    ('数据库系统原理', 1, 6, 7, 1, 7, 'C6楼I区303', '邱洪泽'),
    ('习近平新时代中国特色社会主义思想概论', 1, 6, 7, 8, 15, 'C4楼303', '杨晨晨'),
    ('毛泽东思想和中国特色社会主义理论体系概论', 2, 6, 7, 1, 8, 'C4楼501', '唐诗宇'),
    ('软件设计模式', 2, 6, 7, 9, 15, 'C4楼419机房', '贾志洋'),
    ('算法设计与分析（双语）', 3, 6, 7, 1, 8, 'C4楼405', '胡鸿铭'),
    ('算法设计与分析（双语）', 3, 6, 7, 9, 12, 'C4楼419机房', '胡鸿铭'),
    ('软件设计模式', 3, 6, 7, 14, 15, 'C4楼419机房', '贾志洋'),
    ('数据库系统原理', 5, 6, 7, 1, 2, 'C6楼I区303', '邱洪泽'),
    ('算法设计与分析（双语）', 1, 8, 9, 1, 8, 'C4楼405', '胡鸿铭'),
    ('算法设计与分析（双语）', 1, 8, 9, 9, 12, 'C4楼419机房', '胡鸿铭'),
    ('数据库系统原理', 3, 8, 9, 1, 7, 'C6楼I区303', '邱洪泽'),
    ('习近平新时代中国特色社会主义思想概论', 3, 8, 9, 8, 15, 'C4楼303', '杨晨晨'),
    ('毛泽东思想和中国特色社会主义理论体系概论', 5, 8, 9, 1, 8, 'C4楼501', '唐诗宇'),
    ('软件设计模式', 5, 8, 9, 9, 15, 'C4楼419机房', '贾志洋'),
    ('数据可视化与应用', 3, 10, 11, 1, 8, 'C5楼II区405机房', '张美智'),
]

schedule_B = [
    ('Web程序设计', 1, 1, 2, 1, 12, 'C4楼420机房', '王晓伟'),
    ('项目管理与技术经济', 3, 1, 2, 1, 8, 'C4楼213', '张德远'),
    ('数据库应用开发实践', 3, 1, 2, 9, 15, 'C4楼418机房', '邱洪泽'),
    ('操作系统原理', 4, 1, 2, 1, 12, 'C4楼413/C8II304', '郑顾平'),
    ('概率论与数理统计', 5, 1, 2, 1, 14, 'C4楼118', '李中岩'),
    ('大学体育IV', 2, 3, 4, 1, 15, '乒乓球馆', '王建民'),
    ('项目管理与技术经济', 5, 3, 4, 1, 8, 'C4楼213', '张德远'),
    ('数据库应用开发实践', 5, 3, 5, 9, 12, 'C4楼418机房', '邱洪泽'),
    ('数据库应用开发实践', 5, 3, 4, 13, 15, 'C4楼418机房', '邱洪泽'),
    ('操作系统原理', 1, 4, 5, 1, 12, 'C4楼413/C8II304', '郑顾平'),
    ('概率论与数理统计', 3, 4, 5, 1, 14, 'C4楼118', '李中岩'),
    ('Web程序设计', 4, 4, 5, 1, 12, 'C4楼420机房', '王晓伟'),
    ('算法设计与分析（双语）', 1, 6, 7, 1, 12, 'C4楼409/418', '潘啸晨'),
    ('数据可视化与应用', 2, 6, 7, 1, 8, 'C6楼II区505机房', '王雪颖'),
    ('数据库系统原理', 3, 6, 7, 1, 7, 'C6楼I区303', '邱洪泽'),
    ('习近平新时代中国特色社会主义思想概论', 3, 6, 7, 8, 15, 'C4楼121', '田立年'),
    ('毛泽东思想和中国特色社会主义理论体系概论', 5, 6, 7, 1, 8, 'C4楼118', '斯洪桥'),
    ('软件设计模式', 5, 6, 7, 9, 15, 'C4楼419机房', '贾志洋'),
    ('数据库系统原理', 1, 8, 9, 1, 7, 'C6楼I区303', '邱洪泽'),
    ('习近平新时代中国特色社会主义思想概论', 1, 8, 9, 8, 15, 'C4楼121', '田立年'),
    ('毛泽东思想和中国特色社会主义理论体系概论', 2, 8, 9, 1, 8, 'C4楼118', '斯洪桥'),
    ('软件设计模式', 2, 8, 9, 9, 15, 'C4楼419机房', '贾志洋'),
    ('算法设计与分析（双语）', 3, 8, 9, 1, 12, 'C4楼409/418', '潘啸晨'),
    ('软件设计模式', 3, 8, 9, 14, 15, 'C4楼419机房', '贾志洋'),
    ('数据库系统原理', 5, 8, 9, 1, 2, 'C6楼I区303', '邱洪泽'),
    ('美术鉴赏', 2, 10, 11, 1, 15, 'C4楼415', '张宝'),
    ('数据可视化与应用', 4, 10, 11, 1, 8, 'C6楼II区505机房', '王雪颖'),
    ('美术鉴赏', 2, 12, 12, 14, 15, 'C4楼415', '张宝'),
]


def get_daily_slots(schedule, week, day):
    """获取某周某天的课程列表"""
    slots = []
    for c in schedule:
        name, d, ps, pe, ws, we = c[0], c[1], c[2], c[3], c[4], c[5]
        if d == day and ws <= week <= we:
            slots.append((ps, pe, name))
    slots.sort()
    return slots


def analyze(name, schedule):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    
    for week in [1, 5, 9, 13]:
        print(f"\n--- 第{week}周 ---")
        total_periods = 0
        for day in range(1, 8):
            slots = get_daily_slots(schedule, week, day)
            if slots:
                periods = sum(pe - ps + 1 for ps, pe, _ in slots)
                total_periods += periods
                detail = "; ".join(f"{ps}-{pe}节{n}" for ps, pe, n in slots)
                # 计算最早和最晚
                earliest = min(ps for ps, pe, n in slots)
                latest = max(pe for ps, pe, n in slots)
                print(f"  {days[day]}: {len(slots)}门({periods}节) [{earliest}-{latest}节] {detail}")
        print(f"  >>> 本周总计: {total_periods}节课")


def find_free_time(schedule, week):
    """找出空闲时间段"""
    free = {}
    for day in range(1, 6):
        occupied = set()
        for c in schedule:
            name, d, ps, pe, ws, we = c[0], c[1], c[2], c[3], c[4], c[5]
            if d == day and ws <= week <= we:
                for p in range(ps, pe + 1):
                    occupied.add(p)
        free_slots = []
        for p in range(1, 12):
            if p not in occupied:
                free_slots.append(p)
        free[day] = free_slots
    return free


print("\n" + "=" * 60)
print("  课表对比分析")
print("=" * 60)

analyze("方案A: 李健豪课表 (24-3/4/5班)", schedule_A)
analyze("方案B: 大二下课表 (24-1/2班)", schedule_B)

# 对比关键指标
print("\n" + "=" * 60)
print("  核心差异对比")
print("=" * 60)

courses_set = set()
for c in schedule_A:
    courses_set.add(c[0])
for c in schedule_B:
    courses_set.add(c[0])

print("\n共同课程:")
a_names = set(c[0] for c in schedule_A)
b_names = set(c[0] for c in schedule_B)
common = a_names & b_names
only_a = a_names - b_names
only_b = b_names - a_names

for name in sorted(common):
    a_teacher = set(c[7] for c in schedule_A if c[0] == name)
    b_teacher = set(c[7] for c in schedule_B if c[0] == name)
    a_days = sorted(set(c[1] for c in schedule_A if c[0] == name))
    b_days = sorted(set(c[1] for c in schedule_B if c[0] == name))
    a_day_str = "+".join(days[d] for d in a_days)
    b_day_str = "+".join(days[d] for d in b_days)
    print(f"  {name}:")
    print(f"    A: {'/'.join(a_teacher)} ({a_day_str})")
    print(f"    B: {'/'.join(b_teacher)} ({b_day_str})")

if only_a:
    print(f"\n仅A有: {', '.join(only_a)}")
if only_b:
    print(f"\n仅B有: {', '.join(only_b)}")

# 分析每日最大负载
print("\n" + "=" * 60)
print("  每日负载峰值对比 (全学期最重周)")
print("=" * 60)

for label, sch in [("A", schedule_A), ("B", schedule_B)]:
    max_day_load = {}
    for week in range(1, 16):
        for day in range(1, 6):
            slots = get_daily_slots(sch, week, day)
            periods = sum(pe - ps + 1 for ps, pe, _ in slots)
            key = days[day]
            if key not in max_day_load or periods > max_day_load[key]:
                max_day_load[key] = periods
    print(f"\n方案{label} 每日最大课时:")
    for day in range(1, 6):
        print(f"  {days[day]}: 最多{max_day_load[days[day]]}节")

# 分析空闲时段
print("\n" + "=" * 60)
print("  空闲时间对比 (第5周为例)")  
print("=" * 60)

for label, sch in [("A", schedule_A), ("B", schedule_B)]:
    free = find_free_time(sch, 5)
    print(f"\n方案{label} 第5周空闲节次:")
    for day in range(1, 6):
        if free[day]:
            print(f"  {days[day]}: 第{','.join(str(p) for p in free[day])}节")

# Wednesday comparison (critical day)
print("\n" + "=" * 60)
print("  周三对比 (两方案差异最大的一天)")
print("=" * 60)

for label, sch in [("A", schedule_A), ("B", schedule_B)]:
    print(f"\n方案{label} 周三第5周:")
    slots = get_daily_slots(sch, 5, 3)
    for ps, pe, name in slots:
        print(f"  {ps}-{pe}节: {name}")
    periods = sum(pe - ps + 1 for ps, pe, _ in slots)
    if slots:
        span = f"{min(ps for ps,_,_ in slots)}-{max(pe for _,pe,_ in slots)}节"
    else:
        span = "无课"
    print(f"  总计: {periods}节, 跨度: {span}")
