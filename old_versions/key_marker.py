"""This file allows you to send LSL markers through keyboard input.
It uses the pynput library to listen for keyboard events and the pylsl library to send markers.
INSTALL THESE LIBRARIES:   
pip install pynput pylsl
"""

from pylsl import StreamInfo, StreamOutlet
from time import sleep, time
from pynput import keyboard
import threading
from collections import deque

def main():
    """Send event markers based on keyboard input."""
    # set up LSL stream that will broadcast my markers
    info = StreamInfo(name='DataSyncMarker', type='Tags', channel_count=1,
                      channel_format='string', source_id='12345')
    outlet = StreamOutlet(info)  # start broadcast!

    getting_input = False  # flag to control when to ignore keys
    
    # NEW: Track sent markers for undo functionality
    sent_markers = deque(maxlen=10)  # Keep last 10 markers for undo

    # single letter key markers
    markers = {
        'x': ["Test"],
        't': ["ClassStarted"],
        'a': ["NewActivity"],
        'b': ["Books"],
        'c': ["Clapping"],
        'd': ["Dancing"],
        'r': ["RepeatAfterMe"],
        'p': ["GetPrizes"],
        'e': ["ClassEnded"]
    }

    # two letter combinations - press keys quickly
    two_key_markers = {
        'si': ["Singing"],
        'gm': ["GeneralMusic"],
        'ss': ["SimonSays"],
        'hs': ["HeadShouldersKneesToes"],
        'br': ["Breathing"],
        'qt': ["QuietTime"],
        'cp': ["ChoicePlay"],
        'ec': ["EarnCoins"],
        'cc': ["ClosingCircle"],
        'im': ["InterestingMoment"]
    }

    # to keep track of what keys im typing for the two letter combos
    key_sequence = ""
    last_key_time = 0
    sequence_timeout = 1.0 # if you wait longer than X seconds, it forgets the first key
    pending_single_key = None  # track pending single key
    single_key_timer = None    # timer for single key delay

    print("Set up is complete!")
    print("\nPress keys to send markers (ESC to quit).")

    # keyboard controls
    print("\nSingle Key Controls:")
    print("x - test marker")
    print("t - class started")
    print("a - new activity")
    print("b - books")
    print("c - clapping")
    print("d - dancing")
    print("r - repeat after me")
    print("p - get prizes")
    print("e - class ended")
    print("u - UNDO last marker")  # NEW
    print("\nTwo-Key Combinations:")
    print("si - singing")
    print("gm - general music")
    print("ss - simon says")
    print("hs - head shoulders knees toes")
    print("br - breathing")
    print("qt - quiet time")
    print("cp - choice play")
    print("ec - earn coins")
    print("cc - closing circle")
    print("im - interesting moment")
    print("ESC - quit")

    def reset_sequence():
        nonlocal key_sequence, pending_single_key, single_key_timer
        key_sequence = ""
        pending_single_key = None
        if single_key_timer:
            single_key_timer.cancel()
            single_key_timer = None

    def send_marker(marker_data, marker_type="marker"):
        """Send a marker and track it for undo functionality"""
        outlet.push_sample(marker_data)
        sent_markers.append({
            'marker': marker_data[0],
            'timestamp': time(),
            'type': marker_type
        })
        print(f"Sent {marker_type}: {marker_data[0]}")

    def undo_last_marker():
        """Remove the last sent marker by sending an UNDO marker"""
        if sent_markers:
            last_marker = sent_markers.pop()
            undo_marker = [f"UNDO_{last_marker['marker']}"]
            outlet.push_sample(undo_marker)
            print(f"UNDID: {last_marker['marker']} (sent UNDO_{last_marker['marker']})")
        else:
            print("No markers to undo!")

    def get_activity_name():
        # THIS FUNCTION HANDLES INPUT SAFELY
        nonlocal getting_input
        getting_input = True  # TURN OFF keyboard listener
        reset_sequence()  # CLEAR SEQUENCE IMMEDIATELY BEFORE INPUT
        print(f"Enter activity name: ", end='', flush=True)
        activity_name = input()
        if activity_name.strip():
            # send a new marker with the activity name
            marker = [f"NewActivity_{activity_name.strip()}"]
            send_marker(marker, "activity marker")
        else:
            print("No activity name entered.")
        getting_input = False  # TURN ON keyboard listener again
        reset_sequence()  # clear any stray keys that might have accumulated

    def send_pending_single_key():
        """Send the pending single key marker after delay"""
        nonlocal pending_single_key
        if pending_single_key and len(key_sequence) <= 1:
            key_pressed = pending_single_key
            if key_pressed == 'a':
                # SEND MARKER IMMEDIATELY, THEN GET ACTIVITY NAME SAFELY
                marker = markers[key_pressed]
                send_marker(marker, "single-key marker")
                
                # USE THREADING TO GET INPUT WITHOUT BLOCKING
                threading.Thread(target=get_activity_name, daemon=True).start()
            else:
                # regular markers for other keys
                marker = markers[key_pressed]
                send_marker(marker, "single-key marker")
            reset_sequence()

    def on_key_press(key):
        nonlocal key_sequence, last_key_time, getting_input, pending_single_key, single_key_timer
        
        # IGNORE ALL KEYS WHILE TYPING ACTIVITY NAME
        if getting_input:
            return

        try:
            current_time = time()

            # ignore numbers, symbols, etc
            if hasattr(key, 'char') and key.char and key.char.isalpha():
                key_pressed = key.char.lower()

                # NEW: Handle undo key
                if key_pressed == 'u':
                    undo_last_marker()
                    reset_sequence()
                    return

                # if wait is too long, times out
                if current_time - last_key_time > sequence_timeout:
                    reset_sequence()

                # Cancel any pending single key timer
                if single_key_timer:
                    single_key_timer.cancel()
                    single_key_timer = None

                # add key to the sequence
                key_sequence += key_pressed
                last_key_time = current_time

                # check two-key combo first
                if len(key_sequence) >= 2:
                    # check if the last two characters match any two-key marker
                    last_two = key_sequence[-2:]
                    if last_two in two_key_markers:
                        marker = two_key_markers[last_two]
                        send_marker(marker, "two-key marker")
                        reset_sequence()
                        return

                    # if we have more than 2 characters and no match, reset
                    if len(key_sequence) > 2:
                        reset_sequence()
                        key_sequence = key_pressed
                        last_key_time = current_time

                # For single key that could be part of a two-key combo
                if len(key_sequence) == 1 and key_pressed in markers:
                    # Check if this key could be the start of a two-key combination
                    could_be_two_key = any(combo.startswith(key_pressed) for combo in two_key_markers.keys())
                    
                    if could_be_two_key:
                        # Wait to see if another key comes
                        pending_single_key = key_pressed
                        single_key_timer = threading.Timer(0.3, send_pending_single_key)
                        single_key_timer.start()
                    else:
                        # This key can't be part of a two-key combo, send immediately
                        if key_pressed == 'a':
                            marker = markers[key_pressed]
                            send_marker(marker, "single-key marker")
                            threading.Thread(target=get_activity_name, daemon=True).start()
                        else:
                            marker = markers[key_pressed]
                            send_marker(marker, "single-key marker")
                        reset_sequence()

        except AttributeError:
            # ESC key
            if key == keyboard.Key.esc:
                print("\nExiting...")
                return False
        except Exception as e:
            print(f"Error processing key: {e}")

    def on_key_release(key):
        # IGNORE KEY RELEASES WHILE TYPING
        if getting_input:
            return
            
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