<template>
  <div class="search-form">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-x-6 gap-y-6 items-end">
      <!-- Departure -->
      <div class="form-group lg:col-span-1">
        <label for="departure" class="form-label">出發地</label>
        <div class="input-wrapper">
          <svg class="input-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
          <AirportSelector
            id="departure"
            placeholder="選擇機場"
            :airports="taiwanAirports"
            v-model="formData.departureAirport"
            :loading="loadingTaiwanAirports"
            :error="errors.departureAirport"
            :disabled="isSearching"
            @change="onDepartureChange"
            class="input"
          />
        </div>
      </div>

      <!-- Arrival -->
      <div class="form-group lg:col-span-1">
        <label for="arrival" class="form-label">目的地</label>
        <div class="input-wrapper">
          <svg class="input-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
          <AirportSelector
            id="arrival"
            placeholder="選擇機場"
            :airports="destinationAirports"
            v-model="formData.arrivalAirport"
            :loading="loadingDestinations"
            :error="errors.arrivalAirport"
            :disabled="!formData.departureAirport || isSearching"
            class="input"
          />
        </div>
      </div>

      <!-- Departure Date -->
      <div class="form-group lg:col-span-1">
        <label for="departure-date" class="form-label">出發日期</label>
        <div class="input-wrapper">
          <svg class="input-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
          <DateSelector
            id="departure-date"
            v-model="formData.departureDate"
            :error="errors.departureDate"
            @change="onDepartureDateChange"
            class="input"
          />
        </div>
      </div>

      <!-- Return Date (Optional) -->
      <div class="form-group lg:col-span-1">
        <label for="return-date" class="form-label">回程日期 <span class="text-gray-400">(選填)</span></label>
        <div class="input-wrapper">
          <svg class="input-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
          <DateSelector
            id="return-date"
            v-model="formData.returnDate"
            :min-date="formData.departureDate"
            :error="errors.returnDate"
            class="input"
          />
        </div>
      </div>

      <!-- Submit Button -->
      <div class="form-group lg:col-span-1">
        <button
          class="search-btn w-full"
          @click="submitSearch"
          :disabled="isSearching || loadingTaiwanAirports || loadingDestinations"
          :class="{ 'opacity-70 cursor-not-allowed': isSearching || loadingTaiwanAirports || loadingDestinations }"
        >
          <svg v-if="isSearching" class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          <span v-if="isSearching">搜尋中...</span>
          <span v-else>搜尋航班</span>
        </button>
      </div>

      <!-- Class Type (moved below for better flow on smaller screens, optional) -->
      <div class="form-group md:col-span-2 lg:col-span-5 mt-2">
        <label class="form-label sr-only">艙等</label> <!-- Hide label visually but keep for accessibility -->
        <div class="input-wrapper relative">
          <!-- Optional: Icon for class type -->
          <ClassTypeSelector
            v-model="formData.classType"
            :error="errors.classType"
            :disabled="isSearching"
            class="w-full bg-gray-50 border border-gray-200 rounded-md text-sm focus:ring-primary focus:border-primary"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AirportSelector from '../AirportSelector.vue';
import DateSelector from '../DateSelector.vue';
import ClassTypeSelector from '../ClassTypeSelector.vue';
import flightService from '@/api/services/flightService';
import { ref, reactive, onMounted } from 'vue';

export default {
  name: 'SearchForm',
  components: {
    AirportSelector,
    DateSelector,
    ClassTypeSelector
  },
  props: {
    isSearching: {
      type: Boolean,
      default: false
    }
  },
  emits: ['search'],
  setup(props, { emit }) {
    const taiwanAirports = ref([]);
    const destinationAirports = ref([]);
    const loadingTaiwanAirports = ref(false);
    const loadingDestinations = ref(false);

    const formData = reactive({
      departureAirport: null,
      arrivalAirport: null,
      departureDate: new Date().toISOString().split('T')[0],
      returnDate: '',
      classType: 'economy'
    });

    const errors = reactive({
      departureAirport: '',
      arrivalAirport: '',
      departureDate: '',
      returnDate: '',
      classType: ''
    });

    const fetchTaiwanAirports = async () => {
      loadingTaiwanAirports.value = true;
      errors.departureAirport = '';
      try {
        const airports = await flightService.getTaiwanAirports(formData.departureDate);
        if (airports && airports.length > 0) {
          taiwanAirports.value = airports.map(airport => ({
            id: airport.airport_id || airport.id,
            code: airport.iata_code || airport.code,
            name: airport.name || airport.name_zh || airport.name_en,
            city: airport.city,
          })).sort((a, b) => a.code.localeCompare(b.code));
        } else {
          taiwanAirports.value = [];
          errors.departureAirport = '無法載入出發機場';
        }
      } catch (error) {
        console.error('獲取台灣機場資料時出錯:', error);
        taiwanAirports.value = [];
        errors.departureAirport = '載入出發機場失敗';
      } finally {
        loadingTaiwanAirports.value = false;
      }
    };

    const onDepartureChange = async (selectedAirport) => {
      formData.arrivalAirport = null;
      destinationAirports.value = [];
      if (!selectedAirport || !selectedAirport.code) return;
      loadingDestinations.value = true;
      errors.arrivalAirport = '';
      try {
        const destinations = await flightService.getDestinations(selectedAirport.code, formData.departureDate);
        if (destinations && destinations.length > 0) {
          destinationAirports.value = destinations.map(airport => ({
            id: airport.airport_id || airport.id,
            code: airport.iata_code || airport.code,
            name: airport.name || airport.name_zh || airport.name_en,
            city: airport.city,
          })).sort((a, b) => a.code.localeCompare(b.code));
        } else {
          destinationAirports.value = [];
          errors.arrivalAirport = '此出發地無可用目的地';
        }
      } catch (error) {
        console.error('獲取目的地機場時出錯:', error);
        destinationAirports.value = [];
        errors.arrivalAirport = '載入目的地失敗';
      } finally {
        loadingDestinations.value = false;
      }
    };

    const onDepartureDateChange = () => {
      fetchTaiwanAirports();
      onDepartureChange(formData.departureAirport);
    };

    const validateForm = () => {
      let isValid = true;
      errors.departureAirport = formData.departureAirport ? '' : '請選擇出發機場';
      errors.arrivalAirport = formData.arrivalAirport ? '' : '請選擇目的地機場';
      errors.departureDate = formData.departureDate ? '' : '請選擇出發日期';
      errors.returnDate = '';
      if (formData.returnDate) {
        const depDate = new Date(formData.departureDate);
        const retDate = new Date(formData.returnDate);
        if (retDate < depDate) {
          errors.returnDate = '回程日期必須在出發日期之後';
          isValid = false;
        }
      }
      return isValid && !errors.departureAirport && !errors.arrivalAirport && !errors.departureDate;
    };

    const submitSearch = () => {
      if (!validateForm() || props.isSearching || loadingTaiwanAirports.value || loadingDestinations.value) {
        return;
      }
      emit('search', { ...formData });
    };

    onMounted(fetchTaiwanAirports);

    return {
      taiwanAirports,
      destinationAirports,
      loadingTaiwanAirports,
      loadingDestinations,
      formData,
      errors,
      onDepartureChange,
      onDepartureDateChange,
      submitSearch
    };
  }
};
</script>

<style scoped>
.search-form {
  width: 100%;
}

.form-group {
  @apply relative;
}

.form-label {
  @apply block text-sm font-medium text-gray-700 mb-1.5;
}

.input-wrapper {
  @apply relative;
}

.input-icon {
  @apply absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 z-10 pointer-events-none;
}

/* Override base input padding for icon */
:deep(.input) {
  @apply pl-10 !important;
}

/* Adjust selector specific padding if needed */
:deep(.airport-selector .input) {
   /* padding adjustments specific to airport selector if icon overlaps */
}

:deep(.date-selector .input) {
   /* padding adjustments specific to date selector if icon overlaps */
}

.search-btn {
  @apply w-full h-[50px] flex justify-center items-center text-white font-medium rounded-lg transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary shadow-lg;
  background: linear-gradient(135deg, theme('colors.primary.DEFAULT') 0%, theme('colors.primary.dark') 100%);
}

.search-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, theme('colors.primary.dark') 0%, theme('colors.primary.dark') 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

.search-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.1);
}

/* Style for ClassTypeSelector (if you want it integrated visually) */
:deep(.class-type-selector select) { /* Assuming ClassTypeSelector uses a select element */
  @apply pl-3 pr-10 py-3 bg-gray-50 border border-gray-200 rounded-md text-sm w-full shadow-sm transition-all focus:border-primary focus:ring focus:ring-primary-light/40 focus:outline-none appearance-none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 0.5rem center;
  background-repeat: no-repeat;
  background-size: 1.5em 1.5em;
}

</style> 