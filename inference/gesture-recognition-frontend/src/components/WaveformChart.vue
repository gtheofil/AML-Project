<template>
  <div>
    <h2>EMG Waveform</h2>
    <div ref="chart" style="width: 100%; height: 400px;"></div>
  </div>
</template>

<script>
import * as echarts from "echarts";

export default {
  props: {
    waveform: Array,
    highlightRange: Array
  },
  mounted() {
    this.chart = echarts.init(this.$refs.chart);
    this.updateChart();
  },
  watch: {
    waveform() {
      this.updateChart();
    }
  },
  methods: {
    updateChart() {
      const option = {
        title: { text: "Real-Time EMG Waveform" },
        xAxis: { type: "category", data: Array.from({ length: this.waveform.length }, (_, i) => i) },
        yAxis: { type: "value" },
        series: [
          {
            name: "EMG Data",
            type: "line",
            data: this.waveform,
            markArea: {
              itemStyle: { color: "rgba(255, 0, 0, 0.3)" },
              data: [[{ xAxis: this.highlightRange[0] }, { xAxis: this.highlightRange[1] }]]
            }
          }
        ]
      };
      this.chart.setOption(option);
    }
  }
};
</script>
