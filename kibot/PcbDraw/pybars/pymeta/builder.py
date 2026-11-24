# -*- test-case-name: pymeta.test.test_builder -*-
import linecache, sys
from types import ModuleType as module

import itertools, linecache, sys

class TreeBuilder(object):
    """
    Produce an abstract syntax tree of OMeta operations.
    """

    def __init__(self, name: str, grammar=None, *args):
        self.name = name


    def makeGrammar(self, rules):
        return ["Grammar", self.name, rules]

    def rule(self, name: str, expr):
        return ["Rule", name, expr]

    def apply(self, ruleName, codeName, *exprs):
        return ["Apply", ruleName, codeName, exprs]

    def exactly(self, expr):
        return ["Exactly", expr]

    def many(self, expr):
        return ["Many", expr]

    def many1(self, expr):
        return ["Many1", expr]

    def optional(self, expr):
        return ["Optional", expr]

    def _or(self, exprs):
        return ["Or", exprs]

    def _not(self, expr):
        return ["Not", expr]

    def lookahead(self, expr):
        return ["Lookahead", expr]

    def sequence(self, exprs):
        return ["And", exprs]

    def bind(self, expr, name: str):
        return ["Bind", name, expr]

    def pred(self, expr):
        return ["Predicate", expr]

    def action(self, expr):
        return ["Action", expr]

    def expr(self, expr):
        return ["Python", expr]

    def listpattern(self, exprs):
        return ["List", exprs]



class PythonWriter(object):
    """
    Converts an OMeta syntax tree into Python source.
    """
    def __init__(self, tree):
        self.tree = tree
        self.lines = []
        self.gensymCounter = 0


    def _generate(self, retrn=False):
        result = self._generateNode(self.tree)
        if retrn:
            self.lines.append("return (%s, self.currentError)" % (result,))
        elif result:
            self.lines.append(result)
        return self.lines


    def output(self):
        return '\n'.join(self._generate())


    def _generateNode(self, node):
        name = node[0]
        args =  node[1:]
        return getattr(self, "generate_"+name)(*args)


    def _gensym(self, name: str) -> str:
        """
        Produce a unique name for a variable in generated code.
        """
        self.gensymCounter += 1
        return "_G_%s_%s" % (name, self.gensymCounter)


    def _newThunkFor(self, name: str, expr):
        """
        Define a new function of no arguments.
        @param name: The name of the rule generating this thunk.
        @param expr: A list of lines of Python code.
        """
        
        subwriter = self.__class__(expr)
        flines  = subwriter._generate(retrn=True)
        fname = self._gensym(name)
        self._writeFunction(fname, (),  flines)
        return fname


    def _expr(self, typ, e):
        """
        Generate the code needed to execute the expression, and return the
        variable name bound to its value.
        """
        name = self._gensym(typ)
        self.lines.append("%s, lastError = %s" % (name, e))
        self.lines.append("self.considerError(lastError)")
        return name


    def _writeFunction(self, fname, arglist, flines):
        """
        Generate a function.
        @param head: The initial line defining the function.
        @param body: A list of lines for the function body.
        """

        self.lines.append("def %s(%s):" % (fname, ", ".join(arglist)))
        for line in flines:
            self.lines.append((" " * 4) + line)
        return fname


    def compilePythonExpr(self, expr):
        """
        Generate code for running embedded Python expressions.
        """
        
        return self._expr('python', 'eval(%r, self.globals, _locals), None' %(expr,))


    def generate_Apply(self, ruleName, codeName, rawArgs):
        """
        Create a call to self.apply(ruleName, *args).
        """
        args = [self._generateNode(x) for x in rawArgs]
        if ruleName == 'super':
            return self._expr('apply', 'self.superApply("%s", %s)' % (codeName,
                                                              ', '.join(args)))
        return self._expr('apply', 'self._apply(self.rule_%s, "%s", [%s])' % (ruleName,
                                                                              ruleName,
                                                             ', '.join(args)))

    def generate_Exactly(self, literal):
        """
        Create a call to self.exactly(expr).
        """
        return self._expr('exactly', 'self.exactly(%r)' % (literal,))


    def generate_Many(self, expr):
        """
        Create a call to self.many(lambda: expr).
        """
        fname = self._newThunkFor("many", expr)
        return self._expr('many', 'self.many(%s)' % (fname,))


    def generate_Many1(self, expr):
        """
        Create a call to self.many(lambda: expr).
        """
        fname = self._newThunkFor("many1", expr)
        return self._expr('many1', 'self.many(%s, %s())' % (fname, fname))


    def generate_Optional(self, expr):
        """
        Try to parse an expr and continue if it fails.
        """
        realf = self._newThunkFor("optional", expr)
        passf = self._gensym("optional")
        self._writeFunction(passf, (), ["return (None, self.input.nullError())"])
        return self._expr('or', 'self._or([%s])' % (', '.join([realf, passf])))


    def generate_Or(self, exprs):
        """
        Create a call to
        self._or([lambda: expr1, lambda: expr2, ... , lambda: exprN]).
        """
        if len(exprs) > 1:
            fnames = [self._newThunkFor("or", expr) for expr in exprs]
            return self._expr('or', 'self._or([%s])' % (', '.join(fnames)))
        else:
            return self._generateNode(exprs[0])


    def generate_Not(self, expr):
        """
        Create a call to self._not(lambda: expr).
        """
        fname = self._newThunkFor("not", expr)
        return self._expr("not", "self._not(%s)" % (fname,))


    def generate_Lookahead(self, expr):
        """
        Create a call to self.lookahead(lambda: expr).
        """
        fname = self._newThunkFor("lookahead", expr)
        return self._expr("lookahead", "self.lookahead(%s)" %(fname,))


    def generate_And(self, exprs):
        """
        Generate code for each statement in order.
        """
        v = None
        for ex in exprs:
            v = self._generateNode(ex)
        return v


    def generate_Bind(self, name: str, expr):
        """
        Bind the value of 'expr' to a name in the _locals dict.
        """
        v = self._generateNode(expr)
        ref = "_locals['%s']" % (name,)
        self.lines.append("%s = %s" %(ref, v))
        return ref


    def generate_Predicate(self, expr):
        """
        Generate a call to self.pred(lambda: expr).
        """

        fname = self._newThunkFor("pred", expr)
        return self._expr("pred", "self.pred(%s)" %(fname,))


    def generate_Action(self, expr):
        """
        Generate this embedded Python expression on its own line.
        """
        return self.compilePythonExpr(expr)


    def generate_Python(self, expr):
        """
        Generate this embedded Python expression on its own line.
        """
        return self.compilePythonExpr(expr)


    def generate_List(self, expr):
        """
        Generate a call to self.listpattern(lambda: expr).
        """
        fname = self._newThunkFor("listpattern", expr)
        return  self._expr("listpattern", "self.listpattern(%s)" %(fname,))


    def generate_Rule(self, name: str, expr):
        rulelines = ["_locals = {'self': self}",
                     "self.locals[%r] = _locals" % (name,)]
        subwriter = self.__class__(expr)
        flines  = subwriter._generate(retrn=True)
        rulelines.extend(flines)
        self._writeFunction("rule_" + name, ("self",), rulelines)


    def generate_Grammar(self, name: str, rules):
        self.lines.append("class %s(GrammarBase):" % (name,))
        for rule in rules:
            self._generateNode(rule)
            self.lines.extend(['', ''])
        self.lines[1:] = [line and (' ' * 4 + line) for line in self.lines[1:]]
        del self.lines[-2:]



def writePython(tree):
    pw = PythonWriter(tree)
    return pw.output()


class GeneratedCodeLoader(object):
    """
    Object for use as a module's __loader__, to display generated
    source.
    """
    def __init__(self, source):
        self.source = source
    def get_source(self, name: str):
        return self.source



def moduleFromGrammar(tree, className, superclass, globalsDict):
    source = writePython(tree)
    modname = "pymeta_grammar__" + className
    filename = "/pymeta_generated_code/" + modname + ".py"
    mod = module(modname)
    mod.__dict__.update(globalsDict)
    mod.__name__ = modname
    mod.__dict__[superclass.__name__] = superclass
    mod.__dict__["GrammarBase"] = superclass
    mod.__loader__ = GeneratedCodeLoader(source)
    code = compile(source, filename, "exec")
    eval(code, mod.__dict__)
    fullGlobals = dict(getattr(mod.__dict__[className], "globals", None) or {})
    fullGlobals.update(globalsDict)
    mod.__dict__[className].globals = fullGlobals
    sys.modules[modname] = mod
    linecache.getlines(filename, mod.__dict__)
    return mod.__dict__[className]
