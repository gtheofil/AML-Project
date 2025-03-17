const WS_URL = "ws://localhost:8000/ws/gesture/";
let socket = null;
let reconnectAttempts = 0;
let isManuallyClosed = false;

function connectWebSocket() {
  if (isManuallyClosed) return; // 避免手动关闭后自动重连

  socket = new WebSocket(WS_URL);

  socket.onopen = () => {
    console.log("[INFO] WebSocket connected");
    reconnectAttempts = 0; // 连接成功后重置重试次数
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (typeof websocketCallback === "function") {
        websocketCallback(data);
      }
    } catch (error) {
      console.error("[ERROR] WebSocket 数据解析失败", error);
    }
  };

  socket.onclose = (event) => {
    console.warn("[WARNING] WebSocket disconnected", event);
    if (!isManuallyClosed) retryConnection();
  };

  socket.onerror = (error) => {
    console.error("[ERROR] WebSocket 发生错误", error);
    socket.close();
  };
}

function retryConnection() {
  const retryDelay = Math.min(1000 * 2 ** reconnectAttempts, 30000); // 指数退避，最大 30 秒
  reconnectAttempts++;
  console.log(`[INFO] WebSocket 重新连接尝试 ${reconnectAttempts}, 延迟: ${retryDelay / 1000}s`);
  setTimeout(connectWebSocket, retryDelay);
}

let websocketCallback = null;
export function setWebSocketListener(callback) {
  websocketCallback = callback;
}

export function closeWebSocket() {
  isManuallyClosed = true;
  if (socket) {
    socket.close();
    console.log("[INFO] WebSocket 手动关闭");
  }
}

export function reopenWebSocket() {
  isManuallyClosed = false;
  connectWebSocket();
  console.log("[INFO] WebSocket 重新打开");
}

// 初始连接
connectWebSocket();

export default socket;