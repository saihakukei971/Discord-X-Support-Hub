#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Discord-X-Support-Hub
セットアップスクリプト: 初期設定を対話形式で実行
"""

import os
import json
import getpass
import sys
import re
import time
from pathlib import Path

def print_header():
    """ヘッダー表示"""
    print("\n" + "=" * 60)
    print("     Discord-X-Support-Hub セットアップウィザード")
    print("=" * 60)
    print("このウィザードでは、サポートハブの初期設定を行います。")
    print("必要なAPIキーやトークンの入力と、設定ファイルの生成を行います。")
    print("-" * 60 + "\n")

def get_input(prompt, validate_func=None, default=None, password=False):
    """ユーザー入力を取得"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    while True:
        if password:
            value = getpass.getpass(prompt)
        else:
            value = input(prompt)
        
        if not value and default:
            value = default
        
        if validate_func and value:
            valid, message = validate_func(value)
            if not valid:
                print(f"エラー: {message}")
                continue
        
        if value or default:
            return value
        
        print("値を入力してください。")

def validate_discord_token(token):
    """Discordトークンの検証"""
    pattern = r"^[A-Za-z0-9\.\-_]{59,68}$"
    if not re.match(pattern, token):
        return False, "Discordトークンの形式が正しくありません。"
    return True, ""

def validate_spreadsheet_id(spreadsheet_id):
    """スプレッドシートIDの検証"""
    pattern = r"^[a-zA-Z0-9\-_]{43}$"
    if not re.match(pattern, spreadsheet_id):
        return False, "スプレッドシートIDの形式が正しくありません。"
    return True, ""

def validate_x_token(token):
    """Xトークンの簡易検証"""
    if len(token) < 10:
        return False, "トークンが短すぎます。"
    return True, ""

def setup_env_file():
    """環境変数ファイルのセットアップ"""
    print("\n[1/4] 環境変数の設定")
    print("-" * 30)
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    # .env.exampleがある場合は読み込む
    defaults = {}
    if env_example.exists():
        with open(env_example, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    defaults[key] = value
    
    # 既存の.envがある場合は読み込む
    if env_file.exists():
        print("既存の.envファイルを検出しました。既存の値をデフォルトとして使用します。")
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    defaults[key] = value
    
    # Discord設定
    print("\nDiscord Bot設定:")
    discord_token = get_input("Discord Bot Token", validate_discord_token, defaults.get("DISCORD_TOKEN"), password=True)
    
    # X API設定
    print("\nX (Twitter) API設定:")
    x_consumer_key = get_input("X Consumer Key", validate_x_token, defaults.get("X_CONSUMER_KEY"), password=True)
    x_consumer_secret = get_input("X Consumer Secret", validate_x_token, defaults.get("X_CONSUMER_SECRET"), password=True)
    x_access_token = get_input("X Access Token", validate_x_token, defaults.get("X_ACCESS_TOKEN"), password=True)
    x_access_token_secret = get_input("X Access Token Secret", validate_x_token, defaults.get("X_ACCESS_TOKEN_SECRET"), password=True)
    
    # Google Sheets設定
    print("\nGoogle Sheets設定:")
    sheets_credentials_path = get_input("Sheets API認証ファイルのパス", default=defaults.get("SHEETS_CREDENTIALS_PATH", "credentials/sheets_credentials.json"))
    spreadsheet_id = get_input("スプレッドシートID", validate_spreadsheet_id, defaults.get("SPREADSHEET_ID"))
    
    # .envファイルに書き込み
    env_content = f"""# Discord-X-Support-Hub 環境変数設定
# {time.strftime("%Y-%m-%d %H:%M")}に生成

# Discord設定
DISCORD_TOKEN={discord_token}

# X (Twitter) API設定
X_CONSUMER_KEY={x_consumer_key}
X_CONSUMER_SECRET={x_consumer_secret}
X_ACCESS_TOKEN={x_access_token}
X_ACCESS_TOKEN_SECRET={x_access_token_secret}

# Google Sheets設定
SHEETS_CREDENTIALS_PATH={sheets_credentials_path}
SPREADSHEET_ID={spreadsheet_id}
"""
    
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print("\n✅ 環境変数の設定が完了しました。")
    
def create_directories():
    """必要なディレクトリを作成"""
    print("\n[2/4] ディレクトリ構造の作成")
    print("-" * 30)
    
    directories = [
        "logs",
        "exports",
        "credentials",
        "config",
        "data"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ {directory}/")
    
    print("\n✅ ディレクトリ構造の作成が完了しました。")

def setup_config_files():
    """設定ファイルのセットアップ"""
    print("\n[3/4] 設定ファイルの作成")
    print("-" * 30)
    
    # カテゴリキーワード設定
    category_keywords = {
        "product": ["製品", "商品", "使い方", "機能", "操作", "マニュアル", "説明書"],
        "technical": ["エラー", "不具合", "バグ", "動かない", "表示されない", "クラッシュ", "落ちる", "遅い"],
        "billing": ["請求", "支払い", "料金", "価格", "返金", "課金", "購入", "注文", "キャンセル"],
        "complaint": ["クレーム", "不満", "改善", "悪い", "最悪", "ひどい", "残念", "失望"],
        "feature": ["要望", "追加", "機能リクエスト", "欲しい", "実装", "希望", "今後"]
    }
    
    config_path = Path("config/category_keywords.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(category_keywords, f, ensure_ascii=False, indent=2)
    
    print(f"✓ {config_path}")
    
    # サンプルAPIレスポンス設定（デバッグ用）
    sample_responses = {
        "search_mentions": {
            "data": [
                {
                    "id": "1234567890",
                    "text": "@yourcompany 製品の使い方がわかりません。説明書はどこにありますか？",
                    "author_id": "987654321",
                    "created_at": "2025-05-06T10:00:00Z"
                }
            ]
        },
        "get_user": {
            "data": {
                "id": "987654321",
                "name": "サンプルユーザー",
                "username": "sampleuser"
            }
        }
    }
    
    config_path = Path("config/sample_responses.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(sample_responses, f, ensure_ascii=False, indent=2)
    
    print(f"✓ {config_path}")
    
    print("\n✅ 設定ファイルの作成が完了しました。")

def check_requirements():
    """依存パッケージの確認"""
    print("\n[4/4] 依存パッケージの確認")
    print("-" * 30)
    
    required_packages = [
        "discord.py",
        "tweepy",
        "gspread",
        "google-auth",
        "pandas",
        "gspread-dataframe",
        "python-dotenv",
        "nltk"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_").split("==")[0])
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - インストールが必要です")
            missing_packages.append(package)
    
    if missing_packages:
        print("\n以下のパッケージをインストールする必要があります:")
        print(f"pip install {' '.join(missing_packages)}")
        
        install = get_input("\n今すぐインストールしますか？ (y/n)", default="y")
        if install.lower() == "y":
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
                print("\n✅ パッケージのインストールが完了しました。")
            except Exception as e:
                print(f"\n❌ パッケージのインストールに失敗しました: {e}")
                print("手動でインストールしてください。")
    else:
        print("\n✅ すべての依存パッケージがインストールされています。")

def main():
    """メイン実行関数"""
    print_header()
    
    print("Discord-X-Support-Hubのセットアップを開始します...\n")
    
    # 環境変数ファイルの設定
    setup_env_file()
    
    # ディレクトリ構造の作成
    create_directories()
    
    # 設定ファイルのセットアップ
    setup_config_files()
    
    # 依存パッケージの確認
    check_requirements()
    
    print("\n" + "=" * 60)
    print("     セットアップが完了しました！")
    print("=" * 60)
    print("\nスプレッドシートを以下の構成で作成してください:")
    print("1. 'queries' シート (問い合わせ管理)")
    print("2. 'templates' シート (返信テンプレート)")
    print("3. 'stats' シート (統計情報)")
    print("\n以下のコマンドでBotを起動できます:")
    print("python src/main.py")
    print("-" * 60 + "\n")

if __name__ == "__main__":
    main()