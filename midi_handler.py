"""
虚拟 MIDI 输入设备 (使用 pygame.midi)
创建虚拟 MIDI 端口，接收来自 DAW 的 MIDI 时钟信号和音符事件
"""

import time
import threading
from collections import deque

import pygame.midi

import config


# MIDI 消息类型常量
MIDI_CLOCK = 0xF8        # 时钟脉冲（每拍24个）
MIDI_START = 0xFA        # 开始播放
MIDI_CONTINUE = 0xFB     # 继续播放
MIDI_STOP = 0xFC         # 停止播放
MIDI_NOTE_ON = 0x90      # 音符开（通道1）
MIDI_NOTE_OFF = 0x80     # 音符关（通道1）


class VirtualMIDIInput:
    """
    创建虚拟 MIDI 输入端口并监听 MIDI 消息。
    DAW 可以像连接普通 MIDI 设备一样连接此虚拟端口。
    """

    def __init__(self, port_name: str = None, on_beat: callable = None):
        """
        port_name: 虚拟 MIDI 端口名称
        on_beat: 每拍触发回调 callback(bpm)
        """
        self.port_name = port_name or config.MIDI_PORT_NAME
        self.on_beat = on_beat

        # MIDI 时钟计数 (24 时钟 = 1 拍)
        self._clock_count = 0
        self._ppqn = 24  # pulses per quarter note

        # BPM 计算
        self._clock_times = deque(maxlen=24)
        self._bpm = 120.0

        # 播放状态
        self.is_playing = False

        # pygame.midi 实例
        self._midi_in = None
        self._input_id = None

        # 线程
        self._running = False
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # 端口管理
    # ------------------------------------------------------------------
    def open(self) -> bool:
        """打开虚拟 MIDI 端口"""
        try:
            pygame.midi.init()
            print(f"[MIDI] pygame.midi initialized")

            # 列出可用端口
            self._print_available_ports()

            # 查找匹配名称的输入端口
            device_id = self._find_matching_port()

            if device_id is None:
                print("[MIDI] No MIDI input ports found")
                print("[MIDI] Use loopMIDI to create a virtual MIDI port")
                print("[MIDI] Download: https://www.tobias-erichsen.de/software/loopmidi.html")
                print("[MIDI] Create a port and re-run")
                return False

            self._input_id = device_id
            self._midi_in = pygame.midi.Input(device_id)
            print(f"[MIDI] Opened MIDI input: '{self.port_name}' (device ID: {device_id})")
            print(f"[MIDI] Select this port in your DAW's MIDI clock output")

            # 启动读取线程
            self._running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()

            return True

        except Exception as e:
            print(f"[MIDI] Failed to open port: {e}")
            import traceback
            traceback.print_exc()
            return False

    def close(self):
        """关闭 MIDI 端口"""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)
        if self._midi_in:
            try:
                self._midi_in.close()
            except Exception:
                pass
            self._midi_in = None
        try:
            pygame.midi.quit()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 端口发现
    # ------------------------------------------------------------------
    def _print_available_ports(self):
        """打印所有可用 MIDI 端口"""
        count = pygame.midi.get_count()
        print(f"[MIDI] {count} MIDI devices found:")
        for i in range(count):
            info = pygame.midi.get_device_info(i)
            # info: (interf, name, is_input, is_output, opened)
            name = info[1].decode() if isinstance(info[1], bytes) else info[1]
            io_type = "IN " if info[2] else "OUT"
            print(f"  [{i}] {io_type} - {name}")

    def _find_matching_port(self) -> int | None:
        """
        查找匹配 port_name 的 MIDI 输入端口
        如果没有精确匹配，回退到第一个可用的输入端口
        """
        count = pygame.midi.get_count()
        first_input = None

        for i in range(count):
            info = pygame.midi.get_device_info(i)
            name = info[1].decode() if isinstance(info[1], bytes) else info[1]
            is_input = info[2]

            if is_input and first_input is None:
                first_input = i

            if is_input and self.port_name.lower() in name.lower():
                return i

        # 没有精确匹配 → 使用第一个输入端口
        if first_input is not None:
            info = pygame.midi.get_device_info(first_input)
            name = info[1].decode() if isinstance(info[1], bytes) else info[1]
            print(f"[MIDI] '{self.port_name}' not found, using first available: '{name}'")
            self.port_name = name
            return first_input

        return None

    # ------------------------------------------------------------------
    # 读取线程
    # ------------------------------------------------------------------
    def _read_loop(self):
        """持续轮询 MIDI 输入"""
        while self._running:
            if self._midi_in and self._midi_in.poll():
                events = self._midi_in.read(32)
                for event in events:
                    # event: [[status, data1, data2, data3], timestamp_ms]
                    msg = event[0]
                    self._process_message(msg)
            else:
                time.sleep(0.001)  # 1ms 轮询间隔

    def _process_message(self, msg: list):
        """处理 MIDI 消息"""
        if not msg:
            return
        status = msg[0]

        if status == MIDI_CLOCK:
            self._handle_clock()

        elif status == MIDI_START:
            self.is_playing = True
            self._clock_count = 0
            print("[MIDI] > DAW started")

        elif status == MIDI_CONTINUE:
            self.is_playing = True
            print("[MIDI] > DAW continued")

        elif status == MIDI_STOP:
            self.is_playing = False
            self._clock_count = 0
            print("[MIDI] ■ DAW stopped")

        elif status & 0xF0 == MIDI_NOTE_ON:
            velocity = msg[2] if len(msg) > 2 else 0
            if velocity > 0:
                self._trigger_beat()

    # ------------------------------------------------------------------
    # 时钟处理
    # ------------------------------------------------------------------
    def _handle_clock(self):
        """处理 MIDI 时钟脉冲"""
        now = time.perf_counter()
        self._clock_times.append(now)
        self._clock_count += 1

        # 计算 BPM (基于时钟脉冲间隔)
        if len(self._clock_times) >= 2:
            dt = (self._clock_times[-1] - self._clock_times[0]) / (len(self._clock_times) - 1)
            if dt > 0:
                # 24 个时钟 = 1 拍 → BPM = 60 / (dt * 24)
                self._bpm = 60.0 / (dt * 24)

        # 每拍触发一次 (24 个时钟 = 1 拍)
        if self._clock_count >= self._ppqn:
            self._clock_count = 0
            self._trigger_beat()

    def _trigger_beat(self):
        """每拍触发"""
        if self.on_beat:
            self.on_beat(self._bpm)

    # ------------------------------------------------------------------
    # 属性
    # ------------------------------------------------------------------
    @property
    def bpm(self) -> float:
        """当前 BPM"""
        return self._bpm
