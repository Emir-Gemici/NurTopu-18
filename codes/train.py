from roboflow import Roboflow
from ultralytics import YOLO

# Dataset indir
rf = Roboflow(api_key="UAKMO48cQ4KPFiQvWdZO")
project = rf.workspace("rubble-project").project("rubble-detection")
dataset = project.version(1).download("yolov8")

# Eğit
model = YOLO('yolov8n.pt')
model.train(
    data=f"{dataset.location}/data.yaml",
    epochs=30,
    imgsz=640,
    batch=8,
    patience=10,
    name='rubble_v1'
)

print("Eğitim bitti!")
print("Model: runs/detect/rubble_v1/weights/best.pt")
