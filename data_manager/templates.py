#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Discord-X-Support-Hub
テンプレート管理: 返信テンプレートの管理
"""

import logging
import json
import os
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class TemplateManager:
    """返信テンプレートを管理するクラス"""

    def __init__(self, sheets_manager):
        """初期化"""
        self.sheets_manager = sheets_manager
        self.templates = {}
        self.last_update = None

    async def load_templates(self):
        """スプレッドシートからテンプレートを読み込む"""
        try:
            templates_data = await self.sheets_manager.get_templates()

            # カテゴリ別にテンプレートを整理
            self.templates = {}
            for template in templates_data:
                category = template.get("category", "general")
                template_id = template.get("template_id", "")

                if not template_id:
                    continue

                if category not in self.templates:
                    self.templates[category] = []

                self.templates[category].append(template)

            self.last_update = datetime.now()
            logger.info(f"{len(templates_data)}件のテンプレートを読み込みました")

            return True

        except Exception as e:
            logger.error(f"テンプレートの読み込みに失敗しました: {e}", exc_info=True)
            return False

    async def get_template(self, template_id):
        """指定IDのテンプレートを取得"""
        # 最終更新から1時間以上経過していたら再読み込み
        if not self.last_update or (datetime.now() - self.last_update).total_seconds() > 3600:
            await self.load_templates()

        # すべてのカテゴリからテンプレートを検索
        for category, templates in self.templates.items():
            for template in templates:
                if template.get("template_id") == template_id:
                    return template

        return None

    async def get_templates_by_category(self, category):
        """カテゴリ別のテンプレート一覧を取得"""
        # 最終更新から1時間以上経過していたら再読み込み
        if not self.last_update or (datetime.now() - self.last_update).total_seconds() > 3600:
            await self.load_templates()

        return self.templates.get(category, [])

    async def apply_template(self, template_id, query_data):
        """テンプレートを適用して返信文を生成"""
        template = await self.get_template(template_id)
        if not template:
            return None

        template_text = template.get("template_text", "")

        # 変数置換
        replacements = {
            "{username}": query_data.get("username", "お客様"),
            "{query_id}": query_data.get("query_id", ""),
            "{category}": query_data.get("category", ""),
            "{timestamp}": query_data.get("timestamp", ""),
            "{date}": datetime.now().strftime("%Y年%m月%d日"),
            "{time}": datetime.now().strftime("%H:%M"),
            "{company_name}": "株式会社サンプル",  # 実際には設定ファイルから読み込むべき
            "{support_email}": "support@example.com",
            "{support_phone}": "03-1234-5678"
        }

        for key, value in replacements.items():
            template_text = template_text.replace(key, value)

        return template_text

    async def add_custom_template(self, category, template_text, name=None):
        """カスタムテンプレートを追加"""
        try:
            templates_data = await self.sheets_manager.get_templates()

            # 新しいテンプレートIDを生成
            template_ids = [t.get("template_id", "") for t in templates_data]
            template_numbers = [int(tid.replace("T", "")) for tid in template_ids if tid.startswith("T") and tid[1:].isdigit()]

            next_number = 1
            if template_numbers:
                next_number = max(template_numbers) + 1

            template_id = f"T{next_number:03d}"

            # テンプレート名がない場合はカテゴリ+番号
            if not name:
                name = f"{category.capitalize()} Template {next_number}"

            # スプレッドシートに追加
            sheet = self.sheets_manager._get_sheet("templates")
            row_data = [category, template_id, name, template_text]
            sheet.append_row(row_data)

            # キャッシュを更新
            await self.load_templates()

            logger.info(f"カスタムテンプレート {template_id} を追加しました")
            return template_id

        except Exception as e:
            logger.error(f"カスタムテンプレートの追加に失敗しました: {e}", exc_info=True)
            return None

    async def delete_template(self, template_id):
        """テンプレートを削除"""
        try:
            sheet = self.sheets_manager._get_sheet("templates")

            # テンプレートIDを検索
            cell = sheet.find(template_id)
            if not cell:
                return False

            # 行を削除
            sheet.delete_rows(cell.row)

            # キャッシュを更新
            await self.load_templates()

            logger.info(f"テンプレート {template_id} を削除しました")
            return True

        except Exception as e:
            logger.error(f"テンプレートの削除に失敗しました: {e}", exc_info=True)
            return False

    def get_template_list(self):
        """テンプレート一覧を整形して返す"""
        result = []

        for category, templates in self.templates.items():
            category_items = {
                "category": category,
                "templates": []
            }

            for template in templates:
                template_text = template.get("template_text", "")
                # プレビューは最初の50文字
                preview = template_text[:50] + "..." if len(template_text) > 50 else template_text

                category_items["templates"].append({
                    "id": template.get("template_id", ""),
                    "name": template.get("name", ""),
                    "preview": preview
                })

            result.append(category_items)

        return result