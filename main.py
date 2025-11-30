import tkinter as tk
from tkinter import ttk, messagebox
import backend_logic as logic
import autocomplete_widget as ac
import logging

# ==================================================================================
# ログ設定 (app.log というファイルにエラーを記録)
# ==================================================================================
logging.basicConfig(
    filename="app.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)

# ==================================================================================
# フォント設定
# ==================================================================================
MAIN_FONT = ("Noto Sans CJK JP", 10)
BOLD_FONT = ("Noto Sans CJK JP", 12, "bold")

# ==================================================================================
# イベントハンドラ関数
# ==================================================================================


def execute_update():
    """「更新実行」が押されたときの処理"""
    try:
        input_values = {
            "処理種別": combo_action.get(),
            "型番": entry_model.get(),
            "製品名": entry_name.get(),
            "カテゴリ": entry_category.get(),
            "メーカー": entry_maker.get(),
            "数量": entry_quantity.get(),
            "保管場所": entry_location.get(),
        }

        if not input_values["製品名"] or not input_values["数量"]:
            messagebox.showwarning("入力エラー", "製品名と数量は必須です。")
            return

        result = logic.run_main_process_from_ui(input_values)

        if result["success"]:
            messagebox.showinfo("成功", result["message"])
        else:
            logging.error(f"更新失敗: {result['message']}")
            messagebox.showerror("エラー", result["message"])

    except Exception as e:
        logging.error("UI操作中に予期せぬエラーが発生", exc_info=True)
        messagebox.showerror(
            "致命的なエラー",
            f"予期せぬエラーが発生しました。\nログを確認してください。\n{e}",
        )


def clear_entries():
    """すべての入力欄を初期状態にリセットする"""
    combo_action.current(0)
    entry_model.delete(0, tk.END)
    entry_name.delete(0, tk.END)
    entry_category.delete(0, tk.END)
    entry_maker.delete(0, tk.END)
    entry_quantity.delete(0, tk.END)
    entry_location.delete(0, tk.END)
    stock_monitor_label.config(text="現在の在庫数: ---")


def on_model_selected_action(selected_model):
    """
    ★変更: AutocompleteEntryから呼ばれるコールバック関数
    型番が確定したときに詳細を自動入力する
    """
    details = logic.get_item_details_by_model(selected_model)

    if details:
        # 一旦クリアしてから挿入
        entry_name.delete(0, tk.END)
        entry_name.insert(0, details.get("製品名", ""))

        entry_category.delete(0, tk.END)
        entry_category.insert(0, details.get("カテゴリ", ""))

        entry_maker.delete(0, tk.END)
        entry_maker.insert(0, details.get("メーカー", ""))

        entry_location.delete(0, tk.END)
        if details.get("保管場所"):
            entry_location.insert(0, details.get("保管場所"))

        stock_monitor_label.config(
            text=f"現在の在庫数: {details.get('現在数量','---')}"
        )
    else:
        stock_monitor_label.config(text="現在の在庫数: --- (新規登録)")


# ==================================================================================
# GUIの構築
# ==================================================================================

root = tk.Tk()
root.title("在庫管理システム")
root.geometry("400x550")

try:
    icon_img = tk.PhotoImage(file="icon.png")
    root.iconphoto(False, icon_img)
except Exception:
    pass

# 全体のスタイル設定（フォント一括指定）
style = ttk.Style()
style.configure(".", font=MAIN_FONT)
style.configure("TLabel", font=MAIN_FONT)
style.configure("TButton", font=MAIN_FONT)

form_frame = ttk.Frame(root, padding=20)
form_frame.pack(fill=tk.BOTH, expand=True)

# ラベル作成
labels_texts = [
    "処理種別:",
    "型番:",
    "製品名:",
    "カテゴリ:",
    "メーカー:",
    "数量:",
    "保管場所:",
]

# ウィジェット作成
combo_action = ttk.Combobox(form_frame, values=["補充", "使用"], state="readonly")
combo_action.current(0)

# 型番には on_select_callback を渡して、確定時に自動入力を走らせる
entry_model = ac.AutocompleteEntry(
    form_frame,
    get_suggestions_func=logic.get_autocomplete_suggestions,
    column_name="型番",
    on_select_callback=on_model_selected_action,
    font=MAIN_FONT,
)

# 他の項目はコールバックなし（単なるサジェストのみ）
entry_name = ac.AutocompleteEntry(
    form_frame,
    get_suggestions_func=logic.get_autocomplete_suggestions,
    column_name="製品名",
    font=MAIN_FONT,
)

entry_category = ac.AutocompleteEntry(
    form_frame,
    get_suggestions_func=logic.get_autocomplete_suggestions,
    column_name="カテゴリ",
    font=MAIN_FONT,
)

entry_maker = ac.AutocompleteEntry(
    form_frame,
    get_suggestions_func=logic.get_autocomplete_suggestions,
    column_name="メーカー",
    font=MAIN_FONT,
)

entry_quantity = ttk.Entry(form_frame)
entry_location = ttk.Entry(form_frame)

widgets = [
    combo_action,
    entry_model,
    entry_name,
    entry_category,
    entry_maker,
    entry_quantity,
    entry_location,
]

# 配置ループ
for i, (text, widget) in enumerate(zip(labels_texts, widgets)):
    label = ttk.Label(form_frame, text=text)
    label.grid(row=i, column=0, sticky=tk.W, pady=5)
    widget.grid(row=i, column=1, sticky=tk.EW, padx=5)

# ボタン配置
execute_button = ttk.Button(form_frame, text="更新実行", command=execute_update)
execute_button.grid(row=7, column=0, columnspan=2, pady=(20, 5), sticky=tk.EW)

clear_button = ttk.Button(form_frame, text="入力クリア", command=clear_entries)
clear_button.grid(row=8, column=0, columnspan=2, pady=(0, 15), sticky=tk.EW)

stock_monitor_label = ttk.Label(form_frame, text="現在の在庫数: ---", font=BOLD_FONT)
stock_monitor_label.grid(row=9, column=0, columnspan=2, pady=10)

form_frame.columnconfigure(1, weight=1)

if __name__ == "__main__":
    root.mainloop()
