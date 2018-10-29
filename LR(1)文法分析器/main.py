import copy
import queue
import wx
import wx.xrc


class Parser:
    """
        LR(1)语法分析器
    """

    def __init__(self, file_path):
        self.file_path = file_path
        self.vn = list()
        self.vt = list()
        # 开始符号
        self.start = None
        self.grammar = list()
        # 求FIRST集所构造的字典数据结构文法
        self.dict_grammar = dict()
        self.first = dict()
        # 项目
        self.project = list()
        # 存放状态编号及对应的项目集
        self.status = dict()
        # GOTO表
        self.goto = dict()
        # ACTION表
        self.action = dict()

    # 读取文法
    def read_grammar(self):
        with open(self.file_path) as file:
            for line in file:
                lists = line[3:].replace('\n', "").split('|')
                for element in lists:
                    self.grammar.append(line[0:3] + element)
            file.close()
        self.start = self.grammar[0][0]

    # 读取字典数据结构语法
    def get_dict_grammar(self):
        file = open(self.file_path)
        for line in file.readlines():
            if line[0] in self.dict_grammar.keys():
                self.dict_grammar[line[0]] += line[3:].replace('\n', '').split('|')
            else:
                self.dict_grammar[line[0]] = line[3:].replace('\n', '').split('|')

    # 找到终结符和非终结符
    def get_vt_vn(self):
        temp_vt = []
        for i in range(len(self.grammar)):
            x, y = self.grammar[i].split('->')
            if x not in self.vn:
                self.vn.append(x)
            for yi in y:
                temp_vt.append(yi)
        for i in temp_vt:
            if i not in self.vn and i not in self.vt:
                self.vt.append(i)

    # 建立项目
    def get_project(self):
        for f in self.grammar:
            temporary = copy.deepcopy(f)
            temporary = temporary.split('->')
            # 产生式左部
            l = temporary[0]
            # 产生式右部
            r = list(temporary[1])
            # 对产生式右部处理
            for i in range(len(r) + 1):
                temporary1 = copy.deepcopy(r)
                temporary1.insert(i, '·')
                newf = l + '->' + ''.join(temporary1)
                self.project.append(newf)

    # 列表去重
    @staticmethod
    def __duplicate_removal(list):
        new_list = []
        for i in list:
            if i not in new_list:
                new_list.append(i)
        return new_list

    # 求FIRST集
    def get_first(self):
        for k in self.dict_grammar.keys():
            self.first[k] = list()
        for k in self.vt:
            self.first[k] = [k]
        self.first['ε'] = ['ε']
        for _ in range(len(self.dict_grammar)):
            for k in self.dict_grammar.keys():
                output_list = self.dict_grammar[k]
                for string in output_list:
                    if string[0] in self.vt or string[0] == 'ε':
                        self.first[k].extend(string[0])
                    else:
                        temp_list = self.first[string[0]]
                        if 'ε' in temp_list:
                            temp_list.remove('ε')
                        self.first[k].extend(temp_list)
                    count = 0
                    while count < len(string) and string[count] in self.vn and 'ε' in self.first[string[count]]:
                        count += 1
                    if count == len(string):
                        self.first[k].extend(self.first[string[count - 1]])
                        self.first[k].extend('ε')
                    else:
                        if string[count] in self.vt and not string[count] == 'ε':
                            self.first[k].extend(self.first[string[count]])
                    self.first[k] = self.__duplicate_removal(self.first[k])

    # 得到FIRST(βb)列表
    def __get_first(self, string, source):
        if len(string) == 1:
            first = self.first[string]
            if first == ['ε']:
                return source
            else:
                return first
        else:
            i = 0
            while i < len(string) and self.first[string[i]] == ['ε']:
                i += 1
            if i > len(string):
                return source
            else:
                return self.first[string[i]]

    # 求项目pro的闭包
    def closure(self, pro):
        # 最终返回的结果
        temporary = list()
        # 将pro自身加入
        temporary.append(pro)
        # 左部
        l1 = pro[0].split('->')[0]
        # 右部
        r1 = pro[0].split('->')[1]
        # 存放右部的列表
        x = list(r1)
        # 得到圆点位置
        index = x.index('·')
        # S->·
        if len(x) == 1:
            return self.__duplicate_removal(temporary)
        else:
            # E->a·
            if index == len(r1) - 1:
                return self.__duplicate_removal(temporary)
            # E->...·a...
            elif x[index + 1] in self.vt:
                return self.__duplicate_removal(temporary)
            # E->...a·A...
            else:
                for elem in range(len(self.project)):
                    # 左部
                    l = self.project[elem].split('->')[0]
                    # 右部
                    r = self.project[elem].split('->')[1]
                    # 继续求B->·γ闭包
                    if l == x[index + 1] and r.startswith('·'):
                        if index == len(r1) - 2:
                            new_list = [self.project[elem], pro[1]]
                        else:
                            first = self.__get_first(r1[index + 2:], pro[1])
                            new_list = [self.project[elem], first]
                        if new_list == pro:
                            return self.__duplicate_removal(temporary)
                        conlist = self.generate_list(self.closure(new_list))
                        if len(conlist) == 0:
                            pass
                        else:
                            temporary.extend(conlist)
                            temporary = self.generate_list(self.__duplicate_removal(temporary))
                return self.__duplicate_removal(temporary)

    # 计算项目集的GO(I,x)
    def go(self, project):
        # 存放GO(I,x)结果
        go = dict()
        for elem in project:
            # 项目左部
            l = elem[0].split('->')[0]
            # 项目右部
            r = elem[0].split('->')[1]
            # 返回·的位置
            index = list(r).index('·')
            # 不是S->a·形式
            if not r.endswith('·'):
                # 说明x所对应的go中没有项目
                if go.get(list(r)[index + 1]) is None:
                    temporary = list(r)
                    temporary.insert(index + 2, '·')
                    # 将·后移一位
                    temporary.remove('·')
                    # 产生一个完整的项目
                    x = [l + '->' + ''.join(temporary), elem[1]]
                    # 将该项目对应的项目集加入x的go中
                    go[list(r)[index + 1]] = self.generate_list(self.closure(x))
                # 说明x所对应的go中已有项目
                else:
                    temporary = list(r)
                    temporary.insert(index + 2, '·')
                    # 将·后移一位
                    temporary.remove('·')
                    # 产生一个完整的项目
                    x = [l + '->' + ''.join(temporary), elem[1]]
                    go[list(r)[index + 1]].extend(self.closure(x))
        return go

    # 判断两项目集是否相等
    @staticmethod
    def __is_equal(a, b):
        if len(a) != len(b):
            return False
        else:
            t = 0
            for i in range(len(a)):
                j = 0
                while j < len(b):
                    if a[i][0] == b[j][0] and set(a[i][1]) != set(b[i][1]):
                        return False
                    if a[i][0] == b[i][0]:
                        break
                    j += 1
                if j < len(b):
                    t += 1
            if t == len(a):
                return True
            else:
                return False

    # 合并一个项目中状态
    def generate_list(self, list):
        l = list
        for i in range(len(l)):
            j = i + 1
            while j < len(l):
                if l[i][0] == l[j][0]:
                    l[i][1] = self.__duplicate_removal(l[i][1] + l[j][1])
                    del l[j]
                j += 1
        return l

    # 建立识别活前缀的DFA
    def create_dfa(self):
        # 初始状态编号为0
        number = 0
        # 初态
        first0 = 'S->·' + self.start
        first = [first0, ['#']]
        # 初态闭包
        x = self.generate_list(self.closure(first))
        self.status[number] = x
        # 构造队列，用于存放得到的状态
        qu = queue.Queue()
        # 把初始状态加入队列中
        qu.put({number: self.status[number]})
        number += 1
        while not qu.empty():
            temporary = qu.get()
            for k, v in temporary.items():
                # 求项目集的GO(I,x)
                y = self.go(v)
                for key, value in y.items():
                    # 标志位，判断value是否是新的状态
                    flag = -1
                    for ke, va in self.status.items():
                        if self.__is_equal(value, va):
                            flag = ke
                            break
                    # 新的状态，加入状态集中
                    if flag == -1:
                        self.status[number] = value
                        qu.put({number: self.status[number]})
                        number += 1

    # goto表
    def create_goto(self):
        number = -1
        for i in range(len(self.status)):
            self.goto[i] = {}
            # 每个状态的GO
            temp = self.go(self.status[i])
            for vn in self.vn:
                # 非终结符存在于状态的GO中
                if vn in temp.keys():
                    for key, value in self.status.items():
                        if self.__is_equal(value, temp[vn]):
                            number = key
                            break
                    self.goto[i][vn] = number
                else:
                    self.goto[i][vn] = ' '

    def create_action(self):
        vtx = copy.deepcopy(self.vt)
        # 终结符加‘#’
        vtx.append('#')
        for i in range(len(self.status)):
            # 初始化
            self.action[i] = {}
            for vt in vtx:
                self.action[i][vt] = ' '
            # 移进项目
            temp = self.go(self.status[i])
            for vt in vtx:
                if vt in temp.keys():
                    # 确定到哪一个状态
                    for key, value in self.status.items():
                        if self.__is_equal(value, temp[vt]):
                            number = key
                            break
                    self.action[i][vt] = 's' + str(number)
            # 规约项目
            for list in self.status[i]:
                index = list[0].index('·')
                if index == len(list[0]) - 1:
                    temp = list[0].rstrip('·')
                    m = -1
                    for n in range(len(self.grammar)):
                        if self.grammar[n] == temp:
                            # 产生式在G'中下标从1开始
                            m = n + 1
                            break
                    for vt in list[1]:
                        if m != -1:
                            self.action[i][vt] = 'r' + str(m)
            # 接受项目
            for list in self.status[i]:
                index = list[0].index('·')
                if list[0].startswith('S') and index == len(list[0]) - 1:
                    self.action[i]['#'] = 'acc'


class MyFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=-1, title='LR(1)文法分析器', pos=wx.DefaultPosition,
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
        self.file_picker_ctrl = wx.FilePickerCtrl(self, wx.ID_ANY, wx.EmptyString, "选择文本文件", "*.txt",
                                                  wx.DefaultPosition, wx.Size(660, -1),
                                                  wx.FLP_DEFAULT_STYLE | wx.FLP_SMALL)
        flex_gird_sizer1.Add(self.file_picker_ctrl, 0, wx.ALL, 5)
        # 添加确认按钮
        self.button1 = wx.Button(self, wx.ID_ANY, '检查', wx.DefaultPosition, wx.Size(240, -1))
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
        self.button = wx.Button(self, wx.ID_ANY, '确认', wx.DefaultPosition, wx.Size(240, -1))
        self.button.Bind(wx.EVT_BUTTON, self.button_on_button_click)
        flex_gird_sizer1.Add(self.button, 0, wx.ALL, 5)
        flex_gird_sizer2 = wx.FlexGridSizer(0, 1, 0, 0)
        flex_gird_sizer2.SetFlexibleDirection(wx.BOTH)
        flex_gird_sizer2.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
        # 创建列表
        self.list_ctrl = wx.ListCtrl(self, -1, style=wx.LC_REPORT, size=wx.Size(1250, 720))
        self.list_ctrl.InsertColumn(0, '步骤', wx.LIST_FORMAT_CENTER, width=240)
        self.list_ctrl.InsertColumn(1, '状态栈', wx.LIST_FORMAT_CENTER, width=240)
        self.list_ctrl.InsertColumn(2, '符号栈', wx.LIST_FORMAT_CENTER, width=240)
        self.list_ctrl.InsertColumn(3, '输入串', wx.LIST_FORMAT_CENTER, width=240)
        self.list_ctrl.InsertColumn(4, '动作说明', wx.LIST_FORMAT_CENTER, width=290)
        flex_gird_sizer2.Add(self.list_ctrl, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)
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
        self.parser.read_grammar()
        self.parser.get_dict_grammar()
        self.parser.get_vt_vn()
        self.parser.get_first()
        self.parser.get_project()
        self.parser.create_dfa()
        self.parser.create_action()
        self.parser.create_goto()
        wx.MessageBox('文法读取成功', 'Correct', wx.OK | wx.ICON_INFORMATION)
        wx.MessageBox(self.output(), 'Correct', wx.OK | wx.ICON_INFORMATION)
        wx.MessageBox(self.show(), 'Correct', wx.OK | wx.ICON_INFORMATION)

    # 点击按钮事件
    def button_on_button_click(self, event):
        self.analyze()

    # 输出分析表
    def output(self):
        s = str()
        s += '{:^60}'.format('LR(1)分析表') + '\n'
        s += '{:^30} {:^30} {:^30}'.format('状态', 'ACTION', 'GOTO') + '\n'
        s += '\n'
        s += '{:^12} '.format(' ')
        for vt in self.parser.vt:  # action
            s += '{:^12}'.format(vt)
        s += '{:^12}'.format('#')
        for vn in self.parser.vn:  # goto
            s += '{:^12}'.format(vn)
        s += '\n'
        vtx = copy.deepcopy(self.parser.vt)
        vtx.append('#')
        for i in range(len(self.parser.status)):  # 输出每一行
            s += '{:^12}'.format(str(i))
            for vt in vtx:
                for key in self.parser.action[i]:  # {0:{'b':'S1'}}
                    if vt == key:
                        s += '{:^12}'.format(self.parser.action[i][key])
                        break
            for vn in self.parser.vn:
                for key in self.parser.goto[i]:
                    if vn == key:
                        s += '{:^12}'.format(str(self.parser.goto[i][key]))
                        break
            s += '\n'
        return s

    # 显示各个状态及对应的项目集
    def show(self):
        s = '所有状态及对应的项目集:\n'
        for key in self.parser.status.keys():
            s += str(key) + ': \n'
            for val in self.parser.status[key]:
                s += str(val) + '\n'
            s += '\n\n'
        return s

    # 统计产生式右部的个数
    @staticmethod
    def count_right_num(grammar_i):
        return len(grammar_i) - 3

    def analyze(self):
        step = 0
        self.dict.clear()
        status_stack = list()
        symbol_stack = list()
        input_str = self.text_ctrl.GetValue()
        location = 0
        symbol_stack.append('#')
        status_stack.append(0)
        correct = True
        while correct:
            step += 1
            now_state = status_stack[-1]
            input_ch = input_str[location]
            find = self.parser.action[now_state][input_ch]
            if find == 'acc':
                break
            elif find == ' ':
                correct = False
                break
            elif find[0] == 's':
                st = 'ACTION[%s][%s]=s%s，状态=%s入栈' % (now_state, input_ch, find[1:], find[1:])
                self.dict[step] = (
                str(step), ''.join('%s' % id for id in status_stack), ''.join('%s' % id for id in symbol_stack),
                ''.join(input_str[location:]), st)
                symbol_stack.append(input_ch)
                status_stack.append(int(find[1:]))
                location += 1
            elif find[0] == 'r':
                num = int(find[1:])
                g = self.parser.grammar[num - 1]
                ss1 = status_stack[:]
                ss2 = symbol_stack[:]
                right_num = self.count_right_num(g)
                for i in range(right_num):
                    status_stack.pop()
                    symbol_stack.pop()
                symbol_stack.append(g[0])
                now_state = status_stack[-1]
                symbol_ch = symbol_stack[-1]
                find = self.parser.goto[now_state][symbol_ch]
                if find == '':
                    correct = False
                    break
                status_stack.append(find)
                st = 'r%s: %s规约，GOTO(%s，%s)=%s入栈' % (num, g, status_stack[-2], symbol_stack[-1], find)
                self.dict[step] = (str(step), ''.join('%s' % id for id in ss1), ''.join('%s' % id for id in ss2),
                                   ''.join(input_str[location:]), st)
        if correct:
            st = "Acc: 分析成功"
            self.dict[step] = (
            str(step), ''.join('%s' % id for id in status_stack), ''.join('%s' % id for id in symbol_stack),
            ''.join(input_str[location:]), st)
        else:
            st = 'Error: 分析失败'
            self.dict[step] = (
            str(step), ''.join('%s' % id for id in status_stack), ''.join('%s' % id for id in symbol_stack),
            ''.join(input_str[location:]), st)
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
