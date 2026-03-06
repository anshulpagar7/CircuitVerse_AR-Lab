CircuitVerse – AR-Based Virtual Electronics Laboratory

CircuitVerse is an Augmented Reality (AR) based virtual electronics laboratory that helps students visualize and understand electronic circuits interactively. By using ArUco markers and computer vision, the system detects experiments and displays circuit components step-by-step on the screen, making electronics learning more intuitive and engaging.

This project aims to enhance traditional electronics labs by providing real-time circuit visualization, interactive experiment guidance, and modular experiment configuration.

🚀 Features

📷 Real-Time ArUco Marker Detection

🔌 Step-by-Step Circuit Construction Visualization

⚡ Interactive Electronic Component Rendering

📚 Multiple Electronics Experiments

🧠 Conceptual Learning Through Visualization

⚙️ JSON-Based Experiment Configuration

🖥️ Works with Standard Webcam

🧪 Experiments Implemented

Ohm’s Law Verification with Measurement Points

Voltage Divider with Load

RC Circuit – Charging and Discharging with LED

LED Control using Raspberry Pi GPIO

Logic Threshold Demonstration using GPIO

RC Circuit Charging & Discharging

Transistor as a Switch

Threshold / Logic Demonstration Circuit

🧩 Components Supported

Voltage Source / Battery

Resistor

LED

Capacitor

Diode

Transistor

Switch

Ammeter

Voltmeter

Breadboard

Jumper Wires

Ground

Raspberry Pi GPIO

🧠 How It Works

The webcam captures real-time video frames.

OpenCV detects ArUco markers in the video stream.

Each marker ID is mapped to a specific experiment.

Experiment details are loaded from JSON configuration files.

Circuit components are rendered step-by-step.

Green wires display connections between components.

Users navigate experiment steps using keyboard controls.

⚙️ Tech Stack
Programming

Python 3

Computer Vision

OpenCV

OpenCV Contrib (ArUco Module)

Libraries

NumPy

JSON

Tools

Git & GitHub

VS Code

Hardware

Webcam

📂 Project Structure
CircuitVerse/
│
├── python_app/
│   └── ar_main.py
│
├── circuit_engine/
│   ├── loader.py
│   ├── solver.py
│   └── components.py
│
├── experiments/
│   ├── exp1_ohms_law_measurement.json
│   ├── exp2_voltage_divider_load.json
│   ├── exp3_rc_charging_led.json
│   └── ...
│
├── assets/
│   ├── resistor.png
│   ├── led.png
│   ├── capacitor.png
│   └── ...
│
├── markers/
│   └── aruco markers
│
└── README.md
🛠 Installation
1️⃣ Install Python

Recommended version: Python 3.9 – 3.11

2️⃣ Install Required Libraries
pip install opencv-contrib-python numpy
3️⃣ Run the Project
python python_app/ar_main.py
🎮 Controls
Key	Action
N	Next Step
R	Reset Experiment
Q	Quit Program
🎯 Applications

Virtual electronics laboratories

Educational demonstrations

Remote learning environments

Concept visualization for beginners

AR-based engineering education

👨‍🏫 Mentor

Dr. Angayarkanni V

👨‍💻 Developer

Anshul Pagar
B.Tech CSE
SRM Institute of Science and Technology

🌟 Future Improvements

Mobile AR implementation

3D circuit visualization

Web-based AR version

Fault detection in circuits

Real-time current flow animation

📜 License

This project is developed for academic and educational purposes.
