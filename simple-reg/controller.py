from typing import Optional, MutableMapping
from libcst.codemod import CodemodContext
import libcst as cst
import libcst.matchers as match
from ast_tools.stack import SymbolTable
from ast_tools.passes import PASS_ARGS_T, Pass, apply_cst_passes
from ast_tools.cst_utils import to_module, InsertStatementsVisitor
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


class _ChannelRewriter(InsertStatementsVisitor):
    """
    Create channels:
        * for each send/receive in type, create a valid and data port
          * send/receive of the same type can share a channel
        * Find offer/choose with greatest number of labels, create valid and
          data port with number of bits needed to encode all labels
          * offer/choose with less labels can use same data port

    NOTE: eventually we can try to encode everything in one input and one
    output data port (using max number of bits needed)
    """
    def leave_Parameters(self, original_node, updated_node):
        new_params = []
        for param in updated_node.params:
            # TODO: Check annotation
            if param.name.value == "chan":
                new_params.append(
                    param.with_changes(
                        annotation=cst.Annotation(cst.parse_expression(
                            'm.Product.from_fields("anon",'
                            ' {"valid": m.Bit, "data": m.Bits[1]})'
                        ))
                    )
                )
            else:
                new_params.append(param)

        return updated_node.with_changes(params=new_params)

    def leave_Expr(self, original_node, updated_node):
        if isinstance(updated_node.value, cst.Call):
            call = updated_node.value
            if match.matches(
                call.func,
                match.Attribute(
                    match.DoNotCare(),
                    match.Name("receive")
                )
            ):
                # TODO: Assert we are checking a channel
                assert len(call.args) == 2, "assume receive(<ENUM>)"
                assert call.args[1].keyword.value == "wait_outputs"
                chan_name = call.func.value
                expected_value = call.args[0].value
                wait_outputs = call.args[1].value
                cond = cst.BinaryOperation(
                    cst.Attribute(chan_name, cst.Name("valid")),
                    cst.BitAnd(),
                    cst.Comparison(
                        cst.Attribute(chan_name, cst.Name("data")),
                        [cst.ComparisonTarget(cst.Equal(),
                                              expected_value)],
                        lpar=[cst.LeftParen()],
                        rpar=[cst.RightParen()]
                    ),
                    lpar=[cst.LeftParen()],
                    rpar=[cst.RightParen()]
                )
                self.insert_statements_before_current([cst.While(
                    cst.UnaryOperation(cst.BitInvert(), cond),
                    cst.IndentedBlock([
                        cst.SimpleStatementLine([
                            cst.Expr(cst.Yield(wait_outputs))])])
                )])
                return cst.FlattenSentinel([])
        return updated_node


class _RewriteChannels(Pass):
    def rewrite(self,
                tree: cst.CSTNode,
                env: SymbolTable,
                metadata: MutableMapping) -> PASS_ARGS_T:
        rewriter = _ChannelRewriter(CodemodContext())
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
        cls.__call__ = apply_cst_passes(
            passes=[_RewriteChannels()],
            debug=debug,
            env=env,
            path=path,
            file_name=file_name,
        )(cls.__call__)

        return m.coroutine(
            pre_passes=pre_passes,
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
