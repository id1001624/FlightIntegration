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

#### 3.3.1 旅程路徑加載動畫
- **標準旅程路徑加載動畫**:
```html
<div class="journey-loader">
  <div class="journey-track"></div>
  <div class="journey-plane"></div>
</div>
```

```css
.journey-loader {
  position: relative;
  width: 100%;
  height: 2px;
  overflow: hidden;
}

.journey-track {
  position: absolute;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, rgba(0,95,115,0.1) 0%, rgba(0,95,115,0.05) 100%);
  border-radius: 1px;
}

.journey-plane {
  position: absolute;
  width: 12px;
  height: 12px;
  background-color: #005F73;
  transform: translateY(-5px) rotate(45deg);
  animation: journey-flight 2s infinite ease-in-out;
}

@keyframes journey-flight {
  0% {
    left: -12px;
    box-shadow: 0 0 0 rgba(0,95,115,0);
  }
  50% {
    box-shadow: 0 0 10px rgba(0,95,115,0.3);
  }
  100% {
    left: 100%;
    box-shadow: 0 0 0 rgba(0,95,115,0);
  }
}
```

#### 3.3.2 路徑軌跡加載動畫
- **路徑擴展動畫**:
```html
<div class="path-loader">
  <div class="path-track"></div>
  <div class="path-progress"></div>
  <div class="path-dots">
    <span class="path-dot"></span>
    <span class="path-dot"></span>
  </div>
</div>
```

```css
.path-loader {
  position: relative;
  width: 100%;
  height: 4px;
  margin: 12px 0;
}

.path-track {
  position: absolute;
  width: 100%;
  height: 2px;
  top: 1px;
  background-color: rgba(0,95,115,0.1);
  border-radius: 1px;
}

.path-progress {
  position: absolute;
  width: 0%;
  height: 2px;
  top: 1px;
  background-color: #005F73;
  border-radius: 1px;
  animation: path-expand 2.2s infinite ease-in-out;
}

.path-dots {
  position: absolute;
  width: 100%;
  display: flex;
  justify-content: space-between;
}

.path-dot {
  width: 6px;
  height: 6px;
  background-color: #F4A261;
  border-radius: 50%;
  transform: translateY(-1px);
}

@keyframes path-expand {
  0% { width: 0%; }
  50% { width: 100%; }
  100% { width: 0%; }
}
```

- **尺寸變體**:
  - 小型: `.journey-loader-sm` 或 `.path-loader-sm` (元素內嵌使用)
  - 中型: `.journey-loader-md` 或 `.path-loader-md` (區域級別使用)
  - 大型: `.journey-loader-lg` 或 `.path-loader-lg` (頁面級別使用)

#### 3.3.3 點脈衝加載動畫
- **簡約點陣列脈衝動畫**:
```html
<div class="dots-loader">
  <span class="dot"></span>
  <span class="dot"></span>
  <span class="dot"></span>
</div>
```

```css
.dots-loader {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.dots-loader .dot {
  width: 6px;
  height: 6px;
  background-color: #005F73;
  border-radius: 50%;
  opacity: 0.6;
}

.dots-loader .dot:nth-child(1) {
  animation: dot-pulse 1.4s infinite ease-in-out;
}

.dots-loader .dot:nth-child(2) {
  animation: dot-pulse 1.4s infinite ease-in-out .2s;
}

.dots-loader .dot:nth-child(3) {
  animation: dot-pulse 1.4s infinite ease-in-out .4s;
}

@keyframes dot-pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.6;
  }
  50% {
    transform: scale(1.5);
    opacity: 1;
  }
}
```

#### 3.3.4 雲層穿越加載動畫
- **雲層穿越加載動畫**:
```html
<div class="clouds-loader">
  <div class="cloud"></div>
  <div class="cloud"></div>
  <div class="cloud"></div>
  <div class="plane-icon">
    <svg viewBox="0 0 24 24" width="100%" height="100%" fill="currentColor">
      <path d="M21,16V14L13,9V3.5A1.5,1.5,0,0,0,11.5,2h0A1.5,1.5,0,0,0,10,3.5V9L2,14V16L10,13.5V19L8,20.5V22L11.5,21L15,22V20.5L13,19V13.5Z" />
    </svg>
  </div>
</div>
```

```css
.clouds-loader {
  position: relative;
  width: 280px;
  height: 60px;
  margin: 0 auto;
  overflow: hidden;
}

.cloud {
  position: absolute;
  width: 60px;
  height: 20px;
  background-color: rgba(248, 249, 250, 0.9);
  border-radius: 20px;
}

.cloud:before, .cloud:after {
  content: '';
  position: absolute;
  background-color: rgba(248, 249, 250, 0.9);
  border-radius: 50%;
}

.cloud:before {
  width: 30px;
  height: 30px;
  top: -15px;
  left: 10px;
}

.cloud:after {
  width: 20px;
  height: 20px;
  top: -10px;
  left: 35px;
}

.cloud:nth-child(1) {
  top: 10px;
  left: -60px;
  opacity: 0.7;
  animation: cloud-move 3.5s infinite linear;
}

.cloud:nth-child(2) {
  top: 25px;
  left: -60px;
  opacity: 0.9;
  animation: cloud-move 3s infinite 1s linear;
}

.cloud:nth-child(3) {
  top: 40px;
  left: -60px;
  opacity: 0.6;
  animation: cloud-move 4s infinite 0.5s linear;
}

.plane-icon {
  position: absolute;
  width: 30px;
  height: 30px;
  left: 50%;
  top: 15px;
  transform: translateX(-50%);
  z-index: 10;
  color: #005F73;
}

@keyframes cloud-move {
  0% { left: -60px; }
  100% { left: 100%; }
}
```

- **尺寸變體**:
  - 小型: `.clouds-loader-sm` (元素內嵌使用)
  - 中型: `.clouds-loader-md` (區域級別使用)
  - 大型: `.clouds-loader-lg` (頁面級別使用)

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