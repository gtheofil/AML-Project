<template>
  <div>
    <h1>Gesture Recognition Dashboard</h1>
    <WebSocketHandler />
  </div>
</template>

<script>
import WebSocketHandler from "../components/WebSocketHandler.vue";

export default {
  components: { WebSocketHandler }
};
</script>
