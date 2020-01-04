"""
Calculate strings as math arguments.
Note:
    Numbers and operators within string must be separated with spaces.
"""


class Calculator:
    @staticmethod
    def evaluate(string: str) -> float:
        """
        Use to evaluate math strings
        :param string: str, '1 + 2 * 3'
        :return: float, 7
        """
        s = string.split(' ')

        flag = False
        for x in ['/', '*', '+', '-']:
            if x in string:
                flag = True
        if not flag:
            return float(string)

        elif len(s) == 1:
            return float(s[0])

        def div():
            for i, c in enumerate(s):
                if c == '/':
                    temp = float(s[i-1]) / float(s[i+1])
                    s[i-1:i+2] = [temp]
                    break

        def mul():
            for i, c in enumerate(s):
                if c == '*':
                    temp = float(s[i-1]) * float(s[i+1])
                    s[i - 1:i + 2] = [temp]
                    break

        def add():
            for i, c in enumerate(s):
                if c == '+':
                    temp = float(s[i-1]) + float(s[i+1])
                    s[i - 1:i + 2] = [temp]
                    break

        def sub():
            for i, c in enumerate(s):
                if c == '-':
                    temp = float(s[i-1]) - float(s[i+1])
                    s[i - 1:i + 2] = [temp]
                    break

        while '*' in s or '/' in s:
            for x in s:
                if x == '*':
                    mul()
                    s = [c for c in s]
                    break

                elif x == '/':
                    div()
                    s = [c for c in s]
                    break

                else:
                    continue

        while '+' in s or '-' in s:
            for x in s:
                if x == '+':
                    add()
                    s = [c for c in s]
                    break

                elif x == '-':
                    sub()
                    s = [c for c in s]
                    break

                else:
                    continue

        return float(sum(s))
