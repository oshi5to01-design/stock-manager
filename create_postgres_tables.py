import psycopg2


def create_tables():
    print("🔨 PostgreSQLにテーブルを作成中...")

    # データベースに接続
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="postgres",
        user="postgres",
        password="password",
    )
    conn.autocommit = True
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
        "No." SERIAL PRIMARY KEY,
        型番 TEXT UNIQUE,
        製品名 TEXT,
        カテゴリ TEXT,
        メーカー TEXT,
        現在数量 INTEGER,
        保管場所 INTEGER
    );
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
    );
    """
    )

    print("テーブル作成完了！")
    conn.close()


if __name__ == "__main__":
    create_tables()
