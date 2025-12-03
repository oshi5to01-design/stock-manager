import sqlite3
import configparser
import os
from datetime import datetime

# ==================================================================================
# 設定読み込み
# ==================================================================================
config = configparser.ConfigParser()
if os.path.exists("config.ini"):
    config.read("config.ini", encoding="utf-8")
    DB_FILE = config["DATABASE"]["path"]
else:
    DB_FILE = "inventory.db"


# ==================================================================================
# ユーティリティ関数
# ==================================================================================
def get_db_connection():
    """データベースへの接続を確立し、接続オブジェクトを返す"""
    # データベースがロックされている場合、最大20秒間待機してからエラーを出す
    conn = sqlite3.connect(DB_FILE, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn


# ==================================================================================
# データ読み取り（Read）
# ==================================================================================
def get_autocomplete_suggestions(column_name, search_term):
    """指定された列から「前方一致」する候補をSQLで検索する"""
    if not search_term:
        return []

    conn = get_db_connection()
    try:
        query = f"SELECT DISTINCT {column_name} FROM inventory WHERE CAST({column_name} AS TEXT) LIKE ? ORDER BY {column_name}"
        suggestions = conn.execute(query, (search_term + "%",)).fetchall()
        return [row[column_name] for row in suggestions]
    finally:
        conn.close()


def get_item_details_by_model(model_number):
    """指定された型番のレコードをデータベースから取得し、辞書として返す"""
    conn = get_db_connection()
    try:
        query = "SELECT * FROM inventory WHERE 型番 = ?"
        item = conn.execute(query, (model_number,)).fetchone()
        return dict(item) if item else None
    finally:
        conn.close()


# ==================================================================================
# 司令塔部門（Controller / Writer）
# ==================================================================================
def run_main_process_from_ui(input_data):
    """UIから受け取ったデータに基づき、在庫の更新または新規登録を実行する"""

    # 1. 入力データのサニタイズ
    try:
        if input_data.get("数量") and str(input_data["数量"]).strip() != "":
            hankaku_quantity = str(input_data["数量"]).translate(
                str.maketrans("０１２３４５６７８９", "0123456789")
            )
            input_data["数量"] = int(hankaku_quantity)
        else:
            input_data["数量"] = None
    except (ValueError, TypeError):
        return {"success": False, "message": "数量には数字を入力してください。"}

    if input_data.get("保管場所") and isinstance(input_data["保管場所"], str):
        zen = "０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
        han = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        input_data["保管場所"] = input_data["保管場所"].translate(
            str.maketrans(zen, han)
        )

    # 2. 必須項目のチェック
    if (
        input_data.get("製品名") is None or str(input_data["製品名"]).strip() == ""
    ) or (input_data.get("数量") is None):
        return {"success": False, "message": "製品名と数量は必須です。"}

    # 3. データベース更新処理
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 4. 既存レコードの確認
        cursor.execute(
            "SELECT * FROM inventory WHERE 型番 = ?", (str(input_data.get("型番", "")),)
        )
        existing_item = cursor.fetchone()

        final_stock = 0

        if existing_item:
            # --- 更新処理 ---
            current_stock = int(existing_item["現在数量"])
            quantity = input_data["数量"]
            action = input_data["処理種別"]

            if action == "補充":
                new_stock = current_stock + quantity
            else:
                new_stock = current_stock - quantity
                if new_stock < 0:
                    new_stock = 0

            final_stock = new_stock

            cursor.execute(
                "UPDATE inventory SET 現在数量 = ?, 保管場所 = ? WHERE 型番 = ?",
                (new_stock, input_data["保管場所"], str(input_data["型番"])),
            )
        else:
            # --- 新規登録処理 ---
            final_stock = input_data["数量"]
            if final_stock < 0:
                final_stock = 0

            cursor.execute(
                "INSERT INTO inventory (型番,製品名,カテゴリ,メーカー,現在数量,保管場所) VALUES (?,?,?,?,?,?)",
                (
                    input_data["型番"],
                    input_data["製品名"],
                    input_data["カテゴリ"],
                    input_data["メーカー"],
                    final_stock,
                    input_data["保管場所"],
                ),
            )

        # 5. 履歴の記録
        history_quantity = (
            input_data["数量"]
            if input_data["処理種別"] != "使用"
            else -input_data["数量"]
        )

        cursor.execute(
            "INSERT INTO history (日時,型番,製品名,カテゴリ,メーカー,数量,在庫数量) VALUES (?,?,?,?,?,?,?)",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                input_data["型番"],
                input_data["製品名"],
                input_data["カテゴリ"],
                input_data["メーカー"],
                history_quantity,
                final_stock,
            ),
        )

        # 6. コミット（確定）
        conn.commit()
        return {"success": True, "message": "データベースの更新が完了しました！"}

    except sqlite3.OperationalError as e:
        conn.rollback()
        # エラーメッセージに "locked" が含まれていたら、同時アクセスエラー
        if "locked" in str(e):
            return {
                "success": False,
                "message": "現在、他の人が編集中です。\n20秒待機しましたが解除されませんでした。\n少し時間を置いてから再度実行してください。",
            }
        else:
            # その他のOperationalError
            return {
                "success": False,
                "message": f"データベース操作エラーが発生しました:\n{str(e)}",
            }

    except Exception as e:
        conn.rollback()
        import traceback

        traceback.print_exc()
        return {
            "success": False,
            "message": f"予期せぬエラーが発生しました:\n{str(e)}",
        }
    finally:
        conn.close()
