#!/usr/bin/python3
import csv
import itertools
import os
import re
import sys
import tempfile
from collections import OrderedDict

from pathlib import Path
from shutil import copyfile


class bcolors:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YEL = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def printc(string, color=bcolors.RED):
    print(color + string + bcolors.ENDC)


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


PRONOUNS = {
    'XE':  {'M': "he",  'F': 'she', 'N': 'they',  'NAME': 'NAME'},
    'XIM': {'M': "him", 'F': 'her', 'N': 'them',  'NAME': 'NAME'},
    'XIS': {'M': "his", 'F': 'her', 'N': 'their', 'NAME': "NAME's"},
}


def parse_pronouns(comment, sex='N', name=None):
    pronouns = list(PRONOUNS.keys())
    comment = replace_nth_with_name(comment, pronouns, 3)
    for p in pronouns:
        comment = comment.replace(p, PRONOUNS[p][sex])

    comment = comment.replace('NAME', name.capitalize())
    return comment


def replace_nth_with_name(text, pronouns, n=3):
    # p = '|'.join(pronouns)
    # pattern = '(' + p + ')'
    # # https://stackoverflow.com/a/46705842/2700631
    # replaced = re.sub(pattern, lambda m, c=itertools.count(): m.group() if next(c) % n else 'NAME', text)
    new_text = ""
    count = 0
    for word in text.split():
        if word in pronouns:
            if count % n == 0:
                new_text += PRONOUNS[word]['NAME']
            else:
                new_text += word
            count += 1
        else:
            new_text += word

        if word == 'NAME':
            count = 1  # reset counter

        new_text += " "
    return new_text


def cap_matches(match):
    return match.group().capitalize()


def capitalize_sentences(text):
    # https://stackoverflow.com/a/22801162/2700631
    p = re.compile(r'((?<=[\.\?!]\s)(\w+)|(^\w+)|(?<=\)\s)(\w+))')
    return p.sub(cap_matches, text)


class Student:

    def __init__(self, firstname, lastname, sex):
        self.firstname = firstname
        self.lastname = lastname
        self.sex = sex
        self.comments = []

    def comment_string(self):
        s = ""
        for i, c in enumerate(self.comments):
            s += "({}{}{}) {} ".format(bcolors.BLUE, i, bcolors.ENDC, c)
        s = parse_pronouns(s, self.sex, self.firstname) if s else s
        return capitalize_sentences(s)

    def final_comment_string(self):
        s = ' '.join(self.comments)
        s = parse_pronouns(s, self.sex, self.firstname) if s else s
        return capitalize_sentences(s)


class CommentGenerator:

    def __init__(self):
        self.comment_file = None
        self.students = self.generate_students(self.get_student_list())
        self.comments = self.get_comment_dict()
        self.save_file = "saved_comments.txt"

    def generate_students(self, student_list):
        students = []
        for s in student_list:
            student = Student(s["FIRST NAME"], s["LAST NAME"], s["SEX"])
            students.append(student)

        return students

    def get_student_list(self):

        while True:
            print("Student data file should be csv with at least the following fields: "
                  "FIRST NAME, LAST NAME, SEX")
            filename = input("Student data file path (default is ~/StudentList.csv): ")

            if filename == '':
                filename = "~/StudentList.csv"

            if filename[0] is '~':  # expand ~ to home dir
                home_path = str(Path.home())
                filename = filename.replace('~', home_path)
                # print("Looking for: {}".format(filename))
            try:
                with open(filename) as f:
                    f.readline()  # skip first row with is just column number, 2nd row is headings.
                    csv_reader = csv.DictReader(f)
                    csv_reader.fieldnames = [field.strip().upper() for field in csv_reader.fieldnames]
                    student_list = list(csv_reader)
                    for i, student in enumerate(student_list):
                        student_list[i] = {k: v.strip() for k, v in student.items() if k}  # strip whitespace and remove empty keys

                return student_list

            except FileNotFoundError:
                print("File not found... try again?")

    def get_comment_dict(self):

        while True:
            filename = input("Enter comment file path, or [Enter] for default: ")

            if filename == '':
                filename = "comments.txt"
            elif filename[0] is '~':  # expand ~ to home dir
                home_path = str(Path.home())
                filename = filename.replace('~', home_path)
                # print("Looking for: {}".format(filename))

            try:
                comment_dict_import = OrderedDict()

                with open(filename) as f:
                    # read the first line separately so we can set an initial category
                    line = f.readline().strip()
                    current_list = []
                    if line and line[0] != '#':
                        current_category = "GENERAL"
                        current_list.append(line)
                    else:
                        current_category = line[1:].strip()  # remove hash and whitespace

                    # we have a category, let's do the rest now.
                    for line in f:
                        line = line.strip()
                        if line and line[0] == '#':  # comment heading
                            # save the current list with the previous heading and start a new one.
                            comment_dict_import[current_category] = current_list
                            current_category = line[1:].strip()  # remove hash
                            current_list = []  # start a new list for the new category
                        elif line:
                            current_list.append(line)

                    # add the last category
                    comment_dict_import[current_category] = current_list

                self.comment_file = filename  # save so we can add to it later!

                return comment_dict_import

            except FileNotFoundError:
                print("File not found... try again?")

    def insert_into_comment_file(self, comment, category):
        # backup
        copyfile(self.comment_file, "{}_bu".format(self.comment_file))

        with open(self.comment_file) as f:
            original = f.readlines()

        with open(self.comment_file, 'w') as f:
            found_category = False
            inserted = False
            for line in original:
                if not inserted:
                    if not found_category and line[1:].strip() == category:
                        found_category = True

                    elif found_category and line[0] == '#':  # add before the next category (at end of chosen category)
                        f.write(comment + "\n")
                        inserted = True

                f.write(line)

            if not inserted:  # last category?
                f.write(comment + "\n")

    def remove_comment_from_file(self, category):
        index = int(input("Which comment template do you want to delete? "))
        comment_to_remove = self.comments[category][index]
        print(comment_to_remove)
        confirm = input("Are you sure you want to delete this template? ")
        if confirm == 'y':
            with open(self.comment_file) as f:
                original = f.readlines()

            with open(self.comment_file, 'w') as f:
                for line in original:
                    if line.strip() != comment_to_remove.strip():
                        f.write(line + "\n")
                    else:  # found the line, also remove from current list
                        self.comments[category].remove(comment_to_remove)

    def custom_comment(self, category, save_option=True):
        comment = input("Enter your custom comment (use XE XIS and XIM to allow for easy reuse): ")

        prompt = "Do you want to save this comment for future use under the {} category? (y) or n: ".format(category)
        gotta_save = input(prompt) if save_option else 'n'

        if gotta_save == '' or gotta_save.lower()[0] != 'n':
            self.insert_into_comment_file(comment, category)
            self.comments[category].append(comment)
        return comment

    def remove_comment(self, student):
        self.print_header(student)
        index = input("Which comment do you want to remove (a for all)? ")
        if index == 'a':
            student.comments = []
        student.comments.pop(int(index))

    def move_comment(self, student):
        self.print_header(student)
        index = int(input("Which comment do you want to move? "))
        comment = student.comments.pop(index)
        print(student.comment_string())
        index = int(input("Move it before which comment? "))
        student.comments.insert(index, comment)

    def update_gender(self, student):
        self.print_header(student)
        choice = input("Choose a gender: M, F, or N (neutral): ")
        if choice.upper() in ['M', 'F', 'N']:
            student.sex = choice.upper()

    def update_name(self, student):
        self.print_header(student)
        choice = input("First name to use in comments: ")
        student.firstname = choice

    def save(self):
        with open(self.save_file, 'w') as f:
            for student in self.students:
                f.write(student.firstname.upper() + " " + student.lastname.upper() + "\n")
                f.write(student.final_comment_string())
                f.write("\n\n")

    def get_category(self, index):
        return list(self.comments.keys())[index]

    def get_categories(self):
        return list(self.comments.keys())

    def print_header(self, student):
        clear()
        print("Generating comments for: {}{} {}{} ({}):".
              format(bcolors.PURPLE, student.firstname, student.lastname, bcolors.ENDC, student.sex))
        print(student.comment_string())
        printc(student.final_comment_string())

    def choose_comment(self, student):

        try:
            categories = self.get_categories()
            self.print_header(student)
            print("Choose a comment category")
            for i, cat in enumerate(categories):
                print("{}: {}".format(i, cat))
            # print("c: CUSTOM")
            print("-------- OR --------")
            print("change (g)ender or (n)ame | "
                  "(c)ustom comment | "
                  "(r)emove or (m)ove a comment | "
                  "(s)ave and ne(x)t or save and (q)uit"
                  )

            choice = input()

            if choice == 'q':
                self.save()
                clear()
                sys.exit()
            elif choice == 's':
                self.save()
                return None, "complete"
            elif choice == 'x':
                return None, "complete"
            elif choice == 'r':
                self.remove_comment(student)
                return None, "continue"
            elif choice == 'c':
                return self.custom_comment(category=None, save_option=False), "new"
            elif choice == 'g':
                self.update_gender(student)
                return None, "continue"
            elif choice == 'n':
                self.update_name(student)
                return None, "continue"
            elif choice == 'm':
                self.move_comment(student)
                return None, "continue"
            else:
                choice = int(choice)

            self.print_header(student)

            category = self.get_category(choice)
            print("Choose a {} Comment:".format(category))
            for i, com in enumerate(self.comments[category]):
                print("{}: {}".format(i, com))
            print("-------- OR --------")
            print("a: Add a new templated comment")
            print("r: remove a templated comment")
            print("b: Go back")

            choice = input()
            if choice == 'a':
                return self.custom_comment(category), "new"
            if choice == 'r':
                self.remove_comment_from_file(category)
                return None, "continue"
            elif choice == 'b':
                return None, "continue"

            choice = int(choice)
            return self.comments[category][choice], "new"

        except (IndexError, ValueError):
            print("That wasn't a valid option!")
            return None, "continue"

    def generate_comments(self, student):
        adding_comments = True
        while adding_comments:
            comment, status = self.choose_comment(student)

            if status == "new":
                student.comments.append(comment)
            elif status == "complete":
                adding_comments = False

    def run(self):
        for student in self.students:
            self.generate_comments(student)


print("**** REPORT CARD COMMENT GENERATOR 2000 ****")
cg = CommentGenerator()
cg.run()

