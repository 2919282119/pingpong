# 乒小Yo (PingXiaoYo) — 乒乓球动作分析 + 约球社交平台

基于 FastAPI + Vue3 的乒乓球综合平台，融合 AI 动作分析与约球社交两大子系统。

## 功能概览

### 🏓 动作分析
用户选择击球类型（正手/反手 × 上旋/下旋）并上传视频，系统经由 AI 流水线处理后输出结构化分析报告：

1. **视频预处理** — FFmpeg 压缩至 720p / 10fps
2. **时序动作检测** — BMN (Boundary-Matching Network) 定位视频中的击球片段，支持 ONNX GPU 加速与 PaddlePaddle CPU fallback
3. **骨骼关键点提取** — MediaPipe Pose 提取 33 个人体骨骼关键点
4. **DTW 对比** — 与马龙/樊振东标准动作模板做动态时间规整 (Dynamic Time Warping) 相似度计算
5. **6 项量化指标**：
   - 肘关节夹角 — 右手肘部最大展开角度
   - 引拍高度 — 手腕相对肩部的最高位置
   - 转腰髋偏移 — 髋部与肩部的水平偏移量
   - 重心起伏 — 髋部中心点的垂直稳定性
   - 挥拍轨迹范围 — 手腕运动轨迹的凸包面积
   - 挥拍速度 — 手腕最大加速度
6. **报告生成** — 阈值匹配打分 + 教练级中文问题描述与改进建议

### 🤝 约球社交
- 邮箱注册 / 登录（验证码）
- 附近球友发现（按距离、性别、年龄、球龄、打法筛选）
- 好友系统（发送/接受/拒绝请求）
- 实时聊天（WebSocket 双向通信，消息持久化到 MySQL）
- 个人资料编辑与头像上传

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python 3.10+) |
| 前端框架 | Vue 3 + Vite |
| 状态管理 | Pinia |
| 路由 | Vue Router 4 |
| HTTP 客户端 | Axios |
| 数据库 | MySQL 8.0+ (SQLAlchemy + PyMySQL) |
| 认证 | JWT (PyJWT + bcrypt) |
| 实时通信 | WebSocket |
| 动作检测 | PaddleVideo BMN / ONNX Runtime GPU |
| 骨骼提取 | MediaPipe Pose (CPU) |
| 相似度计算 | FastDTW (加权位置 60% + 加速度 40%) |
| 视频处理 | FFmpeg |

## 项目结构

```
pingpong/
├── backend/                          # FastAPI 后端
│   ├── app/
│   │   ├── main.py                   # 应用入口
│   │   ├── config.py                 # 全局配置
│   │   ├── database.py               # MySQL 连接
│   │   ├── api/
│   │   │   ├── router.py             # 动作分析 API
│   │   │   ├── auth.py               # 注册/登录/验证码
│   │   │   ├── user.py               # 用户信息
│   │   │   ├── player.py             # 附近球友
│   │   │   ├── friend.py             # 好友管理
│   │   │   ├── chat.py               # 聊天消息
│   │   │   ├── upload.py             # 图片上传
│   │   │   ├── ws.py                 # WebSocket 聊天
│   │   │   └── deps.py               # JWT 依赖
│   │   ├── models/
│   │   │   ├── schemas.py            # Pydantic 数据模型
│   │   │   └── db.py                 # ORM 模型
│   │   └── services/
│   │       ├── pipeline.py           # 分析流水线编排
│   │       ├── video_preprocessor.py # 视频压缩
│   │       ├── paddle_infer.py       # PaddlePaddle BMN 推理
│   │       ├── onnx_inference.py     # ONNX Runtime BMN 推理
│   │       ├── mediapipe_extractor.py# 骨骼关键点提取
│   │       ├── comparator.py         # DTW 相似度 + 指标计算
│   │       ├── report_generator.py   # 报告生成
│   │       └── analysis_manager.py   # 异步任务管理
│   ├── config/
│   │   ├── thresholds.yaml           # 评分阈值
│   │   └── report_templates.yaml     # 文案模板
│   ├── scripts/
│   │   └── generate_templates.py     # 离线模板生成
│   ├── templates/                    # 标准动作 .npy 模板
│   ├── requirements.txt
│   └── database/init.sql             # 建表 SQL
│
├── frontend/                         # Vue3 前端
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.vue              # 首页-附近球友
│   │   │   ├── Message.vue           # 消息-会话列表
│   │   │   ├── Analysis.vue          # 动作分析
│   │   │   ├── Profile.vue           # 个人中心
│   │   │   ├── Login.vue / Register.vue
│   │   │   ├── Chat.vue / PlayerDetail.vue
│   │   │   ├── Friends.vue / EditProfile.vue
│   │   │   └── Settings.vue
│   │   ├── components/
│   │   │   ├── TabBar.vue            # 底部导航
│   │   │   ├── VideoUpload.vue       # 拖拽上传
│   │   │   ├── AnalysisReport.vue    # 评分展示
│   │   │   └── ComparisonPlayer.vue  # 左右对比播放器
│   │   ├── stores/                   # Pinia 状态
│   │   ├── api/                      # Axios API 封装
│   │   └── utils/                    # WebSocket/UI 工具
│   ├── package.json
│   └── vite.config.js
│
└── pingyo/                           # 原 uniapp 项目（保留参考）
```

## 快速开始

### 环境依赖

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- FFmpeg（需加入 PATH）
- CUDA 11.8 + PaddlePaddle GPU（可选，用于加速 BMN 推理）

### 数据库初始化

```bash
mysql -u root -p < backend/database/init.sql
```

### 后端

```bash
cd backend
pip install -r requirements.txt
python -m app.main
# 服务启动在 http://localhost:8000
```

### 生成动作模板

放置 4 段标准动作视频到 `backend/scripts/input_videos/`：

| 文件 | 内容 |
|------|------|
| `fore_topspin.mp4` | 正手拉上旋（马龙） |
| `back_topspin.mp4` | 反手拉上旋（马龙） |
| `fore_underspin.mp4` | 正手起下旋（樊振东） |
| `back_underspin.mp4` | 反手起下旋（樊振东） |

```bash
cd backend
python scripts/generate_templates.py
```

### 前端

```bash
cd frontend
npm install
npm run dev
# 服务启动在 http://localhost:3000
```

## 配置

### 阈值配置 (`backend/config/thresholds.yaml`)

定义 6 项指标与 DTW 相似度的评分区间，分为 good / fair / poor 三档，输出对应分数。

### 报告文案 (`backend/config/report_templates.yaml`)

每项指标在各评分档位下的中文问题描述与改进建议。

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CUDA_VISIBLE_DEVICES` | CUDA 设备编号 | `0` |
| `BAIDU_MAP_AK` | 百度地图 API Key | 内置测试 Key |
| `PP_BMN_MODEL` | PaddleVideo BMN 模型路径 | `/models/paddlevideo/bmn/` |

## API 概览

### 动作分析

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/analyze` | 上传视频并启动分析，返回 task_id |
| `GET` | `/api/analyze/{task_id}` | 轮询分析进度与结果 |
| `GET` | `/api/analyze/history/list` | 获取历史记录 |
| `DELETE` | `/api/analyze/history` | 清除历史记录 |

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/auth/register` | 邮箱注册 |
| `POST` | `/api/auth/login` | 邮箱登录 |
| `POST` | `/api/auth/logout` | 退出登录 |
| `POST` | `/api/auth/send-code` | 发送验证码 |

### 社交

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/players` | 附近球友列表 |
| `GET` | `/api/players/{id}` | 球友详情 |
| `POST` | `/api/friends/request` | 发送好友请求 |
| `GET` | `/api/friends/requests` | 好友请求列表 |
| `POST` | `/api/friends/accept` | 接受好友请求 |
| `GET` | `/api/chat/conversations` | 会话列表 |
| `GET` | `/api/chat/messages/{userId}` | 聊天记录 |

### WebSocket

| 端点 | 说明 |
|------|------|
| `ws://host/ws` | 实时聊天（需发送 auth 消息认证） |

## 动作分析流水线

```
用户上传视频 → 预处理 (720p/10fps) → BMN 时序检测 → 击球片段裁剪
→ MediaPipe 骨骼提取 → DTW 对比模板 → 6 项指标计算 → 报告生成
```

- 假设 **右手持拍**，关键点计算使用右臂
- BMN 优先使用 ONNX Runtime GPU 加速，ONNX 模型不存在时自动 fallback 到 PaddlePaddle CPU

## 许可证

本项目仅供学习和参考。
