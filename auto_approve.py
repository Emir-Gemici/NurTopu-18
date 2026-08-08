import pyautogui
import time

print("Otomatik onaylayıcı başlatıldı. Durdurmak için terminalde Ctrl+C yapın.")

# VS Code penceresinin sol tarafındaki Continue paneline denk gelen bir koordinat
# Ekran çözünürlüğünüze göre Continue sohbet alanının x, y değeridir
CHAT_PANEL_X = 250  
CHAT_PANEL_Y = 500

while True:
    try:
        # 1. Önce odağı Continue sohbet paneline getir
        pyautogui.click(x=CHAT_PANEL_X, y=CHAT_PANEL_Y)
        time.sleep(0.5)
        
        # 2. Terminal/Komut onay kısayolunu gönder
        pyautogui.hotkey('ctrl', 'enter')
        
        time.sleep(4)
    except KeyboardInterrupt:
        break