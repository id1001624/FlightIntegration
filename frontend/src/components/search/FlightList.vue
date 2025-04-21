<template>
  <div class="flex flex-col gap-4">
    <div 
      v-for="flight in flights" 
      :key="flight.flight_id" 
      class="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
    >
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