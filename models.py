# -*- coding: utf-8 -*-
"""
数据库模型文件 (models.py)
这个文件定义了数据库的表结构，使用 SQLAlchemy ORM (对象关系映射) 框架
ORM 的作用：让我们用 Python 类来操作数据库，而不用直接写 SQL 语句
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 创建 SQLAlchemy 数据库对象
# 这个 db 对象会在 app.py 中与 Flask 应用绑定
db = SQLAlchemy()


class Course(db.Model):
    """
    课程表模型 - 对应数据库中的 course 表
    用于存储课程的基本信息
    """
    
    # __tablename__ 指定数据库中的表名（可选，默认是类名的小写）
    __tablename__ = 'course'
    
    # ========== 字段定义 ==========
    
    # id: 主键字段
    # db.Integer: 整数类型，用于存储数字
    # primary_key=True: 设置为主键，每条记录的唯一标识
    # autoincrement=True: 自动递增，插入新记录时自动生成 id（1, 2, 3...）
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # course_name: 课程名称
    # db.String(100): 字符串类型，最大长度 100 个字符
    # nullable=False: 不允许为空，必须填写课程名
    course_name = db.Column(db.String(100), nullable=False)
    
    # location: 上课地点
    # db.String(100): 字符串类型，最大长度 100 个字符
    # nullable=True: 允许为空（默认值），可以不填地点
    location = db.Column(db.String(100), nullable=True)
    
    # teacher: 任课老师
    # db.String(50): 字符串类型，最大长度 50 个字符
    teacher = db.Column(db.String(50), nullable=True)
    
    # day_of_week: 星期几
    # db.Integer: 整数类型，用 1-7 表示周一到周日
    # nullable=False: 必须填写是星期几
    day_of_week = db.Column(db.Integer, nullable=False)
    
    # period: 第几节课（起始节次）
    # db.Integer: 整数类型，例如 1 表示第一节，2 表示第二节
    # nullable=False: 必须填写是第几节课
    period = db.Column(db.Integer, nullable=False)
    
    # period_end: 结束节次（用于连堂课）
    # 例如 period=1, period_end=2 表示第1-2节连堂
    period_end = db.Column(db.Integer, nullable=True)
    
    # start_week: 起始周次
    # 例如 start_week=2 表示从第2周开始上课
    start_week = db.Column(db.Integer, nullable=True, default=1)
    
    # end_week: 结束周次
    # 例如 end_week=13 表示到第13周结束
    end_week = db.Column(db.Integer, nullable=True, default=20)
    
    # ========== 关系定义 ==========
    
    # assignments: 定义与 Assignment 模型的"一对多"关系
    # 一门课程可以有多个作业，这个字段让我们能通过 course.assignments 访问该课程的所有作业
    # 
    # db.relationship() 的参数解释：
    # - 'Assignment': 关联的模型名称（字符串形式）
    # - backref='course': 反向引用，让 Assignment 对象可以通过 assignment.course 访问所属课程
    # - lazy='dynamic': 懒加载模式，不立即查询所有作业，而是返回一个查询对象，可以继续添加过滤条件
    # - cascade='all, delete-orphan': 级联删除，删除课程时自动删除该课程的所有作业
    #   * 'all': 所有操作都级联（保存、更新、删除等）
    #   * 'delete-orphan': 如果作业不再属于任何课程，也会被删除
    assignments = db.relationship('Assignment', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        """
        定义对象的字符串表示形式
        当我们打印 Course 对象时，会显示这个格式
        """
        return f'<Course {self.course_name}>'


class Assignment(db.Model):
    """
    作业模型 - 对应数据库中的 assignment 表
    用于存储作业的详细信息
    """
    
    __tablename__ = 'assignment'
    
    # ========== 字段定义 ==========
    
    # id: 主键字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # assignment_name: 作业名称
    # nullable=False: 必须填写作业名
    assignment_name = db.Column(db.String(200), nullable=False)
    
    # description: 作业描述
    # db.Text: 文本类型，可以存储大量文字（比 String 更长）
    # nullable=True: 描述可以为空
    description = db.Column(db.Text, nullable=True)
    
    # due_date: 截止日期
    # db.DateTime: 日期时间类型，存储年月日时分秒
    # nullable=False: 必须设置截止日期
    due_date = db.Column(db.DateTime, nullable=False)
    
    # is_completed: 是否完成
    # db.Boolean: 布尔类型，只有 True 或 False 两个值
    # default=False: 默认值为 False（未完成）
    # nullable=False: 不允许为空
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    
    # ========== 外键定义 ==========
    
    # course_id: 外键字段，关联到 course 表的 id
    # 
    # db.ForeignKey() 的作用：
    # - 建立表与表之间的关联关系
    # - 'course.id': 指向 course 表的 id 字段
    # - 确保数据完整性：course_id 的值必须是 course 表中存在的 id
    # - 例如：如果 course_id = 3，那么 course 表中必须有 id=3 的记录
    # 
    # nullable=False: 每个作业必须属于某门课程
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    # 注意：通过上面 Course 模型中定义的 backref='course'
    # 我们可以用 assignment.course 来访问这个作业所属的课程对象
    # 例如：assignment.course.course_name 可以获取课程名称
    
    def __repr__(self):
        """
        定义对象的字符串表示形式
        """
        return f'<Assignment {self.assignment_name}>'


# ========== 数据库知识总结 ==========
"""
1. 字段类型 (Column Types):
   - Integer: 整数
   - String(n): 字符串，n 是最大长度
   - Text: 长文本
   - DateTime: 日期时间
   - Boolean: 布尔值 (True/False)

2. 字段约束 (Constraints):
   - primary_key: 主键，唯一标识每条记录
   - nullable: 是否允许为空 (True/False)
   - default: 默认值
   - autoincrement: 自动递增

3. 关系 (Relationships):
   - ForeignKey: 外键，建立表之间的关联
   - relationship: 定义 ORM 层面的关系，方便访问关联数据
   - backref: 反向引用，双向访问关系
   - cascade: 级联操作，控制关联数据的删除行为

4. 一对多关系示例:
   一门课程 (Course) 可以有多个作业 (Assignment)
   - Course 中用 relationship 定义 assignments
   - Assignment 中用 ForeignKey 定义 course_id
   - 通过 backref，Assignment 可以反向访问 Course
"""
