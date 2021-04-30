import session
import ast
import inspect
import textwrap


_SESSION_FUNCS = ["send", "receive", "offer", "choose", "close"]


class Checker(ast.NodeVisitor):
    def __init__(self, name, type_, filename, line_offset):
        super().__init__()
        self.name = name
        self.type_ = type_
        self.offer_stack = []
        self.rec_Ts = {}
        self.filename = filename
        self.line_offset = line_offset

    def _get_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute) and node.attr in _SESSION_FUNCS:
            return self._get_name(node.value)
        if isinstance(node, ast.Call):
            return self._get_name(node.func)
        raise NotImplementedError(ast.dump(node), type(node))

    def visit_Call(self, node):
        if isinstance(self.type_, session.Rec):
            exit(1)
            self.rec_Ts[self.type_.name] = self.type_.T
            self.type_ = self.type_.T
        if isinstance(self.type_, str):
            self.type_ = self.rec_Ts[self.type_]
        self.visit(node.func)
        match = (isinstance(node.func, ast.Attribute) and
                 node.func.attr in _SESSION_FUNCS and
                 self._get_name(node.func.value) == self.name and
                 node.func.attr in _SESSION_FUNCS)
        if not match:
            return
        if node.func.attr == "close":
            if self.type_ is not session.Epsilon:
                with open(self.filename) as f:
                    file_str = f.read().splitlines()
                lineno = node.lineno + self.line_offset - 1
                raise SyntaxError(
                    f"Expected type Epsilon when calling closed, found "
                    f"{self.type_} instead",
                    (self.filename, lineno, node.col_offset, file_str[lineno])
                )
            assert self.type_ is session.Epsilon
            self.type_ = None
        elif node.func.attr == "send":
            assert isinstance(self.type_, session.Send)
            # TODO: Check datatype
            self.type_ = self.type_.next
        elif node.func.attr == "receive":
            if not isinstance(self.type_, session.Receive):
                with open(self.filename) as f:
                    file_str = f.read().splitlines()
                lineno = node.lineno + self.line_offset - 1
                raise SyntaxError(
                    f"Expected type Receive when calling receive, found "
                    f"{self.type_} instead",
                    (self.filename, lineno, node.col_offset, file_str[lineno])
                )
            # TODO: Check datatype
            self.type_ = self.type_.next
        elif node.func.attr == "choose":
            assert len(node.args) == 1
            assert isinstance(node.args[0], ast.Str)
            next_T = list(filter(lambda x: x[0] == node.args[0].s,
                                 self.type_.branches))
            assert len(next_T) == 1
            self.type_ = next_T[0][1]
        # elif node.func.attr == "offer":
        #     assert isinstance(self.type_, session.Offer)
        #     self.offer_stack.append(self.type_)
        else:
            raise NotImplementedError(node.func.attr)

    def visit_While(self, node):
        assert isinstance(node.test, ast.Constant) and node.test.value is True
        assert isinstance(self.type_, session.Rec)
        curr_T = self.type_
        self.type_ = curr_T.T
        for child in node.body:
            self.visit(child)
        self.type_ = None

    def visit_Return(self, node):
        assert self.type_ is None, self.type_
        self.type_ = "returned"

    def visit_If(self, node):
        if isinstance(self.type_, session.Rec):
            self.rec_Ts[self.type_.name] = self.type_.T
        curr_T = self.type_
        # TODO: Check all offers are matched
        is_offer = (isinstance(node.test, ast.Call) and
                    isinstance(node.test.func, ast.Attribute) and
                    isinstance(node.test.func.value, ast.Name) and
                    node.test.func.value.id == "c" and
                    node.test.func.attr == "offer")
        if is_offer:
            assert len(node.test.args) == 1
            assert isinstance(node.test.args[0], ast.Str)
            print(curr_T)
            assert isinstance(curr_T, session.Offer)
            next_T = list(filter(lambda x: x[0] == node.test.args[0].s,
                                 curr_T.branches))
            assert len(next_T) == 1
            self.type_ = next_T[0][1]

        for child in node.body:
            self.visit(child)
        if isinstance(self.type_, str) and self.type_ != "returned":
            self.type_ = self.rec_Ts[self.type_]
        true_T = self.type_
        if node.orelse:
            self.type_ = curr_T
            for child in node.orelse:
                self.visit(child)
            if isinstance(self.type_, str) and self.type_ != "returned":
                self.type_ = self.rec_Ts[self.type_]
            false_T = self.type_
            if false_T != "returned" and true_T != "returned":
                assert true_T == false_T, (true_T, false_T)
        if true_T == "returned":
            self.type_ = curr_T

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        assert self.type_ is None


def check(fn):
    annotations = fn.__annotations__
    caller = inspect.getframeinfo(inspect.stack()[1][0])
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))

    for key, value in fn.__annotations__.items():
        if not isinstance(value, session.Channel):
            continue
        Checker(key, value.T, caller.filename, caller.lineno - 2).visit(tree)
