<template>
  <div class="container">
    <h1>Real-time Gesture Recognition for AML lab</h1>
    <p>
      Current Gesture: <strong>{{ gestureLabel }}</strong>
    </p>

    <!-- WebSocket 状态 -->
    <p class="ws-status">{{ wsStatus }}</p>

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
import { ref, onMounted, watchEffect, nextTick, computed } from "vue";
import connectWebSocket, { setWebSocketListener } from "./websocket";
import Chart from "chart.js/auto";

export default {
  setup() {
    const NUM_CHANNELS = 10; // 4 EMG + 6 IMU
    const waveformChart = ref(null);
    const gestureLabel = ref("Waiting...");
    const detectedGesture = ref(null); // Store detected gesture index
    const wsStatus = ref("🔴 Disconnected"); // WebSocket 状态
    const waveformData = ref([...Array(NUM_CHANNELS)].map(() => new Array(1000).fill(0))); // 10 channels, 1000ms each
    let chartInstance = null;

    // 计算动态手势图片
    const gestureImage = computed(() => {
      if (detectedGesture.value === null) {
        return new URL("./assets/alpha/waiting.png", import.meta.url).href; // 默认显示 waiting.png
      }
      return new URL(`./assets/alpha/${detectedGesture.value + 1}.png`, import.meta.url).href;
    });

    // 初始化 WebSocket 连接并监听数据
    onMounted(() => {
      connectWebSocket(); // 连接 WebSocket

      setWebSocketListener((data) => {
        console.log("🌐 Received WebSocket Data:", data);

        if (!data || !data.gesture || !data.waveform) return;

        detectedGesture.value = data.gesture;
        gestureLabel.value = `Gesture ${data.gesture}`;

        // 更新 WebSocket 状态
        wsStatus.value = "🟢 Connected";

        // 确保所有 10 个通道都被正确更新
        if (Array.isArray(data.waveform) && data.waveform.length >= NUM_CHANNELS * 1000) {
          for (let i = 0; i < NUM_CHANNELS; i++) {
            waveformData.value[i] = data.waveform.slice(i * 1000, (i + 1) * 1000);
          }
        }
      });

      // 等待 DOM 渲染后初始化 Chart
      nextTick(() => {
        if (!chartInstance) {
          initChart();
        }
      });
    });

    // 初始化 Chart.js
    function initChart() {
      if (!waveformChart.value) return;
      const ctx = waveformChart.value.getContext("2d");

      const colors = [
        "red", "blue", "green", "purple", "orange", "pink", "brown", "cyan", "magenta", "black"
      ]; // 给 10 个通道不同颜色

      chartInstance = new Chart(ctx, {
        type: "line",
        data: {
          labels: Array.from({ length: 1000 }, (_, i) => i),
          datasets: waveformData.value.map((data, i) => ({
            label: `Channel ${i + 1}`,
            data: data,
            borderColor: colors[i % colors.length],
            borderWidth: 1.5,
            pointRadius: 0, // 平滑曲线
          })),
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: false, // 关闭动画，减少延迟
          scales: {
            x: { display: false },
            y: { 
              beginAtZero: true, 
              min: 0,
              max: 10000, 
            },
          },
        },
      });
    }

    // 自动更新 Chart，当 `waveformData` 变化时触发
    watchEffect(() => {
      if (chartInstance) {
        chartInstance.data.datasets.forEach((dataset, i) => {
          dataset.data = waveformData.value[i];
        });
        chartInstance.update();
      }
    });

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
/* Full-page layout */
html,
body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  background-color: #f8f8f8;
  font-family: Arial, sans-serif;
}

/* Center content */
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

/* WebSocket 状态显示 */
.ws-status {
  font-size: 1rem;
  font-weight: bold;
  margin: 10px;
}

/* Wrapper to create padding around the chart */
.chart-wrapper {
  width: 100%;
  max-width: 850px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Chart container with a visible border */
.chart-container {
  width: 100%;
  height: 400px; /* Increased height for 10-channel visualization */
  border: 2px solid #007bff; /* Blue border */
  border-radius: 10px;
  background: #ffffff;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 15px;
}

/* Gesture Image Display */
.gesture-image {
  margin: 20px 0;
}

.gesture-image img {
  width: 150px; /* Adjust image size */
  height: 150px;
  object-fit: contain;
  border: 2px solid #007bff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>
