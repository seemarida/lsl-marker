"""This file allows you to send LSL markers through keyboard input with undo functionality.
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
    
    # NEW: Keep track of sent markers for undo functionality
    marker_history = deque(maxlen=10)  # Keep last 10 markers
    undo_count = 0  # Track how many undos we've done

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
        'e': ["ClassEnded"],
        'u': ["UNDO"]  # NEW: Undo key
    }

    # two letter combinations - press keys quickly!!!
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
        'im': ["InterestingMoment"],
        'un': ["UNDO"]  # NEW: Two-key undo combo
    }

    # to keep track of what keys im typing for the two letter combos
    key_sequence = ""
    last_key_time = 0
    sequence_timeout = 1.0 # if you wait longer than X seconds, it forgets the first key
    pending_single_key = None  # track pending single key
    single_key_timer = None    # timer for single key delay

    def send_marker_with_history(marker_data, description=""):
        """Send marker and add to history for undo functionality"""
        nonlocal undo_count
        timestamp = time()
        outlet.push_sample(marker_data, timestamp)
        
        # Add to history (but not if it's an undo marker)
        if not marker_data[0].startswith("UNDO") and not marker_data[0].startswith("CANCEL"):
            marker_history.append({
                'marker': marker_data[0],
                'timestamp': timestamp,
                'description': description
            })
            undo_count = 0  # Reset undo count when new marker is sent
        
        print(f"Sent marker: {marker_data[0]} {description}")

    def handle_undo():
        """Handle undo functionality"""
        nonlocal undo_count
        
        if len(marker_history) == 0:
            print("No markers to undo!")
            return
            
        if undo_count >= len(marker_history):
            print("Already undone all available markers!")
            return
            
        # Get the marker to undo (going backwards from most recent)
        marker_to_undo = list(marker_history)[-1 - undo_count]
        undo_count += 1
        
        # Send an undo marker that references the original
        undo_marker = [f"UNDO_{marker_to_undo['marker']}"]
        timestamp = time()
        outlet.push_sample(undo_marker, timestamp)
        
        print(f"UNDOING: {marker_to_undo['marker']} (sent {undo_marker[0]})")
        print(f"Undo count: {undo_count}/{len(marker_history)}")

    def show_marker_history():
        """Show recent marker history"""
        if not marker_history:
            print("No marker history available")
            return
            
        print("\n--- Recent Marker History ---")
        for i, entry in enumerate(reversed(list(marker_history))):
            status = " (UNDONE)" if i < undo_count else ""
            print(f"{len(marker_history)-i}: {entry['marker']}{status}")
        print("-----------------------------\n")

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
    print("un - UNDO last marker")  # NEW
    print("\nSpecial Commands:")
    print("ESC - quit")

    def reset_sequence():
        nonlocal key_sequence, pending_single_key, single_key_timer
        key_sequence = ""
        pending_single_key = None
        if single_key_timer:
            single_key_timer.cancel()
            single_key_timer = None

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
            send_marker_with_history(marker, f"(activity: {activity_name.strip()})")
        else:
            print("No activity name entered.")
        getting_input = False  # TURN ON keyboard listener again
        reset_sequence()  # clear any stray keys that might have accumulated

    def get_interesting_moment_note():
        # THIS FUNCTION HANDLES INPUT SAFELY FOR INTERESTING MOMENTS
        nonlocal getting_input
        getting_input = True  # TURN OFF keyboard listener
        reset_sequence()  # CLEAR SEQUENCE IMMEDIATELY BEFORE INPUT
        print(f"What was interesting? ", end='', flush=True)
        note = input()
        if note.strip():
            # send a marker with the note
            marker = [f"InterestingMoment_{note.strip()}"]
            send_marker_with_history(marker, f"(note: {note.strip()})")
        else:
            # send generic interesting moment if no note provided
            marker = ["InterestingMoment"]
            send_marker_with_history(marker, "(no note provided)")
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
                send_marker_with_history(marker, f"(key: {key_pressed})")
                
                # USE THREADING TO GET INPUT WITHOUT BLOCKING
                threading.Thread(target=get_activity_name, daemon=True).start()
            elif key_pressed == 'u':
                # Handle undo
                handle_undo()
            else:
                # regular markers for other keys
                marker = markers[key_pressed]
                send_marker_with_history(marker, f"(key: {key_pressed})")
            reset_sequence()

    def on_key_press(key):
        nonlocal key_sequence, last_key_time, getting_input, pending_single_key, single_key_timer
        
        # IGNORE ALL KEYS WHILE TYPING ACTIVITY NAME
        if getting_input:
            return

        try:
            # Handle F1 for history
            if key == keyboard.Key.f1:
                show_marker_history()
                return

            current_time = time()

            # ignore numbers, symbols, etc
            if hasattr(key, 'char') and key.char and key.char.isalpha():
                key_pressed = key.char.lower()

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
                        if last_two == 'un':
                            # Handle two-key undo
                            handle_undo()
                        elif last_two == 'im':
                            # Handle interesting moment with note input
                            threading.Thread(target=get_interesting_moment_note, daemon=True).start()
                        else:
                            marker = two_key_markers[last_two]
                            send_marker_with_history(marker, f"(keys: {last_two})")
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
                            send_marker_with_history(marker, f"(key: {key_pressed})")
                            threading.Thread(target=get_activity_name, daemon=True).start()
                        elif key_pressed == 'u':
                            handle_undo()
                        else:
                            marker = markers[key_pressed]
                            send_marker_with_history(marker, f"(key: {key_pressed})")
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