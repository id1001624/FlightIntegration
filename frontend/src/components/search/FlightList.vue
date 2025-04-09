<template>
  <div class="flight-list">
    <div v-for="(flight, index) in flights" :key="flight.id || index" class="flight-item">
      <FlightCard :flight="flight" />
    </div>
  </div>
</template>

<script>
import FlightCard from '../FlightCard.vue';

export default {
  name: 'FlightList',
  components: {
    FlightCard
  },
  props: {
    flights: {
      type: Array,
      required: true
    }
  }
};
</script>

<style scoped>
.flight-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.flight-item {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.flight-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}
</style> 