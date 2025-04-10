<template>
  <div class="bg-white p-6 rounded-lg shadow-sm">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
      <!-- Row 1: Departure & Arrival -->
      <div>
        <AirportSelector
          id="departure"
          label="出發地"
          placeholder="選擇出發機場"
          :airports="taiwanAirports"
          v-model="formData.departureAirport"
          :loading="loadingTaiwanAirports"
          :error="errors.departureAirport"
          :disabled="isSearching"
          @change="onDepartureChange"
        />
      </div>

      <div>
        <AirportSelector
          id="arrival"
          label="目的地"
          placeholder="選擇目的地機場"
          :airports="destinationAirports"
          v-model="formData.arrivalAirport"
          :loading="loadingDestinations"
          :error="errors.arrivalAirport"
          :disabled="!formData.departureAirport || isSearching"
        />
      </div>

      <!-- Row 2: Dates -->
      <div>
        <DateSelector
          id="departure-date"
          label="出發日期"
          v-model="formData.departureDate"
          :error="errors.departureDate"
          @change="onDepartureDateChange"
        />
      </div>

      <div>
        <DateSelector
          id="return-date"
          label="回程日期 (選填)"
          v-model="formData.returnDate"
          :min-date="formData.departureDate"
          :error="errors.returnDate"
        />
      </div>

      <!-- Row 3: Class Type & Button -->
      <div>
        <ClassTypeSelector
          v-model="formData.classType"
          :error="errors.classType"
          :disabled="isSearching"
        />
      </div>

      <div class="flex items-end">
        <button
          class="btn-primary w-full py-2.5"
          @click="submitSearch"
          :disabled="isSearching || loadingTaiwanAirports || loadingDestinations"
          :class="{ 'opacity-50 cursor-not-allowed': isSearching || loadingTaiwanAirports || loadingDestinations }"
        >
          <span v-if="isSearching">搜尋中...</span>
          <span v-else>搜尋航班</span>
        </button>
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
          console.error('API 未返回有效台灣機場資料');
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
      if (!selectedAirport || !selectedAirport.code) {
          return;
      }
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
      errors.departureAirport = '';
      errors.arrivalAirport = '';
      errors.departureDate = '';
      errors.returnDate = '';
      errors.classType = '';

      if (!formData.departureAirport) {
        errors.departureAirport = '請選擇出發機場';
        isValid = false;
      }
      if (!formData.arrivalAirport) {
        errors.arrivalAirport = '請選擇目的地機場';
        isValid = false;
      }
      if (!formData.departureDate) {
        errors.departureDate = '請選擇出發日期';
        isValid = false;
      }
      if (formData.returnDate) {
        const depDate = new Date(formData.departureDate);
        const retDate = new Date(formData.returnDate);
        if (retDate < depDate) {
          errors.returnDate = '回程日期必須在出發日期之後';
          isValid = false;
        }
      }
      return isValid;
    };

    const submitSearch = () => {
      if (!validateForm() || props.isSearching || loadingTaiwanAirports.value || loadingDestinations.value) {
        return;
      }
      emit('search', { ...formData });
    };

    onMounted(() => {
      fetchTaiwanAirports();
    });

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

<!-- Removed scoped styles --> 