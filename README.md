Smart Patient Monitoring & Fall Detection System (INF 208)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
Dieses Repository enthält den Quellcode und die Simulationsumgebung für das Projekt "Intelligentes Patientenüberwachungs- und Sturzerkennungssystem" im Rahmen des Kurses INF 208: Eingebettete und Cyber-Physische Systeme an der Türkisch-Deutschen Universität (TDU).
🚀 Features (Modellierung & Simulation)
Formal Models: Implemented StateCharts for reactive behavior and Petri-Nets (via Mutex locks) for shared memory concurrency.
Real-Time OS (RTOS) Simulation: Priority-based task scheduling (Rate Monotonic) using Python's `simpy` framework. Implements Priority Inheritance Protocol to avoid deadlocks.
Edge AI Vision (Bonus): Integrated OpenCV-based background subtraction and bounding box ratio analysis for real-time fall detection.
Energy & Thermal Analysis: Theoretical evaluation of dynamic CMOS power and RC thermal models (see PDF Report).
🛠️ Setup & Installation
```bash
# Clone the repository
git clone [https://github.com/yourusername/INF208_SmartPatient_CPS.git](https://github.com/yourusername/INF208_SmartPatient_CPS.git)
cd INF208_SmartPatient_CPS

# Install dependencies
pip install simpy opencv-python numpy

# Run the simulation
python main.py
