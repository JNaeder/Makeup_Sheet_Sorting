import dateutil.parser
from google.cloud import vision
from google.oauth2 import service_account
import io
import os
from dateutil import parser
import time
from bcolors import *


class Makeup_Sheet_Sorter:
    def __init__(self, image_folder_path, output_folder_path):
        self._credentials = service_account.Credentials.from_service_account_file("google_credentials.json")
        self._client = vision.ImageAnnotatorClient(credentials=self._credentials)
        self._image_folder_path = image_folder_path
        self._the_images = os.listdir(self._image_folder_path)
        self._output_folder = output_folder_path

    def main(self):
        print(bcolors.OKGREEN + "\n-------------------------STARTING-------------------------" + bcolors.ENDC)
        start_time = time.perf_counter()
        total_files = len(self._the_images)
        total_sort_success = 0
        for file in self._the_images:
            full_file_path = os.path.join(self._image_folder_path, file)
            with io.open(full_file_path, "rb") as image_file:
                content = image_file.read()

            image = vision.Image(content=content)
            response = self._client.document_text_detection(image=image)

            annotated_text = response.full_text_annotation
            student_name = self.parse_text_for_key(annotated_text, "Student Name")
            if student_name != "---Unsorted---":
                total_sort_success += 1
            date_of_session = self.parse_text_for_key(annotated_text, "Date of Session")
            makeup_sheet = Makeup_Sheet(student_name, date_of_session, file, self._image_folder_path,
                                        self._output_folder)
            makeup_sheet.process_file()
        if total_files != 0:
            success_rate = round(total_sort_success / total_files, 2)
            print(bcolors.WARNING + f"[Total Files: {total_files}] [Successful: {total_sort_success}] "
                                    f"[Success Rate: {success_rate}]" + bcolors.ENDC)
        total_time = time.perf_counter() - start_time
        print(bcolors.WARNING + f"Finished in {round(total_time, 2)} seconds.")
        print(bcolors.OKGREEN + "-------------------------COMPLETE-------------------------" + bcolors.ENDC)

    def check_vertices(self, list_of_verts, bounding_box):
        up = bounding_box[0]
        down = bounding_box[2]
        right = bounding_box[1]
        buffer = 50
        check_box = self.get_bounding_average(list_of_verts)
        check_y = check_box[1]
        check_x = check_box[0]
        if right + buffer < check_x:
            if up <= check_y:
                if down + buffer >= check_y:
                    return True
        return False

    @staticmethod
    def get_bounding_range(vertices):
        left = 100000
        right = 0
        up = 100000
        down = 0
        for vertex in vertices:
            x_value = vertex.x
            y_value = vertex.y
            if x_value > right:
                right = x_value
            if x_value < left:
                left = x_value
            if y_value < up:
                up = y_value
            if y_value > down:
                down = y_value
        return [up, right, down, left]

    def get_bounding_average(self, vertices):
        bounding_box = self.get_bounding_range(vertices)
        average_x = (bounding_box[1] + bounding_box[3]) / 2
        average_y = (bounding_box[0] + bounding_box[2]) / 2
        return [average_x, average_y]

    def parse_text_for_key(self, the_annotated_text, the_key):
        for page in the_annotated_text.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    paragraph_text = ""
                    for word in paragraph.words:
                        word_text = ''.join([symbol.text for symbol in word.symbols])
                        paragraph_text += word_text + " "
                    if the_key in paragraph_text:
                        if the_key == "Student Name":
                            bounding_box = self.get_bounding_range(paragraph.bounding_box.vertices)
                            return self.get_the_name(the_annotated_text, bounding_box)
                        elif the_key == "Date of Session":
                            bounding_box = self.get_bounding_range(paragraph.bounding_box.vertices)
                            return self.get_the_date(the_annotated_text, bounding_box)

    def get_the_name(self, the_annotated_text, vertices):
        output = []
        total_confidence = 0
        total_word_count = 0
        for page in the_annotated_text.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        word_text = ''.join([symbol.text for symbol in word.symbols])
                        if self.check_vertices(word.bounding_box.vertices, vertices):
                            output.append(word_text)
                            total_confidence += word.confidence
                            total_word_count += 1
        confidence = total_confidence / total_word_count
        if confidence >= 0.7:
            full_name = output[1].title() + "_" + output[0].title()
            return full_name
        else:
            return "---Unsorted---"

    def get_the_date(self, the_annotated_text, vertices):
        output = []
        total_confidence = 0
        total_word_count = 0
        for page in the_annotated_text.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        word_text = ''.join([symbol.text for symbol in word.symbols])
                        if self.check_vertices(word.bounding_box.vertices, vertices):
                            output.append(word_text)
                            total_confidence += word.confidence
                            total_word_count += 1
        confidence = total_confidence / total_word_count
        if confidence >= 0.7:
            return output[0]
        else:
            return ""


class Makeup_Sheet:
    def __init__(self, student_name, date_of_session, the_file, old_folder_path, new_folder_path):
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
    # --- Mac File Path ---
    # raw_folder = "/Users/johnnaeder/Google Drive/Shared drives/NY Tech Drive/Makeup Sheets Stuff/RAW"
    # sorted_folder = "/Users/johnnaeder/Google Drive/Shared drives/NY Tech Drive/Makeup Sheets Stuff/SORTED"

    # --- Windows File Path ---
    raw_folder = "G:/Shared drives/NY Tech Drive/Makeup Sheets Stuff/RAW"
    sorted_folder = "G:/Shared drives/NY Tech Drive/Makeup Sheets Stuff/SORTED"

    # Start Sorter
    muss = Makeup_Sheet_Sorter(raw_folder, sorted_folder)
    muss.main()
