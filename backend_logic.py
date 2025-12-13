import psycopg2
from psycopg2.extras import RealDictCursor
import configparser
import os
from datetime import datetime

# ==================================================================================
# 設定読み込み
# ==================================================================================
# ※Postgresの場合はconfig.iniを使わず、コード内で接続情報を管理するか、
# 環境変数を使うのが一般的だが、今回はハードコードで進める
DB_HOST = "localhost"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "password"


# ==================================================================================
# ユーティリティ関数
# ==================================================================================
def get_db_connection():
    """PostgreSQLへの接続を確立する"""
    conn = psycopg2.connect(
        host=DB_HOST, port="5432", database=DB_NAME, user=DB_USER, password=DB_PASS
    )
    return conn, RealDictCursor


# ==================================================================================
# データ読み取り（Read）
# ==================================================================================
def get_autocomplete_suggestions(column_name, search_term):
    """指定された列から「前方一致」する候補をSQLで検索する"""
    if not search_term:
        return []

    # ★修正: 戻り値を2つ受け取る
    conn, cursor_factory = get_db_connection()
    try:
        # ★修正: cursorを作成してから execute する
        with conn.cursor(cursor_factory=cursor_factory) as cursor:
            # 列名はプレースホルダにできないのでF文字列、値は %s
            query = f"SELECT DISTINCT {column_name} FROM inventory WHERE CAST({column_name} AS TEXT) LIKE %s ORDER BY {column_name}"
            cursor.execute(query, (search_term + "%",))
            suggestions = cursor.fetchall()
            return [row[column_name] for row in suggestions]
    finally:
        conn.close()


def get_item_details_by_model(model_number):
    """指定された型番のレコードをデータベースから取得し、辞書として返す"""
    # ★修正: 戻り値を2つ受け取る
    conn, cursor_factory = get_db_connection()
    try:
        with conn.cursor(cursor_factory=cursor_factory) as cursor:
            query = "SELECT * FROM inventory WHERE 型番 = %s"
            cursor.execute(query, (model_number,))
            item = cursor.fetchone()
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
    # ★修正: 戻り値を2つ受け取る
    conn, cursor_factory = get_db_connection()

    try:
        # ★修正: cursorを作成する
        with conn.cursor(cursor_factory=cursor_factory) as cursor:

            # 4. 既存レコードの確認
            cursor.execute(
                "SELECT * FROM inventory WHERE 型番 = %s",
                (str(input_data.get("型番", "")),),
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
                    "UPDATE inventory SET 現在数量 = %s, 保管場所 = %s WHERE 型番 = %s",
                    (new_stock, input_data["保管場所"], str(input_data["型番"])),
                )
            else:
                # --- 新規登録処理 ---
                final_stock = input_data["数量"]
                if final_stock < 0:
                    final_stock = 0

                cursor.execute(
                    "INSERT INTO inventory (型番,製品名,カテゴリ,メーカー,現在数量,保管場所) VALUES (%s,%s,%s,%s,%s,%s)",
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
                "INSERT INTO history (日時,型番,製品名,カテゴリ,メーカー,数量,在庫数量) VALUES (%s,%s,%s,%s,%s,%s,%s)",
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

    except Exception as e:
        conn.rollback()
        import traceback

        traceback.print_exc()
        return {
            "success": False,
            "message": f"処理中にデータベースエラーが発生しました:\n{str(e)}",
        }
    finally:
        conn.close()
