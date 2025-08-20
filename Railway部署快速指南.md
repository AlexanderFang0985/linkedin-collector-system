# Railway部署快速指南 - LinkedIn智能挖掘系统

## 🎯 部署目标
将已完成开发的LinkedIn智能挖掘系统部署到Railway云平台，实现生产环境运行，并与已部署的n8n系统集成。

## 🔗 现有n8n环境
- **平台**：Railway云平台（已部署运行）
- **版本**：n8n 1.106.3
- **部署方式**：Docker容器
- **状态**：稳定运行中
- **集成优势**：同平台部署，网络延迟最小，便于统一管理

## 📋 部署前检查清单

### ✅ 项目文件准备完毕
- [x] app.py - Flask主应用
- [x] requirements.txt - 依赖配置
- [x] Procfile - Railway部署配置
- [x] railway.toml - Railway项目配置
- [x] templates/ - HTML模板
- [x] static/ - 静态资源
- [x] README.md - 项目文档

### 🔧 需要准备的外部服务

#### 1. Google Cloud服务账号
**目的**：用于Google Sheets API访问
**步骤**：
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用Google Sheets API
4. 创建服务账号
5. 下载JSON密钥文件
6. 记录服务账号邮箱地址

#### 2. Google Sheets表格
**目的**：存储LinkedIn链接和处理状态
**步骤**：
1. 创建新的Google Sheets表格
2. 设置表头：`邮箱地址 | LinkedIn链接 | 提交时间 | 处理状态`
3. 将服务账号邮箱添加为编辑者
4. 复制表格ID（URL中的长字符串）

#### 3. QQ邮箱SMTP配置
**目的**：发送验证码邮件
**步骤**：
1. 登录QQ邮箱
2. 设置 → 账户 → 开启SMTP服务
3. 生成授权码（16位字符）
4. 记录QQ邮箱地址和授权码

## 🚀 Railway部署步骤

### 方法一：GitHub连接部署（推荐）

#### 步骤1：准备GitHub仓库
```bash
# 初始化Git仓库
git init
git add .
git commit -m "Initial commit: LinkedIn智能挖掘系统"

# 推送到GitHub
git remote add origin https://github.com/your-username/linkedin-collector-system.git
git push -u origin main
```

#### 步骤2：Railway部署
1. 访问 [Railway.app](https://railway.app/)
2. 使用GitHub账号登录
3. 点击 "New Project"
4. 选择 "Deploy from GitHub repo"
5. 选择 linkedin-collector-system 仓库
6. Railway会自动检测Flask应用并开始部署

#### 步骤3：配置环境变量
在Railway项目设置中添加以下环境变量：

```bash
# Flask应用密钥（生成一个随机字符串）
SECRET_KEY=your-random-secret-key-here-make-it-long-and-complex

# QQ邮箱配置
QQ_EMAIL=your-qq-email@qq.com
QQ_PASSWORD=your-16-digit-qq-auth-code

# Google Sheets配置
GOOGLE_SHEETS_ID=your-google-sheets-id-from-url
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"your-project",...}
```

### 方法二：Railway CLI部署

#### 步骤1：安装Railway CLI
```bash
# 使用npm安装
npm install -g @railway/cli

# 或使用curl安装
curl -fsSL https://railway.app/install.sh | sh
```

#### 步骤2：登录和部署
```bash
# 登录Railway
railway login

# 在项目目录中初始化
railway init

# 设置环境变量
railway variables set SECRET_KEY="your-secret-key"
railway variables set QQ_EMAIL="your-qq-email@qq.com"
railway variables set QQ_PASSWORD="your-qq-auth-code"
railway variables set GOOGLE_SHEETS_ID="your-sheets-id"
railway variables set GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'

# 部署应用
railway up
```

## 🔧 环境变量详细说明

### SECRET_KEY
- **用途**：Flask会话加密
- **生成方法**：
```python
import secrets
print(secrets.token_hex(32))
```

### QQ_EMAIL 和 QQ_PASSWORD
- **QQ_EMAIL**：您的QQ邮箱地址
- **QQ_PASSWORD**：QQ邮箱授权码（不是QQ密码）
- **获取授权码**：QQ邮箱设置 → 账户 → SMTP服务

### GOOGLE_SHEETS_ID
- **获取方法**：从Google Sheets URL提取
- **URL格式**：`https://docs.google.com/spreadsheets/d/{SHEETS_ID}/edit`

### GOOGLE_CREDENTIALS_JSON
- **格式**：完整的JSON服务账号密钥
- **示例**：
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "service-account@project.iam.gserviceaccount.com",
  "client_id": "client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

## ✅ 部署验证

### 1. 检查部署状态
- Railway控制台显示 "Active" 状态
- 应用日志无错误信息
- 获得公网访问URL

### 2. 功能测试
1. **访问登录页面**：确认页面正常加载
2. **邮箱验证**：测试验证码发送和接收
3. **表单提交**：测试LinkedIn链接提交
4. **数据存储**：检查Google Sheets是否正确写入数据

### 3. n8n集成验证
1. **数据连通性**：确认n8n可以读取Google Sheets中的新数据
2. **网络连接**：验证LinkedIn系统和n8n之间的网络通信
3. **工作流测试**：创建简单的测试工作流验证集成效果
4. **同平台优势**：确认Railway内部网络通信正常

### 3. 性能检查
- 页面加载速度 < 3秒
- 验证码发送 < 5秒
- 表单提交响应 < 5秒

## 🚨 常见问题解决

### 部署失败
- 检查requirements.txt是否包含所有依赖
- 确认Procfile格式正确
- 查看Railway部署日志

### 验证码发送失败
- 确认QQ邮箱SMTP已开启
- 检查QQ_PASSWORD是否为授权码
- 验证QQ_EMAIL格式正确

### Google Sheets写入失败
- 确认服务账号有表格编辑权限
- 检查GOOGLE_SHEETS_ID是否正确
- 验证JSON格式是否有效

### 应用无法访问
- 检查Railway域名是否正确
- 确认应用状态为Active
- 查看应用日志排查错误

## 🔗 n8n集成后续步骤

### 部署完成后的n8n配置
1. **访问n8n界面**：使用Railway提供的n8n访问URL
2. **配置Google Sheets连接**：
   - 添加Google Sheets节点
   - 使用相同的服务账号凭证
   - 连接到LinkedIn系统使用的同一个表格

3. **创建基础工作流**：
   ```
   定时触发 → 读取Google Sheets → 过滤待处理记录 → 处理LinkedIn数据 → 更新状态
   ```

4. **测试集成效果**：
   - 在LinkedIn系统提交测试数据
   - 验证n8n工作流是否能正确读取和处理

### Railway平台集成优势
- **内网通信**：同平台服务间通信速度更快
- **统一监控**：在同一个控制台监控所有服务
- **环境一致性**：共享相同的网络和安全配置
- **成本效益**：避免跨平台数据传输费用

## 📞 技术支持
如遇到问题，请检查：
1. Railway部署日志
2. 环境变量配置
3. 外部服务权限设置
4. 网络连接状态
5. n8n工作流配置

---
**预计部署时间**：30-60分钟（不含n8n工作流配置）
**技术难度**：中等
**成功率**：按步骤操作成功率 > 95%
**集成优势**：同平台部署，集成更简单高效
