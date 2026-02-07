# 个人课程表与作业提醒系统

## 项目简介
这是一个基于 Flask + SQLite + Vue 3 的个人课程表与作业提醒系统，帮助大学生管理课程和作业。

## 技术栈
- **后端**: Flask (Python Web 框架)
- **数据库**: SQLite (轻量级数据库)
- **前端**: Vue 3 (通过 CDN 引入，无需 Node.js)

## 项目结构
```
MyScheduler/
├── app.py              # Flask 应用主文件
├── models.py           # 数据库模型定义
├── requirements.txt    # Python 依赖包
├── scheduler.db        # SQLite 数据库文件（运行后自动生成）
├── templates/
│   └── index.html      # 前端页面
└── static/
    ├── style.css       # 样式文件
    └── script.js       # Vue 应用脚本
```

## 功能特性
1. **课程管理**
   - 添加课程（课程名、地点、老师、星期、节次）
   - 查看课程列表
   - 删除课程

2. **作业管理**
   - 添加作业（作业名、描述、截止日期、所属课程）
   - 查看作业列表
   - 标记作业完成状态
   - 删除作业

## 安装步骤

### 1. 安装 Python 依赖
```bash
pip install -r requirements.txt
```

### 2. 运行应用
```bash
python app.py
```

### 3. 访问应用
打开浏览器访问：http://localhost:5000

## 数据库说明
- 数据库文件 `scheduler.db` 会在首次运行时自动创建
- 包含两个表：
  - `course`: 课程表
  - `assignment`: 作业表
- 两表通过外键关联（assignment.course_id → course.id）

## 学习要点
- **models.py** 中有详细的中文注释，解释了：
  - 数据库字段类型（Integer, String, Text, DateTime, Boolean）
  - 主键和外键的概念
  - 一对多关系的实现
  - ORM 的基本用法

## 注意事项
- 删除课程时，该课程的所有作业也会被删除（级联删除）
- 截止日期使用浏览器的日期时间选择器
- 所有数据存储在本地 SQLite 数据库中

## 后续扩展建议
- 添加作业提醒功能
- 支持课程时间冲突检测
- 添加用户登录系统
- 导出课程表为图片
