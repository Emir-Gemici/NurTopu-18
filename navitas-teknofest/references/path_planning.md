# Path Planning Referans

## Sistem Mimarisi
- **İHA** (Jetson Orin NX) → görüntü işle → segmentasyon maskesi → İKA'ya gönder
- **İKA** (RPi 5) → maskeyi grid'e dönüştür → A* çalıştır → rota çıkar

---

## Grid Map Üretimi

### Segmentasyon maskesinden occupancy grid
```python
import numpy as np
import cv2

def mask_to_grid(mask: np.ndarray, grid_size: int = 50) -> np.ndarray:
    """
    YOLOv8-seg çıktısını A* için occupancy grid'e dönüştür.
    mask  : binary (H x W), 1 = geçilebilir yol
    return: grid_size x grid_size, 0=geçilebilir 1=engel
    """
    resized = cv2.resize(mask.astype(np.uint8), (grid_size, grid_size),
                         interpolation=cv2.INTER_NEAREST)
    occupancy = 1 - resized   # yol=0, engel=1
    return occupancy
```

### Grid Çözünürlüğü Seçimi
- 50×50m alan → 50×50 grid → her hücre = 1m²  (önerilen başlangıç)
- İHA hızı yüksekse → 25×25 grid (daha hızlı planlama)
- Hassasiyet gerekliyse → 100×100 (A* maliyeti artar)

---

## A* Implementasyonu (RPi 5)

```python
import heapq

def astar(grid: np.ndarray, start: tuple, goal: tuple) -> list:
    """
    grid  : 2D numpy array, 0=free 1=obstacle
    start : (row, col)
    goal  : (row, col)
    return: [(row, col), ...] path veya []
    """
    rows, cols = grid.shape
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}

    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])  # Manhattan

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            return path[::-1]

        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            nr, nc = current[0]+dr, current[1]+dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
                tentative_g = g_score[current] + (1.414 if dr and dc else 1.0)
                neighbor = (nr, nc)
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f, neighbor))
    return []  # yol bulunamadı
```

---

## İHA↔İKA İletişim

### Öneri: UDP Socket (düşük latency)
```python
# İHA tarafı — mask gönder
import socket, pickle, numpy as np

def send_mask(mask: np.ndarray, host='IKA_IP', port=5005):
    data = pickle.dumps(mask)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.sendto(data, (host, port))

# İKA tarafı — mask al
def receive_mask(port=5005) -> np.ndarray:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', port))
        data, _ = s.recvfrom(65535)
    return pickle.loads(data)
```

### Gecikme Bütçesi
- NCNN inference: ~36ms
- Network (UDP lokal): <5ms
- A* (50×50 grid): <10ms
- **Toplam**: ~51ms → ~20Hz güncelleme mümkün

---

## Edge Cases

| Durum | Çözüm |
|-------|-------|
| Yol bulunamadı | Son geçerli rotayı tut, İHA beklet |
| Maske gelmedi | Timeout=100ms → önceki frame kullan |
| Grid tamamen engel | Confidence threshold düşür, tekrar dene |
| Koridor geçiş noktası belirsiz | Ortalama yol koordinatını waypoint al |
