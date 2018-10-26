import wx
import wx.xrc


class Parser:
    """构造语法分析器"""
    def __init__(self, file_path):
        self.file_path = file_path
        self.first = dict()
        self.follow = dict()
        self.grammar = dict()
        self.table = dict()
        self.vt = set()
        self.vn = set()
        self.begin = str()

    def __is_vt(self, i):
        return i in self.vt

    def __is_vn(self, i):
        return i in self.vn

    def __is_epsilon(self, i):
        return i == 'ε'

    @staticmethod
    def __is_not_epsilon(i):
        return i != 'ε'

    @staticmethod
    def duplicate_removal(list):
        new_list = []
        for i in list:
            if i not in new_list:
                new_list.append(i)
        return new_list

    # 处理语法
    def get_grammar(self):
        file = open(self.file_path)
        for line in file.readlines():
            if line[0] in self.grammar.keys():
                self.grammar[line[0]] += line[3:].replace('\n', '').split('|')
            else:
                self.grammar[line[0]] = line[3:].replace('\n', '').split('|')
        self.begin = list(self.grammar.keys())[0]

    # 得到终结符集合
    def get_vt(self):
        for output_list in self.grammar.values():
            for string in output_list:
                for char in string:
                    if (not char.isupper()) and not self.__is_epsilon(char):
                        self.vt.add(char)

    # 得到非终结符集合
    def get_vn(self):
        for key in self.grammar.keys():
            self.vn.add(key)

    # 求FIRST集
    def get_first(self):
        # 初始化列表
        for k in self.grammar.keys():
            self.first[k] = list()
        for k in self.vt:
            self.first[k] = k
        self.first['ε'] = 'ε'

        for _ in range(len(self.grammar)):
            for k in self.grammar.keys():
                output_list = self.grammar[k]
                for string in output_list:

                    # 若X→aY或X->ε是一个产生式，则把a或ε加至FIRST(X)中
                    if self.__is_vt(string[0]) or self.__is_epsilon(string[0]):
                        self.first[k].extend(string[0])
                    else:

                        # 若X→Y...是一个产生式，则把FIRST(Y)/{ε}加至FIRST(X)中
                        temp_list = self.first[string[0]]
                        if 'ε' in temp_list:
                            temp_list.remove('ε')
                        self.first[k].extend(temp_list)

                    # 若X→Y1Y2…Yk是一个产生式，Y1，…，Yi-1都是非终结符，而且，对于任何j，1<=j<=i-1，FIRST(Yj)都含有ε(即Y1…Yi-1ε)，
                    # 则把FIRST(Yi)中的所有非ε-元素都加到FIRST(X)中；特别是，若所有的FIRST(Yj)均含有ε，j＝1，2，…，k，
                    # 则把ε加到FIRST(X)中
                    count = 0
                    while count < len(string) and self.__is_vn(string[count]) and 'ε' in self.first[string[count]]:
                        count += 1
                    if count == len(string):
                        self.first[k].extend(self.first[string[count - 1]])
                        self.first[k].extend('ε')
                    else:
                        if self.__is_vt(string[count]) and not self.__is_epsilon(string[count]):
                            self.first[k].extend(self.first[string[count]])

                    # 去掉列表中重复的元素
                    self.first[k] = self.duplicate_removal(self.first[k])

    # 求FOLLOW集
    def get_follow(self):
        for k in self.grammar.keys():
            self.follow[k] = list()
            if k == self.begin:
                self.follow[k].append('#')
        for _ in range(len(self.grammar)):
            for k in self.grammar.keys():
                output_list = self.grammar[k]
                for string in output_list:

                    # 若A→αB是一个产生式，则把FOLLOW(A)加至FOLLOW(B)中
                    if self.__is_vn(string[len(string) - 1]):
                        self.follow[string[len(string) - 1]].extend(self.follow[k])
                        self.follow[string[len(string) - 1]] = list(filter(self.__is_not_epsilon, self.follow[string[len(string) - 1]]))  # 去除空串

                    for i in range(len(string) - 1):
                        # 若A→αBβ是一个产生式，则把FIRST(β)\{ε}加至FOLLOW(B)中；
                        if self.__is_vn(string[i]):
                            if self.__is_vn(string[i + 1]):
                                self.follow[string[i]].extend(self.first[string[i + 1]])

                                # 利用filter方法去掉'ε'
                                self.follow[string[i]] = list(filter(self.__is_not_epsilon, self.follow[string[i]]))

                            if self.__is_vt(string[i + 1]):
                                self.follow[string[i]].append(string[i + 1])

                            # A→αBβ是一个产生式而(即ε属于FIRST(β))，则把FOLLOW(A)加至FOLLOW(B)中
                            empty_flag = True
                            for j in range(i + 1, len(string)):
                                if not self.__is_vn(string[j]) or (self.__is_vn(string[j]) and 'ε' not in self.first[string[j]]):
                                    empty_flag = False
                                    break
                            if empty_flag:
                                self.follow[string[i]].extend(self.follow[k])

                                # 利用filter方法去掉'ε'
                                self.follow[string[i]] = list(filter(self.__is_not_epsilon, self.follow[string[i]]))

            # 去掉列表中重复的元素
            for k in self.follow.keys():
                self.follow[k] = self.duplicate_removal(self.follow[k])

    def create_table(self):
        # 初始化分析表
        for k in self.grammar.keys():
            self.table[k] = dict()
            for e in self.vt:
                self.table[k][e] = None
            self.table[k]['ε'] = None
            self.table[k]['#'] = None

        # 对每个终结符a属于FIRST(α)，把A→α加至M[A，a]中，若ε属于FIRST(α)，则对任何b属于FOLLOW(A)把A→α加至M[A，b]中。
        for k in self.grammar.keys():
            output_list = self.grammar[k]
            for string in output_list:
                for e in self.first[string[0]]:
                    self.table[k][e] = string
                    if self.__is_epsilon(e):
                        for a in self.follow[k]:
                            self.table[k][a] = string


class MyFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=-1, title='LL(1)文法分析器', pos=wx.DefaultPosition,
                          size=wx.Size(1280, 720),
                          style=wx.MINIMIZE_BOX | wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN,
                          name='frame')

        self.icon = wx.Icon('icon.ico', type=wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)

        # 垂直布局
        vertical_box = wx.BoxSizer(wx.VERTICAL)

        flex_gird_sizer1 = wx.FlexGridSizer(2, 3, 0, 80)
        flex_gird_sizer1.SetFlexibleDirection(wx.BOTH)
        flex_gird_sizer1.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        # 创建提示文本
        self.static_text1 = wx.StaticText(self, wx.ID_ANY, "选择文法文本", wx.DefaultPosition, wx.Size(160, -1))
        self.static_text1.Wrap(-1)
        flex_gird_sizer1.Add(self.static_text1, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        # 创建文件选择框
        self.file_picker_ctrl = wx.FilePickerCtrl(self, wx.ID_ANY, wx.EmptyString, "选择文本文件", "*.txt", wx.DefaultPosition, wx.Size(660, -1), wx.FLP_DEFAULT_STYLE | wx.FLP_SMALL)
        flex_gird_sizer1.Add(self.file_picker_ctrl, 0, wx.ALL, 5)

        # 添加确认按钮
        self.button1 = wx.Button(self, wx.ID_ANY,  '检查', wx.DefaultPosition, wx.Size(240, -1))
        self.button1.Bind(wx.EVT_BUTTON, self.button_on_button1_click)
        flex_gird_sizer1.Add(self.button1, 0, wx.ALL, 5)
         
        # 创建提示文本
        self.static_text = wx.StaticText(self, wx.ID_ANY, '输入待分析的语句', wx.DefaultPosition, wx.Size(160, -1))
        self.static_text.Wrap(-1)
        flex_gird_sizer1.Add(self.static_text, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        # 创建输入文本框
        self.text_ctrl = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.Point(-1, -1), wx.Size(660, -1))
        flex_gird_sizer1.Add(self.text_ctrl, 0, wx.ALL, 5)

        # 添加确认按钮
        self.button = wx.Button(self, wx.ID_ANY,  '确认', wx.DefaultPosition, wx.Size(240, -1))
        self.button.Bind(wx.EVT_BUTTON, self.button_on_button_click)
        flex_gird_sizer1.Add(self.button, 0, wx.ALL, 5)

        flex_gird_sizer2 = wx.FlexGridSizer(0, 1, 0, 0)
        flex_gird_sizer2.SetFlexibleDirection(wx.BOTH)
        flex_gird_sizer2.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        # 创建列表
        self.list_ctrl = wx.ListCtrl(self, -1, style=wx.LC_REPORT, size=wx.Size(1250, 720))
        self.list_ctrl.InsertColumn(0, '步骤', wx.LIST_FORMAT_CENTER, width=250)
        self.list_ctrl.InsertColumn(1, '分析栈', wx.LIST_FORMAT_CENTER, width=250)
        self.list_ctrl.InsertColumn(2, '剩余输入串', wx.LIST_FORMAT_CENTER, width=250)
        self.list_ctrl.InsertColumn(3, '所用产生式', wx.LIST_FORMAT_CENTER, width=250)
        self.list_ctrl.InsertColumn(4, '动作', wx.LIST_FORMAT_CENTER, width=250)
        flex_gird_sizer2.Add(self.list_ctrl, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)

        vertical_box.Add(flex_gird_sizer1, 0, wx.EXPAND, 5)
        vertical_box.Add(flex_gird_sizer2, 0, wx.EXPAND, 5)

        self.SetSizer(vertical_box)
        self.Layout()
        self.Centre(wx.BOTH)

        self.parser = None
        self.dict = dict()

    # 点击按钮事件
    def button_on_button1_click(self, event):
        self.list_ctrl.DeleteAllItems()
        file_path = self.file_picker_ctrl.GetPath()
        self.parser = Parser(file_path)
        self.parser.get_grammar()
        self.eliminate_left_recursion()
        self.parser.get_vt()
        self.parser.get_vn()
        self.parser.get_first()
        self.parser.get_follow()
        if self.__is_ll1():
            wx.MessageBox('文法为LL(1)文法', 'Correct', wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox('文法非LL(1)文法，请重新选择文法', 'Wrong', wx.OK | wx.ICON_ERROR)

    # 点击按钮事件
    def button_on_button_click(self, event):
        self.parser.create_table()
        self.analyze()

    # 消除直接左递归
    @staticmethod
    def __eliminate_direct_left_recursion(grammar, vn):
        list1 = list()
        list2 = list()
        for string in grammar[vn]:
            if string[0] == vn:
                list1.append(string[1:])
            else:
                list2.append(string)

        # 无直接左递归
        if list1:
            for i in range(len(list1)):
                list1[i] += 'Z'
            for i in range(len(list2)):
                list2[i] += 'Z'
            list1.append('ε')
            grammar[vn] = list2
            grammar['Z'] = list1

        return grammar

    # 判断是否为LL1(1)文法
    def __is_ll1(self):
        correct = True
        for vn in self.parser.vn:
            temp_first_list = list()
            for i in range(len(self.parser.grammar[vn]) - 1):

                # 对于文法中每一个非终结符A的各个产生式的候选首符集两两不相交。即，若
                # A→α1|α2|…|αn
                # 则FIRST(αi)∩FIRST(αj)＝Φ   (i != j)
                temp_first_list = list(set(self.parser.first[self.parser.grammar[vn][i][0]]).intersection(set(self.parser.first[self.parser.grammar[vn][i + 1][0]])))

                # 对文法中的每个非终结符A，若它存在某个候选首符集包含ε，则
                # FIRST(αi)∩FOLLOW(A)=Φ
                # i=1,2,...,n
                if 'ε' in self.parser.first[self.parser.grammar[vn][i][0]]:
                    if list(set( self.parser.first[self.parser.grammar[vn][i][0]]).intersection(set(self.parser.follow[vn]))):
                        correct = False
                        break
            if temp_first_list:
                correct = False
                break
        return correct

    # 消除左递归
    def eliminate_left_recursion(self):

        # 1. 把文法G的所有非终结符按任一种顺序排列成P1，P2，…，Pn；按此顺序执行；
        # 2. FOR  i:=1  TO  n  DO
        # BEGIN
        # FOR  j:=1  TO  i-1  DO
        #     把形如Pi→Pj的规则改写成
        #     Pi→1|2|…|k ;
        #     (其中Pj→1|2|…|k是关于Pj的所有规则)
        # 消除关于Pi规则的直接左递归性
        # END
        grammar = self.parser.grammar
        vn_list = list(grammar.keys())
        for i in range(len(vn_list)):
            for j in range(i):

                is_exit = False
                index = 0
                string_list = grammar[vn_list[i]]
                for string in string_list:
                    if string[0] == vn_list[j]:
                        is_exit = True
                        break
                    else:
                        index += 1
                if is_exit:
                    left_string = grammar[vn_list[i]][index][1:]
                    new_lists = grammar[vn_list[j]][:]
                    for k in range(len(new_lists)):
                        new_lists[k] += left_string
                    del grammar[vn_list[i]][index]
                    grammar[vn_list[i]].extend(new_lists)
                    grammar[vn_list[i]] = self.parser.duplicate_removal(grammar[vn_list[i]])

            # 消除关于Pi规则的直接左递归性
            grammar = self.__eliminate_direct_left_recursion(grammar, vn_list[i])

    # 文法分析
    def analyze(self):

        wx.MessageBox('FIRST集\n' + str(self.parser.first), 'Correct', wx.OK | wx.ICON_INFORMATION)
        wx.MessageBox('FOLLOW集\n' + str(self.parser.first), 'Correct', wx.OK | wx.ICON_INFORMATION)
        wx.MessageBox('分析表\n' + str(self.parser.table), 'Correct', wx.OK | wx.ICON_INFORMATION)


        # 得到并处理输入语句
        string = self.text_ctrl.GetValue()
        string = list(string[1:])

        # 分析步骤
        count = 0

        # 初始化分析表
        stack = list()
        stack.append('#')  # "#"入栈
        stack.append(self.parser.begin)  # 开始符入栈
        self.dict.clear()
        self.dict[count] = (str(count), ''.join(stack), ''.join(string), ' ', '初始化')

        correct = True
        while correct:
            # 取栈顶符号
            count += 1
            current = stack.pop()

            # 分析成功结束
            if current == string[0] == '#':
                self.dict[count] = (str(count), '分', '析', '成', '功')
                break

            # 匹配终结符
            if current in self.parser.vt and current == string[0]:
                string = string[1:]
                self.dict[count] = (str(count), ''.join(stack), ''.join(string), ' ', 'GETNEXT(' + current + ')')
                continue

            # 匹配非终结符
            if string[0] in self.parser.vt or string[0] == '#':
                new_str = self.parser.table[current][string[0]]
            else:
                self.dict[count] = (str(count), ''.join(stack), ''.join(string), '错误：', '非法输入')
                correct = False

            if new_str is None:
                self.dict[count] = (str(count), ''.join(stack), ''.join(string), '错误：', '产生式不存在')
                correct = False

            # 产生式为ε
            elif new_str == 'ε':
                self.dict[count] = (str(count), ''.join(stack), ''.join(string), current + '->ε', 'POP')

            # 将产生式倒置入栈
            else:
                for c in reversed(new_str):
                    stack.append(c)
                self.dict[count] = (str(count), ''.join(stack), ''.join(string), current + '->' +
                                    ''.join(new_str), 'POP,PUSH(' + new_str[::-1] + ')')

        # 添加至列表
        self.list_ctrl.DeleteAllItems()
        for key, value in self.dict.items():
            index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), str(key))
            self.list_ctrl.SetItem(index, 0, value[0])
            self.list_ctrl.SetItem(index, 1, value[1])
            self.list_ctrl.SetItem(index, 2, value[2])
            self.list_ctrl.SetItem(index, 3, value[3])
            self.list_ctrl.SetItem(index, 4, value[4])


if __name__ == '__main__':
    app = wx.App(False)
    frame = MyFrame(None)
    frame.Show(True)
    app.MainLoop()
