#!/usr/bin/env python3
"""轻松背单词 — 基于 SM-2 间隔重复的 Tkinter 桌面应用。"""

import json
import random
from datetime import date, timedelta
from pathlib import Path
from tkinter import (
    END,
    Button,
    Frame,
    Label,
    Menu,
    StringVar,
    Text,
    Tk,
    Toplevel,
    filedialog,
    messagebox,
)
from tkinter import ttk

from word_import import WordRow, import_from_excel, import_from_pdf

DATA_FILE = Path(__file__).parent / "words.json"
STATS_FILE = Path(__file__).parent / "study_stats.json"
DAILY_REVIEW_GOAL = 6

DEFAULT_WORDS = [
    {
        "id": 1,
        "word": "abandon",
        "definition": "抛弃，放弃",
        "example": "He abandoned his car in the snow.",
        "interval": 1,
        "ease_factor": 2.5,
        "next_review": "2020-01-01",
    },
    {
        "id": 2,
        "word": "benefit",
        "definition": "利益；好处；有益于",
        "example": "Regular exercise has many health benefits.",
        "interval": 1,
        "ease_factor": 2.5,
        "next_review": "2020-01-01",
    },
    {
        "id": 3,
        "word": "challenge",
        "definition": "挑战；质疑",
        "example": "Climbing the mountain was a real challenge.",
        "interval": 1,
        "ease_factor": 2.5,
        "next_review": "2020-01-01",
    },
    {
        "id": 4,
        "word": "delicate",
        "definition": "精致的；脆弱的；微妙的",
        "example": "Handle the delicate glass with care.",
        "interval": 1,
        "ease_factor": 2.5,
        "next_review": "2020-01-01",
    },
    {
        "id": 5,
        "word": "efficient",
        "definition": "高效的；有能力的",
        "example": "This new engine is more fuel-efficient.",
        "interval": 1,
        "ease_factor": 2.5,
        "next_review": "2020-01-01",
    },
    {
        "id": 6,
        "word": "gratitude",
        "definition": "感激；感谢",
        "example": "She expressed her gratitude with a thank-you note.",
        "interval": 1,
        "ease_factor": 2.5,
        "next_review": "2020-01-01",
    },
]


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def format_date(d: date) -> str:
    return d.isoformat()


def load_data() -> list[dict]:
    if not DATA_FILE.exists():
        save_data(DEFAULT_WORDS)
        return [dict(w) for w in DEFAULT_WORDS]
    with DATA_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def save_data(words: list[dict]) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)


def next_id(words: list[dict]) -> int:
    if not words:
        return 1
    return max(w["id"] for w in words) + 1


def apply_sm2(word: dict, grade: int) -> None:
    """根据 SM-2 规则更新 interval、ease_factor 与 next_review。"""
    ease = float(word["ease_factor"])
    interval = float(word["interval"])

    if grade == 1:
        interval = 1
        ease = max(1.3, ease - 0.2)
    else:
        interval = max(1, round(interval * ease))
        delta = 0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02)
        ease = ease + delta

    word["interval"] = int(interval)
    word["ease_factor"] = round(ease, 2)
    word["next_review"] = format_date(date.today() + timedelta(days=int(interval)))


def due_words(words: list[dict], today: date | None = None) -> list[dict]:
    today = today or date.today()
    return [w for w in words if parse_date(w["next_review"]) <= today]


def load_stats() -> dict[str, int]:
    if not STATS_FILE.exists():
        return {}
    with STATS_FILE.open(encoding="utf-8") as f:
        data = json.load(f)
    return {k: int(v) for k, v in data.items()}


def save_stats(stats: dict[str, int]) -> None:
    with STATS_FILE.open("w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def get_today_study_count(today: date | None = None) -> int:
    today = today or date.today()
    return load_stats().get(format_date(today), 0)


def increment_today_study(today: date | None = None) -> int:
    today = today or date.today()
    key = format_date(today)
    stats = load_stats()
    stats[key] = stats.get(key, 0) + 1
    save_stats(stats)
    return stats[key]


def build_daily_review_queue(words: list[dict], today: date | None = None) -> list[dict]:
    """今日必复习队列：最多 DAILY_REVIEW_GOAL 个待复习单词。"""
    due = list(due_words(words, today))
    random.shuffle(due)
    return due[:DAILY_REVIEW_GOAL]


class Theme:
    """蓝灰现代主题配色。"""

    BG = "#e8edf2"
    BG_CARD = "#ffffff"
    BG_HEADER = "#2f4054"
    BG_INPUT = "#f4f7fa"
    ACCENT = "#4a7ab5"
    ACCENT_DARK = "#3a628f"
    ACCENT_LIGHT = "#d6e4f0"
    TEXT = "#2c3e50"
    TEXT_SECONDARY = "#6b7c93"
    TEXT_MUTED = "#9aa8b8"
    TEXT_ON_DARK = "#e8eef4"
    BORDER = "#d4dde6"
    SUCCESS = "#3d8b7a"
    SUCCESS_BG = "#e8f4f1"
    WARN = "#8b7a4a"
    WARN_BG = "#f5f0e6"
    DANGER = "#a65d5d"
    DANGER_BG = "#f5eaea"
    FONT = "Microsoft YaHei UI"
    FONT_EN = "Segoe UI"


def _flat_button(
    parent,
    text: str,
    command,
    *,
    bg: str,
    fg: str,
    hover_bg: str,
    font_size: int = 10,
    width: int | None = None,
    padx: int = 20,
    pady: int = 10,
) -> Button:
    btn = Button(
        parent,
        text=text,
        command=command,
        font=(Theme.FONT, font_size),
        bg=bg,
        fg=fg,
        activebackground=hover_bg,
        activeforeground=fg,
        relief="flat",
        borderwidth=0,
        highlightthickness=0,
        cursor="hand2",
        padx=padx,
        pady=pady,
    )
    if width is not None:
        btn.config(width=width)

    def on_enter(_e):
        if str(btn["state"]) != "disabled":
            btn.config(bg=hover_bg)

    def on_leave(_e):
        if str(btn["state"]) != "disabled":
            btn.config(bg=bg)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn


class AddWordDialog(Toplevel):
    def __init__(self, parent: "VocabApp", on_save, on_import_batch) -> None:
        super().__init__(parent)
        self.title("添加单词")
        self.resizable(False, False)
        self.parent_app = parent
        self.on_save = on_save
        self.on_import_batch = on_import_batch
        self.transient(parent)
        self.grab_set()
        self.configure(bg=Theme.BG)

        header = Frame(self, bg=Theme.BG_HEADER, height=52)
        header.pack(fill="x")
        header.pack_propagate(False)
        Label(
            header,
            text="添加新单词",
            font=(Theme.FONT, 13, "bold"),
            bg=Theme.BG_HEADER,
            fg=Theme.TEXT_ON_DARK,
        ).pack(side="left", padx=20, pady=14)

        body = Frame(self, bg=Theme.BG, padx=24, pady=20)
        body.pack(fill="both")

        fields = [
            ("单词", "word"),
            ("释义", "definition"),
            ("例句（可选）", "example"),
        ]
        self.vars: dict[str, StringVar] = {}
        self.entries: list[ttk.Entry] = []
        for row, (label, key) in enumerate(fields):
            Label(
                body,
                text=label,
                font=(Theme.FONT, 10),
                bg=Theme.BG,
                fg=Theme.TEXT_SECONDARY,
                anchor="w",
            ).grid(row=row * 2, column=0, sticky="w", pady=(0, 4))
            var = StringVar()
            self.vars[key] = var
            entry = ttk.Entry(body, textvariable=var, width=36, style="Modern.TEntry")
            entry.grid(row=row * 2 + 1, column=0, sticky="ew", pady=(0, 12))
            self.entries.append(entry)
            if row == 0:
                entry.focus_set()
        body.columnconfigure(0, weight=1)

        btn_row = Frame(body, bg=Theme.BG)
        btn_row.grid(row=len(fields) * 2, column=0, pady=(4, 0))
        _flat_button(
            btn_row,
            "保存",
            self._save,
            bg=Theme.ACCENT,
            fg="#ffffff",
            hover_bg=Theme.ACCENT_DARK,
            font_size=10,
            padx=24,
            pady=8,
        ).pack(side="left", padx=(0, 10))
        _flat_button(
            btn_row,
            "取消",
            self.destroy,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_SECONDARY,
            hover_bg=Theme.BORDER,
            font_size=10,
            padx=24,
            pady=8,
        ).pack(side="left")

        import_sep = Frame(body, bg=Theme.BG)
        import_sep.grid(row=len(fields) * 2 + 1, column=0, sticky="ew", pady=(20, 12))
        Frame(import_sep, bg=Theme.BORDER, height=1).pack(fill="x", side="left", expand=True)
        Label(
            import_sep,
            text="  批量导入  ",
            font=(Theme.FONT, 9),
            bg=Theme.BG,
            fg=Theme.TEXT_MUTED,
        ).pack(side="left")
        Frame(import_sep, bg=Theme.BORDER, height=1).pack(fill="x", side="left", expand=True)

        import_row = Frame(body, bg=Theme.BG)
        import_row.grid(row=len(fields) * 2 + 2, column=0, sticky="ew")
        _flat_button(
            import_row,
            "从 Excel 导入",
            self._import_excel,
            bg=Theme.ACCENT_LIGHT,
            fg=Theme.ACCENT_DARK,
            hover_bg=Theme.BORDER,
            font_size=10,
            padx=16,
            pady=8,
        ).pack(side="left", padx=(0, 10))
        _flat_button(
            import_row,
            "从 PDF 导入",
            self._import_pdf,
            bg=Theme.ACCENT_LIGHT,
            fg=Theme.ACCENT_DARK,
            hover_bg=Theme.BORDER,
            font_size=10,
            padx=16,
            pady=8,
        ).pack(side="left")

        hint = (
            "Excel：首行表头（单词/释义/例句），或三列无表头。\n"
            "PDF：每行「单词\\t释义」或「单词 - 释义」，可选例句。"
        )
        Label(
            body,
            text=hint,
            font=(Theme.FONT, 8),
            bg=Theme.BG,
            fg=Theme.TEXT_MUTED,
            justify="left",
        ).grid(row=len(fields) * 2 + 3, column=0, sticky="w", pady=(10, 0))

        self.bind("<Return>", lambda _e: self._save())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _import_excel(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            title="选择 Excel 文件",
            filetypes=[
                ("Excel 工作簿", "*.xlsx"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return
        self._run_import(import_from_excel, Path(path))

    def _import_pdf(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            title="选择 PDF 文件",
            filetypes=[
                ("PDF 文档", "*.pdf"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return
        self._run_import(import_from_pdf, Path(path))

    def _run_import(self, importer, path: Path) -> None:
        try:
            rows: list[WordRow] = importer(path)
        except ImportError as exc:
            messagebox.showerror("缺少依赖", str(exc), parent=self)
            return
        except Exception as exc:
            messagebox.showerror("导入失败", str(exc), parent=self)
            return
        if not rows:
            messagebox.showwarning(
                "导入结果",
                "未解析到有效单词，请检查文件格式。",
                parent=self,
            )
            return
        added, skipped = self.on_import_batch(rows)
        messagebox.showinfo(
            "导入完成",
            f"成功导入 {added} 个单词"
            + (f"，跳过重复 {skipped} 个" if skipped else "")
            + "。",
            parent=self,
        )
        if added:
            self.destroy()

    def _save(self) -> None:
        word = self.vars["word"].get().strip()
        definition = self.vars["definition"].get().strip()
        example = self.vars["example"].get().strip()
        if not word or not definition:
            messagebox.showwarning("提示", "单词和释义不能为空。", parent=self)
            return
        self.on_save(word, definition, example)
        self.destroy()


class VocabApp(Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("轻松背单词")
        self.minsize(560, 520)
        self.geometry("600x560")
        self.configure(bg=Theme.BG)

        self.words = load_data()
        self.today = date.today()
        self.mode = "review"  # review | extra
        self.queue: list[dict] = build_daily_review_queue(self.words, self.today)
        self.review_session_total = len(self.queue)
        self.index = 0
        self.def_hidden = True
        self._btn_styles: dict[Button, tuple[str, str]] = {}

        self._setup_styles()
        self._build_ui()
        self._build_menu()

        if not self.queue:
            if self._extra_candidates():
                messagebox.showinfo(
                    "轻松背单词",
                    f"今日 {DAILY_REVIEW_GOAL} 个复习任务已完成！\n"
                    f"今日累计已学 {get_today_study_count(self.today)} 个单词。\n"
                    "可点击「继续学习」预习更多单词。",
                )
            else:
                messagebox.showinfo(
                    "轻松背单词",
                    f"恭喜，今日完成复习！\n今日累计已学 {get_today_study_count(self.today)} 个单词。",
                )
            self._set_idle_state()
        else:
            self._show_current()

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Modern.Horizontal.TProgressbar",
            troughcolor=Theme.BORDER,
            background=Theme.ACCENT,
            thickness=6,
            borderwidth=0,
            lightcolor=Theme.ACCENT,
            darkcolor=Theme.ACCENT,
        )
        style.configure(
            "Modern.TEntry",
            fieldbackground=Theme.BG_INPUT,
            foreground=Theme.TEXT,
            padding=8,
        )

    def _build_menu(self) -> None:
        menubar = Menu(self, tearoff=0, bg=Theme.BG_CARD, fg=Theme.TEXT)
        file_menu = Menu(menubar, tearoff=0, bg=Theme.BG_CARD, fg=Theme.TEXT)
        file_menu.add_command(label="添加单词", command=self._open_add_dialog)
        file_menu.add_command(label="从 Excel 导入…", command=self._import_excel)
        file_menu.add_command(label="从 PDF 导入…", command=self._import_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit)
        menubar.add_cascade(label="菜单", menu=file_menu)
        self.config(menu=menubar)

    def _build_ui(self) -> None:
        header = Frame(self, bg=Theme.BG_HEADER, height=72)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_row = Frame(header, bg=Theme.BG_HEADER)
        title_row.pack(fill="x", padx=24, pady=(14, 0))
        Label(
            title_row,
            text="轻松背单词",
            font=(Theme.FONT, 16, "bold"),
            bg=Theme.BG_HEADER,
            fg=Theme.TEXT_ON_DARK,
        ).pack(side="left")
        Label(
            title_row,
            text="SM-2 间隔重复",
            font=(Theme.FONT, 9),
            bg=Theme.BG_HEADER,
            fg=Theme.TEXT_MUTED,
        ).pack(side="left", padx=(12, 0), pady=(4, 0))

        badge_row = Frame(header, bg=Theme.BG_HEADER)
        badge_row.place(relx=1.0, rely=0.5, anchor="e", x=-24)
        self.study_badge = Label(
            badge_row,
            text="",
            font=(Theme.FONT, 9),
            bg="#3d5268",
            fg=Theme.TEXT_ON_DARK,
            padx=10,
            pady=4,
        )
        self.study_badge.pack(side="right", padx=(6, 0))
        self.due_badge = Label(
            badge_row,
            text="",
            font=(Theme.FONT, 10),
            bg=Theme.ACCENT,
            fg="#ffffff",
            padx=12,
            pady=4,
        )
        self.due_badge.pack(side="right")

        content = Frame(self, bg=Theme.BG)
        content.pack(fill="both", expand=True, padx=24, pady=20)

        self.card = Frame(
            content,
            bg=Theme.BG_CARD,
            highlightbackground=Theme.BORDER,
            highlightthickness=1,
        )
        self.card.pack(fill="both", expand=True)

        card_inner = Frame(self.card, bg=Theme.BG_CARD, padx=32, pady=28)
        card_inner.pack(fill="both", expand=True)

        self.word_label = Label(
            card_inner,
            text="",
            font=(Theme.FONT_EN, 32, "bold"),
            bg=Theme.BG_CARD,
            fg=Theme.TEXT,
            wraplength=500,
        )
        self.word_label.pack(pady=(4, 20))

        sep = Frame(card_inner, bg=Theme.BORDER, height=1)
        sep.pack(fill="x", pady=(0, 16))

        self.def_label = Label(
            card_inner,
            text="点击「显示释义」查看中文释义",
            font=(Theme.FONT, 13),
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_MUTED,
            wraplength=500,
            justify="center",
        )
        self.def_label.pack(pady=(0, 12))

        self.btn_reveal = _flat_button(
            card_inner,
            "显示释义",
            self._reveal_definition,
            bg=Theme.ACCENT_LIGHT,
            fg=Theme.ACCENT_DARK,
            hover_bg=Theme.BORDER,
            font_size=10,
            padx=18,
            pady=6,
        )
        self.btn_reveal.pack(pady=(0, 20))

        example_hdr = Frame(card_inner, bg=Theme.BG_CARD)
        example_hdr.pack(fill="x")
        Label(
            example_hdr,
            text="例句",
            font=(Theme.FONT, 9),
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_MUTED,
        ).pack(side="left")
        Frame(example_hdr, bg=Theme.BORDER, height=1).pack(
            side="left", fill="x", expand=True, padx=(8, 0), pady=6
        )

        example_box = Frame(
            card_inner, bg=Theme.BG_INPUT, highlightbackground=Theme.BORDER, highlightthickness=1
        )
        example_box.pack(fill="x", pady=(8, 0))
        self.example_text = Text(
            example_box,
            height=3,
            wrap="word",
            font=(Theme.FONT_EN, 11),
            relief="flat",
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_SECONDARY,
            padx=12,
            pady=10,
            borderwidth=0,
            highlightthickness=0,
        )
        self.example_text.pack(fill="x")
        self.example_text.config(state="disabled")

        grade_frame = Frame(content, bg=Theme.BG)
        grade_frame.pack(fill="x", pady=(20, 0))

        self.btn_known = _flat_button(
            grade_frame,
            "认识",
            lambda: self._grade(4),
            bg=Theme.SUCCESS_BG,
            fg=Theme.SUCCESS,
            hover_bg="#d4ebe5",
            font_size=11,
            padx=0,
            pady=12,
        )
        self.btn_fuzzy = _flat_button(
            grade_frame,
            "模糊",
            lambda: self._grade(3),
            bg=Theme.WARN_BG,
            fg=Theme.WARN,
            hover_bg="#ebe4d4",
            font_size=11,
            padx=0,
            pady=12,
        )
        self.btn_unknown = _flat_button(
            grade_frame,
            "不认识",
            lambda: self._grade(1),
            bg=Theme.DANGER_BG,
            fg=Theme.DANGER,
            hover_bg="#ebd4d4",
            font_size=11,
            padx=0,
            pady=12,
        )
        for i, btn in enumerate((self.btn_known, self.btn_fuzzy, self.btn_unknown)):
            btn.pack(side="left", fill="x", expand=True, padx=(0 if i == 0 else 6, 0))
            self._btn_styles[btn] = (btn["bg"], btn["fg"])

        footer = Frame(content, bg=Theme.BG)
        footer.pack(fill="x", pady=(16, 0))

        progress_row = Frame(footer, bg=Theme.BG)
        progress_row.pack(fill="x")
        self.progress_label = Label(
            progress_row,
            text="",
            font=(Theme.FONT, 9),
            bg=Theme.BG,
            fg=Theme.TEXT_SECONDARY,
        )
        self.progress_label.pack(side="left")

        self.progress_bar = ttk.Progressbar(
            progress_row,
            style="Modern.Horizontal.TProgressbar",
            mode="determinate",
            length=120,
        )
        self.progress_bar.pack(side="right")

        action_row = Frame(footer, bg=Theme.BG)
        action_row.pack(pady=(12, 0))

        self.btn_continue = _flat_button(
            action_row,
            "继续学习",
            self._start_extra_learning,
            bg=Theme.ACCENT,
            fg="#ffffff",
            hover_bg=Theme.ACCENT_DARK,
            font_size=10,
            padx=20,
            pady=8,
        )
        self.btn_continue.pack(side="left", padx=(0, 8))
        self.btn_continue.pack_forget()

        self.btn_add = _flat_button(
            action_row,
            "＋ 添加单词",
            self._open_add_dialog,
            bg=Theme.BG_CARD,
            fg=Theme.ACCENT,
            hover_bg=Theme.ACCENT_LIGHT,
            font_size=10,
            padx=16,
            pady=8,
        )
        self.btn_add.pack(side="left")

    def _set_grade_buttons_state(self, state: str) -> None:
        for btn in (self.btn_known, self.btn_fuzzy, self.btn_unknown):
            btn.config(state=state)
            if state == "disabled":
                btn.config(bg=Theme.BORDER, fg=Theme.TEXT_MUTED)
            else:
                bg, fg = self._btn_styles[btn]
                btn.config(bg=bg, fg=fg)

    def _extra_candidates(self) -> list[dict]:
        """可继续学习的单词：尚未到复习日期的词。"""
        return [
            w
            for w in self.words
            if parse_date(w["next_review"]) > self.today
        ]

    def _start_extra_learning(self) -> None:
        candidates = self._extra_candidates()
        if not candidates:
            messagebox.showinfo(
                "提示",
                "暂无可以预习的单词。\n添加新单词或明天再来复习吧！",
            )
            return
        random.shuffle(candidates)
        self.mode = "extra"
        self.queue = candidates
        self.index = 0
        self.btn_continue.pack_forget()
        self._show_current()

    def _set_idle_state(self, *, review_done: bool = True) -> None:
        self._update_header()
        studied = get_today_study_count(self.today)
        if review_done and self.mode == "review":
            self.word_label.config(
                text=f"今日复习已完成 ✓（{self.review_session_total} 个）",
                fg=Theme.SUCCESS,
            )
            sub = (
                f"今日累计已学 {studied} 个单词。"
                if studied
                else "点击下方「继续学习」预习更多单词。"
            )
            if self._extra_candidates():
                sub = f"今日累计已学 {studied} 个单词。可继续学习更多单词。"
            self.def_label.config(text=sub, fg=Theme.TEXT_SECONDARY)
        else:
            self.word_label.config(text="今日学习已完成 ✓", fg=Theme.SUCCESS)
            self.def_label.config(
                text=f"今日累计已学 {studied} 个单词，明天见！",
                fg=Theme.TEXT_SECONDARY,
            )
        self.example_text.config(state="normal")
        self.example_text.delete("1.0", END)
        self.example_text.insert(
            "1.0",
            "所有今日复习任务已处理完毕。" if review_done else "拓展学习已结束。",
        )
        self.example_text.config(state="disabled", fg=Theme.TEXT_MUTED)
        self.progress_label.config(text=f"今日累计  {studied}  个")
        self.progress_bar["value"] = 0
        self.btn_reveal.config(state="disabled")
        self._set_grade_buttons_state("disabled")
        if self._extra_candidates():
            self.btn_continue.pack(side="left", padx=(0, 8), before=self.btn_add)
        else:
            self.btn_continue.pack_forget()

    def _update_header(self) -> None:
        studied = get_today_study_count(self.today)
        self.study_badge.config(text=f"今日已学 {studied}")
        if self.mode == "review" and self.index < len(self.queue):
            self.due_badge.config(
                text=f"今日复习  {self.index + 1}/{len(self.queue)} · 目标 {DAILY_REVIEW_GOAL}"
            )
        elif self.mode == "extra" and self.index < len(self.queue):
            self.due_badge.config(text=f"继续学习  {self.index + 1}/{len(self.queue)}")
        else:
            total_due = len(due_words(self.words, self.today))
            self.due_badge.config(text=f"待复习 {min(total_due, DAILY_REVIEW_GOAL)}")

    def _update_progress(self) -> None:
        studied = get_today_study_count(self.today)
        if not self.queue or self.index >= len(self.queue):
            self.progress_label.config(text=f"今日累计  {studied}  个")
            self.progress_bar["value"] = 0
            return
        current = self.index + 1
        total = len(self.queue)
        prefix = "复习" if self.mode == "review" else "拓展"
        self.progress_label.config(
            text=f"{prefix} 第 {current}/{total} 个 · 今日累计 {studied} 个"
        )
        self.progress_bar["maximum"] = total
        self.progress_bar["value"] = current

    def _reveal_definition(self) -> None:
        if self.index >= len(self.queue):
            return
        entry = self.queue[self.index]
        self.def_hidden = False
        self.def_label.config(text=entry["definition"], fg=Theme.TEXT)
        self.btn_reveal.config(state="disabled", bg=Theme.BORDER, fg=Theme.TEXT_MUTED)

    def _show_current(self) -> None:
        if self.index >= len(self.queue):
            save_data(self.words)
            studied = get_today_study_count(self.today)
            if self.mode == "review":
                if self._extra_candidates():
                    messagebox.showinfo(
                        "轻松背单词",
                        f"今日 {len(self.queue)} 个复习任务已完成！\n"
                        f"今日累计已学 {studied} 个单词。\n"
                        "可点击「继续学习」预习更多单词。",
                    )
                else:
                    messagebox.showinfo(
                        "轻松背单词",
                        f"恭喜，今日完成复习！\n今日累计已学 {studied} 个单词。",
                    )
                self._set_idle_state(review_done=True)
            else:
                messagebox.showinfo(
                    "轻松背单词",
                    f"拓展学习本轮已完成！\n今日累计已学 {studied} 个单词。",
                )
                self.mode = "review"
                self._set_idle_state(review_done=False)
            return

        entry = self.queue[self.index]
        self.def_hidden = True
        self.word_label.config(text=entry["word"], fg=Theme.TEXT)
        self.def_label.config(
            text="点击「显示释义」查看中文释义",
            fg=Theme.TEXT_MUTED,
        )
        self.btn_reveal.config(state="normal", bg=Theme.ACCENT_LIGHT, fg=Theme.ACCENT_DARK)
        self.example_text.config(state="normal", fg=Theme.TEXT_SECONDARY)
        self.example_text.delete("1.0", END)
        self.example_text.insert("1.0", entry.get("example") or "（暂无例句）")
        self.example_text.config(state="disabled")

        self._set_grade_buttons_state("normal")
        self._update_header()
        self._update_progress()

    def _grade(self, grade: int) -> None:
        if self.index >= len(self.queue):
            return

        entry = self.queue[self.index]
        if self.def_hidden:
            self.def_label.config(text=entry["definition"], fg=Theme.TEXT)
            self.def_hidden = False
            self.btn_reveal.config(state="disabled", bg=Theme.BORDER, fg=Theme.TEXT_MUTED)

        apply_sm2(entry, grade)
        for w in self.words:
            if w["id"] == entry["id"]:
                w.update(
                    {
                        "interval": entry["interval"],
                        "ease_factor": entry["ease_factor"],
                        "next_review": entry["next_review"],
                    }
                )
                break

        save_data(self.words)
        increment_today_study(self.today)
        self.index += 1
        self._show_current()

    def _open_add_dialog(self) -> None:
        AddWordDialog(self, self._add_word, self._add_words_bulk)

    def _new_word_entry(self, word: str, definition: str, example: str) -> dict:
        return {
            "id": next_id(self.words),
            "word": word,
            "definition": definition,
            "example": example,
            "interval": 1,
            "ease_factor": 2.5,
            "next_review": format_date(self.today),
        }

    def _enqueue_if_due(self, entry: dict) -> None:
        queue_ids = {w["id"] for w in self.queue}
        if entry["id"] in queue_ids:
            return
        if (
            self.mode == "review"
            and parse_date(entry["next_review"]) <= self.today
            and len(self.queue) < DAILY_REVIEW_GOAL
        ):
            self.queue.append(entry)
        elif (
            self.mode == "extra"
            and parse_date(entry["next_review"]) > self.today
        ):
            self.queue.append(entry)

    def _refresh_after_add(self) -> None:
        was_idle = str(self.btn_known["state"]) == "disabled"
        if was_idle and self.queue and self.index < len(self.queue):
            self._set_grade_buttons_state("normal")
            self.btn_reveal.config(
                state="normal", bg=Theme.ACCENT_LIGHT, fg=Theme.ACCENT_DARK
            )
            self._show_current()
        else:
            self._update_header()
            self._update_progress()

    def _add_word(self, word: str, definition: str, example: str) -> None:
        if word.lower() in {w["word"].lower() for w in self.words}:
            messagebox.showwarning("提示", f"单词「{word}」已存在。")
            return
        new_entry = self._new_word_entry(word, definition, example)
        self.words.append(new_entry)
        save_data(self.words)
        self._enqueue_if_due(new_entry)
        self._refresh_after_add()
        messagebox.showinfo("添加成功", f"已添加单词：{word}")

    def _add_words_bulk(self, rows: list[WordRow]) -> tuple[int, int]:
        existing = {w["word"].lower() for w in self.words}
        added = 0
        skipped = 0
        for word, definition, example in rows:
            key = word.strip().lower()
            if not word.strip() or not definition.strip():
                continue
            if key in existing:
                skipped += 1
                continue
            entry = self._new_word_entry(word.strip(), definition.strip(), example.strip())
            self.words.append(entry)
            existing.add(key)
            self._enqueue_if_due(entry)
            added += 1
        if added:
            save_data(self.words)
            self._refresh_after_add()
        return added, skipped

    def _import_excel(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 Excel 文件",
            filetypes=[("Excel 工作簿", "*.xlsx"), ("所有文件", "*.*")],
        )
        if path:
            self._import_file(import_from_excel, Path(path))

    def _import_pdf(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 PDF 文件",
            filetypes=[("PDF 文档", "*.pdf"), ("所有文件", "*.*")],
        )
        if path:
            self._import_file(import_from_pdf, Path(path))

    def _import_file(self, importer, path: Path) -> None:
        try:
            rows = importer(path)
        except ImportError as exc:
            messagebox.showerror("缺少依赖", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("导入失败", str(exc))
            return
        if not rows:
            messagebox.showwarning("导入结果", "未解析到有效单词，请检查文件格式。")
            return
        added, skipped = self._add_words_bulk(rows)
        messagebox.showinfo(
            "导入完成",
            f"成功导入 {added} 个单词"
            + (f"，跳过重复 {skipped} 个" if skipped else "")
            + "。",
        )


def main() -> None:
    app = VocabApp()
    app.mainloop()


if __name__ == "__main__":
    main()
