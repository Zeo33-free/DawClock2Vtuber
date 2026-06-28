"""
DawClock2Vtuber 控制面板
使用 tkinter 实时调节所有动画参数
"""

import tkinter as tk
from tkinter import ttk
import threading

import config


class ControlPanel:
    """小巧的浮动控制面板，实时调节动画参数"""

    def __init__(self, animation=None):
        self._animation = animation
        self._running = False

    def start(self):
        """在后台线程启动 GUI"""
        self._running = True
        t = threading.Thread(target=self._run_tk, daemon=True)
        t.start()
        return t

    def stop(self):
        self._running = False

    # ------------------------------------------------------------------
    # tkinter 主循环
    # ------------------------------------------------------------------
    def _run_tk(self):
        root = tk.Tk()
        root.title("🎵 DawClock2Vtuber 控制面板")
        root.geometry("360x590")
        root.resizable(False, True)
        root.attributes("-topmost", True)

        # 样式
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # ---- 主帧 ----
        main = ttk.Frame(root, padding=12)
        main.pack(fill="both", expand=True)

        row = 0

        # ========== 标题：点头强度 ==========
        ttk.Label(main, text="━━━ 点头 (FaceAngleY) ━━━",
                  font=("", 9, "bold")).grid(row=row, column=0, columnspan=2, pady=(0, 4), sticky="w")
        row += 1

        ttk.Label(main, text="点头强度").grid(row=row, column=0, sticky="w")
        self._nod_var = tk.DoubleVar(value=config.NOD_INTENSITY)
        nod_scale = ttk.Scale(main, from_=0.5, to=12.0, variable=self._nod_var,
                              command=lambda v: self._on_nod(v))
        nod_scale.grid(row=row, column=1, sticky="ew", padx=(8, 0))
        self._nod_lbl = ttk.Label(main, text=f"{config.NOD_INTENSITY:.2f}", width=5)
        self._nod_lbl.grid(row=row, column=2, padx=(4, 0))
        row += 1

        # ========== 标题：上下位移 ==========
        ttk.Label(main, text="━━━ 上下位移 (FacePositionY) ━━━",
                  font=("", 9, "bold")).grid(row=row, column=0, columnspan=3, pady=(10, 4), sticky="w")
        row += 1

        self._pos_enabled = tk.BooleanVar(value=config.ENABLE_POSITION_Y_BOB)
        ttk.Checkbutton(main, text="启用位移", variable=self._pos_enabled,
                        command=self._on_pos_toggle).grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1

        ttk.Label(main, text="位移强度").grid(row=row, column=0, sticky="w")
        self._pos_var = tk.DoubleVar(value=config.POSITION_Y_INTENSITY)
        pos_scale = ttk.Scale(main, from_=0.1, to=5.0, variable=self._pos_var,
                              command=lambda v: self._on_pos(v))
        pos_scale.grid(row=row, column=1, sticky="ew", padx=(8, 0))
        self._pos_lbl = ttk.Label(main, text=f"{config.POSITION_Y_INTENSITY:.2f}", width=5)
        self._pos_lbl.grid(row=row, column=2, padx=(4, 0))
        row += 1

        # ========== 标题：左右微摇 ==========
        ttk.Label(main, text="━━━ 左右微摇 (FaceAngleY) ━━━",
                  font=("", 9, "bold")).grid(row=row, column=0, columnspan=3, pady=(10, 4), sticky="w")
        row += 1

        self._yaw_enabled = tk.BooleanVar(value=config.ENABLE_YAW_SWAY)
        ttk.Checkbutton(main, text="启用摇摆", variable=self._yaw_enabled,
                        command=self._on_yaw_toggle).grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1

        ttk.Label(main, text="摇摆强度").grid(row=row, column=0, sticky="w")
        self._yaw_var = tk.DoubleVar(value=config.YAW_INTENSITY)
        yaw_scale = ttk.Scale(main, from_=0.0, to=2.0, variable=self._yaw_var,
                              command=lambda v: self._on_yaw(v))
        yaw_scale.grid(row=row, column=1, sticky="ew", padx=(8, 0))
        self._yaw_lbl = ttk.Label(main, text=f"{config.YAW_INTENSITY:.2f}", width=5)
        self._yaw_lbl.grid(row=row, column=2, padx=(4, 0))
        row += 1

        # ========== 标题：滚转 ==========
        ttk.Label(main, text="━━━ 滚转 (FaceAngleZ) ━━━",
                  font=("", 9, "bold")).grid(row=row, column=0, columnspan=3, pady=(10, 4), sticky="w")
        row += 1

        self._roll_enabled = tk.BooleanVar(value=config.ENABLE_ROLL)
        ttk.Checkbutton(main, text="启用滚转", variable=self._roll_enabled,
                        command=self._on_roll_toggle).grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1

        ttk.Label(main, text="滚转强度").grid(row=row, column=0, sticky="w")
        self._roll_var = tk.DoubleVar(value=config.ROLL_INTENSITY)
        roll_scale = ttk.Scale(main, from_=0.0, to=1.5, variable=self._roll_var,
                               command=lambda v: self._on_roll(v))
        roll_scale.grid(row=row, column=1, sticky="ew", padx=(8, 0))
        self._roll_lbl = ttk.Label(main, text=f"{config.ROLL_INTENSITY:.2f}", width=5)
        self._roll_lbl.grid(row=row, column=2, padx=(4, 0))
        row += 1

        # ========== 标题：物理参数 ==========
        ttk.Label(main, text="━━━ 物理参数 ━━━",
                  font=("", 9, "bold")).grid(row=row, column=0, columnspan=3, pady=(10, 4), sticky="w")
        row += 1

        ttk.Label(main, text="衰减速度").grid(row=row, column=0, sticky="w")
        self._decay_var = tk.DoubleVar(value=config.ANIMATION_DECAY)
        decay_scale = ttk.Scale(main, from_=0.70, to=0.95, variable=self._decay_var,
                                command=lambda v: self._on_decay(v))
        decay_scale.grid(row=row, column=1, sticky="ew", padx=(8, 0))
        self._decay_lbl = ttk.Label(main, text=f"{config.ANIMATION_DECAY:.2f}", width=5)
        self._decay_lbl.grid(row=row, column=2, padx=(4, 0))
        row += 1

        ttk.Label(main, text="动画速度").grid(row=row, column=0, sticky="w")
        self._speed_var = tk.DoubleVar(value=config.ANIMATION_SPEED)
        speed_scale = ttk.Scale(main, from_=0.1, to=1.0, variable=self._speed_var,
                                command=lambda v: self._on_speed(v))
        speed_scale.grid(row=row, column=1, sticky="ew", padx=(8, 0))
        self._speed_lbl = ttk.Label(main, text=f"{config.ANIMATION_SPEED:.2f}", width=5)
        self._speed_lbl.grid(row=row, column=2, padx=(4, 0))
        row += 1

        # ========== 标题：眨眼 ==========
        ttk.Label(main, text="━━━ 眨眼同步 ━━━",
                  font=("", 9, "bold")).grid(row=row, column=0, columnspan=3, pady=(10, 4), sticky="w")
        row += 1

        self._eye_enabled = tk.BooleanVar(value=config.ENABLE_EYE_BLINK)
        ttk.Checkbutton(main, text="低头时闭眼", variable=self._eye_enabled,
                        command=self._on_eye_toggle).grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1

        ttk.Label(main, text="闭眼力度").grid(row=row, column=0, sticky="w")
        self._eye_var = tk.DoubleVar(value=config.EYE_BLINK_STRENGTH)
        eye_scale = ttk.Scale(main, from_=0.05, to=1.0, variable=self._eye_var,
                              command=lambda v: self._on_eye(v))
        eye_scale.grid(row=row, column=1, sticky="ew", padx=(8, 0))
        self._eye_lbl = ttk.Label(main, text=f"{config.EYE_BLINK_STRENGTH:.2f}", width=5)
        self._eye_lbl.grid(row=row, column=2, padx=(4, 0))
        row += 1

        # ========== 标题：微颤 ==========
        ttk.Label(main, text="━━━ 真人微颤 ━━━",
                  font=("", 9, "bold")).grid(row=row, column=0, columnspan=3, pady=(10, 4), sticky="w")
        row += 1

        self._jitter_enabled = tk.BooleanVar(value=config.ENABLE_HUMAN_JITTER)
        ttk.Checkbutton(main, text="启用微颤", variable=self._jitter_enabled,
                        command=self._on_jitter_toggle).grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1

        ttk.Label(main, text="微颤幅度").grid(row=row, column=0, sticky="w")
        self._jitter_var = tk.DoubleVar(value=config.JITTER_AMOUNT)
        jitter_scale = ttk.Scale(main, from_=0.0, to=1.0, variable=self._jitter_var,
                                 command=lambda v: self._on_jitter(v))
        jitter_scale.grid(row=row, column=1, sticky="ew", padx=(8, 0))
        self._jitter_lbl = ttk.Label(main, text=f"{config.JITTER_AMOUNT:.2f}", width=5)
        self._jitter_lbl.grid(row=row, column=2, padx=(4, 0))
        row += 1

        # ========== 状态栏 ==========
        ttk.Separator(main, orient="horizontal").grid(
            row=row, column=0, columnspan=3, sticky="ew", pady=(10, 6))
        row += 1

        self._status_lbl = ttk.Label(main, text="BPM: -- | 角度: +0.00°",
                                     font=("", 10))
        self._status_lbl.grid(row=row, column=0, columnspan=3)

        # ========== 事件循环 ==========
        self._root = root
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 用 after 定时刷新状态（500ms）
        self._schedule_refresh()

        # 用 after 定时检查是否需要退出
        self._schedule_exit_check()

        root.mainloop()

    # ------------------------------------------------------------------
    # 回调：写入 config 模块
    # ------------------------------------------------------------------
    def _on_nod(self, value):
        config.NOD_INTENSITY = round(float(value), 2)
        self._nod_lbl.config(text=f"{config.NOD_INTENSITY:.2f}")

    def _on_pos_toggle(self):
        config.ENABLE_POSITION_Y_BOB = self._pos_enabled.get()

    def _on_pos(self, value):
        config.POSITION_Y_INTENSITY = round(float(value), 2)
        self._pos_lbl.config(text=f"{config.POSITION_Y_INTENSITY:.2f}")

    def _on_yaw_toggle(self):
        config.ENABLE_YAW_SWAY = self._yaw_enabled.get()

    def _on_yaw(self, value):
        config.YAW_INTENSITY = round(float(value), 2)
        self._yaw_lbl.config(text=f"{config.YAW_INTENSITY:.2f}")

    def _on_roll_toggle(self):
        config.ENABLE_ROLL = self._roll_enabled.get()

    def _on_roll(self, value):
        config.ROLL_INTENSITY = round(float(value), 2)
        self._roll_lbl.config(text=f"{config.ROLL_INTENSITY:.2f}")

    def _on_decay(self, value):
        config.ANIMATION_DECAY = round(float(value), 3)
        self._decay_lbl.config(text=f"{config.ANIMATION_DECAY:.3f}")

    def _on_speed(self, value):
        config.ANIMATION_SPEED = round(float(value), 2)
        self._speed_lbl.config(text=f"{config.ANIMATION_SPEED:.2f}")
        self._speed_lbl.config(text=f"{config.ANIMATION_SPEED:.2f}")

    def _on_jitter_toggle(self):
        config.ENABLE_HUMAN_JITTER = self._jitter_enabled.get()

    def _on_jitter(self, value):
        config.JITTER_AMOUNT = round(float(value), 2)
        self._jitter_lbl.config(text=f"{config.JITTER_AMOUNT:.2f}")

    def _on_eye_toggle(self):
        config.ENABLE_EYE_BLINK = self._eye_enabled.get()

    def _on_eye(self, value):
        config.EYE_BLINK_STRENGTH = round(float(value), 2)
        self._eye_lbl.config(text=f"{config.EYE_BLINK_STRENGTH:.2f}")

    # ------------------------------------------------------------------
    # 状态刷新
    # ------------------------------------------------------------------
    def _refresh_status(self):
        """刷新底部状态栏（BPM + 角度）"""
        try:
            if self._animation:
                bpm = self._animation.bpm
                ax = self._animation.angle_x
                self._status_lbl.config(text=f"BPM: {bpm:.0f} | 点头角度: {ax:+.2f}°")
        except Exception:
            pass

    def _schedule_refresh(self):
        """定时刷新状态栏"""
        if self._running:
            self._refresh_status()
            try:
                self._root.after(500, self._schedule_refresh)
            except tk.TclError:
                pass

    def _schedule_exit_check(self):
        """定时检查是否需要退出"""
        if not self._running:
            try:
                self._root.destroy()
            except tk.TclError:
                pass
            return
        try:
            self._root.after(200, self._schedule_exit_check)
        except tk.TclError:
            pass

    def _on_close(self):
        """关闭窗口时只隐藏，不退出程序"""
        self._root.withdraw()
        print("[GUI] Panel hidden (program still running)")
