@echo off
chcp 65001 >nul 2>&1
setlocal
title [企业微信] Claude Code Chat - 交付质量审核

set "PROJECT_ROOT=E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目"
set "CLAUDE_WORKTREE=%PROJECT_ROOT%\worktrees\claude"

echo ============================================
echo  ORCA Dual-Instance: Claude Code Chat
echo  Project: 企业微信群定制接单项目
echo ============================================

if not exist "%CLAUDE_WORKTREE%" (echo [ERROR] Worktree not found & pause & exit /b 1)
cd /d "%CLAUDE_WORKTREE%"
claude -p "你是龙虾舰队审核校验Agent（Claude Code），工作目录：%CLAUDE_WORKTREE%。项目：企业微信群定制接单项目。负责商单交付质量审核、合规审查。请用中文回复。"
endlocal
