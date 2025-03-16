<template>
  <div class="container">
    <h1>Real-time Gesture Recognition</h1>
    <p>
      Current Gesture: <strong>{{ gestureLabel }}</strong>
    </p>
    <div class="chart-wrapper">
      <div class="chart-container">
        <canvas ref="waveformChart"></canvas>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watchEffect, nextTick } from "vue";
import { setWebSocketListener } from "./websocket";
import Chart from "chart.js/auto";

export default {
  setup() {
    const NUM_CHANNELS = 10; // 4 EMG + 6 IMU
    const waveformChart = ref(null);
    const gestureLabel = ref("Waiting for data...");
    const waveformData = ref([...Array(NUM_CHANNELS)].map(() => new Array(1000).fill(0))); // 10 channels, 1000ms each
    let chartInstance = null;

    // Initialize WebSocket listener
    onMounted(() => {
      setWebSocketListener((data) => {
        gestureLabel.value = `Gesture ${data.gesture}`;
        
        // Ensure all 10 channels are updated
        if (data.waveform.length === NUM_CHANNELS * 1000) {
          for (let i = 0; i < NUM_CHANNELS; i++) {
            waveformData.value[i] = data.waveform.slice(i * 1000, (i + 1) * 1000);
          }
        }
      });

      // Ensure DOM is rendered before initializing the chart
      nextTick(() => {
        initChart();
      });
    });

    function initChart() {
      if (!waveformChart.value) return;
      const ctx = waveformChart.value.getContext("2d");

      const colors = [
        "red", "blue", "green", "purple", "orange", "pink", "brown", "cyan", "magenta", "black"
      ]; // Unique colors for each channel

      chartInstance = new Chart(ctx, {
        type: "line",
        data: {
          labels: Array.from({ length: 1000 }, (_, i) => i),
          datasets: waveformData.value.map((data, i) => ({
            label: `Channel ${i + 1}`,
            data: data,
            borderColor: colors[i % colors.length],
            borderWidth: 1.5,
            pointRadius: 0, // Smooth line without dots
          })),
        },
        options: {
          responsive: true,
          maintainAspectRatio: false, // Allow flexible resizing
          animation: false, // Reduce latency
          scales: {
            x: { display: false },
            y: { beginAtZero: true },
          },
        },
      });
    }

    // Automatically update chart when waveformData changes
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
</style>
