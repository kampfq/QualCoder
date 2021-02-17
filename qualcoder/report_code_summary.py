# -*- coding: utf-8 -*-

"""
Copyright (c) 2021 Colin Curtain

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Author: Colin Curtain (ccbogel)
https://github.com/ccbogel/QualCoder
"""

from copy import deepcopy
#import datetime
import logging
import os
#from PIL import Image
#from PIL.ExifTags import TAGS
#import platform
import sys
import traceback
#import vlc

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from GUI.ui_dialog_report_code_summary import Ui_Dialog_code_summary


path = os.path.abspath(os.path.dirname(__file__))
logger = logging.getLogger(__name__)


def exception_handler(exception_type, value, tb_obj):
    """ Global exception handler useful in GUIs.
    tb_obj: exception.__traceback__ """
    tb = '\n'.join(traceback.format_tb(tb_obj))
    text = 'Traceback (most recent call last):\n' + tb + '\n' + exception_type.__name__ + ': ' + str(value)
    print(text)
    logger.error(_("Uncaught exception:") + "\n" + text)
    QtWidgets.QMessageBox.critical(None, _('Uncaught Exception'), text)


class DialogReportCodeSummary(QtWidgets.QDialog):
    """ Provide a summary report for selected code.
    """

    app = None
    parent_tetEdit = None
    categories = []
    codes = []
    #files = []

    def __init__(self, app, parent_textEdit):
        sys.excepthook = exception_handler
        self.app = app
        self.parent_textEdit = parent_textEdit
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_Dialog_code_summary()
        self.ui.setupUi(self)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        font = 'font: ' + str(self.app.settings['fontsize']) + 'pt '
        font += '"' + self.app.settings['font'] + '";'
        self.setStyleSheet(font)
        docfont = 'font: ' + str(self.app.settings['docfontsize']) + 'pt '
        docfont += '"' + self.app.settings['font'] + '";'
        self.ui.textEdit.setStyleSheet(docfont)
        treefont = 'font: ' + str(self.app.settings['treefontsize']) + 'pt '
        treefont += '"' + self.app.settings['font'] + '";'
        try:
            s0 = int(self.app.settings['dialogreport_code_summary_splitter0'])
            s1 = int(self.app.settings['dialogreport_code_summary_splitter1'])
            self.ui.splitter.setSizes([s0, s1])
        except:
            pass
        self.ui.splitter.splitterMoved.connect(self.splitter_sizes)
        self.ui.treeWidget.setStyleSheet(treefont)
        self.ui.treeWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.fill_tree()
        self.ui.treeWidget.itemClicked.connect(self.fill_text_edit)

    def splitter_sizes(self, pos, index):
        """ Detect size changes in splitter and store in app.settings variable. """

        sizes = self.ui.splitter.sizes()
        self.app.settings['dialogreport_code_summary_splitter0'] = sizes[0]
        self.app.settings['dialogreport_code_summary_splitter1'] = sizes[1]

    #TODO UPDATE CODES CATEGORIES WHEN CHANGED IN CODING DIALOG

    def get_codes_and_categories(self):
        """ Called from init, delete category/code.
        Also called on other coding dialogs in the dialog_list. """

        self.codes, self.categories = self.app.get_data()

    def fill_tree(self):
        """ Fill tree widget, top level items are main categories and unlinked codes.
        The Count column counts the number of times that code has been used by selected coder in selected file. """

        self.get_codes_and_categories()
        cats = deepcopy(self.categories)
        codes = deepcopy(self.codes)
        self.ui.treeWidget.clear()
        self.ui.treeWidget.setColumnCount(4)
        self.ui.treeWidget.setHeaderLabels([_("Name"), _("Id"), _("Memo"), _("Count")])
        if self.app.settings['showids'] == 'False':
            self.ui.treeWidget.setColumnHidden(1, True)
        else:
            self.ui.treeWidget.setColumnHidden(1, False)
        self.ui.treeWidget.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.ui.treeWidget.header().setStretchLastSection(False)
        # add top level categories
        remove_list = []
        for c in cats:
            if c['supercatid'] is None:
                memo = ""
                if c['memo'] != "" and c['memo'] is not None:
                    memo = _("Memo")
                top_item = QtWidgets.QTreeWidgetItem([c['name'], 'catid:' + str(c['catid']), memo])
                top_item.setToolTip(2, c['memo'])
                self.ui.treeWidget.addTopLevelItem(top_item)
                remove_list.append(c)
        for item in remove_list:
            #try:
            cats.remove(item)
            #except Exception as e:
            #    logger.debug(e, item)

        ''' Add child categories. look at each unmatched category, iterate through tree
         to add as child, then remove matched categories from the list '''
        count = 0
        while len(cats) > 0 and count < 10000:
            remove_list = []
            #logger.debug("Cats: " + str(cats))
            for c in cats:
                it = QtWidgets.QTreeWidgetItemIterator(self.ui.treeWidget)
                item = it.value()
                count2 = 0
                while item and count2 < 10000:  # while there is an item in the list
                    if item.text(1) == 'catid:' + str(c['supercatid']):
                        memo = ""
                        if c['memo'] != "" and c['memo'] is not None:
                            memo = _("Memo")
                        child = QtWidgets.QTreeWidgetItem([c['name'], 'catid:' + str(c['catid']), memo])
                        child.setToolTip(2, c['memo'])
                        item.addChild(child)
                        remove_list.append(c)
                    it += 1
                    item = it.value()
                    count2 += 1
            for item in remove_list:
                cats.remove(item)
            count += 1

        # add unlinked codes as top level items
        remove_items = []
        for c in codes:
            if c['catid'] is None:
                memo = ""
                if c['memo'] != "" and c['memo'] is not None:
                    memo = _("Memo")
                top_item = QtWidgets.QTreeWidgetItem([c['name'], 'cid:' + str(c['cid']), memo])
                top_item.setToolTip(2, c['memo'])
                top_item.setBackground(0, QtGui.QBrush(QtGui.QColor(c['color']), Qt.SolidPattern))
                top_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)
                self.ui.treeWidget.addTopLevelItem(top_item)
                remove_items.append(c)
        for item in remove_items:
            codes.remove(item)

        # add codes as children
        for c in codes:
            it = QtWidgets.QTreeWidgetItemIterator(self.ui.treeWidget)
            item = it.value()
            count = 0
            while item and count < 10000:
                if item.text(1) == 'catid:' + str(c['catid']):
                    memo = ""
                    if c['memo'] != "" and c['memo'] is not None:
                        memo = _("Memo")
                    child = QtWidgets.QTreeWidgetItem([c['name'], 'cid:' + str(c['cid']), memo])
                    child.setBackground(0, QtGui.QBrush(QtGui.QColor(c['color']), Qt.SolidPattern))
                    child.setToolTip(2, c['memo'])
                    child.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)
                    item.addChild(child)
                    c['catid'] = -1  # Make unmatchable
                it += 1
                item = it.value()
                count += 1
        self.ui.treeWidget.expandAll()


    def fill_text_edit(self):
        """ Get data about file and fill text edit. """

        current = self.ui.treeWidget.currentItem()
        if current.text(1)[0:3] != 'cid':
            return
        cur = self.app.conn.cursor()
        text = _("CODE: ") + current.text(0) + "  " + current.text(1) + "\n"

        #text += _("MEMO: ") + "\n" + "\n"

        '''cur.execute("select date, owner, fulltext, mediapath from source where id=?", [file_['id']])
        res = cur.fetchone()
        text += "ID: " + str(file_['id']) + "  " + _("Date: ") + res[0] + "  " + _("Owner: ") + res[1] + "\n"
        media_path = ""
        file_type = ""
        if res[3] is None or res[3] == "":
            media_path = _("Internal text document")
            file_type = "text"
        elif res[3][0:5] == "docs:":
            media_path = _("External text document: ") + res[3][5:]
            file_type = "text"
        elif res[3][0:6] == "audio:":
            media_path = _("External audio file: ") + res[3][6:]
            file_type = "audio"
        elif res[3][0:7] == "/audio/":
            media_path = _("Internal audio file")
            file_type = "audio"
        elif res[3][0:6] == "video:":
            media_path = _("External video file: ") + res[3][6:]
            file_type = "video"
        elif res[3][0:7] == "/video/":
            media_path = _("Internal video file")
            file_type = "video"
        elif res[3][0:7] == "images:":
            media_path = _("External image file: ") + res[3][7:]
            file_type = "image"
        elif res[3][0:8] == "/images/":
            media_path = _("Internal image file")
            file_type = "image"
        text += _("Media path: ") + media_path + "\n"
        if file_type == "text":
            text += self.text_statistics(file_['id'])
        if file_type == "image":
            text += self.image_statistics(file_['id'])
        if file_type == "audio":
            text += self.audio_statistics(file_['id'])
        if file_type == "video":
            text += self.video_statistics(file_['id'])'''

        self.ui.textEdit.setText(text)


    '''def video_statistics(self, id):
        """ Get video statistics for image file
        param: id : Integer """

        text = _("METADATA:") + "\n"
        cur = self.app.conn.cursor()
        cur.execute("select mediapath from source where id=?", [id])
        mediapath = cur.fetchone()[0]
        abs_path = ""
        if 'video:' == mediapath[0:6]:
            abs_path = mediapath[6:]
        else:
            abs_path = self.app.project_path + mediapath

        instance = vlc.Instance()
        mediaplayer = instance.media_player_new()
        media = instance.media_new(abs_path)
        media.parse()
        mediaplayer.play()
        mediaplayer.pause()
        msecs = media.get_duration()
        secs = int(msecs / 1000)
        mins = int(secs / 60)
        remainder_secs = str(secs - mins * 60)
        if len(remainder_secs) == 1:
            remainder_secs = "0" + remainder_secs
        text += _("Duration: ") + str(mins) + ":" + remainder_secs + "\n"
        for k in meta_keys:
            meta = media.get_meta(k)
            if meta is not None:
                text += str(k)+ ":  " + meta + "\n"
        return text

    def audio_statistics(self, id):
        """ Get audio statistics for image file
        param: file_ Dictionary of {name, id, memo} """

        text = _("METADATA:") + "\n"
        cur = self.app.conn.cursor()
        cur.execute("select mediapath from source where id=?", [id])
        mediapath = cur.fetchone()[0]
        abs_path = ""
        if 'audio:' == mediapath[0:6]:
            abs_path = mediapath[6:]
        else:
            abs_path = self.app.project_path + mediapath

        instance = vlc.Instance()
        mediaplayer = instance.media_player_new()
        media = instance.media_new(abs_path)
        media.parse()
        msecs = media.get_duration()
        secs = int(msecs / 1000)
        mins = int(secs / 60)
        remainder_secs = str(secs - mins * 60)
        if len(remainder_secs) == 1:
            remainder_secs = "0" + remainder_secs
        text += _("Duration: ") + str(mins) + ":" + remainder_secs + "\n"
        for k in meta_keys:
            meta = media.get_meta(k)
            if meta is not None:
                text += str(k)+ ":  " + meta + "\n"

        # Codes
        sql = "select code_name.name, code_av.cid, count(code_av.cid), round(avg(pos1 - pos0)) "
        sql += " from code_av join code_name "
        sql += "on code_name.cid=code_av.cid where id=? "
        sql += "group by code_name.name, code_av.cid order by count(code_av.cid) desc"
        cur.execute(sql, [id])
        res = cur.fetchall()
        text += "\n\n" + _("CODE COUNTS:") + "\n"

        for r in res:
            text += r[0] + "  " + _("Count: ") + str(r[2]) + "   "
            text += _("Average segment: ") + f"{int(r[3]):,d}" + _(" msecs") + "\n"
        return text

    def image_statistics(self, id):
        """ Get image statistics for image file
        param: id: Integer """

        text = _("METADATA:") + "\n"
        cur = self.app.conn.cursor()
        cur.execute("select mediapath from source where id=?", [id])
        mediapath = cur.fetchone()[0]
        abs_path = ""
        if 'images:' == mediapath[0:7]:
            abs_path = mediapath[7:]
        else:
            abs_path = self.app.project_path + mediapath

        # Image size and metadata
        image = Image.open(abs_path)
        w, h = image.size
        text += _("Width: ") + f"{w:,d}"  + "  " + _("Height: ") + f"{h:,d}" + "  " + _("Area: ") + f"{w * h:,d}" + _(" pixels") + "\n"
        image_type = abs_path[-3:].lower()
        # From: www.thepythoncode.com/article/extracting-image-metadata-in-python
        if image_type in ("jpg", "peg"):
            exifdata = image.getexif()
            # iterating over the EXIF data fields
            for tag_id in exifdata:
                # get the tag name, instead of human unreadable tag id
                tag = TAGS.get(tag_id, tag_id)
                data = exifdata.get(tag_id)
                # Decode bytes
                if isinstance(data, bytes):
                    try:
                        data = data.decode()
                        text += f"{tag:25}: {data}" + "\n"
                    except UnicodeDecodeError as e:
                        logger.debug(e)
                        #text += str(e) + "\n"
        # From: www.vice.com/en/article/aekn58/hack-this-extra-image-metadata-using-python
        if image_type == "png":
            for tag, value in image.info.items():
                key = TAGS.get(tag, tag)
                text += key + " " + str(value) + "\n"

        # Codes
        sql = "select code_name.name, code_image.cid, count(code_image.cid), round(avg(width)), round(avg(height)) "
        sql += " from code_image join code_name "
        sql += "on code_name.cid=code_image.cid where id=? "
        sql += "group by code_name.name, code_image.cid order by count(code_image.cid) desc"
        cur.execute(sql, [id])
        res = cur.fetchall()
        text += "\n\n" + _("CODE COUNTS:") + "\n"

        for r in res:
            area = int(r[3] * r[4])
            text += r[0]+ "  " + _("Count: ") + str(r[2]) + "   " + _("Average area: ") + f"{area:,d}" + _(" pixels") + "\n"
        return text

    def text_statistics(self, id):
        """ Get details of text file statistics
        param: id Integer
        """

        text = _("STATISTICS:") + "\n"
        cur = self.app.conn.cursor()
        cur.execute("select fulltext from source where id=?", [id])
        fulltext = cur.fetchone()[0]
        if fulltext is None:
            fulltext = ""
        text += _("Characters: ") + f"{len(fulltext):,d}" + "\n"
        # Remove punctuation. Convert to lower case
        chars = ""
        for c in range(0, len(fulltext)):
            if fulltext[c].isalpha() or fulltext[c] =="'":
                chars += fulltext[c]
            else:
                chars += " "
        chars = chars.lower()
        word_list = chars.split()
        #print(word_list)
        msg = _("Word calculations: Words use alphabet characters and include the apostrophe. All other characters are word separators")
        text += "\n" + msg + "\n"
        #TODO use word list for word proximity

        text += "\n" + _("Words: ") + f"{len(word_list):,d}" + "\n"
        # Word frequency
        d = {}
        for word in word_list:
            d[word] = d.get(word, 0) + 1  # get(key, value if not present)
        # https://codeburst.io/python-basics-11-word-count-filter-out-punctuation-dictionary-manipulation-and-sorting-lists-3f6c55420855
        word_freq = []
        for key, value in d.items():
            word_freq.append((value, key))
        word_freq.sort(reverse=True)
        #print(word_freq)
        text += _("Unique words: ") + str(len(word_freq)) + "\n"
        # Top 100 or maximum of less than 100
        max_count = len(word_freq)
        if max_count > 100:
            max_count = 100
        text += _("Top 100 words") + "\n"
        for i in range(0, max_count):
            text += word_freq[i][1] + "   " + str(word_freq[i][0]) + " | "

        # Codes
        sql = "select code_name.name, code_text.cid, count(code_text.cid), sum(length(code_text.seltext)), "
        sql += "round(avg(length(code_text.seltext))) from code_text join code_name "
        sql += "on code_name.cid=code_text.cid where fid=? "
        sql += "group by code_name.name, code_text.cid order by count(code_text.cid) desc"
        cur.execute(sql, [id])
        res = cur.fetchall()
        text += "\n\n" + _("CODE COUNTS:") + "\n"
        for r in res:
            text += r[0]+ "  " + _("Count: ") + str(r[2]) + "  " + _("Total characters: ") + f"{r[3]:,d}"
            text += "  " + _("Average characters: ") + str(int(r[4])) + "\n"
        return text'''


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = DialogReportCodeSummary()
    ui.show()
    sys.exit(app.exec_())

