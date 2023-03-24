import platform
import os


# Get the Operating System that I am running
the_os = platform.system()

# --- Mac File Path ---
if the_os == "Darwin":
    raw_folder = "/Users/johnnaeder/Google Drive/Shared drives/NY Tech Drive/Makeup Sheets Stuff/RAW"
    sorted_folder = "/Users/johnnaeder/Google Drive/Shared drives/NY Tech Drive/Makeup Sheets Stuff/SORTED"

# --- Windows File Path ---
else:
    raw_folder = "G:/Shared drives/NY Tech Drive/Makeup Sheets Stuff/RAW"
    sorted_folder = "G:/Shared drives/NY Tech Drive/Makeup Sheets Stuff/SORTED"


def count_sorted_files():
    count = 0
    folders = os.listdir(sorted_folder)
    for folder in folders:
        files_in_folder = os.listdir(f"{sorted_folder}/{folder}")
        count += len(files_in_folder)
    print("Total: ", count)

    unsorted = len(os.listdir(f"{sorted_folder}/---Unsorted---"))
    print("Unsorted: ", unsorted)

    print("Successful: %", round(((count - unsorted) / count) * 100, 2))


count_sorted_files()
