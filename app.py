# -*- coding: utf-8 -*-
"""
Flask 应用主文件 (app.py)
这是整个 Web 应用的入口文件
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from models import db, User, Course, Assignment
from datetime import datetime
from functools import wraps
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash, check_password_hash
import os

# 创建 Flask 应用实例
app = Flask(__name__)

# ========== 数据库配置 ==========

# 设置数据库文件路径
# os.path.abspath: 获取绝对路径
# os.path.dirname(__file__): 获取当前文件所在目录
# 数据库文件 scheduler.db 会保存在项目根目录
basedir = os.path.abspath(os.path.dirname(__file__))
database_path = os.path.join(basedir, 'scheduler.db')

# SQLALCHEMY_DATABASE_URI: 数据库连接字符串
# sqlite:/// 表示使用 SQLite 数据库，后面跟数据库文件路径
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'

# SQLALCHEMY_TRACK_MODIFICATIONS: 是否追踪对象修改
# 设为 False 可以节省内存，Flask-SQLAlchemy 官方推荐
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'myscheduler-dev-secret-key')

# 设置 JSON 响应支持中文
# 不进行 ASCII 编码，直接返回 UTF-8 中文
app.config['JSON_AS_ASCII'] = False

# 将数据库对象与 Flask 应用绑定
db.init_app(app)


def get_current_user_id():
    return session.get('user_id')


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not get_current_user_id():
            return jsonify({'error': '请先登录'}), 401
        return func(*args, **kwargs)

    return wrapper


# ========== 路由定义 ==========

@app.route('/sw.js')
def service_worker():
    """从根路径提供 Service Worker，使其作用域覆盖整个站点"""
    response = send_from_directory(app.static_folder, 'sw.js')
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response


@app.route('/manifest.json')
def manifest():
    """从根路径提供 manifest.json，提高 PWA 兼容性"""
    return send_from_directory(app.static_folder, 'manifest.json')


@app.route('/')
def index():
    """
    首页路由
    访问 http://localhost:5000/ 时会调用这个函数
    返回 templates/index.html 页面
    """
    if not get_current_user_id():
        return redirect(url_for('login_page'))
    return render_template('index.html')


@app.route('/login')
def login_page():
    if get_current_user_id():
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    if len(username) > 50:
        return jsonify({'error': '用户名长度不能超过 50'}), 400

    if User.query.count() >= 20:
        return jsonify({'error': '当前系统最多支持 20 个账号'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400

    user = User(
        username=username,
        password_hash=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': '注册成功，请登录'}), 201


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': '用户名或密码错误'}), 401

    session['user_id'] = user.id
    session['username'] = user.username
    return jsonify({'message': '登录成功', 'username': user.username})


@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return jsonify({'message': '已退出登录'})


@app.route('/api/account', methods=['DELETE'])
@login_required
def delete_my_account():
    data = request.get_json() or {}
    password = data.get('password') or ''

    if not password:
        return jsonify({'error': '请输入当前密码确认注销'}), 400

    user_id = get_current_user_id()
    user = User.query.get_or_404(user_id)

    if not check_password_hash(user.password_hash, password):
        return jsonify({'error': '密码错误，无法注销账号'}), 401

    db.session.delete(user)
    db.session.commit()
    session.clear()
    return jsonify({'message': '账号已注销'})


@app.route('/api/me', methods=['GET'])
@login_required
def me():
    return jsonify({
        'user_id': session.get('user_id'),
        'username': session.get('username')
    })


@app.route('/api/courses', methods=['GET', 'POST'])
@login_required
def courses():
    """
    课程 API 路由
    GET: 获取所有课程列表
    POST: 添加新课程
    """
    if request.method == 'GET':
        # 查询所有课程，按星期和节次排序
        current_user_id = get_current_user_id()
        all_courses = Course.query.filter_by(user_id=current_user_id).order_by(Course.day_of_week, Course.period).all()
        
        # 将课程对象转换为字典列表，方便 JSON 序列化
        courses_list = []
        for course in all_courses:
            courses_list.append({
                'id': course.id,
                'course_name': course.course_name,
                'location': course.location,
                'teacher': course.teacher,
                'day_of_week': course.day_of_week,
                'period': course.period,
                'period_end': course.period_end,
                'start_week': course.start_week,
                'end_week': course.end_week,
                'user_id': course.user_id
            })
        
        # 返回 JSON 格式的响应
        return jsonify(courses_list)
    
    elif request.method == 'POST':
        # 获取前端发送的 JSON 数据
        data = request.get_json()
        current_user_id = get_current_user_id()
        
        # 创建新课程对象
        new_course = Course(
            course_name=data['course_name'],
            location=data.get('location', ''),
            teacher=data.get('teacher', ''),
            day_of_week=data['day_of_week'],
            period=data['period'],
            period_end=data.get('period_end', data['period']),
            start_week=data.get('start_week', 1),
            end_week=data.get('end_week', 20),
            user_id=current_user_id
        )
        
        # 添加到数据库会话并提交
        db.session.add(new_course)
        db.session.commit()
        
        return jsonify({'message': '课程添加成功', 'id': new_course.id}), 201


@app.route('/api/courses/<int:course_id>', methods=['DELETE'])
@login_required
def delete_course(course_id):
    """
    删除课程 API
    DELETE: 删除指定 ID 的课程
    """
    current_user_id = get_current_user_id()
    course = Course.query.filter_by(id=course_id, user_id=current_user_id).first_or_404()
    db.session.delete(course)
    db.session.commit()
    return jsonify({'message': '课程删除成功'})


@app.route('/api/assignments', methods=['GET', 'POST'])
@login_required
def assignments():
    """
    作业 API 路由
    GET: 获取所有作业列表
    POST: 添加新作业
    """
    if request.method == 'GET':
        # 查询所有作业，按截止日期排序
        current_user_id = get_current_user_id()
        all_assignments = Assignment.query.filter_by(user_id=current_user_id).order_by(Assignment.due_date).all()
        
        assignments_list = []
        for assignment in all_assignments:
            assignments_list.append({
                'id': assignment.id,
                'assignment_name': assignment.assignment_name,
                'description': assignment.description,
                'due_date': assignment.due_date.strftime('%Y-%m-%d %H:%M'),
                'is_completed': assignment.is_completed,
                'course_id': assignment.course_id,
                'user_id': assignment.user_id,
                'course_name': assignment.course.course_name  # 通过外键关系获取课程名
            })
        
        return jsonify(assignments_list)
    
    elif request.method == 'POST':
        data = request.get_json()
        current_user_id = get_current_user_id()

        course = Course.query.filter_by(id=data['course_id'], user_id=current_user_id).first()
        if not course:
            return jsonify({'error': '课程不存在或无权限'}), 404
        
        # 将字符串格式的日期转换为 datetime 对象
        due_date = datetime.strptime(data['due_date'], '%Y-%m-%dT%H:%M')
        
        new_assignment = Assignment(
            assignment_name=data['assignment_name'],
            description=data.get('description', ''),
            due_date=due_date,
            is_completed=False,
            course_id=data['course_id'],
            user_id=current_user_id
        )
        
        db.session.add(new_assignment)
        db.session.commit()
        
        return jsonify({'message': '作业添加成功', 'id': new_assignment.id}), 201


@app.route('/api/assignments/<int:assignment_id>', methods=['PUT', 'DELETE'])
@login_required
def assignment_detail(assignment_id):
    """
    作业详情 API
    PUT: 更新作业（主要用于标记完成状态）
    DELETE: 删除作业
    """
    current_user_id = get_current_user_id()
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=current_user_id).first_or_404()
    
    if request.method == 'PUT':
        data = request.get_json()
        assignment.is_completed = data.get('is_completed', assignment.is_completed)
        db.session.commit()
        return jsonify({'message': '作业状态更新成功'})
    
    elif request.method == 'DELETE':
        db.session.delete(assignment)
        db.session.commit()
        return jsonify({'message': '作业删除成功'})


@app.route('/api/import_schedule', methods=['POST'])
@login_required
def import_schedule():
    """
    从强智教务系统导入课表 API
    POST: 接收学号和密码，爬取课表数据并导入数据库
    """
    try:
        # 获取前端发送的学号和密码
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': '请提供学号和密码'}), 400
        
        clear_old = data.get('clear_old', False)
        current_user_id = get_current_user_id()
        
        # 导入爬虫函数
        from utils import import_schedule_from_kingosoft
        
        # 调用爬虫获取课表
        courses_data = import_schedule_from_kingosoft(username, password)
        
        # 如果选择清空旧课表，先删除所有已有课程（级联删除关联作业）
        deleted_count = 0
        if clear_old:
            deleted_count = Course.query.filter_by(user_id=current_user_id).count()
            Course.query.filter_by(user_id=current_user_id).delete()
            db.session.commit()
        
        # 统计导入结果
        imported_count = 0
        skipped_count = 0
        
        # 将课程数据导入数据库
        for course_data in courses_data:
            # 检查是否已存在相同的课程（避免重复）
            existing_course = Course.query.filter_by(
                user_id=current_user_id,
                course_name=course_data['course_name'],
                day_of_week=course_data['day_of_week'],
                period=course_data['period'],
                start_week=course_data.get('start_week', 1)
            ).first()
            
            if existing_course:
                # 如果已存在，跳过
                skipped_count += 1
                continue
            
            # 创建新课程
            new_course = Course(
                course_name=course_data['course_name'],
                teacher=course_data.get('teacher', ''),
                location=course_data.get('location', ''),
                day_of_week=course_data['day_of_week'],
                period=course_data['period'],
                period_end=course_data.get('period_end', course_data['period']),
                start_week=course_data.get('start_week', 1),
                end_week=course_data.get('end_week', 20),
                user_id=current_user_id
            )
            
            db.session.add(new_course)
            imported_count += 1
        
        # 提交到数据库
        db.session.commit()
        
        # 返回导入结果
        if clear_old:
            msg = f'已清空旧课表（{deleted_count} 门），成功导入 {imported_count} 门新课程'
        else:
            msg = f'导入成功！新增 {imported_count} 门课程，跳过 {skipped_count} 门重复课程'
        
        return jsonify({
            'message': msg,
            'imported': imported_count,
            'skipped': skipped_count
        }), 200
        
    except Exception as e:
        # 捕获所有异常并返回错误信息
        error_message = str(e)
        
        # 根据错误类型返回不同的 HTTP 状态码
        if '用户名或密码错误' in error_message or '登录失败' in error_message:
            return jsonify({'error': error_message}), 401
        else:
            return jsonify({'error': f'导入失败: {error_message}'}), 500



# ========== 数据库初始化 ==========

def migrate_legacy_schema():
    """
    兼容旧版数据库结构：为已有表补充 user_id 字段
    """
    inspector = inspect(db.engine)

    if 'course' in inspector.get_table_names():
        course_columns = [col['name'] for col in inspector.get_columns('course')]
        if 'user_id' not in course_columns:
            db.session.execute(text('ALTER TABLE course ADD COLUMN user_id INTEGER'))

    if 'assignment' in inspector.get_table_names():
        assignment_columns = [col['name'] for col in inspector.get_columns('assignment')]
        if 'user_id' not in assignment_columns:
            db.session.execute(text('ALTER TABLE assignment ADD COLUMN user_id INTEGER'))

    db.session.commit()


def ensure_default_user():
    """
    确保至少存在一个用户，并把旧数据归属到该用户
    """
    if User.query.count() == 0:
        default_user = User(username='user1', password_hash=generate_password_hash('123456'))
        db.session.add(default_user)
        db.session.commit()

    first_user = User.query.order_by(User.id).first()
    if first_user:
        Course.query.filter(Course.user_id.is_(None)).update({'user_id': first_user.id})
        Assignment.query.filter(Assignment.user_id.is_(None)).update({'user_id': first_user.id})
        db.session.commit()


def init_database():
    """
    初始化数据库
    创建所有表结构
    """
    with app.app_context():
        # 创建所有表（如果不存在）
        db.create_all()
        migrate_legacy_schema()
        ensure_default_user()
        print('数据库初始化成功！')


# ========== 应用启动 ==========

if __name__ == '__main__':
    # 首次运行时初始化数据库
    init_database()
    
    # 启动 Flask 开发服务器
    # debug=True: 开启调试模式，代码修改后自动重启
    # host='0.0.0.0': 允许外部访问
    # port=5000: 监听 5000 端口
    app.run(debug=True, host='0.0.0.0', port=5000)
