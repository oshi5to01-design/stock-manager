import pytest
import os
import sqlite3
import backend_logic  # テスト対象のファイルをインポート

# テスト用のDBファイル名
TEST_DB_FILE = "test_inventory.db"


# ====================================================================
# ⚙️ テストの準備と後片付け (フィクスチャ)
# ====================================================================
@pytest.fixture(scope="function")
def setup_db():
    """
    テストのたびに新しい空のDBを作り、
    backend_logicがそのDBを使うように差し替える
    """
    # 1. 本番のDB設定を、テスト用ファイルに書き換える（ここが重要！）
    #    これでテスト中は test_inventory.db が使われる
    backend_logic.DB_FILE = TEST_DB_FILE

    # 2. テスト用DBにテーブルを作る（create_dummy_db.pyと同じ構造）
    conn = sqlite3.connect(TEST_DB_FILE)
    cursor = conn.cursor()

    # inventoryテーブル作成
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

    # historyテーブル作成
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
    conn.commit()
    conn.close()

    # 3. テスト実行！ (ここでテスト関数が動く)
    yield

    # 4. 後片付け: テストが終わったらDBファイルを消す
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)


# ====================================================================
# ✅ ここからテストケース
# ====================================================================


def test_sanitization_full_width_numbers(setup_db):
    """全角数字が半角に変換されて登録されるか？"""
    input_data = {
        "処理種別": "補充",
        "型番": "TEST-01",
        "製品名": "テスト製品",
        "カテゴリ": "テスト",
        "メーカー": "テスト社",
        "数量": "１０",  # ★全角で入力！
        "保管場所": "100",
    }

    # 実行
    result = backend_logic.run_main_process_from_ui(input_data)

    # 成功したかチェック
    assert result["success"] is True

    # DBの中身を見て、本当に「10」になっているか確認
    details = backend_logic.get_item_details_by_model("TEST-01")
    assert details["現在数量"] == 10  # 半角の10になっているはず


def test_stock_calculation_add(setup_db):
    """在庫の足し算（補充）が正しく動くか？"""
    # まず10個登録
    backend_logic.run_main_process_from_ui(
        {
            "処理種別": "補充",
            "型番": "TEST-02",
            "製品名": "A",
            "カテゴリ": "C",
            "メーカー": "M",
            "数量": 10,
            "保管場所": "100",
        }
    )

    # さらに5個補充
    backend_logic.run_main_process_from_ui(
        {
            "処理種別": "補充",
            "型番": "TEST-02",
            "製品名": "A",
            "カテゴリ": "C",
            "メーカー": "M",
            "数量": 5,
            "保管場所": "100",
        }
    )

    # 結果は15個のはず
    details = backend_logic.get_item_details_by_model("TEST-02")
    assert details["現在数量"] == 15


def test_stock_calculation_subtract(setup_db):
    """在庫の引き算（使用）が正しく動くか？"""
    # 10個登録
    backend_logic.run_main_process_from_ui(
        {
            "処理種別": "補充",
            "型番": "TEST-03",
            "製品名": "A",
            "カテゴリ": "C",
            "メーカー": "M",
            "数量": 10,
            "保管場所": "100",
        }
    )

    # 3個使用
    backend_logic.run_main_process_from_ui(
        {
            "処理種別": "使用",
            "型番": "TEST-03",
            "製品名": "A",
            "カテゴリ": "C",
            "メーカー": "M",
            "数量": 3,
            "保管場所": "100",
        }
    )

    # 結果は7個のはず
    details = backend_logic.get_item_details_by_model("TEST-03")
    assert details["現在数量"] == 7


def test_stock_floor_limit(setup_db):
    """在庫がマイナスにならず0で止まるか？"""
    # 5個登録
    backend_logic.run_main_process_from_ui(
        {
            "処理種別": "補充",
            "型番": "TEST-04",
            "製品名": "A",
            "カテゴリ": "C",
            "メーカー": "M",
            "数量": 5,
            "保管場所": "100",
        }
    )

    # 10個使用（在庫より多く使う！）
    backend_logic.run_main_process_from_ui(
        {
            "処理種別": "使用",
            "型番": "TEST-04",
            "製品名": "A",
            "カテゴリ": "C",
            "メーカー": "M",
            "数量": 10,
            "保管場所": "100",
        }
    )

    # 結果はマイナスではなく0のはず
    details = backend_logic.get_item_details_by_model("TEST-04")
    assert details["現在数量"] == 0
