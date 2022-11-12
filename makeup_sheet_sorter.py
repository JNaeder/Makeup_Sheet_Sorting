import dateutil.parser
from google.cloud import vision
from google.oauth2 import service_account
import io
import os
import platform
from dateutil import parser
import time
from bcolors import *
from vertex_helper import get_bounding_range, check_vertices


class Makeup_Sheet_Sorter:
    def __init__(self, image_folder_path, output_folder_path):
        # Google Vision Stuff
        self._credentials = service_account.Credentials.from_service_account_file("google_credentials.json")
        self._client = vision.ImageAnnotatorClient(credentials=self._credentials)
        self._annotated_text = None

        # File Path Stuff
        self._image_folder_path = image_folder_path
        self._the_images = os.listdir(self._image_folder_path)
        self._output_folder = output_folder_path

        # Tweak these things
        self._confidence_threshold = 0.7
        self._word_buffer = 50

    def main(self):
        """
        Main function that loops through all the files in the folder and processes them. Also calculates the
        statistics and the print the statements in the output.
        """

        print(bcolors.OKGREEN + "\n-------------------------STARTING-------------------------" + bcolors.ENDC)

        # Start the performance timer
        start_time = time.perf_counter()

        # Initialize counters
        total_files = len(self._the_images)
        total_sort_success = 0

        # Loop through every file in the RAW Google Drive folder
        for file in self._the_images:

            # Create a content variable with the binary information of the image
            full_file_path = os.path.join(self._image_folder_path, file)
            with io.open(full_file_path, "rb") as image_file:
                content = image_file.read()

            # Sends the image to the Google Cloud Vision API. Gets back response text.
            image = vision.Image(content=content)
            response = self._client.document_text_detection(image=image)
            self._annotated_text = response.full_text_annotation

            # Parse through the text to get the Student Name and the Date of Session
            student_name = " ".join([word.title() for word in self.parse_text_for_key("Student Name")])
            date_of_session = self.parse_text_for_key("Date of Session")[0]
            if student_name != "---Unsorted---":
                total_sort_success += 1

            # Create a new makeup sheet object, and run the process method on it
            makeup_sheet = Makeup_Sheet(student_name, date_of_session, file, self._image_folder_path,
                                        self._output_folder)
            makeup_sheet.process_file()

        # If there are files, calculate success rate and print the results
        if total_files != 0:
            success_rate = round(total_sort_success / total_files, 4)
            print(bcolors.WARNING + f"[Total Files: {total_files}] [Successful: {total_sort_success}] "
                                    f"[Success Rate: {success_rate * 100}%]" + bcolors.ENDC)

        #  End the performance timer
        total_time = time.perf_counter() - start_time

        print(bcolors.WARNING + f"Finished in {round(total_time, 2)} seconds.")
        print(bcolors.OKGREEN + "-------------------------COMPLETE-------------------------" + bcolors.ENDC)

    def parse_text_for_key(self, the_key):
        for page in self._annotated_text.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    paragraph_text = ""
                    for word in paragraph.words:
                        word_text = ''.join([symbol.text for symbol in word.symbols])
                        paragraph_text += word_text + " "
                    if the_key in paragraph_text:
                        if the_key == "Student Name":
                            bounding_box = get_bounding_range(paragraph.bounding_box.vertices)
                            return self.get_the_value(bounding_box)
                        elif the_key == "Date of Session":
                            bounding_box = get_bounding_range(paragraph.bounding_box.vertices)
                            return self.get_the_value(bounding_box)

    def get_the_value(self, vertices):
        output = []
        total_confidence = 0
        total_word_count = 0
        for page in self._annotated_text.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        word_text = ''.join([symbol.text for symbol in word.symbols])
                        if check_vertices(word.bounding_box.vertices, vertices, self._word_buffer):
                            output.append(word_text)
                            total_confidence += word.confidence
                            total_word_count += 1
        confidence = total_confidence / total_word_count
        if confidence >= self._confidence_threshold:
            return output
        else:
            return ["---Unsorted---"]


class Makeup_Sheet:
    def __init__(self, student_name, date_of_session, the_file, old_folder_path, new_folder_path):
        """
        TODO: Get the file extension
        """
        self._student_name = student_name
        self._date_of_session = date_of_session
        self._the_file = the_file
        self._old_folder_path = old_folder_path
        self._new_folder_path = new_folder_path

    def process_file(self):
        try:
            the_date = parser.parse(self._date_of_session).strftime("%Y-%m-%d")
        except dateutil.parser.ParserError:
            the_date = "--Undated"
        original_file = self._old_folder_path + "/" + self._the_file
        new_path = self._new_folder_path + "/" + self._student_name
        if self._student_name == "---Unsorted---":
            new_file_name = self._the_file
            print(bcolors.FAIL + f"Failed to sort {self._the_file}. Moved to unsorted folder.")
        else:
            new_file_name = self._student_name + " (" + the_date + ")"
            print(bcolors.ENDC + f"Successfully sorted makeup sheet: {bcolors.OKCYAN}{new_file_name}" + bcolors.ENDC)
        new_file = new_path + "/" + new_file_name
        if not os.path.exists(new_path):
            os.makedirs(new_path)
        os.rename(original_file, new_file)


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

    # Start Sorter
    makeup_sheet_sorter = Makeup_Sheet_Sorter(raw_folder, sorted_folder)
    makeup_sheet_sorter.main()
