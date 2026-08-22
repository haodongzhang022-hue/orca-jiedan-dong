/* 智能测评 App · 前端交互脚本  v2
   风格：粉红顶部横条 + 暖色界面
   仅前端界面：表单校验 / 密码明文切换 / Tab 切换 / 页面跳转 */
(function () {
  "use strict";

  /* ---------- 通用：图标渲染 ---------- */
  function renderIcons() {
    document.querySelectorAll("i[data-icon]").forEach(function (el) {
      if (el.querySelector("svg")) return; // 已渲染
      var name = el.getAttribute("data-icon");
      var use = document.createElementNS("http://www.w3.org/2000/svg", "use");
      use.setAttribute("href", "#i-" + name);
      var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("viewBox", "0 0 24 24");
      svg.setAttribute("fill", "none");
      svg.setAttribute("stroke", "currentColor");
      svg.setAttribute("stroke-width", "1.8");
      svg.setAttribute("stroke-linecap", "round");
      svg.setAttribute("stroke-linejoin", "round");
      svg.appendChild(use);
      el.appendChild(svg);
    });
  }

  /* ---------- 手机号校验（中国大陆 11 位） ---------- */
  function isPhoneValid(v) {
    return /^1[3-9]\d{9}$/.test(v);
  }

  function setFieldMsg(msgEl, text, ok) {
    if (!msgEl) return;
    msgEl.textContent = text || "";
    msgEl.classList.toggle("ok", !!ok);
  }

  /* ============================================================
     1️⃣ 首页
     ============================================================ */
  function initHome() {
    var startBtn = document.getElementById("startQuiz");
    if (startBtn) {
      startBtn.addEventListener("click", function () {
        alert("开始测评：请先登录以同步测评记录。");
        window.location.href = "login.html";
      });
    }
  }

  /* ============================================================
     2️⃣ 登录页
     ============================================================ */
  function initLogin() {
    var backBtn = document.getElementById("backHome");
    if (backBtn) {
      backBtn.addEventListener("click", function () {
        window.location.href = "index.html";
      });
    }

    var loginForm = document.getElementById("loginForm");
    var regForm = document.getElementById("registerForm");
    var tabs = document.querySelectorAll(".tab");
    var switchEntry = document.getElementById("switchEntry");
    var toRegister = document.getElementById("toRegister");
    var curTab = "login";

    function setTab(tab) {
      curTab = tab;
      tabs.forEach(function (t) {
        t.classList.toggle("active", t.getAttribute("data-tab") === tab);
      });
      loginForm.classList.toggle("hidden", tab !== "login");
      regForm.classList.toggle("hidden", tab !== "register");
      if (switchEntry) {
        switchEntry.classList.toggle("hidden", tab === "register");
        if (tab === "login") {
          switchEntry.querySelector("span").textContent = "还没有账号？";
          toRegister.textContent = "立即注册";
        }
      }
      clearAllMsgs();
    }

    tabs.forEach(function (t) {
      t.addEventListener("click", function () {
        setTab(t.getAttribute("data-tab"));
      });
    });

    if (toRegister) {
      toRegister.addEventListener("click", function (e) {
        e.preventDefault();
        setTab("register");
      });
    }

    // 从首页带参数进入（login.html?tab=register）
    var params = new URLSearchParams(window.location.search);
    if (params.get("tab") === "register") setTab("register");

    /* ---- 密码明文 / 隐藏切换 ---- */
    document.querySelectorAll(".eye-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var input = document.getElementById(btn.getAttribute("data-eye"));
        if (!input) return;
        var isPwd = input.type === "password";
        input.type = isPwd ? "text" : "password";
        btn.querySelector("i").setAttribute("data-icon", isPwd ? "eye-off" : "eye");
        btn.querySelector("i").innerHTML = "";
        renderIcons();
      });
    });

    function clearAllMsgs() {
      document.querySelectorAll(".field-msg").forEach(function (m) {
        m.textContent = "";
        m.classList.remove("ok");
      });
      document.querySelectorAll(".input-box").forEach(function (b) {
        b.classList.remove("error");
      });
    }

    function validatePhone(phoneInput, msgEl) {
      var v = phoneInput.value.trim();
      if (!v) {
        setFieldMsg(msgEl, "请输入手机号");
        phoneInput.closest(".input-box").classList.add("error");
        return false;
      }
      if (!isPhoneValid(v)) {
        setFieldMsg(msgEl, "手机号格式不正确（11 位大陆号码）");
        phoneInput.closest(".input-box").classList.add("error");
        return false;
      }
      setFieldMsg(msgEl, "手机号格式正确", true);
      phoneInput.closest(".input-box").classList.remove("error");
      return true;
    }

    function validatePwd(pwdInput, msgEl) {
      var v = pwdInput.value;
      if (!v) {
        setFieldMsg(msgEl, "请输入密码");
        pwdInput.closest(".input-box").classList.add("error");
        return false;
      }
      if (v.length < 6) {
        setFieldMsg(msgEl, "密码至少 6 位");
        pwdInput.closest(".input-box").classList.add("error");
        return false;
      }
      setFieldMsg(msgEl, "");
      pwdInput.closest(".input-box").classList.remove("error");
      return true;
    }

    function validateConfirm(pwdInput, confirmInput, msgEl) {
      if (confirmInput.value !== pwdInput.value) {
        setFieldMsg(msgEl, "两次输入的密码不一致");
        confirmInput.closest(".input-box").classList.add("error");
        return false;
      }
      setFieldMsg(msgEl, "");
      confirmInput.closest(".input-box").classList.remove("error");
      return true;
    }

    /* ---- 实时校验 ---- */
    var loginPhone = document.getElementById("loginPhone");
    var loginPwd = document.getElementById("loginPwd");
    var regPhone = document.getElementById("regPhone");
    var regPwd = document.getElementById("regPwd");
    var regPwd2 = document.getElementById("regPwd2");

    if (loginPhone) loginPhone.addEventListener("input", function () {
      validatePhone(loginPhone, document.getElementById("loginPhoneMsg"));
    });
    if (loginPwd) loginPwd.addEventListener("input", function () {
      validatePwd(loginPwd, document.getElementById("loginPwdMsg"));
    });
    if (regPhone) regPhone.addEventListener("input", function () {
      validatePhone(regPhone, document.getElementById("regPhoneMsg"));
    });
    if (regPwd) regPwd.addEventListener("input", function () {
      validatePwd(regPwd, document.getElementById("regPwdMsg"));
      if (regPwd2.value) validateConfirm(regPwd, regPwd2, document.getElementById("regPwd2Msg"));
    });
    if (regPwd2) regPwd2.addEventListener("input", function () {
      validateConfirm(regPwd, regPwd2, document.getElementById("regPwd2Msg"));
    });

    /* ---- 提交（仅前端演示） ---- */
    if (loginForm) {
      loginForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var okP = validatePhone(loginPhone, document.getElementById("loginPhoneMsg"));
        var okW = validatePwd(loginPwd, document.getElementById("loginPwdMsg"));
        if (okP && okW) {
          alert("登录成功（前端演示，未接入后端）。");
        }
      });
    }

    if (regForm) {
      regForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var okP = validatePhone(regPhone, document.getElementById("regPhoneMsg"));
        var okW = validatePwd(regPwd, document.getElementById("regPwdMsg"));
        var okC = validateConfirm(regPwd, regPwd2, document.getElementById("regPwd2Msg"));
        if (okP && okW && okC) {
          alert("注册成功（前端演示，未接入后端）。");
        }
      });
    }
  }

  /* ---------- 初始化 ---------- */
  function boot() {
    renderIcons();
    if (document.querySelector(".home-screen")) initHome();
    if (document.querySelector(".login-screen")) initLogin();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
