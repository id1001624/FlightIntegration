<template>
  <div class="form-control" :class="{ 'has-error': error }">
    <label v-if="label" 
           :for="id" 
           class="form-label" 
           :class="{ 'form-label-animated': value || focused }">
      {{ label }}
      <span v-if="required" class="required-indicator">*</span>
    </label>
    
    <div class="input-container" :class="{ focused }">
      <div v-if="icon" class="input-icon">
        <slot name="icon">
          <!-- 預設圖標插槽 -->
        </slot>
      </div>
      
      <input
        :id="id"
        :type="type"
        :value="value"
        :placeholder="focused ? placeholder : ''"
        :required="required"
        :disabled="disabled"
        :autocomplete="autocomplete"
        :aria-invalid="!!error"
        :aria-describedby="error ? `${id}-error` : null"
        class="form-input"
        @input="$emit('update:modelValue', $event.target.value)"
        @focus="onFocus"
        @blur="onBlur"
      />
      
      <div v-if="hasClearable && value" class="input-clear" @click="clearInput">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="clear-icon">
          <path fill-rule="evenodd" d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25zm-1.72 6.97a.75.75 0 10-1.06 1.06L10.94 12l-1.72 1.72a.75.75 0 101.06 1.06L12 13.06l1.72 1.72a.75.75 0 101.06-1.06L13.06 12l1.72-1.72a.75.75 0 10-1.06-1.06L12 10.94l-1.72-1.72z" clip-rule="evenodd" />
        </svg>
      </div>
    </div>
    
    <transition name="fade">
      <p v-if="error" :id="`${id}-error`" class="input-error">{{ error }}</p>
    </transition>
    
    <p v-if="hint && !error" class="input-hint">{{ hint }}</p>
  </div>
</template>

<script>
import { ref, computed } from 'vue';

export default {
  name: 'FormInput',
  props: {
    id: {
      type: String,
      required: true
    },
    modelValue: {
      type: [String, Number],
      default: ''
    },
    label: {
      type: String,
      default: ''
    },
    placeholder: {
      type: String,
      default: ''
    },
    type: {
      type: String,
      default: 'text'
    },
    required: {
      type: Boolean,
      default: false
    },
    disabled: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: ''
    },
    hint: {
      type: String,
      default: ''
    },
    clearable: {
      type: Boolean,
      default: false
    },
    icon: {
      type: Boolean,
      default: false
    },
    autocomplete: {
      type: String,
      default: 'off'
    }
  },
  emits: ['update:modelValue', 'focus', 'blur', 'clear'],
  setup(props, { emit }) {
    const focused = ref(false);
    
    const value = computed(() => props.modelValue);
    
    const hasClearable = computed(() => props.clearable && !props.disabled);
    
    const onFocus = () => {
      focused.value = true;
      emit('focus');
    };
    
    const onBlur = () => {
      focused.value = false;
      emit('blur');
    };
    
    const clearInput = () => {
      emit('update:modelValue', '');
      emit('clear');
    };
    
    return {
      focused,
      value,
      hasClearable,
      onFocus,
      onBlur,
      clearInput
    };
  }
}
</script>

<style scoped>
.form-control {
  position: relative;
  margin-bottom: 1.25rem;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary, #6C757D);
  margin-bottom: 0.5rem;
  transition: all var(--transition-fast, 150ms) ease-in-out;
}

.form-label-animated {
  color: var(--color-primary, #005F73);
  font-size: 0.75rem;
  transform: translateY(-0.25rem);
}

.required-indicator {
  color: var(--color-danger, #DC2F02);
  margin-left: 0.125rem;
}

.input-container {
  position: relative;
  display: flex;
  align-items: center;
  border: 1px solid var(--color-border, #DEE2E6);
  border-radius: var(--radius-md, 0.5rem);
  background-color: var(--color-base, #FFFFFF);
  transition: all var(--transition-fast, 150ms) ease-in-out;
}

.input-container:hover {
  border-color: var(--color-primary-light, #0A9396);
}

.input-container.focused {
  border-color: var(--color-primary, #005F73);
  box-shadow: 0 0 0 3px rgba(0, 95, 115, 0.1);
}

.form-input {
  flex: 1;
  width: 100%;
  padding: 0.75rem 1rem;
  background: transparent;
  border: none;
  outline: none;
  font-size: 1rem;
  color: var(--color-text-primary, #212529);
  font-family: inherit;
}

.form-input::placeholder {
  color: var(--color-text-muted, #ADB5BD);
  opacity: 1;
}

.form-input:disabled {
  background-color: var(--color-gray-100, #F8F9FA);
  cursor: not-allowed;
  opacity: 0.7;
}

.input-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-left: 1rem;
  color: var(--color-text-secondary, #6C757D);
}

.input-clear {
  padding-right: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--color-text-muted, #ADB5BD);
  transition: color var(--transition-fast, 150ms) ease-in-out;
}

.input-clear:hover {
  color: var(--color-danger, #DC2F02);
}

.clear-icon {
  width: 1.25rem;
  height: 1.25rem;
}

.input-error {
  margin-top: 0.375rem;
  font-size: 0.75rem;
  color: var(--color-danger, #DC2F02);
}

.input-hint {
  margin-top: 0.375rem;
  font-size: 0.75rem;
  color: var(--color-text-secondary, #6C757D);
}

/* 動畫 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-fast, 150ms) ease-in-out;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.has-error .input-container {
  border-color: var(--color-danger, #DC2F02);
}
</style>