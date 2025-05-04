import keyboard
import mouse
import time
import sys
import pyautogui
import winsound
import sqlite3
import os
import tkinter as tk
from tkinter import messagebox
import threading

# Database file name
DB_FILE = "sequences.db"

# Default base sequence structure (SAME)
base_sequence = [
    [0, 0, 0, 1, 0],  # Step 1: X, Y, delay, status (on), beep (off)
    [0, 0, 0, 1, 0],  # Step 2: X, Y, delay, status (on), beep (off)
    [0, 0, 0, 1, 0],  # Step 3: X, Y, delay, status (on), beep (off)
    [0, 0, 0, 0, 0],  # Step 4: Remains constant
]

# Save sequences to the database
def save_sequences_to_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        # Ensure the sequences table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sequence_id INTEGER NOT NULL,
                step_index INTEGER NOT NULL,
                x_percent REAL NOT NULL,
                y_percent REAL NOT NULL,
                delay REAL NOT NULL,
                status INTEGER NOT NULL,
                beep INTEGER NOT NULL
            )
        """)

        # Clear the table before inserting new data
        cursor.execute("DELETE FROM sequences")
        for seq_id, sequence in enumerate(sequences, start=1):
            for step_index, step in enumerate(sequence, start=1):
                x_percent, y_percent, delay, status, beep = step
                cursor.execute("""
                    INSERT INTO sequences (sequence_id, step_index, x_percent, y_percent, delay, status, beep)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (seq_id, step_index, x_percent, y_percent, delay, status, beep))
        conn.commit()
        print(f"Sequences saved to {DB_FILE}")

# Generate sequences dynamically (SAME)
sequences = []

for i in range(9):
    sequence = [step[:] for step in base_sequence]  # Deep copy of the base structure

    if i == 6:  # Sequence 7
        sequence[2][3] = 0  # Step 3: status = off
    elif i in [7, 8]:  # Sequence 8 and 9
        sequence[2][3] = 0  # Step 3: status = off

    sequences.append(sequence)

    # dynamicly OFF secuence 4 (put louse to center of screen)
# Dynamically turn off Step 4 in all sequences
for sequence in sequences:
    sequence[3][3] = 0  # Step 4: status = 0 (off)
# Save the updated sequences to the database
#save_sequences_to_db()
    
# Initialize the SQLite database
def initialize_database():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sequence_id INTEGER NOT NULL,
                step_index INTEGER NOT NULL,
                x_percent REAL NOT NULL,
                y_percent REAL NOT NULL,
                delay REAL NOT NULL,
                status INTEGER NOT NULL,
                beep INTEGER NOT NULL
            )
        """)
        conn.commit()


# Load sequences from the database
def load_sequences_from_db():
    global sequences
    sequences = []
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sequence_id, step_index, x_percent, y_percent, delay, status, beep
            FROM sequences
            ORDER BY sequence_id, step_index
        """)
        data = cursor.fetchall()
        if data:
            current_sequence_id = 1
            current_sequence = []
            for row in data:
                sequence_id, step_index, x_percent, y_percent, delay, status, beep = row
                if sequence_id != current_sequence_id:
                    sequences.append(current_sequence)
                    current_sequence = []
                    current_sequence_id = sequence_id
                current_sequence.append([x_percent, y_percent, delay, status, beep])
            if current_sequence:
                sequences.append(current_sequence)
            print(f"Sequences loaded from {DB_FILE}")
        else:
            print(f"No data in database. Using default sequences.")
            
# new in ver 5.1 - protect phisical moving the mouse
def lock_mouse_position(lock, position):
    """Continuously move the mouse to a locked position while `lock` is True."""
    while lock[0]:
        pyautogui.moveTo(position[0], position[1])
        time.sleep(0.09)  # Small delay to avoid excessive CPU usage**!!!!!!!!!!!!!!!!
        #in v_5.15 = 0.1 - works well
        #in v_5.16 = 0.01 - works bed
        #in v_5.17 = 0.05 - works bed


# Execute a sequence. updated to have in ver 5.1 - protect phisical moving the mouse

def execute_sequence(sequence, sequence_id, return_position):
    """
    Execute a sequence of mouse actions and lock the mouse during execution.
    """
    print(f"Executing Sequence {sequence_id}")

    # Get screen dimensions once
    screen_width, screen_height = pyautogui.size()

    # Precompute all target positions for this sequence
    targets = []
    for step_index, step in enumerate(sequence, start=1):
        x_percent, y_percent, delay, status, beep = step

        # Skip steps that are turned off
        if status == 0:
            print(f"Step {step_index} in Sequence {sequence_id} is turned off. Skipping.")
            continue

        # Calculate screen coordinates
        target_x = int(screen_width * x_percent)
        target_y = int(screen_height * y_percent)

        # Skip steps with (0, 0) coordinates to prevent fail-safe
        if target_x == 0 and target_y == 0:
            print(f"Step {step_index}: Skipping due to fail-safe coordinates (0, 0).")
            continue

        targets.append((target_x, target_y, delay, beep, step_index))

    # Start locking the mouse to the initial position
    lock = [True]
    lock_thread = threading.Thread(target=lock_mouse_position, args=(lock, pyautogui.position()))
    lock_thread.start()

    try:
        # Execute all actions
        for target_x, target_y, delay, beep, step_index in targets:
            # Move the mouse instantly to the target location

            if step_index == 1:
                time.sleep(0.001)  # Brief delay to ensure cursor settles !!!!!!!!!!!
                #in v_5.15 = 0.001 - works well
                
            pyautogui.moveTo(target_x, target_y, duration=0)
            print(f"Step {step_index}: Moved to ({target_x}, {target_y}).")
            print(f"Step {step_index}: Delay of {delay} seconds applied.")

            if step_index == 1:
                time.sleep(0.001)  # Brief delay to ensure cursor settles !!!!!!!!!!!

            # Perform click for non-special cases
            if step_index != 4:  # Example: Skip click for Step 4
                pyautogui.click()
                print(f"Step {step_index}: Click performed.")
            else:
                print(f"Step {step_index}: No click performed (special case).")

            # Beep if enabled
            if beep == 1:
                winsound.Beep(600, 50)  # Short beep duration
                print(f"Step {step_index}: Beep sounded.")

            # Apply delay before the next step
            if delay > 0:
                time.sleep(delay)
            # Add a small sleep between steps to slow the sequence slightly
            time.sleep(0.01)  #********************************************************
            #in v_5.15 = 0.01 - works well

        # Return the mouse to the original position
        original_x, original_y = return_position
        pyautogui.moveTo(original_x, original_y, duration=0)
        print(f"Mouse returned to original position: ({original_x}, {original_y}).")

        # Final small pause to let the system process
        time.sleep(0.0001) #**********************************************************

    finally:
        # Stop locking the mouse
        lock[0] = False
        lock_thread.join()

    print(f"Sequence {sequence_id} execution complete.")





# Define popup windows
def show_topmost_message(title, message):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showinfo(title, message)
    root.destroy()

# Hotkey function: Setup and save coordinates
def shift_s():

    show_topmost_message("Setup Ctrl+alt+0", "PLEASE CLICK 6 TIMES TO ORIENT YOUR 3D MODEL TO NORTH, CENTER VIEW, REMOVE, CLIP.")

   
    # List to store clicks and a flag to stop the loop
    clicks = []
    finished = [False]  # Use a list to modify this flag inside the nested callback

    def on_click():
        if finished[0]:  # Ignore further clicks if finished
            return

        x, y = pyautogui.position()  # Get the current mouse position
        print(f"Click recorded at: ({x}, {y})")
        clicks.append((x, y))  # Append the position to the clicks list
        winsound.Beep(600, 200)  # Short beep for confirmation

        # Stop listening after 5 clicks
        if len(clicks) >= 6:
            finished[0] = True  # Signal that the loop should exit
            try:
                mouse.unhook(on_click)  # Unhook the listener safely
            except ValueError:
                pass  # Handle cases where unhook is attempted twice

    # Start listening for mouse clicks
    mouse.on_click(on_click)

    while not finished[0]:
        time.sleep(0.01)  # Small delay to avoid busy waiting
        pass

    # Normalize and save clicks to Sequence 1
    screen_width, screen_height = pyautogui.size()

    # Save the first 3 clicks to Sequence 1
    for i in range(3):
        sequences[0][i][0] = clicks[i][0] / screen_width  # X
        sequences[0][i][1] = clicks[i][1] / screen_height  # Y

    # Save the 4th click to Sequence 9 (first step) IN FACT IT IS SEQUENCE 7
    sequences[6][1][0] = clicks[3][0] / screen_width  # X
    sequences[6][1][1] = clicks[3][1] / screen_height  # Y

    # Save the 5th click to Sequence 9 (first step) IN FACT IT IS SEQUENCE 9
    sequences[8][1][0] = clicks[5][0] / screen_width  # X
    sequences[8][1][1] = clicks[5][1] / screen_height  # Y

    # Save the 6th click to Sequence 8 (first step)  IN FACT IT IS SEQUENCE 8
    sequences[7][1][0] = clicks[4][0] / screen_width  # X
    sequences[7][1][1] = clicks[4][1] / screen_height  # Y

    # Calculate Sequence 2 from Sequence 1 using constants
    adjustment_constants_2 = [
        [0, 0],     # Step 1 adjustment [X, Y]
        [0, 0],     # Step 2 adjustment [X, Y]
        [0.0165, 0], # Step 3 adjustment [X, Y]
        [0, 0]      # Step 4 adjustment [X, Y]
    ]

    for step_index in range(len(sequences[1])):  # sequences[1] corresponds to Sequence 2
        sequences[1][step_index][0] = round(sequences[0][step_index][0] + adjustment_constants_2[step_index][0], 3)  # X
        sequences[1][step_index][1] = round(sequences[0][step_index][1] + adjustment_constants_2[step_index][1], 3)  # Y
        sequences[1][step_index][2] = sequences[0][step_index][2]  # Copy delay
        sequences[1][step_index][3] = sequences[0][step_index][3]  # Copy status
        sequences[1][step_index][4] = sequences[0][step_index][4]  # Copy beep 

    # Calculate Sequence 3 from Sequence 1 using constants
    adjustment_constants_3 = [
        [0, 0],    # Step 1 adjustment [X, Y]
        [0, 0],    # Step 2 adjustment [X, Y]
        [0, 0.04], # Step 3 adjustment [X, Y]
        [0, 0]     # Step 4 adjustment [X, Y]
    ]

    for step_index in range(len(sequences[2])):  # Use sequences[1] for Sequence 3
        sequences[2][step_index][0] = round(sequences[0][step_index][0] + adjustment_constants_3[step_index][0],3)  # X
        sequences[2][step_index][1] = round(sequences[0][step_index][1] + adjustment_constants_3[step_index][1],3)  # Y
        sequences[2][step_index][2] = sequences[0][step_index][2]  # Copy delay
        sequences[2][step_index][3] = sequences[0][step_index][3]  # Copy status
        sequences[2][step_index][4] = sequences[0][step_index][4]  # Copy beep

    # Calculate Sequence 4 from Sequence 1 using constants
    adjustment_constants_4 = [
        [0, 0],      # Step 1 adjustment [X, Y]
        [0, 0],      # Step 2 adjustment [X, Y]
        [0.030, 0],  # Step 3 adjustment [X, Y] [0.032, 0]
        [0, 0]       # Step 4 adjustment [X, Y]
    ]

    for step_index in range(len(sequences[3])):  # Use sequences[1] for Sequence 4
        sequences[3][step_index][0] = round(sequences[0][step_index][0] + adjustment_constants_4[step_index][0],3)  # X
        sequences[3][step_index][1] = round(sequences[0][step_index][1] + adjustment_constants_4[step_index][1],3)  # Y
        sequences[3][step_index][2] = sequences[0][step_index][2]  # Copy delay
        sequences[3][step_index][3] = sequences[0][step_index][3]  # Copy status
        sequences[3][step_index][4] = sequences[0][step_index][4]  # Copy beep    


    # Calculate Sequence 5 from Sequence 1 using constants - 4th picture
    adjustment_constants_5 = [
        [0, 0],      # Step 1 adjustment [X, Y]
        [0, 0],      # Step 2 adjustment [X, Y]
        [0.05, 0],  # Step 3 adjustment [X, Y] [0.0445, 0]
        [0, 0]       # Step 4 adjustment [X, Y]
    ]

    for step_index in range(len(sequences[4])):  # Use sequences[1] for Sequence 5
        sequences[4][step_index][0] = round(sequences[0][step_index][0] + adjustment_constants_5[step_index][0],3)  # X
        sequences[4][step_index][1] = round(sequences[0][step_index][1] + adjustment_constants_5[step_index][1],3)  # Y
        sequences[4][step_index][2] = sequences[0][step_index][2]  # Copy delay
        sequences[4][step_index][3] = sequences[0][step_index][3]  # Copy status
        sequences[4][step_index][4] = sequences[0][step_index][4]  # Copy beep    

    # Calculate Sequence 6 from Sequence 1 using constants
    adjustment_constants_6 = [
        [0, 0],      # Step 1 adjustment [X, Y]
        [0, 0],      # Step 2 adjustment [X, Y]
        [0.017, 0.04],  # Step 3 adjustment [X, Y]
        [0, 0]       # Step 4 adjustment [X, Y]
    ]

    for step_index in range(len(sequences[5])):  # Use sequences[1] for Sequence 6
        sequences[5][step_index][0] = round(sequences[0][step_index][0] + adjustment_constants_6[step_index][0],3)  # X
        sequences[5][step_index][1] = round(sequences[0][step_index][1] + adjustment_constants_6[step_index][1],3)  # Y
        sequences[5][step_index][2] = sequences[0][step_index][2]  # Copy delay
        sequences[5][step_index][3] = sequences[0][step_index][3]  # Copy status
        sequences[5][step_index][4] = sequences[0][step_index][4]  # Copy beep 

    # Calculate Sequence 7 from Sequence 1 using constants 
    adjustment_constants_7 = [
        [0, 0],                 # Step 1 adjustment [X, Y]
        [0, 0],         # Step 2 adjustment [X, Y]
        [0, 0],                 # Step 3 adjustment [X, Y]
        [0, 0]                  # Step 4 adjustment [X, Y]
    ]

    step_index = 0  # First row (0) from click 1, second row (1) - from click 4
        
    sequences[6][step_index][0] = sequences[0][step_index][0]  # X
    sequences[6][step_index][1] = sequences[0][step_index][1]  # Y
    sequences[6][step_index][2] = sequences[0][step_index][2]  # Copy delay
    sequences[6][step_index][3] = sequences[0][step_index][3]  # Copy status
    sequences[6][step_index][4] = sequences[0][step_index][4]  # Copy beep
    
    step_index = 3

    sequences[6][step_index][0] = sequences[0][step_index][0]  # X
    sequences[6][step_index][1] = sequences[0][step_index][1]  # Y
    sequences[6][step_index][2] = sequences[0][step_index][2]  # Copy delay
    sequences[6][step_index][3] = sequences[0][step_index][3]  # Copy status
    sequences[6][step_index][4] = sequences[0][step_index][4]  # Copy beep  

    # Calculate Sequence 8 from Sequence 1 using constants 
    adjustment_constants_8 = [
        [0, 0],         # Step 1 adjustment [X, Y]
        [0, 0],         # Step 2 adjustment [X, Y]
        [0, 0],         # Step 3 adjustment [X, Y]
        [0, 0]          # Step 4 adjustment [X, Y]
    ]

    step_index = 0  # First row (0) from click 1, second row (1) - from click 5
        
    sequences[7][step_index][0] = sequences[0][step_index][0]  # X
    sequences[7][step_index][1] = sequences[0][step_index][1]  # Y
    sequences[7][step_index][2] = sequences[0][step_index][2]  # Copy delay
    sequences[7][step_index][3] = sequences[0][step_index][3]  # Copy status
    sequences[7][step_index][4] = sequences[0][step_index][4]  # Copy beep
    
    step_index = 3

    sequences[7][step_index][0] = sequences[0][step_index][0]  # X
    sequences[7][step_index][1] = sequences[0][step_index][1]  # Y
    sequences[7][step_index][2] = sequences[0][step_index][2]  # Copy delay
    sequences[7][step_index][3] = sequences[0][step_index][3]  # Copy status
    sequences[7][step_index][4] = sequences[0][step_index][4]  # Copy beep

    # Calculate Sequence 9 from Sequence 1 using constants 
    adjustment_constants_9 = [
        [0, 0],         # Step 1 adjustment [X, Y]
        [0, 0],         # Step 2 adjustment [X, Y]
        [0, 0],         # Step 3 adjustment [X, Y]
        [0, 0]          # Step 4 adjustment [X, Y]
    ]

    step_index = 0  # First row (0) from click 1, second row (1) - from click 6
        
    sequences[8][step_index][0] = sequences[0][step_index][0]  # X
    sequences[8][step_index][1] = sequences[0][step_index][1]  # Y
    sequences[8][step_index][2] = sequences[0][step_index][2]  # Copy delay
    sequences[8][step_index][3] = sequences[0][step_index][3]  # Copy status
    sequences[8][step_index][4] = sequences[0][step_index][4]  # Copy beep
    
    step_index = 3

    sequences[8][step_index][0] = sequences[0][step_index][0]  # X
    sequences[8][step_index][1] = sequences[0][step_index][1]  # Y
    sequences[8][step_index][2] = sequences[0][step_index][2]  # Copy delay
    sequences[8][step_index][3] = sequences[0][step_index][3]  # Copy status
    sequences[8][step_index][4] = sequences[0][step_index][4]  # Copy beep 
    

    print("Normalized coordinates saved:")
    print(f" - Sequence 1: {sequences[0][:3]}")
    print(f" - Sequence 9, Step 1: {sequences[8][0]}")
    print(f" - Sequence 8, Step 1: {sequences[7][0]}")
    print(f" - Sequence 2 (calculated): {sequences[1]}")
    

    # Notify the user and save the updated sequences 
    save_sequences_to_db()

    # Unhook and re-register hotkeys
    unhook_all_hotkeys()  # Clear existing hotkeys - use new unhook method
    register_all_hotkeys()  # Re-enable all functionality

    show_topmost_message("Setup Complete", "Sequences have been successfully updated.")
    print("Setup complete. All hotkeys are now enabled.")

# Hotkeys to execute sequences new in 4.99
def ctrl_alt_1():
    original_position = pyautogui.position()
    execute_sequence(sequences[0], 1, original_position)
def ctrl_alt_2():
    original_position = pyautogui.position()
    execute_sequence(sequences[1], 2, original_position)
def ctrl_alt_3():
    original_position = pyautogui.position()
    execute_sequence(sequences[2], 3, original_position)
def ctrl_alt_4():
    original_position = pyautogui.position()
    execute_sequence(sequences[3], 4, original_position)
def ctrl_alt_5():
    original_position = pyautogui.position()
    execute_sequence(sequences[4], 5, original_position)
def ctrl_alt_6():
    original_position = pyautogui.position()
    execute_sequence(sequences[5], 6, original_position)
def ctrl_alt_7():
    original_position = pyautogui.position()
    execute_sequence(sequences[6], 7, original_position)
def ctrl_alt_8():
    original_position = pyautogui.position()
    execute_sequence(sequences[7], 8, original_position)
def ctrl_alt_9():
    original_position = pyautogui.position()
    execute_sequence(sequences[8], 9, original_position)
def ctrl_alt_0():
    shift_s()
    

def unhook_all_hotkeys():
    """Unhook all registered hotkeys manually."""
    try:
        keyboard.remove_hotkey("ctrl+alt+0")  # for shift_S
        keyboard.remove_hotkey("ctrl+alt+1")
        keyboard.remove_hotkey("ctrl+alt+2")
        keyboard.remove_hotkey("ctrl+alt+3")
        keyboard.remove_hotkey("ctrl+alt+4")
        keyboard.remove_hotkey("ctrl+alt+5")
        keyboard.remove_hotkey("ctrl+alt+6")
        keyboard.remove_hotkey("ctrl+alt+7")
        keyboard.remove_hotkey("ctrl+alt+8")
        keyboard.remove_hotkey("ctrl+alt+9")
        keyboard.remove_hotkey("alt+esc")
    except KeyError:
        pass  # Hotkey might not be registered yet

def exit_script():
    print("Exiting the script. Goodbye!")
    keyboard.unhook_all_hotkeys()
    sys.exit()

# Register hotkeys
def register_all_hotkeys():
    """Register all hotkeys."""
    keyboard.add_hotkey("ctrl+alt+0", shift_s)  # Keep setup hotkey
    keyboard.add_hotkey("ctrl+alt+1", ctrl_alt_1)
    keyboard.add_hotkey("ctrl+alt+2", ctrl_alt_2)
    keyboard.add_hotkey("ctrl+alt+3", ctrl_alt_6)  # Adjust based on your logic
    keyboard.add_hotkey("ctrl+alt+4", ctrl_alt_4)
    keyboard.add_hotkey("ctrl+alt+5", ctrl_alt_5)
    keyboard.add_hotkey("ctrl+alt+6", ctrl_alt_3)  # Adjust based on your logic
    keyboard.add_hotkey("ctrl+alt+7", ctrl_alt_7)
    keyboard.add_hotkey("ctrl+alt+8", ctrl_alt_9)  # Adjust based on your logic
    keyboard.add_hotkey("ctrl+alt+9", ctrl_alt_8)  # Adjust based on your logic
    # keyboard.add_hotkey("ctrl+alt+0", ctrl_alt_0)
    keyboard.add_hotkey("alt+esc", exit_script)



# Initialize and load sequences
if not os.path.exists(DB_FILE):
    # Show a popup message if the database does not exist
    def db_missing_message():
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showerror(
            "Database Missing",
            "Database file not found.\nPlease set up the coordinates using ctrl+alt+0."
        )
        root.destroy()

    db_missing_message()

    # Register only the setup hotkey (ctrl+alt+0)
    # keyboard.clear_all_hotkeys()  # Remove all other hotkeys
    keyboard.add_hotkey("ctrl+alt+0", shift_s)

    # Notify in the console
    print("Database file missing. Only ctrl+alt+0 is available for setup.")
else:
    # Ensure the sequences table exists in the database
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sequence_id INTEGER NOT NULL,
                step_index INTEGER NOT NULL,
                x_percent REAL NOT NULL,
                y_percent REAL NOT NULL,
                delay REAL NOT NULL,
                status INTEGER NOT NULL,
                beep INTEGER NOT NULL
            )
        """)
        conn.commit()

    # Load sequences from the database and proceed normally
    load_sequences_from_db()

    # Register all hotkeys as usual
    keyboard.add_hotkey("ctrl+alt+1", ctrl_alt_1)
    keyboard.add_hotkey("ctrl+alt+2", ctrl_alt_2)
    keyboard.add_hotkey("ctrl+alt+3", ctrl_alt_6)  # 8 and 8 chanched by tuning:mistake
    keyboard.add_hotkey("ctrl+alt+4", ctrl_alt_4)
    keyboard.add_hotkey("ctrl+alt+5", ctrl_alt_5)
    keyboard.add_hotkey("ctrl+alt+6", ctrl_alt_3)
    keyboard.add_hotkey("ctrl+alt+7", ctrl_alt_7)
    keyboard.add_hotkey("ctrl+alt+8", ctrl_alt_9)  # 8 and 8 chanched by tuning:mistake
    keyboard.add_hotkey("ctrl+alt+9", ctrl_alt_8)
    keyboard.add_hotkey("ctrl+alt+0", ctrl_alt_0)
    keyboard.add_hotkey("alt+esc", exit_script)

# Instructions
print("Hotkeys:")
print(" - ctrl+alt+0: Setup coordinates")
if os.path.exists(DB_FILE):
    print(" - Ctrl+Alt+1 to Ctrl+Alt+9: Execute sequences")
    print(" - Alt+Esc: Exit the script")
else:
    print("Database file missing. Only ctrl+alt+0 is available for setup.")

# Keep the script running
keyboard.wait()
