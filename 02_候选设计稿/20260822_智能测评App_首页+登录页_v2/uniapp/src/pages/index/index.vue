<template>
  <!-- 1️⃣ 首页模块（粉红顶部横条 + 暖色界面） -->
  <view class="home-page">
    <!-- 粉红顶部横条 -->
    <view class="topbar">
      <view class="topbar-inner">
        <view class="slogan">
          <text class="slogan-icon">✨</text>
          <text>AI 让学习更高效</text>
        </view>
        <view class="icon-btn">
          <text class="dots">···</text>
        </view>
      </view>
    </view>

    <!-- 暖色光晕背景 -->
    <view class="warm-bg">
      <view class="glow glow-1"></view>
      <view class="glow glow-2"></view>
    </view>

    <view class="home-body">
      <!-- 品牌区 -->
      <view class="brand">
        <view class="app-logo">
          <text class="logo-spark">✦</text>
        </view>
        <text class="app-name">智测</text>
        <text class="app-tagline">AI 自动生成测评题 · 让每一步学习都可见</text>
      </view>

      <!-- 卡片布局 · App 简介 -->
      <view class="feature-cards">
        <view class="feature-card">
          <view class="card-icon"><text>📝</text></view>
          <view class="card-text">
            <text class="card-title">AI 测评题</text>
            <text class="card-desc">智能生成专属测评题目</text>
          </view>
        </view>
        <view class="feature-card">
          <view class="card-icon"><text>🧠</text></view>
          <view class="card-text">
            <text class="card-title">知识巩固</text>
            <text class="card-desc">针对性复习薄弱知识点</text>
          </view>
        </view>
        <view class="feature-card">
          <view class="card-icon"><text>📊</text></view>
          <view class="card-text">
            <text class="card-title">成绩分析</text>
            <text class="card-desc">可视化学习数据报告</text>
          </view>
        </view>
        <view class="feature-card">
          <view class="card-icon"><text>📖</text></view>
          <view class="card-text">
            <text class="card-title">错题本</text>
            <text class="card-desc">错题自动归纳随时回顾</text>
          </view>
        </view>
      </view>

      <!-- 核心按钮 -->
      <view class="cta-area">
        <button class="primary-btn" @click="goLogin">
          <text>开始测评</text>
          <text class="btn-arrow">→</text>
        </button>
      </view>

      <!-- 底部：轻量登录注册向导 -->
      <view class="login-guide">
        <text class="guide-text">登录后即可同步测评记录</text>
        <view class="guide-links">
          <text class="guide-link" @click="goLogin">登录</text>
          <text class="dot">·</text>
          <text class="guide-link" @click="goLogin('register')">注册</text>
        </view>
      </view>
    </view>

    <!-- 底部导航 -->
    <view class="bottom-nav">
      <view class="nav-item active">
        <text class="nav-emoji">🏠</text>
        <text>首页</text>
      </view>
      <view class="nav-item" @click="toast('测评页开发中')">
        <text class="nav-emoji">📝</text>
        <text>测评</text>
      </view>
      <view class="nav-item" @click="toast('成绩页开发中')">
        <text class="nav-emoji">📊</text>
        <text>成绩</text>
      </view>
      <view class="nav-item" @click="goLogin">
        <text class="nav-emoji">👤</text>
        <text>我的</text>
      </view>
    </view>
  </view>
</template>

<script setup>
// 首页逻辑
function goLogin(tab) {
  uni.navigateTo({
    url: '/pages/login/login' + (tab === 'register' ? '?tab=register' : '')
  });
}

function toast(msg) {
  uni.showToast({ title: msg, icon: 'none' });
}
</script>

<style scoped lang="scss">
/* ============ 1️⃣ 首页 ============ */
.home-page {
  position: relative;
  min-height: 100vh;
  padding-bottom: 120rpx;
  background: linear-gradient(180deg, #fff6f8 0%, #ffeef2 45%, #ffd9c0 100%);
}

/* 粉红顶部横条 */
.topbar {
  background: linear-gradient(135deg, #f56e9c 0%, #f78cab 45%, #ffb86c 100%);
  padding: 60rpx 40rpx 60rpx;
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
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.slogan {
  display: flex;
  align-items: center;
  font-size: 30rpx;
  font-weight: 700;
}
.slogan-icon {
  margin-right: 10rpx;
  font-size: 32rpx;
}
.icon-btn {
  width: 72rpx;
  height: 72rpx;
  background: rgba(255, 255, 255, 0.28);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.dots {
  font-size: 30rpx;
  letter-spacing: 2rpx;
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

/* 主体 */
.home-body {
  padding: 40rpx;
  position: relative;
  z-index: 2;
}

/* 品牌区 */
.brand {
  text-align: center;
  margin-bottom: 40rpx;
}
.app-logo {
  width: 140rpx;
  height: 140rpx;
  margin: 0 auto 24rpx;
  border-radius: 44rpx;
  background: linear-gradient(135deg, #ec5f8f 0%, #f56e9c 60%, #ff8fb0 100%);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 16rpx 40rpx rgba(236, 95, 143, 0.32);
}
.logo-spark {
  font-size: 60rpx;
}
.app-name {
  display: block;
  font-size: 56rpx;
  letter-spacing: 4rpx;
  color: #d84a78;
  font-weight: 700;
}
.app-tagline {
  display: block;
  margin-top: 12rpx;
  font-size: 26rpx;
  color: #9a6b78;
}

/* 卡片 */
.feature-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24rpx;
  margin-bottom: 48rpx;
}
.feature-card {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #f8e3ea;
  border-radius: 36rpx;
  padding: 28rpx 26rpx;
  box-shadow: 0 12rpx 30rpx rgba(236, 95, 143, 0.14);
}
.card-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 24rpx;
  background: #fde4ec;
  color: #ec5f8f;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
  font-size: 40rpx;
}
.card-text {
  display: flex;
  flex-direction: column;
}
.card-title {
  font-size: 30rpx;
  color: #d84a78;
  font-weight: 600;
}
.card-desc {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #9a6b78;
  line-height: 1.5;
}

/* 核心按钮 */
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
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-arrow {
  margin-left: 10rpx;
}

/* 登录向导 */
.login-guide {
  margin-top: 40rpx;
  text-align: center;
  color: #9a6b78;
  font-size: 26rpx;
}
.guide-links {
  margin-top: 12rpx;
  display: flex;
  justify-content: center;
  align-items: center;
}
.guide-link {
  color: #ec5f8f;
  font-weight: 600;
  margin: 0 8rpx;
}
.dot {
  color: #fbacc4;
}

/* 底部导航 */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  border-top: 1px solid #f8e3ea;
  display: flex;
  justify-content: space-around;
  padding: 16rpx 0 24rpx;
  z-index: 10;
}
.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #9a6b78;
  font-size: 22rpx;
}
.nav-item.active {
  color: #ec5f8f;
  font-weight: 600;
}
.nav-emoji {
  font-size: 40rpx;
  margin-bottom: 4rpx;
}
</style>
