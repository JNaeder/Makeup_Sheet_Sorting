import dateutil.parser
import os
from dateutil import parser
from source.bcolors import *
from source.vertex_helper import get_bounding_range, check_vertices


class PDF_Extractor:
    """
    The master class that finds images in a path, sense them to the Google Vision API, and parses the data back
    """
    def __init__(self):

        self._annotated_text = None
        self._width = None
        self._height = None

        # Tweak these things
        self._confidence_threshold = 0.7
        self._word_buffer = 20

    def get_name_date_object(self, text_annotation):
        self._annotated_text = text_annotation
        self._width = self._annotated_text["pages"][0]["width"]
        self._height = self._annotated_text["pages"][0]["height"]
        student_name_list = self.parse_text_for_key("Student Name")
        date_of_session_list = self.parse_text_for_key("Date of Session")

        if date_of_session_list:
            try:
                date_of_session = parser.parse(date_of_session_list[0]).strftime("%Y-%m-%d")
            except dateutil.parser.ParserError:
                date_of_session = "--Undated--"
        else:
            date_of_session = "--Undated--"

        if student_name_list:
            if len(student_name_list) > 1:
                student_name = " ".join(student_name_list[1:]) + ", " + student_name_list[0]
            else:
                student_name = student_name_list[0]
        else:
            student_name = "---Unsorted---"

        name_date_object = {
            "name": student_name.title(),
            "date": date_of_session
        }
        return name_date_object

    def parse_text_for_key(self, the_key):
        """
        Searches through all the text to find a keyword. Creates a bounding box for that keyword,
        then calls the method to find the value associated with that keyword.
        """
        for page in self._annotated_text["pages"]:
            for block in page["blocks"]:
                for paragraph in block["paragraphs"]:
                    paragraph_text = ""
                    for word in paragraph["words"]:
                        word_text = ''.join([symbol["text"] for symbol in word["symbols"]])
                        paragraph_text += word_text + " "
                    if the_key in paragraph_text:
                        bounding_box = get_bounding_range(paragraph["boundingBox"]["normalizedVertices"],
                                                          self._height, self._width)
                        return self.get_the_value(bounding_box)

    def get_the_value(self, vertices):
        """
        Searches through all the text to find the value that is associated with the given vertices.
        """
        output = []
        total_confidence = 0
        total_word_count = 0
        for page in self._annotated_text["pages"]:
            for block in page["blocks"]:
                for paragraph in block["paragraphs"]:
                    for word in paragraph["words"]:
                        word_text = ''.join([symbol["text"] for symbol in word["symbols"]])
                        if check_vertices(word["boundingBox"]["normalizedVertices"], vertices, self._word_buffer,
                                          self._height, self._width):
                            output.append(word_text)
                            total_confidence += word["confidence"]
                            total_word_count += 1
        if total_word_count <= 0:
            return ["---Unsorted---"]
        confidence = total_confidence / total_word_count
        # print(bcolors.HEADER, output, "Confidence:", confidence, bcolors.ENDC)
        if confidence >= self._confidence_threshold:
            return output
        else:
            return ["---Unsorted---"]


class Makeup_Sheet:
    """
    A class for a makeup sheet. Takes makeup sheet info and folder locations.
    Is responsible for moving and renaming the files.
    """
    def __init__(self, name_date_object, the_file, old_folder_path, new_folder_path):
        self._student_name = name_date_object["name"].replace("/", "")
        self._date_of_session = name_date_object["date"]
        self._the_file = the_file
        self._file_extension = self._the_file.split(".")[1]
        self._old_folder_path = old_folder_path
        self._new_folder_path = new_folder_path

    def process_file(self):
        """Takes all the information from the class to move and rename the file."""

        # Tries to turn the date of session into a datetime object, and then converts it into a normalized string.
        try:
            the_date = parser.parse(self._date_of_session).strftime("%Y-%m-%d")
        except dateutil.parser.ParserError:
            the_date = "--Undated--"

        # Gets the full path of the original file.
        original_file = self._old_folder_path + "/" + self._the_file

        # Gets the path to the folder the new file will go into.
        new_path = self._new_folder_path + "/" + self._student_name

        # Set the new file name. If no name can be found, keep the original file name.
        if self._student_name == "---Unsorted---":
            new_file_name = self._the_file
            print(bcolors.FAIL + f"Failed to sort {self._the_file}. Moved to unsorted folder." + bcolors.ENDC)
        else:
            new_file_name = self._student_name + " (" + the_date + ")" + "." + self._file_extension
            print(bcolors.ENDC + f"Successfully sorted makeup sheet: {bcolors.OKCYAN}{new_file_name}" + bcolors.ENDC)

        # Create full path for the new file
        new_file = new_path + "/" + new_file_name

        # Check if file name already exists, add a number to the end of it
        file_exists = os.path.isfile(new_file)
        file_suffix_num = 0
        while file_exists:
            file_suffix_num += 1
            new_file_name = self._student_name + " (" + the_date + ")" + f" -({str(file_suffix_num)})" + "." + self._file_extension
            new_file = new_path + "/" + new_file_name
            file_exists = os.path.isfile(new_file)


        # Check if the folder already exists. If it doesn't, create one.
        if not os.path.exists(new_path):
            os.makedirs(new_path)

        # Move the file from old path to the new path.
        os.rename(original_file, new_file)

