import platform
import time
from file_manager import File_Manager
from bcolors import bcolors
from pdf_extractor import PDF_Extractor, Makeup_Sheet
from google_cloud_manager import Google_Cloud_Manager

if __name__ == "__main__":

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

    # Create instances of the classes
    file_manager = File_Manager(raw_folder, sorted_folder)
    makeup_sheet_sorter = PDF_Extractor()
    google_cloud_manager = Google_Cloud_Manager()

    # Get all the PDFs in the raw folder
    raw_files = file_manager.get_all_files()

    print(bcolors.OKGREEN + "------------------------Starting--------------------------" + bcolors.ENDC)

    total_start_time = time.perf_counter()
    total_files = 0
    total_files_fail = 0


    # Process each one
    for file in raw_files:
        full_path = raw_folder + "/" + file

        # 1) Upload the full PDF to the GCS Bucket
        google_cloud_manager.pdf_uploader(full_path, file)
        print(bcolors.HEADER + f"Uploaded {file}" + bcolors.ENDC)

        # 2) Analyze PDF pages and get text annotation
        print(bcolors.OKGREEN + "Starting Analyzing Process....." + bcolors.ENDC)
        analyze_start_time = time.perf_counter()
        annotation_list = google_cloud_manager.pdf_analyzer(file)
        analyze_finish_time = time.perf_counter() - analyze_start_time
        print(bcolors.OKGREEN + f"Finished analyzing in {round(analyze_finish_time, 4)} seconds." + bcolors.ENDC)

        # 3) Feed list to analyzer to get Names and Dates
        # 4) Return outputs as a list of objects with info
        name_date_list = []
        for annotation in annotation_list:
            name_date_list.append(makeup_sheet_sorter.get_name_date_object(annotation))

        # 5) Split the original PDF into separate pdfs
        list_of_split_files = file_manager.pdf_splitter(full_path, file)
        total_files += len(list_of_split_files)
        total_files_fail += len([file for file in name_date_list if file["name"] == "---Unsorted---"])

        # 6) Go through PDFs and rename by the output
        for i in range(len(list_of_split_files)):
            new_sheet = Makeup_Sheet(name_date_list[i], list_of_split_files[i], raw_folder, sorted_folder)
            new_sheet.process_file()

        # 7) Delete the files in the bucket
        google_cloud_manager.delete_pdfs_from_buckets()

    total_files_success = total_files - total_files_fail
    if total_files > 0:
        success_percentage = round(((total_files_success / total_files) * 100), 2)
        print(bcolors.WARNING + f"[Total Files: {total_files}] [Success: {total_files_success}] [Fail: {total_files_fail}] [{success_percentage}%]" + bcolors.ENDC)
    print(bcolors.OKGREEN + "------------------------Finished--------------------------" + bcolors.ENDC)



