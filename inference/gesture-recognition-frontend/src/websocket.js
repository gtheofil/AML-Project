const socket = new WebSocket("ws://localhost:8000/ws/arduino/");

// Event listeners
socket.onopen = () => {
    console.log("WebSocket connected");
};

socket.onclose = () => {
    console.log("WebSocket disconnected");
};

// Function to set a callback for incoming messages
export function setWebSocketListener(callback) {
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        callback(data);  // Pass received data to the provided function
    };
}

export default socket;
