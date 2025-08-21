import os
import re
import sys
import json
import smtplib
import random
import string
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import flask
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import gspread
from google.oauth2.service_account import Credentials

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 获取应用的基础目录
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, 
           template_folder=os.path.join(basedir, 'templates'),
           static_folder=os.path.join(basedir, 'static'))
app.secret_key = os.environ.get('SECRET_KEY', 'your-default-secret-key')

# 添加调试信息
logger.info(f"应用基础目录: {basedir}")
logger.info(f"模板文件夹路径: {os.path.join(basedir, 'templates')}")
logger.info(f"静态文件夹路径: {os.path.join(basedir, 'static')}")

# 配置信息
QQ_EMAIL = os.environ.get('QQ_EMAIL')
QQ_PASSWORD = os.environ.get('QQ_PASSWORD')
GOOGLE_SHEETS_ID = os.environ.get('GOOGLE_SHEETS_ID')

# Google Sheets API配置
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

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
    """完整的健康检查端点"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }

    all_healthy = True

    try:
        # 1. 检查环境变量
        required_vars = ['QQ_EMAIL', 'QQ_PASSWORD', 'GOOGLE_SHEETS_ID', 'GOOGLE_CREDENTIALS_JSON', 'SECRET_KEY']
        missing_vars = []

        for var in required_vars:
            value = os.environ.get(var)
            if not value:
                missing_vars.append(var)
            elif var == 'GOOGLE_CREDENTIALS_JSON':
                # 验证JSON格式
                try:
                    import json
                    json.loads(value)
                    health_status['checks'][var] = 'OK - Valid JSON'
                except json.JSONDecodeError:
                    health_status['checks'][var] = 'ERROR - Invalid JSON'
                    all_healthy = False
            else:
                health_status['checks'][var] = 'OK'

        if missing_vars:
            health_status['checks']['missing_vars'] = f"Missing: {', '.join(missing_vars)}"
            all_healthy = False

        # 2. 测试邮件连接（带超时和错误处理）
        try:
            import smtplib
            import socket

            # 设置较短的超时时间
            socket.setdefaulttimeout(10)

            server = smtplib.SMTP('smtp.qq.com', 587)
            server.starttls()
            server.login(os.environ.get('QQ_EMAIL', ''), os.environ.get('QQ_PASSWORD', ''))
            server.quit()
            health_status['checks']['email_smtp'] = 'OK - Connection successful'

        except Exception as e:
            health_status['checks']['email_smtp'] = f'WARNING - {str(e)[:100]}'
            # 邮件连接失败不影响整体健康状态，只是警告
            logger.warning(f"邮件连接测试失败: {e}")

        # 3. 测试Google Sheets连接（带超时和错误处理）
        try:
            import gspread
            import json
            from google.oauth2.service_account import Credentials

            credentials_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            if credentials_json:
                credentials_dict = json.loads(credentials_json)
                credentials = Credentials.from_service_account_info(credentials_dict)
                gc = gspread.authorize(credentials)

                # 尝试打开工作表（带超时）
                sheet_id = os.environ.get('GOOGLE_SHEETS_ID')
                if sheet_id:
                    sheet = gc.open_by_key(sheet_id)
                    health_status['checks']['google_sheets'] = 'OK - Connection successful'
                else:
                    health_status['checks']['google_sheets'] = 'ERROR - No sheet ID'
                    all_healthy = False
            else:
                health_status['checks']['google_sheets'] = 'ERROR - No credentials'
                all_healthy = False

        except Exception as e:
            health_status['checks']['google_sheets'] = f'WARNING - {str(e)[:100]}'
            # Google Sheets连接失败不影响整体健康状态，只是警告
            logger.warning(f"Google Sheets连接测试失败: {e}")

        # 4. 检查Flask应用状态
        health_status['checks']['flask_app'] = 'OK - Running'

        # 设置最终状态
        if all_healthy:
            health_status['status'] = 'healthy'
            health_status['message'] = '所有系统正常运行'
            return jsonify(health_status), 200
        else:
            health_status['status'] = 'degraded'
            health_status['message'] = '部分系统存在问题，但应用仍可运行'
            return jsonify(health_status), 200  # 返回200以通过Railway健康检查

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'健康检查失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/debug')
def debug_info():
    """调试信息端点"""
    try:
        # 检查环境变量（不显示敏感信息）
        env_status = {}
        required_vars = ['QQ_EMAIL', 'QQ_PASSWORD', 'GOOGLE_SHEETS_ID', 'GOOGLE_CREDENTIALS_JSON', 'SECRET_KEY']

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
                elif var in ['QQ_PASSWORD', 'SECRET_KEY']:
                    env_status[var] = f'Present ({len(value)} chars)'
                else:
                    env_status[var] = 'Present'
            else:
                env_status[var] = 'Missing'

        return jsonify({
            'status': 'debug',
            'environment_variables': env_status,
            'timestamp': datetime.now().isoformat(),
            'python_version': sys.version,
            'flask_version': flask.__version__
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
    required_vars = ['QQ_EMAIL', 'QQ_PASSWORD', 'GOOGLE_SHEETS_ID', 'GOOGLE_CREDENTIALS_JSON', 'SECRET_KEY']
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
