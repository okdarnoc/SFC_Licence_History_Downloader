import os
import pdfkit as pdf
import csv
from datetime import datetime
from bs4 import BeautifulSoup
import shutil
import time
import threading

found_record = True


def log(msg, msg_type="info", show=True):  # A simple logger
    if show:
        if msg_type == "info":
            print("[INFO]: {0}".format(msg))
        elif msg_type == "error":
            print("[ERROR]: {0}".format(msg))


def create_html(file_name, sfc_arg, lid_arg, lang, hide_name):
    log("-> Creating {0}.html".format(file_name))
    try:

        # Retrieving URLs with their respective SFC name
        url_eng = 'https://sfc.hk/publicregWeb/indi/{}/licenceRecord'.format(sfc_arg)
        url_chi = 'https://sfc.hk/publicregWeb/indi/{}/licenceRecord?locale=zh'.format(sfc_arg)

        """
        Downloads both english and chinese web pages with the wget tool
        and then moves the files to root directory and renames them to
        LID-DATE(Page)(Language)
        """
        if lang == "eng":
            os.system("wget --mirror --convert-links --adjust-extension --page-requisites --no-parent "
                      "{0}".format(url_eng))
            shutil.move("sfc.hk/publicregWeb/indi/{0}/licenceRecord.html".format(sfc_arg),
                        '{0}/{1}'.format(os.getcwd(), file_name + '.html'))
        elif lang == "chi":
            os.system("wget --mirror --convert-links --adjust-extension --page-requisites --no-parent "
                      "{0}".format(url_chi))
            shutil.move("sfc.hk/publicregWeb/indi/{0}/licenceRecord@locale=zh.html".format(sfc_arg),
                        '{0}/{1}'.format(os.getcwd(), file_name + '.html'))

        # Getting rid of useless folders
        shutil.rmtree('sfc.hk', ignore_errors=True)

        log("-> HTML File created.")

        redesign_and_txt(file_name)
        change_text(file_name, hide_name, sfc_arg, lid_arg)
    except (FileNotFoundError, OSError) as e:
        log(e, msg_type="error")
        pass


def redesign_and_txt(file_name):
    """
    Here we are basically retrieving the HTML code, we reformat it because
    it's pretty messy, we want it to be beautiful in order to work more efficiently
    with the code. After that, we empty the HTML and create the TXT file with the same name.
    """

    log("-> Reformatting HTML code (prettifying) ...")
    log("-> Creating {0}.txt".format(file_name))
    file_n = open(file_name + ".html", "r", encoding="utf-8")
    soup = BeautifulSoup(file_n, "html.parser")
    rewrite_file = soup.prettify()
    file_n.close()

    empty_file = open(file_name + ".html", "w", encoding="utf-8")
    empty_file.close()

    with open(file_name + ".html", "w", encoding="utf-8") as output:
        output.write(rewrite_file)

    with open(file_name + ".txt", "w", encoding="utf-8") as output:
        output.write(rewrite_file)

    log("-> HTML file has been reformatted.")


def change_text(file_name, hide_name, sfc_arg, lid_arg):
    """
    Here we are converting each line in the TXT file into a big list so we can
    edit the index that contains the TEXT that we want to change.

    We also check for the "Record not Found" and "找不到記錄" in the page so
    we can skip the page and add the SFC to the list of not working SFCs.
    """
    global files, found_record

    log("-> Editing texts...")

    with open(file_name + ".txt", "r", encoding="utf-8") as output:
        lines = output.read().split("\n")

    empty_file = open(file_name + ".html", "w", encoding="utf-8")
    empty_file.close()

    with open(file_name + ".html", "w", encoding="utf-8") as output:
        not_found_eng = "No record found."
        not_found_chi = "找不到記錄"

        if not_found_eng in lines[84] or not_found_chi in lines[84]:
            log("-> Record not found.", msg_type="error")
            records_not_found[sfc_arg] = lid_arg
            found_record = False
        else:
            found_record = True

        if found_record:
            lines[
                20] = "<h2 style='position: fixed;right: 0;top: 0;font-size: 15px;'>" + lid_arg + "-" + date_now + \
                      "<h2><br><br><br><br>"

            if hide_name:
                lines[120] = ""
                lines[122] = "{0}-{1}".format(lid_arg, date_now)
                lines[170] = "value: '" + lid_arg + "-" + date_now + "',"

            for line in lines:
                output.write("{0}\n".format(line))

        log("-> Texts edited...")

        log("-> Removing TXT file")
        if os.path.isfile(file_name + ".txt"):
            os.remove(file_name + ".txt")
        log("-> TXT File removed.")


def create_pdf(file_name):
    global found_record

    """
    If the record is found, we want to create the PDF for it because it would take too much
    to create a useless PDF just to remove it because the page doesn't exist.

    We also add the LID-DATE in the top right corner of the PDF because it creates a better
    position than the HTML file. The rest of the text is edited directly within the HTML for
    neat look and efficient program.
    """

    try:
        if found_record:
            pdf.from_file(file_name + ".html", file_name + ".pdf")
        else:
            log("-> Skipping file, because record not found.", msg_type="error")
            # log("-> Deleting non-existing record files.")

            os.remove(file_name + ".html")
    except (FileNotFoundError, OSError):
        log("-> Issue with LID or SFC", msg_type="error")


date = datetime.now()  # We need this to name the file with the current date time.
date_now = "{0}{1}{2}".format(date.year, date.month, date.day)  # above line explains it

csv_file = open('SFC_LID.csv', 'r', encoding='UTF-8')  # The CSV that contains the SFC and LID

details_list = list()  # This list will contain what the CSV contains
details_dict = dict()
files = list()  # All the existing files in the directory that we've created
records_not_found = dict()  # All the SFC that weren't found


if os.path.isdir("sfc.hk"):
    log("-> SFC directory detected ... removing")
    shutil.rmtree('sfc.hk', ignore_errors=True)

# Getting rid of the failed_records.csv from previous session
if os.path.isfile("failed_records.csv"):
    log("-> failed_records.csv found: deleting ...")
    os.remove("failed_records.csv")
    log("-> Deleted.")

# Reading the CSV file
with csv_file:
    log("-> Reading CSV...")
    file = csv.reader(csv_file)

    for row in file:
        if len(row) > 0:
            if len(row[0]) >= 1 or len(row[0]) == 6:
                details_list.append(row)

list_size = len(details_list)
log("-> CSV Read.")


# We are repeating the process of creating files etc for as many SFC we have.
for x in range(1, len(details_list)):
    print(details_list)

    """The script will try to retrieve the SFC and Lid from the CSV.
        If there are errors in the index range, it will name the SFC: "NonExi"
        and the Lid: "NonLid" by default so it can continue running the script
        without further errors."""

    try:
        sfc_name = details_list[x][0]
        lid_id = details_list[x][1]
    except IndexError:
        sfc_name = "NonExi"
        lid_id = "NonLid"

    eng_one = "{0}-{1}(1)(Eng)".format(lid_id, date_now)
    eng_two = "{0}-{1}(2)(Eng)(X)".format(lid_id, date_now)
    chi_one = "{0}-{1}(3)(Chi)".format(lid_id, date_now)
    chi_two = "{0}-{1}(4)(Chi)(X)".format(lid_id, date_now)

    files.append(eng_one)
    files.append(eng_two)
    files.append(chi_one)
    files.append(chi_two)

    if not found_record:
        for retry in range(0, 3):
            log("Retrying record ...")

            time.sleep(10)

    create_html(eng_one, sfc_name, lid_id, "eng", False)
    create_html(eng_two, sfc_name, lid_id, "eng", True)
    create_html(chi_one, sfc_name, lid_id, "chi", False)
    create_html(chi_two, sfc_name, lid_id, "chi", True)

    create_first_pdf = threading.Thread(target=create_pdf, args=(eng_one,))
    create_second_pdf = threading.Thread(target=create_pdf, args=(eng_two,))
    create_third_pdf = threading.Thread(target=create_pdf, args=(chi_one,))
    create_fourth_pdf = threading.Thread(target=create_pdf, args=(chi_two,))

    create_first_pdf.start()
    create_second_pdf.start()
    create_third_pdf.start()
    create_fourth_pdf.start()

if len(records_not_found) == 0:
    log("-> All the records were found.")
elif len(records_not_found) > 0:
    log("-> {0} records were not found.".format(len(records_not_found)))
    log("-> failed_records.csv has been added to the folder.")

    # Writes all the non-existing SFC to separate rows and columns in the failed_records.csv file.
    with open("failed_records.csv", "w", encoding="utf-8", newline="") as f:
        write_csv = csv.writer(f)
        write_csv.writerow(["SFC_CE, LID"])
        for sfc, lid in records_not_found.items():
            write_csv.writerow(["{0}, {1}".format(sfc, lid)])

log("-> Job done !")
