"""
Class to read KiPlot config files
"""

import os
from sys import (exit, maxsize, exc_info)
from traceback import print_tb
from collections import OrderedDict

from .error import (KiPlotConfigurationError)
from .gs import GS
from .kiplot import (Layer, load_board)
from .misc import (NO_YAML_MODULE, EXIT_BAD_CONFIG, EXIT_BAD_ARGS, EXAMPLE_CFG, WONT_OVERWRITE)
from .optionable import Optionable
from .out_base import BaseOutput
from .pre_base import BasePreFlight
# Logger
from . import log

logger = log.get_logger(__name__)

try:
    import yaml
except ImportError:  # pragma: no cover
    log.init(False, False)
    logger.error('No yaml module for Python, install python3-yaml')
    exit(NO_YAML_MODULE)


def config_error(msg):
    if GS.debug_enabled:
        logger.error('Trace stack:')
        (type, value, traceback) = exc_info()
        print_tb(traceback)
    logger.error(msg)
    exit(EXIT_BAD_CONFIG)


class CfgYamlReader(object):
    def __init__(self):
        super(CfgYamlReader, self).__init__()

    def _check_version(self, v):
        if not isinstance(v, dict):
            config_error("Incorrect `kiplot` section")
        if 'version' not in v:
            config_error("YAML config needs `kiplot.version`.")
        version = v['version']
        # Only version 1 is known
        if version != 1:
            config_error("Unknown KiPlot config version: "+str(version))
        return version

    def _parse_layers(self, layers_to_parse):
        # Check we have a list of layers
        if not isinstance(layers_to_parse, list):
            raise KiPlotConfigurationError("`layers` must be a list")
        # Parse the elements
        layers = []
        for l in layers_to_parse:
            # Extract the attributes
            layer = None
            description = 'no desc'
            suffix = ''
            for k, v in l.items():
                if k == 'layer':
                    layer = str(v)
                elif k == 'description':
                    description = str(v)
                elif k == 'suffix':
                    suffix = str(v)
                else:
                    raise KiPlotConfigurationError("Unknown `{}` attribute for `layer`".format(k))
            # Check we got the layer name
            if layer is None:
                raise KiPlotConfigurationError("Missing `layer` attribute for layer entry ({})".format(l))
            # Create an object for it
            layers.append(Layer(layer, suffix, description))
        return layers

    def _parse_output(self, o_obj):
        # Default values
        name = None
        desc = None
        otype = None
        options = None
        outdir = '.'
        layers = []
        # Parse all of them
        for k, v in o_obj.items():
            if k == 'name':
                name = v
            elif k == 'comment':
                desc = v
            elif k == 'type':
                otype = v
            elif k == 'options':
                options = v
            elif k == 'dir':
                outdir = v
            elif k == 'layers':
                layers = v
            else:
                config_error("Unknown key `{}` in `{}` ({})".format(k, name, otype))
        # Validate them
        if not name:
            config_error("Output needs a name in: "+str(o_obj))
        if not otype:
            config_error("Output `"+name+"` needs a type")
        name_type = "`"+name+"` ("+otype+")"

        # Is a valid type?
        if not BaseOutput.is_registered(otype):
            config_error("Unknown output type: `{}`".format(otype))
        # Load it
        logger.debug("Parsing output options for "+name_type)
        o_out = BaseOutput.get_class_for(otype)(name, otype, desc)
        # Apply the options
        try:
            # If we have layers parse them
            if layers:
                layers = self._parse_layers(layers)
            o_out.config(outdir, options, layers)
        except KiPlotConfigurationError as e:
            config_error("In section '"+name+"' ("+otype+"): "+str(e))

        return o_out

    def _parse_filters(self, filters):
        if not isinstance(filters, list):
            config_error("'filters' must be a list")
        parsed = None
        for filter in filters:
            if 'filter' in filter:
                comment = filter['filter']
                if 'number' in filter:
                    number = filter['number']
                    if number is None:
                        config_error("empty 'number' in 'filter' definition ("+str(filter)+")")
                else:
                    config_error("missing 'number' for 'filter' definition ("+str(filter)+")")
                if 'regex' in filter:
                    regex = filter['regex']
                    if regex is None:
                        config_error("empty 'regex' in 'filter' definition ("+str(filter)+")")
                else:
                    config_error("missing 'regex' for 'filter' definition ("+str(filter)+")")
                logger.debug("Adding DRC/ERC filter '{}','{}','{}'".format(comment, number, regex))
                if parsed is None:
                    parsed = ''
                if comment:
                    parsed += '# '+comment+'\n'
                parsed += '{},{}\n'.format(number, regex)
            else:
                config_error("'filters' section of 'preflight' must contain 'filter' definitions (not "+str(filter)+")")
        return parsed

    def _parse_preflight(self, pf):
        logger.debug("Parsing preflight options: {}".format(pf))
        if not isinstance(pf, dict):
            config_error("Incorrect `preflight` section")

        for k, v in pf.items():
            if not BasePreFlight.is_registered(k):
                config_error("Unknown preflight: `{}`".format(k))
            try:
                logger.debug("Parsing preflight "+k)
                if k == 'filters':
                    v = self._parse_filters(v)
                o_pre = BasePreFlight.get_class_for(k)(k, v)
            except KiPlotConfigurationError as e:
                config_error("In preflight '"+k+"': "+str(e))
            BasePreFlight.add_preflight(o_pre)

    def read(self, fstream):
        """
        Read a file object into a config object

        :param fstream: file stream of a config YAML file
        """
        try:
            data = yaml.safe_load(fstream)
        except yaml.YAMLError as e:
            config_error("Error loading YAML "+str(e))
        # List of outputs
        outputs = []
        version = None
        # Analize each section
        for k, v in data.items():
            # logger.debug('{} {}'.format(k, v))
            if k == 'kiplot':
                version = self._check_version(v)
            elif k == 'preflight':
                self._parse_preflight(v)
            elif k == 'outputs':
                if isinstance(v, list):
                    for o in v:
                        outputs.append(self._parse_output(o))
                else:
                    config_error("`outputs` must be a list")
            else:
                config_error('Unknown section `{}` in config.'.format(k))
        if version is None:
            config_error("YAML config needs `kiplot.version`.")
        return outputs


def trim(docstring):
    """ PEP 257 recommended trim for __doc__ """
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return trimmed


def print_output_options(name, cl, indent):
    ind_str = indent*' '
    if issubclass(cl, BaseOutput):
        obj = cl('', name, '')
    else:
        obj = cl(name, '')
    print(ind_str+'* Options:')
    num_opts = 0
    for k, v in Optionable.get_attrs_gen(obj):
        help = getattr(obj, '_help_'+k)
        if help is None:
            help = 'Undocumented'
        lines = help.split('\n')
        preface = ind_str+'  - `{}`: '.format(k)
        clines = len(lines)
        print('{}{}{}'.format(preface, lines[0].strip(), '.' if clines == 1 else ''))
        ind_help = len(preface)*' '
        for ln in range(1, clines):
            print('{}{}'.format(ind_help+lines[ln].strip(), '.' if ln+1 == clines else ''))
        num_opts = num_opts+1
        if isinstance(v, type):
            print_output_options('', v, indent+4)
    if num_opts == 0:
        print(ind_str+'  - No available options')


def print_one_out_help(details, n, o):
    lines = trim(o.__doc__)
    if len(lines) == 0:
        lines = ['Undocumented', 'No description']
    if details:
        print('* '+lines[0])
        print('  * Type: `{}`'.format(n))
        print('  * Description: '+lines[1])
        for ln in range(2, len(lines)):
            print('                 '+lines[ln])
        print_output_options(n, o, 2)
    else:
        print('* {} [{}]'.format(lines[0], n))


def print_outputs_help(details=False):
    outs = BaseOutput.get_registered()
    logger.debug('{} supported outputs'.format(len(outs)))
    print('Supported outputs:')
    for n, o in OrderedDict(sorted(outs.items())).items():
        if details:
            print()
        print_one_out_help(details, n, o)


def print_output_help(name):
    if not BaseOutput.is_registered(name):
        logger.error('Unknown output type `{}`, try --help-list-outputs'.format(name))
        exit(EXIT_BAD_ARGS)
    print_one_out_help(True, name, BaseOutput.get_class_for(name))


def print_preflights_help():
    pres = BasePreFlight.get_registered()
    logger.debug('{} supported preflights'.format(len(pres)))
    print('Supported preflight options:\n')
    for n, o in pres.items():
        help = o.__doc__
        if help is None:
            help = 'Undocumented'
        print('- {}: {}.'.format(n, help.rstrip()))


def print_example_options(f, cls, name, indent, po):
    ind_str = indent*' '
    if issubclass(cls, BaseOutput):
        obj = cls('', name, '')
    else:
        obj = cls(name, '')
    if po:
        obj.read_vals_from_po(po)
    for k, v in Optionable.get_attrs_gen(obj):
        help = getattr(obj, '_help_'+k)
        if help:
            help_lines = help.split('\n')
            for hl in help_lines:
                f.write(ind_str+'# '+hl.strip()+'\n')
        val = getattr(obj, k)
        if isinstance(val, str):
            val = "'{}'".format(val)
        elif isinstance(val, bool):
            val = str(val).lower()
        if isinstance(val, type):
            f.write(ind_str+'{}:\n'.format(k))
            print_example_options(f, val, '', indent+2, None)
        else:
            f.write(ind_str+'{}: {}\n'.format(k, val))
    return obj


def create_example(pcb_file, out_dir, copy_options):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    fname = os.path.join(out_dir, EXAMPLE_CFG)
    if os.path.isfile(fname):
        logger.error(fname+" already exists, won't overwrite")
        exit(WONT_OVERWRITE)
    with open(fname, 'w') as f:
        logger.info('Creating {} example configuration'.format(fname))
        f.write('kiplot:\n  version: 1\n')
        # Preflights
        f.write('\npreflight:\n')
        pres = BasePreFlight.get_registered()
        for n, o in OrderedDict(sorted(pres.items())).items():
            if o.__doc__:
                f.write('  #'+o.__doc__.rstrip()+'\n')
            f.write('  {}: {}\n'.format(n, o.get_example()))
        # Outputs
        outs = BaseOutput.get_registered()
        f.write('\noutputs:\n')
        # List of layers
        po = None
        if pcb_file:
            # We have a PCB to take as reference
            board = load_board(pcb_file)
            if copy_options:
                # Layers and plot options from the PCB
                layers = Layer.get_plot_layers()
                po = board.GetPlotOptions()
            else:
                layers = Layer.get_pcb_layers()
        else:
            # Use the default list of layers
            layers = Layer.get_default_layers()
        for n, cls in OrderedDict(sorted(outs.items())).items():
            lines = trim(cls.__doc__)
            if len(lines) == 0:
                lines = ['Undocumented', 'No description']
            f.write('  # '+lines[0].rstrip()+':\n')
            for ln in range(2, len(lines)):
                f.write('  # '+lines[ln].rstrip()+'\n')
            f.write("  - name: '{}_example'\n".format(n))
            f.write("    comment: '{}'\n".format(lines[1]))
            f.write("    type: '{}'\n".format(n))
            f.write("    dir: 'Example/{}_dir'\n".format(n))
            f.write("    options:\n")
            obj = print_example_options(f, cls, n, 6, po)
            if '_layers' in obj.__dict__:
                f.write('    layers:\n')
                for layer in layers:
                    f.write("      - layer: '{}'\n".format(layer.name))
                    f.write("        suffix: '{}'\n".format(layer.suffix))
                    if layer.desc:
                        f.write("        description: '{}'\n".format(layer.desc))
            f.write('\n')
