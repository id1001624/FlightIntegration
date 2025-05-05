# 台灣航班整合系統 - 視覺設計標準

本文檔定義了台灣航班整合系統的視覺設計標準，確保整個應用程序的一致性和專業性。

## 1. 色彩系統

### 1.1 主色調

- **基礎色**: `#FFFFFF` (白色)
- **背景色**: `#F8F9FA` (淺灰背景)
- **主要強調色**: 
  - `#005F73` (主色調，海藍色)
  - `#0A9396` (淺海藍色)
  - `#033F4D` (深海藍色)
- **次強調色**:
  - `#F4A261` (橙色)
  - `#F8BC8A` (淺橙色)
  - `#E07A38` (深橙色)

### 1.2 功能色彩

- **成功**: `#38B000` (綠色)
- **警告**: `#FFB703` (黃色)
- **危險**: `#DC2F02` (紅色)
- **信息**: `#219EBC` (藍色)

### 1.3 中性色

- **邊框**: `#DEE2E6` (灰色)
- **文字**:
  - 主要: `#212529` (深灰)
  - 次要: `#6C757D` (中灰)
  - 柔和: `#ADB5BD` (淺灰)

## 2. 排版

### 2.1 字體族

```css
font-family: 'Inter', 'Noto Sans TC', 'system-ui', 'sans-serif';
```

### 2.2 字體大小層級

- **標題一**: `text-3xl` (1.875rem)
- **標題二**: `text-2xl` (1.5rem)
- **標題三**: `text-xl` (1.25rem)
- **正文**: `text-base` (1rem)
- **小字**: `text-sm` (0.875rem)
- **極小字**: `text-xs` (0.75rem)

### 2.3 字重

- **粗體**:  `font-bold` (700)
- **中粗體**: `font-semibold` (600)
- **標準體**: `font-medium` (500)
- **常規**: `font-normal` (400)

## 3. 元素風格

### 3.1 按鈕

- **主要按鈕**: `bg-primary text-white`
- **次要按鈕**: `bg-white text-primary border border-primary`
- **警告按鈕**: `bg-warning text-white`
- **危險按鈕**: `bg-danger text-white`
- **按鈕形狀**: 方形設計 (`border-radius: 0`)

### 3.2 輸入框

- **基本樣式**: `border border-gray-300 focus:border-primary focus:outline-none`
- **錯誤狀態**: `border-red-500`
- **禁用狀態**: `opacity-50 cursor-not-allowed`
- **輸入框形狀**: 方形設計 (`border-radius: 0`)

### 3.3 加載動畫

- **標準 SVG 加載動畫**:
```html
<svg class="animate-spin h-4 w-4 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
</svg>
```

- **尺寸變體**:
  - 小型: `h-4 w-4` (元素內嵌使用)
  - 中型: `h-8 w-8` (區域級別使用)
  - 大型: `h-12 w-12` (頁面級別使用)

### 3.4 卡片

- **基本樣式**: `bg-white shadow-card rounded-lg p-6 border border-gray-200`
- **懸停效果**: `shadow-card-hover`
- **動畫過渡**: `transition duration-200`

## 4. 交互設計

### 4.1 懸停效果

- **按鈕懸停**: `hover:bg-primary-dark` (主按鈕)
- **列表項懸停**: `hover:bg-primary hover:bg-opacity-10`
- **圖標懸停**: `hover:text-primary`

### 4.2 選中狀態

- **標準選中**: `bg-primary bg-opacity-20`
- **強調選中**: `bg-primary text-white`

### 4.3 過渡效果

- **默認過渡**: `transition-all duration-200 ease-in-out`
- **慢速過渡**: `transition-all duration-300 ease-in-out`
- **漸入效果**: `animate-fade-in` (自定義動畫)
- **上滑效果**: `animate-slide-up` (自定義動畫)

## 5. 響應式設計

### 5.1 斷點

- **手機**: `sm` (640px)
- **平板**: `md` (768px)
- **筆記本**: `lg` (1024px)
- **桌面**: `xl` (1280px)
- **大屏**: `2xl` (1536px)

### 5.2 容器最大寬度

- **內容區域**: `max-w-7xl` (1280px)
- **內容寬度**: `w-full`
- **間距**: `px-4 md:px-6 lg:px-8`

## 6. 佈局規範

### 6.1 間距系統

- **項目間距**: `space-y-4` (垂直) 或 `space-x-4` (水平)
- **內部間距**: `p-6` (均等) 或 `px-4 py-2` (不均等)
- **外部間距**: `m-4` (均等) 或 `mt-4 mb-6` (不均等)

### 6.2 網格系統

- **基本網格**: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6`
- **不均等網格**: `grid grid-cols-3` 與 `col-span-2` 結合使用

### 6.3 Flex 佈局

- **基本 Flex**: `flex items-center`
- **平均分布**: `flex justify-between`
- **居中對齊**: `flex justify-center items-center`
- **垂直堆疊**: `flex flex-col`

## 7. 圖標與圖像

### 7.1 圖標

- **大小規範**:
  - 小型: `h-4 w-4`
  - 中型: `h-6 w-6`
  - 大型: `h-8 w-8`
- **顏色**: 繼承文字顏色或使用 `text-primary`

### 7.2 圖像

- **圓形圖像**: `rounded-full`
- **方形圖像**: 不添加圓角 (與系統風格一致)
- **縮放處理**: `object-cover` 或 `object-contain`

## 8. 動畫與過渡

### 8.1 自定義動畫

- **漸入**: `animate-fade-in`
- **上滑**: `animate-slide-up`
- **輕脈衝**: `animate-pulse-gentle`
- **漂浮**: `animate-float`
- **旅程線**: `animate-journey-line`

### 8.2 關鍵幀定義

```css
@keyframes fadeIn {
  0% { opacity: 0; }
  100% { opacity: 1; }
}

@keyframes slideUp {
  0% { transform: translateY(20px); opacity: 0; }
  100% { transform: translateY(0); opacity: 1; }
}

@keyframes pulseGentle {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes journeyLine {
  0% { width: 0%; opacity: 0.5; }
  100% { width: 100%; opacity: 1; }
}
```

## 9. 陰影系統

```css
boxShadow: {
  'card': '0 2px 4px rgba(0,0,0,0.05)',
  'card-hover': '0 4px 8px rgba(0,0,0,0.08)',
  'elevation-1': '0 1px 3px rgba(0,0,0,0.05)',
  'elevation-2': '0 4px 6px rgba(0,0,0,0.05)',
  'elevation-3': '0 10px 15px rgba(0,0,0,0.05)',
}
```

## 10. 漸變背景

```css
backgroundImage: {
  'journey-gradient': 'linear-gradient(120deg, #005F73 0%, #0A9396 100%)',
  'warm-gradient': 'linear-gradient(120deg, #F4A261 0%, #E07A38 100%)',
}
```

---

本文檔應與 [專案設計指南](mdc:docs/UI-UX/ui-design-guidelines.mdc) 和 [前端開發指南](mdc:docs/development/frontend-guidelines.mdc) 一起參考，確保所有新開發的元件符合系統的視覺標準。 