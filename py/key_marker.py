"""Minimal example of how to send event triggers in PsychoPy with
LabStreamingLayer.
In this example, the words "hello" and "world" alternate on the terminal, and
an event marker is sent with the appearance of each word.
"""

from pylsl import StreamInfo, StreamOutlet
from time import sleep
from pynput import keyboard

def main():
    """Send event markers based on keyboard input."""
    # Set up LabStreamingLayer stream.
    info = StreamInfo(name='DataSyncMarker', type='Tags', channel_count=1,
                      channel_format='string', source_id='12345')
    outlet = StreamOutlet(info)  # Broadcast the stream.

    # Keyboard Controls
    print("Keyboard Controls:")
    print("x - test marker")
    print("s - class started")
    print("a - new activity")
    print("e - class ended")
    print("ESC - quit")


    # This is not necessary but can be useful to keep track of markers and the
    # events they correspond to.
    markers = {
        'x': ["Test"],
        's': ["ClassStarted"],
        'a': ["NewActivity"],
        'e': ["ClassEnded"],
    }
    
    print("Stream setup complete. Ready to send markers!")
    print("\nPress keys to send markers (ESC to exit):")
    
    def on_key_press(key):
        try:
            # Handle alphanumeric keys
            if hasattr(key, 'char') and key.char and key.char.lower() in markers:
                key_pressed = key.char.lower()
                
                if key_pressed == 'a':
                    # Special handling for activity - prompt for name
                    print(f"\nKey '{key.char}' pressed - Enter activity name: ", end='', flush=True)
                    activity_name = input()
                    if activity_name.strip():
                        marker = [f"Activity_{activity_name.strip()}"]
                        outlet.push_sample(marker)
                        print(f"Sent marker: {marker[0]}")
                    else:
                        print("No activity name entered, marker not sent.")
                else:
                    # Normal marker handling for other keys
                    marker = markers[key_pressed]
                    outlet.push_sample(marker)
                    print(f"Sent marker: {marker[0]} (key: {key.char})")
        except AttributeError:
            # Handle special keys like ESC
            if key == keyboard.Key.esc:
                print("\nExiting...")
                return False
        except Exception as e:
            print(f"Error processing key: {e}")
    
    def on_key_release(key):
        # Exit on ESC key release as well
        if key == keyboard.Key.esc:
            return False
    
    # Set up keyboard listener
    print("Keyboard listener active...")
    try:
        with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as listener:
            listener.join()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"Error with keyboard listener: {e}")

if __name__ == "__main__":
    main()