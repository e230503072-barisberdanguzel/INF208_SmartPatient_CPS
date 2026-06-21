import simpy
import cv2
import numpy as np
import threading
import time
import random

# --- 1. STATECHARTS MODELLEMESİ (Rapor Bölüm 2.1) ---
class SystemState:
    IDLE_NORMAL = "IDLE_NORMAL"
    MONITORING_ACTIVE = "MONITORING_ACTIVE"
    EMERGENCY_ALERT = "EMERGENCY_ALERT"

# Global Sistem Durumu
current_state = SystemState.IDLE_NORMAL
fall_detected_flag = False
heart_rate = 75

# --- 2. PETRI NET & PAYLAŞILAN KAYNAK (Rapor Bölüm 2.2) ---
# Paylaşılan I2C/SPI veri yolu için Mutex (Token = 1)
# Öncelik tersinmesini (Priority Inversion) engellemek için PriorityResource kullanıyoruz.
class CyberPhysicalSystem:
    def __init__(self, env):
        self.env = env
        self.bus_mutex = simpy.PriorityResource(env, capacity=1)
        self.shared_memory = {"vitals": 75, "fall_status": False}

# --- 3. RTOS GÖREVLERİ (Rapor Bölüm 4) ---

def task_sensor_ecg(env, cps):
    """TASK 1: Yüksek Öncelikli EKG/Nabız Sensörü (RM: 4ms periyot simülasyonu)"""
    global current_state, heart_rate
    while True:
        # Nyquist teoremine uygun örnekleme simülasyonu
        heart_rate = random.randint(60, 100)
        
        if heart_rate > 150 or heart_rate < 40:
            current_state = SystemState.EMERGENCY_ALERT
            print(f"[{env.now:.1f}s] [ALARM] Kritik Nabız: {heart_rate} bpm!")

        # Mutex isteği (Öncelik: 1 - En yüksek)
        with cps.bus_mutex.request(priority=1) as req:
            yield req
            cps.shared_memory["vitals"] = heart_rate
            
        yield env.timeout(0.5) # Simüle edilmiş gecikme

def task_telemetry(env, cps):
    """TASK 3: Düşük Öncelikli Telemetri Görevi"""
    global current_state
    while True:
        # Mutex isteği (Öncelik: 3 - En düşük)
        with cps.bus_mutex.request(priority=3) as req:
            yield req
            vitals = cps.shared_memory["vitals"]
            fall = cps.shared_memory["fall_status"]
            print(f"[{env.now:.1f}s] [TELEMETRİ] Durum: {current_state} | Nabız: {vitals} | Düşme: {fall}")
            
        yield env.timeout(2.0)

# --- 4. GÖRÜNTÜ İŞLEME VE KAMERA BONUSU (Rapor Bölüm 3.2) ---
def opencv_vision_thread(cps):
    """Kamera modülü ayrı bir thread olarak çalışır, SoC üzerindeki Edge AI donanımını simüle eder."""
    global current_state, fall_detected_flag
    
    cap = cv2.VideoCapture(0) # Web kamerasını aç
    fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)
    
    print("[SYSTEM] Kamera modülü başlatıldı. OpenCV devrede...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame = cv2.resize(frame, (640, 480))
        fgmask = fgbg.apply(frame)
        
        # Gürültü azaltma (Filtreleme simülasyonu)
        fgmask = cv2.erode(fgmask, None, iterations=2)
        fgmask = cv2.dilate(fgmask, None, iterations=2)
        
        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) > 5000: # Sadece büyük nesneleri (insan) takip et
                motion_detected = True
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Sturz (Düşme) Algoritması: Bounding Box genişliği yüksekliğinden büyükse (Yatay pozisyon)
                if w > h * 1.5:
                    fall_detected_flag = True
                    cv2.putText(frame, "STURZ ERKANNT! (FALL DETECTED)", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 3)
                    cps.shared_memory["fall_status"] = True
                    current_state = SystemState.EMERGENCY_ALERT

        # Durum Makinesi Geçişleri (StateChart)
        if motion_detected and current_state == SystemState.IDLE_NORMAL:
            current_state = SystemState.MONITORING_ACTIVE
            
        if not motion_detected and current_state == SystemState.MONITORING_ACTIVE:
            current_state = SystemState.IDLE_NORMAL

        # Ekranda Durumu Göster
        cv2.putText(frame, f"State: {current_state}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        cv2.putText(frame, f"Pulse: {heart_rate} bpm", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        cv2.imshow('Smart Patient Monitoring - Edge AI', frame)
        
        if cv2.waitKey(30) & 0xFF == 27: # ESC tuşu ile çıkış
            break

    cap.release()
    cv2.destroyAllWindows()
    # Programı kapatmak için ortamı sonlandır
    import os
    os._exit(0)

# --- 5. SİSTEMİ BAŞLATMA ---
if __name__ == "__main__":
    env = simpy.Environment()
    system = CyberPhysicalSystem(env)
    
    # RTOS Görevlerini Zamanlayıcıya Ekle
    env.process(task_sensor_ecg(env, system))
    env.process(task_telemetry(env, system))
    
    # OpenCV Kamera İşlemini Ayrı Bir İşlemci Çekirdeğinde (Thread) Çalıştır
    vision_thread = threading.Thread(target=opencv_vision_thread, args=(system,))
    vision_thread.start()
    
    print("[SYSTEM] RTOS Zamanlayıcı başlatıldı...")
    env.run(until=100) # 100 saniye simüle et