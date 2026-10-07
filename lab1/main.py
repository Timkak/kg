# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import colorchooser
import random

BG = "#f2f2f2"


def rgb_to_cmyk(r, g, b):
    """RGB (0..255) -> CMYK (каждая компонента 0..1)."""
    if r == 0 and g == 0 and b == 0:
        return 0.0, 0.0, 0.0, 1.0
    r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
    k = 1.0 - max(r_, g_, b_)
    c = (1.0 - r_ - k) / (1.0 - k)
    m = (1.0 - g_ - k) / (1.0 - k)
    y = (1.0 - b_ - k) / (1.0 - k)
    return c, m, y, k


def cmyk_to_rgb(c, m, y, k):
    """CMYK (0..1) -> RGB (0..255)."""
    r = 255.0 * (1.0 - c) * (1.0 - k)
    g = 255.0 * (1.0 - m) * (1.0 - k)
    b = 255.0 * (1.0 - y) * (1.0 - k)
    return r, g, b


def rgb_to_hsv(r, g, b):
    """RGB (0..255) -> HSV (H: 0..360, S: 0..1, V: 0..1)."""
    r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
    mx = max(r_, g_, b_)
    mn = min(r_, g_, b_)
    d = mx - mn
    v = mx
    s = 0.0 if mx == 0 else d / mx
    if d == 0:
        h = 0.0
    elif mx == r_:
        h = 60.0 * (((g_ - b_) / d) % 6)
    elif mx == g_:
        h = 60.0 * ((b_ - r_) / d + 2)
    else:
        h = 60.0 * ((r_ - g_) / d + 4)
    return h % 360.0, s, v

def hsv_to_rgb(h, s, v):
    """HSV (H: 0..360, S: 0..1, V: 0..1) -> RGB (0..255)."""
    h = h % 360.0
    c = v * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = v - c
    if h < 60:
        rp, gp, bp = c, x, 0
    elif h < 120:
        rp, gp, bp = x, c, 0
    elif h < 180:
        rp, gp, bp = 0, c, x
    elif h < 240:
        rp, gp, bp = 0, x, c
    elif h < 300:
        rp, gp, bp = x, 0, c
    else:
        rp, gp, bp = c, 0, x
    return (rp + m) * 255.0, (gp + m) * 255.0, (bp + m) * 255.0



class Channel:

    def __init__(self, parent, row, label, lo, hi, model, key, owner, trough):
        self.model = model
        self.key = key
        self.owner = owner
        self.lo, self.hi = lo, hi
        self._silent = False

        tk.Label(parent, text=label, width=2, anchor="w", bg=BG,
                 font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=(6, 2))

        self.var = tk.DoubleVar(value=lo)
        self.scale = tk.Scale(parent, from_=lo, to=hi, orient=tk.HORIZONTAL,
                              variable=self.var, showvalue=False, length=250,
                              resolution=1, command=self._on_scale,
                              bg=BG, troughcolor=trough, highlightthickness=0,
                              bd=1, sliderrelief="raised")
        self.scale.grid(row=row, column=1, sticky="we", padx=2)
        parent.columnconfigure(1, weight=1)

        self.entry_var = tk.StringVar(value=str(int(lo)))
        self.entry = tk.Entry(parent, textvariable=self.entry_var, width=6,
                              justify="right", font=("Consolas", 10))
        self.entry.grid(row=row, column=2, padx=(4, 8))
        self.entry.bind("<Return>", self._on_entry)
        self.entry.bind("<KP_Enter>", self._on_entry)
        self.entry.bind("<FocusOut>", self._on_entry)

    def _on_scale(self, _=None):
        if self._silent:
            return
        self.entry_var.set(str(int(round(self.var.get()))))
        self.owner.on_channel_change(self)

    def _on_entry(self, _=None):
        if self._silent:
            return
        try:
            val = float(self.entry_var.get().replace(",", "."))
        except ValueError:
            self.entry_var.set(str(int(round(self.var.get()))))
            return
        val = int(round(max(self.lo, min(self.hi, val))))
        self._silent = True
        self.var.set(val)
        self.entry_var.set(str(val))
        self._silent = False
        self.owner.on_channel_change(self)

    def get(self):
        return self.var.get()

    def set(self, val):
        val = int(round(max(self.lo, min(self.hi, val))))
        self._silent = True
        self.var.set(val)
        self.entry_var.set(str(val))
        self._silent = False


class ColorApp:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная работа 1 — Цветовые модели: CMYK / RGB / HSV. Онищук Тимофей")
        root.configure(bg=BG)
        root.resizable(False, False)

        self.updating = False
        self.h, self.s, self.v = 0.0, 0.0, 0.0

        main = tk.Frame(root, bg=BG, padx=12, pady=12)
        main.pack(fill="both", expand=True)

        left = tk.Frame(main, bg=BG)
        left.grid(row=0, column=0, sticky="n")
        right = tk.Frame(main, bg=BG)
        right.grid(row=0, column=1, sticky="n", padx=(18, 0))


        tk.Label(right,
                 text="Онищук Тимофей"
                      "",
                 bg=BG, fg="#555555", justify="left",
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(10, 0))
        # ---------------- CMYK ----------------
        gb = tk.LabelFrame(left, text=" CMYK  (0–100 %) ", bg=BG,
                           font=("Segoe UI", 10, "bold"), padx=4, pady=4)
        gb.pack(fill="x", pady=4)
        self.ch_c = Channel(gb, 0, "C", 0, 100, "cmyk", "c", self, "#8fd3f4")
        self.ch_m = Channel(gb, 1, "M", 0, 100, "cmyk", "m", self, "#f48fb1")
        self.ch_y = Channel(gb, 2, "Y", 0, 100, "cmyk", "y", self, "#fff176")
        self.ch_k = Channel(gb, 3, "K", 0, 100, "cmyk", "k", self, "#b0bec5")

        # ---------------- RGB ----------------
        gb = tk.LabelFrame(left, text=" RGB  (0–255) ", bg=BG,
                           font=("Segoe UI", 10, "bold"), padx=4, pady=4)
        gb.pack(fill="x", pady=4)
        self.ch_r = Channel(gb, 0, "R", 0, 255, "rgb", "r", self, "#e57373")
        self.ch_g = Channel(gb, 1, "G", 0, 255, "rgb", "g", self, "#81c784")
        self.ch_b = Channel(gb, 2, "B", 0, 255, "rgb", "b", self, "#64b5f6")

        # ---------------- HSV ----------------
        gb = tk.LabelFrame(left, text=" HSV  (H: 0–360°, S,V: 0–100 %) ", bg=BG,
                           font=("Segoe UI", 10, "bold"), padx=4, pady=4)
        gb.pack(fill="x", pady=4)
        self.ch_h = Channel(gb, 0, "H", 0, 360, "hsv", "h", self, "#ce93d8")
        self.ch_s = Channel(gb, 1, "S", 0, 100, "hsv", "s", self, "#ffab91")
        self.ch_v = Channel(gb, 2, "V", 0, 100, "hsv", "v", self, "#90a4ae")

        self.rgb_ch = {"r": self.ch_r, "g": self.ch_g, "b": self.ch_b}
        self.cmyk_ch = {"c": self.ch_c, "m": self.ch_m,
                        "y": self.ch_y, "k": self.ch_k}
        self.hsv_ch = {"h": self.ch_h, "s": self.ch_s, "v": self.ch_v}

        # right
        prev = tk.LabelFrame(right, text=" Предпросмотр ", bg=BG,
                             font=("Segoe UI", 10, "bold"), padx=8, pady=8)
        prev.pack(fill="x")

        self.preview = tk.Frame(prev, width=240, height=110,
                                bg="#000000", relief="solid", bd=1)
        self.preview.pack()
        self.preview.pack_propagate(False)

        hexrow = tk.Frame(prev, bg=BG)
        hexrow.pack(fill="x", pady=(8, 0))
        tk.Label(hexrow, text="HEX:", bg=BG,
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        self.hex_var = tk.StringVar()
        self.hex_entry = tk.Entry(hexrow, textvariable=self.hex_var, width=9,
                                  justify="center", font=("Consolas", 11))
        self.hex_entry.pack(side="left", padx=6)
        self.hex_entry.bind("<Return>", self._on_hex)
        self.hex_entry.bind("<KP_Enter>", self._on_hex)
        self.hex_entry.bind("<FocusOut>", self._on_hex)

        tk.Button(prev, text="Выбрать цвет…", command=self._choose_color,
                  font=("Segoe UI", 10)).pack(fill="x", pady=(8, 0))

        # pal 
        pal = tk.LabelFrame(right, text=" Палитра ", bg=BG,
                            font=("Segoe UI", 10, "bold"), padx=6, pady=6)
        pal.pack(fill="x", pady=(10, 0))

        row = 0
        for s, v in ((1.0, 1.0), (1.0, 0.65), (0.45, 1.0)):
            for i, hue in enumerate(range(0, 360, 30)):
                r, g, b = hsv_to_rgb(hue, s, v)
                self._swatch(pal, row, i, (int(r), int(g), int(b)))
            row += 1
        for i in range(12):
            val = int(round(255 * (1 - i / 11.0)))
            self._swatch(pal, row, i, (val, val, val))

        tk.Button(right, text="Случайный цвет", font=("Segoe UI", 10),
                  command=self._random_color).pack(fill="x", pady=(8, 0))

        tk.Label(right,
                 text="Изменение любой координаты автоматически\n"
                      "пересчитывает цвет во всех трёх моделях.",
                 bg=BG, fg="#555555", justify="left",
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(10, 0))

        self.set_rgb(0, 120, 215)

    # ------------------------------------------------------------------
    def _swatch(self, parent, r, c, rgb):
        hexs = "#%02X%02X%02X" % rgb
        cv = tk.Canvas(parent, width=17, height=17, bg=hexs,
                       highlightthickness=1, highlightbackground="#888888",
                       cursor="hand2")
        cv.grid(row=r, column=c, padx=1, pady=1)
        cv.bind("<Button-1>", lambda e, col=rgb: self.set_rgb(*col))

    # ------------------------------------------------------------------
    def set_rgb(self, r, g, b):
        """Установить цвет по RGB и пересчитать всё."""
        h, s, v = rgb_to_hsv(r, g, b)
        if s == 0.0:            # для серых/чёрных оттенок не определён —
            h = self.h          # сохраняем текущий
        self.h, self.s, self.v = h, s, v
        self.refresh()

    # ------------------------------------------------------------------
    def on_channel_change(self, ch):
        """Пользователь изменил одну из координат цвета."""
        if self.updating:
            return

        if ch.model == "rgb":
            r = self.rgb_ch["r"].get()
            g = self.rgb_ch["g"].get()
            b = self.rgb_ch["b"].get()
            h, s, v = rgb_to_hsv(r, g, b)
            if s == 0.0:
                h = self.h
            self.h, self.s, self.v = h, s, v

        elif ch.model == "cmyk":
            c = self.cmyk_ch["c"].get() / 100.0
            m = self.cmyk_ch["m"].get() / 100.0
            y = self.cmyk_ch["y"].get() / 100.0
            k = self.cmyk_ch["k"].get() / 100.0
            r, g, b = cmyk_to_rgb(c, m, y, k)
            h, s, v = rgb_to_hsv(r, g, b)
            if s == 0.0:
                h = self.h
            self.h, self.s, self.v = h, s, v

        else:  # hsv — обновляем только изменённую координату
            if ch.key == "h":
                self.h = ch.get()
            elif ch.key == "s":
                self.s = ch.get() / 100.0
            else:
                self.v = ch.get() / 100.0

        self.refresh()

    # ------------------------------------------------------------------
    def refresh(self):
        """Пересчитать и отобразить цвет во всех трёх моделях."""
        r, g, b = hsv_to_rgb(self.h, self.s, self.v)
        ri = max(0, min(255, int(round(r))))
        gi = max(0, min(255, int(round(g))))
        bi = max(0, min(255, int(round(b))))

        c, m, y, k = rgb_to_cmyk(ri, gi, bi)

        self.updating = True
        try:
            self.rgb_ch["r"].set(ri)
            self.rgb_ch["g"].set(gi)
            self.rgb_ch["b"].set(bi)

            self.cmyk_ch["c"].set(round(c * 100))
            self.cmyk_ch["m"].set(round(m * 100))
            self.cmyk_ch["y"].set(round(y * 100))
            self.cmyk_ch["k"].set(round(k * 100))

            self.hsv_ch["h"].set(round(self.h) % 360)
            self.hsv_ch["s"].set(round(self.s * 100))
            self.hsv_ch["v"].set(round(self.v * 100))
        finally:
            self.updating = False

        hexs = "#%02X%02X%02X" % (ri, gi, bi)
        self.preview.config(bg=hexs)
        self.hex_var.set(hexs)

    # ------------------------------------------------------------------
    def _on_hex(self, _=None):
        s = self.hex_var.get().strip().lstrip("#")
        if len(s) == 3:
            s = "".join(ch * 2 for ch in s)
        try:
            r = int(s[0:2], 16)
            g = int(s[2:4], 16)
            b = int(s[4:6], 16)
        except (ValueError, IndexError):
            self.refresh()
            return
        self.set_rgb(r, g, b)

    def _choose_color(self):
        rgb, _hex = colorchooser.askcolor(color=self.hex_var.get(),
                                          title="Выбор цвета")
        if rgb:
            self.set_rgb(int(rgb[0]), int(rgb[1]), int(rgb[2]))

    def _random_color(self):
        self.set_rgb(random.randint(0, 255),
                     random.randint(0, 255),
                     random.randint(0, 255))


# =========================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = ColorApp(root)
    root.mainloop()