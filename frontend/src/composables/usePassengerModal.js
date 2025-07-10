import { ref } from 'vue';

export function usePassengerModal() {
  const isPassengerModalVisible = ref(false);

  const openPassengerModal = () => {
    isPassengerModalVisible.value = true;
  };

  const closePassengerModal = () => {
    isPassengerModalVisible.value = false;
  };

  return {
    isPassengerModalVisible,
    openPassengerModal,
    closePassengerModal,
  };
} 