let isAdminMode = localStorage.getItem('isAdminMode') === 'true';

function toggleUserMode() {
    if (!isAdminMode) {
        // 显示登录对话框
        showLoginDialog();
    } else {
        // 直接切换回访客模式
        switchToGuestMode();
    }
}

function showLoginDialog() {
    const loginHtml = `
        <div id="loginDialog" class="modal" style="display:block">
            <div class="modal-content">
                <h3>Admin Login</h3>
                <div class="login-form">
                    <input type="text" id="userId" placeholder="User ID" />
                    <input type="password" id="password" placeholder="Password" />
                </div>
                <div class="modal-buttons">
                    <button class="cancel-btn" onclick="closeLoginDialog()">Cancel</button>
                    <button class="confirm-btn" onclick="verifyLogin()">Login</button>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', loginHtml);
}

function closeLoginDialog() {
    const dialog = document.getElementById('loginDialog');
    if (dialog) {
        dialog.remove();
    }
}

function verifyLogin() {
    const userId = document.getElementById('userId').value;
    const password = document.getElementById('password').value;
    
    // 这里设置默认的管理员账号密码
    if (userId === 'admin' && password === 'admin123') {
        switchToAdminMode();
        closeLoginDialog();
    } else {
        alert('用户ID或密码错误！');
    }
}

function switchToAdminMode() {
    const body = document.body;
    const modeIndicator = document.querySelector('.mode-indicator i');
    const modeText = document.querySelector('.mode-text');
    const switchButton = document.querySelector('.switch-button');
    
    isAdminMode = true;
    localStorage.setItem('isAdminMode', true);
    
    body.classList.remove('guest-mode');
    body.classList.add('admin-mode');
    modeIndicator.className = 'fas fa-user-shield';
    modeText.textContent = 'Admin Mode';
    switchButton.textContent = 'Switch to Guest';
}

function switchToGuestMode() {
    const body = document.body;
    const modeIndicator = document.querySelector('.mode-indicator i');
    const modeText = document.querySelector('.mode-text');
    const switchButton = document.querySelector('.switch-button');
    
    isAdminMode = false;
    localStorage.setItem('isAdminMode', false);
    
    body.classList.remove('admin-mode');
    body.classList.add('guest-mode');
    modeIndicator.className = 'fas fa-user';
    modeText.textContent = 'Guest Mode';
    switchButton.textContent = 'Switch to Admin';
}

// 页面加载时的初始化代码保持不变
document.addEventListener('DOMContentLoaded', function() {
    const body = document.body;
    const modeIndicator = document.querySelector('.mode-indicator i');
    const modeText = document.querySelector('.mode-text');
    const switchButton = document.querySelector('.switch-button');
    
    if (isAdminMode) {
        body.classList.add('admin-mode');
        modeIndicator.className = 'fas fa-user-shield';
        modeText.textContent = 'Admin Mode';
        switchButton.textContent = 'Switch to Guest';
    } else {
        body.classList.add('guest-mode');
        modeIndicator.className = 'fas fa-user';
        modeText.textContent = 'Guest Mode';
        switchButton.textContent = 'Switch to Admin';
    }
});