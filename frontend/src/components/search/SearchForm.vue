<template>
  <div class="bg-white p-6 shadow-sm">
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
            :isDeparture="true"
            @change="onDepartureChange"
          class="square-selector"
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
          class="square-selector"
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
          class="square-selector"
          />
        </div>
        
      <div>
          <DateSelector 
            id="return-date"
            label="回程日期 (選填)"
            v-model="formData.returnDate"
            :min-date="formData.departureDate"
            :error="errors.returnDate"
          class="square-selector"
          />
      </div>
      
      <!-- Row 3: Class Type & Button -->
      <div>
          <ClassTypeSelector 
            v-model="formData.classType"
            :error="errors.classType"
          :disabled="isSearching"
          class="square-selector"
          />
        </div>
        
      <div class="flex items-end">
          <button 
          class="bg-primary text-white w-full py-2.5"
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

    // 輔助函數：獲取本地時區的 YYYY-MM-DD 日期
    const getLocalDateString = () => {
      const date = new Date();
      const year = date.getFullYear();
      const month = (date.getMonth() + 1).toString().padStart(2, '0');
      const day = date.getDate().toString().padStart(2, '0');
      return `${year}-${month}-${day}`;
    };

    const formData = reactive({
        departureAirport: null,
        arrivalAirport: null,
        departureDate: getLocalDateString(), // 使用本地日期
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
        console.log('SearchForm: Raw API response for Taiwan airports:', JSON.parse(JSON.stringify(airports)));
        if (airports && airports.length > 0) {
          taiwanAirports.value = airports.map(airport => ({
            id: airport.airport_id || airport.id,
            code: airport.iata_code || airport.code || airport.airport_id || airport.id || 'N/A',
            name: airport.name || airport.name_zh || airport.name_en || '未知名稱',
            city: airport.city,
            country: airport.country || 'Taiwan',
            region: '台灣'
          }));
          console.log('SearchForm: Mapped Taiwan airports:', JSON.parse(JSON.stringify(taiwanAirports.value)));
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
      console.log('SearchForm: onDepartureChange received (v-model restored):', JSON.parse(JSON.stringify(selectedAirport)));
      console.log('SearchForm: formData.departureAirport after v-model update:', JSON.parse(JSON.stringify(formData.departureAirport)));

      const airportCode = selectedAirport?.code;

      if (!airportCode) {
        console.log('無效或缺失的 airport code，提前退出 onDepartureChange');
        return;
      }

      loadingDestinations.value = true;
      errors.arrivalAirport = '';
      try {
        console.log(`獲取目的地: 出發=${airportCode}, 日期=${formData.departureDate}`);
        const destinations = await flightService.getDestinations(airportCode, formData.departureDate);
        console.log('原始目的地數據:', destinations);

        if (destinations && destinations.length > 0) {
          const mappedDestinations = destinations.map(airport => {
            const code = airport.code || 'N/A';
            const name = airport.name || '未知名稱';
            const country = airport.country || '';

            let region = '其他';
            if (['TPE', 'TSA', 'KHH', 'RMQ', 'TNN', 'CYI', 'HUN', 'TTT', 'MZG', 'KNH', 'MFK', 'LZN', 'KYD', 'GNI', 'TXG', 'PIF'].includes(code) || country === 'Taiwan') {
              region = '台灣';
            } else if (country === 'China' || ['PEK', 'SHA', 'PVG', 'CAN', 'CTU', 'SZX', 'XIY', 'KMG', 'HGH', 'CSX', 'TAO', 'NKG', 'DLC', 'TSN'].some(c => code.includes(c))) {
              region = '中國';
            } else if (country === 'Japan' || ['NRT', 'HND', 'KIX', 'ITM', 'FUK', 'CTS', 'NGO', 'OKA'].some(c => code.includes(c))) {
              region = '東北亞';
            } else if (country === 'South Korea' || ['ICN', 'GMP', 'PUS', 'CJU'].some(c => code.includes(c))) {
              region = '東北亞';
            } else if (['HKG', 'MFM'].includes(code) || country === 'Hong Kong' || country === 'Macau') {
              region = '香港/澳門';
            } else if (['Thailand', 'Vietnam', 'Singapore', 'Malaysia', 'Philippines', 'Indonesia', 'Cambodia', 'Myanmar', 'Laos', 'Brunei'].includes(country)) {
              region = '東南亞';
            } else if (['United States', 'Canada', 'Mexico', 'Brazil', 'Argentina', 'Chile', 'Peru', 'Colombia'].includes(country)) {
              region = '美洲';
            } else if (['United Kingdom', 'France', 'Germany', 'Italy', 'Spain', 'Netherlands', 'Sweden', 'Russia', 'Switzerland', 'Portugal', 'Greece', 'Turkey'].includes(country)) {
              region = '歐洲';
            } else if (['Australia', 'New Zealand', 'Fiji', 'Papua New Guinea', 'Guam'].includes(country)) {
              region = '大洋洲';
            }
            
            return {
              id: airport.id,
              code: code,
              name: name,
              city: airport.city,
              country: country,
              region: region
            };
          });
          console.log('處理後目的地數據:', mappedDestinations);
          destinationAirports.value = mappedDestinations;
          
          const regionOrder = ['台灣', '東北亞', '香港/澳門', '中國', '東南亞', '美洲', '歐洲', '大洋洲', '其他'];
          destinationAirports.value.sort((a, b) => {
            const regionAIndex = regionOrder.indexOf(a.region);
            const regionBIndex = regionOrder.indexOf(b.region);
            if (regionAIndex !== regionBIndex) {
              return regionAIndex - regionBIndex;
            }
            return (a.name || '').localeCompare(b.name || '');
          });
          
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
      if (formData.departureAirport) {
        onDepartureChange(formData.departureAirport);
      }
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
      if (!formData.arrivalAirport || !formData.arrivalAirport.code || formData.arrivalAirport.code === 'N/A') {
        errors.arrivalAirport = '請選擇有效的目的地機場';
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
      if (!validateForm() || props.isSearching || loadingTaiwanAirports.value || loadingDestinations.value || !formData.arrivalAirport || !formData.arrivalAirport.code || formData.arrivalAirport.code === 'N/A') {
        if(!formData.arrivalAirport || !formData.arrivalAirport.code || formData.arrivalAirport.code === 'N/A') {
          errors.arrivalAirport = '請選擇有效的目的地機場';
        }
        return;
      }
      const searchParams = {
          departure: formData.departureAirport ? formData.departureAirport.code : null,
          arrival: formData.arrivalAirport.code,
          date: formData.departureDate,
          return_date: formData.returnDate || null,
          class_type: formData.classType
      };
      
      emit('search', searchParams);
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

<style scoped>
/* 方正設計 */
:deep(.square-selector input),
:deep(.square-selector select),
button {
  border-radius: 0 !important; /* 移除圓角 */
}

:deep(.square-selector .input),
:deep(.square-selector .form-input) {
  border-radius: 0 !important;
}

:deep(.loading-spinner),
:deep(.animate-spin) {
  border-radius: 50%; /* 保持載入動畫為圓形 */
}
</style> 