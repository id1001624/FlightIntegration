<template>
  <div class="bg-white p-6 shadow-sm relative z-20">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4 items-end">
      <!-- Row 1: Departure & Arrival -->
      <div>
        <AirportSelector 
          id="departure"
          label="出發地"
          placeholder="選擇或搜尋出發機場"
          :airports="taiwanAirports"
          v-model="formData.departureAirport"
          :loading="loadingTaiwanAirports"
          :error="errors.departureAirport"
          :disabled="isSearching"
          :isDeparture="true"
          @change="onDepartureChange"
          @select-recent-route="handleRecentRouteSelected"
          class="square-selector"
        />
      </div>
        
      <div>
        <AirportSelector 
          id="arrival"
          label="目的地"
          placeholder="選擇或搜尋目的地機場"
          :airports="destinationAirports"
          v-model="formData.arrivalAirport"
          :loading="loadingDestinations"
          :error="errors.arrivalAirport"
          :disabled="!formData.departureAirport || isSearching"
          @select-recent-route="handleRecentRouteSelected"
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
      
      <!-- Row 3: Passenger & Cabin Selection Trigger / Search Button -->
      <div class="md:col-span-1">
        <label class="block text-sm font-medium text-gray-700 mb-1">旅客與艙等</label>
        <button 
          @click="openPassengerModal"
          type="button"
          class="w-full text-left bg-white border border-gray-300 rounded-md shadow-sm px-3 py-2.5 text-sm text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 square-selector flex justify-between items-center"
          :disabled="isSearching"
        >
          <span>{{ passengerCabinDisplay }}</span>
          <svg class="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
        </button>
      </div>
        
      <div class="flex items-end">
        <button 
          class="bg-primary text-white w-full py-2.5 rounded-md shadow-sm hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition duration-150 ease-in-out"
          @click="submitSearch"
          :disabled="isSearching || loadingTaiwanAirports || loadingDestinations"
          :class="{ 'opacity-50 cursor-not-allowed': isSearching || loadingTaiwanAirports || loadingDestinations }"
        >
          <span v-if="isSearching">搜尋中...</span>
          <span v-else>搜尋航班</span>
        </button>
      </div>
    </div>

    <!-- Passenger and Cabin Selection Modal -->
    <PassengerCabinSelectModal
      :visible="isPassengerModalVisible"
      :initial-passengers="formData.passengers"
      :initial-cabin-class="formData.cabinClass"
      @close="closePassengerModal"
      @confirm="handlePassengerConfirm"
    />

    <!-- (可選) 顯示已選路線 -->
    <div v-if="formData.departureAirport && formData.arrivalAirport" class="mt-4 pt-3 border-t border-gray-200 text-center">
        <p class="text-sm text-gray-600">
            <span class="font-medium">{{ formData.departureAirport.name }} ({{ formData.departureAirport.code }})</span>
            <span class="mx-2">→</span>
            <span class="font-medium">{{ formData.arrivalAirport.name }} ({{ formData.arrivalAirport.code }})</span>
        </p>
    </div>

  </div>
</template>

<script>
import AirportSelector from '../AirportSelector.vue';
import DateSelector from '../DateSelector.vue';
import PassengerCabinSelectModal from '../ui/PassengerCabinSelectModal.vue';
import flightService from '@/api/services/flightService';
import { ref, reactive, onMounted, watch, computed } from 'vue';
import { useSearchStore } from '@/store/modules/search';
import { useRoute } from 'vue-router';

export default {
  name: 'SearchForm',
  components: {
    AirportSelector,
    DateSelector,
    PassengerCabinSelectModal
  },
  props: {
    isSearching: {
      type: Boolean,
      default: false
    }
  },
  emits: ['search'],
  setup(props, { emit }) {
    const searchStore = useSearchStore();
    const route = useRoute();
    
    const taiwanAirports = ref([]);
    const destinationAirports = ref([]);
    const loadingTaiwanAirports = ref(false);
    const loadingDestinations = ref(false);

    const isPassengerModalVisible = ref(false);

    const getLocalDateString = () => {
      const date = new Date();
      const year = date.getFullYear();
      const month = (date.getMonth() + 1).toString().padStart(2, '0');
      const day = date.getDate().toString().padStart(2, '0');
      return `${year}-${month}-${day}`;
    };

    const formData = reactive({
        departureAirport: searchStore.searchParams.departureAirport || null,
        arrivalAirport: searchStore.searchParams.arrivalAirport || null,
        departureDate: searchStore.searchParams.departureDate || getLocalDateString(),
        returnDate: searchStore.searchParams.returnDate || '',
        cabinClass: searchStore.searchParams.cabinClass || 'Economy',
        passengers: searchStore.searchParams.passengers || { adults: 1, children: 0, infants: 0 },
    });

    const passengerCabinDisplay = computed(() => {
      const { adults, children, infants } = formData.passengers;
      const totalPassengers = adults + children + infants;
      const cabinText = cabinClassesMap[formData.cabinClass] || formData.cabinClass;
      return `${totalPassengers}位旅客, ${cabinText}`;
    });

    const cabinClassesMap = {
      'Economy': '經濟艙',
      'Premium Economy': '優質經濟艙',
      'Business': '商務艙',
      'First': '頭等艙'
    };

    watch(() => searchStore.searchParams.departureAirport, (newVal) => {
      if (newVal === null) {
        console.log('[SearchForm] Detected store reset, clearing local form airports.');
        formData.departureAirport = null;
        formData.arrivalAirport = null;
        destinationAirports.value = [];
      }
    });

    const errors = reactive({
        departureAirport: '',
        arrivalAirport: '',
        departureDate: '',
        returnDate: '',
    });

    const fetchTaiwanAirports = async () => {
      if (taiwanAirports.value.length > 0) return;
      
      try {
        loadingTaiwanAirports.value = true;
        const airportsData = await flightService.getTaiwanAirports();
        
        let airportsArray = [];
        if (Array.isArray(airportsData)) {
          airportsArray = airportsData;
        } else if (airportsData && airportsData.success && Array.isArray(airportsData.data)) {
          airportsArray = airportsData.data;
        } else {
          console.error('獲取台灣機場列表：資料格式不符合預期');
        }
        
        taiwanAirports.value = airportsArray.map(airport => ({
          ...airport,
          id: airport.id || airport.airport_id,
          code: airport.iata_code || airport.code || airport.airport_id,
          name: airport.name || airport.name_zh || airport.name_en || '未知名稱',
          city: airport.city || '',
          country: airport.country || 'Taiwan',
          region: airport.region || '台灣'
        }));
      } catch (error) {
        console.error('獲取台灣機場列表時出錯:', error);
      } finally {
        loadingTaiwanAirports.value = false;
      }
    };

    const checkUrlParams = async () => {
      if (route.query.from && route.query.to && 
          (!formData.departureAirport || !formData.arrivalAirport)) {
        console.log('[SearchForm] 從URL參數填充機場信息:', route.query.from, route.query.to);
        
        try {
          loadingTaiwanAirports.value = true;
          loadingDestinations.value = true;
          
          const [fromResponse, toResponse] = await Promise.all([
            flightService.getAirportByCode(route.query.from),
            flightService.getAirportByCode(route.query.to)
          ]);
          
          // 處理出發地響應
          if (fromResponse) {
            let fromAirportData = null;
            if (fromResponse.success && fromResponse.data) {
              fromAirportData = fromResponse.data;
            } else if (typeof fromResponse === 'object' && (fromResponse.code || fromResponse.airport_id)) {
              fromAirportData = fromResponse;
            }
            
            if (fromAirportData) {
              // **確保 formData.departureAirport 包含 code 屬性**
              formData.departureAirport = {
                ...fromAirportData,
                code: fromAirportData.code || fromAirportData.airport_id
              };
              console.log('[SearchForm] 已設置出發地機場 (含code):', JSON.parse(JSON.stringify(formData.departureAirport)));
              
              // 獲取所有機場信息
              const allAirportsResponse = await flightService.getAllAirports();
              if (allAirportsResponse) {
                let allAirportsArray = [];
                if (allAirportsResponse.success && Array.isArray(allAirportsResponse.data)) {
                  allAirportsArray = allAirportsResponse.data;
                } else if (Array.isArray(allAirportsResponse)) {
                  allAirportsArray = allAirportsResponse;
                }
                // **確保 destinationAirports 中的對象包含 code 屬性**
                destinationAirports.value = allAirportsArray.map(ap => ({
                  ...ap,
                  code: ap.code || ap.airport_id
                }));
              }
            }
          }
          
          // 處理目的地響應
          if (toResponse) {
            let toAirportData = null;
            if (toResponse.success && toResponse.data) {
              toAirportData = toResponse.data;
            } else if (typeof toResponse === 'object' && (toResponse.code || toResponse.airport_id)) {
              toAirportData = toResponse;
            }
            
            if (toAirportData) {
              // **確保 formData.arrivalAirport 包含 code 屬性**
              formData.arrivalAirport = {
                ...toAirportData,
                code: toAirportData.code || toAirportData.airport_id
              };
              console.log('[SearchForm] 已設置目的地機場 (含code):', JSON.parse(JSON.stringify(formData.arrivalAirport)));
            }
          }
        } catch (error) {
          console.error('[SearchForm] 獲取機場信息時出錯:', error);
        } finally {
          loadingTaiwanAirports.value = false;
          loadingDestinations.value = false;
        }
      }
    };

    const onDepartureChange = async (selectedAirport) => {
      console.log('SearchForm: onDepartureChange received (v-model restored):', JSON.parse(JSON.stringify(selectedAirport)));
      console.log('SearchForm: formData.departureAirport after v-model update:', JSON.parse(JSON.stringify(formData.departureAirport)));

      if (!selectedAirport) {
        console.log('出發地已被清除，重置目的地和目的地列表');
        formData.arrivalAirport = null;
        destinationAirports.value = [];
        return;
      }

      if (!formData.arrivalAirport || 
          (formData.departureAirport && formData.departureAirport.code !== selectedAirport?.code)) {
        formData.arrivalAirport = null;
        destinationAirports.value = [];
      }

      // 檢查機場代碼是否有效，防止使用 'N/A' 或空值作為機場代碼
      const airportCode = selectedAirport?.code;
      if (!airportCode || airportCode === 'N/A') {
        console.log('無效或缺失的 airport code，提前退出 onDepartureChange');
        errors.arrivalAirport = '請選擇有效的出發機場';
        return;
      }

      loadingDestinations.value = true;
      errors.arrivalAirport = '';
      try {
        console.log(`獲取目的地: 出發=${airportCode}, 日期=${formData.departureDate}`);
        const destinations = await flightService.getDestinations(airportCode, formData.departureDate);
        console.log('原始目的地數據:', destinations);

        // 確保 destinations 是數組
        let destinationsArray = [];
        if (Array.isArray(destinations)) {
          destinationsArray = destinations;
        } else if (destinations && destinations.success && Array.isArray(destinations.data)) {
          destinationsArray = destinations.data;
        }

        if (destinationsArray && destinationsArray.length > 0) {
          const mappedDestinations = destinationsArray.map(airport => {
            const code = airport.code || airport.airport_id || 'N/A';
            const name = airport.name_zh || airport.name || '未知名稱';
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
              id: airport.id || airport.airport_id,
              code: code,
              name: name,
              name_zh: airport.name_zh || '',
              name_en: airport.name || '',
              city: airport.city || '',
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
      if (formData.returnDate && new Date(formData.returnDate) < new Date(formData.departureDate)) {
        formData.returnDate = '';
      }
      if (formData.departureAirport && formData.departureAirport.code) {
        onDepartureChange(formData.departureAirport);
      }
    };

    const handleRecentRouteSelected = (route) => {
      console.log('[SearchForm] Recent route selected:', route);
      
      // **確保從最近搜索記錄設置的機場物件包含 code 屬性**
      if (route.departureAirport) {
        formData.departureAirport = {
          ...route.departureAirport,
          code: route.departureAirport.code || route.departureAirport.airport_id
        };
      } else {
        formData.departureAirport = null;
      }
      
      if (route.arrivalAirport) {
        formData.arrivalAirport = {
          ...route.arrivalAirport,
          code: route.arrivalAirport.code || route.arrivalAirport.airport_id
        };
      } else {
        formData.arrivalAirport = null;
      }
      
      console.log('[SearchForm] After recent route selection (departure):', JSON.parse(JSON.stringify(formData.departureAirport)));
      console.log('[SearchForm] After recent route selection (arrival):', JSON.parse(JSON.stringify(formData.arrivalAirport)));
      
      if (formData.departureAirport && formData.departureAirport.code) {
        onDepartureChange(formData.departureAirport);
      } else {
        destinationAirports.value = [];
      }
    };

    const validateForm = () => {
      let isValid = true;
      errors.departureAirport = '';
      errors.arrivalAirport = '';
      errors.departureDate = '';
      errors.returnDate = '';

      if (!formData.departureAirport) {
        errors.departureAirport = '請選擇出發機場';
        isValid = false;
      } else if (!formData.departureAirport.code || formData.departureAirport.code === 'N/A') {
        errors.departureAirport = '請選擇有效的出發機場';
        isValid = false;
      }
      
      if (!formData.arrivalAirport) {
        errors.arrivalAirport = '請選擇目的地機場';
        isValid = false;
      } else if (!formData.arrivalAirport.code || formData.arrivalAirport.code === 'N/A') {
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
      if (!validateForm() || props.isSearching || loadingTaiwanAirports.value || loadingDestinations.value) {
        return;
      }
      
      // 即使通過了 validateForm，也再次檢查關鍵條件
      if (!formData.departureAirport || !formData.departureAirport.code || 
          formData.departureAirport.code === 'N/A' ||
          !formData.arrivalAirport || !formData.arrivalAirport.code || 
          formData.arrivalAirport.code === 'N/A') {
        console.error('搜索前檢測到無效的機場代碼');
        if (!formData.departureAirport || !formData.departureAirport.code || formData.departureAirport.code === 'N/A') {
          errors.departureAirport = '請選擇有效的出發機場';
        }
        if (!formData.arrivalAirport || !formData.arrivalAirport.code || formData.arrivalAirport.code === 'N/A') {
          errors.arrivalAirport = '請選擇有效的目的地機場';
        }
        return;
      }
      
      const searchData = {
        departure: formData.departureAirport.code,
        arrival: formData.arrivalAirport.code,
        date: formData.departureDate,
        return_date: formData.returnDate || null,
        class_type: formData.cabinClass,
      };
      
      emit('search', searchData);
      searchStore.setSearchParams({
        departureAirport: formData.departureAirport,
        arrivalAirport: formData.arrivalAirport,
        departureDate: formData.departureDate,
        returnDate: formData.returnDate,
        cabinClass: formData.cabinClass,
        passengers: formData.passengers,
      });
      
      if (formData.departureAirport && formData.departureAirport.code && 
          formData.arrivalAirport && formData.arrivalAirport.code) {
        searchStore.addRecentSearch({
          departureAirport: { ...formData.departureAirport },
          arrivalAirport: { ...formData.arrivalAirport }
        });
      }
    };

    const openPassengerModal = () => {
      isPassengerModalVisible.value = true;
    };

    const closePassengerModal = () => {
      isPassengerModalVisible.value = false;
    };

    const handlePassengerConfirm = (data) => {
      formData.passengers = { ...data.passengers };
      formData.cabinClass = data.cabinClass;
      closePassengerModal();
    };

    onMounted(async () => {
      await fetchTaiwanAirports();
      await checkUrlParams();
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
      submitSearch,
      isPassengerModalVisible,
      openPassengerModal,
      closePassengerModal,
      handlePassengerConfirm,
      passengerCabinDisplay,
      handleRecentRouteSelected
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