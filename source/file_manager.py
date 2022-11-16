import os
from PyPDF2 import PdfFileReader, PdfFileWriter


class File_Manager:
    def __init__(self, input_folder_path, output_folder_path):
        self._input_folder_path = input_folder_path
        self._the_images = os.listdir(self._input_folder_path)

    def pdf_splitter(self, pdf_file_path, file):
        file_name = file.split(".")[0]
        output_list = []
        pdf = PdfFileReader(pdf_file_path)
        file_index = 0
        for i in range(0, pdf.getNumPages(), 2):
            pdf_writer = PdfFileWriter()
            pdf_writer.addPage(pdf.getPage(i))
            pdf_writer.addPage(pdf.getPage(i + 1))

            output_file_name = f"{file_name}-{file_index}.pdf"
            file_index += 1
            full_output_path = self._input_folder_path + "/" + output_file_name
            with open(full_output_path, "wb") as output:
                pdf_writer.write(output)
                output_list.append(output_file_name)

    #   Delete the original file
        os.remove(pdf_file_path)
    #   Return the names of the new files
        return output_list

    def get_all_files(self):
        output = []
        all_files = os.listdir(self._input_folder_path)
        for file in all_files:
            output.append(file)
        return output

