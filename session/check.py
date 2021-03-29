import session
import ast
import inspect


class Checker(ast.NodeVisitor):
    def __init__(self, c_T):
        super().__init__()
        self.c_T = c_T
        self.offer_stack = []
        self.rec_Ts = {}

    def visit_Call(self, node):
        if isinstance(self.c_T, session.Rec):
            self.rec_Ts[self.c_T.name] = self.c_T.T
            self.c_T = self.c_T.T
        if isinstance(self.c_T, str):
            self.c_T = self.rec_Ts[self.c_T]
        match = (isinstance(node.func, ast.Attribute) and
                 isinstance(node.func.value, ast.Name) and
                 node.func.value.id == "c" and
                 node.func.attr in ["send", "receive", "offer", "choose",
                                    "close"])
        if not match:
            return
        if node.func.attr == "close":
            assert self.c_T is session.Epsilon
            self.c_T = None
        elif node.func.attr == "send":
            assert isinstance(self.c_T, session.Send)
            # TODO: Check datatype
            self.c_T = self.c_T.next
        elif node.func.attr == "receive":
            assert isinstance(self.c_T, session.Receive)
            # TODO: Check datatype
            self.c_T = self.c_T.next
        elif node.func.attr == "choose":
            assert len(node.args) == 1
            assert isinstance(node.args[0], ast.Str)
            next_T = list(filter(lambda x: x[0] == node.args[0].s,
                                 self.c_T.branches))
            assert len(next_T) == 1
            self.c_T = next_T[0][1]
        # elif node.func.attr == "offer":
        #     assert isinstance(self.c_T, session.Offer)
        #     self.offer_stack.append(self.c_T)
        else:
            raise NotImplementedError(node.func.attr)

    def visit_While(self, node):
        assert isinstance(node.test, ast.Constant) and node.test.value is True
        assert isinstance(self.c_T, session.Rec)
        curr_T = self.c_T
        self.c_T = curr_T.T
        for child in node.body:
            self.visit(child)
        self.c_T = None


    def visit_Return(self, node):
        assert self.c_T is None, self.c_T
        self.c_T = "returned"

    def visit_If(self, node):
        if isinstance(self.c_T, session.Rec):
            self.rec_Ts[self.c_T.name] = self.c_T.T
            self.c_T = self.c_T.T
        curr_T = self.c_T
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
            self.c_T = next_T[0][1]

        for child in node.body:
            self.visit(child)
        true_T = self.c_T
        if node.orelse:
            self.c_T = curr_T
            for child in node.orelse:
                self.visit(child)
            false_T = self.c_T
            if false_T != "returned" and true_T != "returned":
                assert true_T == false_T, (true_T, false_T)

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        assert self.c_T is None


def check(fn):
    annotations = fn.__annotations__
    assert 'c' in annotations
    c_T = annotations['c'].T
    tree = ast.parse(inspect.getsource(fn))
    Checker(c_T).visit(tree)
