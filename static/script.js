// Vue 3 应用
const { createApp } = Vue;

createApp({
    data() {
        return {
            courses: [],              // 课程列表
            assignments: [],          // 作业列表
            showAddCourseForm: false, // 是否显示添加课程表单
            showAddAssignmentForm: false, // 是否显示添加作业表单
            newCourse: {              // 新课程表单数据
                course_name: '',
                location: '',
                teacher: '',
                day_of_week: '',
                period: ''
            },
            newAssignment: {          // 新作业表单数据
                assignment_name: '',
                description: '',
                course_id: '',
                due_date: ''
            },
            showImportForm: false,    // 是否显示导入课表模态框
            importing: false,         // 是否正在导入中
            showUploadForm: false,    // 是否显示上传PDF模态框
            uploading: false,         // 是否正在上传解析中
            selectedPDF: null,        // 选中的PDF文件
            uploadClearOld: false,    // 上传时是否清空旧课表
            currentUser: '',          // 当前登录用户名
            importForm: {             // 导入课表表单数据
                username: '',
                password: '',
                clear_old: false
            },
            currentWeek: 1,          // 当前周次
            totalWeeks: 20,          // 学期总周数（可按需调整）
            touchStartX: 0,          // 触摸起始位置
            dayNames: ['', '一', '二', '三', '四', '五', '六', '日'],
            periodTimes: {
                1: '09:30\n10:15',
                2: '10:20\n11:05',
                3: '11:25\n12:10',
                4: '12:15\n13:00',
                5: '13:05\n13:50',
                6: '16:00\n16:45',
                7: '16:50\n17:35',
                8: '17:55\n18:40',
                9: '18:45\n19:30',
                10: '20:30\n21:15',
                11: '21:20\n22:05'
            },
            // 课程配色方案：浅底色 + 深文字，对比度高
            courseColors: [
                { bg: '#fce4ec', text: '#c62828', border: '#ef9a9a' },   // 粉红
                { bg: '#e3f2fd', text: '#1565c0', border: '#90caf9' },   // 蓝
                { bg: '#e8f5e9', text: '#2e7d32', border: '#a5d6a7' },   // 绿
                { bg: '#fff3e0', text: '#e65100', border: '#ffcc80' },   // 橙
                { bg: '#f3e5f5', text: '#6a1b9a', border: '#ce93d8' },   // 紫
                { bg: '#e0f2f1', text: '#00695c', border: '#80cbc4' },   // 青
                { bg: '#fbe9e7', text: '#bf360c', border: '#ffab91' },   // 珊瑚
                { bg: '#e8eaf6', text: '#283593', border: '#9fa8da' },   // 靛蓝
                { bg: '#f9fbe7', text: '#827717', border: '#dce775' },   // 柠檬
                { bg: '#efebe9', text: '#4e342e', border: '#bcaaa4' },   // 棕
            ]
        };
    },
    computed: {
        maxPeriod() {
            // 默认显示到第11节
            let max = 11;
            if (this.courses.length) {
                const courseMax = Math.max(...this.courses.map(c =>
                    Math.max(Number(c.period) || 0, Number(c.period_end) || 0)
                ));
                max = Math.max(max, courseMax);
            }
            return max;
        },
        todayLabel() {
            const today = new Date();
            return `${today.getFullYear()}/${today.getMonth() + 1}/${today.getDate()}`;
        },
        // 按当前周次过滤后的课程
        filteredCourses() {
            return this.courses.filter(c => {
                const sw = Number(c.start_week) || 1;
                const ew = Number(c.end_week) || 20;
                return this.currentWeek >= sw && this.currentWeek <= ew;
            });
        }
    },
    methods: {
        async loadCurrentUser() {
            try {
                const response = await fetch('/api/me');
                if (response.status === 401) {
                    window.location.href = '/login';
                    return;
                }
                const data = await response.json();
                this.currentUser = data.username || '';
            } catch (error) {
                console.error('获取用户信息失败:', error);
            }
        },

        async logout() {
            try {
                await fetch('/api/logout', { method: 'POST' });
            } catch (error) {
                console.error('退出登录失败:', error);
            } finally {
                window.location.href = '/login';
            }
        },

        async deleteMyAccount() {
            const ok = confirm('注销后将永久删除当前账号及其课程和作业，确定继续吗？');
            if (!ok) {
                return;
            }

            const password = prompt('请输入当前账号密码以确认注销：');
            if (password === null) {
                return;
            }

            if (!password.trim()) {
                alert('请输入密码后再试');
                return;
            }

            try {
                const response = await fetch('/api/account', {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ password })
                });

                const result = await response.json();
                if (!response.ok) {
                    alert(result.error || '注销失败，请重试');
                    return;
                }

                alert('账号已注销');
                window.location.href = '/login';
            } catch (error) {
                console.error('注销账号失败:', error);
                alert('注销失败，请检查网络后重试');
            }
        },

        // 获取星期名称
        getDayName(day) {
            return this.dayNames[day];
        },

        // 获取节次时间（返回 HTML 用于 v-html 渲染换行）
        getTimeLabel(period) {
            const t = this.periodTimes[period];
            return t ? t.replace('\n', '<br>') : '';
        },

        // 切换周次
        changeWeek(delta) {
            const next = this.currentWeek + delta;
            if (next < 1 || next > this.totalWeeks) {
                return;
            }
            this.currentWeek = next;
        },

        // 触摸开始
        onTouchStart(event) {
            if (event.changedTouches && event.changedTouches.length) {
                this.touchStartX = event.changedTouches[0].clientX;
            }
        },

        // 触摸结束
        onTouchEnd(event) {
            if (event.changedTouches && event.changedTouches.length) {
                const endX = event.changedTouches[0].clientX;
                const diffX = endX - this.touchStartX;
                if (Math.abs(diffX) > 50) {
                    this.changeWeek(diffX < 0 ? 1 : -1);
                }
            }
        },

        // 获取某天某节的课程列表（仅返回 period 起始节匹配的课程，避免重复渲染）
        getCoursesByDayPeriod(day, period) {
            return this.filteredCourses.filter(course =>
                Number(course.day_of_week) === day && Number(course.period) === period
            );
        },

        // 计算课程跨越的节数（用于 CSS grid-row span）
        getCourseSpan(course) {
            const start = Number(course.period) || 1;
            const end = Number(course.period_end) || start;
            return end - start + 1;
        },

        // 判断某个格子是否被上方课程的跨行占据（用于隐藏被覆盖的格子）
        isOccupied(day, period) {
            return this.filteredCourses.some(course => {
                const cDay = Number(course.day_of_week);
                const cStart = Number(course.period);
                const cEnd = Number(course.period_end) || cStart;
                return cDay === day && period > cStart && period <= cEnd;
            });
        },

        // 课程颜色（根据课程名生成稳定颜色，使用浅底+深字方案）
        getCourseColor(name) {
            let hash = 0;
            for (let i = 0; i < name.length; i++) {
                hash = name.charCodeAt(i) + ((hash << 5) - hash);
            }
            const idx = Math.abs(hash) % this.courseColors.length;
            return this.courseColors[idx];
        },

        // 加载所有课程
        async loadCourses() {
            try {
                const response = await fetch('/api/courses');
                if (response.status === 401) {
                    window.location.href = '/login';
                    return;
                }
                this.courses = await response.json();
            } catch (error) {
                console.error('加载课程失败:', error);
                alert('加载课程失败，请刷新页面重试');
            }
        },

        // 加载所有作业
        async loadAssignments() {
            try {
                const response = await fetch('/api/assignments');
                if (response.status === 401) {
                    window.location.href = '/login';
                    return;
                }
                this.assignments = await response.json();
            } catch (error) {
                console.error('加载作业失败:', error);
                alert('加载作业失败，请刷新页面重试');
            }
        },

        // 添加课程
        async addCourse() {
            try {
                const response = await fetch('/api/courses', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(this.newCourse)
                });

                if (response.ok) {
                    alert('课程添加成功！');
                    this.showAddCourseForm = false;
                    // 重置表单
                    this.newCourse = {
                        course_name: '',
                        location: '',
                        teacher: '',
                        day_of_week: '',
                        period: ''
                    };
                    // 重新加载课程列表
                    await this.loadCourses();
                } else {
                    alert('添加课程失败，请重试');
                }
            } catch (error) {
                console.error('添加课程失败:', error);
                alert('添加课程失败，请重试');
            }
        },

        // 删除课程
        async deleteCourse(courseId) {
            if (!confirm('确定要删除这门课程吗？相关作业也会被删除。')) {
                return;
            }

            try {
                const response = await fetch(`/api/courses/${courseId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    alert('课程删除成功！');
                    await this.loadCourses();
                    await this.loadAssignments(); // 重新加载作业列表
                } else {
                    alert('删除课程失败，请重试');
                }
            } catch (error) {
                console.error('删除课程失败:', error);
                alert('删除课程失败，请重试');
            }
        },

        // 添加作业
        async addAssignment() {
            try {
                const response = await fetch('/api/assignments', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(this.newAssignment)
                });

                if (response.ok) {
                    alert('作业添加成功！');
                    this.showAddAssignmentForm = false;
                    // 重置表单
                    this.newAssignment = {
                        assignment_name: '',
                        description: '',
                        course_id: '',
                        due_date: ''
                    };
                    // 重新加载作业列表
                    await this.loadAssignments();
                } else {
                    alert('添加作业失败，请重试');
                }
            } catch (error) {
                console.error('添加作业失败:', error);
                alert('添加作业失败，请重试');
            }
        },

        // 切换作业完成状态
        async toggleComplete(assignment) {
            try {
                const response = await fetch(`/api/assignments/${assignment.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        is_completed: !assignment.is_completed
                    })
                });

                if (response.ok) {
                    // 重新加载作业列表
                    await this.loadAssignments();
                } else {
                    alert('更新作业状态失败，请重试');
                }
            } catch (error) {
                console.error('更新作业状态失败:', error);
                alert('更新作业状态失败，请重试');
            }
        },

        // 删除作业
        async deleteAssignment(assignmentId) {
            if (!confirm('确定要删除这个作业吗?')) {
                return;
            }

            try {
                const response = await fetch(`/api/assignments/${assignmentId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    alert('作业删除成功！');
                    await this.loadAssignments();
                } else {
                    alert('删除作业失败，请重试');
                }
            } catch (error) {
                console.error('删除作业失败:', error);
                alert('删除作业失败，请重试');
            }
        },

        // PDF 文件选择
        onPDFSelected(event) {
            const file = event.target.files[0];
            if (file && file.type === 'application/pdf') {
                this.selectedPDF = file;
            } else if (file) {
                alert('请选择 PDF 格式的文件');
                event.target.value = '';
            }
        },

        // PDF 拖拽放置
        onDropPDF(event) {
            const file = event.dataTransfer.files[0];
            if (file && file.type === 'application/pdf') {
                this.selectedPDF = file;
            } else {
                alert('请拖入 PDF 格式的文件');
            }
        },

        // 关闭上传模态框
        closeUploadModal() {
            this.showUploadForm = false;
            this.selectedPDF = null;
            if (this.$refs.pdfInput) {
                this.$refs.pdfInput.value = '';
            }
        },

        // 上传 PDF 课表
        async uploadSchedulePDF() {
            if (!this.selectedPDF) {
                alert('请先选择 PDF 文件');
                return;
            }

            this.uploading = true;

            try {
                const formData = new FormData();
                formData.append('file', this.selectedPDF);
                formData.append('clear_old', this.uploadClearOld);

                const response = await fetch('/api/upload_schedule', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    alert(result.message);
                    this.showUploadForm = false;
                    this.selectedPDF = null;
                    this.uploadClearOld = false;
                    await this.loadCourses();
                } else {
                    alert('导入失败：' + (result.error || '未知错误'));
                }
            } catch (error) {
                console.error('上传PDF课表失败:', error);
                alert('上传失败，请检查网络连接后重试');
            } finally {
                this.uploading = false;
            }
        },

        // 从教务系统导入课表
        async importSchedule() {
            // 开启加载状态
            this.importing = true;

            try {
                const response = await fetch('/api/import_schedule', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username: this.importForm.username,
                        password: this.importForm.password,
                        clear_old: this.importForm.clear_old
                    })
                });

                const result = await response.json();

                if (response.ok) {
                    alert(result.message);
                    this.showImportForm = false;
                    // 清空表单
                    this.importForm = { username: '', password: '', clear_old: false };
                    // 刷新课程列表
                    await this.loadCourses();
                } else {
                    // 显示后端返回的错误信息
                    alert('导入失败：' + (result.error || '未知错误'));
                }
            } catch (error) {
                console.error('导入课表失败:', error);
                alert('导入课表失败，请检查网络连接后重试');
            } finally {
                // 无论成功失败都关闭加载状态
                this.importing = false;
            }
        }
    },
    mounted() {
        // 页面加载时获取数据
        this.loadCurrentUser();
        this.loadCourses();
        this.loadAssignments();
    }
}).mount('#app');
// 注册 Service Worker 以支持 PWA 离线缓存和安装功能
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        // 从根路径注册 SW，使其作用域覆盖整个站点
        navigator.serviceWorker.register('/sw.js', { scope: '/' })
            .then(reg => {
                console.log('Service Worker 注册成功，作用域为: ', reg.scope);
            })
            .catch(err => {
                console.log('Service Worker 注册失败: ', err);
            });
    });
}