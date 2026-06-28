"""
DawClock2Vtuber - 主入口
=======================
让 VTube Studio 角色跟随 DAW 节拍自然晃动头部。

使用方法：
  1. 启动 VTube Studio，开启 API (设置 → 允许插件API访问)
  2. 运行此脚本: python main.py
  3. 在 DAW 的 MIDI 输出设置中选择 "DawClock2Vtuber"
  4. 播放 DAW，角色会跟随节拍晃动！

按 Ctrl+C 退出。
"""

import time
import threading
import sys
import signal

from midi_handler import VirtualMIDIInput
from vts_client import VTSClient
from beat_animation import BeatAnimation
from gui import ControlPanel
import config


class DawClock2Vtuber:
    """主控制器"""

    def __init__(self):
        self.animation = BeatAnimation()
        self.vts = VTSClient()
        self.midi = VirtualMIDIInput(on_beat=self._on_beat)

        self._send_thread: threading.Thread | None = None
        self._running = False

    # ------------------------------------------------------------------
    # 事件处理
    # ------------------------------------------------------------------
    def _on_beat(self, bpm: float):
        """MIDI 节拍回调 → 驱动动画引擎"""
        self.animation.on_beat(bpm)

    # ------------------------------------------------------------------
    # 发送线程：定时将动画状态推送到 VTS
    # ------------------------------------------------------------------
    def _send_loop(self):
        """以固定频率发送追踪参数到 VTube Studio"""
        interval = 1.0 / config.SEND_RATE
        last_reconnect_attempt = 0.0  # 防止频繁重连

        while self._running:
            loop_start = time.perf_counter()

            # 更新物理模拟（仅在连接正常时累积冲量）
            self.animation.update(interval)

            # 获取当前参数值
            params = self.animation.get_parameters()

            # 发送到 VTS
            if params and self.vts.authenticated:
                success = self.vts.inject_parameters(params)
                if not success:
                    print("[!] Inject failed, reconnecting...")
                    now = time.perf_counter()
                    if now - last_reconnect_attempt > 8.0:
                        last_reconnect_attempt = now
                        self._try_reconnect()
                    else:
                        print("[!] Last reconnect < 8s, skipping")
            elif not self.vts.authenticated and time.perf_counter() - last_reconnect_attempt > 10.0:
                last_reconnect_attempt = time.perf_counter()
                self._try_reconnect()

            # 保持发送频率
            elapsed = time.perf_counter() - loop_start
            sleep_time = max(0, interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    # ------------------------------------------------------------------
    # 重连逻辑
    # ------------------------------------------------------------------
    def _try_reconnect(self):
        """尝试重新连接 VTS"""
        self.animation.reset()  # 重置动画状态，防止累积值爆炸
        self.vts.disconnect()
        for i in range(3):
            print(f"[*] Reconnect attempt {i+1}/3 ...")
            time.sleep(3)
            if self.vts.connect():
                print("[*] Reconnected!")
                return
        print("[!] Reconnect failed, check VTube Studio")

    # ------------------------------------------------------------------
    # 启动 / 停止
    # ------------------------------------------------------------------
    def start(self):
        """启动所有模块"""
        print("=" * 60)
        print("  DawClock2Vtuber v1.0")
        print("  DAW MIDI Clock -> VTube Studio head animation")
        print("=" * 60)

        # 1. 连接 VTube Studio
        print("\n[1/3] Connect VTube Studio ...")
        if not self.vts.connect():
            print("[!] Cannot connect to VTube Studio, check:")
            print("     1. VTube Studio is running")
            print("     2. 'Allow Plugin API' is enabled in settings")
            print("     3. Port is 8001 (default)")
            print("\n     Will keep running, auto-reconnect when VTS is available")

        # 2. 创建虚拟 MIDI 端口
        print("\n[2/3] Create virtual MIDI port ...")
        if not self.midi.open():
            print("[!] Cannot create virtual MIDI port")
            print("     Windows: install loopMIDI or equivalent")
            print("     Or try running as administrator")
            return

        # 3. 启动发送线程
        print("\n[3/3] Start animation engine ...")
        self._running = True
        self._send_thread = threading.Thread(target=self._send_loop, daemon=True)
        self._send_thread.start()

        # 4. 启动 GUI 控制面板
        self._panel = ControlPanel(animation=self.animation)
        self._panel.start()

        print("\n" + "=" * 60)
        print("  Ready!")
        print(f"  MIDI port: '{config.MIDI_PORT_NAME}'")
        print(f"  VTS address: {config.VTS_HOST}:{config.VTS_PORT}")
        print("  Select the above port in your DAW's MIDI out, then start playback!")
        print("  Press Ctrl+C to exit")
        print("=" * 60 + "\n")

        # 主线程：显示状态
        try:
            while self._running:
                time.sleep(2)
                bpm = self.animation.bpm
                ax = self.animation.angle_x
                status = "Playing" if self.midi.is_playing else "Waiting for DAW"
                print(f"\r[{status}] BPM: {bpm:.0f} | Nod: {ax:+.2f}°  ", end="", flush=True)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        """停止所有模块"""
        print("\n\nShutting down...")
        self._running = False

        if self._send_thread and self._send_thread.is_alive():
            self._send_thread.join(timeout=1)

        self.midi.close()
        self.vts.disconnect()
        self._panel.stop()
        print("Exited. Bye!")


# ------------------------------------------------------------------
# 入口
# ------------------------------------------------------------------
def main():
    app = DawClock2Vtuber()

    # 处理 Ctrl+C
    signal.signal(signal.SIGINT, lambda s, f: app.stop())

    app.start()


if __name__ == "__main__":
    main()
