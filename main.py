import platform
from file_manager import File_Manager
from makeup_sheet_sorter import Makeup_Sheet_Sorter, Makeup_Sheet
from pdf_analyzer import PDF_Manager

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

    # Create instances of classes
    file_manager = File_Manager(raw_folder, sorted_folder)
    makeup_sheet_sorter = Makeup_Sheet_Sorter()
    pdf_analyzer = PDF_Manager()

    # Get all the PDFs in the raw folder
    raw_files = file_manager.get_all_files()

    # Process each one
    for file in raw_files:
        full_path = raw_folder + "/" + file

        # 1) Upload the full PDF to the GCS Bucket
        pdf_analyzer.pdf_uploader(full_path, file)

        # 2) Analyze PDF pages and get text annotation
        annotation_list = pdf_analyzer.pdf_analyzer(file)

        # 3) Feed list to analyzer to get Names and Dates
        # 4) Return outputs as a list of objects with info
        name_date_list = []
        for annotation in annotation_list:
            name_date_list.append(makeup_sheet_sorter.get_name_date_object(annotation))

        # 5) Split the original PDF into separate pdfs
        list_of_split_files = file_manager.pdf_splitter(full_path, file)

        # 6) Go through PDFs and rename by the output
        for i in range(len(list_of_split_files)):
            new_sheet = Makeup_Sheet(name_date_list[i], list_of_split_files[i], raw_folder, sorted_folder)
            new_sheet.process_file()

        # 7) Delete the files in the bucket
        pdf_analyzer.delete_pdfs_from_buckets()



