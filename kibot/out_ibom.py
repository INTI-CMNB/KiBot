# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - name: Interactive HTML BoM
    role: mandatory
    github: INTI-CMNB/InteractiveHtmlBom
    command: generate_interactive_bom.py
    no_cmd_line_version_old: true
    plugin_dirs:
      - InteractiveHtmlBom
      - InteractiveHtmlBom/InteractiveHtmlBom
      - org_openscopeproject_InteractiveHtmlBom
      - org_openscopeproject_InteractiveHtmlBom/InteractiveHtmlBom
    version: 2.7.0
    downloader: pytool
    id: ibom
"""
import os
from subprocess import (check_output, STDOUT, CalledProcessError)
from shutil import which, rmtree
from .error import KiPlotConfigurationError
from .misc import BOM_ERROR, W_EXTNAME, W_NONETLIST, W_IBOMNOCHK
from .gs import GS
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()
WARNING_MIX = "Avoid using it in conjunction with IBoM native filtering options"


class IBoMOptions(VariantOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output, use '' to use the IBoM filename (%i=ibom, %x=html) """
            self.dark_mode = False
            """ Default to dark mode """
            self.hide_pads = False
            """ Hide footprint pads by default """
            self.show_fabrication = False
            """ Show fabrication layer by default """
            self.hide_silkscreen = False
            """ Hide silkscreen by default """
            self.highlight_pin1 = False
            """ [boolean|string=false] [none,all,selected] Highlight pin1 by default """
            self.no_redraw_on_drag = False
            """ Do not redraw pcb on drag by default """
            self.board_rotation = 0
            """ *Board rotation in degrees (-180 to 180). Will be rounded to multiple of 5 """
            self.offset_back_rotation = False
            """ Offset the back of the pcb by 180 degrees """
            self.checkboxes = 'Sourced,Placed'
            """ Comma separated list of checkbox columns """
            self.mark_when_checked = ''
            """ Name of the checkbox column used to mark components when checked.
                When enabled components checked in this column will be displayed in green.
                Leave empty to disable it.
                Needs iBoM newer than 2.10.0. """
            self.bom_view = 'left-right'
            """ *[bom-only,left-right,top-bottom] Default BOM view """
            self.layer_view = 'FB'
            """ *[F,FB,B] Default layer view """
            self.no_compression = False
            """ Disable compression of pcb data """
            self.name_format = 'ibom'
            """ Output file name format supports substitutions:
                %f : original pcb file name without extension.
                %p : pcb/project title from pcb metadata.
                %c : company from pcb metadata.
                %r : revision from pcb metadata.
                %d : pcb date from metadata if available, file modification date otherwise.
                %D : bom generation date.
                %T : bom generation time.
                Extension .html will be added automatically.
                Note that this name is used only when output is '' """
            self.include_tracks = False
            """ *Include track/zone information in output. F.Cu and B.Cu layers only """
            self.include_nets = False
            """ Include netlist information in output. """
            self.sort_order = 'C,R,L,D,U,Y,X,F,SW,A,~,HS,CNN,J,P,NT,MH'
            """ Default sort order for components. Must contain '~' once """
            self.netlist_file = None
            """ {extra_data_file} """
            self.extra_data_file = ''
            """ Path to netlist or xml file. You can use '%F.xml' to avoid specifying the project name.
                Leave it blank for most uses, data will be extracted from the PCB """
            self.extra_fields = ''
            """ *Comma separated list of extra fields to pull from netlist or xml file.
                Using 'X,Y' is a shortcut for `show_fields` and `group_fields` with values 'Value,Footprint,X,Y' """
            self.show_fields = ''
            """ *Comma separated list of fields to show in the BOM.
                Value and Footprint are displayed when nothing is specified """
            self.group_fields = ''
            """ Comma separated list of fields that components will be grouped by.
                Value and Footprint are used when nothing is specified """
            self.normalize_field_case = False
            """ *Normalize extra field name case. E.g. 'MPN' and 'mpn' will be considered the same field """
            self.blacklist = ''
            """ List of comma separated blacklisted components or prefixes with *. E.g. 'X1,MH*'.
                IBoM option, avoid using in conjunction with KiBot variants/filters """
            self.no_blacklist_virtual = False
            """ Do not blacklist virtual components.
                IBoM option, avoid using in conjunction with KiBot variants/filters """
            self.blacklist_empty_val = False
            """ Blacklist components with empty value.
                IBoM option, avoid using in conjunction with KiBot variants/filters """
            self.variant_field = ''
            """ Name of the extra field that stores board variant for component.
                IBoM option, avoid using in conjunction with KiBot variants/filters """
            self.variants_whitelist = ''
            """ List of board variants to include in the BOM.
                IBoM option, avoid using in conjunction with KiBot variants/filters """
            self.variants_blacklist = ''
            """ List of board variants to exclude from the BOM.
                IBoM option, avoid using in conjunction with KiBot variants/filters """
            self.dnp_field = ''
            """ Name of the extra field that indicates do not populate status.
                Components with this field not empty will be blacklisted.
                IBoM option, avoid using in conjunction with KiBot variants/filters """
            self.hide_excluded = False
            """ Hide components in the Fab layer that are marked as excluded by a variant.
                Affected by global options """
            self.forced_name = ''
            """ Name to be used for the PCB/project (no file extension).
                This will affect the name iBoM displays in the generated HTML """
        super().__init__()
        self.add_to_doc('variant', WARNING_MIX)
        self.add_to_doc('dnf_filter', WARNING_MIX)
        self._expand_id = 'ibom'
        self._expand_ext = 'html'

    def need_extra_fields(self):
        return (self.extra_fields or
                self.variants_whitelist or
                self.variants_blacklist or
                self.variant_field or
                self.dnp_field or
                self.variant)

    def config(self, parent):
        super().config(parent)
        self._extra_data_file_guess = False
        if not self.extra_data_file and self.need_extra_fields():
            self.extra_data_file = '%F.xml'
            self._extra_data_file_guess = True
        if self.extra_data_file:
            self.extra_data_file = self.expand_filename('', self.extra_data_file, 'ibom', 'xml')
        if isinstance(self.highlight_pin1, bool):
            self.highlight_pin1 = 'all' if self.highlight_pin1 else 'none'
        checkboxes = self.checkboxes.split(',')
        if not checkboxes:
            logger.warning(W_IBOMNOCHK+"No checkbox columns provided for iBoM")
        elif self.mark_when_checked and self.mark_when_checked not in checkboxes:
            raise KiPlotConfigurationError(f"The `mark_when_checked` ({self.mark_when_checked}) isn't in "
                                           f"`checkboxes` ({checkboxes})")

    def get_targets(self, out_dir):
        if self.output:
            return [self.expand_filename(out_dir, self.output, 'ibom', 'html')]
        logger.warning(W_EXTNAME+'{} uses a name generated by the external tool.'.format(self._parent))
        logger.warning(W_EXTNAME+'Please use a name generated by KiBot or specify the name explicitly.')
        return []

    def get_dependencies(self):
        files = [GS.pcb_file]
        if self.extra_data_file and os.path.isfile(self.extra_data_file):
            files.append(self.extra_data_file)
        return files

    def run(self, name):
        super().run(name)
        tool, version = self.ensure_tool_get_ver('ibom')
        logger.debug('Doing Interactive BoM')
        # Tell ibom we don't want to use the screen
        os.environ['INTERACTIVE_HTML_BOM_NO_DISPLAY'] = ''
        # Solve the output name
        output = None
        if self.output:
            output = name
            self.name_format = 'ibom'
            output_dir = os.path.dirname(name)
            cur = os.path.join(output_dir, 'ibom.html')
        else:
            output_dir = name
        # Solve the variants stuff
        ori_extra_data_file = self.extra_data_file
        net_dir = None
        pcb_name = GS.pcb_file
        if self.will_filter_pcb_components():
            # Write a custom netlist to a temporal dir
            prj_name = os.path.basename(self.expand_filename('', self.forced_name, 'ibom', '')) if self.forced_name \
                       else GS.pcb_basename
            net_dir = GS.mkdtemp('ibom')
            netlist = os.path.join(net_dir, prj_name+'.xml')
            self.extra_data_file = netlist
            logger.debug('Creating variant netlist `{}`'.format(netlist))
            with open(netlist, 'wb') as f:
                GS.sch.save_netlist(f, self._comps)
            # Write a board with the filtered values applied
            self.filter_pcb_components()
            pcb_name, _ = self.save_tmp_dir_board('ibom', force_dir=net_dir, forced_name=prj_name)
            self.unfilter_pcb_components()
        else:
            # Check if the user wants extra_fields but there is no data about them (#68)
            if self.need_extra_fields() and not os.path.isfile(self.extra_data_file):
                logger.warning(W_NONETLIST+'iBoM needs information about user defined fields and no netlist provided')
                if self._extra_data_file_guess:
                    logger.warning(W_NONETLIST+'Create a BoM in XML format or use the `update_xml` preflight')
                    # If the name of the netlist is just a guess remove it from the options
                    self.extra_data_file = ''
                else:
                    logger.warning(W_NONETLIST+"The file name used in `extra_data_file` doesn't exist")
        cmd = [tool, pcb_name, '--dest-dir', output_dir, '--no-browser', ]
        if not which(tool) and not os.access(tool, os.X_OK):
            # Plugin could be installed without execute flags
            cmd.insert(0, 'python3')
        # Apply variants/filters
        to_remove = ','.join(self.get_not_fitted_refs(parent=True))
        if self.blacklist and to_remove:
            self.blacklist += ','
        self.blacklist += to_remove
        # Convert attributes into options
        # Note: here we should use self, instead of a template, but this is currently safer
        template = IBoMOptions()
        for k, v in template.get_attrs_gen():
            v = getattr(self, k)
            if not v or k in ['output', 'variant', 'dnf_filter', 'exclude_filter', 'pre_transform', 'hide_excluded',
                              'forced_name']:
                continue
            if k == 'offset_back_rotation' and version < (2, 5, 0, 2):
                continue
            cmd.append(BaseOutput.attr2longopt(k))  # noqa: F821
            if not isinstance(v, bool):  # must be str/(int, float)
                cmd.append(str(v))
        # Run the command
        logger.debug('Running: '+str(cmd))
        try:
            cmd_output = check_output(cmd, stderr=STDOUT)
            cmd_output_dec = cmd_output.decode()
            # IBoM returns 0 for this error!!!
            if 'ERROR Parsing failed' in cmd_output_dec:
                raise CalledProcessError(1, cmd, cmd_output)
        except CalledProcessError as e:
            GS.exit_with_error(f'Failed to create BoM, error {e.returncode}', BOM_ERROR, e,
                               [("'PCB_SHAPE' object has no attribute 'GetAngle'",
                                "Update Interactive HTML BoM your version doesn't support KiCad 6 files")])
        finally:
            if net_dir:
                logger.debug('Removing temporal variant dir `{}`'.format(net_dir))
                rmtree(net_dir)
            # Restore the real name selected
            self.extra_data_file = ori_extra_data_file
        logger.debug('Output from command:\n'+cmd_output_dec+'\n')
        if output:
            logger.debug('Renaming output file: {} -> {}'.format(cur, output))
            os.replace(cur, output)


@output_class
class IBoM(BaseOutput):  # noqa: F821
    """ IBoM (Interactive HTML BoM)
        Generates an interactive web page useful to identify the position of the components in the PCB.
        For more information: https://github.com/INTI-CMNB/InteractiveHtmlBom
        This output is what you get from the InteractiveHtmlBom plug-in (pcbnew). """
    def __init__(self):
        super().__init__()
        with document:
            self.options = IBoMOptions
            """ *[dict={}] Options for the `ibom` output """
        self._category = ['Schematic/BoM', 'PCB/fabrication/assembly']

    def get_dependencies(self):
        return self.options.get_dependencies()

    @staticmethod
    def get_conf_examples(name, layers):
        tool = GS.check_tool(name, 'ibom')
        if tool is None:
            return None
        return BaseOutput.simple_conf_examples(name, 'Interactive HTML BoM', 'Assembly')  # noqa: F821

    def get_navigate_targets(self, out_dir):
        return (self.options.get_targets(out_dir), ['ibom'])
