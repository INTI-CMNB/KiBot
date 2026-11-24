# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from collections import OrderedDict
from copy import copy
from .error import KiPlotConfigurationError
from .gs import GS
from .misc import pretty_list
from .optionable import Optionable
from . import log

logger = log.get_logger()


def fname(file) -> str:
    if file:
        return ", while importing from `{}`".format(file)
    return ""


class GroupEntry(object):
    def __init__(self, item, from_out=False, out=None):
        self.item = item              # The name (group or output)
        self.from_out = from_out      # Defined in the "groups" option of an output
        self.from_top = not from_out  # Defined in the global "groups"
        self.out = out                # Optional pointer to the output object

    def update_out(self):
        """ Update the pointer to the output object """
        self.out = RegOutput.get_output(self.item)

    def is_from_output(self):
        return self.from_out

    def is_from_top(self):
        return self.from_top

    def __repr__(self) -> str:
        origin = ''
        if self.from_out and self.from_top:
            origin = ' (from both)'
        elif self.from_out:
            origin = ' (from output)'
        elif self.from_top:
            origin = ' (from groups)'
        return f"{self.out if self.out else self.item}{origin}"

    # def __str__(self):
    #     return str(self.out) if self.out else self.item

    def short_str(self):
        return self.out.short_str() if self.out else self.item


class Group(object):
    def __init__(self, name: str, items):
        self.name = name
        if len(items) == 0 or isinstance(items[0], GroupEntry):
            self.items = items
        else:
            self.items = [GroupEntry(i) for i in items]

    def add_from_output(self, out):
        i = next((i for i in self.items if i.item == out.name), None)
        if i is not None:
            i.from_out = True
            return
        self.items.append(GroupEntry(out.name, from_out=True, out=out))

    def remove_from_output(self, out):
        i = next((i for i in self.items if i.item == out.name), None)
        if i is None or not i.is_from_output():
            return None
        i.from_out = False
        return i

    def get_list(self):
        """ Get the name of the items """
        return [i.item for i in self.items]

    def update_out(self):
        """ Update the output pointer for all items """
        for i in self.items:
            i.update_out()

    def __repr__(self) -> str:
        return f"{self.name} -> {list(self.items)}"

    def __str__(self) -> str:
        return f"{self.name} -> {pretty_list(self.items, True)}"


class Registrable(object):
    """ This class adds the mechanism to register plug-ins """
    def __init__(self):
        super().__init__()

    @classmethod
    def register(cl, name: str, aclass):
        cl._registered[name] = aclass

    @classmethod
    def is_registered(cl, name: str) -> bool:
        return name in cl._registered

    @classmethod
    def get_class_for(cl, name: str):
        return cl._registered[name]

    @classmethod
    def get_registered(cl):
        return cl._registered

    def __str__(self) -> str:
        return "'{}' ({}) [{}]".format(self.comment, self.name, self.type)

    def short_str(self) -> str:
        return "{} [{}]".format(self.name, self.type)


class RegOutput(Optionable, Registrable):
    """ An optionable that is also registrable.
        Used by BaseOutput.
        Here because it doesn't need macros. """
    _registered = {}
    # Defined filters
    _def_filters = {}
    # Defined variants
    _def_variants = {}
    # Defined groups
    _def_groups = {}
    # List of defined outputs
    _def_outputs = OrderedDict()

    def __init__(self):
        super().__init__()

    @staticmethod
    def reset():
        # Defined filters
        RegOutput._def_filters = {}
        # Defined variants
        RegOutput._def_variants = {}
        # Defined groups
        RegOutput._def_groups = {}
        # List of defined outputs
        RegOutput._def_outputs = OrderedDict()

    @staticmethod
    def add_output(obj, file=None):
        if obj.name in RegOutput._def_outputs:
            raise KiPlotConfigurationError("Output name `{}` already defined".format(obj.name)+fname(file))
        if obj.name in RegOutput._def_groups:
            raise KiPlotConfigurationError("Output name `{}` already defined as group".format(obj.name)+fname(file))
        RegOutput._def_outputs[obj.name] = obj

    @staticmethod
    def add_outputs(objs, file=None):
        for o in objs:
            RegOutput.add_output(o, file)

    @staticmethod
    def remove_output(obj):
        del RegOutput._def_outputs[obj.name]

    @staticmethod
    def get_outputs():
        return RegOutput._def_outputs.values()

    @staticmethod
    def get_output(name: str):
        return RegOutput._def_outputs.get(name, None)

    @staticmethod
    def is_output_or_group(name: str) -> bool:
        return name in RegOutput._def_outputs or name in RegOutput._def_groups

    @staticmethod
    def reset_done():
        for o in RegOutput._def_outputs.values():
            o._done = False

    # ###################################
    #  Variants operations
    # ###################################

    @staticmethod
    def add_variants(variants):
        RegOutput._def_variants.update(variants)

    @staticmethod
    def add_variant(variant):
        RegOutput._def_variants[variant.name] = variant

    @staticmethod
    def remove_variant(variant):
        del RegOutput._def_variants[variant.name]

    @staticmethod
    def separate_variant_and_subpcb(name: str):
        """ Separate VARIANT[SUBPCB] into VARIANT, SUBPCB """
        subpcb = None
        if '[' in name:
            try:
                name, subpcb = name.split('[')
                if subpcb.endswith(']'):
                    subpcb = subpcb[:-1]
            except ValueError:
                pass
        return name, subpcb

    @staticmethod
    def is_variant(name: str):
        name, subpcb = RegOutput.separate_variant_and_subpcb(name)
        variant = RegOutput._def_variants.get(name)
        if variant is None:
            return False
        if subpcb is None:
            return True
        return any((sp.name == subpcb for sp in variant.sub_pcbs))

    @staticmethod
    def get_variant(name: str):
        name, subpcb = RegOutput.separate_variant_and_subpcb(name)
        variant = RegOutput._def_variants[name]
        if variant and subpcb:
            # Return a copy customized for the desired sub-pcb
            variant = copy(variant)
            variant._sub_pcb = sp = next((sp for sp in variant.sub_pcbs if sp.name == subpcb))
            if sp.file_id:
                variant.file_id = sp.file_id
            else:
                variant.file_id += '_'+sp.name
        return variant

    @staticmethod
    def get_variants():
        return RegOutput._def_variants

    @staticmethod
    def check_variant(variant):
        if variant:
            if isinstance(variant, RegVariant):
                return variant
            if not RegOutput.is_variant(variant):
                raise KiPlotConfigurationError("Unknown variant name `{}`".format(variant))
            return RegOutput.get_variant(variant)
        return None

    # ###################################
    #  Groups operations
    # ###################################

    @staticmethod
    def add_group(name: str, lst, file=None):
        if name in RegOutput._def_groups:
            raise KiPlotConfigurationError("Group name `{}` already defined".format(name)+fname(file))
        if name in RegOutput._def_outputs:
            raise KiPlotConfigurationError("Group name `{}` already defined as output".format(name)+fname(file))
        new_grp = Group(name, lst)
        RegOutput._def_groups[name] = new_grp
        return new_grp

    @staticmethod
    def add_groups(objs, file=None):
        logger.debug(f'Adding groups: {objs}')
        for n, lst in objs.items():
            RegOutput.add_group(n, lst, file)

    @staticmethod
    def replace_group(old_name: str, name: str, lst):
        new_group = Group(name, lst)
        RegOutput._def_groups[name] = new_group
        return new_group

    @staticmethod
    def add_out_to_group(out, group):
        """ Add `out` to the `group` assuming this is from the `groups` option of the output """
        grp = RegOutput._def_groups.get(group)
        if grp is not None:
            grp.add_from_output(out)
            return True, grp
        grp = RegOutput.add_group(group, [GroupEntry(out.name, from_out=True)])
        return False, grp

    @staticmethod
    def remove_out_from_group(out, group):
        """ Remove `out` from the `group` assuming this is from the `groups` option of the output """
        grp = RegOutput._def_groups.get(group)
        if grp is None:
            # Wrong group?
            return
        i = grp.remove_from_output(out)
        if i is None:
            # Not found or not from output
            return False
        if i.is_from_top():
            # Also defined at top level
            return False
        del grp.items[grp.items.index(i)]
        return True

    @staticmethod
    def get_groups():
        return {g.name: g.get_list() for g in RegOutput._def_groups.values()}

    @staticmethod
    def get_groups_struct():
        return RegOutput._def_groups

    @staticmethod
    def get_group_names():
        return RegOutput._def_groups.keys()

    @staticmethod
    def solve_groups(targets, where, level=0):
        """ Replaces any group by its members.
            Returns a new list.
            Assumes the outputs and groups are valid. """
        new_targets = []
        # Avoid infinite loops
        level += 1
        if level > 20:
            raise KiPlotConfigurationError("More than 20 levels of nested groups, possible loop")
        for t in targets:
            if t in RegOutput._def_outputs:
                new_targets.append(t)
            else:
                new_grp = RegOutput._def_groups.get(t, None)
                if new_grp is None:
                    raise KiPlotConfigurationError('Unknown output/group `{}` (in `{}`)'.format(t, where))
                # Recursive expand
                new_targets.extend(RegOutput.solve_groups(new_grp.get_list(), t, level))
        return new_targets

    # ###################################
    #  Filters operations
    # ###################################

    @staticmethod
    def add_filters(filters):
        RegOutput._def_filters.update(filters)

    @staticmethod
    def remove_filter(obj):
        del RegOutput._def_filters[obj.name]

    @staticmethod
    def is_filter(name: str) -> bool:
        return name in RegOutput._def_filters

    @staticmethod
    def get_filter(name: str):
        return RegOutput._def_filters[name]

    @staticmethod
    def add_filter(obj):
        RegOutput._def_filters[obj.name] = obj

    @staticmethod
    def get_filters():
        return RegOutput._def_filters


class RegVariant(Optionable, Registrable):
    """ An optionable that is also registrable.
        Used by BaseVariant.
        Here because it doesn't need macros. """
    _registered = {}

    def __init__(self):
        super().__init__()


class RegFilter(Optionable, Registrable):
    """ An optionable that is also registrable.
        Used by BaseFilter.
        Here because it doesn't need macros. """
    _registered = {}

    def __init__(self):
        super().__init__()


class RegDependency(Registrable):
    """ Used to register output tools dependencies """
    _registered = {}

    def __init__(self):
        super().__init__()

    @classmethod
    def register(cl, aclass):
        name = aclass.name
        if name in cl._registered:
            # Already registered, add the roles
            old_reg = cl._registered[name]
            old_reg.role.append(aclass.role)
        else:
            cp = copy(aclass)
            cp.role = [aclass.role]
            cl._registered[name] = cp


def solve_variant(variant):
    if isinstance(variant, str):
        return RegOutput.check_variant(variant)
    return variant


GS.solve_variant = solve_variant
