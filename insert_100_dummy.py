import psycopg2
import random
from datetime import datetime, timedelta


def insert_100_items():
    print("🚀 PostgreSQLにダミーデータ100件を投入中...")

    # 1. DB接続
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="postgres",
        user="postgres",
        password="password",
    )
    cursor = conn.cursor()

    # 2. ランダム生成用の素材リスト
    categories = [
        "PC周辺機器",
        "ケーブル",
        "消耗品",
        "オフィス家具",
        "PC本体",
        "ネットワーク機器",
    ]
    makers = [
        "エレコム",
        "サンワサプライ",
        "ロジクール",
        "Dell",
        "HP",
        "Anker",
        "コクヨ",
        "Sony",
    ]

    adjectives = [
        "高耐久",
        "静音",
        "ゲーミング",
        "業務用",
        "スリム",
        "ワイヤレス",
        "4K対応",
        "超軽量",
    ]
    nouns = [
        "マウス",
        "キーボード",
        "モニター",
        "デスク",
        "チェア",
        "USBハブ",
        "HDMIケーブル",
        "ノートPC",
    ]

    # 3. 100回ループしてデータを生成・投入
    for i in range(1, 101):

        model = f"TEST-{i:04d}"

        # 製品名: 「形容詞」+「名詞」をランダムに合体
        name = f"{random.choice(adjectives)}{random.choice(nouns)}"

        category = random.choice(categories)
        maker = random.choice(makers)
        current_qty = random.randint(0, 200)  # 在庫数 0〜200
        location = random.randint(100, 999)  # 保管場所 100〜999

        try:
            # --- inventoryテーブルへ登録 ---
            # ON CONFLICT (型番) DO NOTHING
            # → もし既に同じ型番があったら、エラーにせずスキップする（安全策）
            cursor.execute(
                """
            INSERT INTO inventory (型番, 製品名, カテゴリ, メーカー, 現在数量, 保管場所)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (型番) DO NOTHING;
            """,
                (model, name, category, maker, current_qty, location),
            )

            # --- historyテーブルへ履歴も登録 ---
            # 日付をランダムに過去60日以内にばらけさせる
            random_days = random.randint(0, 60)
            past_date = datetime.now() - timedelta(days=random_days)

            cursor.execute(
                """
            INSERT INTO history (日時, 型番, 製品名, カテゴリ, メーカー, 数量, 在庫数量)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
                (past_date, model, name, category, maker, current_qty, current_qty),
            )

        except Exception as e:
            print(f"⚠️ エラー発生 ({model}): {e}")

    # 4. 確定して閉じる
    conn.commit()
    conn.close()
    print("✅ 完了！ 100件のデータが入りました。VS Codeで確認してみて！")


if __name__ == "__main__":
    insert_100_items()
