#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Discord-X-Support-Hub
メインプログラム: Botの初期化と実行
"""

import os
import asyncio
import logging
from datetime import datetime

from discord_bot.bot import SupportBot
from x_monitor.api_client import XMonitor
from data_manager.sheets import SheetsManager

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/support_hub_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 環境変数
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
X_CONSUMER_KEY = os.environ.get("X_CONSUMER_KEY")
X_CONSUMER_SECRET = os.environ.get("X_CONSUMER_SECRET")
X_ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET")
SHEETS_CREDENTIALS_PATH = os.environ.get("SHEETS_CREDENTIALS_PATH", "credentials/sheets_credentials.json")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")

async def check_x_mentions(bot, x_monitor, sheets_manager):
    """X上の新規メンションを定期的に確認するタスク"""
    logger.info("Xモニタリングタスクを開始しました")
    while True:
        try:
            # 新規メンションを確認
            mentions = await x_monitor.check_new_mentions()

            for mention in mentions:
                # 問い合わせとして処理
                query_data = await x_monitor.process_tweet(mention)

                # スプレッドシートに記録
                query_id = await sheets_manager.log_query(query_data)
                query_data['query_id'] = query_id

                # Discordに転送
                await bot.forward_query(query_data)

                logger.info(f"問い合わせ処理完了: {query_id} ({query_data['username']})")

            # 統計情報を更新
            if mentions:
                await sheets_manager.update_stats()

        except Exception as e:
            logger.error(f"Xモニタリング中にエラーが発生しました: {e}", exc_info=True)

        # 10分(600秒)待機
        await asyncio.sleep(600)

async def main():
    """メイン実行関数"""
    try:
        logger.info("Discord-X-Support-Hub を起動中...")

        # X APIクライアントを初期化
        x_api_credentials = {
            'consumer_key': X_CONSUMER_KEY,
            'consumer_secret': X_CONSUMER_SECRET,
            'access_token': X_ACCESS_TOKEN,
            'access_token_secret': X_ACCESS_TOKEN_SECRET
        }
        x_monitor = XMonitor(x_api_credentials)

        # スプレッドシート管理を初期化
        sheets_manager = SheetsManager(SHEETS_CREDENTIALS_PATH)
        sheets_manager.set_spreadsheet_id(SPREADSHEET_ID)

        # テンプレートを読み込み
        templates = await sheets_manager.get_templates()

        # Discordボットを初期化
        bot = SupportBot(templates, sheets_manager)

        # X監視タスクを開始
        bot.loop.create_task(check_x_mentions(bot, x_monitor, sheets_manager))

        # Botを起動
        await bot.start(DISCORD_TOKEN)

    except Exception as e:
        logger.critical(f"アプリケーション起動中に致命的なエラーが発生しました: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    # ログディレクトリの作成
    os.makedirs("logs", exist_ok=True)

    # メイン関数を実行
    asyncio.run(main())