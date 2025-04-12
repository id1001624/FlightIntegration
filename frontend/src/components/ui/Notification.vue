<template>
  <div v-if="show" 
       class="notification" 
       :class="type"
       role="alert">
    <div class="notification-content">
      <div class="notification-icon">
        <svg v-if="type === 'success'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="icon">
          <path fill-rule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" clip-rule="evenodd" />
        </svg>
        <svg v-else-if="type === 'error'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="icon">
          <path fill-rule="evenodd" d="M9.401 3.003c1.155-2 4.043-2 5.197 0l7.355 12.748c1.154 2-.29 4.5-2.599 4.5H4.645c-2.309 0-3.752-2.5-2.598-4.5L9.4 3.003zM12 8.25a.75.75 0 01.75.75v3.75a.75.75 0 01-1.5 0V9a.75.75 0 01.75-.75zm0 8.25a.75.75 0 100-1.5.75.75 0 000 1.5z" clip-rule="evenodd" />
        </svg>
        <svg v-else-if="type === 'info'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="icon">
          <path fill-rule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm8.706-1.442c1.146-.573 2.437.463 2.126 1.706l-.709 2.836.042-.02a.75.75 0 01.67 1.34l-.04.022c-1.147.573-2.438-.463-2.127-1.706l.71-2.836-.042.02a.75.75 0 11-.671-1.34l.041-.022zM12 9a.75.75 0 100-1.5.75.75 0 000 1.5z" clip-rule="evenodd" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="icon">
          <path fill-rule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zM12 8.25a.75.75 0 01.75.75v3.75a.75.75 0 01-1.5 0V9a.75.75 0 01.75-.75zm0 8.25a.75.75 0 100-1.5.75.75 0 000 1.5z" clip-rule="evenodd" />
        </svg>
      </div>
      <div class="notification-message">{{ message }}</div>
      <button class="notification-close" @click="onClose" aria-label="關閉">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="icon">
          <path fill-rule="evenodd" d="M5.47 5.47a.75.75 0 011.06 0L12 10.94l5.47-5.47a.75.75 0 111.06 1.06L13.06 12l5.47 5.47a.75.75 0 11-1.06 1.06L12 13.06l-5.47 5.47a.75.75 0 01-1.06-1.06L10.94 12 5.47 6.53a.75.75 0 010-1.06z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Notification',
  props: {
    show: {
      type: Boolean,
      required: true
    },
    message: {
      type: String,
      required: true
    },
    type: {
      type: String,
      default: 'info',
      validator: (value) => ['info', 'success', 'error', 'warning'].includes(value)
    },
    duration: {
      type: Number,
      default: 5000
    }
  },
  emits: ['close'],
  data() {
    return {
      timeout: null
    }
  },
  watch: {
    show(newVal) {
      if (newVal && this.duration > 0) {
        this.setupAutoClose();
      } else {
        this.clearTimeout();
      }
    }
  },
  methods: {
    setupAutoClose() {
      this.clearTimeout();
      this.timeout = setTimeout(() => {
        this.onClose();
      }, this.duration);
    },
    clearTimeout() {
      if (this.timeout) {
        clearTimeout(this.timeout);
        this.timeout = null;
      }
    },
    onClose() {
      this.clearTimeout();
      this.$emit('close');
    }
  },
  mounted() {
    if (this.show && this.duration > 0) {
      this.setupAutoClose();
    }
  },
  beforeUnmount() {
    this.clearTimeout();
  }
}
</script>

<style scoped>
.notification {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 50;
  max-width: 24rem;
  border-radius: var(--radius-md, 0.5rem);
  box-shadow: var(--shadow-lg, 0 10px 15px rgba(0, 0, 0, 0.05));
  opacity: 0;
  transform: translateY(-0.5rem);
  animation: notification-enter var(--transition-normal, 250ms) forwards;
}

.notification-content {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-radius: var(--radius-md, 0.5rem);
}

.notification-icon {
  flex-shrink: 0;
  margin-right: 0.75rem;
}

.icon {
  width: 1.5rem;
  height: 1.5rem;
}

.notification-message {
  flex-grow: 1;
  font-size: 0.875rem;
  line-height: 1.25rem;
  font-weight: 500;
}

.notification-close {
  flex-shrink: 0;
  margin-left: 0.75rem;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity var(--transition-fast, 150ms);
  padding: 0.25rem;
  background: transparent;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: inherit;
}

.notification-close:hover {
  opacity: 1;
}

.notification-close .icon {
  width: 1.25rem;
  height: 1.25rem;
}

/* 類型樣式 */
.success {
  background-color: #ecfdf5;
  color: #064e3b;
  border-left: 4px solid var(--color-success, #38B000);
}

.error {
  background-color: #fef2f2;
  color: #7f1d1d;
  border-left: 4px solid var(--color-danger, #DC2F02);
}

.info {
  background-color: #eff6ff;
  color: #1e40af;
  border-left: 4px solid var(--color-info, #219EBC);
}

.warning {
  background-color: #fffbeb;
  color: #854d0e;
  border-left: 4px solid var(--color-warning, #FFB703);
}

/* 動畫 */
@keyframes notification-enter {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 響應式 */
@media (max-width: 640px) {
  .notification {
    top: 0.5rem;
    right: 0.5rem;
    left: 0.5rem;
    max-width: none;
  }
}
</style>