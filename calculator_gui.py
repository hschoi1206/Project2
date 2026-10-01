# 클릭으로 사용하는 GUI 계산기 (tkinter)
# 실행: python calculator_gui.py
# 사칙연산 로직은 calculator.py의 calculate()를 재사용한다.

from calculator import calculate

OP_SYMBOLS = {"+": "+", "-": "−", "*": "×", "/": "÷"}


def format_number(value):
    """정수로 딱 떨어지면 소수점 없이, 아니면 최대 10자리 유효숫자로 표시한다."""
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    return f"{value:.10g}"


class CalculatorState:
    """버튼 입력을 받아 화면에 보일 값을 관리한다. (UI와 분리되어 있어 단독 테스트 가능)"""

    def __init__(self):
        self.clear()

    def clear(self):
        self.current = "0"       # 현재 입력 중인 숫자 (문자열)
        self.stored = None       # 연산자 앞의 숫자
        self.op = None           # 대기 중인 연산자
        self.reset_next = False  # 다음 숫자 입력 시 화면을 새로 시작할지
        self.history = ""        # 위쪽 작은 줄에 보일 수식

    def input_digit(self, digit):
        if self.reset_next or self.current == "0":
            self.current = digit
            self.reset_next = False
        elif len(self.current) < 15:
            self.current += digit

    def input_dot(self):
        if self.reset_next:
            self.current = "0"
            self.reset_next = False
        if "." not in self.current:
            self.current += "."

    def backspace(self):
        if self.reset_next:
            return
        self.current = self.current[:-1]
        if self.current in ("", "-"):
            self.current = "0"

    def toggle_sign(self):
        if self.current == "0":
            return
        if self.current.startswith("-"):
            self.current = self.current[1:]
        else:
            self.current = "-" + self.current

    def percent(self):
        self.current = format_number(float(self.current) / 100)
        self.reset_next = True

    def set_op(self, op):
        # 연산자를 연속으로 누르면 연산자만 교체
        if self.op is not None and self.reset_next:
            self.op = op
        else:
            if self.op is not None:
                self._evaluate()
                if self.current == "오류":
                    return
            self.stored = float(self.current)
            self.op = op
            self.reset_next = True
        self.history = f"{format_number(self.stored)} {OP_SYMBOLS[op]}"

    def equals(self):
        if self.op is None:
            return
        left = format_number(self.stored)
        right = self.current
        self._evaluate()
        if self.current != "오류":
            self.history = f"{left} {OP_SYMBOLS[self.op]} {right} ="
        self.op = None
        self.stored = None

    def _evaluate(self):
        try:
            result = calculate(self.stored, self.op, float(self.current))
            self.current = format_number(result)
        except ZeroDivisionError:
            self.clear()
            self.current = "오류"
            self.history = "0으로 나눌 수 없습니다"
        self.reset_next = True

    def press(self, key):
        """버튼 라벨/키 하나를 처리하는 단일 진입점."""
        if self.current == "오류" and key not in ("C",):
            self.clear()
        if key.isdigit():
            self.input_digit(key)
        elif key == ".":
            self.input_dot()
        elif key in ("+", "-", "*", "/"):
            self.set_op(key)
        elif key == "=":
            self.equals()
        elif key == "C":
            self.clear()
        elif key == "⌫":
            self.backspace()
        elif key == "±":
            self.toggle_sign()
        elif key == "%":
            self.percent()


# (라벨, 내부 키, 색상 종류)
BUTTONS = [
    [("C", "C", "func"), ("⌫", "⌫", "func"), ("%", "%", "func"), ("÷", "/", "op")],
    [("7", "7", "num"), ("8", "8", "num"), ("9", "9", "num"), ("×", "*", "op")],
    [("4", "4", "num"), ("5", "5", "num"), ("6", "6", "num"), ("−", "-", "op")],
    [("1", "1", "num"), ("2", "2", "num"), ("3", "3", "num"), ("+", "+", "op")],
    [("±", "±", "num"), ("0", "0", "num"), (".", ".", "num"), ("=", "=", "eq")],
]

COLORS = {
    "bg": "#1e1e1e",
    "num": ("#3a3a3a", "#505050"),   # (기본, 마우스 올렸을 때)
    "func": ("#5c5c5c", "#707070"),
    "op": ("#ff9500", "#ffaa33"),
    "eq": ("#ff9500", "#ffaa33"),
}


class CalculatorApp:
    def __init__(self, root):
        import tkinter as tk

        self.tk = tk
        self.root = root
        self.state = CalculatorState()

        root.title("계산기")
        root.geometry("280x400")
        root.resizable(False, False)
        root.configure(bg=COLORS["bg"])

        self.history_var = tk.StringVar()
        self.display_var = tk.StringVar(value="0")

        tk.Label(root, textvariable=self.history_var, anchor="e",
                 bg=COLORS["bg"], fg="#9a9a9a", font=("Arial", 11),
                 padx=12).pack(fill="x", pady=(12, 0))
        tk.Label(root, textvariable=self.display_var, anchor="e",
                 bg=COLORS["bg"], fg="white", font=("Arial", 30),
                 padx=12).pack(fill="x", pady=(0, 8))

        grid = tk.Frame(root, bg=COLORS["bg"])
        grid.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        for r, row in enumerate(BUTTONS):
            grid.rowconfigure(r, weight=1, uniform="row")
            for c, (label, key, kind) in enumerate(row):
                grid.columnconfigure(c, weight=1, uniform="col")
                self._make_button(grid, label, key, kind).grid(
                    row=r, column=c, sticky="nsew", padx=3, pady=3)

        # 키보드로도 입력 가능
        root.bind("<Key>", self._on_key)
        root.bind("<Return>", lambda e: self.press("="))
        root.bind("<BackSpace>", lambda e: self.press("⌫"))
        root.bind("<Escape>", lambda e: self.press("C"))

    def _make_button(self, parent, label, key, kind):
        normal, hover = COLORS[kind]
        # Label을 버튼처럼 사용: macOS에서도 배경색이 그대로 적용된다
        btn = self.tk.Label(parent, text=label, bg=normal, fg="white",
                            font=("Arial", 16), cursor="hand2")
        btn.bind("<Button-1>", lambda e: self.press(key))
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover))
        btn.bind("<Leave>", lambda e: btn.configure(bg=normal))
        return btn

    def _on_key(self, event):
        ch = event.char
        if ch and (ch.isdigit() or ch in "+-*/.%="):
            self.press(ch)

    def press(self, key):
        self.state.press(key)
        self.display_var.set(self.state.current)
        self.history_var.set(self.state.history)


def main():
    import tkinter as tk

    root = tk.Tk()
    CalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
