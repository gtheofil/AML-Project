import json
import torch
import numpy as np
from channels.generic.websocket import AsyncWebsocketConsumer
from my_model import MyGestureModel  # Import the gesture classification model

class GestureRecognitionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handles new WebSocket connections."""
        await self.accept()
        self.model = MyGestureModel()  # Load the gesture classification model
        print("WebSocket connection established")

    async def receive(self, text_data):
        """Processes incoming data, runs model inference, and sends the result."""
        data = json.loads(text_data)
        emg = np.array([data["emg"]])
        acc = np.array(data["acc"])
        gyro = np.array(data["gyro"])

        # Combine EMG and IMU data into a single input tensor
        input_data = np.concatenate((emg, acc, gyro)).reshape(1, 15, 10)

        # Perform gesture classification using the model
        input_tensor = torch.tensor(input_data, dtype=torch.float32)
        output = self.model(input_tensor)
        predicted_class = int(torch.argmax(output, dim=1))

        # Send the classification result and waveform data to the frontend
        await self.send(json.dumps({
            "gesture": predicted_class,
            "waveform": list(emg),  # Send only the EMG waveform for visualization
            "highlight_range": [0, 1000]  # Highlight the 1-second data range
        }))

    async def disconnect(self, close_code):
        """Handles WebSocket disconnection."""
        print("WebSocket connection closed")
