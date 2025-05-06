@echo off
echo Discord-X-Support-Hub を起動しています...
echo.
echo 起動後はこのウィンドウを閉じないでください。
echo 終了するには Ctrl+C を押すか、このウィンドウを閉じてください。
echo.
echo ログインしています...

:: 環境変数ファイルをリネーム
if exist @env.txt (
  copy @env.txt .env >nul
)

:: メインプログラムを実行
python main.py

:: エラーが発生した場合
if %ERRORLEVEL% NEQ 0 (
  echo.
  echo エラーが発生しました。
  echo 詳細はログを確認してください。
  pause
)