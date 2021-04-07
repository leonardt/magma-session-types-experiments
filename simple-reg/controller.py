import magma as m
import ast
import inspect
import textwrap
import sys
sys.path.append("../session/")

from session import Receive, Epsilon, Channel, Rec, Choose
from check import check


def get_ast(fn):
    return ast.parse(textwrap.dedent(inspect.getsource(fn)))


def get_types(init):
    collector = TypeCollector()
    collector.visit(get_ast(init))
    return collector.types


def controller(cls):
    check(cls.__call__)
    obj = cls()
    annotations = cls.__annotations__
    assert "state" in annotations
    state_T = annotations["state"]

    class Controller(m.Circuit):
        io = m.IO(state=m.Out(state_T))
        io += m.ClockIO()
        state = m.Register(state_T)()
        io.state @= state.O

    tree = ast.parse(textwrap.dedent(inspect.getsource(cls.__call__)))
    print(ast.dump(tree))
