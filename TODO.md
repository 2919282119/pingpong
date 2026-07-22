# 开发进度

## ✅ 已完成 — 动作分析

- [x] **项目骨架 + 配置层**
  - FastAPI 入口（main.py）、CORS 中间件
  - 全局配置（config.py）、Pydantic 模型（schemas.py）
  - 评分阈值（thresholds.yaml）、教练文案（report_templates.yaml）
- [x] **视频预处理服务** — FFmpeg 压缩 720P/10fps
- [x] **BMN 时序检测服务** — 真实推理（权重不存在时 fallback 占位）
- [x] **MediaPipe 骨骼提取** — 逐帧 33 关键点 + NaN 插值（CPU）
- [x] **对比分析引擎**
  - 三点关节夹角计算
  - fastDTW 归一化相似度（位置 60% + 加速度 40%）
  - 6 项指标（肘角、引拍高度、转腰髋偏移、重心起伏、挥拍轨迹、挥拍加速度）
- [x] **异步任务队列** — threading.Thread + 轮询
- [x] **报告生成器 + 全流程编排**
- [x] **Vue3 前端（动作分析）** — 上传、对比播放器、评分展示、历史记录
- [x] **离线模板生成脚本**（scripts/generate_templates.py）
- [x] **生成 4 类动作模板** — `backend/templates/template_{fore,back}_{top,under}spin.npy`
- [x] **架构变更: 去掉 Swin 分类器** — 用户手动选择动作类型

## ✅ 已完成 — 约球社交合并

- [x] **后端依赖** — SQLAlchemy + PyMySQL + PyJWT + bcrypt
- [x] **数据库模型** — User、UserToken、FriendRequest、Friend、ChatMessage、UserSettings、VerifyCode
- [x] **初始化数据库** — 8 张表已创建（users, friends, chat_messages 等）
- [x] **后端工具模块** — JWT 认证、邮箱验证码、Haversine 距离
- [x] **认证 API** — 邮箱注册/登录、验证码发送、退出
- [x] **用户 API** — 个人信息 CRUD、位置更新、通知设置
- [x] **球友 API** — 附近球友搜索（距离/性别/年龄/球龄/打法）、球友详情
- [x] **好友 API** — 好友请求/接受/拒绝、好友列表
- [x] **聊天 API** — 消息列表/发送/会话、WebSocket 实时通信
- [x] **上传 API** — 本地图片存储（替代阿里云 OSS）
- [x] **Vue3 前端迁移**
  - 底部 4 Tab 导航（首页、消息、分析、我的）
  - 登录/注册页面（邮箱 + 验证码）
  - 首页：附近球友列表 + 筛选（性别/打法/距离）
  - 消息：会话列表 + 未读计数
  - 动作分析页面迁移到 Tab3
  - 个人中心：资料展示、编辑资料、球友管理、设置
  - 球友详情、实时聊天、编辑资料、好友管理、通知设置
- [x] **图片上传压缩** — Canvas API 压缩大图 1920px/85% JPEG
- [x] **聊天清空消息软删除** — `deletedBy` 字段记录删除用户，仅自己删除
- [x] **登录持久化** — localStorage 缓存 token + userInfo，后端不可用时保留登录态
- [x] **密码错误不清空表单** — 401 拦截器排除登录页

## ✅ 已完成 — 部署与优化

- [x] **Nginx 生产部署** — 静态资源托管 + gzip + 缓存策略
- [x] **Nginx WebSocket 代理** — 聊天 WebSocket 支持
- [x] **Nginx 上传大小限制** — `client_max_body_size 500m`
- [x] **前端 build 部署到 nginx（端口 3000）**，停止 dev server（端口 3001）

## ✅ 已完成 — GPU 加速

- [x] **Paddle 2.6.2 + paddle2onnx 1.3.1 导出 ONNX**（ResNet50 + BMN）
- [x] **ONNX Runtime GPU 推理** — CUDA 12.9 + cuDNN 9
- [x] **自动切换** — ONNX 模型存在时 GPU，否则回退 Paddle CPU
- [x] **已验证通过** — Paddle CPU vs ONNX GPU 输出一致（误差 < 1e-5）

## ✅ 已完成 — 定位与地图

- [x] **百度地图 API 集成**（后端 Web 服务） — 逆地理编码坐标→地址
- [x] **浏览器定位** — `navigator.geolocation` 获取位置
- [x] **登录/注册自动获取定位** — Pinia store action 中触发，保存到数据库
- [x] **首页定位初始化** — 使用已存坐标作为初始值，定位返回后自动刷新列表
- [x] **定位结果 Toast 提示** — 成功/失败/未授权均有提示

## ✅ 已完成 — UI 完善

- [x] **消息红点徽标修正** — Friends.vue、Message.vue 改为正圆
- [x] **好友请求移入消息页** — 消息页双 Tab：消息 / 好友请求（含未读数）
- [x] **聊天头像可点击** — 跳转到球友详情页

## 📝 待完成

- [ ] **阈值/文案调优** — 根据实测微调 `config/*.yaml`
- [ ] **BMN 置信度阈值调优**
- [ ] **骨架动画对比可视化** — 叠加骨骼线到对比播放器
- [ ] **约球邀请 UI** — 数据库已有 invitations 表，待实现前端界面
- [ ] **DTW 对比改进实现** — 右臂相对向量特征方案
- [ ] **IP 定位降级** — 浏览器定位失败时通过 IP 获取城市级位置
- [ ] **验证 ONNX GPU 推理精度**（已通过一致测试，待实机验证）
