import os
import re
import smtplib
import random
import string
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import gspread
from google.oauth2.service_account import Credentials

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-default-secret-key')

# 配置信息
QQ_EMAIL = os.environ.get('QQ_EMAIL')
QQ_PASSWORD = os.environ.get('QQ_PASSWORD')
GOOGLE_SHEETS_ID = os.environ.get('GOOGLE_SHEETS_ID')

# Google Sheets API配置
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_google_sheets_client():
    """获取Google Sheets客户端"""
    try:
        # 从环境变量获取服务账号凭据
        credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path and os.path.exists(credentials_path):
            credentials = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        else:
            # 如果没有文件路径，尝试从环境变量获取JSON内容
            credentials_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            if credentials_json:
                import json
                credentials_info = json.loads(credentials_json)
                credentials = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
            else:
                raise ValueError("未找到Google服务账号凭据")
        
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        logger.error(f"Google Sheets客户端初始化失败: {e}")
        return None

def send_verification_email(email, code):
    """发送验证码邮件"""
    try:
        msg = MIMEMultipart()
        msg['From'] = QQ_EMAIL
        msg['To'] = email
        msg['Subject'] = '外贸LinkedIn收集系统 - 验证码'
        
        body = f"""
        您好！
        
        您的验证码是：{code}
        
        验证码有效期为5分钟，请及时使用。
        
        如果您没有请求此验证码，请忽略此邮件。
        
        ---
        外贸LinkedIn信息收集系统
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.login(QQ_EMAIL, QQ_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"验证码邮件已发送至: {email}")
        return True
    except Exception as e:
        logger.error(f"发送邮件失败: {e}")
        return False

def generate_verification_code():
    """生成6位数字验证码"""
    return ''.join(random.choices(string.digits, k=6))

def validate_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_linkedin_url(url):
    """验证LinkedIn URL格式"""
    linkedin_patterns = [
        r'https?://(?:www\.)?linkedin\.com/in/[\w-]+/?',
        r'https?://(?:www\.)?linkedin\.com/pub/[\w-]+/[\w/]+/?',
        r'linkedin\.com/in/[\w-]+/?',
        r'linkedin\.com/pub/[\w-]+/[\w/]+/?'
    ]
    
    for pattern in linkedin_patterns:
        if re.match(pattern, url.strip()):
            return True
    return False

def normalize_linkedin_url(url):
    """标准化LinkedIn URL"""
    url = url.strip()
    if not url.startswith('http'):
        url = 'https://' + url
    return url

def write_to_google_sheets(email, linkedin_urls):
    """将数据写入Google Sheets"""
    try:
        client = get_google_sheets_client()
        if not client:
            return False, "Google Sheets客户端初始化失败"
        
        sheet = client.open_by_key(GOOGLE_SHEETS_ID).sheet1
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 处理多个LinkedIn URL
        urls = [url.strip() for url in linkedin_urls.split('\n') if url.strip()]
        
        rows_to_add = []
        for url in urls:
            if validate_linkedin_url(url):
                normalized_url = normalize_linkedin_url(url)
                rows_to_add.append([email, normalized_url, current_time, '待处理'])
            else:
                logger.warning(f"无效的LinkedIn URL: {url}")
        
        if rows_to_add:
            sheet.append_rows(rows_to_add)
            logger.info(f"成功写入 {len(rows_to_add)} 条记录到Google Sheets")
            return True, f"成功提交 {len(rows_to_add)} 个LinkedIn链接"
        else:
            return False, "没有有效的LinkedIn链接"
            
    except Exception as e:
        logger.error(f"写入Google Sheets失败: {e}")
        return False, f"数据保存失败: {str(e)}"

@app.route('/')
def index():
    """首页 - 重定向到登录页"""
    return redirect(url_for('login'))

@app.route('/login')
def login():
    """登录页面"""
    return render_template('login.html')

@app.route('/send_code', methods=['POST'])
def send_code():
    """发送验证码"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()

        if not email:
            return jsonify({'success': False, 'message': '请输入邮箱地址'})

        if not validate_email(email):
            return jsonify({'success': False, 'message': '邮箱格式不正确'})

        code = generate_verification_code()

        if send_verification_email(email, code):
            session['verification_code'] = code
            session['verification_email'] = email
            session['code_timestamp'] = datetime.now().timestamp()
            return jsonify({'success': True, 'message': '验证码已发送，请查收邮件'})
        else:
            return jsonify({'success': False, 'message': '验证码发送失败，请稍后重试'})

    except Exception as e:
        logger.error(f"发送验证码错误: {e}")
        return jsonify({'success': False, 'message': '系统错误，请稍后重试'})

@app.route('/verify_code', methods=['POST'])
def verify_code():
    """验证验证码"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        code = data.get('code', '').strip()
        
        if not email or not code:
            return jsonify({'success': False, 'message': '请输入邮箱和验证码'})
        
        # 检查验证码是否存在
        if 'verification_code' not in session:
            return jsonify({'success': False, 'message': '请先获取验证码'})
        
        # 检查邮箱是否匹配
        if session.get('verification_email') != email:
            return jsonify({'success': False, 'message': '邮箱不匹配'})
        
        # 检查验证码是否过期（5分钟）
        code_timestamp = session.get('code_timestamp', 0)
        if datetime.now().timestamp() - code_timestamp > 300:
            return jsonify({'success': False, 'message': '验证码已过期，请重新获取'})
        
        # 验证验证码
        if session.get('verification_code') == code:
            session['logged_in'] = True
            session['user_email'] = email
            # 清除验证码信息
            session.pop('verification_code', None)
            session.pop('verification_email', None)
            session.pop('code_timestamp', None)
            return jsonify({'success': True, 'message': '登录成功'})
        else:
            return jsonify({'success': False, 'message': '验证码错误'})
            
    except Exception as e:
        logger.error(f"验证码验证错误: {e}")
        return jsonify({'success': False, 'message': '系统错误，请稍后重试'})

@app.route('/form')
def form():
    """表单页面"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('form.html', user_email=session.get('user_email'))

@app.route('/submit_linkedin', methods=['POST'])
def submit_linkedin():
    """提交LinkedIn链接"""
    try:
        if not session.get('logged_in'):
            return jsonify({'success': False, 'message': '请先登录'})
        
        data = request.get_json()
        linkedin_urls = data.get('linkedin_urls', '').strip()
        
        if not linkedin_urls:
            return jsonify({'success': False, 'message': '请输入LinkedIn链接'})
        
        user_email = session.get('user_email')
        success, message = write_to_google_sheets(user_email, linkedin_urls)
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        logger.error(f"提交LinkedIn链接错误: {e}")
        return jsonify({'success': False, 'message': '系统错误，请稍后重试'})

@app.route('/logout')
def logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/health')
def health_check():
    """简化的健康检查端点"""
    try:
        # 基本的健康检查，不测试外部连接
        return jsonify({
            'status': 'healthy',
            'message': '应用运行正常',
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'健康检查失败: {str(e)}'
        }), 500

@app.route('/debug')
def debug_info():
    """调试信息端点"""
    try:
        # 检查环境变量（不显示敏感信息）
        env_status = {}
        required_vars = ['QQ_EMAIL', 'QQ_PASSWORD', 'GOOGLE_SHEETS_ID', 'GOOGLE_CREDENTIALS_JSON']

        for var in required_vars:
            value = os.environ.get(var)
            if value:
                if var == 'GOOGLE_CREDENTIALS_JSON':
                    # 验证JSON格式
                    try:
                        import json
                        json.loads(value)
                        env_status[var] = 'Present and valid JSON'
                    except json.JSONDecodeError:
                        env_status[var] = 'Present but invalid JSON'
                else:
                    env_status[var] = 'Present'
            else:
                env_status[var] = 'Missing'

        return jsonify({
            'status': 'debug',
            'environment_variables': env_status,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"调试信息获取失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'调试信息获取失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    # 启动时的基本检查
    logger.info("正在启动LinkedIn收集系统...")

    # 检查必要的环境变量
    required_vars = ['QQ_EMAIL', 'QQ_PASSWORD', 'GOOGLE_SHEETS_ID', 'GOOGLE_CREDENTIALS_JSON']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        logger.error("应用将继续启动，但功能可能受限")
    else:
        logger.info("所有必要的环境变量已配置")

    # 测试Google凭据
    try:
        credentials_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if credentials_json:
            import json
            json.loads(credentials_json)  # 验证JSON格式
            logger.info("Google凭据JSON格式验证通过")
        else:
            logger.warning("未找到GOOGLE_CREDENTIALS_JSON环境变量")
    except json.JSONDecodeError as e:
        logger.error(f"Google凭据JSON格式错误: {e}")
    except Exception as e:
        logger.error(f"Google凭据验证失败: {e}")

    port = int(os.environ.get('PORT', 5000))
    logger.info(f"应用将在端口 {port} 上启动")

    app.run(debug=False, host='0.0.0.0', port=port)
