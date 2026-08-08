import os
import time

TASK_FILE = "TASK_QUEUE.md"

def trigger_human_alert(action_text):
    print("\a")  # Bip sesi uyarısı
    print("\033[91m" + "=" * 85)
    print("🚨🚨🚨 İNSAN MÜDAHALESİ GEREKLİ / HUMAN IN THE LOOP REQUIRED 🚨🚨🚨")
    print("=" * 85)
    print(f"👉 GÖREV DETAYI : {action_text}")
    print("👉 DURUM        : Yazılım Otomasyonu Donduruldu.")
    print("👉 AÇIKLAMA     : Claude 1 (Mimar) senin yapman gereken bir manuel veri")
    print("                  seti veya donanım adımı tespit etti.")
    print("=" * 85 + "\033[0m")
    
    input("\n>>> Eylemi (Veri yükleme / Etiketleme / Donanım) tamamladıktan sonra ENTER'a basın...")
    print("\033[92m[OK] Müdahale onaylandı. Otomasyon akışı devam ediyor...\033[0m\n")

def check_task_queue():
    if not os.path.exists(TASK_FILE):
        return

    with open(TASK_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated_lines = []
    task_modified = False

    for line in lines:
        if "[REQUIRES_HUMAN:" in line and "[HUMAN_COMPLETED]" not in line:
            start = line.find("[REQUIRES_HUMAN:") + 16
            end = line.find("]", start)
            action_text = line[start:end]
            
            trigger_human_alert(action_text)
            
            line = line.replace(f"[REQUIRES_HUMAN:{action_text}]", f"[HUMAN_COMPLETED: {action_text}]")
            task_modified = True
            
        updated_lines.append(line)

    if task_modified:
        with open(TASK_FILE, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)

def run_orchestrator():
    print("🤖 Navitas Multi-AI Otomasyon Motoru Başlatıldı...")
    while True:
        check_task_queue()
        time.sleep(2)

if __name__ == "__main__":
    run_orchestrator()