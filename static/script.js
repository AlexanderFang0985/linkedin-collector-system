// 外贸LinkedIn收集系统 - 前端交互脚本

// 全局变量
let isCodeSent = false;
let resendTimer = null;
let resendCountdown = 60;

// 工具函数
function showMessage(elementId, message, type = 'info') {
    const messageEl = document.getElementById(elementId);
    if (messageEl) {
        messageEl.textContent = message;
        messageEl.className = `message ${type}`;
        messageEl.style.display = 'block';
        
        // 自动隐藏成功消息
        if (type === 'success') {
            setTimeout(() => {
                messageEl.style.display = 'none';
            }, 3000);
        }
    }
}

function hideMessage(elementId) {
    const messageEl = document.getElementById(elementId);
    if (messageEl) {
        messageEl.style.display = 'none';
    }
}

function setButtonLoading(buttonId, loading = true) {
    const button = document.getElementById(buttonId);
    if (button) {
        if (loading) {
            button.classList.add('loading');
            button.disabled = true;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
        }
    }
}

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validateLinkedInURL(url) {
    const linkedinPatterns = [
        /^https?:\/\/(www\.)?linkedin\.com\/in\/[\w-]+\/?$/,
        /^https?:\/\/(www\.)?linkedin\.com\/pub\/[\w-]+\/[\w\/]+\/?$/,
        /^linkedin\.com\/in\/[\w-]+\/?$/,
        /^linkedin\.com\/pub\/[\w-]+\/[\w\/]+\/?$/
    ];
    
    return linkedinPatterns.some(pattern => pattern.test(url.trim()));
}

function countLinkedInURLs(text) {
    if (!text.trim()) return 0;
    
    const urls = text.split('\n').filter(line => line.trim());
    return urls.filter(url => validateLinkedInURL(url)).length;
}

// AJAX请求函数
async function makeRequest(url, data) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Request failed:', error);
        throw error;
    }
}

// 登录页面功能
function initLoginPage() {
    const emailInput = document.getElementById('email');
    const sendCodeBtn = document.getElementById('send-code-btn');
    const verificationCodeInput = document.getElementById('verification-code');
    const verifyBtn = document.getElementById('verify-btn');
    const resendBtn = document.getElementById('resend-btn');
    const emailStep = document.getElementById('email-step');
    const codeStep = document.getElementById('code-step');
    const emailDisplay = document.getElementById('email-display');

    // 发送验证码
    if (sendCodeBtn) {
        sendCodeBtn.addEventListener('click', async function() {
            const email = emailInput.value.trim();
            
            if (!email) {
                showMessage('email-message', '请输入邮箱地址', 'error');
                return;
            }
            
            if (!validateEmail(email)) {
                showMessage('email-message', '邮箱格式不正确', 'error');
                return;
            }
            
            setButtonLoading('send-code-btn', true);
            hideMessage('email-message');
            
            try {
                const result = await makeRequest('/send_code', { email });
                
                if (result.success) {
                    showMessage('email-message', result.message, 'success');
                    emailDisplay.textContent = email;
                    
                    // 切换到验证码步骤
                    setTimeout(() => {
                        emailStep.classList.remove('active');
                        codeStep.classList.add('active');
                        verificationCodeInput.focus();
                    }, 1000);
                    
                    isCodeSent = true;
                    startResendTimer();
                } else {
                    showMessage('email-message', result.message, 'error');
                }
            } catch (error) {
                showMessage('email-message', '网络错误，请稍后重试', 'error');
            } finally {
                setButtonLoading('send-code-btn', false);
            }
        });
    }

    // 验证验证码
    if (verifyBtn) {
        verifyBtn.addEventListener('click', async function() {
            const email = emailInput.value.trim();
            const code = verificationCodeInput.value.trim();
            
            if (!code) {
                showMessage('code-message', '请输入验证码', 'error');
                return;
            }
            
            if (code.length !== 6) {
                showMessage('code-message', '验证码应为6位数字', 'error');
                return;
            }
            
            setButtonLoading('verify-btn', true);
            hideMessage('code-message');
            
            try {
                const result = await makeRequest('/verify_code', { email, code });
                
                if (result.success) {
                    showMessage('code-message', result.message, 'success');
                    
                    // 登录成功，跳转到表单页面
                    setTimeout(() => {
                        window.location.href = '/form';
                    }, 1000);
                } else {
                    showMessage('code-message', result.message, 'error');
                }
            } catch (error) {
                showMessage('code-message', '网络错误，请稍后重试', 'error');
            } finally {
                setButtonLoading('verify-btn', false);
            }
        });
    }

    // 重新发送验证码
    if (resendBtn) {
        resendBtn.addEventListener('click', async function() {
            const email = emailInput.value.trim();
            
            setButtonLoading('resend-btn', true);
            hideMessage('code-message');
            
            try {
                const result = await makeRequest('/send_code', { email });
                
                if (result.success) {
                    showMessage('code-message', '验证码已重新发送', 'success');
                    startResendTimer();
                } else {
                    showMessage('code-message', result.message, 'error');
                }
            } catch (error) {
                showMessage('code-message', '网络错误，请稍后重试', 'error');
            } finally {
                setButtonLoading('resend-btn', false);
            }
        });
    }

    // 验证码输入框回车事件
    if (verificationCodeInput) {
        verificationCodeInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                verifyBtn.click();
            }
        });
        
        // 只允许输入数字
        verificationCodeInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '');
        });
    }

    // 邮箱输入框回车事件
    if (emailInput) {
        emailInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendCodeBtn.click();
            }
        });
    }
}

// 重新发送倒计时
function startResendTimer() {
    const resendBtn = document.getElementById('resend-btn');
    if (!resendBtn) return;
    
    resendCountdown = 60;
    resendBtn.disabled = true;
    
    resendTimer = setInterval(() => {
        resendCountdown--;
        resendBtn.textContent = `重新发送 (${resendCountdown}s)`;
        
        if (resendCountdown <= 0) {
            clearInterval(resendTimer);
            resendBtn.disabled = false;
            resendBtn.textContent = '重新发送';
        }
    }, 1000);
}

// 表单页面功能
function initFormPage() {
    const linkedinCountSelect = document.getElementById('linkedin-count');
    const linkedinInputsContainer = document.getElementById('linkedin-inputs-container');
    const submitBtn = document.getElementById('submit-btn');
    const clearBtn = document.getElementById('clear-btn');
    const urlCounter = document.getElementById('url-count');
    const linkedinForm = document.getElementById('linkedin-form');

    // 生成LinkedIn输入框
    function generateLinkedInInputs(count) {
        linkedinInputsContainer.innerHTML = '';

        for (let i = 1; i <= count; i++) {
            const inputGroup = document.createElement('div');
            inputGroup.className = 'linkedin-input-group';

            inputGroup.innerHTML = `
                <label for="linkedin-url-${i}">LinkedIn链接 ${i}</label>
                <input
                    type="url"
                    id="linkedin-url-${i}"
                    name="linkedin_url_${i}"
                    placeholder="请输入LinkedIn链接，例如：https://www.linkedin.com/in/username"
                    data-index="${i}"
                    required
                >
                <span class="validation-icon" id="icon-${i}"></span>
            `;

            linkedinInputsContainer.appendChild(inputGroup);

            // 为每个输入框添加验证事件
            const input = inputGroup.querySelector('input');
            const icon = inputGroup.querySelector('.validation-icon');

            input.addEventListener('input', function() {
                validateSingleLinkedInInput(this, icon);
                updateUrlCounter();
            });

            input.addEventListener('blur', function() {
                validateSingleLinkedInInput(this, icon);
            });
        }

        linkedinInputsContainer.classList.add('active');
        updateUrlCounter();
    }

    // 验证单个LinkedIn输入框
    function validateSingleLinkedInInput(input, icon) {
        const url = input.value.trim();

        if (!url) {
            input.classList.remove('valid', 'invalid');
            icon.textContent = '';
            icon.classList.remove('valid', 'invalid');
            return false;
        }

        if (validateLinkedInURL(url)) {
            input.classList.remove('invalid');
            input.classList.add('valid');
            icon.textContent = '✓';
            icon.classList.remove('invalid');
            icon.classList.add('valid');
            return true;
        } else {
            input.classList.remove('valid');
            input.classList.add('invalid');
            icon.textContent = '✗';
            icon.classList.remove('valid');
            icon.classList.add('invalid');
            return false;
        }
    }

    // 更新URL计数器
    function updateUrlCounter() {
        const inputs = linkedinInputsContainer.querySelectorAll('input');
        let validCount = 0;

        inputs.forEach(input => {
            if (input.value.trim() && validateLinkedInURL(input.value.trim())) {
                validCount++;
            }
        });

        urlCounter.textContent = `${validCount} 个有效链接`;
    }

    // 监听数量选择变化
    if (linkedinCountSelect) {
        linkedinCountSelect.addEventListener('change', function() {
            const count = parseInt(this.value);
            generateLinkedInInputs(count);
            hideMessage('form-message');
        });

        // 初始化生成1个输入框
        generateLinkedInInputs(1);
    }

    // 清空内容
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            if (confirm('确定要清空所有内容吗？')) {
                const inputs = linkedinInputsContainer.querySelectorAll('input');
                inputs.forEach(input => {
                    input.value = '';
                    input.classList.remove('valid', 'invalid');
                });

                const icons = linkedinInputsContainer.querySelectorAll('.validation-icon');
                icons.forEach(icon => {
                    icon.textContent = '';
                    icon.classList.remove('valid', 'invalid');
                });

                updateUrlCounter();
                hideMessage('form-message');
            }
        });
    }

    // 表单提交
    if (linkedinForm) {
        linkedinForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const inputs = linkedinInputsContainer.querySelectorAll('input');
            const linkedinUrls = [];
            let hasEmpty = false;
            let hasInvalid = false;

            inputs.forEach(input => {
                const url = input.value.trim();
                if (!url) {
                    hasEmpty = true;
                    return;
                }

                if (!validateLinkedInURL(url)) {
                    hasInvalid = true;
                    return;
                }

                linkedinUrls.push(url);
            });

            if (hasEmpty) {
                showMessage('form-message', '请填写所有LinkedIn链接输入框', 'error');
                return;
            }

            if (hasInvalid) {
                showMessage('form-message', '请检查并修正无效的LinkedIn链接格式', 'error');
                return;
            }

            if (linkedinUrls.length === 0) {
                showMessage('form-message', '请至少输入一个有效的LinkedIn链接', 'error');
                return;
            }

            setButtonLoading('submit-btn', true);
            hideMessage('form-message');

            try {
                const result = await makeRequest('/submit_linkedin', {
                    linkedin_urls: linkedinUrls.join('\n')
                });

                if (result.success) {
                    showMessage('form-message', result.message, 'success');

                    // 成功后清空表单
                    setTimeout(() => {
                        inputs.forEach(input => {
                            input.value = '';
                            input.classList.remove('valid', 'invalid');
                        });

                        const icons = linkedinInputsContainer.querySelectorAll('.validation-icon');
                        icons.forEach(icon => {
                            icon.textContent = '';
                            icon.classList.remove('valid', 'invalid');
                        });

                        updateUrlCounter();
                    }, 2000);
                } else {
                    showMessage('form-message', result.message, 'error');
                }
            } catch (error) {
                showMessage('form-message', '网络错误，请稍后重试', 'error');
            } finally {
                setButtonLoading('submit-btn', false);
            }
        });
    }
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 通用初始化
    console.log('外贸LinkedIn收集系统已加载');
    
    // 为所有输入框添加焦点样式
    const inputs = document.querySelectorAll('input, textarea');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });
});
