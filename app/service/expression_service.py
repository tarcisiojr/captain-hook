import distutils.util
import operator
import pyparsing as pp


def _get_value(value: dict, path):
    ret = value
    for att in path:
        ret = ret[att] if ret is not None and att in ret else None
    return ret


def _operator_operands(tokens):
    it = iter(tokens)
    while True:
        try:
            yield next(it), next(it)
        except StopIteration:
            break


def _parse_signop(results: pp.ParseResults):
    sign, value = results[0]
    mult = {"+": 1, "-": -1}[sign]
    return mult * value


def _parse_power(results: pp.ParseResults):
    value = results[0]
    res = value[-1]
    for val in value[-3::-2]:
        res = val ** res
    return res


def _do_arith_expr(op1, op, op2):
    _handlers = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
        "!=": lambda a, b: a != b,
        "==": lambda a, b: a == b,
        'or': lambda a, b: a or b,
        'and': lambda a, b: a and b,
    }

    return _handlers[op](op1, op2)


def _parse_arith_expr(results: pp.ParseResults):
    value = results[0]
    ret = value[0]
    for op, val in _operator_operands(value[1:]):
        ret = _do_arith_expr(ret, op, val)
    return ret


def _parse_and_or(results: pp.ParseResults):
    value = results[0]
    bool_ret = value[0]
    for op, val in _operator_operands(value[1:]):
        if (not bool_ret and op == 'and') or (bool_ret and op == 'or'):
            return bool_ret
        bool_ret = _do_arith_expr(bool_ret, op, val)
    return bool_ret


def evaluate(expression, variables):
    pp.ParserElement.enablePackrat()

    variable = pp.Word(pp.alphas, pp.alphanums + "_")
    dot_notation = pp.delimited_list(variable, delim='.')
    dot_notation_path = variable + pp.Suppress('.') + dot_notation | variable

    quoted_string = pp.QuotedString('"')
    integer = pp.Word(pp.nums)
    real = pp.Combine(pp.Word(pp.nums) + "." + pp.Word(pp.nums))
    bool_value = pp.CaselessLiteral('true') | pp.CaselessLiteral('false')
    and_or = pp.CaselessLiteral('and') | pp.CaselessLiteral('or')
    operand = and_or | bool_value | dot_notation_path | real | integer | quoted_string
    sign_op = pp.one_of("+ -")
    mult_op = pp.one_of("* /")
    plus_op = pp.one_of("+ -")
    exp_op = pp.Literal("**")

    bool_value.set_parse_action(lambda results: distutils.util.strtobool(results[0]) == 1)
    dot_notation_path.set_parse_action(lambda results: _get_value(variables, results))
    real.set_parse_action(lambda results: float(results[0]))
    integer.set_parse_action(lambda results: int(results[0]))
    comparison_op = pp.one_of("< <= > >= != ==")

    arith_expr = pp.infix_notation(
        operand,
        [
            (sign_op, 1, pp.OpAssoc.RIGHT, _parse_signop),
            (exp_op, 2, pp.OpAssoc.LEFT, _parse_power),
            (mult_op, 2, pp.OpAssoc.LEFT, _parse_arith_expr),
            (plus_op, 2, pp.OpAssoc.LEFT, _parse_arith_expr),
        ],
    )
    comp_expr = pp.infix_notation(
        arith_expr,
        [
            (comparison_op, 2, pp.OpAssoc.LEFT, _parse_arith_expr),
        ],
    )

    exp = pp.infix_notation(comp_expr, [(and_or, 2, pp.OpAssoc.LEFT, _parse_and_or)])
    ret = exp.parse_string(expression, parse_all=True)[0]
    return ret

# if __name__ == '__main__':
#     print(evaluate("event.ff == 30 and sellout.a >= 10", {
#         'sellout': {'a': 10, 'ff': 1},
#         'event': {'ff': 30, 'a': 100},
#     }))
