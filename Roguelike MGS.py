import ctypes
import time
import random
import PySimpleGUI as sg

items = {
    "Socom": [0x300B2A1A, 0x302B2A1A, 0x304B2A1A, 0x306B2A1A],
    "C4": [0x306B2A26, 0x302B2A26, 0x304B2A26, 0x306B2A26],
    "Famas": [0x300B2A1C, 0x302B2A1C, 0x304B2A1C, 0x306B2A1C],
    "Grenades": [0x300B2A1E, 0x302B2A1E, 0x304B2A1E, 0x306B2A1E],
    "Claymore": [0x300B2A24, 0x302B2A24, 0x304B2A24, 0x306B2A24],
    "Nikita": [0x300B2A20, 0x302B2A20, 0x304B2A20, 0x306B2A20],
    "PSG1": [0x300B2A2C, 0x302B2A2C, 0x304B2A2C, 0x306B2A2C],
    "Stinger": [0x300B2A22, 0x302B2A22, 0x304B2A22, 0x306B2A22],
    "Stun": [0x300B2A28, 0x302B2A28, 0x304B2A28, 0x306B2A28]
}

players_inventory = {
    "Socom": 10,
    "C4": 10,
    "Famas": 10,
    "Grenades": 10,
    "Claymore": 10,
    "Nikita": 10,
    "PGS1": 10,
    "Stinger": 10,
    "Stun": 10
}

def write_to_memory(process_id, addresses, data):
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    process_handle = kernel32.OpenProcess(0x1F0FFF, False, process_id)
    if process_handle:
        data_c = ctypes.c_int(data)
        for address in addresses:
            success = kernel32.WriteProcessMemory(process_handle, address, ctypes.byref(data_c), ctypes.sizeof(data_c), None)
        kernel32.CloseHandle(process_handle)

def generate_random_ammo():
    return random.randint(2, 10)

def generate_random_subtraction(ammo_to_add):
    min_subtract = max(1, ammo_to_add - 2)
    max_subtract = ammo_to_add + 2
    return random.randint(min_subtract, max_subtract)

def read_from_memory(process_id, addresses, data_type=ctypes.c_int):
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    process_handle = kernel32.OpenProcess(0x0010, False, process_id)
    if process_handle:
        data_c = data_type()
        bytes_read = ctypes.c_size_t()
        success = kernel32.ReadProcessMemory(process_handle, addresses[0], ctypes.byref(data_c), ctypes.sizeof(data_c), ctypes.byref(bytes_read))
        kernel32.CloseHandle(process_handle)
        if success and bytes_read.value > 0:
            return data_c.value

def get_process_id():
    layout = [[sg.Text('Enter the PID of the game emulator: [Task Manager - Details - PID # of emulator]')], [sg.InputText()], [sg.Submit()]]
    window = sg.Window('Game Mod', layout)
    event, values = window.read()
    window.close()
    return int(values[0])

def present_options(pid, inventory):
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

    layout = [
        [sg.Text(f"Option {i+1}: Add {ammo_to_add} ammo to {options[i][0]}" + (f" (Subtracting {subtract_amount} from {subtract_item})" if subtract_item else ""))]
        for i in range(3)
    ] + [[sg.Button("Option 1"), sg.Button("Option 2"), sg.Button("Option 3")]]
    window = sg.Window("Choose an Option", layout)
    event, values = window.read()
    window.close()
    if event in ["Option 1", "Option 2", "Option 3"]:
        chosen_option = int(event.split(' ')[1]) - 1
        chosen_item = options[chosen_option][0]
        inventory[chosen_item] += ammo_to_add
        if subtract_item:
            inventory[subtract_item] = max(0, inventory[subtract_item] - subtract_amount)
        write_to_memory(pid, items[chosen_item], inventory[chosen_item])
        if subtract_item:
            write_to_memory(pid, items[subtract_item], inventory[subtract_item])


saved_inventory = {}

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
    saved_inventory[item] += ammo_to_add
    for item, ammo in saved_inventory.items():
        write_to_memory(pid, items[item], ammo)
    saved_inventory = {}

def main():
    pid = get_process_id()
    while True:
        inventory = {item: read_from_memory(pid, addr) or 0 for item, addr in items.items()}
        present_options(pid, inventory)
        time.sleep(0.5)

if __name__ == "__main__":
    main()
