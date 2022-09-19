import timeit

from lark import Lark, Transformer, v_args

grammar = """
    ?start: sum

    ?sum: product
        | sum "+" product   -> add
        | sum "-" product   -> sub

    ?product: atom
        | product "*" atom  -> mul
        | product "/" atom  -> div
        
    path: NAME "." NAME     -> getvalue
        | path "." NAME     -> dotnot
    
    ?atom: NUMBER           -> number
         | "-" atom         -> neg
         | NAME             -> var
         | "(" sum ")"
         | path

    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS_INLINE

    %ignore WS_INLINE
"""


@v_args(inline=True)
class CalculateTree(Transformer):
    from operator import add, sub, mul, truediv as div, neg
    number = float

    def __init__(self):
        super().__init__()
        self.vars = {'a': {'b': {'c': 200}}}

    def getvalue(self, prop_var, prop_att):
        ret = self.vars.get(prop_var)
        if prop_att in ret:
            return ret[prop_att]
        return None

    def dotnot(self, value, prop_att):
        if prop_att in value:
            return value[prop_att]
        return value

    def var(self, name):
        try:
            return self.vars[name]
        except KeyError:
            raise Exception("Variable not found: %s" % name)


parser = Lark(grammar, parser="lalr", transformer=CalculateTree())

if __name__ == '__main__':
    start_time = timeit.default_timer()
    print(parser.parse('a.b.c'))
    print(timeit.default_timer() - start_time)

