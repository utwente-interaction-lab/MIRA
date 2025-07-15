# **📘 Project Documentation: Augmented Reality Digital Mirror (MIRA)**

This documentation outlines setup of the system and the important Unity C\# and Python scripts used in the MIRA prototype. Each section includes the script’s purpose, main responsibilities, interaction with other components, and key developer notes. Yes, AI was used to help make this, but everything is correct :)

MORE INFORMATION CAN BE FOUND IN MY [THESIS](https://essay.utwente.nl/106375/)

Good luck\! \-Rens

# 

# 

# **🪞 MIRA System Setup Guide**

---

## **🧰 1\. Hardware Requirements**

Before getting started, make sure you have the following:

* ✅ **PC or Laptop** (Windows recommended, capable of running Unity and Python)  
* ✅ **Screen/Monitor** (preferably portrait, ≥1080p; mirror-sized for ideal UX)  
* ✅ **Webcam**  
  * **Recommended**: 4K webcam (e.g., Newline Modular 4K Camera)  
  * Must support at least 30 FPS  
* ✅ **Distance sensor** (Hooked onto an arduino, sending distance through Serial)

💡 *A high-resolution webcam improves image fidelity in Unity, while a lower-res stream reduces load on Python.*

---

## 

## **🧪 2\. Software Installation**

### **A. OBS (Open Broadcaster Software)**

To split the camera feed into two separate virtual camera streams (for performance reasons):

* 🔽 **Install OBS Studio 27.2.4**  
   [Download link (GitHub)](https://github.com/obsproject/obs-studio/releases/tag/27.2.4)  
   *Later versions **will not work** with the VirtualCam plugin described below.*  
* 🔌 **Install OBS VirtualCam Plugin**  
   [Download OBS-VirtualCam](https://github.com/CatxFish/obs-virtual-cam/releases)  
  * This plugin allows for **a second virtual camera**.

🔁 You will use:

* **OBS's default virtual camera** → sent to **Unity** (high resolution)  
* **VirtualCam plugin output** → sent to **Python** (low resolution)

---

## **🧠 3\. Python Pose Estimation Setup**

### **A. Environment**

Make sure you have Python 3.9 or higher installed. Then install the required packages:

`pip install mediapipe opencv-python numpy tensorflow`

⚠️ Python code runs on **CPU**. GPU implementation is optional and recommended, but not required.

### **B. Configure Python Webcam Feed**

* **Input**: the lower-resolution virtual camera from OBS (e.g., 720p or 1080p).  
* Make sure your device index or `VideoCapture` call points to the correct OBS plugin cam.

---

## **🧱 4\. Unity Project Setup**

### **A. Requirements**

* Unity **2021.x or 2022.x**  
* Open the included Unity project

**B. OBS Input**

* Use the **high-resolution virtual camera** (e.g., 4K) as a texture feed.  
* Assigned via the `ImageDisplay.cs` script in the scene.

## **🚀 5\. System Launch Order**

To avoid timing or socket errors, **follow this order exactly**:

### **✅ Step-by-step**

1. **Launch OBS Studio**  
   * Load the webcam source.  
   * Enable:  
     * `Start Virtual Camera`  
     * `Start VirtualCam Plugin`  
        *(Confirm both virtual cameras are running — check in your video device list.)*

2. **Start Python (`PoseEstimation.py`)**  
   * It will connect to Unity via TCP socket.  
   * Starts listening for client connection and begins pose \+ Arduino streaming.

3. **Run Unity Scene**  
   * Unity connects to the Python socket server.  
   * Begin interaction via the boot → calibration → active states.

---

## **🛠️ Additional Notes & Recommendations**

* 🧪 **Calibration**:  
  * Users must stand at a default position to calibrate head height and distance.  
  * Controlled via `CorrectPerspective.cs`.

* 📡 **Distance Sensor (IMPORTANT)**:  
  * If using an Arduino and VL53L1X ToF sensor, ensure it's connected before launching Python.  
  * This provides stable calibration and scale accuracy.  
  * You can use other distance sensors, but a ToF sensor is recommended. (see thesis linked at the top)

* 🧠 **Performance Tips**:  
  * Reduce Python frame resolution (e.g., 720p) to improve FPS.  
  * Unity's projection logic assumes portrait webcam FOV; flip the camera feed if needed.  
  * For accurate overlays (like stains), keep camera angle consistent (top center is default).

* 🗃️ **OBS Scene Layout**:  
  * Add two sources:  
    * Your physical webcam  
    * A downscaled version (using a filter or transformed duplicate)  
  * Route them to different virtual cams (OBS vs. plugin).

# **🪞 MIRA Logic Overview**

(Almost) All Unity setup should be doable though changing the exposed variables in the inspector, with the notable exception of the FOV scaling (due to prior time constraints).  
---

## **🔁 Core System Controllers**

### **`GameManager.cs`**

**Role**: Controls application state transitions (Booting → Calibrating → Active).

**Responsibilities**:

* Displays the appropriate UI for each game state.  
* Starts boot sequence and handles restart/reset logic.  
* Triggers UnityEvents for calibration (`StartCalibration`) and mirror activation (`StartMirroring`).

**Interacts with**:

* `CorrectPerspective.cs` (calls `OnStateChangeToBooting()` and `OnStateChangeToCalibration()`).  
* `ARAddition.cs` and others read `GameManager.Instance.GameState`.

**Key Notes**:

* Add any logic that must be synchronized with system state changes here.  
* You can register other scripts to the `UnityEvent` hooks for custom transitions.

---

### **`CorrectPerspective.cs`**

**Role**: Simulates a mirror’s camera logic by adjusting Unity’s main camera to follow the user’s position and head angle.

**Responsibilities**:

* Calculates user's head position and vertical viewing angle.  
* Adjusts camera’s `fieldOfView`, `rotation`, and `lookAt` to mimic a real mirror.  
* Handles calibration (both distance and height).  
* Manages distance validation logic for proximity warnings.

**Interacts with**:

* `HandleLandmarks.cs` for eye and mouth landmark data.  
* `HandleDistance.cs` for physical distance values.  
* `GameManager.cs` to respond to state transitions.  
* `CameraPlacement.cs` for calibration offsets.  
* `Logger` for writing session data (position, brightness, etc.)

**Key Notes**:

* Calibration results (like `distanceNullPosition` and `eyesNullDistance`) are used to infer scale and distance in real time.  
* Implements smoothing and adaptive UI feedback for guiding users to the correct position.

---

## **🧠 Data Ingestion**

### **`SocketClient.cs`**

**Role**: TCP client that receives pose landmark data and distance data from Python.

**Responsibilities**:

* Parses pose data into landmark vectors and forwards to `HandleLandmarks`.  
* Parses Arduino ToF distance data and forwards to `HandleDistance`.

**Interacts with**:

* `HandleLandmarks.cs` (`UpdateLandmarks2D/3D`)  
  `HandleDistance.cs` (`SendDistanceData`)

**Key Notes**:

* Handles multiple packet types: Pose only, Arduino only, or combined.  
* Automatically selects between 2D or 3D pose data based on the selected mode.

---

### **`PoseEstimation.py` (Python)**

**Role**: Captures video from a webcam and sends MediaPipe pose data and Arduino distance values over TCP to Unity.

**Responsibilities**:

* Uses MediaPipe to extract 33 pose landmarks.  
* Sends raw data with a prefix to identify packet type (Pose vs Arduino).  
* Runs a separate thread to sample the Arduino sensor via serial.

**Interacts with**:

* Unity via TCP socket (`SocketClient.cs`).  
* Arduino (via serial port, e.g., `/dev/ttyUSB0` or `COMx`).

**Key Notes**:

* High-frequency loop (30Hz for pose, 10Hz for Arduino).  
* You can adjust the resolution for better speed/accuracy trade-off in `cap.set()`.

---

## **🧍 Landmark & Distance Systems**

### **`HandleLandmarks.cs`**

**Role**: Stores and updates landmark positions used for all mirror logic and augmentation.

**Responsibilities**:

* Maintains a normalized list of 2D or 3D landmark positions.  
* Optionally draws lines between specific landmarks for debugging or visual feedback.

**Interacts with**:

* `SocketClient.cs` (updates landmark array).  
* `CorrectPerspective.cs` and `ARAddition.cs` (reads landmarks).  
* `ImageDisplay.cs` (for pixel-based brightness sampling).

**Key Notes**:

* Landmarks are accessed via `landmarkValuesNormalized[index]`.

---

### **`HandleDistance.cs`**

**Role**: Buffers, smooths, and provides user distance data received from the Arduino.

**Responsibilities**:

* Buffers incoming distance readings for noise reduction.  
* Computes lerped distance for smoother use in other scripts.

**Interacts with**:

* `SocketClient.cs` (receives raw data).  
* `CorrectPerspective.cs` (reads smoothed distance).  
* `GameManager.cs` (for user calibration steps).

**Key Notes**:

* `lerpedProcessedDistance` is the most reliable distance variable for logic.

---

## **🧩 Augmentation and AR**

### **`ARAddition.cs`**

**Role**: Projects and animates a virtual object (e.g. stain) onto the user’s body.

**Responsibilities**:

* Computes position and scale of the object from 4 landmark points.  
* Has a basic mode and advanced mode (which includes rotation and dynamic brightness).  
* Adjusts transparency based on viewing angle and brightness.

**Interacts with**:

* `HandleLandmarks.cs` for the body landmarks.  
* `CorrectPerspective.cs` for angle calculations.  
* `GameManager.cs` for checking the current state.  
* `ImageDisplay.cs` for brightness sampling.

**Key Notes**:

* Call `SetAdditionDefaults()` after calibration to lock in scale/rotation nulls.  
* `AddAdditionAdvanced()` handles body rotation, z-depth adjustment, and "stick out" offsets.  
* Use `Logger.Log("Brightness", ...)` to log brightness analysis during user tests.

---

## **🧮 Geometry & Visual Processing**

### **`ProceduralBentPlane.cs`**

**Role**: Generates a curved mesh that matches the camera's FOV to simulate a screen that wraps around the user.

**Responsibilities**:

* Uses `HandleLandmarks.fov` to shape a procedural mesh.  
* Bends plane vertices toward the origin to simulate perspective.

**Interacts with**:

* `HandleLandmarks.cs` (reads FOV, screen dimensions).  
* `ARAddition.cs` references the generated plane for projections.

**Key Notes**:

* This plane gives a spatially-accurate base for projecting the video feed.

---

### **`ImageDisplay.cs`**

**Role**: Manages the webcam feed as a texture and samples pixel brightness.

**Responsibilities**:

* Displays the webcam feed on a material.  
* Samples pixel color using normalized coordinates.

**Interacts with**:

* `ARAddition.cs` (samples brightness of the body area).  
* Unity `Renderer` (mainTexture manipulation).

**Key Notes**:

* Flip image if needed via the `flipImage` flag.  
* `GetPixelColor(float u, float v)` is used for real-time brightness estimation.

---

## **🧾 Configuration & Utilities**

### **`CameraPlacement.cs` (ScriptableObject)**

**Role**: Stores camera placement offsets and FOV settings for `CorrectPerspective.cs`.

**Responsibilities**:

* Offset values for X and Y placement.  
* Angle offset for FOV correction.

**Interacts with**:

* `CorrectPerspective.cs` (accessed via public field `camPlace`).

