from typing import Optional, MutableMapping
import libcst as cst
import libcst.matchers as match
from ast_tools.stack import SymbolTable
from ast_tools.passes import PASS_ARGS_T, Pass, apply_cst_passes
from ast_tools.cst_utils import to_module
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


class _ChannelRewriter(cst.CSTTransformer):
    def __init__(self):
        pass

    def leave_Parameters(self, original_node, updated_node):
        new_params = []
        for param in updated_node.params:
            # TODO: Check annotation
            if param.name.value == "chan":
                new_params.append(
                    cst.Param(
                        cst.Name(param.name.value + "_valid"),
                        # TODO: Assumes `m` symbol present
                        cst.Annotation(
                            cst.Attribute(cst.Name("m"), cst.Name("Bit"))
                        )
                    )
                )
                new_params.append(
                    cst.Param(
                        cst.Name(param.name.value + "_data"),
                        cst.Annotation(
                            cst.Subscript(
                                # TODO: Assumes `m` symbol present
                                cst.Attribute(cst.Name("m"), cst.Name("Bits")),
                                # TODO: Assumes width
                                [cst.SubscriptElement(cst.Index(cst.Integer("1")))]
                            )
                        )
                    )
                )
            else:
                new_params.append(param)

        return updated_node.with_changes(params=new_params)

    def leave_Call(self, original_node, updated_node):
        if match.matches(
            updated_node.func,
            match.Attribute(
                match.DoNotCare(),
                match.Name("receive")
            )
        ):
            # TODO: Assert we are checking a channel
            assert len(updated_node.args) == 1, "assume receive(<ENUM>)"
            chan_name = updated_node.func.value.value
            expected_value = updated_node.args[0].value
            return cst.BinaryOperation(
                cst.Name(chan_name + "_valid"),
                cst.BitAnd(),
                cst.Comparison(
                    cst.Name(chan_name + "_data"),
                    [cst.ComparisonTarget(cst.Equal(), expected_value)],
                    lpar=[cst.LeftParen()],
                    rpar=[cst.RightParen()]
                ),
                lpar=[cst.LeftParen()],
                rpar=[cst.RightParen()]
            )
        return updated_node


class _RewriteChannels(Pass):
    def rewrite(self,
                tree: cst.CSTNode,
                env: SymbolTable,
                metadata: MutableMapping) -> PASS_ARGS_T:
        rewriter = _ChannelRewriter()
        return tree.visit(rewriter), env, metadata


def controller(pre_passes=[], post_passes=[],
               debug: bool = False,
               env: Optional[SymbolTable] = None,
               path: Optional[str] = None,
               file_name: Optional[str] = None,
               annotations: Optional[dict] = None,
               manual_encoding: bool = False,
               reset_type: m.AbstractReset = None,
               has_enable: bool = False,
               reset_priority: bool = True):
    def inner(cls):
        return m.coroutine(
            pre_passes=pre_passes + [_RewriteChannels()],
            post_passes=post_passes,
            debug=debug,
            env=env,
            path=path,
            file_name=file_name,
            annotations=annotations,
            manual_encoding=manual_encoding,
            reset_type=reset_type,
            has_enable=has_enable,
            reset_priority=reset_priority,
        )(cls)

    return inner
