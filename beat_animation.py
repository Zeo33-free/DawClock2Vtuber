"""
节拍 → 头部晃动动画引擎
模拟摄像机捕捉到的人自然点头晃动的感觉

核心思路：
- 不是简单地上下平移模型，而是驱动 Live2D 的 FaceAngle 追踪参数
- 在节拍点施加一个"冲量"，然后让头部按照物理衰减自然回落
- 加入微量随机噪声模拟真人微颤
- 多个角度叠加，产生立体自然的头部晃动
"""

import time
import math
import random
import threading

import config


class BeatAnimation:
    """
    基于物理模拟的头部晃动动画
    VTS 参数映射：
      - FaceAngleY = 俯仰 (点头/抬头) ← 主晃动轴
      - FaceAngleX = 偏航 (左右转头) ← 极微辅助
      - FaceAngleZ = 滚转 (歪头)
      - FacePositionY = 上下位移
    """

    def __init__(self):
        # 当前值（会随时间衰减）
        self._angle_y = 0.0    # 主晃动：点头角度 (FaceAngleY = 俯仰)
        self._angle_x = 0.0    # 左右微摇 (FaceAngleX = 偏航)
        self._angle_z = 0.0    # 滚转 (FaceAngleZ)
        self._pos_y = 0.0      # Y轴位移

        # 速度（用于弹簧衰减模拟）
        self._vel_y = 0.0      # 点头速度
        self._vel_x = 0.0      # 偏航速度
        self._vel_z = 0.0
        self._vel_pos_y = 0.0

        # 衰减系数 (0~1, 越小衰减越快回到原位)
        self._decay = config.ANIMATION_DECAY

        # 弹簧系数（越大回弹越硬越快）
        self._spring = 0.25

        # 当前 BPM
        self._bpm = 120.0

        # 节拍相位 (用于生成连续的晃动)
        self._beat_count = 0

        # 上一个节拍时间
        self._last_beat_time = time.perf_counter()

        # 线程安全
        self._lock = threading.Lock()

        # 预计算的人性化微颤偏移
        self._jitter_phase_x = random.random() * math.pi * 2
        self._jitter_phase_y = random.random() * math.pi * 2
        self._jitter_phase_z = random.random() * math.pi * 2

    # ------------------------------------------------------------------
    # 外部接口：每拍调用一次
    # ------------------------------------------------------------------
    def on_beat(self, bpm: float):
        """在每拍被 MIDI 回调时触发"""
        with self._lock:
            now = time.perf_counter()
            dt = now - self._last_beat_time
            self._last_beat_time = now

            # 更新 BPM（平滑）
            self._bpm = self._bpm * 0.7 + bpm * 0.3
            self._beat_count += 1

            # ---- 根据 BPM 调整冲量大小 ----
            # BPM 快时晃动幅度稍小，慢时稍大
            bpm_factor = 1.0
            if self._bpm > 0:
                # 120 BPM 为基准
                bpm_factor = math.sqrt(120.0 / max(self._bpm, 40))

            # ---- 主点头 (FaceAngleY = 俯仰)：核心上下晃动 ----
            # 在重拍（每小节第一拍）力度更大
            beat_in_bar = self._beat_count % 4
            accent = 1.4 if beat_in_bar == 0 else 1.0

            # 向下点头（负角度 = 低头），冲量驱动 FaceAngleY
            intensity = config.NOD_INTENSITY * bpm_factor * accent
            self._vel_y -= intensity

            # ---- Y轴位移：辅助上下（与点头同向增强效果）----
            if config.ENABLE_POSITION_Y_BOB:
                self._vel_pos_y -= config.POSITION_Y_INTENSITY * bpm_factor * 0.6

            # ---- 极轻微的左右微摇 (FaceAngleX = 偏航) ----
            if config.ENABLE_YAW_SWAY and beat_in_bar == 0:
                direction = 1.0 if (self._beat_count // 4) % 2 == 0 else -1.0
                self._vel_x += direction * config.YAW_INTENSITY * bpm_factor * 0.08

            # ---- 极轻微的滚转 (FaceAngleZ) ----
            if config.ENABLE_ROLL and beat_in_bar == 0:
                roll_dir = 1.0 if (self._beat_count // 4) % 2 == 0 else -1.0
                self._vel_z += roll_dir * config.ROLL_INTENSITY * bpm_factor * 0.05

    # ------------------------------------------------------------------
    # 重置所有动画状态
    # ------------------------------------------------------------------
    def reset(self):
        """重置动画状态到初始值（用于重连时）"""
        with self._lock:
            self._angle_y = 0.0
            self._angle_x = 0.0
            self._angle_z = 0.0
            self._pos_y = 0.0
            self._vel_y = 0.0
            self._vel_x = 0.0
            self._vel_z = 0.0
            self._vel_pos_y = 0.0
            self._bpm = 120.0

    # ------------------------------------------------------------------
    # 外部接口：每帧调用，更新物理模拟
    # ------------------------------------------------------------------
    def update(self, dt: float):
        """
        更新物理模拟
        dt: 距上次更新的秒数
        """
        with self._lock:
            # 弹簧力：将值拉回 0（平衡位置）
            spring_y = -self._spring * self._angle_y
            spring_x = -self._spring * self._angle_x
            spring_z = -self._spring * self._angle_z
            spring_pos_y = -self._spring * self._pos_y

            # 更新速度（弹簧力 + 阻尼衰减）
            self._vel_y = (self._vel_y + spring_y) * self._decay
            self._vel_x = (self._vel_x + spring_x) * self._decay
            self._vel_z = (self._vel_z + spring_z) * self._decay
            self._vel_pos_y = (self._vel_pos_y + spring_pos_y) * self._decay

            # 更新位置（ANIMATION_SPEED 控制整体快慢）
            speed = config.ANIMATION_SPEED * dt * 60  # 归一化到 ~60fps
            self._angle_y += self._vel_y * speed
            self._angle_x += self._vel_x * speed
            self._angle_z += self._vel_z * speed
            self._pos_y += self._vel_pos_y * speed

            # ---- 安全钳位：防止值失控 ----
            max_angle = 20.0
            max_pos = 8.0
            self._angle_y = max(-max_angle, min(max_angle, self._angle_y))
            self._angle_x = max(-max_angle, min(max_angle, self._angle_x))
            self._angle_z = max(-max_angle, min(max_angle, self._angle_z))
            self._pos_y = max(-max_pos, min(max_pos, self._pos_y))

            # 微小值直接归零，避免永久颤动
            if abs(self._angle_y) < 0.001:
                self._angle_y = 0.0
                self._vel_y = 0.0
            if abs(self._angle_x) < 0.001:
                self._angle_x = 0.0
                self._vel_x = 0.0
            if abs(self._angle_z) < 0.001:
                self._angle_z = 0.0
                self._vel_z = 0.0
            if abs(self._pos_y) < 0.001:
                self._pos_y = 0.0
                self._vel_pos_y = 0.0

    # ------------------------------------------------------------------
    # 外部接口：获取当前应发送给 VTS 的参数值
    # ------------------------------------------------------------------
    def get_parameters(self) -> dict:
        """
        返回当前帧应该注入 VTS 的追踪参数
        使用 "add" 模式，所以这些值是偏移量
        """
        with self._lock:
            # VTS: FaceAngleY=俯仰(点头), FaceAngleX=偏航(左右), FaceAngleZ=滚转
            params = {
                "FaceAngleY": self._angle_y,   # 主晃动：点头
                "FaceAngleX": self._angle_x,   # 辅助：左右微摇
                "FaceAngleZ": self._angle_z,   # 辅助：滚转
            }

            if config.ENABLE_POSITION_Y_BOB:
                params["FacePositionY"] = self._pos_y

            # ---- 人性化微颤 ----
            if config.ENABLE_HUMAN_JITTER:
                t = time.perf_counter()
                jitter = config.JITTER_AMOUNT
                # 使用不同频率的正弦波叠加，模拟真人微颤
                params["FaceAngleY"] += math.sin(t * 7.3 + self._jitter_phase_x) * jitter * 0.5
                params["FaceAngleX"] += math.sin(t * 5.7 + self._jitter_phase_y) * jitter * 0.3
                params["FaceAngleZ"] += math.sin(t * 6.1 + self._jitter_phase_z) * jitter * 0.2

            # ---- 点头同步眨眼（低头时闭眼）----
            if config.ENABLE_EYE_BLINK:
                # 只在低头时触发（_angle_y < 0），闭眼幅度正比于低头角度
                eye_close = max(0.0, -self._angle_y) * config.EYE_BLINK_STRENGTH
                if eye_close > 0.001:
                    params["EyeOpenLeft"] = -eye_close
                    params["EyeOpenRight"] = -eye_close

            # 过滤掉接近零的值，减少传输数据
            return {k: round(v, 4) for k, v in params.items() if abs(v) > 0.0001}

    # ------------------------------------------------------------------
    # 属性
    # ------------------------------------------------------------------
    @property
    def bpm(self) -> float:
        return self._bpm

    @property
    def angle_x(self) -> float:
        """返回当前点头角度 (FaceAngleY = 俯仰)"""
        return self._angle_y
