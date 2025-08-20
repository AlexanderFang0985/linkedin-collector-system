# LinkedIn智能挖掘系统

专业的外贸客户联系方式挖掘平台，通过LinkedIn链接智能分析目标客户信息，自动查找联系方式，助力外贸业务拓展。

## 功能特性

- 🎯 **精准定位**: 通过LinkedIn链接智能分析目标客户信息
- 📧 **联系方式挖掘**: 自动查找邮箱、电话等关键联系信息
- 🔍 **深度分析**: 挖掘职业背景、公司信息、行业关系
- ⚡ **批量处理**: 支持同时处理多个目标客户，提升工作效率
- 📊 **数据整理**: 自动整理并导出客户信息，便于后续跟进
- 🔐 **安全登录**: QQ邮箱验证码登录系统
- 🚀 **云端部署**: 支持Railway平台一键部署
- 🔗 **n8n集成**: 可与n8n工作流无缝集成

## 技术栈

- **后端**: Python Flask
- **前端**: HTML5 + CSS3 + JavaScript
- **邮件服务**: QQ邮箱SMTP
- **数据存储**: Google Sheets API
- **部署平台**: Railway

## 快速开始

### 1. 环境准备

确保您已安装Python 3.8+和pip包管理器。

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 环境变量配置

在Railway部署时，需要配置以下环境变量：

```bash
# Flask应用密钥
SECRET_KEY=your-flask-secret-key-here

# QQ邮箱配置
QQ_EMAIL=your-qq-email@qq.com
QQ_PASSWORD=your-qq-auth-code

# Google Sheets配置
GOOGLE_SHEETS_ID=your-google-sheets-id
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}

# 可选：如果使用文件方式
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json
```

### 4. Google Sheets设置

1. 创建Google Sheets表格
2. 设置表头：`邮箱地址 | LinkedIn链接 | 提交时间 | 处理状态`
3. 创建Google Cloud服务账号
4. 下载服务账号JSON文件
5. 将服务账号邮箱添加到表格编辑权限

### 5. QQ邮箱配置

1. 登录QQ邮箱
2. 设置 → 账户 → 开启SMTP服务
3. 获取授权码（不是QQ密码）
4. 将授权码设置为`QQ_PASSWORD`环境变量

## Railway部署指南

### 方法一：GitHub连接部署

1. 将代码推送到GitHub仓库
2. 登录Railway控制台
3. 选择"Deploy from GitHub repo"
4. 连接您的GitHub仓库
5. 配置环境变量
6. 点击部署

### 方法二：CLI部署

```bash
# 安装Railway CLI
npm install -g @railway/cli

# 登录Railway
railway login

# 初始化项目
railway init

# 部署应用
railway up
```

### 环境变量配置

在Railway项目设置中添加以下环境变量：

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `SECRET_KEY` | Flask应用密钥 | `your-secret-key-123` |
| `QQ_EMAIL` | QQ邮箱地址 | `example@qq.com` |
| `QQ_PASSWORD` | QQ邮箱授权码 | `abcdefghijklmnop` |
| `GOOGLE_SHEETS_ID` | Google表格ID | `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms` |
| `GOOGLE_CREDENTIALS_JSON` | 服务账号JSON | `{"type":"service_account",...}` |

## 本地开发

```bash
# 克隆项目
git clone <repository-url>
cd linkedin-collector

# 安装依赖
pip install -r requirements.txt

# 设置环境变量（创建.env文件）
export SECRET_KEY=your-secret-key
export QQ_EMAIL=your-qq-email@qq.com
export QQ_PASSWORD=your-qq-auth-code
export GOOGLE_SHEETS_ID=your-sheets-id
export GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'

# 运行应用
python app.py
```

访问 `http://localhost:5000` 查看应用。

## n8n集成

### 推荐工作流

1. **定时触发**: 使用Cron节点每5-10分钟触发一次
2. **读取数据**: 使用Google Sheets节点读取"待处理"状态的记录
3. **处理逻辑**: 根据LinkedIn链接执行相应的数据收集操作
4. **更新状态**: 将处理完成的记录状态更新为"已处理"

### 示例n8n节点配置

```json
{
  "nodes": [
    {
      "name": "定时触发",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "rule": {
          "interval": [{"field": "minute", "value": 10}]
        }
      }
    },
    {
      "name": "读取Google Sheets",
      "type": "n8n-nodes-base.googleSheets",
      "parameters": {
        "operation": "read",
        "sheetId": "your-sheet-id",
        "range": "A:D"
      }
    }
  ]
}
```

## 项目结构

```
linkedin-collector/
├── app.py                 # Flask主应用
├── requirements.txt       # Python依赖
├── Procfile              # Railway部署配置
├── railway.toml          # Railway项目配置
├── README.md             # 项目文档
├── templates/            # HTML模板
│   ├── login.html        # 登录页面
│   └── form.html         # 表单页面
└── static/               # 静态资源
    ├── style.css         # 样式文件
    └── script.js         # JavaScript文件
```

## 常见问题

### Q: 验证码收不到怎么办？
A: 检查QQ邮箱SMTP设置，确保授权码正确，检查垃圾邮件文件夹。

### Q: Google Sheets写入失败？
A: 确认服务账号有表格编辑权限，检查GOOGLE_SHEETS_ID是否正确。

### Q: Railway部署失败？
A: 检查环境变量配置，确保requirements.txt包含所有依赖。

### Q: 如何获取Google Sheets ID？
A: 从Google Sheets URL中提取：`https://docs.google.com/spreadsheets/d/{SHEETS_ID}/edit`

## 技术支持

如有问题，请检查：
1. 环境变量配置是否正确
2. Google API权限设置
3. QQ邮箱SMTP配置
4. Railway部署日志

## 许可证

本项目仅供学习和个人使用。
