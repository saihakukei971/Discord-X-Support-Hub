#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Discord-X-Support-Hub
スプレッドシート連携: Google Sheetsとの連携機能
"""

import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe, get_as_dataframe

logger = logging.getLogger(__name__)

# スコープの設定
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class SheetsManager:
    """Google Sheetsとの連携を管理するクラス"""

    def __init__(self, credentials_path):
        """初期化"""
        self.credentials_path = credentials_path
        self.spreadsheet_id = None
        self.client = None
        self._init_client()

    def _init_client(self):
        """Google Sheets APIクライアントを初期化"""
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=SCOPES
            )
            self.client = gspread.authorize(credentials)
            logger.info("Google Sheets APIクライアントが初期化されました")
        except Exception as e:
            logger.error(f"Google Sheets APIクライアントの初期化に失敗しました: {e}", exc_info=True)
            raise

    def set_spreadsheet_id(self, spreadsheet_id):
        """スプレッドシートIDを設定"""
        self.spreadsheet_id = spreadsheet_id

    def _get_sheet(self, sheet_name):
        """指定したシートを取得"""
        try:
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            return worksheet
        except Exception as e:
            logger.error(f"シート '{sheet_name}' の取得に失敗しました: {e}", exc_info=True)
            return None

    async def log_query(self, query_data):
        """問い合わせデータをスプレッドシートに記録"""
        try:
            sheet = self._get_sheet("queries")
            if not sheet:
                raise Exception("queries シートが見つかりません")

            # 最新の問い合わせIDを取得
            existing_ids = sheet.col_values(1)[1:]  # ヘッダーを除く
            if existing_ids:
                last_id = existing_ids[-1]
                query_num = int(last_id.replace("Q", "")) + 1
            else:
                query_num = 1

            # 新しい問い合わせIDを生成
            query_id = f"Q{query_num:03d}"

            # スプレッドシートに追加するデータを準備
            row_data = [
                query_id,
                query_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                query_data.get("platform", "X"),
                query_data.get("username", "不明"),
                query_data.get("content", ""),
                query_data.get("category", "general"),
                query_data.get("status", "未対応"),
                "",  # assigned_to
                "",  # response
                ""   # resolved_at
            ]

            # スプレッドシートに追加
            sheet.append_row(row_data)

            logger.info(f"問い合わせ {query_id} をスプレッドシートに記録しました")
            return query_id

        except Exception as e:
            logger.error(f"問い合わせの記録に失敗しました: {e}", exc_info=True)
            raise

    async def update_assigned(self, query_id, assigned_to):
        """担当者を更新"""
        try:
            sheet = self._get_sheet("queries")
            if not sheet:
                raise Exception("queries シートが見つかりません")

            # IDの行を検索
            cell = sheet.find(query_id)
            if not cell:
                raise Exception(f"問い合わせ {query_id} が見つかりません")

            # assigned_to列（8列目）を更新
            sheet.update_cell(cell.row, 8, assigned_to)

            # status列（7列目）を「対応中」に更新
            sheet.update_cell(cell.row, 7, "対応中")

            logger.info(f"問い合わせ {query_id} の担当者を {assigned_to} に更新しました")
            return True

        except Exception as e:
            logger.error(f"担当者の更新に失敗しました: {e}", exc_info=True)
            raise

    async def update_response(self, query_id, response):
        """返信内容を更新"""
        try:
            sheet = self._get_sheet("queries")
            if not sheet:
                raise Exception("queries シートが見つかりません")

            # IDの行を検索
            cell = sheet.find(query_id)
            if not cell:
                raise Exception(f"問い合わせ {query_id} が見つかりません")

            # response列（9列目）を更新
            sheet.update_cell(cell.row, 9, response)

            logger.info(f"問い合わせ {query_id} の返信内容を更新しました")
            return True

        except Exception as e:
            logger.error(f"返信内容の更新に失敗しました: {e}", exc_info=True)
            raise

    async def update_status(self, query_id, status):
        """ステータスを更新"""
        try:
            sheet = self._get_sheet("queries")
            if not sheet:
                raise Exception("queries シートが見つかりません")

            # IDの行を検索
            cell = sheet.find(query_id)
            if not cell:
                raise Exception(f"問い合わせ {query_id} が見つかりません")

            # status列（7列目）を更新
            sheet.update_cell(cell.row, 7, status)

            logger.info(f"問い合わせ {query_id} のステータスを {status} に更新しました")
            return True

        except Exception as e:
            logger.error(f"ステータスの更新に失敗しました: {e}", exc_info=True)
            raise

    async def update_resolved_time(self, query_id):
        """解決時間を更新"""
        try:
            sheet = self._get_sheet("queries")
            if not sheet:
                raise Exception("queries シートが見つかりません")

            # IDの行を検索
            cell = sheet.find(query_id)
            if not cell:
                raise Exception(f"問い合わせ {query_id} が見つかりません")

            # resolved_at列（10列目）を更新
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.update_cell(cell.row, 10, current_time)

            logger.info(f"問い合わせ {query_id} の解決時間を更新しました")
            return True

        except Exception as e:
            logger.error(f"解決時間の更新に失敗しました: {e}", exc_info=True)
            raise

    async def get_query(self, query_id):
        """問い合わせデータを取得"""
        try:
            sheet = self._get_sheet("queries")
            if not sheet:
                raise Exception("queries シートが見つかりません")

            # ヘッダーを取得
            headers = sheet.row_values(1)

            # IDの行を検索
            cell = sheet.find(query_id)
            if not cell:
                return None

            # 行データを取得
            row_data = sheet.row_values(cell.row)

            # 辞書形式でデータを返す
            query_data = {}
            for i, header in enumerate(headers):
                if i < len(row_data):
                    query_data[header] = row_data[i]
                else:
                    query_data[header] = ""

            return query_data

        except Exception as e:
            logger.error(f"問い合わせデータの取得に失敗しました: {e}", exc_info=True)
            return None

    async def get_templates(self):
        """テンプレートデータを取得"""
        try:
            sheet = self._get_sheet("templates")
            if not sheet:
                raise Exception("templates シートが見つかりません")

            # ヘッダーを取得
            headers = sheet.row_values(1)

            # すべての行データを取得
            all_data = sheet.get_all_values()[1:]  # ヘッダーを除く

            # テンプレートのリストを作成
            templates = []
            for row in all_data:
                template = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        template[header] = row[i]
                    else:
                        template[header] = ""
                templates.append(template)

            return templates

        except Exception as e:
            logger.error(f"テンプレートデータの取得に失敗しました: {e}", exc_info=True)
            return []

    async def update_stats(self):
        """統計情報を更新"""
        try:
            queries_sheet = self._get_sheet("queries")
            stats_sheet = self._get_sheet("stats")

            if not queries_sheet or not stats_sheet:
                raise Exception("必要なシートが見つかりません")

            # 今日の日付
            today = datetime.now().strftime("%Y-%m-%d")

            # 今日のデータがあるか確認
            date_cell = stats_sheet.find(today)

            # クエリデータを取得
            query_data = get_as_dataframe(queries_sheet)

            # 今日の問い合わせ数をカウント
            today_queries = query_data[query_data['timestamp'].str.startswith(today)]
            total_queries = len(today_queries)

            # 解決済みの問い合わせ数
            resolved_queries = len(today_queries[today_queries['status'].isin(['完了', 'クローズ'])])

            # 平均応答時間を計算（簡易版）
            avg_response_time = 0
            resolved_count = 0

            for idx, row in today_queries.iterrows():
                if pd.notna(row['timestamp']) and pd.notna(row['resolved_at']) and row['resolved_at']:
                    try:
                        start_time = datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S")
                        end_time = datetime.strptime(row['resolved_at'], "%Y-%m-%d %H:%M:%S")
                        response_time = (end_time - start_time).total_seconds() / 60  # 分単位
                        avg_response_time += response_time
                        resolved_count += 1
                    except:
                        pass

            if resolved_count > 0:
                avg_response_time = round(avg_response_time / resolved_count, 1)

            # 最も多いカテゴリを特定
            if not today_queries.empty:
                top_category = today_queries['category'].value_counts().idxmax()
            else:
                top_category = "N/A"

            # 統計データを更新または追加
            if date_cell:
                # 既存の行を更新
                stats_sheet.update_cell(date_cell.row, 2, total_queries)
                stats_sheet.update_cell(date_cell.row, 3, resolved_queries)
                stats_sheet.update_cell(date_cell.row, 4, avg_response_time)
                stats_sheet.update_cell(date_cell.row, 5, top_category)
            else:
                # 新しい行を追加
                stats_sheet.append_row([today, total_queries, resolved_queries, avg_response_time, top_category])

            logger.info(f"{today} の統計情報を更新しました")
            return True

        except Exception as e:
            logger.error(f"統計情報の更新に失敗しました: {e}", exc_info=True)
            return False

    async def get_todays_stats(self):
        """今日の統計情報を取得"""
        try:
            stats_sheet = self._get_sheet("stats")
            if not stats_sheet:
                raise Exception("stats シートが見つかりません")

            # 今日の日付
            today = datetime.now().strftime("%Y-%m-%d")

            # 統計データを探す
            date_cell = stats_sheet.find(today)

            if date_cell:
                # 行データを取得
                row_data = stats_sheet.row_values(date_cell.row)

                # 統計情報を辞書形式で返す
                return {
                    "date": row_data[0],
                    "total_queries": row_data[1],
                    "resolved_queries": row_data[2],
                    "average_response_time": row_data[3],
                    "top_category": row_data[4] if len(row_data) > 4 else "N/A"
                }
            else:
                # データがない場合は現在のクエリから集計
                await self.update_stats()
                return await self.get_todays_stats()

        except Exception as e:
            logger.error(f"統計情報の取得に失敗しました: {e}", exc_info=True)
            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_queries": 0,
                "resolved_queries": 0,
                "average_response_time": 0,
                "top_category": "N/A"
            }

    async def export_queries(self, days=7):
        """問い合わせデータをエクスポート"""
        try:
            sheet = self._get_sheet("queries")
            if not sheet:
                raise Exception("queries シートが見つかりません")

            # 全データを取得
            all_data = get_as_dataframe(sheet)

            # 指定日数分のデータをフィルタリング
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            filtered_data = all_data[all_data['timestamp'] >= start_date]

            if filtered_data.empty:
                return None

            # CSVとして保存
            export_file = f"exports/queries_export_{datetime.now().strftime('%Y%m%d')}.csv"
            os.makedirs("exports", exist_ok=True)
            filtered_data.to_csv(export_file, index=False, encoding='utf-8')

            logger.info(f"問い合わせデータを {export_file} にエクスポートしました")
            return export_file

        except Exception as e:
            logger.error(f"データエクスポート中にエラーが発生しました: {e}", exc_info=True)
            return None

    async def search_queries(self, keyword):
        """キーワードで問い合わせを検索"""
        try:
            sheet = self._get_sheet("queries")
            if not sheet:
                raise Exception("queries シートが見つかりません")

            # 全データを取得
            all_data = get_as_dataframe(sheet)

            # キーワード検索（内容・ユーザー名・カテゴリ）
            keyword = keyword.lower()
            results = all_data[
                all_data['content'].str.lower().str.contains(keyword, na=False) |
                all_data['username'].str.lower().str.contains(keyword, na=False) |
                all_data['category'].str.lower().str.contains(keyword, na=False)
            ]

            # 結果を辞書のリストとして返す
            return results.to_dict('records')

        except Exception as e:
            logger.error(f"検索中にエラーが発生しました: {e}", exc_info=True)
            return []

    async def analyze_queries(self, period="week"):
        """問い合わせデータを分析"""
        try:
            sheet = self._get_sheet("queries")
            if not sheet:
                raise Exception("queries シートが見つかりません")

            # 全データを取得
            all_data = get_as_dataframe(sheet)

            # 期間に基づいて日付範囲を設定
            end_date = datetime.now()
            if period == "day":
                start_date = end_date - timedelta(days=1)
            elif period == "week":
                start_date = end_date - timedelta(weeks=1)
            elif period == "month":
                start_date = end_date - timedelta(days=30)
            elif period == "year":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(weeks=1)

            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            # 期間内のデータをフィルタリング
            filtered_data = all_data[all_data['timestamp'] >= start_date_str]

            if filtered_data.empty:
                return None

            # 基本統計情報
            total_queries = len(filtered_data)
            resolved_queries = len(filtered_data[filtered_data['status'].isin(['完了', 'クローズ'])])
            resolution_rate = round((resolved_queries / total_queries) * 100, 1) if total_queries > 0 else 0

            # カテゴリ分布
            category_counts = filtered_data['category'].value_counts()
            categories = {}
            for category, count in category_counts.items():
                percentage = round((count / total_queries) * 100, 1)
                categories[category] = (count, percentage)

            # 平均応答・解決時間
            avg_first_response_time = 0
            avg_resolution_time = 0
            response_count = 0
            resolution_count = 0

            for idx, row in filtered_data.iterrows():
                if pd.notna(row['timestamp']) and pd.notna(row['response']) and row['response']:
                    # 簡易版：実際には返信時間のカラムが別途必要
                    response_count += 1

                if pd.notna(row['timestamp']) and pd.notna(row['resolved_at']) and row['resolved_at']:
                    try:
                        start_time = datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S")
                        end_time = datetime.strptime(row['resolved_at'], "%Y-%m-%d %H:%M:%S")
                        resolution_time = (end_time - start_time).total_seconds() / 60  # 分単位
                        avg_resolution_time += resolution_time
                        resolution_count += 1
                    except:
                        pass

            if response_count > 0:
                avg_first_response_time = 30  # 簡易版：実際には計算が必要

            if resolution_count > 0:
                avg_resolution_time = round(avg_resolution_time / resolution_count, 1)

            # トレンド分析（簡易版）
            if total_queries > 5:
                trend = "問い合わせ数は安定しています。"
                if "complaint" in categories and categories["complaint"][1] > 30:
                    trend = "苦情の割合が高くなっています。早急な対応が必要です。"
                elif resolution_rate < 50:
                    trend = "解決率が低下しています。サポート体制の強化を検討してください。"
                elif avg_resolution_time > 120:  # 2時間以上
                    trend = "解決までの時間が長くなっています。効率化が必要です。"
            else:
                trend = "分析するデータが不足しています。"

            # 分析結果を返す
            return {
                "start_date": start_date_str,
                "end_date": end_date_str,
                "total_queries": total_queries,
                "resolved_queries": resolved_queries,
                "resolution_rate": resolution_rate,
                "categories": categories,
                "avg_first_response_time": avg_first_response_time,
                "avg_resolution_time": avg_resolution_time,
                "trend": trend
            }

        except Exception as e:
            logger.error(f"データ分析中にエラーが発生しました: {e}", exc_info=True)
            return None