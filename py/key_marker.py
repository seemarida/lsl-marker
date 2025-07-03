"""This file allows you to send LSL markers through keyboard input.
It uses the `pynput` library to listen for keyboard events and the `pylsl` library to send markers.
Make sure to install these libraries if you haven't already:   
pip install pynput pylsl
"""

from pylsl import StreamInfo, StreamOutlet
from time import sleep
from pynput import keyboard

def main():
    """Send event markers based on keyboard input."""
    # set up LSL steam
    info = StreamInfo(name='DataSyncMarker', type='Tags', channel_count=1,
                      channel_format='string', source_id='12345')
    outlet = StreamOutlet(info)  # Broadcast the stream.

    # This is not necessary but can be useful to keep track of markers and the
    # events they correspond to.
    markers = {
        'x': ["Test"],
        's': ["ClassStarted"],
        'a': ["NewActivity"],
        'e': ["ClassEnded"],
        'b': ["BreakStartedEnded"]
    }
    
    print("Set up complete.")
    print("\nPress keys to send markers (ESC to exit):")

     # Keyboard Controls
    print("\nKeyboard Controls:")
    print("x - test marker")
    print("s - class started")
    print("a - new activity")
    print("b - break started/ended")
    print("e - class ended")
    print("ESC - quit")
    
    def on_key_press(key):
        try:
            # Handle alphanumeric keys
            if hasattr(key, 'char') and key.char and key.char.lower() in markers:
                key_pressed = key.char.lower()
                
                if key_pressed == 'a':
                    # activity - prompt for name
                    print(f"\nKey '{key.char}' pressed - Enter activity name: ", end='', flush=True)
                    activity_name = input()
                    if activity_name.strip():
                        marker = [f"Activity_{activity_name.strip()}"]
                        outlet.push_sample(marker)
                        print(f"Sent marker: {marker[0]}")
                    else:
                        print("No activity name entered, marker not sent.")
                else:
                    # regular markers for other keys
                    marker = markers[key_pressed]
                    outlet.push_sample(marker)
                    print(f"Sent marker: {marker[0]} (key: {key.char})")
        except AttributeError:
            # ESC key
            if key == keyboard.Key.esc:
                print("\nExiting...")
                return False
        except Exception as e:
            print(f"Error processing key: {e}")
    
    def on_key_release(key):
        # exit on ESC key release as well
        if key == keyboard.Key.esc:
            return False
    
    # keyboard listener setup
    try:
        with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as listener:
            listener.join()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"Error with keyboard listener: {e}")

if __name__ == "__main__":
    main()