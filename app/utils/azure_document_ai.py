import pathlib
import sys

try:
    FILE = pathlib.Path(__file__)
except NameError:
    FILE = pathlib.Path("azure_document_ai.py")
BASE_ABSOLUTE = FILE.absolute().parent.parent.parent
if BASE_ABSOLUTE.absolute().as_posix() not in sys.path:
    sys.path.append(BASE_ABSOLUTE.absolute().as_posix())

from collections import defaultdict

import azure
import pandas as pd


__all__ = ["parse_document_ai_object"]


class AzureDocumentAI:
    def __init__(self, line_dataframe, word_dataframe, azure_result, document_id=None):
        self.line_dataframe = line_dataframe
        self.word_dataframe = word_dataframe
        if document_id is None:
            document_id = azure_result.get("document_id")
        self.document_id = document_id
        # Check if azure_result is of type dict
        if isinstance(azure_result, dict):
            self.azure_result = azure_result
        else:
            # Handle the case where azure_result is not a dict
            raise TypeError("azure_result should be a dictionary")


class OCRCoordinates:
    def __init__(
        self,
        top_left_x: float = None,
        top_left_y: float = None,
        top_right_x: float = None,
        top_right_y: float = None,
        bottom_right_x: float = None,
        bottom_right_y: float = None,
        bottom_left_x: float = None,
        bottom_left_y: float = None,
    ):
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y
        self.top_right_x = top_right_x
        self.top_right_y = top_right_y
        self.bottom_right_x = bottom_right_x
        self.bottom_right_y = bottom_right_y
        self.bottom_left_x = bottom_left_x
        self.bottom_left_y = bottom_left_y


def get_increasing_sequence(lst):
    count = 1
    seq = []
    prev_item = lst and lst[0]
    for item in lst:
        if prev_item != item:
            count += 1
        seq.append(count)
        prev_item = item
    return seq


def dict_to_class(class_name, dictionary):
    # Define a new class
    new_class = type(class_name, (), {})

    # Set attributes based on dictionary keys and values
    for key, value in dictionary.items():
        setattr(new_class, key, value)

    return new_class


def azure_doc_ai_parser(result):
    """
    A function which parsers encoded response and create dataframes.

    Parameters
    ----------
    result : azure.ai.formrecognizer._models.AnalyzeResult
        A dataclass of RespJson.

    Returns
    -------
    line_dataframe : pd.DataFrame
        Dataframe containing information of  OCR lines.
    word_dataframe : pd.DataFrame
        Dataframe containing information of OCR words.
    selection_mark_dataframe : pd.DataFrame
        Dataframe containing information of OCR selection marks.

    """
    
    # Rotation-aware sorting
    def sort_rotated(df):
        sorted_dfs = []
        for angle in df["angle"].unique():
            page_df = df[df["angle"] == angle]
            if 80 < abs(angle) < 100:  # ~90 degrees
                sorted_df = page_df.sort_values(by=["page", "bottom_left_x", "bottom_left_y"])
            elif 170 < abs(angle) < 190:  # ~180 degrees
                sorted_df = page_df.sort_values(by=["page", "bottom_left_y", "bottom_left_x"], ascending=[False, False])
            elif 260 < abs(angle) < 280:  # ~270 degrees
                sorted_df = page_df.sort_values(by=["page", "bottom_left_x"], ascending=False)
            else:  # 0 or unknown
                sorted_df = page_df.sort_values(by=["page", "bottom_left_y", "bottom_left_x"])
            sorted_dfs.append(sorted_df)
        return pd.concat(sorted_dfs, ignore_index=True)

    if isinstance(result, azure.ai.documentintelligence.models._models.AnalyzeResult):
        try:
            result_dict = result.to_dict()
        except AttributeError:
            result_dict = result.as_dict()
    else:
        result_dict = result
    read_results = result_dict.get("pages")

    # Lines and words
    line_ocr_coordinates_dictionary = defaultdict(list)
    line_ocr_texts = []
    line_pages = []
    line_angles = []
    line_widths = []
    line_heights = []
    line_units = []
    line_numbers = []
    line_offsets = []
    line_lengths = []
    line_contents = []
    line_page_offsets_lst = []
    line_page_lengths_lst = []
    line_page_contents_lst = []
    line_number = 0

    word_ocr_coordinates_dictionary = defaultdict(list)
    word_ocr_texts = []
    word_ocr_text_confidences = []
    word_pages = []
    word_angles = []
    word_widths = []
    word_heights = []
    word_units = []
    word_line_numbers = []
    word_numbers = []
    word_offsets = []
    word_lengths = []
    word_contents = []
    word_page_offsets_lst = []
    word_page_lengths_lst = []
    word_page_contents_lst = []
    word_number_counter = 0
    for read_result in read_results:
        page = read_result.get("pageNumber")
        angle = read_result.get("angle")
        width = read_result.get("width")
        height = read_result.get("height")
        unit = read_result.get("unit")
        spans = read_result.get("spans")

        page_offsets = []
        page_lengths = []
        page_contents = []
        for enum, item in enumerate(spans):
            offset = item["offset"]
            page_offsets.append(offset)
            length = item["length"]
            page_lengths.append(length)
            content = result_dict.get("content")[offset : offset + length]
            page_contents.append(content)

        # Lines and words
        lines = read_result.get("lines")
        for line in lines:
            line_number += 1
            line_numbers.append(line_number)
            line_text = line.get("content")
            offsets = []
            lengths = []
            contents = []
            for enum, item in enumerate(line.get("spans")):
                offset = item["offset"]
                offsets.append(offset)
                length = item["length"]
                lengths.append(length)
                content = result_dict.get("content")[offset : offset + length]
                contents.append(content)
            line_page_offsets_lst.append(page_offsets)
            line_page_lengths_lst.append(page_lengths)
            line_page_contents_lst.append(page_contents)
            line_ocr_texts.append(line_text)
            line_pages.append(page)
            line_angles.append(angle)
            line_widths.append(width)
            line_heights.append(height)
            line_units.append(unit)
            line_offsets.append(offsets)
            line_lengths.append(lengths)
            line_contents.append(contents)
            # get line coordinates
            line_bounding_box = line.get("polygon")
            line_ocr_coordinates = OCRCoordinates(
                top_left_x=line_bounding_box[0],
                top_left_y=line_bounding_box[1],
                top_right_x=line_bounding_box[2],
                top_right_y=line_bounding_box[3],
                bottom_right_x=line_bounding_box[4],
                bottom_right_y=line_bounding_box[5],
                bottom_left_x=line_bounding_box[6],
                bottom_left_y=line_bounding_box[7],
            )
            for (
                line_corrd_key,
                line_corrd_value,
            ) in line_ocr_coordinates.__dict__.items():
                line_ocr_coordinates_dictionary[line_corrd_key].append(line_corrd_value)
        words = read_result.get("words")
        for word in words:
            offsets = []
            lengths = []
            contents = []
            for enum, item in enumerate([word.get("span")]):
                offset = item["offset"]
                offsets.append(offset)
                length = item["length"]
                lengths.append(length)
                content = result_dict.get("content")[offset : offset + length]
                contents.append(content)
            word_page_offsets_lst.append(page_offsets)
            word_page_lengths_lst.append(page_lengths)
            word_page_contents_lst.append(page_contents)
            word_line_numbers.append(line_number)
            word_number_counter += 1
            word_numbers.append(word_number_counter)
            word_ocr_texts.append(word.get("content"))
            word_ocr_text_confidences.append(word.get("confidence"))
            word_pages.append(page)
            word_angles.append(angle)
            word_widths.append(width)
            word_heights.append(height)
            word_units.append(unit)
            word_offsets.append(offsets)
            word_lengths.append(lengths)
            word_contents.append(contents)
            # get word coordinates
            word_bounding_box = word.get("polygon")
            word_ocr_coordinates = OCRCoordinates(
                top_left_x=word_bounding_box[0],
                top_left_y=word_bounding_box[1],
                top_right_x=word_bounding_box[2],
                top_right_y=word_bounding_box[3],
                bottom_right_x=word_bounding_box[4],
                bottom_right_y=word_bounding_box[5],
                bottom_left_x=word_bounding_box[6],
                bottom_left_y=word_bounding_box[7],
            )
            for (
                word_corrd_key,
                word_corrd_value,
            ) in word_ocr_coordinates.__dict__.items():
                word_ocr_coordinates_dictionary[word_corrd_key].append(word_corrd_value)

    # Creating line DataFrame
    line_dictionary = dict()
    line_dictionary["text"] = line_ocr_texts
    line_dictionary["line_numbers"] = line_numbers
    line_dictionary.update(line_ocr_coordinates_dictionary)
    line_dataframe = pd.DataFrame(line_dictionary)
    line_dataframe["page"] = line_pages
    line_dataframe["angle"] = line_angles
    line_dataframe["width"] = line_widths
    line_dataframe["height"] = line_heights
    line_dataframe["unit"] = line_units
    line_dataframe["offset"] = line_offsets
    line_dataframe["length"] = line_lengths
    line_dataframe["content"] = line_contents
    line_dataframe["page_offset"] = line_page_offsets_lst
    line_dataframe["page_length"] = line_page_lengths_lst
    line_dataframe["page_content"] = line_page_contents_lst
    line_dataframe = sort_rotated(line_dataframe)
    line_dataframe["bottom_left_x_diff"] = line_dataframe["bottom_left_y"].diff()
    line_dataframe["bottom_left_x_diff_bool"] = line_dataframe[
        "bottom_left_x_diff"
    ].apply(lambda x: True if 0 <= x < 0.015 else False)
    line_numbers = []
    line_numbers_count = 0
    for true_false in line_dataframe["bottom_left_x_diff_bool"]:
        if true_false == False:
            line_numbers_count += 1
        line_numbers.append(line_numbers_count)
    line_dataframe["line_numbers"] = line_numbers
    line_dataframe = line_dataframe.sort_values(
        by=["page", "line_numbers", "bottom_left_x"], ignore_index=True
    )

    # Creating word DataFrame
    word_dictionary = dict()
    word_dictionary["text"] = word_ocr_texts
    word_dictionary["line_numbers"] = word_line_numbers
    word_dictionary["word_numbers"] = word_numbers
    word_dictionary["confidence"] = word_ocr_text_confidences
    word_dictionary.update(word_ocr_coordinates_dictionary)
    word_dataframe = pd.DataFrame(word_dictionary)
    word_dataframe["page"] = word_pages
    word_dataframe["angle"] = word_angles
    word_dataframe["width"] = word_widths
    word_dataframe["height"] = word_heights
    word_dataframe["unit"] = word_units
    word_dataframe["offset"] = word_offsets
    word_dataframe["length"] = word_lengths
    word_dataframe["content"] = word_contents
    word_dataframe["page_offset"] = word_page_offsets_lst
    word_dataframe["page_length"] = word_page_lengths_lst
    word_dataframe["page_content"] = word_page_contents_lst
    word_dataframe = sort_rotated(word_dataframe)
    word_dataframe["bottom_left_x_diff"] = word_dataframe["bottom_left_y"].diff()
    word_dataframe["bottom_left_x_diff_bool"] = word_dataframe[
        "bottom_left_x_diff"
    ].apply(lambda x: True if 0 <= x < 0.015 else False)
    line_numbers = []
    line_numbers_count = 0
    for true_false in word_dataframe["bottom_left_x_diff_bool"]:
        if true_false == False:
            line_numbers_count += 1
        line_numbers.append(line_numbers_count)
    word_dataframe["line_numbers"] = line_numbers
    word_dataframe = word_dataframe.sort_values(
        by=["page", "line_numbers", "bottom_left_x"], ignore_index=True
    )
    word_dataframe['phrase_line'] = get_increasing_sequence(word_dataframe['line_numbers'].tolist())
    return (line_dataframe, word_dataframe, result)


def remove_header_footer_df(line_dataframe):
    line_dataframe["text"].apply(lambda x: x.startswith('<!-- PageFooter="'))
    line_dataframe["text_starting"] = line_dataframe["text"].apply(
        lambda x: x.startswith('<!-- PageFooter="')
    )
    line_dataframe["text_ending"] = line_dataframe["text"].apply(
        lambda x: x.endswith('" -->')
    )
    text_starting_df = line_dataframe[line_dataframe["text_starting"] == True]
    text_ending_df = line_dataframe[line_dataframe["text_ending"] == True]
    line_dataframe.loc[text_starting_df.index, "text"] = line_dataframe.loc[
        text_starting_df.index, "text"
    ].apply(lambda x: x.replace('<!-- PageFooter="', ""))
    line_dataframe.loc[text_ending_df.index, "text"] = line_dataframe.loc[
        text_ending_df.index, "text"
    ].apply(lambda x: x.replace('" -->', ""))

    line_dataframe["text_starting"] = line_dataframe["text"].apply(
        lambda x: x.startswith('<!-- PageHeader="')
    )
    line_dataframe["text_ending"] = line_dataframe["text"].apply(
        lambda x: x.endswith('" -->')
    )
    text_starting_df = line_dataframe[line_dataframe["text_starting"] == True]
    text_ending_df = line_dataframe[line_dataframe["text_ending"] == True]
    line_dataframe.loc[text_starting_df.index, "text"] = line_dataframe.loc[
        text_starting_df.index, "text"
    ].apply(lambda x: x.replace('<!-- PageHeader="', ""))
    line_dataframe.loc[text_ending_df.index, "text"] = line_dataframe.loc[
        text_ending_df.index, "text"
    ].apply(lambda x: x.replace('" -->', ""))

    line_dataframe["text_starting"] = line_dataframe["text"].apply(
        lambda x: x.startswith('<!-- PageNumber="')
    )
    line_dataframe["text_ending"] = line_dataframe["text"].apply(
        lambda x: x.endswith('" -->')
    )
    text_starting_df = line_dataframe[line_dataframe["text_starting"] == True]
    text_ending_df = line_dataframe[line_dataframe["text_ending"] == True]
    line_dataframe.loc[text_starting_df.index, "text"] = line_dataframe.loc[
        text_starting_df.index, "text"
    ].apply(lambda x: x.replace('<!-- PageNumber="', ""))
    line_dataframe.loc[text_ending_df.index, "text"] = line_dataframe.loc[
        text_ending_df.index, "text"
    ].apply(lambda x: x.replace('" -->', ""))
    line_dataframe = line_dataframe.reset_index(drop=True)

    return line_dataframe


def parse_document_ai_object(azure_document_ai_object, logger=None):
    (line_dataframe, word_dataframe, azure_document_ai_object) = azure_doc_ai_parser(
        azure_document_ai_object
    )
    line_dataframe = remove_header_footer_df(line_dataframe)
    azure_document_ai_object = AzureDocumentAI(
        line_dataframe,
        word_dataframe,
        azure_document_ai_object,
    )
    return azure_document_ai_object
