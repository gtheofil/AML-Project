<template>
  <div>
    <GestureDisplay :gesture="gesture" />
    <WaveformChart :waveform="waveform" :highlightRange="highlightRange" />
  </div>
</template>

<script>
import { setWebSocketListener } from "../websocket";
import GestureDisplay from "./GestureDisplay.vue";
import WaveformChart from "./WaveformChart.vue";

export default {
  components: { GestureDisplay, WaveformChart },
  data() {
    return {
      gesture: 0,
      waveform: [],
      highlightRange: [0, 1000]
    };
  },
  created() {
    setWebSocketListener((data) => {
      this.gesture = data.gesture;
      this.waveform = data.waveform;
      this.highlightRange = data.highlight_range;
    });
  }
};
</script>
