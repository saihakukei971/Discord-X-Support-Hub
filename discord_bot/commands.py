#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Discord-X-Support-Hub
コマンド実装: Discordコマンドの実装
"""

import discord
from discord.ext import commands
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class SupportCommands(commands.Cog):
    """サポート関連のコマンドを提供するCog"""

    def __init__(self, bot, sheets_manager):
        self.bot = bot
        self.sheets_manager = sheets_manager

    @commands.command(name="export")
    @commands.has_permissions(administrator=True)
    async def export_command(self, ctx, days: int = 7):
        """指定日数分の問い合わせデータをエクスポート"""
        try:
            await ctx.send(f"過去{days}日分の問い合わせデータをエクスポートしています...")

            # データをエクスポート
            file_path = await self.sheets_manager.export_queries(days)

            if not file_path:
                await ctx.send("エクスポートするデータがありませんでした。")
                return

            # ファイルをDiscordに送信
            with open(file_path, 'rb') as f:
                file = discord.File(f, filename=f"support_queries_{days}days.csv")
                await ctx.send(f"過去{days}日分の問い合わせデータです:", file=file)

        except Exception as e:
            logger.error(f"データエクスポート中にエラーが発生しました: {e}", exc_info=True)
            await ctx.send(f"❌ エラーが発生しました: {str(e)}")

    @commands.command(name="search")
    @commands.has_permissions(manage_messages=True)
    async def search_command(self, ctx, *, keyword: str):
        """キーワードで問い合わせを検索"""
        try:
            await ctx.send(f"キーワード「{keyword}」で検索しています...")

            # 検索を実行
            results = await self.sheets_manager.search_queries(keyword)

            if not results:
                await ctx.send("検索結果はありませんでした。")
                return

            # 結果を表示
            embed = discord.Embed(
                title=f"検索結果: {keyword}",
                description=f"{len(results)}件の問い合わせが見つかりました。",
                color=discord.Color.green()
            )

            # 最大5件まで表示
            for i, result in enumerate(results[:5]):
                query_id = result.get("query_id", "不明")
                content = result.get("content", "内容なし")
                username = result.get("username", "不明")
                timestamp = result.get("timestamp", "不明")

                # 内容は最大100文字まで
                if len(content) > 100:
                    content = content[:97] + "..."

                embed.add_field(
                    name=f"{query_id} ({username}, {timestamp})",
                    value=content,
                    inline=False
                )

            if len(results) > 5:
                embed.set_footer(text=f"他に{len(results) - 5}件の結果があります。詳細な検索はスプレッドシートで確認してください。")

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"検索中にエラーが発生しました: {e}", exc_info=True)
            await ctx.send(f"❌ エラーが発生しました: {str(e)}")

    @commands.command(name="analyze")
    @commands.has_permissions(administrator=True)
    async def analyze_command(self, ctx, period: str = "week"):
        """問い合わせ分析レポートを生成"""
        valid_periods = ["day", "week", "month", "year"]
        if period not in valid_periods:
            await ctx.send(f"❌ 無効な期間です。有効な値: {', '.join(valid_periods)}")
            return

        try:
            await ctx.send(f"{period}間の分析レポートを生成しています...")

            # 分析データを取得
            analysis = await self.sheets_manager.analyze_queries(period)

            if not analysis:
                await ctx.send("分析するデータがありませんでした。")
                return

            # 結果を表示
            embed = discord.Embed(
                title=f"{period}間の問い合わせ分析",
                description=f"期間: {analysis.get('start_date', '不明')} から {analysis.get('end_date', '不明')}",
                color=discord.Color.purple()
            )

            # 統計情報
            embed.add_field(name="総問い合わせ数", value=analysis.get("total_queries", 0), inline=True)
            embed.add_field(name="解決済み", value=analysis.get("resolved_queries", 0), inline=True)
            embed.add_field(name="解決率", value=f"{analysis.get('resolution_rate', 0)}%", inline=True)

            # カテゴリ分布
            categories = analysis.get("categories", {})
            if categories:
                category_text = "\n".join([f"{cat}: {count}件 ({percentage}%)" for cat, (count, percentage) in categories.items()])
                embed.add_field(name="カテゴリ分布", value=category_text, inline=False)

            # 平均応答時間
            embed.add_field(name="平均初回応答時間", value=f"{analysis.get('avg_first_response_time', 0)}分", inline=True)
            embed.add_field(name="平均解決時間", value=f"{analysis.get('avg_resolution_time', 0)}分", inline=True)

            # トレンド
            if "trend" in analysis:
                embed.add_field(name="トレンド", value=analysis["trend"], inline=False)

            embed.set_footer(text=f"分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"分析中にエラーが発生しました: {e}", exc_info=True)
            await ctx.send(f"❌ エラーが発生しました: {str(e)}")

    @commands.command(name="clear")
    @commands.has_permissions(administrator=True)
    async def clear_command(self, ctx, channel: discord.TextChannel = None):
        """指定チャンネルのメッセージをクリア"""
        target_channel = channel or ctx.channel

        # 確認メッセージ
        confirm_msg = await ctx.send(f"⚠️ {target_channel.mention} のメッセージをすべて削除しますか？ (y/n)")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['y', 'n']

        try:
            # 返答を待つ
            response = await self.bot.wait_for('message', check=check, timeout=30.0)

            if response.content.lower() == 'y':
                await target_channel.purge(limit=None)
                await ctx.send(f"✅ {target_channel.mention} のメッセージをクリアしました。", delete_after=5)
            else:
                await ctx.send("❌ キャンセルしました。", delete_after=5)

        except asyncio.TimeoutError:
            await ctx.send("⏱️ タイムアウトしました。操作をキャンセルします。", delete_after=5)

        finally:
            # 確認メッセージを削除
            try:
                await confirm_msg.delete()
            except:
                pass

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """コマンドエラーハンドリング"""
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"❌ このコマンドを実行する権限がありません。", delete_after=10)
            return

        if isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ 引数が無効です: {str(error)}", delete_after=10)
            return

        logger.error(f"コマンド実行中にエラーが発生しました: {error}", exc_info=True)
        await ctx.send(f"❌ エラーが発生しました: {str(error)}")

def setup(bot, sheets_manager):
    """Cogをセットアップ"""
    bot.add_cog(SupportCommands(bot, sheets_manager))