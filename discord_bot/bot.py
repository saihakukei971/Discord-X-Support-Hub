#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Discord-X-Support-Hub
Discordボット実装: サポートボットのコア機能
"""

import os
import discord
from discord.ext import commands
import logging
import json
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

# サポートカテゴリ設定
SUPPORT_CATEGORIES = {
    "general": "一般的な質問",
    "product": "製品に関する質問",
    "technical": "技術的な問題",
    "billing": "請求に関する問い合わせ",
    "complaint": "苦情・クレーム",
    "feature": "機能リクエスト"
}

class SupportBot(commands.Bot):
    """サポート用Discordボットクラス"""

    def __init__(self, templates, sheets_manager):
        """初期化"""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(command_prefix='!', intents=intents)

        self.support_channels = {}
        self.sheets_manager = sheets_manager
        self.templates = templates

        # コマンドの登録
        self.remove_command("help")  # デフォルトのhelpコマンドを削除
        self._load_commands()

    async def on_ready(self):
        """ボット起動時の処理"""
        logger.info(f"{self.user.name} が起動しました！")

        # アクティビティステータスの設定
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Xのメンション"
        )
        await self.change_presence(activity=activity)

        # サポートチャンネルの設定
        await self.setup_channels()

    async def setup_channels(self):
        """サポート用チャンネルの設定"""
        # サポートカテゴリの確認または作成
        for guild in self.guilds:
            support_category = discord.utils.get(guild.categories, name="サポート")

            if not support_category:
                logger.info(f"サーバー {guild.name} にサポートカテゴリを作成します")
                support_category = await guild.create_category("サポート")

            # 各カテゴリのチャンネル確認
            for category_id, category_name in SUPPORT_CATEGORIES.items():
                channel_name = f"support-{category_id}"
                channel = discord.utils.get(guild.text_channels, name=channel_name)

                if not channel:
                    logger.info(f"チャンネル {channel_name} を作成します")
                    channel = await guild.create_text_channel(
                        name=channel_name,
                        category=support_category,
                        topic=f"{category_name}に関する問い合わせチャンネル"
                    )

                self.support_channels[category_id] = channel

            # 通知用チャンネルの確認
            notification_channel = discord.utils.get(guild.text_channels, name="support-notifications")
            if not notification_channel:
                logger.info("通知用チャンネルを作成します")
                notification_channel = await guild.create_text_channel(
                    name="support-notifications",
                    category=support_category,
                    topic="サポート関連の通知チャンネル"
                )

            self.support_channels["notifications"] = notification_channel

    def _load_commands(self):
        """コマンドを登録"""
        @self.command(name="help")
        async def help_command(ctx):
            """ヘルプコマンド"""
            embed = discord.Embed(
                title="サポートボットコマンド一覧",
                description="以下のコマンドが利用可能です：",
                color=discord.Color.blue()
            )

            commands_list = [
                ("!help", "このヘルプメッセージを表示"),
                ("!assign @ユーザー #問い合わせID", "問い合わせを担当者にアサイン"),
                ("!reply #問い合わせID 返信内容", "問い合わせに返信"),
                ("!template #テンプレートID #問い合わせID", "テンプレートを使用して返信"),
                ("!status #問い合わせID #ステータス", "問い合わせのステータスを更新"),
                ("!stats", "今日の問い合わせ統計を表示")
            ]

            for cmd, desc in commands_list:
                embed.add_field(name=cmd, value=desc, inline=False)

            embed.set_footer(text=f"Discord-X-Support-Hub | {datetime.now().strftime('%Y-%m-%d')}")
            await ctx.send(embed=embed)

        @self.command(name="assign")
        async def assign_command(ctx, member: discord.Member, query_id: str):
            """問い合わせを担当者にアサイン"""
            if not ctx.author.guild_permissions.manage_messages:
                await ctx.send("このコマンドを使用する権限がありません。")
                return

            try:
                await self.sheets_manager.update_assigned(query_id, member.name)
                await ctx.send(f"✅ 問い合わせ {query_id} を {member.mention} にアサインしました。")

                # 通知チャンネルにも通知
                notification = f"📝 {ctx.author.name} が問い合わせ {query_id} を {member.name} にアサインしました。"
                await self.support_channels["notifications"].send(notification)

            except Exception as e:
                logger.error(f"アサイン処理中にエラーが発生しました: {e}")
                await ctx.send(f"❌ エラーが発生しました: {str(e)}")

        @self.command(name="reply")
        async def reply_command(ctx, query_id: str, *, response: str):
            """問い合わせに返信"""
            if not ctx.author.guild_permissions.manage_messages:
                await ctx.send("このコマンドを使用する権限がありません。")
                return

            try:
                # 問い合わせの詳細を取得
                query_data = await self.sheets_manager.get_query(query_id)
                if not query_data:
                    await ctx.send(f"❌ 問い合わせ {query_id} が見つかりません。")
                    return

                # 返信をスプレッドシートに記録
                await self.sheets_manager.update_response(query_id, response)

                # 返信の確認メッセージを送信
                embed = discord.Embed(
                    title=f"問い合わせ {query_id} への返信",
                    description=response,
                    color=discord.Color.green()
                )
                embed.add_field(name="元の問い合わせ", value=query_data.get("content", "内容なし"), inline=False)
                embed.add_field(name="ユーザー", value=query_data.get("username", "不明"), inline=True)
                embed.set_footer(text=f"返信者: {ctx.author.name} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

                await ctx.send(embed=embed)

                # XにAPIで返信するロジックは実際の実装時に追加
                await ctx.send("✅ 返信が記録されました。X上でも返信を行います。")

            except Exception as e:
                logger.error(f"返信処理中にエラーが発生しました: {e}")
                await ctx.send(f"❌ エラーが発生しました: {str(e)}")

        @self.command(name="template")
        async def template_command(ctx, template_id: str, query_id: str):
            """テンプレートを使用して返信"""
            if not ctx.author.guild_permissions.manage_messages:
                await ctx.send("このコマンドを使用する権限がありません。")
                return

            try:
                # テンプレートを取得
                template = None
                for t in self.templates:
                    if t.get("template_id") == template_id:
                        template = t
                        break

                if not template:
                    await ctx.send(f"❌ テンプレート {template_id} が見つかりません。")
                    return

                # 問い合わせの詳細を取得
                query_data = await self.sheets_manager.get_query(query_id)
                if not query_data:
                    await ctx.send(f"❌ 問い合わせ {query_id} が見つかりません。")
                    return

                # テンプレートの変数を置換
                response_text = template.get("template_text", "")
                response_text = response_text.replace("{username}", query_data.get("username", "お客様"))

                # 返信を記録
                await self.sheets_manager.update_response(query_id, response_text)

                # 返信の確認メッセージを送信
                embed = discord.Embed(
                    title=f"テンプレート {template_id} での返信",
                    description=response_text,
                    color=discord.Color.blue()
                )
                embed.add_field(name="問い合わせID", value=query_id, inline=True)
                embed.add_field(name="ユーザー", value=query_data.get("username", "不明"), inline=True)
                embed.set_footer(text=f"返信者: {ctx.author.name} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

                await ctx.send(embed=embed)

                # XにAPIで返信するロジックは実際の実装時に追加
                await ctx.send("✅ テンプレート返信が記録されました。X上でも返信を行います。")

            except Exception as e:
                logger.error(f"テンプレート返信処理中にエラーが発生しました: {e}")
                await ctx.send(f"❌ エラーが発生しました: {str(e)}")

        @self.command(name="status")
        async def status_command(ctx, query_id: str, status: str):
            """問い合わせのステータスを更新"""
            if not ctx.author.guild_permissions.manage_messages:
                await ctx.send("このコマンドを使用する権限がありません。")
                return

            valid_statuses = ["未対応", "対応中", "完了", "保留中", "クローズ"]
            if status not in valid_statuses:
                await ctx.send(f"❌ 無効なステータスです。有効なステータス: {', '.join(valid_statuses)}")
                return

            try:
                await self.sheets_manager.update_status(query_id, status)

                # 完了の場合は解決時間も記録
                if status == "完了" or status == "クローズ":
                    await self.sheets_manager.update_resolved_time(query_id)

                await ctx.send(f"✅ 問い合わせ {query_id} のステータスを「{status}」に更新しました。")

                # 通知チャンネルにも通知
                notification = f"🔄 {ctx.author.name} が問い合わせ {query_id} のステータスを「{status}」に更新しました。"
                await self.support_channels["notifications"].send(notification)

            except Exception as e:
                logger.error(f"ステータス更新処理中にエラーが発生しました: {e}")
                await ctx.send(f"❌ エラーが発生しました: {str(e)}")

        @self.command(name="stats")
        async def stats_command(ctx):
            """今日の問い合わせ統計を表示"""
            try:
                stats = await self.sheets_manager.get_todays_stats()

                embed = discord.Embed(
                    title="今日の問い合わせ統計",
                    color=discord.Color.gold()
                )

                embed.add_field(name="総問い合わせ数", value=stats.get("total_queries", 0), inline=True)
                embed.add_field(name="解決済み", value=stats.get("resolved_queries", 0), inline=True)
                embed.add_field(name="平均応答時間", value=f"{stats.get('average_response_time', 0)}分", inline=True)

                if stats.get("top_category"):
                    embed.add_field(name="最多カテゴリ", value=SUPPORT_CATEGORIES.get(stats.get("top_category"), stats.get("top_category")), inline=False)

                embed.set_footer(text=f"集計日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

                await ctx.send(embed=embed)

            except Exception as e:
                logger.error(f"統計取得処理中にエラーが発生しました: {e}")
                await ctx.send(f"❌ エラーが発生しました: {str(e)}")

    async def forward_query(self, query_data):
        """Xからの問い合わせをDiscordに転送する"""
        try:
            # カテゴリに基づいて適切なチャンネルを選択
            category = query_data.get("category", "general")
            if category not in self.support_channels:
                category = "general"

            channel = self.support_channels[category]

            # 問い合わせ内容のEmbed作成
            embed = discord.Embed(
                title=f"新規問い合わせ: {query_data.get('query_id')}",
                description=query_data.get("content", "内容なし"),
                color=discord.Color.blue()
            )

            embed.add_field(name="プラットフォーム", value="X (Twitter)", inline=True)
            embed.add_field(name="ユーザー", value=query_data.get("username", "不明"), inline=True)
            embed.add_field(name="カテゴリ", value=SUPPORT_CATEGORIES.get(category, category), inline=True)
            embed.add_field(name="ステータス", value="未対応", inline=True)
            embed.add_field(name="受信日時", value=query_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M")), inline=True)

            # URLがある場合は追加
            if "url" in query_data and query_data["url"]:
                embed.add_field(name="元ツイートURL", value=query_data["url"], inline=False)

            embed.set_footer(text=f"コマンド: !assign @ユーザー {query_data.get('query_id')} で担当者を割り当て")

            # 通知用メンション
            mention = "@here" if category in ["complaint", "billing"] else ""

            # 送信
            await channel.send(content=mention, embed=embed)

            # 全体通知チャンネルにも通知
            notification = f"📢 新規問い合わせ {query_data.get('query_id')} が {SUPPORT_CATEGORIES.get(category, category)} カテゴリに届きました。"
            await self.support_channels["notifications"].send(notification)

            return True

        except Exception as e:
            logger.error(f"問い合わせ転送中にエラーが発生しました: {e}", exc_info=True)
            return False