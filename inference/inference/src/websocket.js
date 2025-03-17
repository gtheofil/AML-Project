const WS_URL = "ws://localhost:8000/ws/gesture/";

let socket;
let reconnectInterval = 3000; // 3秒后尝试重连
let isManuallyClosed = false; // 标记是否是用户手动关闭

function connectWebSocket() {
  socket = new WebSocket(WS_URL);

  socket.onopen = () => {
    console.log("✅ WebSocket connected");
    isManuallyClosed = false;
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (typeof handleMessage === "function") {
        handleMessage(data);
      }
    } catch (error) {
      console.error("❌ Error parsing WebSocket message:", error);
    }
  };

  socket.onclose = (event) => {

    console.log("⚠️ WebSocket disconnected", event.reason);
    if (!isManuallyClosed) {
      console.log(`🔄 Attempting to reconnect in ${reconnectInterval / 1000} seconds...`);
      setTimeout(connectWebSocket, reconnectInterval);
    }
  };

  socket.onerror = (error) => {
    console.error("❌ WebSocket error:", error);
  };
}

// 默认消息处理函数
let handleMessage = null;

export function setWebSocketListener(callback) {
  handleMessage = callback;
}

export function closeWebSocket() {
  isManuallyClosed = true;
  if (socket) {
    socket.close();
  }
}

export default connectWebSocket;
