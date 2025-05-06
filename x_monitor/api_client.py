#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Discord-X-Support-Hub
X API クライアント: X (Twitter) APIとの通信処理
"""

import tweepy
import logging
import asyncio
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class XMonitor:
    """X (Twitter) APIのモニタリングクラス"""

    def __init__(self, api_credentials):
        """初期化"""
        self.client = tweepy.Client(
            consumer_key=api_credentials['consumer_key'],
            consumer_secret=api_credentials['consumer_secret'],
            access_token=api_credentials['access_token'],
            access_token_secret=api_credentials['access_token_secret'],
            wait_on_rate_limit=True
        )

        self.user_id = None
        self.monitored_keywords = [
            "サポート", "問い合わせ", "質問", "ヘルプ", "不具合", "エラー",
            "使い方", "機能", "要望", "改善", "クレーム", "返金"
        ]
        self.last_check_time = datetime.now() - timedelta(hours=1)

        # 自分のユーザーIDを取得
        self._get_user_id()

    def _get_user_id(self):
        """自分のユーザーIDを取得"""
        try:
            me = self.client.get_me()
            self.user_id = me.data.id
            logger.info(f"X アカウントID: {self.user_id}")

        except Exception as e:
            logger.error(f"ユーザーID取得中にエラーが発生しました: {e}", exc_info=True)

    async def check_new_mentions(self):
        """新しいメンションを確認"""
        try:
            logger.info("新規メンションを確認中...")

            # メンションの取得
            mentions = self.client.get_users_mentions(
                id=self.user_id,
                start_time=self.last_check_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                tweet_fields=["created_at", "text", "author_id", "conversation_id"]
            )

            # DMの取得（実際のAPIでは実装方法が異なる場合があります）
            # この例ではメンションのみを処理

            # 最終確認時間を更新
            self.last_check_time = datetime.now()

            if not mentions.data:
                logger.info("新規メンションはありませんでした")
                return []

            logger.info(f"{len(mentions.data)}件の新規メンションを検出")
            return mentions.data

        except Exception as e:
            logger.error(f"メンション確認中にエラーが発生しました: {e}", exc_info=True)
            return []

    async def process_tweet(self, tweet):
        """ツイートを問い合わせデータに変換"""
        try:
            # ユーザー情報を取得
            user = self.client.get_user(id=tweet.author_id).data

            # ツイートの内容
            content = tweet.text

            # タイムスタンプ
            timestamp = tweet.created_at.strftime("%Y-%m-%d %H:%M:%S")

            # カテゴリを推定
            category = self._estimate_category(content)

            # ツイートURL
            tweet_url = f"https://twitter.com/user/status/{tweet.id}"

            # 問い合わせデータを作成
            query_data = {
                "platform": "X",
                "username": f"@{user.username}",
                "user_id": user.id,
                "content": content,
                "timestamp": timestamp,
                "category": category,
                "status": "未対応",
                "tweet_id": tweet.id,
                "url": tweet_url
            }

            logger.info(f"問い合わせ処理: @{user.username} のツイートをカテゴリ '{category}' として処理")
            return query_data

        except Exception as e:
            logger.error(f"ツイート処理中にエラーが発生しました: {e}", exc_info=True)
            # 最低限の情報を返す
            return {
                "platform": "X",
                "username": f"不明",
                "content": tweet.text if hasattr(tweet, "text") else "内容不明",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "category": "general",
                "status": "未対応"
            }

    def _estimate_category(self, content):
        """問い合わせ内容からカテゴリを推定"""
        content = content.lower()

        # カテゴリごとのキーワード
        category_keywords = {
            "product": ["製品", "商品", "使い方", "機能", "操作"],
            "technical": ["エラー", "不具合", "バグ", "動かない", "表示されない", "クラッシュ"],
            "billing": ["請求", "支払い", "料金", "価格", "返金", "課金"],
            "complaint": ["クレーム", "不満", "改善", "遅い", "悪い"],
            "feature": ["要望", "追加", "機能リクエスト", "欲しい", "実装して"]
        }

        # 各カテゴリのキーワードマッチをカウント
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content)
            category_scores[category] = score

        # 最もスコアが高いカテゴリを選択
        if any(score > 0 for score in category_scores.values()):
            max_category = max(category_scores.items(), key=lambda x: x[1])
            if max_category[1] > 0:
                return max_category[0]

        # デフォルトカテゴリ
        return "general"

    async def reply_to_tweet(self, tweet_id, message):
        """ツイートに返信"""
        try:
            # ツイートに返信
            response = self.client.create_tweet(
                text=message,
                in_reply_to_tweet_id=tweet_id
            )

            logger.info(f"ツイート {tweet_id} に返信しました")
            return response.data.id

        except Exception as e:
            logger.error(f"ツイート返信中にエラーが発生しました: {e}", exc_info=True)
            return None