#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Discord-X-Support-Hub
ツイート処理: X (Twitter) からのデータを処理
"""

import logging
import re
import json
import asyncio
from datetime import datetime
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

# 必要なNLTKデータをダウンロード
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class TweetProcessor:
    """ツイートを処理するクラス"""

    def __init__(self):
        """初期化"""
        self.stop_words = set(stopwords.words('japanese') + stopwords.words('english'))
        self.load_category_keywords()

    def load_category_keywords(self):
        """カテゴリ分類のキーワードを読み込み"""
        try:
            with open('config/category_keywords.json', 'r', encoding='utf-8') as f:
                self.category_keywords = json.load(f)

        except Exception as e:
            logger.warning(f"カテゴリキーワードファイルの読み込みに失敗しました: {e}")
            # デフォルトのキーワード設定
            self.category_keywords = {
                "product": ["製品", "商品", "使い方", "機能", "操作", "マニュアル", "説明書"],
                "technical": ["エラー", "不具合", "バグ", "動かない", "表示されない", "クラッシュ", "落ちる", "遅い"],
                "billing": ["請求", "支払い", "料金", "価格", "返金", "課金", "購入", "注文", "キャンセル"],
                "complaint": ["クレーム", "不満", "改善", "悪い", "最悪", "ひどい", "残念", "失望"],
                "feature": ["要望", "追加", "機能リクエスト", "欲しい", "実装", "希望", "今後"]
            }

    async def classify_tweet(self, tweet_text):
        """ツイートの内容を分類"""
        # 前処理
        text = self.preprocess_text(tweet_text)

        # カテゴリごとのスコア計算
        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text.lower())
            category_scores[category] = score

        # 感情分析（簡易版）
        sentiment = await self.analyze_sentiment(tweet_text)

        # 苦情の場合はcomplaintカテゴリのスコアを上げる
        if sentiment < -0.3:
            category_scores["complaint"] = category_scores.get("complaint", 0) + 2

        # 最もスコアが高いカテゴリを選択
        if any(score > 0 for score in category_scores.values()):
            max_category = max(category_scores.items(), key=lambda x: x[1])
            if max_category[1] > 0:
                return max_category[0]

        # デフォルトカテゴリ
        return "general"

    def preprocess_text(self, text):
        """テキストの前処理"""
        # メンションや特殊文字を削除
        text = re.sub(r'@\w+', '', text)  # メンション削除
        text = re.sub(r'#\w+', '', text)  # ハッシュタグ削除
        text = re.sub(r'http\S+', '', text)  # URL削除
        text = re.sub(r'[^\w\s]', '', text)  # 特殊文字削除

        return text.strip()

    async def analyze_sentiment(self, text):
        """感情分析（簡易版）"""
        # ポジティブ/ネガティブワード辞書
        positive_words = [
            "ありがとう", "感謝", "素晴らしい", "良い", "好き", "嬉しい", "助かる",
            "便利", "使いやすい", "快適", "期待", "楽しみ", "great", "good", "thanks",
            "helpful", "excellent", "love", "appreciate"
        ]

        negative_words = [
            "ダメ", "悪い", "問題", "エラー", "不具合", "遅い", "使いにくい", "困る",
            "最悪", "ひどい", "残念", "失望", "不満", "怒り", "待てない", "返金",
            "bad", "terrible", "error", "issue", "problem", "slow", "difficult",
            "disappointed", "frustrating", "useless"
        ]

        # 単語への分割
        words = word_tokenize(text.lower())

        # ポジティブ・ネガティブのカウント
        pos_count = sum(1 for word in words if word in positive_words)
        neg_count = sum(1 for word in words if word in negative_words)

        # 基本スコア計算（-1.0 から 1.0 の範囲）
        total_count = pos_count + neg_count
        if total_count == 0:
            return 0.0

        # ネガティブワードの重みを少し大きくする
        sentiment_score = (pos_count - (neg_count * 1.5)) / (total_count * 1.5)
        return max(-1.0, min(1.0, sentiment_score))  # -1.0〜1.0の範囲に収める

    async def extract_keywords(self, text, max_keywords=5):
        """重要なキーワードを抽出"""
        # 前処理
        processed_text = self.preprocess_text(text)

        # 単語に分割
        words = word_tokenize(processed_text)

        # ストップワードを除去
        filtered_words = [word for word in words if word.lower() not in self.stop_words]

        # 単語の出現回数をカウント
        word_freq = {}
        for word in filtered_words:
            if len(word) > 1:  # 1文字の単語は除外
                word_freq[word] = word_freq.get(word, 0) + 1

        # 出現回数でソートし、上位のキーワードを返す
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:max_keywords]]

    async def generate_summary(self, text, max_length=100):
        """テキストの要約を生成（簡易版）"""
        # 前処理
        processed_text = self.preprocess_text(text)

        # すでに短い場合はそのまま返す
        if len(processed_text) <= max_length:
            return processed_text

        # 文に分割
        sentences = re.split(r'[。.!?！？]', processed_text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # 1文だけの場合は先頭を返す
        if len(sentences) <= 1:
            return sentences[0][:max_length] + "..." if len(sentences[0]) > max_length else sentences[0]

        # 重要度の高い文を選択（ここでは単純に最初の文を重要と見なす）
        summary = sentences[0]

        # 長さが足りない場合は2文目も追加
        if len(summary) < max_length and len(sentences) > 1:
            remaining = max_length - len(summary)
            if len(sentences[1]) <= remaining:
                summary += "。" + sentences[1]
            else:
                summary += "。" + sentences[1][:remaining-1] + "..."

        return summary