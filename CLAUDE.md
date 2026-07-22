# 乒小Yo — 乒乓球动作分析 + 约球社交平台

## 项目概述
基于 FastAPI + Vue3 的乒乓球综合平台，融合两个子系统：

1. **动作分析** — 用户选择正反手/上下旋类型并上传视频，经 PaddleVideo BMN 做时序切割，MediaPipe 提取骨骼关键点，与马龙/樊振东标准模板做 DTW 对比，输出结构化 JSON 分析报告。
2. **约球社交** — 邮箱注册登录、附近球友发现、好友系统、实时聊天。

## 项目结构
```
pingpong/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── main.py             # 入口，挂载所有路由 + WebSocket + 静态文件
│   │   ├── config.py           # 全局配置（路径、帧率、CUDA 设备等）
│   │   ├── database.py         # SQLAlchemy 引擎 + MySQL 连接
│   │   ├── api/
│   │   │   ├── router.py       # POST /api/analyze (动作分析)
│   │   │   ├── auth.py         # 注册/登录/验证码/退出
│   │   │   ├── user.py         # 用户信息/位置/设置
│   │   │   ├── player.py       # 附近球友/球友详情
│   │   │   ├── friend.py       # 好友请求/列表/管理
│   │   │   ├── chat.py         # 聊天消息/会话列表
│   │   │   ├── upload.py       # 图片上传（本地存储）
│   │   │   ├── ws.py           # WebSocket 实时聊天
│   │   │   └── deps.py         # JWT 认证依赖
│   │   ├── models/
│   │   │   ├── schemas.py      # Pydantic 分析报告模型
│   │   │   └── db.py           # SQLAlchemy 模型（User/Chat/Friend 等）
│   │   └── services/           # 动作分析服务
│   │       ├── video_preprocessor.py   # FFmpeg 720P/10fps 压缩
│   │       ├── paddle_infer.py         # BMN 时序动作检测
│   │       ├── mediapipe_extractor.py  # MediaPipe Pose 骨骼提取
│   │       ├── comparator.py           # DTW 相似度 + 6 项指标计算
│   │       ├── report_generator.py     # 阈值匹配 + 教练文案
│   │       └── pipeline.py             # 全流程编排器
│   ├── config/
│   │   ├── thresholds.yaml            # 评分阈值（good/fair/poor）
│   │   └── report_templates.yaml      # 问题描述与建议文案
│   ├── scripts/
│   │   └── generate_templates.py      # 离线模板生成脚本
│   ├── uploads/                # 本地图片上传目录
│   └── requirements.txt
│
├── frontend/                   # Vue3 前端
│   ├── src/
│   │   ├── App.vue             # 根组件（登录检查 + router-view）
│   │   ├── main.js             # 入口（挂载 Pinia + Router）
│   │   ├── router/
│   │   │   └── index.js        # 路由配置（底部 4 Tab + 子页面）
│   │   ├── stores/
│   │   │   └── user.js         # Pinia 用户状态
│   │   ├── api/
│   │   │   ├── index.js        # 统一导出
│   │   │   ├── request.js      # Axios 封装（拦截器 + 统一错误处理）
│   │   │   ├── auth.js         # 认证 API
│   │   │   ├── user.js         # 用户 API
│   │   │   ├── player.js       # 球友 API
│   │   │   ├── friend.js       # 好友 API
│   │   │   ├── chat.js         # 聊天 API
│   │   │   └── analysis.js     # 动作分析 API
│   │   ├── utils/
│   │   │   ├── websocket.js    # WebSocket 管理
│   │   │   └── ui.js           # Toast/Loading/Modal/图标
│   │   ├── pages/
│   │   │   ├── Home.vue        # Tab1-首页（附近球友列表+筛选）
│   │   │   ├── Message.vue     # Tab2-消息（会话列表）
│   │   │   ├── Analysis.vue    # Tab3-动作分析（上传+对比+报告）
│   │   │   ├── Profile.vue     # Tab4-我的（资料+菜单）
│   │   │   ├── Login.vue       # 邮箱登录
│   │   │   ├── Register.vue    # 邮箱注册（验证码）
│   │   │   ├── PlayerDetail.vue# 球友详情
│   │   │   ├── Chat.vue        # 实时聊天
│   │   │   ├── EditProfile.vue # 编辑资料
│   │   │   ├── Friends.vue     # 球友列表/好友请求
│   │   │   └── Settings.vue    # 通知设置
│   │   └── components/
│   │       ├── TabBar.vue          # 底部导航栏
│   │       ├── VideoUpload.vue     # 拖拽上传
│   │       ├── AnalysisReport.vue  # 评分展示
│   │       └── ComparisonPlayer.vue# 左右对比播放器
│   ├── package.json
│   └── vite.config.js          # 端口 3000，代理 /api → :8000
│
└── pingyo/                     # 原 uniapp 项目（保留参考）
```

## 架构要点
### 动作分析
- **处理流水线**: 预处理 → BMN 时序切割 → MediaPipe 骨骼提取 → DTW 对比模板 → JSON 报告
- **用户选择动作类型**: 前端 4 选 1（正手/反手 × 上旋/下旋），直接决定对比哪个模板
- **BMN 已集成真实推理**（ResNet50 特征 + BMN 后处理），权重文件不存在时自动 fallback
- **MediaPipe 在 CPU 独立运行**（Task API PoseLandmarker，需 `app/models/pose_landmarker_lite.task`）
- **6 项量化指标**: 肘关节夹角、引拍高度、转腰髋偏移、重心起伏、挥拍轨迹范围、挥拍加速度
- **假设右手持拍**: 关键点计算使用右臂

### 约球社交
- **认证**: 邮箱注册/登录，邮箱验证码
- **附近球友**: 按距离/性别/年龄/球龄/打法筛选
- **好友系统**: 发送/接受/拒绝好友请求
- **实时聊天**: WebSocket 双向通信，消息持久化到 MySQL
- **图片上传**: 本地存储（替换阿里云 OSS）

### 数据库
- **MySQL**（配置见 `backend/app/database.py`）
- **表**: users, user_tokens, friend_requests, friends, chat_messages, user_settings, verify_codes

## 运行方式
```bash
# 后端
cd backend
pip install -r requirements.txt
python -m app.main          # http://localhost:8000

# 前端
cd frontend
npm install
npm run dev                 # http://localhost:3000
```

## 首次使用前
1. 确保 MySQL 运行，执行 `database/init.sql` 建表
2. 使用 `scripts/generate_templates.py` 生成动作模板
3. 前端访问 http://localhost:3000，注册账号后即可使用

## 环境依赖
- Python 3.10+
- FFmpeg（需加入 PATH）
- MySQL 8.0+
- Node.js 18+
- CUDA 11.8 + PaddlePaddle GPU（可选，用于加速）

## 编码约束
1. **编码前先思考** — 不确定时先确认，不自行假设
2. **优先保持简洁** — 最少代码实现目标，不做推测式设计
3. **精准修改代码** — 只改必需代码，不重构无关代码
4. **目标驱动执行** — 先定义验证标准，确保测试通过
