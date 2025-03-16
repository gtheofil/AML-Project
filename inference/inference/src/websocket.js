// src/websocket.js
const socket = new WebSocket("ws://localhost:8000/ws/gesture/");

socket.onopen = () => console.log("WebSocket connected");
socket.onclose = () => console.log("WebSocket disconnected");

export function setWebSocketListener(callback) {
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    callback(data);
  };
}

export default socket;
