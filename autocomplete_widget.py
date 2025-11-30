import tkinter as tk
from tkinter import ttk


class AutocompleteEntry(ttk.Entry):
    def __init__(
        self,
        master,
        get_suggestions_func,
        column_name,
        on_select_callback=None,
        font=None,
        **kwargs
    ):
        """
        :param master: 親ウィジェット
        :param get_suggestions_func: 候補を取得する関数 (logic.get_autocomplete_suggestions)
        :param column_name: DBの検索対象カラム名 ("型番" など)
        :param on_select_callback: 確定したときに呼び出す関数 (自動入力用)
        :param font: フォント設定
        """
        super().__init__(master, font=font, **kwargs)
        self.get_suggestions_func = get_suggestions_func
        self.column_name = column_name
        self.on_select_callback = on_select_callback
        self.font = font

        # 候補表示用のListbox（最初は隠しておく）
        # Toplevelではなく、同じフレーム内に配置して最前面に表示する方式
        self.listbox = tk.Listbox(
            master, font=font, height=5, selectmode=tk.SINGLE, exportselection=False
        )
        self.listbox_open = False

        # イベントバインド
        self.bind("<KeyRelease>", self._on_key_release)
        self.bind("<Down>", self._on_down)
        self.bind("<Up>", self._on_up)
        self.bind("<Return>", self._on_return)
        self.bind("<FocusOut>", self._on_focus_out)

        # Listbox側のイベント
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_click)

    def _on_key_release(self, event):
        """文字が打たれたら候補を検索して表示"""
        # 特殊キー（矢印やエンター）は無視
        if event.keysym in ("Down", "Up", "Return", "Tab"):
            return

        typed_text = self.get()
        if not typed_text:
            self._hide_listbox()
            return

        # DBから候補を取得
        suggestions = self.get_suggestions_func(self.column_name, typed_text)

        if suggestions:
            self._show_listbox(suggestions)
        else:
            self._hide_listbox()

    def _show_listbox(self, suggestions):
        """Listboxを表示・更新する"""
        self.listbox.delete(0, tk.END)
        for item in suggestions:
            self.listbox.insert(tk.END, item)

        # Entryの真下に配置（placeを使うと他のウィジェットを押し出さずに浮かせられる）
        x = self.winfo_x()
        y = self.winfo_y() + self.winfo_height()
        w = self.winfo_width()

        self.listbox.place(x=x, y=y, width=w)
        self.listbox.lift()  # 最前面に持ってくる
        self.listbox_open = True

    def _hide_listbox(self):
        """Listboxを隠す"""
        self.listbox.place_forget()
        self.listbox_open = False

    def _on_down(self, event):
        """下矢印キー：フォーカスはEntryのまま、Listboxの選択を下げる"""
        if not self.listbox_open:
            return

        current_sel = self.listbox.curselection()
        if not current_sel:
            index = 0
        else:
            index = min(current_sel[0] + 1, self.listbox.size() - 1)

        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.see(index)  # スクロール追従

    def _on_up(self, event):
        """上矢印キー"""
        if not self.listbox_open:
            return

        current_sel = self.listbox.curselection()
        if not current_sel:
            index = self.listbox.size() - 1
        else:
            index = max(current_sel[0] - 1, 0)

        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.see(index)

    def _on_return(self, event):
        """Enterキー：選択中の候補を確定する"""
        if self.listbox_open:
            current_sel = self.listbox.curselection()
            if current_sel:
                selected_text = self.listbox.get(current_sel[0])
                self._confirm_selection(selected_text)
                return (
                    "break"  # Enterのデフォルト動作（次のウィジェットへ移動など）を防ぐ
                )

    def _on_listbox_click(self, event):
        """マウスでクリックされた場合"""
        selection = self.listbox.curselection()
        if selection:
            selected_text = self.listbox.get(selection[0])
            self._confirm_selection(selected_text)

    def _confirm_selection(self, text):
        """確定処理"""
        self.delete(0, tk.END)
        self.insert(0, text)
        self._hide_listbox()

        # コールバックがあれば実行（型番詳細の自動入力など）
        if self.on_select_callback:
            self.on_select_callback(text)

    def _on_focus_out(self, event):
        """フォーカスが外れたらリストを消す（少し遅らせないとクリック判定と競合する）"""
        self.after(100, self._hide_listbox)
