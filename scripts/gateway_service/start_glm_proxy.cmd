@echo off
rem Start TeamoRouter GLM protocol bridge (Responses -> Chat Completions).
rem API key is read from the TEAMOROUTER_API_KEY user environment variable.
start /min "TeamoGLMProxy" "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" "%~dp0teamorouter_glm_proxy.py"
