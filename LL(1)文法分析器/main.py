import re
import wx
import wx.xrc

# 关键字
keywords = {'do': 0, 'end': 1, 'for': 2, 'if': 3, 'printf': 4, 'scanf': 5, 'then': 6, 'while': 7}

# 关系运算符
relational_operators = {'<': 0x00, '<=': 0x01, '=': 0x02, '>': 0x03, '>=': 0x04, '<>': 0x05, '==': 0x06}

# 算数运算符
arithmetic_operators = {'+': 0x10, '-': 0x11, '*': 0x20, '/': 0x21}

# 分界符
separators = {',': 0, ';': 1, '(': 2, ')': 3, '[': 4, ']': 5}

# 标识符
ids = {}
id_code = 0

# 常数
cis = {}
ci_code = 0

# 输出字符串
string = str()


# 读取并处理文件中的字符串
def get_list(file_name):
    word_lists = []
    source_file = open(file_name)
    lines = source_file.readlines()
    for line in lines:
        word_lists += re.split(r' +', line)   # 正则表达式处理字符串中的空格
    return word_lists


# 判断关键字
def is_keyword(element):
    return element in keywords.keys()


# 判断关系运算符
def is_relational_operator(element):
    return element in relational_operators.keys()


# 判断算数运算符
def is_arithmetic_operator(element):
    return element in arithmetic_operators.keys()


# 判断分界符
def is_separator(element):
    return element in separators.keys()


# 识别处理后字符串中的单词
def recognition(word_lists):
    global string

    # 定位单词所在行与列
    row = 1
    col = 1

    for element in word_lists:
        if is_keyword(element):
            string += element + '\t' + '(1, ' + str(keywords[element]) + ')\t' + \
                      '关键字\t' + '(' + str(row) + ', ' + str(col) + ')\n'
            col += 1

        elif is_arithmetic_operator(element):
            string += element + '\t' + '(3, ' + str(arithmetic_operators[element]) + ')\t' + \
                      '算数运算符\t' + '(' + str(row) + ', ' + str(col) + ')\n'
            col += 1

        elif is_relational_operator(element):
            string += element + '\t' + '(4 ' + str(relational_operators[element]) + ')\t' + \
                      '关系运算符\t' + '(' + str(row) + ', ' + str(col) + ')\n'
            col += 1

        elif is_separator(element):
            string += element + '\t' + '(2, ' + str(separators[element]) + ')\t' + \
                      '分界符\t' + '(' + str(row) + ', ' + str(col) + ')\n'
            col += 1

        # 无法直接识别成上述类型
        else:

            # 对每一个字符串依次进行字符遍历
            i = 0
            while i < len(element):
                # 遇到换行行数加1，列数置1
                if element[i] == '\n':
                    row += 1
                    col = 1
                    i += 1
                    continue

                global id_code
                global ci_code

                # 当前识别字符串
                str_token = ''

                # 识别关键字或标识符
                if element[i].isalpha():
                    while i <= len(element) - 1 and (element[i].isalpha() or element[i].isdigit()):
                        str_token += element[i]
                        i += 1
                    i -= 1
                    if is_keyword(str_token):
                        string += str_token + '\t' + '(1, ' + str(keywords[str_token]) + ')\t' + \
                                  '关键字\t' + '(' + str(row) + ', ' + str(col) + ')\n'
                        col += 1
                    else:
                        if str_token not in ids.keys():
                            ids[str_token] = id_code
                            id_code += 1
                        string += str_token + '\t' + '(6, ' + str(ids[str_token]) + ')\t' + \
                                  '标识符\t' + '(' + str(row) + ', ' + str(col) + ')\n'
                        col += 1
                    i += 1

                # 识别常数
                elif element[i].isdigit():
                    while i <= len(element) - 1 and element[i].isdigit():
                        str_token += element[i]
                        i += 1
                    i -= 1
                    if i == len(element) - 1 or is_arithmetic_operator(element[i + 1]) or is_relational_operator(element[i + 1]) or is_separator(element[i + 1]):
                        if str_token not in cis.keys():
                            cis[str_token] = ci_code
                            ci_code += 1
                        string += str_token + '\t' + '(5, ' + str(cis[str_token]) + ')\t' + \
                                  '常数\t' + '(' + str(row) + ', ' + str(col) + ')\n'
                        col += 1
                        i += 1
                    elif element[i + 1].isalpha():
                        j = i + 1
                        while j <= len(element) - 1 and element[j].isalpha():
                            j += 1
                        j -= 1
                        string += element[i: j + 1] + '\t' + 'Error\t' + 'Error\t' + '(' + str(row) + ', ' + str(col) + ')\n'
                        col += 1
                        i = j + 1
                    else:
                        i += 1

                # 识别算数运算符 '/' '-' '*'
                elif element[i] == '/' or element[i] == '-' or element[i] == '*':
                    str_token += element[i]
                    string += str_token + '\t' + '(3, ' + str(arithmetic_operators[str_token]) + ')\t' + \
                            '算数运算符\t' + '(' + str(row) + ', ' + str(col) + ')\n'
                    col += 1
                    i += 1

                # 识别算数运算符 '+'
                elif element[i] == '+':
                    if i < len(element) - 1 and is_arithmetic_operator(element[i + 1]):
                        string += element[i: i + 2] + '\t' + 'Error\t' + 'Error\t' + '(' + str(row) + ', ' + str(col) + ')\n'
                        col += 1
                        i += 2
                    else:
                        str_token += element[i]
                        string += str_token + '\t' + '(3, ' + str(arithmetic_operators[str_token]) + ')\t' + \
                                  '算数运算符\t' + '(' + str(row) + ', ' + str(col) + ')\n'
                        col += 1
                        i += 1

                # 识别关系运算符 '<' '<=' '<>'
                elif element[i] == '<':
                    if i < len(element) - 1 and is_relational_operator(element[i + 1]):
                        str_token += element[i: i+2]
                        string += str_token + '\t' + '(4, ' + str(relational_operators[str_token]) + ')\t' + \
                                  '关系运算符\t' + '(' + str(row) + ', ' + str(col) + ')\n'
                        col += 1
                        i += 2
                    else:
                        str_token = element[i]
                        string += str_token + '\t' + '(4, ' + str(relational_operators[str_token]) + ')\t' + \
                                  '关系运算符\t' + '(' + str(row) + ', ' + str(col) + ')\n'
                        col += 1
                        i += 1

                # 识别关系运算符 '>' '>='
                elif element[i] == '>':
                    if i < len(element) - 1 and element[i + 1] == '=':
                        str_token += element[i: i+2]
                        string += str_token + '\t' + '(4, ' + str(relational_operators[str_token]) + ')\t' + \
                                  '关系运算符\t' + '(' + str(row) + ', ' + str(col) + ')\n'
                        col += 1
                        i += 2
                    else:
                        str_token = element[i]
                        string += str_token + '\t' + '(4, ' + str(relational_operators[str_token]) + ')\t' + \
                                  '关系运算符\t' + '(' + str(row) + ', ' + str(col) + ')\n'
                        col += 1
                        i += 1

                # 识别关系运算符 '=' '=='
                elif element[i] == '=':
                    if i < len(element) - 1 and element[i + 1] == '=':
                        str_token += element[i: i+2]
                        string += str_token + '\t' + '(4, ' + str(relational_operators[str_token]) + ')\t' + \
                                  '关系运算符\t' + '(' + str(row) + ', ' + str(col) + ')\n'
                        col += 1
                        i += 2
                    else:
                        str_token = element[i]
                        string += str_token + '\t' + '(4, ' + str(relational_operators[str_token]) + ')\t' + \
                                  '关系运算符\t' + '(' + str(row) + ', ' + str(col) + ')\n'
                        col += 1
                        i += 1

                # 识别分界符
                elif is_separator(element[i]):
                    str_token += element[i]
                    string += str_token+ '\t' + '(2, ' + str(separators[str_token]) + ')\t' + \
                              '分界符\t' + '(' + str(row) + ', ' + str(col) + ')\n'
                    col += 1
                    i += 1

                # 错误
                else:
                    string += element[i] + '\t' + 'Error\t' + 'Error\t' + '(' + str(row) + ', ' + str(col) + ')\n'
                    col += 1
                    i += 1


class MyFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=-1, title='词法分析器', pos=wx.DefaultPosition,
                          size=wx.Size(1280, 720),
                          style=wx.MINIMIZE_BOX | wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN,
                          name='frame')

        self.icon = wx.Icon('icon.ico', type=wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)

        # 垂直布局
        vertical_box = wx.BoxSizer(wx.VERTICAL)

        flex_gird_sizer1 = wx.FlexGridSizer(1, 3, 0, 80)
        flex_gird_sizer1.SetFlexibleDirection(wx.BOTH)
        flex_gird_sizer1.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        # 创建提示文本
        self.static_text1 = wx.StaticText(self, wx.ID_ANY, "请选择文本", wx.DefaultPosition, wx.Size(160, -1))
        self.static_text1.Wrap(-1)
        flex_gird_sizer1.Add(self.static_text1, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        # 创建文件选择框
        self.file_picker_ctrl = wx.FilePickerCtrl(self, wx.ID_ANY, wx.EmptyString, "选择文本文件", "*.txt",
                                                  wx.DefaultPosition, wx.Size(660, -1),
                                                  wx.FLP_DEFAULT_STYLE | wx.FLP_SMALL)
        flex_gird_sizer1.Add(self.file_picker_ctrl, 0, wx.ALL, 5)

        # 添加确认按钮
        self.button = wx.Button(self, wx.ID_ANY, '确认', wx.DefaultPosition, wx.Size(240, -1))
        self.button.Bind(wx.EVT_BUTTON, self.button_on_button_click)
        flex_gird_sizer1.Add(self.button, 0, wx.ALL, 5)

        flex_gird_sizer2 = wx.FlexGridSizer(0, 1, 0, 0)
        flex_gird_sizer2.SetFlexibleDirection(wx.BOTH)
        flex_gird_sizer2.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        # 创建列表
        self.list_ctrl = wx.ListCtrl(self, -1, style=wx.LC_REPORT, size=wx.Size(1250, 720))
        self.list_ctrl.InsertColumn(0, '单词', wx.LIST_FORMAT_CENTER, width=312)
        self.list_ctrl.InsertColumn(1, '二元序列', wx.LIST_FORMAT_CENTER, width=312)
        self.list_ctrl.InsertColumn(2, '类型', wx.LIST_FORMAT_CENTER, width=312)
        self.list_ctrl.InsertColumn(3, '位置（行，列）', wx.LIST_FORMAT_CENTER, width=312)
        flex_gird_sizer2.Add(self.list_ctrl, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        vertical_box.Add(flex_gird_sizer1, 0, wx.EXPAND, 5)
        vertical_box.Add(flex_gird_sizer2, 0, wx.EXPAND, 5)

        self.SetSizer(vertical_box)
        self.Layout()
        self.Centre(wx.BOTH)

        self.parser = None
        self.dict = dict()

    # 点击按钮事件
    def button_on_button_click(self, event):
        self.list_ctrl.DeleteAllItems()
        self.analyze()

    # 文本分析
    def analyze(self):

        global string

        file_path = self.file_picker_ctrl.GetPath()
        word_list = get_list(file_path)
        recognition(word_list)

        string_lists = string.split('\n')

        # 添加至列表
        self.list_ctrl.DeleteAllItems()
        for s in string_lists:
            e = s.split('\t')
            index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), str(0))
            self.list_ctrl.SetItem(index, 0, e[0])
            self.list_ctrl.SetItem(index, 1, e[1])
            self.list_ctrl.SetItem(index, 2, e[2])
            self.list_ctrl.SetItem(index, 3, e[3])


if __name__ == '__main__':
    app = wx.App(False)
    frame = MyFrame(None)
    frame.Show(True)
    app.MainLoop()



