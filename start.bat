@echo off
echo Discord-X-Support-Hub ���N�����Ă��܂�...
echo.
echo �N����͂��̃E�B���h�E����Ȃ��ł��������B
echo �I������ɂ� Ctrl+C ���������A���̃E�B���h�E����Ă��������B
echo.
echo ���O�C�����Ă��܂�...

:: ���ϐ��t�@�C�������l�[��
if exist @env.txt (
  copy @env.txt .env >nul
)

:: ���C���v���O���������s
python main.py

:: �G���[�����������ꍇ
if %ERRORLEVEL% NEQ 0 (
  echo.
  echo �G���[���������܂����B
  echo �ڍׂ̓��O���m�F���Ă��������B
  pause
)