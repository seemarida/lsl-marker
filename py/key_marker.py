#new
"""This file allows you to send LSL markers through keyboard input.
It uses the pynput library to listen for keyboard events and the pylsl library to send markers.
INSTALL THESE LIBRARIES:   
pip install pynput pylsl
"""

from pylsl import StreamInfo, StreamOutlet
from time import sleep, time
from pynput import keyboard
import threading

def main():
    """Send event markers based on keyboard input."""
    # set up LSL stream that will broadcast my markers
    info = StreamInfo(name='DataSyncMarker', type='Tags', channel_count=1,
                      channel_format='string', source_id='12345')
    outlet = StreamOutlet(info)  # start broadcast!

    getting_input = False  # NEW - flag to control when to ignore keys

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

    # two letter combinations - press keys quickly!!!
    two_key_markers = {
        'si': ["Singing"],
        'gm': ["GeneralMusic"],
        #'ar': ["Art"],
        'ss': ["SimonSays"],
        'hs': ["HeadShouldersKneesToes"],
        'br': ["Breathing"],
        'qt': ["QuietTime"],
        'cp': ["ChoicePlay"],
        'ec': ["EarnCoins"],
        'cc': ["ClosingCircle"],
        'im': ["InterestingMoment"]
    }

    # to keep track of waht keys im typing for the two letter combos
    key_sequence = ""
    last_key_time = 0
    sequence_timeout = 1.0 # if you wait longer than X seconds, it forgets the first key

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
    print("\nTwo-Key Combinations:")
    print("si - singing")
    print("gm - general music")
    #print("ar - art")
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
        nonlocal key_sequence
        key_sequence = ""

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
            outlet.push_sample(marker)
            print(f"Sent marker: {marker[0]}")
        else:
            print("No activity name entered.")
        getting_input = False  # TURN ON keyboard listener again
        reset_sequence()  # clear any stray keys that might have accumulated

    def on_key_press(key):
        nonlocal key_sequence, last_key_time, getting_input
        
        # IGNORE ALL KEYS WHILE TYPING ACTIVITY NAME
        if getting_input:
            return

        try:
            current_time = time()

            # ignore numbers, symbols, etc
            if hasattr(key, 'char') and key.char and key.char.isalpha():
                key_pressed = key.char.lower()

                # if wait is too long, times out
                if current_time - last_key_time > sequence_timeout:
                    reset_sequence()

                # add key to the sequence
                key_sequence += key_pressed
                last_key_time = current_time

                # check two-key combo first
                if len(key_sequence) >= 2:
                    # check if the last two characters match any two-key marker
                    last_two = key_sequence[-2:]
                    if last_two in two_key_markers:
                        marker = two_key_markers[last_two]
                        outlet.push_sample(marker)
                        print(f"Sent two-key marker: {marker[0]} (keys: {last_two})")
                        reset_sequence()
                        return

                    # if we have more than 2 characters and no match, reset
                    if len(key_sequence) > 2:
                        reset_sequence()
                        key_sequence = key_pressed
                        last_key_time = current_time

                # check for single key markers (but wait a bit to see if it's part of a sequence)
                if len(key_sequence) == 1 and key_pressed in markers:
                    # wait a bit to see if another key is coming
                    sleep(0.2) # small delay to catch quick two-key sequences

                    # check if sequence was extended during the wait
                    if len(key_sequence) == 1:  # still just one key
                        if key_pressed == 'a':
                            # SEND MARKER IMMEDIATELY, THEN GET ACTIVITY NAME SAFELY
                            marker = markers[key_pressed]
                            outlet.push_sample(marker)
                            print(f"Sent single-key marker: {marker[0]} (key: {key.char})")
                            
                            # USE THREADING TO GET INPUT WITHOUT BLOCKING
                            threading.Thread(target=get_activity_name, daemon=True).start()
                        else:
                            # regular markers for other keys
                            marker = markers[key_pressed]
                            outlet.push_sample(marker)
                            print(f"Sent single-key marker: {marker[0]} (key: {key.char})")
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