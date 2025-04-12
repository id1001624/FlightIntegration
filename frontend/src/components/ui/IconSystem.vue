<template>
  <svg
    :width="size"
    :height="size"
    :viewBox="viewBox"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    :aria-labelledby="name ? `${uid}-title` : undefined"
    :aria-hidden="!name"
    role="img"
    :class="['icon', iconClass]"
  >
    <title v-if="name" :id="`${uid}-title`">{{ name }}</title>
    
    <!-- 航班相關圖標 -->
    <path v-if="icon === 'airplane'" 
          fill-rule="evenodd" 
          clip-rule="evenodd" 
          :fill="color" 
          d="M3.64 14.26l2.86.72 4.5-4.5L19.98 9 21 11.5l-8.63 5.57-4.85 7.5L5 20.5l3.64-6.24zm16.08-11.5c.17-.74-.32-1.22-.99-1.22a1.7 1.7 0 0 0-1.05.42l-9.97 9.97-4.76-1.24S1.96 10.7 2 11.06c.04.37.23.7.57.91l3.7 2.29 2.29 3.7c.21.34.54.53.91.57.38.05.7-.22.7-.22l-1.24-4.76 9.97-9.97c.4-.39.56-.92.42-1.5.06-.14.09-.28.09-.42.01-.23-.04-.44-.14-.62z" />
    
    <path v-else-if="icon === 'departure'" 
          fill-rule="evenodd" 
          clip-rule="evenodd" 
          :fill="color" 
          d="M2.5 19h19v2h-19v-2Zm16.84-4.18-1.91-1.91 1.91-1.91 1.06 1.06-0.85 0.85 0.85 0.85-1.06 1.06Zm-13.59-3.82 2.91-2.87 7.79 7.79-2.91 2.87-7.79-7.79Zm3.54-4.54-1.41-1.41 9.19 9.19 1.41 1.41-9.19-9.19Z" />
    
    <path v-else-if="icon === 'arrival'" 
          fill-rule="evenodd" 
          clip-rule="evenodd" 
          :fill="color" 
          d="M2.5 19h19v2h-19v-2Zm7.18-5.84 1.91 1.91-1.91 1.91-1.06-1.06 0.85-0.85-0.85-0.85 1.06-1.06Zm12.09-5.09L19.6 5.91l-7.79 7.79 2.17 2.17 7.79-7.79Zm-14.08 0L9.86 5.91 17.65 13.7l-2.17 2.17-7.79-7.79Z" />
    
    <path v-else-if="icon === 'calendar'" 
          fill-rule="evenodd" 
          clip-rule="evenodd" 
          :fill="color" 
          d="M7 11h2v2H7v-2Zm0 4h2v2H7v-2Zm4-4h2v2h-2v-2Zm0 4h2v2h-2v-2Zm4-4h2v2h-2v-2Zm0 4h2v2h-2v-2Z M5 22h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-2V2h-2v2H9V2H7v2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2Zm14-2H5V9h14v11Zm0-13H5V6h14v1Z" />
    
    <!-- 搜索、篩選相關圖標 -->
    <path v-else-if="icon === 'search'" 
          fill-rule="evenodd" 
          clip-rule="evenodd" 
          :fill="color" 
          d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" />
    
    <path v-else-if="icon === 'filter'" 
          fill-rule="evenodd" 
          clip-rule="evenodd" 
          :fill="color" 
          d="M10 18h4v-2h-4v2zM3 6v2h18V6H3zm3 7h12v-2H6v2z" />
    
    <path v-else-if="icon === 'sort'" 
          fill-rule="evenodd" 
          clip-rule="evenodd" 
          :fill="color" 
          d="M3 18h6v-2H3v2zM3 6v2h18V6H3zm0 7h12v-2H3v2z" />
    
    <!-- 箭頭圖標 -->
    <path v-else-if="icon === 'arrow-right'" 
          fill-rule="evenodd" 
          clip-rule="evenodd" 
          :fill="color" 
          d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8-8-8z" />
    
    <path v-else-if="icon === 'arrow-left'" 
          fill-rule="evenodd" 
          clip-rule="evenodd" 
          :fill="color" 
          d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
    
    <path v-else-if="icon === 'chevron-down'" 
          fill-rule="evenodd" 
          clip-rule="evenodd" 
          :fill="color" 
          d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z" />
    
    <!-- 用戶反饋圖標 -->
    <path v-else-if="icon === 'check'" 
          fill-rule="evenodd" 
          clip-rule="evenodd" 
          :fill="color" 
          d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
    
    <path v-else-if="icon === 'error'" 
          fill-rule="evenodd" 
          clip-rule="evenodd" 
          :fill="color" 
          d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
    
    <path v-else-if="icon === 'info'" 
          fill-rule="evenodd" 
          clip-rule="evenodd" 
          :fill="color" 
          d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
    
    <!-- 默認圖標 -->
    <path v-else 
          :fill="color" 
          d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z" />
  </svg>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'IconSystem',
  props: {
    icon: {
      type: String,
      required: true
    },
    size: {
      type: [Number, String],
      default: 24
    },
    color: {
      type: String,
      default: 'currentColor'
    },
    name: {
      type: String,
      default: ''
    },
    customClass: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    // 生成唯一ID
    const uid = computed(() => `icon-${Math.random().toString(36).substr(2, 9)}`);
    
    const viewBox = computed(() => '0 0 24 24');
    
    const iconClass = computed(() => {
      const classes = [`icon-${props.icon}`];
      if (props.customClass) {
        classes.push(props.customClass);
      }
      return classes.join(' ');
    });
    
    return {
      uid,
      viewBox,
      iconClass
    };
  }
}
</script>

<style scoped>
.icon {
  display: inline-block;
  flex-shrink: 0;
  vertical-align: middle;
  transition: transform var(--transition-fast, 150ms) ease;
}
</style>