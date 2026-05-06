from ultralytics import YOLO

model = YOLO('runs/detect/rubble_v1/weights/best.pt')

# İnternetten bir moloz fotoğrafı indir, yolunu buraya yaz
results = model('test.jpg', save=True, conf=0.25)

print(f"Tespit sayısı: {len(results[0].boxes)}")
for box in results[0].boxes:
    print(f"  Güven: {box.conf.item():.2f} | Konum: {box.xyxy[0].tolist()}")
