import ctypes
import time
import random
import tkinter as tk
from tkinter import messagebox
from threading import Thread

items = {
    "Socom": [0x300B2A1A, 0x302B2A1A, 0x304B2A1A, 0x306B2A1A, 0x200B2A1A, 0x202B2A1A, 0x204B2A1A, 0x206B2A1A],
    "C4": [0x306B2A26, 0x302B2A26, 0x304B2A26, 0x306B2A26, 0x206B2A26, 0x202B2A26, 0x204B2A26, 0x206B2A26],
    "Famas": [0x300B2A1C, 0x302B2A1C, 0x304B2A1C, 0x306B2A1C, 0x200B2A1C, 0x202B2A1C, 0x204B2A1C, 0x206B2A1C],
    "Grenades": [0x300B2A1E, 0x302B2A1E, 0x304B2A1E, 0x306B2A1E, 0x200B2A1E, 0x202B2A1E, 0x204B2A1E, 0x206B2A1E],
    "Claymore": [0x300B2A24, 0x302B2A24, 0x304B2A24, 0x306B2A24, 0x200B2A24, 0x202B2A24, 0x204B2A24, 0x206B2A24],
    "Nikita": [0x300B2A20, 0x302B2A20, 0x304B2A20, 0x306B2A20, 0x200B2A20, 0x202B2A20, 0x204B2A20, 0x206B2A20],
    "PSG1": [0x300B2A2C, 0x302B2A2C, 0x304B2A2C, 0x306B2A2C, 0x200B2A2C, 0x202B2A2C, 0x204B2A2C, 0x206B2A2C],
    "Stinger": [0x300B2A22, 0x302B2A22, 0x304B2A22, 0x306B2A22, 0x200B2A22, 0x202B2A22, 0x204B2A22, 0x206B2A22],
}

players_inventory = {
    "Socom": 0,
    "C4": 0,
    "Famas": 0,
    "Grenades": 0,
    "Claymore": 0,
    "Nikita": 0,
    "PSG1": 0,
    "Stinger": 0,
    "Stun": 0
}

def write_to_memory(process_id, addresses, data):
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    process_handle = kernel32.OpenProcess(0x1F0FFF, False, process_id)
    if process_handle:
        data = max(0, min(data, 0xFFFF))
        data_c = ctypes.c_ushort(data)
        for address in addresses:
            success = kernel32.WriteProcessMemory(process_handle, address, ctypes.byref(data_c), ctypes.sizeof(data_c), None)
        kernel32.CloseHandle(process_handle)

def update_saved_inventory(pid):
    global saved_inventory
    for item, addresses in items.items():
        current_count = read_from_memory(pid, addresses)
        if current_count is not None and current_count <= 1000:
            saved_inventory[item] = current_count

def generate_random_ammo():
    return random.randint(2, 10)

def generate_random_subtraction(ammo_to_add):
    min_subtract = max(1, ammo_to_add - 2)
    max_subtract = ammo_to_add + 2
    return random.randint(min_subtract, max_subtract)

def read_from_memory(process_id, addresses, data_type=ctypes.c_ushort):
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    process_handle = kernel32.OpenProcess(0x0010, False, process_id)
    if process_handle:
        data_c = data_type()
        bytes_read = ctypes.c_size_t()
        success = kernel32.ReadProcessMemory(process_handle, addresses[0], ctypes.byref(data_c), ctypes.sizeof(data_c), ctypes.byref(bytes_read))
        kernel32.CloseHandle(process_handle)
        if success and bytes_read.value > 0:
            return data_c.value

def get_process_id(window, pid_var, pid_entry):
    pid_value = pid_entry.get()
    if pid_value.isdigit():
        pid_var.set(int(pid_value))
        window.destroy()
    else:
        messagebox.showerror("Error", "Please enter a valid PID.")

def present_options(pid, inventory):
    window = tk.Tk()
    window.title("Choose an Option")

    options = random.sample(list(inventory.items()), 3)
    ammo_to_add = generate_random_ammo()
    current_inventory = {item: read_from_memory(pid, addresses) or 0 for item, addresses in items.items()}

    valid_subtract_items = [item for item, count in current_inventory.items() if count > 0 and item in [option[0] for option in options]]
    subtract_item = None
    subtract_amount = 0
    if valid_subtract_items:
        subtract_item = random.choice(valid_subtract_items)
        max_subtractable = current_inventory[subtract_item]
        subtract_amount = generate_random_subtraction(ammo_to_add)
        subtract_amount = min(subtract_amount, max_subtractable)
        options = [option for option in options if option[0] != subtract_item]
        if len(options) < 3:
            additional_options = random.sample([item for item in inventory.items() if item[0] != subtract_item and item not in options], 3 - len(options))
            options += additional_options

    def on_button_click(chosen_option):
        chosen_item = options[chosen_option][0]
        current_ammo = read_from_memory(pid, items[chosen_item])
        if current_ammo is None:
            current_ammo = 0
        updated_ammo = current_ammo + ammo_to_add
        write_to_memory(pid, items[chosen_item], updated_ammo)

        if subtract_item:
            current_ammo_subtract_item = read_from_memory(pid, items[subtract_item])
            if current_ammo_subtract_item is None:
                current_ammo_subtract_item = 0
            updated_ammo_subtract_item = max(0, current_ammo_subtract_item - subtract_amount)
            write_to_memory(pid, items[subtract_item], updated_ammo_subtract_item)

        window.destroy()

    for i in range(3):
        option_text = f"Option {i + 1}: Add {ammo_to_add} ammo to {options[i][0]}" + (f" (Subtracting {subtract_amount} from {subtract_item})" if subtract_item else "")
        button = tk.Button(window, text=option_text, command=lambda option=i: on_button_click(option))
        button.pack(pady=5)

    for item, count in current_inventory.items():
        label_text = f"{item}: {count} ammo"
        label = tk.Label(window, text=label_text)
        label.pack()

    window.mainloop()

saved_inventory = {}

def reset_high_inventory_counts(pid):
    global saved_inventory
    for item, addresses in items.items():
        current_count = read_from_memory(pid, addresses)
        if current_count > 1000 and item in saved_inventory:
            write_to_memory(pid, addresses, saved_inventory[item])

def check_inventory_changes(pid):
    global saved_inventory
    current_inventory = {item: read_from_memory(pid, addr) or 0 for item, addr in items.items()}
    for item, ammo in current_inventory.items():
        if ammo <= 0 and saved_inventory.get(item, 0) > 0:
            if not saved_inventory:
                saved_inventory = current_inventory
            return True
    return False

def apply_selection_and_restore(pid, item, ammo_to_add):
    global saved_inventory
    if item in saved_inventory and ammo_to_add > 0:
        saved_inventory[item] += ammo_to_add
        for item, ammo in saved_inventory.items():
            if ammo > 0:
                write_to_memory(pid, items[item], ammo)

def check_and_revert_specific_values(pid):
    trigger_values = {
        "Famas": 500,
        "Grenades": 100,
        "Nikita": 100,
        "PSG1": 150,
        "Stinger": 100,
        "Socom": 100,
        "C4": 50,
    }

    for item, trigger_value in trigger_values.items():
        current_count = read_from_memory(pid, items[item])
        if current_count == trigger_value:
            reduced_value = int(trigger_value * 0.15)
            write_to_memory(pid, items[item], reduced_value)

def start_application():
    global saved_inventory
    saved_inventory = {item: 0 for item in items.keys()}
    window = tk.Tk()
    window.title("Game Mod")

    pid_var = tk.IntVar(value=0)

    tk.Label(window, text="Enter the PID of the game emulator: [Task Manager - Details - PID # of emulator]").pack(pady=10)
    pid_entry = tk.Entry(window)
    pid_entry.pack(pady=5)

    submit_button = tk.Button(window, text="Submit", command=lambda: get_process_id(window, pid_var, pid_entry))
    submit_button.pack(pady=10)

    window.mainloop()

    pid = pid_var.get()
    if pid > 0:
        run_game_mod(pid)

def run_game_mod(pid):
    def game_mod_loop():
        while True:
            update_saved_inventory(pid)
            check_and_revert_specific_values(pid)
            reset_high_inventory_counts(pid)
            inventory = {item: read_from_memory(pid, addr) or 0 for item, addr in items.items()}
            present_options(pid, inventory)
            time.sleep(0.5)

    Thread(target=game_mod_loop).start()

def main():
    pid = get_process_id()
    while True:
        inventory = {item: read_from_memory(pid, addr) or 0 for item, addr in items.items()}
        present_options(pid, inventory)
        time.sleep(0.5)

if __name__ == "__main__":
    start_application()
