"""
VTube Studio WebSocket 客户端
负责连接、认证、发送追踪参数注入请求
token 持久化保存，避免反复弹授权窗
"""

import json
import os
import time
import threading
from websocket import create_connection, WebSocket

import config

TOKEN_FILE = os.path.join(os.path.dirname(__file__), "vts_token.json")


class VTSClient:
    """VTube Studio API WebSocket 客户端"""

    def __init__(self, host: str = None, port: int = None):
        self.host = host or config.VTS_HOST
        self.port = port or config.VTS_PORT
        self.ws: WebSocket | None = None
        self.authenticated = False
        self._token: str | None = self._load_token()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Token 持久化
    # ------------------------------------------------------------------
    def _load_token(self) -> str | None:
        """从文件加载已保存的 token"""
        try:
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, "r") as f:
                    data = json.load(f)
                    token = data.get("token", "")
                    if token:
                        print(f"[VTS] Loaded local token: {token[:8]}...")
                        return token
        except Exception:
            pass
        return None

    def _save_token(self, token: str):
        """保存 token 到文件"""
        try:
            with open(TOKEN_FILE, "w") as f:
                json.dump({"token": token}, f)
            print(f"[VTS] Token saved to {TOKEN_FILE}")
        except Exception as e:
            print(f"[VTS] Token save failed: {e}")

    # ------------------------------------------------------------------
    # 连接管理
    # ------------------------------------------------------------------
    def connect(self) -> bool:
        """连接 WebSocket 并完成认证"""
        url = f"ws://{self.host}:{self.port}"
        print(f"[VTS] Connecting to {url} ...")
        try:
            self.ws = create_connection(url, timeout=5, enable_multithread=True)
            print("[VTS] WebSocket connected")
            return self._authenticate()
        except Exception as e:
            print(f"[VTS] Connection failed: {e}")
            print("[VTS] Make sure VTube Studio is running and API is enabled")
            return False

    def disconnect(self):
        """断开连接"""
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None
        self.authenticated = False

    # ------------------------------------------------------------------
    # 认证流程
    # ------------------------------------------------------------------
    def _send_request(self, msg: dict, timeout: float = 5.0) -> dict:
        """发送请求并等待响应"""
        with self._lock:
            raw = json.dumps(msg)
            old_timeout = self.ws.gettimeout()
            self.ws.settimeout(timeout)
            try:
                self.ws.send(raw)
                resp_raw = self.ws.recv()
                return json.loads(resp_raw)
            finally:
                self.ws.settimeout(old_timeout)

    def _authenticate(self) -> bool:
        """认证流程：优先用本地 token，没有再请求新 token"""
        # ---- 如果已有本地 token，直接用 ----
        if self._token:
            return self._try_session_auth(self._token)

        # ---- 没有 token → 请求新的 ----
        return self._request_new_token()

    def _request_new_token(self) -> bool:
        """请求新 token（仅在首次使用时弹出授权窗）"""
        token_req = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": f"auth_token_{int(time.time())}",
            "messageType": "AuthenticationTokenRequest",
            "data": {
                "pluginName": config.PLUGIN_NAME,
                "pluginDeveloper": config.PLUGIN_DEVELOPER,
            },
        }
        resp = self._send_request(token_req, timeout=30.0)

        if resp.get("messageType") == "APIError":
            err = resp.get("data", {})
            msg = err.get("message", "未知错误")
            print(f"[VTS] Token request failed: {msg}")
            if "ongoing" in msg.lower():
                print("[VTS] Old auth window still open in VTS, close it first")
            else:
                print("[VTS] Click 'Allow' in VTube Studio")
            return False

        token = resp.get("data", {}).get("authenticationToken", "")
        if not token:
            print("[VTS] No token received, auth failed")
            return False

        self._token = token
        self._save_token(token)
        print(f"[VTS] New token: {token[:8]}...")

        return self._try_session_auth(token)

    def _try_session_auth(self, token: str) -> bool:
        """尝试用 token 进行会话认证"""
        auth_req = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": f"auth_session_{int(time.time())}",
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": config.PLUGIN_NAME,
                "pluginDeveloper": config.PLUGIN_DEVELOPER,
                "authenticationToken": token,
            },
        }
        resp = self._send_request(auth_req)

        if resp.get("data", {}).get("authenticated", False):
            self.authenticated = True
            print("[VTS] Authenticated")
            return True

        # token 无效（可能被用户撤销了）
        reason = resp.get("data", {}).get("reason", "未知原因")
        print(f"[VTS] Session auth failed: {reason}")

        # 如果本地 token 失效，删掉它并尝试重新获取
        if self._token == token:
            self._token = None
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
                print("[VTS] Cleared invalid local token")
            # 不要在这里递归调用 — 由调用方决定是否重试

        return False

    # ------------------------------------------------------------------
    # 注入追踪参数 - 这是核心功能
    # ------------------------------------------------------------------
    def inject_parameters(self, params: dict) -> bool:
        """
        注入追踪参数到 VTube Studio
        params 示例: {"FaceAngleX": 3.5, "FaceAngleY": 0.2, "FacePositionY": -1.0}
        使用 "add" 模式叠加到现有追踪值上，不会完全覆盖面部追踪。
        """
        if not self.authenticated or not self.ws:
            return False

        parameter_values = [
            {"id": name, "value": value} for name, value in params.items()
        ]

        req = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": f"inject_{int(time.time() * 1000)}",
            "messageType": "InjectParameterDataRequest",
            "data": {
                "faceFound": False,
                "mode": "add",  # 叠加模式，不覆盖已有追踪
                "parameterValues": parameter_values,
            },
        }

        try:
            with self._lock:
                self.ws.send(json.dumps(req))
                # 读取响应防止缓冲区堆积（用短超时避免阻塞动画循环）
                old_timeout = self.ws.gettimeout()
                self.ws.settimeout(0.05)
                try:
                    self.ws.recv()
                except Exception:
                    pass  # 忽略超时（无响应堆积时正常情况）
                self.ws.settimeout(old_timeout)
            return True
        except Exception as e:
            print(f"[VTS] Inject failed: {e}")
            self.authenticated = False
            return False

    # ------------------------------------------------------------------
    # 获取当前模型信息
    # ------------------------------------------------------------------
    def get_current_model(self) -> dict | None:
        """获取当前加载的模型信息"""
        if not self.authenticated or not self.ws:
            return None

        req = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": f"model_{int(time.time())}",
            "messageType": "CurrentModelRequest",
        }
        try:
            resp = self._send_request(req)
            return resp.get("data", {})
        except Exception as e:
            print(f"[VTS] 获取模型信息失败: {e}")
            return None

    def get_parameter_list(self) -> list:
        """获取可用追踪参数列表"""
        if not self.authenticated or not self.ws:
            return []

        req = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": f"params_{int(time.time())}",
            "messageType": "InputParameterListRequest",
        }
        try:
            resp = self._send_request(req)
            data = resp.get("data", {})
            defaults = data.get("defaultParameters", [])
            customs = data.get("customParameters", [])
            return defaults + customs
        except Exception as e:
            print(f"[VTS] 获取参数列表失败: {e}")
            return []
