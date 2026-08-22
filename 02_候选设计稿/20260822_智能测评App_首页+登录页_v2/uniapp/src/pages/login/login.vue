<template>
  <!-- 2️⃣ 登录页面（粉红顶部横条 + 暖色界面） -->
  <view class="login-page">
    <!-- 粉红顶部横条 -->
    <view class="topbar">
      <view class="topbar-inner">
        <view class="slogan">✨ 欢迎回来</view>
      </view>
    </view>

    <!-- 暖色光晕背景 -->
    <view class="warm-bg">
      <view class="glow glow-1"></view>
      <view class="glow glow-2"></view>
    </view>

    <!-- 返回按钮 -->
    <view class="back-btn" @click="goBack">
      <text class="back-arrow">←</text>
    </view>

    <view class="login-wrap">
      <!-- 品牌头 -->
      <view class="login-head">
        <view class="app-logo small">
          <text class="logo-spark">✦</text>
        </view>
        <text class="login-title">欢迎回来</text>
        <text class="login-sub">登录后继续你的学习旅程</text>
      </view>

      <!-- Tab 切换：登录 / 注册 -->
      <view class="tab-switch">
        <view
          class="tab"
          :class="{ active: curTab === 'login' }"
          @click="curTab = 'login'"
        >登录</view>
        <view
          class="tab"
          :class="{ active: curTab === 'register' }"
          @click="curTab = 'register'"
        >注册</view>
      </view>

      <!-- 登录表单 -->
      <view v-if="curTab === 'login'" class="auth-form">
        <view class="field-group">
          <view class="input-box" :class="{ error: loginPhoneError }">
            <text class="field-ico">📱</text>
            <input
              class="field-input"
              type="number"
              v-model="loginPhone"
              placeholder="请输入手机号"
              maxlength="11"
            />
          </view>
          <text class="field-msg" :class="{ ok: loginPhoneOk }">{{ loginPhoneMsg }}</text>
        </view>

        <view class="field-group">
          <view class="input-box" :class="{ error: loginPwdError }">
            <text class="field-ico">🔒</text>
            <input
              class="field-input"
              :type="showLoginPwd ? 'text' : 'password'"
              v-model="loginPwd"
              placeholder="请输入密码"
            />
            <text class="eye-btn" @click="showLoginPwd = !showLoginPwd">
              {{ showLoginPwd ? '🙈' : '👁️' }}
            </text>
          </view>
          <text class="field-msg">{{ loginPwdMsg }}</text>
        </view>

        <view class="form-extra">
          <view class="remember">
            <checkbox-group>
              <checkbox :checked="rememberMe" @click="rememberMe = !rememberMe" color="#ec5f8f" />
            </checkbox-group>
            <text>记住账号</text>
          </view>
          <text class="forgot" @click="toast('找回密码功能开发中')">忘记密码？</text>
        </view>

        <button class="primary-btn" @click="submitLogin">登录</button>
      </view>

      <!-- 注册表单 -->
      <view v-else class="auth-form">
        <view class="field-group">
          <view class="input-box" :class="{ error: regPhoneError }">
            <text class="field-ico">📱</text>
            <input
              class="field-input"
              type="number"
              v-model="regPhone"
              placeholder="请输入手机号"
              maxlength="11"
            />
          </view>
          <text class="field-msg" :class="{ ok: regPhoneOk }">{{ regPhoneMsg }}</text>
        </view>

        <view class="field-group">
          <view class="input-box" :class="{ error: regPwdError }">
            <text class="field-ico">🔒</text>
            <input
              class="field-input"
              :type="showRegPwd ? 'text' : 'password'"
              v-model="regPwd"
              placeholder="设置密码（6-16位）"
            />
            <text class="eye-btn" @click="showRegPwd = !showRegPwd">
              {{ showRegPwd ? '🙈' : '👁️' }}
            </text>
          </view>
          <text class="field-msg">{{ regPwdMsg }}</text>
        </view>

        <view class="field-group">
          <view class="input-box" :class="{ error: regPwd2Error }">
            <text class="field-ico">🔒</text>
            <input
              class="field-input"
              :type="showRegPwd2 ? 'text' : 'password'"
              v-model="regPwd2"
              placeholder="确认密码"
            />
            <text class="eye-btn" @click="showRegPwd2 = !showRegPwd2">
              {{ showRegPwd2 ? '🙈' : '👁️' }}
            </text>
          </view>
          <text class="field-msg">{{ regPwd2Msg }}</text>
        </view>

        <button class="primary-btn" @click="submitRegister">注册</button>
      </view>

      <!-- 跳转入口 -->
      <view v-if="curTab === 'login'" class="switch-entry">
        <text>还没有账号？</text>
        <text class="switch-link" @click="curTab = 'register'">立即注册</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onLoad } from '@dcloudio/uni-app';

// ---------- 登录 ----------
const curTab = ref('login');
const loginPhone = ref('');
const loginPwd = ref('');
const showLoginPwd = ref(false);
const rememberMe = ref(false);
const loginPhoneMsg = ref('');
const loginPhoneError = ref(false);
const loginPhoneOk = ref(false);
const loginPwdMsg = ref('');

// ---------- 注册 ----------
const regPhone = ref('');
const regPwd = ref('');
const regPwd2 = ref('');
const showRegPwd = ref(false);
const showRegPwd2 = ref(false);
const regPhoneMsg = ref('');
const regPhoneError = ref(false);
const regPhoneOk = ref(false);
const regPwdMsg = ref('');
const regPwd2Msg = ref('');
const regPwdError = ref(false);
const regPwd2Error = ref(false);

// 手机号校验（中国大陆 11 位）
function isPhoneValid(v) {
  return /^1[3-9]\d{9}$/.test(v);
}

// 从首页带参数进入（?tab=register）
onLoad((options) => {
  if (options && options.tab === 'register') {
    curTab.value = 'register';
  }
});

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages/index/index' });
    }
  });
}

function toast(msg) {
  uni.showToast({ title: msg, icon: 'none' });
}

// ---------- 登录提交 ----------
function submitLogin() {
  if (!loginPhone.value) {
    loginPhoneMsg.value = '请输入手机号';
    loginPhoneError.value = true;
    return;
  }
  if (!isPhoneValid(loginPhone.value)) {
    loginPhoneMsg.value = '手机号格式不正确（11 位大陆号码）';
    loginPhoneError.value = true;
    return;
  }
  loginPhoneMsg.value = '手机号格式正确';
  loginPhoneOk.value = true;
  loginPhoneError.value = false;

  if (!loginPwd.value) {
    loginPwdMsg.value = '请输入密码';
    return;
  }
  if (loginPwd.value.length < 6) {
    loginPwdMsg.value = '密码至少 6 位';
    return;
  }
  loginPwdMsg.value = '';

  uni.showToast({ title: '登录成功（演示）', icon: 'success' });
  setTimeout(() => {
    uni.switchTab({ url: '/pages/index/index' });
  }, 800);
}

// ---------- 注册提交 ----------
function submitRegister() {
  if (!regPhone.value) {
    regPhoneMsg.value = '请输入手机号';
    regPhoneError.value = true;
    return;
  }
  if (!isPhoneValid(regPhone.value)) {
    regPhoneMsg.value = '手机号格式不正确（11 位大陆号码）';
    regPhoneError.value = true;
    return;
  }
  regPhoneMsg.value = '手机号格式正确';
  regPhoneOk.value = true;
  regPhoneError.value = false;

  if (!regPwd.value) {
    regPwdMsg.value = '请输入密码';
    regPwdError.value = true;
    return;
  }
  if (regPwd.value.length < 6) {
    regPwdMsg.value = '密码至少 6 位';
    regPwdError.value = true;
    return;
  }
  regPwdMsg.value = '';
  regPwdError.value = false;

  if (regPwd2.value !== regPwd.value) {
    regPwd2Msg.value = '两次输入的密码不一致';
    regPwd2Error.value = true;
    return;
  }
  regPwd2Msg.value = '';
  regPwd2Error.value = false;

  uni.showToast({ title: '注册成功（演示）', icon: 'success' });
  setTimeout(() => {
    uni.switchTab({ url: '/pages/index/index' });
  }, 800);
}
</script>

<style scoped lang="scss">
/* ============ 2️⃣ 登录页 ============ */
.login-page {
  position: relative;
  min-height: 100vh;
  background: linear-gradient(180deg, #fff6f8 0%, #ffeef2 45%, #ffd9c0 100%);
}

/* 粉红顶部横条 */
.topbar {
  background: linear-gradient(135deg, #f56e9c 0%, #f78cab 45%, #ffb86c 100%);
  padding: 60rpx 40rpx 70rpx;
  border-radius: 0 0 60rpx 60rpx;
  color: #ffffff;
  position: relative;
  overflow: hidden;
}
.topbar::after {
  content: '';
  position: absolute;
  width: 300rpx;
  height: 300rpx;
  background: rgba(255, 255, 255, 0.16);
  border-radius: 50%;
  top: -90rpx;
  right: -60rpx;
}
.topbar-inner {
  position: relative;
  z-index: 1;
}
.slogan {
  font-size: 30rpx;
  font-weight: 700;
}

/* 暖色光晕 */
.warm-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}
.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(70rpx);
  opacity: 0.5;
}
.glow-1 {
  width: 400rpx;
  height: 400rpx;
  background: #ffd9c0;
  top: 200rpx;
  right: -100rpx;
}
.glow-2 {
  width: 380rpx;
  height: 380rpx;
  background: #fbacc4;
  bottom: -60rpx;
  left: -100rpx;
  opacity: 0.45;
}

/* 返回按钮 */
.back-btn {
  position: absolute;
  top: 180rpx;
  left: 40rpx;
  width: 76rpx;
  height: 76rpx;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 12rpx 30rpx rgba(236, 95, 143, 0.14);
  z-index: 3;
}
.back-arrow {
  font-size: 40rpx;
  color: #ec5f8f;
}

/* 主体 */
.login-wrap {
  padding: 0 40rpx;
  margin-top: 40rpx;
  position: relative;
  z-index: 2;
}

.login-head {
  text-align: center;
}
.app-logo.small {
  width: 100rpx;
  height: 100rpx;
  margin: 0 auto 20rpx;
  border-radius: 32rpx;
  background: linear-gradient(135deg, #ec5f8f 0%, #f56e9c 60%, #ff8fb0 100%);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 16rpx 40rpx rgba(236, 95, 143, 0.32);
}
.logo-spark {
  font-size: 44rpx;
}
.login-title {
  display: block;
  font-size: 52rpx;
  color: #d84a78;
  font-weight: 700;
}
.login-sub {
  display: block;
  margin-top: 10rpx;
  font-size: 26rpx;
  color: #9a6b78;
}

/* Tab 切换 */
.tab-switch {
  display: flex;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 999rpx;
  padding: 8rpx;
  margin: 44rpx 0 36rpx;
  box-shadow: 0 12rpx 30rpx rgba(236, 95, 143, 0.14);
}
.tab {
  flex: 1;
  text-align: center;
  padding: 18rpx 0;
  font-size: 30rpx;
  font-weight: 600;
  color: #9a6b78;
  border-radius: 999rpx;
}
.tab.active {
  background: linear-gradient(135deg, #ec5f8f 0%, #f56e9c 60%, #ff8fb0 100%);
  color: #ffffff;
  box-shadow: 0 16rpx 40rpx rgba(236, 95, 143, 0.32);
}

/* 表单 */
.field-group {
  margin-bottom: 28rpx;
}
.input-box {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  border: 1.5px solid #f8e3ea;
  border-radius: 24rpx;
  padding: 0 28rpx;
  height: 96rpx;
  box-shadow: 0 12rpx 30rpx rgba(236, 95, 143, 0.14);
  transition: border-color 0.2s ease;
}
.input-box:focus-within {
  border-color: #f56e9c;
  box-shadow: 0 0 0 8rpx rgba(245, 110, 156, 0.14);
}
.input-box.error {
  border-color: #ef6b6b;
}
.field-ico {
  font-size: 36rpx;
  margin-right: 20rpx;
}
.field-input {
  flex: 1;
  font-size: 30rpx;
  color: #4a2733;
  height: 100%;
}
.eye-btn {
  font-size: 32rpx;
}
.field-msg {
  display: block;
  margin: 8rpx 8rpx 0;
  font-size: 24rpx;
  color: #e05252;
  min-height: 32rpx;
}
.field-msg.ok {
  color: #ec5f8f;
}

/* 额外行 */
.form-extra {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 36rpx;
}
.remember {
  display: flex;
  align-items: center;
  color: #9a6b78;
  font-size: 26rpx;
}
.forgot {
  color: #ec5f8f;
  font-size: 26rpx;
  font-weight: 500;
}

/* 主按钮 */
.primary-btn {
  width: 100%;
  height: 96rpx;
  line-height: 96rpx;
  border-radius: 999rpx;
  font-size: 34rpx;
  font-weight: 700;
  color: #ffffff;
  background: linear-gradient(135deg, #ec5f8f 0%, #f56e9c 60%, #ff8fb0 100%);
  box-shadow: 0 16rpx 40rpx rgba(236, 95, 143, 0.32);
  border: none;
  text-align: center;
}

/* 跳转入口 */
.switch-entry {
  margin-top: 44rpx;
  text-align: center;
  font-size: 28rpx;
  color: #9a6b78;
}
.switch-link {
  color: #ec5f8f;
  font-weight: 700;
  margin-left: 8rpx;
}
</style>
