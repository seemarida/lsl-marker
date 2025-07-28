# lsl-marker

This script allows you to send LSL (Lab Streaming Layer) markers through keyboard input to set event markers for EmotiBits or other devices with LSL-integrated functionality.

## Setup Instructions

1. **Connect to EmotiBit Oscilloscope**
2. **Run the script**

    ```bash
    pip install pynput pylsl
    python new_marker_file.py
    ```

3. **Open EmotiBit Oscilloscope**: It will automatically detect available LSL streams.
4. **Select your EmotiBit device in Oscilloscope**  
   - Make sure you select an EmotiBit device each time you record a marker!!!
5. **Start recording**

---

## Adding More Markers

```python
markers = {
    'x': ["Test"],
    'your_key': ["YourMarkerName"],
}
