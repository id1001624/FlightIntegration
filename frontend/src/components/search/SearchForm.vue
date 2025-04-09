<template>
  <div class="search-panel">
    <div class="search-form">
      <div class="form-row">
        <div class="form-group">
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
        
        <div class="form-group">
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
      </div>
      
      <div class="form-row">
        <div class="form-group">
          <DateSelector 
            id="departure-date"
            label="出發日期"
            v-model="formData.departureDate"
            :error="errors.departureDate"
            @change="onDepartureDateChange"
          />
        </div>
        
        <div class="form-group">
          <DateSelector 
            id="return-date"
            label="回程日期 (選填)"
            v-model="formData.returnDate"
            :min-date="formData.departureDate"
            :error="errors.returnDate"
          />
        </div>
      </div>
      
      <div class="form-row">
        <div class="form-group">
          <ClassTypeSelector 
            v-model="formData.classType"
            :error="errors.classType"
          />
        </div>
        
        <div class="form-group search-btn-container">
          <button 
            class="search-btn" 
            @click="submitSearch"
            :disabled="isSearching"
          >
            <span v-if="isSearching">搜尋中...</span>
            <span v-else>搜尋航班</span>
          </button>
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
  data() {
    return {
      taiwanAirports: [],
      destinationAirports: [],
      loadingTaiwanAirports: false,
      loadingDestinations: false,
      formData: {
        departureAirport: null,
        arrivalAirport: null,
        departureDate: new Date().toISOString().split('T')[0],
        returnDate: '',
        classType: 'economy'
      },
      errors: {
        departureAirport: '',
        arrivalAirport: '',
        departureDate: '',
        returnDate: '',
        classType: ''
      }
    };
  },
  methods: {
    async fetchTaiwanAirports() {
      this.loadingTaiwanAirports = true;
      try {
        // 使用當前選擇的出發日期過濾機場
        const airports = await flightService.getTaiwanAirports(this.formData.departureDate);
        if (airports && airports.length > 0) {
          this.taiwanAirports = airports.map(airport => ({
            id: airport.airport_id || airport.id,
            code: airport.iata_code || airport.code,
            name: airport.name || airport.name_zh || airport.name_en,
            city: airport.city,
          }));
          console.log('載入了 Taiwan 機場:', this.taiwanAirports);
        } else {
          this.taiwanAirports = [];
          console.error('API 未返回有效機場資料');
        }
      } catch (error) {
        console.error('獲取機場資料時出錯:', error);
        this.taiwanAirports = [];
      } finally {
        this.loadingTaiwanAirports = false;
      }
    },
    async onDepartureChange(departureCode) {
      if (!departureCode) {
        this.destinationAirports = [];
        this.formData.arrivalAirport = null;
        return;
      }
      
      this.loadingDestinations = true;
      
      try {
        // 使用當前選擇的出發日期過濾目的地
        const destinations = await flightService.getDestinations(departureCode, this.formData.departureDate);
        
        if (destinations && destinations.length > 0) {
          // 確保數據格式正確
          this.destinationAirports = destinations.map(airport => ({
            id: airport.airport_id || airport.id,
            code: airport.iata_code || airport.code,
            name: airport.name || airport.name_zh || airport.name_en,
            city: airport.city,
          }));
        } else {
          this.destinationAirports = [];
        }
      } catch (error) {
        console.error('獲取目的地機場時出錯:', error);
        this.destinationAirports = [];
      } finally {
        this.loadingDestinations = false;
      }
    },
    onDepartureDateChange() {
      // 日期變更時，重新載入機場數據和清空目的地選擇
      this.fetchTaiwanAirports();
      this.destinationAirports = [];
      this.formData.arrivalAirport = null;
    },
    validateForm() {
      let isValid = true;
      this.errors = {
        departureAirport: '',
        arrivalAirport: '',
        departureDate: '',
        returnDate: '',
        classType: ''
      };
      
      if (!this.formData.departureAirport) {
        this.errors.departureAirport = '請選擇出發機場';
        isValid = false;
      }
      
      if (!this.formData.arrivalAirport) {
        this.errors.arrivalAirport = '請選擇目的地機場';
        isValid = false;
      }
      
      if (!this.formData.departureDate) {
        this.errors.departureDate = '請選擇出發日期';
        isValid = false;
      }
      
      // 如果有填寫回程日期，檢查是否在出發日期之後
      if (this.formData.returnDate) {
        const depDate = new Date(this.formData.departureDate);
        const retDate = new Date(this.formData.returnDate);
        
        if (retDate < depDate) {
          this.errors.returnDate = '回程日期必須在出發日期之後';
          isValid = false;
        }
      }
      
      return isValid;
    },
    submitSearch() {
      if (!this.validateForm()) {
        return;
      }
      
      // 構建搜索參數
      const searchParams = {
        departureAirport: this.formData.departureAirport,
        arrivalAirport: this.formData.arrivalAirport,
        departureDate: this.formData.departureDate,
        returnDate: this.formData.returnDate,
        classType: this.formData.classType
      };
      
      // 觸發搜索事件
      this.$emit('search', searchParams);
    }
  },
  created() {
    this.fetchTaiwanAirports();
  }
};
</script>

<style scoped>
.search-panel {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  margin-bottom: 2rem;
  transition: box-shadow 0.3s ease;
}

.search-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-row {
  display: flex;
  gap: 1.5rem;
}

.form-group {
  flex: 1;
}

.search-btn-container {
  display: flex;
  align-items: flex-end;
}

.search-btn {
  width: 100%;
  padding: 0.85rem 1rem;
  background-color: #000;
  color: white;
  border: none;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  letter-spacing: 0.03em;
}

.search-btn:hover {
  background-color: #333;
}

.search-btn:disabled {
  background-color: #999;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
    gap: 1rem;
  }
  
  .search-panel {
    padding: 1.5rem;
  }
}
</style> 