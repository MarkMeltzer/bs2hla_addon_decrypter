from os import system
import os
import zipfile
import tkinter as tkin
import tkinter.scrolledtext as st
from tkinter import font
import time
from pathlib import Path
import threading

# Used to allow pyinstaller to find resource files from a relative path
# src: https://stackoverflow.com/a/13790741/
def resource_path(relative):
    return os.path.join(
        os.environ.get(
            "_MEIPASS2",
            os.path.abspath(".")
        ),
        relative
    )

def print_to_textbox(s, textbox):
    textbox.configure(state='normal')
    textbox.insert(tkin.END, s+"\n")
    textbox.configure(state='disabled')
    textbox.see(tkin.END)
    window.update_idletasks()

def decrypt():
    # Get the Bioshock root path and addon zip path
    Bioshock_root_path = Path(Bioshock_root_path_entry.get().strip())
    addon_zip_path = Path(addon_zip_path_entry.get().strip())
    HLA_root_path = Path(HLA_root_path_entry.get().strip())
    if not Bioshock_root_path.is_dir():
        print_to_textbox(f"{Bioshock_root_path} cannot be found, try again.",output)
        return 1
    if not HLA_root_path.is_dir():
        print_to_textbox(f"{HLA_root_path} cannot be found, try again.",output)
        return 1
    if not addon_zip_path.is_file():
        print_to_textbox(f"{addon_zip_path} cannot be found or is not a file, try again.",output)
        return 1

    # load the bioshock assets
    print_to_textbox("Loading Bioshock assets...", output)
    try:
        with open(Bioshock_root_path / "Content" / "BulkContent" / "1-medicalLevel.blk", 'rb') as bulkfile, open(Bioshock_root_path / "Content" / "Maps" / "1-Medical.bsm", 'rb') as mapfile:
            assets = bytearray(bulkfile.read()) + bytearray(mapfile.read())
            assets_size = len(assets)
            print_to_textbox(f"Bioshock assets loaded! Size: {(assets_size / 1000000):.2f}mb", output)
    except Exception as e:
        print_to_textbox("Could not load Bioshock assets.", output)
        print_to_textbox(str(e), output)
        return 1

    # load the addon zip
    print_to_textbox("Loading addon zip...", output)
    try:
        with open(addon_zip_path, 'rb') as addon_zip_file:
            addon_zip = bytearray(addon_zip_file.read())
            addon_zip_size = len(addon_zip)
            print_to_textbox(f"Addon zip loaded! Size: {(addon_zip_size / 1000000):.2f}mb", output)
    except Exception as e:
        print_to_textbox("Could not load the addon zip.", output)
        print_to_textbox(str(e), output)
        return 1

    # decrypt addon by XOR-ing the addon zip with the asset files
    print_to_textbox("Decrypting addon....", output)
    decrypted_addon_zip = bytearray(addon_zip_size)
    start_time = time.time()

    def decrypt_addon_start():
        for i in range(addon_zip_size):
            if i >= len(assets):
                # if assets are smaller than addon zip, pad the assets with 0 bits
                decrypted_addon_zip[i] = 0 ^ addon_zip[i]
            else:
                decrypted_addon_zip[i] = assets[i] ^ addon_zip[i]

            # print progress
            if i % 10000000 == 0:
                print_to_textbox(f"{(i / addon_zip_size * 100):.2f}% done", output)

        print_to_textbox(f"Addon decrypted! Decryption took {time.time() - start_time:.1f} seconds.", output)
        decrypt_addon_finish()

    def decrypt_addon_finish():
        addon_folder = str(HLA_root_path.resolve()) + "\game\hlvr_addons"
        # Save the decrypted addon
        print_to_textbox("Saving addon....", output)
        try:
            with open(addon_zip_path, 'wb') as addon_zip_file:
                addon_zip_file.write(decrypted_addon_zip)
            if not os.path.exists(addon_folder):
                os.makedirs(addon_folder)
            with zipfile.ZipFile(addon_zip_path, 'r') as zip_ref:
                zip_ref.extractall(addon_folder)
        except Exception as e:
            print_to_textbox("Could not save addon.", output)
            print_to_textbox(str(addon_zip_path), output)
            print_to_textbox(str(addon_folder), output)
            print_to_textbox(str(e), output)
            return 1
        print_to_textbox("Decrypted addon saved!", output)
        print_to_textbox("All done!", output)

        # re-enable the button
        decrypt_button['state'] = tkin.NORMAL

    # do the decryption on a different thread from the GUI thread
    XOR_tread = threading.Thread(target=decrypt_addon_start)
    XOR_tread.start()
    decrypt_button['state'] = tkin.DISABLED

# Create tkiner window
window = tkin.Tk()
window.title("BS2HLA Medical Pavilion addon decrypter")
try:
    window.iconbitmap(resource_path('icon.ico'))
except:
    # no icon? no big deal
    pass
window.geometry("670x501")
window.resizable(0,0)

# Input text fields
Bioshock_root_path_entry_label = tkin.Label(window, text="BioShock installation root folder: ")
Bioshock_root_path_entry_label.grid(row=0, sticky=tkin.W, pady=7, ipadx=5)
Bioshock_root_path_entry = tkin.Entry(window, width=75)
Bioshock_root_path_entry.grid(row=0, column=1)

addon_zip_path_entry_label = tkin.Label(window, text='The encrypted addon zip file: ')
addon_zip_path_entry_label.grid(row=1, sticky=tkin.W, ipadx=5)
addon_zip_path_entry = tkin.Entry(window, width=75)
addon_zip_path_entry.grid(row=1, column=1)

HLA_root_path_entry_label = tkin.Label(window, text='HLA installation root folder: ')
HLA_root_path_entry_label.grid(row=2, sticky=tkin.W, ipadx=5)
HLA_root_path_entry = tkin.Entry(window, width=75)
HLA_root_path_entry.grid(row=2, column=1)

# button
decrypt_button = tkin.Button(window, text="Decrypt!", command=decrypt, font=font.Font(size=12))
decrypt_button.grid(row=3, columnspan=2, pady=10)

# Text output
output = st.ScrolledText(window, wrap=tkin.WORD, bg="black", fg="#e8e8e8")
output.grid(row=4, columnspan=2, padx=5)
output.configure(state='disabled')

window.mainloop()