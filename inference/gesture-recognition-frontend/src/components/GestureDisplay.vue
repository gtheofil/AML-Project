<template>
  <div class="gesture-display">
    <h2>Predicted Gesture</h2>
    <div class="gesture-box">
      <span>{{ gestureLabel }}</span>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    gesture: Number
  },
  computed: {
    gestureLabel() {
      const gestureNames = [
        "Gesture 1", "Gesture 2", "Gesture 3", "Gesture 4", 
        "Gesture 5", "Gesture 6", "Gesture 7", "Gesture 8",
        "Gesture 9", "Gesture 10", "Gesture 11", "Gesture 12",
        "Gesture 13", "Gesture 14", "Gesture 15", "Gesture 16",
        "Gesture 17", "Gesture 18", "Gesture 19", "Gesture 20",
        "Gesture 21", "Gesture 22", "Gesture 23", "Gesture 24",
        "Gesture 25", "Gesture 26"
      ];
      return gestureNames[this.gesture] || "Unknown";
    }
  }
};
</script>

<style scoped>
.gesture-display {
  text-align: center;
  padding: 20px;
}

.gesture-box {
  font-size: 24px;
  font-weight: bold;
  padding: 20px;
  border: 2px solid black;
  display: inline-block;
  background-color: lightgray;
}
</style>
