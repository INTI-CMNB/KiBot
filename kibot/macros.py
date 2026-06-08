# -*- coding: utf-8 -*-
# Copyright (c) 2020-2025 Salvador E. Tropea
# Copyright (c) 2020-2025 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Macros to make the output plug-ins cleaner.
"""
import numbers
from .gs import GS  # noqa: F401
from ast import (Assign, Name, Attribute, Expr, Load, Store, UnaryOp, USub,
                 ClassDef, Call, ImportFrom, copy_location, alias, Constant)
from .mcpyrate import unparse


def is_num(value):
    return isinstance(value, Constant) and isinstance(value.value, numbers.Number)


def is_str(value):
    return isinstance(value, Constant) and isinstance(value.value, str)


def document(sentences, **kw):
    """ This macro takes literal strings and converts them into:
        _help_ID = type_hint+STRING
        where:
        ID is the first target of the last assignment.
        type_hint is the assigned type and default value (only works for a few types)
        STRING is the literal string """
    for n in range(len(sentences)):
        s = sentences[n]
        if not n:
            prev = s
            continue
        # The whole sentence is a string?
        if (isinstance(s, Expr) and is_str(s.value) and
           # and the previous is an assign
           isinstance(prev, Assign)):  # noqa: E128
            # Apply it to the first target
            target = prev.targets[0]
            value = prev.value
            # Extract its name
            # variables and attributes are supported
            if isinstance(target, Name):
                # Note: The support for variables isn't currently used
                name = target.id
                is_attr = False
            elif isinstance(target, Attribute):
                name = target.attr
                is_attr = True
            # Remove starting underscore
            if name[0] == '_':
                name = name[1:]
            # Create a _help_ID
            doc_id = '_help_'+name
            # Create the type hint for numbers, strings and booleans
            type_hint = ''
            post_hint = ''
            if isinstance(value, Constant) and isinstance(value.value, bool):
                # Bool checked first because they are a subclass of number
                type_hint = '[boolean={}]'.format(str(value.value).lower())
            elif is_num(value):
                type_hint = '[number={}]'.format(value.value)
            elif isinstance(value, UnaryOp) and is_num(value.operand) and isinstance(value.op, USub):
                # -Num
                type_hint = '[number={}]'.format(-value.operand.value)
            elif is_str(value):
                type_hint = "[string='{}']".format(value.value)
            elif isinstance(value, Attribute):
                # Used for the default options. I.e. GS.def_global_option
                val = eval(unparse(value))
                if isinstance(val, bool):
                    # Not used yet
                    type_hint = '[boolean={}]'.format(str(val).lower())
                elif isinstance(val, (int, float)):
                    # Not used yet
                    type_hint = '[number={}]'.format(val)
                elif isinstance(val, str):
                    type_hint = "[string='{}']".format(val)
                post_hint += '. Affected by global options'
            # Transform the string into an assign for _help_ID
            if is_attr:
                target = Attribute(value=Name(id='self', ctx=Load()), attr=doc_id, ctx=Store())
            else:
                target = Name(id=doc_id, ctx=Store())
            # Reuse the s.value Str
            help_str = s.value
            doc_str = s.value.value.rstrip()
            doc_str_2 = ' '+doc_str[2:] if doc_str.startswith(' *') else doc_str
            if type_hint and (doc_str_2.startswith(' [string') or doc_str_2.startswith(' [number') or
                              doc_str_2.startswith(' [boolean')):
                # Hardcoded type hint, don't add one
                type_hint = ''
            # The * marks this option as a basic (not advanced) option
            if doc_str.startswith(' *') and type_hint:
                # Move the marker to the beginning
                doc_str = doc_str_2
                type_hint = '*'+type_hint
            help_str.value = type_hint+doc_str+post_hint
            sentences[n] = Assign(targets=[target], value=help_str)
            # Copy the line number from the original docstring
            copy_location(target, s)
            copy_location(sentences[n], s)
        prev = s
    # Return the modified AST
    return sentences


def _do_wrap_class_register(tree, mod, base_class):
    if isinstance(tree, ClassDef):
        # Create the register call
        name = tree.name
        reg_name = name.lower()
        # BaseOutput.register member:
        attr = Attribute(value=Name(id=base_class, ctx=Load()), attr='register', ctx=Load())
        # Function call to it passing reg_name and name
        do_register = Expr(value=Call(func=attr, args=[Constant(value=reg_name), Name(id=name, ctx=Load())], keywords=[]))
        # Create the import
        do_import = ImportFrom(module=mod, names=[alias(name=base_class, asname=None, lineno=tree.lineno,
                               col_offset=tree.col_offset)], level=1)
        return [do_import, tree, do_register]
    # Just in case somebody applies it to anything other than a class
    return tree


def output_class(tree, **kw):
    """A decorator to wrap a class with:

       from .out_base import BaseOutput
       ... Class definition
       BaseOutput.register(CLASS_NAME_LOWER_STRING, CLASS_NAME)

       Allowing to register the class as an output. """
    return _do_wrap_class_register(tree, 'out_base', 'BaseOutput')


def variant_class(tree, **kw):
    """A decorator to wrap a class with:

       from .var_base import BaseVariant
       ... Class definition
       BaseVariant.register(CLASS_NAME_LOWER_STRING, CLASS_NAME)

       Allowing to register the class as a variant. """
    return _do_wrap_class_register(tree, 'var_base', 'BaseVariant')


def filter_class(tree, **kw):
    """A decorator to wrap a class with:

       from .fil_base import BaseFilter
       ... Class definition
       BaseFilter.register(CLASS_NAME_LOWER_STRING, CLASS_NAME)

       Allowing to register the class as a variant. """
    return _do_wrap_class_register(tree, 'fil_base', 'BaseFilter')


def pre_class(tree, **kw):
    """A decorator to wrap a class with:

       from .pre_base import BasePreFlight
       ... Class definition
       BasePreFlight.register(CLASS_NAME_LOWER_STRING, CLASS_NAME)

       Allowing to register the class as an output. """
    return _do_wrap_class_register(tree, 'pre_base', 'BasePreFlight')
