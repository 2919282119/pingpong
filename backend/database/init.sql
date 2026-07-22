-- 乒小Yo数据库初始化脚本
-- 数据库名: pingpong
-- 创建数据库
CREATE DATABASE IF NOT EXISTS `pingpong` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `pingpong`;

-- 1. 用户表
CREATE TABLE IF NOT EXISTS `users` (
  `id` VARCHAR(50) PRIMARY KEY COMMENT '用户ID',
  `openid` VARCHAR(100) UNIQUE COMMENT '微信OpenID',
  `unionid` VARCHAR(100) COMMENT '微信UnionID',
  `email` VARCHAR(100) UNIQUE COMMENT '邮箱',
  `password` VARCHAR(255) COMMENT '密码（加密后）',
  `name` VARCHAR(50) COMMENT '昵称',
  `avatar` VARCHAR(500) COMMENT '头像URL',
  `bgImg` VARCHAR(500) COMMENT '背景图URL',
  `gender` VARCHAR(10) COMMENT '性别：男/女',
  `birthdate` DATE COMMENT '出生日期',
  `startPlayingYear` VARCHAR(10) COMMENT '开始打球年份',
  `playStyle` VARCHAR(50) COMMENT '打法',
  `selfDescription` TEXT COMMENT '自我介绍',
  `address` VARCHAR(200) COMMENT '地址',
  `latitude` DECIMAL(10, 7) COMMENT '纬度',
  `longitude` DECIMAL(10, 7) COMMENT '经度',
  `online` TINYINT(1) DEFAULT 0 COMMENT '是否在线',
  `lastActiveTime` DATETIME COMMENT '最后活跃时间',
  `createdAt` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_openid` (`openid`),
  INDEX `idx_email` (`email`),
  INDEX `idx_location` (`latitude`, `longitude`),
  INDEX `idx_createdAt` (`createdAt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 2. 用户Token表（用于管理登录状态）
CREATE TABLE IF NOT EXISTS `user_tokens` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `userId` VARCHAR(50) NOT NULL COMMENT '用户ID',
  `token` VARCHAR(255) NOT NULL UNIQUE COMMENT '访问令牌',
  `expiresAt` DATETIME NOT NULL COMMENT '过期时间',
  `createdAt` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX `idx_userId` (`userId`),
  INDEX `idx_token` (`token`),
  INDEX `idx_expiresAt` (`expiresAt`),
  FOREIGN KEY (`userId`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户Token表';

-- 3. 好友请求表
CREATE TABLE IF NOT EXISTS `friend_requests` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `fromUserId` VARCHAR(50) NOT NULL COMMENT '发起请求的用户ID',
  `toUserId` VARCHAR(50) NOT NULL COMMENT '接收请求的用户ID',
  `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/accepted/rejected',
  `requestTime` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '请求时间',
  `handleTime` DATETIME COMMENT '处理时间',
  `createdAt` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_fromUserId` (`fromUserId`),
  INDEX `idx_toUserId` (`toUserId`),
  INDEX `idx_status` (`status`),
  UNIQUE KEY `uk_from_to` (`fromUserId`, `toUserId`),
  FOREIGN KEY (`fromUserId`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`toUserId`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='好友请求表';

-- 4. 好友关系表
CREATE TABLE IF NOT EXISTS `friends` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `userId1` VARCHAR(50) NOT NULL COMMENT '用户1 ID',
  `userId2` VARCHAR(50) NOT NULL COMMENT '用户2 ID',
  `createdAt` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '成为好友时间',
  INDEX `idx_userId1` (`userId1`),
  INDEX `idx_userId2` (`userId2`),
  UNIQUE KEY `uk_users` (`userId1`, `userId2`),
  FOREIGN KEY (`userId1`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`userId2`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='好友关系表';

-- 5. 约球邀请表
CREATE TABLE IF NOT EXISTS `invitations` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `fromUserId` VARCHAR(50) NOT NULL COMMENT '发起邀请的用户ID',
  `toUserId` VARCHAR(50) NOT NULL COMMENT '接收邀请的用户ID',
  `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/accepted/rejected',
  `inviteTime` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '邀请时间',
  `acceptTime` DATETIME COMMENT '接受时间',
  `rejectTime` DATETIME COMMENT '拒绝时间',
  `isRead` TINYINT(1) DEFAULT 0 COMMENT '是否已读',
  `createdAt` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_fromUserId` (`fromUserId`),
  INDEX `idx_toUserId` (`toUserId`),
  INDEX `idx_status` (`status`),
  INDEX `idx_isRead` (`isRead`),
  FOREIGN KEY (`fromUserId`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`toUserId`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='约球邀请表';

-- 6. 聊天消息表
CREATE TABLE IF NOT EXISTS `chat_messages` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `fromUserId` VARCHAR(50) NOT NULL COMMENT '发送者用户ID',
  `toUserId` VARCHAR(50) NOT NULL COMMENT '接收者用户ID',
  `content` TEXT NOT NULL COMMENT '消息内容',
  `isRead` TINYINT(1) DEFAULT 0 COMMENT '是否已读',
  `createTime` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX `idx_fromUserId` (`fromUserId`),
  INDEX `idx_toUserId` (`toUserId`),
  INDEX `idx_createTime` (`createTime`),
  INDEX `idx_conversation` (`fromUserId`, `toUserId`, `createTime`),
  FOREIGN KEY (`fromUserId`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`toUserId`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天消息表';

-- 7. 用户设置表
CREATE TABLE IF NOT EXISTS `user_settings` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `userId` VARCHAR(50) NOT NULL UNIQUE COMMENT '用户ID',
  `inviteNotification` TINYINT(1) DEFAULT 1 COMMENT '约球通知开关',
  `messageNotification` TINYINT(1) DEFAULT 1 COMMENT '消息通知开关',
  `createdAt` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_userId` (`userId`),
  FOREIGN KEY (`userId`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户设置表';

-- 8. 验证码表（用于注册和找回密码）
CREATE TABLE IF NOT EXISTS `verify_codes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `email` VARCHAR(100) NOT NULL COMMENT '邮箱',
  `code` VARCHAR(10) NOT NULL COMMENT '验证码',
  `type` VARCHAR(20) DEFAULT 'register' COMMENT '类型：register/login/forgot',
  `expiresAt` DATETIME NOT NULL COMMENT '过期时间',
  `used` TINYINT(1) DEFAULT 0 COMMENT '是否已使用',
  `createdAt` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX `idx_email` (`email`),
  INDEX `idx_expiresAt` (`expiresAt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='验证码表';

