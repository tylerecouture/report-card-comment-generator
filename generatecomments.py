
import csv
from collections import OrderedDict

from pathlib import Path

def get_student_list():

    while True:
        filename = input("Student data file path: ")
        try:
            # expand ~ to home dir
            if filename[0] is '~':
                home_path = str(Path.home())
                filename = filename.replace('~', home_path)
                print("Looking for: {}".format(filename))

            with open(filename) as f:
                f.readline()  # skip first row with is just column number, 2nd row is headings.
                csv_reader = csv.DictReader(f)
                csv_reader.fieldnames = [field.strip().upper() for field in csv_reader.fieldnames]
                student_import_list = list(csv_reader)
                for student in student_import_list:
                    student = {k: v.strip() for k, v in student.items() if k}  # strip whitespace and remove empty keys

            return student_import_list

        except FileNotFoundError:
            print("File not found... try again?")


def get_comment_list():

    while True:
        filename = input("Enter comment file path, or [Enter] for default: ")
        try:
            if filename == '':
                filename = "comments.txt"
            elif filename[0] is '~':  # expand ~ to home dir
                home_path = str(Path.home())
                filename = filename.replace('~', home_path)
                print("Looking for: {}".format(filename))

            comment_dict_import = OrderedDict()

            with open(filename) as f:
                # read the first line separately so we can set an initial category
                line = f.readline().strip()
                current_list = []
                if line and line[0] != '#':
                    current_category = "GENERAL"
                    current_list.append(line)
                else:
                    current_category = line[1:].strip()  # remove hash

                # we have a category, let's do the rest now.
                for line in f:
                    line = line.strip()
                    if line and line[0] == '#':  # comment heading
                        # save the current list with the previous heading and start a new one.
                        comment_dict_import[current_category] = current_list
                        current_category = line[1:]  # remove hash
                        current_list = []  # start a new list for the new category
                    elif line:
                        current_list.append(line)

            return comment_dict_import

        except FileNotFoundError:
            print("File not found... try again?")


print("**** REPORT CARD COMMENT GENERATOR 2000 ****")


student_list = get_student_list()
# print("{} students found.".format(len(student_list)))

comment_dict = get_comment_list()
for key, value in comment_dict.items():
    print(key)
    print(value)



