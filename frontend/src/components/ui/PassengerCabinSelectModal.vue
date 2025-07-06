<template>
  <div
    v-if="isVisible"
    class="modal-overlay"
    @click.self="$emit('close')"
  >
    <div class="modal-content">
      <!-- 標題 -->
      <div class="modal-header">
        <h2 class="modal-title">選擇旅客與艙等</h2>
        <button @click="$emit('close')" class="close-btn">×</button>
      </div>

      <!-- 旅客選擇區域 -->
      <div class="passengers-section">
        <h3 class="section-title">旅客人數</h3>
        
        <!-- 成人 -->
        <div class="passenger-row">
          <div class="passenger-info">
            <div class="passenger-type">成人</div>
            <div class="passenger-desc">12歲或以上</div>
          </div>
          <div class="counter-controls">
            <button 
              @click="updatePassengerCount('adults', localPassengers.adults - 1)"
              :disabled="localPassengers.adults <= 1"
              class="counter-btn"
            >
              -
            </button>
            <span class="counter-value">{{ localPassengers.adults }}</span>
            <button 
              @click="updatePassengerCount('adults', localPassengers.adults + 1)"
              :disabled="localPassengers.adults >= 9"
              class="counter-btn"
            >
              +
            </button>
          </div>
        </div>
        
        <!-- 兒童 -->
        <div class="passenger-row">
          <div class="passenger-info">
            <div class="passenger-type">兒童</div>
            <div class="passenger-desc">2-11歲</div>
          </div>
          <div class="counter-controls">
            <button 
              @click="updatePassengerCount('children', localPassengers.children - 1)"
              :disabled="localPassengers.children <= 0"
              class="counter-btn"
            >
              -
            </button>
            <span class="counter-value">{{ localPassengers.children }}</span>
            <button 
              @click="updatePassengerCount('children', localPassengers.children + 1)"
              :disabled="localPassengers.children >= 9"
              class="counter-btn"
            >
              +
            </button>
          </div>
        </div>
        
        <!-- 嬰兒 -->
        <div class="passenger-row">
          <div class="passenger-info">
            <div class="passenger-type">嬰兒 (不佔位)</div>
            <div class="passenger-desc">0-1歲</div>
          </div>
          <div class="counter-controls">
            <button 
              @click="updatePassengerCount('infants', localPassengers.infants - 1)"
              :disabled="localPassengers.infants <= 0"
              class="counter-btn"
            >
              -
            </button>
            <span class="counter-value">{{ localPassengers.infants }}</span>
            <button 
              @click="updatePassengerCount('infants', localPassengers.infants + 1)"
              :disabled="localPassengers.infants >= localPassengers.adults"
              class="counter-btn"
            >
              +
            </button>
          </div>
        </div>
      </div>

      <!-- 艙等選擇區域 -->
      <div class="cabin-section">
        <h3 class="section-title">選擇艙等</h3>
        <div class="cabin-options">
          <label 
            v-for="option in cabinOptions" 
            :key="option.value"
            class="cabin-option"
            :class="{ active: localCabinClass === option.value }"
          >
            <input 
              type="radio" 
              :value="option.value" 
              v-model="localCabinClass"
              class="cabin-radio"
            />
            <div class="cabin-info">
              <div class="cabin-name">{{ option.name }}</div>
              <div class="cabin-desc">{{ option.description }}</div>
            </div>
          </label>
        </div>
      </div>

      <!-- 操作按鈕 -->
      <div class="modal-actions">
        <button
          @click="$emit('close')"
          class="cancel-btn"
        >
          取消
        </button>
        <button
          @click="handleConfirm"
          class="confirm-btn"
        >
          確認
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch } from 'vue';

export default {
  name: 'PassengerCabinSelectModal',
  props: {
    passengers: {
      type: Object,
      default: () => ({ adults: 1, children: 0, infants: 0 })
    },
    cabinClass: {
      type: String,
      default: 'ECONOMY'
    }
  },
  emits: ['close', 'confirm'],
  setup(props, { emit }) {
    // 計算是否顯示 modal
    const isVisible = computed(() => true);
    
    // 本地狀態
    const localPassengers = reactive({
      adults: props.passengers.adults || 1,
      children: props.passengers.children || 0,
      infants: props.passengers.infants || 0
    });
    
    const localCabinClass = ref(props.cabinClass || 'ECONOMY');
    
    // 艙等選項
    const cabinOptions = [
      {
        value: 'ECONOMY',
        name: '經濟艙',
        description: '標準服務，經濟實惠'
      },
      {
        value: 'PREMIUM_ECONOMY',
        name: '豪華經濟艙',
        description: '升級服務，更大空間'
      },
      {
        value: 'BUSINESS',
        name: '商務艙',
        description: '優質服務，舒適座椅'
      },
      {
        value: 'FIRST',
        name: '頭等艙',
        description: '頂級服務，豪華體驗'
      }
    ]
    
    // 監聽 props 變化
    watch(() => props.passengers, (newVal) => {
      localPassengers.adults = newVal.adults || 1;
      localPassengers.children = newVal.children || 0;
      localPassengers.infants = newVal.infants || 0;
    }, { deep: true, immediate: true });
    
    watch(() => props.cabinClass, (newVal) => {
      localCabinClass.value = newVal || 'ECONOMY';
    }, { immediate: true });
    
    // 更新乘客數量
    const updatePassengerCount = (type, count) => {
      if (type === 'adults') {
        localPassengers.adults = Math.max(1, Math.min(count, 9));
        // 確保嬰兒數量不超過成人數量
        if (localPassengers.infants > localPassengers.adults) {
          localPassengers.infants = localPassengers.adults;
        }
      } else if (type === 'children') {
        localPassengers.children = Math.max(0, Math.min(count, 9));
      } else if (type === 'infants') {
        localPassengers.infants = Math.max(0, Math.min(count, localPassengers.adults));
      }
    };
    
    // 確認選擇
    const handleConfirm = () => {
      emit('confirm', {
        passengers: { ...localPassengers },
        cabinClass: localCabinClass.value
      });
    };
    
    return {
      isVisible,
      localPassengers,
      localCabinClass,
      cabinOptions,
      updatePassengerCount,
      handleConfirm
    };
  }
};
</script>

<style scoped>
/* === Modal覆蓋層 === */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

/* === Modal內容 === */
.modal-content {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  width: 100%;
  max-width: 500px;
  padding: 2rem;
  transform: scale(1);
  transition: all 0.3s ease;
}

/* === Modal標題 === */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.close-btn {
  width: 2rem;
  height: 2rem;
  border: none;
  background: #f3f4f6;
  border-radius: 50%;
  font-size: 1.25rem;
  color: #6b7280;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

/* === 乘客選擇區域 === */
.passengers-section {
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.passenger-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.passenger-row:last-child {
  border-bottom: none;
}

.passenger-info {
  flex: 1;
}

.passenger-type {
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.25rem;
}

.passenger-desc {
  font-size: 0.875rem;
  color: #6b7280;
}

.counter-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.counter-btn {
  width: 2rem;
  height: 2rem;
  border: 1px solid #d1d5db;
  background: white;
  border-radius: 50%;
  font-size: 1.125rem;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.counter-btn:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #9ca3af;
}

.counter-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.counter-value {
  font-weight: 500;
  color: #374151;
  min-width: 2rem;
  text-align: center;
}

/* === 艙等選擇區域 === */
.cabin-section {
  margin-bottom: 2rem;
}

.cabin-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.cabin-option {
  display: flex;
  align-items: center;
  padding: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.cabin-option:hover {
  border-color: #d1d5db;
  background: #f9fafb;
}

.cabin-option.active {
  border-color: #059669;
  background: #ecfdf5;
}

.cabin-radio {
  margin-right: 0.75rem;
  accent-color: #059669;
}

.cabin-info {
  flex: 1;
}

.cabin-name {
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.25rem;
}

.cabin-desc {
  font-size: 0.875rem;
  color: #6b7280;
}

/* === 操作按鈕 === */
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.cancel-btn {
  padding: 0.75rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  background: #f3f4f6;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.cancel-btn:hover {
  background: #e5e7eb;
}

.confirm-btn {
  padding: 0.75rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: white;
  background: #059669;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.confirm-btn:hover {
  background: #047857;
}

/* === 響應式設計 === */
@media (max-width: 640px) {
  .modal-overlay {
    padding: 0.5rem;
  }
  
  .modal-content {
    padding: 1.5rem;
  }
  
  .passenger-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .counter-controls {
    align-self: flex-end;
  }
}
</style> 