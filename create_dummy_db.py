import sqlite3
import random
from datetime import datetime, timedelta

# 作成するDBファイル名
DB_FILE = "inventory.db"


def create_dummy_database():
    print(f"🔨 {DB_FILE} を作成中...")

    # データベースに接続
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # ---------------------------------------------------------
    # 1. テーブルの作成
    # ---------------------------------------------------------

    # inventoryテーブル（在庫）
    # 1列目: No. (自動連番) ※ドットを含むためダブルクォートで囲む
    # 2列目: 型番
    # 3列目: 製品名
    # 4列目: カテゴリ
    # 5列目: メーカー
    # 6列目: 現在数量
    # 7列目: 保管場所 (数字)
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS inventory (
        "No." INTEGER PRIMARY KEY AUTOINCREMENT,
        型番 TEXT UNIQUE,
        製品名 TEXT,
        カテゴリ TEXT,
        メーカー TEXT,
        現在数量 INTEGER,
        保管場所 INTEGER
    )
    """
    )

    # historyテーブル（履歴）
    # 1列目: 日時
    # 2列目: 型番
    # 3列目: 製品名
    # 4列目: カテゴリ
    # 5列目: メーカー
    # 6列目: 数量（移動数）
    # 7列目: 在庫数量（残数）
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS history (
        日時 TIMESTAMP,
        型番 TEXT,
        製品名 TEXT,
        カテゴリ TEXT,
        メーカー TEXT,
        数量 INTEGER,
        在庫数量 INTEGER
    )
    """
    )

    # ---------------------------------------------------------
    # 2. ダミーデータの準備
    # ---------------------------------------------------------

    # 保管場所（箱No.）を数字に変更
    sample_items = [
        ("CBL-HDMI-10", "HDMIケーブル 1m", "ケーブル", "エレコム", 101),
        ("CBL-LAN-50", "LANケーブル 5m", "ケーブル", "サンワサプライ", 102),
        ("MSE-WL-BK", "ワイヤレスマウス 黒", "周辺機器", "ロジクール", 205),
        ("KBD-MECH-RD", "メカニカルキーボード 赤軸", "周辺機器", "Razer", 206),
        ("SCR-M4-10", "M4ネジ 10mm 100本入", "消耗品", "トラスコ", 301),
        ("WSH-M6", "M6ワッシャー", "消耗品", "トラスコ", 302),
        ("INK-BK-350", "プリンタインク 350XL", "消耗品", "Canon", 401),
        ("CLN-TISSUE", "除菌ウェットティッシュ", "備品", "エリエール", 999),
        ("MON-24-IPS", "24インチIPSモニター", "PC機器", "Dell", 503),
        ("HUB-USB-4P", "USBハブ 4ポート", "周辺機器", "Anker", 103),
    ]

    print("📦 在庫データを投入中...")

    # ---------------------------------------------------------
    # 3. データの投入
    # ---------------------------------------------------------

    for item in sample_items:
        model, name, category, maker, location = item

        # ランダムな在庫数 (10〜100)
        current_qty = random.randint(10, 100)

        # inventoryテーブルへ登録
        try:
            cursor.execute(
                """
            INSERT INTO inventory (型番, 製品名, カテゴリ, メーカー, 現在数量, 保管場所)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
                (model, name, category, maker, current_qty, location),
            )

            # historyテーブルへ「初期登録」としての履歴を追加
            random_days = random.randint(0, 30)
            past_date = datetime.now() - timedelta(days=random_days)

            cursor.execute(
                """
            INSERT INTO history (日時, 型番, 製品名, カテゴリ, メーカー, 数量, 在庫数量)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (past_date, model, name, category, maker, current_qty, current_qty),
            )

            # ランダムで「使用」や「補充」の履歴を追加
            if random.choice([True, False]):
                use_qty = random.randint(1, 5)
                action_date = past_date + timedelta(days=random.randint(1, 5))

                # 履歴のみ追加（在庫数は計算上のもの）
                cursor.execute(
                    """
                INSERT INTO history (日時, 型番, 製品名, カテゴリ, メーカー, 数量, 在庫数量)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        action_date,
                        model,
                        name,
                        category,
                        maker,
                        -use_qty,
                        current_qty - use_qty,
                    ),
                )

        except sqlite3.IntegrityError:
            print(f"⚠️ 重複スキップ: {model}")

    conn.commit()
    conn.close()
    print("✅ 完了！ 'inventory.db' が作成されました。")


if __name__ == "__main__":
    create_dummy_database()
