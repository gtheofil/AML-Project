<template>
  <div class="container">
    <h1>Real-time Gesture Recognition for AML lab</h1>
    <p>
      Current Gesture: <strong>{{ gestureLabel }}</strong>
    </p>

    <!-- WebSocket 状态 -->
    <p class="ws-status">
      <span :style="{ color: wsStatus === '🟢 Connected' ? 'green' : 'red' }">
        {{ wsStatus }}
      </span>
    </p>

    <!-- Gesture Image Display -->
    <div class="gesture-image">
      <img :src="gestureImage" alt="Recognized Gesture" />
    </div>

    <div class="chart-wrapper">
      <div class="chart-container">
        <canvas ref="waveformChart"></canvas>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watchEffect, nextTick } from "vue";
import connectWebSocket, { setWebSocketListener } from "./websocket";
import Chart from "chart.js/auto";

export default {
  setup() {
    const NUM_CHANNELS = 10; // 4 EMG + 6 IMU
    const waveformChart = ref(null);
    const gestureLabel = ref("Waiting...");
    const detectedGesture = ref(null);
    const wsStatus = ref("🔴 Disconnected");
    const waveformData = ref([...Array(NUM_CHANNELS)].map(() => new Array(5000).fill(0)));  // 10 channels, 5000 data points
    let chartInstance = null;
    const gestureImage = ref("/assets/alpha/waiting.png");

    // 使用 watchEffect 确保图片路径更新
    watchEffect(() => {
      if (detectedGesture.value !== null) {
        import(`@/assets/alpha/${detectedGesture.value}.png`)
          .then((module) => {
            gestureImage.value = module.default;  // 图片路径
            console.log("🖼 Gesture image updated:", gestureImage.value);
          })
          .catch((err) => {
            console.error("Error loading image:", err);
          });
      }
    });

    // 🚀 初始化 WebSocket 连接
    onMounted(() => {
      connectWebSocket();

      setWebSocketListener((data) => {
        console.log("🌐 Received WebSocket Data:", data);

        if (!data || data.gesture === undefined || !Array.isArray(data.waveform)) {
          console.warn("⚠️ WebSocket 数据异常:", data);
          return;
        }

        // 更新手势编号
        detectedGesture.value = data.gesture;
        gestureLabel.value = `Gesture ${data.gesture}`;
        wsStatus.value = "🟢 Connected";

        // 确保 waveformData 变化能触发 Vue 响应式
        // 假设 WebSocket 数据是按每个通道的 5000 个数据传递
        waveformData.value = data.waveform.map((channelData) => {
          // 处理每个通道的 5000 个数据点
          return channelData.slice(0, 5000);  // 确保每个通道的数据长度是 5000
        });

        console.log("📊 Updated waveformData:", JSON.parse(JSON.stringify(waveformData.value)));
        updateChart();  // 更新图表
      });

      nextTick(() => {
        initChart();  // 初始化图表
      });
    });

    // 🚀 初始化 Chart.js
    function initChart() {
      if (!waveformChart.value) return;
      const ctx = waveformChart.value.getContext("2d");

      const colors = [
        "red", "blue", "green", "purple", "orange", "pink", "brown", "cyan", "magenta", "black"
      ];

      chartInstance = new Chart(ctx, {
        type: "line",
        data: {
          labels: Array.from({ length: 5000 }, (_, i) => i), // X轴表示5000个数据点
          datasets: waveformData.value.map((data, i) => ({
            label: `Channel ${i + 1}`,
            data: data,
            borderColor: colors[i % colors.length], // 为每个通道设置不同的颜色
            borderWidth: 1.5,
            pointRadius: 0,
          })),
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: false,
          scales: {
            x: { 
              title: {
                display: true,
                text: 'Time Steps'
              }
            },
            y: {
              beginAtZero: true,
              min: -30000,
              max: 30000,  // 根据你的数据范围调整最大值
              title: {
                display: true,
                text: 'Signal Value'
              }
            },
          },
        },
      });
    }

    // 🚀 确保 Chart.js 重新绘制
    function updateChart() {
      if (!chartInstance) return;
      console.log("📊 Updating Chart.js with new data...");

      // 确保每个通道的数据在图表中更新
      chartInstance.data.datasets.forEach((dataset, i) => {
        dataset.data = waveformData.value[i];  // 更新数据
      });

      chartInstance.update();  // 只更新数据，不销毁
    }

    return {
      gestureLabel,
      waveformChart,
      gestureImage,
      wsStatus,
    };
  },
};
</script>

<style>
html,
body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  background-color: #f8f8f8;
  font-family: Arial, sans-serif;
}

.container {
  width: 90%;
  max-width: 1200px;
  min-height: 80vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
}

.ws-status {
  font-size: 1rem;
  font-weight: bold;
  margin: 10px;
}

.chart-wrapper {
  width: 100%;
  max-width: 850px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.chart-container {
  width: 100%;
  height: 400px;
  border: 2px solid #007bff;
  border-radius: 10px;
  background: #ffffff;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 15px;
}

.gesture-image {
  margin: 20px 0;
}

.gesture-image img {
  width: 150px;
  height: 150px;
  object-fit: contain;
  border: 2px solid #007bff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>
