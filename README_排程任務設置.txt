===== 航班資料自動更新排程任務設置說明 =====

為了確保每天早上2:30自動更新航班資料，請按照以下步驟設置Windows排程任務：

【方法一：使用PowerShell腳本】

1. 右鍵點擊「setup_task.ps1」文件，選擇「以管理員身份運行 PowerShell」
2. 如果出現安全警告，輸入「Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass」並按Enter
3. 執行「.\setup_task.ps1」命令
4. 確認任務創建成功

【方法二：手動設置】

1. 按下Windows鍵 + R，輸入「taskschd.msc」並按Enter，打開「工作排程器」
2. 在右側面板中點擊「創建基本任務」
3. 輸入名稱「FlightDataUpdate」，點擊「下一步」
4. 選擇「每天」，點擊「下一步」
5. 設置「開始時間」為「02:30:00」，點擊「下一步」
6. 選擇「啟動程序」，點擊「下一步」
7. 在「程序/腳本」中輸入：
   C:\Users\Aliothouo\OneDrive\文件\學校\AlphaVision\FlightIntegration\update_with_timeout.bat
8. 點擊「完成」

【驗證任務】

設置完成後，您可以在「工作排程器」中找到並右鍵點擊「FlightDataUpdate」任務，選擇「運行」來測試。
任務應該會啟動並在執行約10分鐘後自動結束。

【注意事項】

* 此任務配置為運行10分鐘後強制終止所有Python進程，以確保腳本不會無限運行。
* 如果您的計算機在凌晨2:30關機，任務將在下次計算機開機時自動運行（已設置「StartWhenAvailable」選項）。
* 批處理文件已設置為獲取2025-04-07日期的航班數據。如需更改日期，請編輯update_with_timeout.bat文件。