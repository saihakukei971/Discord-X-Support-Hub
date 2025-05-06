# Discord-X-Support-Hub

## プロジェクト概要

Discord-X-Support-Hubは、X（旧Twitter）上の問い合わせを自動監視し、Discordチャンネルへ転送することで、企業のカスタマーサポート業務を効率化するシステムです。会社のXアカウント（例：@会社名）へのメンションやDMを自動的に監視し、適切なDiscordチャンネルに通知します。これにより、サポートチームはリアルタイムで問い合わせに対応できます。

**こんな課題を解決します：**
- SNS上の問い合わせ対応に時間がかかる
- 複数プラットフォームでの顧客対応の一元管理が難しい
- サポート対応の履歴や統計を効率的に管理したい
- チーム間でのサポート情報共有を効率化したい

## 使用技術

- **Python 3.10+** - メインプログラミング言語
- **discord.py 2.3.2** - Discord Bot API連携
- **tweepy 4.14.0** - X (Twitter) API連携
- **Google Sheets API** - データベース管理（gspread, google-auth）
- **Google Spreadsheet** - 問い合わせデータ、テンプレート、統計情報の管理

## 処理の流れ

```
X上での問い合わせ → 自動分類・スプレッドシートに記録 → Discordの適切なチャンネルに通知
 → 担当者アサイン・テンプレート返信 → 対応結果をスプレッドシートに更新 → X上で返信
```

## 特徴・工夫した点

1. **マルチチャネル対応**: X、Discord、スプレッドシートの連携による一元管理
2. **自動分類機能**: キーワード分析と感情分析による問い合わせ内容の自動カテゴリ分け
3. **効率化機能**: Webhookを活用した即時通知とテンプレート回答機能
4. **データ分析**: 問い合わせ傾向の可視化と時系列分析
5. **バックグラウンド常駐**: 24時間365日稼働するサービスとして実装

## セットアップ手順

### 前提条件
- Python 3.10以上
- Discordアカウントとサーバー管理権限
- X (Twitter) 開発者アカウント（無料枠で十分）
- Google Cloud Platformアカウント

### 1. リポジトリのクローン
```bash
# リポジトリをクローン
git clone https://github.com/yourusername/Discord-X-Support-Hub.git
cd Discord-X-Support-Hub

# 必要なパッケージをインストール
pip install -r requirements.txt
```

### 2. Google Cloud Platformの設定
1. Google Cloud Consoleにアクセス
2. 新しいプロジェクトを作成
3. Google Sheets APIを有効化
4. サービスアカウントを作成し、JSONキーをダウンロード
5. ダウンロードしたJSONキーを`credentials/sheets_credentials.json`として保存

### 3. スプレッドシートの設定
1. 新しいGoogle Spreadsheetを作成し、「Support-Hub-Database」と名付ける
2. 以下の3つのシートを作成:
   - `queries` - 問い合わせ管理
   - `templates` - 返信テンプレート
   - `stats` - 統計情報
3. サービスアカウントのメールアドレスに編集権限を付与

### 4. Discord Botの設定
1. Discord Developer Portalで新しいアプリケーションを作成
2. BotをDiscordサーバーに追加し、必要な権限を付与

### 5. X (Twitter) API設定
1. Twitter Developer Portalでアプリケーションを作成
2. 必要なAPIキーとトークンを取得

### 6. 環境変数の設定

⚠️ **セキュリティに関する重要な注意** ⚠️

リポジトリには `@env.txt.example` というサンプルファイルが含まれています。**実際の認証情報は絶対にGitHubにアップロードしないでください。**

1. リポジトリ内の `@env.txt.example` をコピーして `@env.txt` を作成します:
   ```bash
   cp @env.txt.example @env.txt
   ```

2. 作成した `@env.txt` ファイルを編集し、以下の項目を実際の値に置き換えます:
   ```
   # Discord設定
   DISCORD_TOKEN=your_discord_bot_token_here

   # X (Twitter) API設定
   X_CONSUMER_KEY=your_x_consumer_key_here
   X_CONSUMER_SECRET=your_x_consumer_secret_here
   X_ACCESS_TOKEN=your_x_access_token_here
   X_ACCESS_TOKEN_SECRET=your_x_access_token_secret_here

   # Google Sheets設定
   SHEETS_CREDENTIALS_PATH=credentials/sheets_credentials.json
   SPREADSHEET_ID=your_spreadsheet_id_here
   ```

3. `.gitignore` ファイルに以下の行が含まれていることを確認してください:
   ```
   # 環境変数とシークレット
   .env
   @env.txt
   credentials/*.json
   ```

このセキュリティ対策により、APIキーやトークンなどの機密情報がGitHubに公開されることを防止できます。

### 7. アプリケーションの起動
サービスを起動するには、付属のバッチファイル `start.bat` (Windows) または `start.sh` (Linux) を使用してください。

## プログラムの起動と停止

### 起動方法
- **Windows**: `start.bat` をダブルクリック
- **Linux**: `./start.sh` を実行

### 停止方法

#### 1. Windows 環境での停止方法
* **① コマンドプロンプトから起動している場合：**
   * 実行中のコンソール上で `Ctrl + C` を押すことで停止
   * または別のコンソールで以下のコマンドを実行（強制終了）：
   ```
   taskkill /F /IM python.exe
   ```

* **② タスクマネージャーからの停止：**
   1. `Ctrl + Shift + Esc` でタスクマネージャーを開く
   2. 「詳細」タブで `python.exe` または `pythonw.exe` を探す
   3. 右クリックして「**タスクの終了**」を選択

* **③ タスクスケジューラから起動している場合：**
   1. スタート → 「タスクスケジューラ」を開く
   2. 対象タスクを右クリック
   3. 「**実行中のタスクを終了**」を選択

#### 2. Linux 環境での停止方法
* **① ターミナルから起動している場合：**
   * `Ctrl + C` で即時停止
   * または以下でPID確認 → 強制終了：
   ```bash
   ps aux | grep python
   kill -9 [対象のPID]
   ```

* **② systemd でサービス管理している場合：**
   ```bash
   sudo systemctl stop discord-x-support-hub
   ```

* **③ supervisor で管理している場合：**
   ```bash
   supervisorctl stop discord-x-support-hub
   ```

## プログラムの更新方法

1. **現在のプログラムを停止**（上記の「停止方法」参照）
2. **最新コードに更新**：
   ```bash
   git pull
   ```
3. **依存ライブラリを更新**（必要な場合）：
   ```bash
   pip install -r requirements.txt
   ```
4. **プログラムを再起動**（`start.bat` または `start.sh` を実行）

## 自動起動設定

### Windows環境での自動起動設定
1. スタートメニューから「タスクスケジューラ」を起動
2. 右側の「**基本タスクの作成**」をクリック
3. 以下を設定：
   * **名前**：Discord-X-Support-Hub（任意）
   * **トリガー**：`コンピューターの起動時`
   * **操作**：`プログラムの開始`
      * プログラム：`C:\path\to\Discord-X-Support-Hub\start.bat` （←フルパスで指定）
4. 「完了」をクリック

### 自動起動されたタスクを停止したい場合：
* 「タスクスケジューラ」から該当タスクを右クリックし「**無効**」を選択
* または、「停止方法」に記載の方法を実施

## スプレッドシート構成

### queries シート（問い合わせ管理）

| 列名 | 説明 | 例 |
|------|------|-----|
| query_id | 問い合わせID | Q001 |
| timestamp | 受信日時 | 2025-05-06 10:30:00 |
| platform | 問い合わせ元 | X |
| username | ユーザー名 | @user123 |
| content | 問い合わせ内容 | 製品の使い方がわかりません |
| category | カテゴリ | product |
| status | 対応状況 | 未対応/対応中/完了/保留中/クローズ |
| assigned_to | 担当者 | @staff1 |
| response | 返信内容 | ご質問ありがとうございます... |
| resolved_at | 解決日時 | 2025-05-06 11:15:00 |

### templates シート（返信テンプレート）

| 列名 | 説明 | 例 |
|------|------|-----|
| category | カテゴリ | product |
| template_id | テンプレートID | T001 |
| name | テンプレート名 | 使い方質問への返信 |
| template_text | テンプレート本文 | {username}様、ご質問ありがとうございます... |

### stats シート（統計情報）

| 列名 | 説明 | 例 |
|------|------|-----|
| date | 日付 | 2025-05-06 |
| total_queries | 総問い合わせ数 | 24 |
| resolved_queries | 解決済み数 | 18 |
| average_response_time | 平均応答時間（分） | 15.5 |
| top_category | 最多カテゴリ | product |


### 以下は実際のスプレッドシートの例です。
https://docs.google.com/spreadsheets/d/1qFnaGxLLAw9KiQSMHHGBrgrByFE6RONqNx-Fr3ehEHw/edit?gid=1160669244#gid=1160669244

## ディレクトリ構成

```
Discord-X-Support-Hub/
├── README.md                # プロジェクト説明
├── requirements.txt         # 必要なPythonパッケージ
├── @env.txt.example         # 環境変数設定例（実際の値を入れて@env.txtとして使用）
├── .gitignore               # Git除外設定（機密ファイルを保護）
├── setup.py                 # セットアップスクリプト
├── main.py                  # メインプログラム（常駐サービス）
├── start.bat                # Windows用起動スクリプト
├── start.sh                 # Linux用起動スクリプト
├── credentials/             # API認証情報
│   └── README.md            # 認証情報の配置手順（実際のJSONは含まない）
├── discord_bot/             # Discordボット関連
│   ├── bot.py               # Botクラス
│   └── commands.py          # コマンド定義
├── x_monitor/               # X監視関連
│   ├── api_client.py        # X API通信
│   └── processor.py         # ツイート処理
└── data_manager/            # データ管理
    ├── sheets.py            # スプレッドシート連携
    └── templates.py         # テンプレート管理
```

## 使用方法

### Discordコマンド
```
!help                         - コマンド一覧を表示
!assign @ユーザー #問い合わせID  - 担当者を割り当て
!reply #問い合わせID 返信内容    - 問い合わせに返信
!template #テンプレートID #問い合わせID - テンプレートで返信
!status #問い合わせID #ステータス - ステータスを更新
!stats                        - 統計情報を表示
!search キーワード             - 問い合わせを検索
```

### 運用例
1. Xで「@会社名 製品の使い方がわかりません」とユーザーが投稿
2. 自動的にDiscordの「support-product」チャンネルに通知
3. サポート担当者が「!assign @staff1 Q001」でアサイン
4. 「!template T001 Q001」で定型文を使って返信
5. 対応完了後「!status Q001 完了」でステータスを更新

## トラブルシューティング

- **認証エラー**: APIキーとトークンの設定を確認
- **Discordへの通知が届かない**: Webhook URLの設定を確認
- **スプレッドシートアクセスエラー**: サービスアカウント権限を確認
- **X APIのレート制限**: APIリクエスト頻度を調整
