"""
DawClock2Vtuber 配置文件
"""

# ---- VTube Studio 连接设置 ----
VTS_HOST = "127.0.0.1"
VTS_PORT = 8001

# ---- 插件认证信息 ----
PLUGIN_NAME = "DawClock2Vtuber"
PLUGIN_DEVELOPER = "DawClock2Vtuber Dev"

# ---- 虚拟MIDI端口名 ----
# loopMIDI 中创建的端口名（程序会自动匹配模糊名称）
MIDI_PORT_NAME = "DawClock2Vtube"

# ---- 头部晃动参数 ----
# 晃动强度 (FaceAngleX 俯仰角的振幅，单位：度)
NOD_INTENSITY = 5.0

# 是否启用 Y 轴位移辅助晃动
ENABLE_POSITION_Y_BOB = True
POSITION_Y_INTENSITY = 1.5

# 是否启用极轻微的左右摇摆 (FaceAngleY) — 仅在重拍触发，不会变成摇头
ENABLE_YAW_SWAY = True
YAW_INTENSITY = 0.15

# 是否启用极轻微的头部滚动 (FaceAngleZ)
ENABLE_ROLL = True
ROLL_INTENSITY = 0.1

# 动画衰减速度 (越小衰减越快回原位，推荐 0.8~0.88)
ANIMATION_DECAY = 0.82

# 动画整体速度倍率 (0.1=极慢, 0.5=自然, 1.0=原速)
ANIMATION_SPEED = 0.35

# 向 VTS 发送数据的频率 (Hz)
SEND_RATE = 60

# 是否启用随机抖动模拟真人
ENABLE_HUMAN_JITTER = True
JITTER_AMOUNT = 0.15

# 点头时同步眨眼
ENABLE_EYE_BLINK = True
EYE_BLINK_STRENGTH = 0.35   # 闭眼力度（越大闭得越紧）
