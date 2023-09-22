# -*- coding: utf-8 -*-
# Copyright (c) 2023 Salvador E. Tropea
# Copyright (c) 2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Based on:
# - background_job.py: Blender example
#   https://developer.blender.org/diffusion/B/browse/master/release/scripts/templates_py/background_job.py
# - blender_pcb2gltf.py: PCB3D to various formats
#   https://github.com/Haschtl/pcb2blender/blob/master/CI/blender_pcb2gltf.py
#
# Should be invoked using:
# blender -b --factory-startup -P blender_export.py -- OPTIONS
import argparse  # to parse options for us and print a nice help message
import json
import math
import os
import sys       # to get command line args
# Blender modules
import addon_utils
import bpy

X_AXIS = 0
Y_AXIS = 1
Z_AXIS = 2
VALID_FORMATS = {'fbx': 'Filmbox, proprietary format developed by Kaydara (owned by Autodesk)',
                 'obj': 'geometry definition format developed by Wavefront Technologies. Currently open',
                 'x3d': 'VRML successor. A royalty-free ISO/IEC standard for declaratively representing 3D graphics.',
                 'blender': 'Blender native format',
                 'gltf': 'standard file format for three-dimensional scenes and models.',
                 'stl': '3D printing from stereolithography CAD software created by 3D SystemsSTL (only mesh)',
                 'ply': 'Polygon File Format or the Stanford Triangle Format (only mesh)',
                 'render': 'do render'}


def fbx_export(name):
    bpy.ops.export_scene.fbx(filepath=name)


def obj_export(name):
    bpy.ops.export_scene.obj(filepath=name)


def x3d_export(name):
    bpy.ops.export_scene.x3d(filepath=name)


def stl_export(name):
    bpy.ops.export_mesh.stl(filepath=name)


def ply_export(name):
    bpy.ops.export_mesh.ply(filepath=name)


def blender_export(name):
    bpy.ops.wm.save_as_mainfile(filepath=name)


def gltf_export(name):
    bpy.ops.export_scene.gltf(filepath=name, export_copyright="KiBot", export_draco_mesh_compression_enable=True,
                              export_draco_mesh_compression_level=6, export_colors=False, export_yup=True)


def render_export(render_path):
    print('- Render')
    render = bpy.context.scene.render
    render.use_file_extension = True
    render.filepath = render_path
    bpy.ops.render.render(write_still=True)


def rot(axis, deg):
    bpy.context.active_object.rotation_euler[axis] = math.radians(deg)


def do_rotate(scene, name, id):
    rotate = scene.get(name)
    if rotate:
        rot(id, rotate)


def do_point_of_view(scene, name):
    view = scene.get(name)
    if view is None or view == 'z':
        return
    if view == 'Z':
        rot(Y_AXIS, 180)
        return
    if view == 'y':
        rot(X_AXIS, -90)
        return
    if view == 'Y':
        rot(X_AXIS, 90)
        rot(Z_AXIS, 180)
        return
    if view == 'x':
        rot(Y_AXIS, 90)
        rot(Z_AXIS, 90)
        return
    if view == 'X':
        rot(Y_AXIS, -90)
        rot(Z_AXIS, -90)
        return


def srgb_to_linearrgb(c):
    """ Apply the gamma correction """
    if c < 0:
        return 0
    elif c < 0.04045:
        return c/12.92
    else:
        return ((c+0.055)/1.055)**2.4


def hex_to_rgba(hex_value):
    hex_color = hex_value[1:]
    r = int(hex_color[:2], base=16)
    sr = r/255.0
    lr = srgb_to_linearrgb(sr)
    g = int(hex_color[2:4], base=16)
    sg = g/255.0
    lg = srgb_to_linearrgb(sg)
    b = int(hex_color[4:6], base=16)
    sb = b/255.0
    lb = srgb_to_linearrgb(sb)
    return (lr, lg, lb, 1.0)


def create_background_gradient(color1, color0):
    """ This creates a background gradient relative to the camera.
        I'm not a Blender guru and I took the idea from:
        https://www.youtube.com/watch?v=9NdZ8leYDcM (in Urdu/Hindi!)
        If you know a simpler mechanism please let me know """
    world_name = "World"
    # Create a "World"
    scn = bpy.context.scene
    scn.world = bpy.data.worlds.new(world_name)
    # Enable the use of nodes
    scn.world.use_nodes = True
    # Get the default nodes
    nt = scn.world.node_tree
    nodes = nt.nodes
    # Create a texture coordinate
    tc = nodes.new(type="ShaderNodeTexCoord")
    tc.location = (-580, 435)
    # Create a mapping
    mp = nodes.new(type="ShaderNodeMapping")
    mp.location = (-400, 400)
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(90))
    mp.inputs["Location"].default_value = (0.7, 0, 0)
    nt.links.new(tc.outputs["Camera"], mp.inputs["Vector"])
    # Create a gradient texture
    gt = nodes.new(type="ShaderNodeTexGradient")
    gt.location = (-180, 280)
    gt.gradient_type = "EASING"
    nt.links.new(mp.outputs["Vector"], gt.inputs["Vector"])
    # Create a color ramp
    cr = nodes.new(type="ShaderNodeValToRGB")
    cr.location = (10, 325)
    cr.color_ramp.interpolation = "EASE"
    cr.color_ramp.elements[0].color = hex_to_rgba(color0)
    cr.color_ramp.elements[1].color = hex_to_rgba(color1)
    nt.links.new(gt.outputs["Color"], cr.inputs["Fac"])
    # Move the Background
    bk1 = nodes["Background"]
    bk1.location = (355, 100)
    nt.links.new(cr.outputs["Color"], bk1.inputs["Color"])
    # Create another background
    bk2 = nodes.new(type="ShaderNodeBackground")
    bk2.location = (355, 240)
    nt.links.new(cr.outputs["Color"], bk2.inputs["Color"])
    # Create a light path
    lp = nodes.new(type="ShaderNodeLightPath")
    lp.location = (355, 580)
    # Create a mix shader
    mx = nodes.new(type="ShaderNodeMixShader")
    mx.location = (560, 220)
    nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs["Fac"])
    nt.links.new(bk2.outputs["Background"], mx.inputs[1])
    nt.links.new(bk1.outputs["Background"], mx.inputs[2])
    # Move the World Output
    wo = nodes["World Output"]
    wo.location = (760, 245)
    wo_is = wo.inputs["Surface"]
    nt.links.remove(wo_is.links[0])
    nt.links.new(mx.outputs["Shader"], wo_is)


jscene = None
auto_camera = False
cam_ob = None


def apply_scene(file, n_view=0):
    # Loads scene
    if not file:
        return 1
    global jscene
    if jscene is None:
        with open(file, 'rt') as f:
            text = f.read()
            print(text)
            jscene = json.loads(text)
    scene = bpy.context.scene

    # Select the board
    print('- Select all')
    bpy.ops.object.select_all(action='SELECT')
    # Make sure we start rotations from 0
    bpy.context.active_object.rotation_euler = (0, 0, 0)
    povs = jscene.get('point_of_view')
    if povs:
        pov = povs[n_view]
        # Apply point of view
        do_point_of_view(pov, 'view')
        # Apply extra rotations
        do_rotate(pov, 'rotate_x', 0)
        do_rotate(pov, 'rotate_y', 1)
        do_rotate(pov, 'rotate_z', 2)

    # Add a camera
    global auto_camera
    if not n_view:
        # First time: create the camera
        camera = jscene.get('camera')
        if not camera:
            auto_camera = True
            name = 'kibot_camera'
            pos = (0.0, 0.0, 10.0)
            type = 'PERSP'
        else:
            name = camera.get('name', 'unknown')
            pos = camera.get('position', None)
            type = camera.get('type', 'PERSP')
            if pos is None:
                auto_camera = True
                pos = (0, 0, 0)
            else:
                auto_camera = False
        print(f"- Creating camera {name} at {pos}")
        cam_data = bpy.data.cameras.new(name)
        global cam_ob
        cam_ob = bpy.data.objects.new(name=name, object_data=cam_data)
        scene.collection.objects.link(cam_ob)  # instance the camera object in the scene
        scene.camera = cam_ob       # set the active camera
        cam_ob.location = pos
        cam_ob.data.type = type
    if auto_camera:
        print('- Changing camera to focus the board')
        bpy.ops.view3d.camera_to_view_selected()
        cam_ob.location = (cam_ob.location[0], cam_ob.location[1], cam_ob.location[2]*1.1)

    # Add lights
    if not n_view:
        # First time: create the lights
        lights = jscene.get('lights')
        if lights:
            for light in lights:
                name = light.get('name', 'unknown')
                pos = light.get('position', (0.0, 0.0, 0.0))
                typ = light.get('type', 'SUN')
                energy = light.get('energy', 0.0)
                print(f"- Creating light {name} at {pos}, type: {typ} energy: {energy}")
                light_data = bpy.data.lights.new(name, typ)
                print(f"- Default energy: {light_data.energy}")
                if energy:
                    light_data.energy = energy
                light_ob = bpy.data.objects.new(name=name, object_data=light_data)
                scene.collection.objects.link(light_ob)
                light_ob.location = pos

    bpy.context.view_layer.update()

    # Setup render options
    render = jscene.get('render')
    if render and not n_view:
        scene.cycles.samples = render.get('samples', 10)
        r = scene.render
        r.engine = 'CYCLES'
        r.resolution_x = render.get('resolution_x', 1920)
        r.resolution_y = render.get('resolution_y', 1080)
        r.resolution_percentage = 100
        r.use_border = False
        if render.get('transparent_background'):
            r.film_transparent = True
            r.image_settings.color_mode = 'RGBA'
        else:
            create_background_gradient(render.get('background1', '#66667F'), render.get('background2', '#CCCCE5'))
    return len(povs)


EXPORTERS = {'fbx': fbx_export,
             'obj': obj_export,
             'x3d': x3d_export,
             'stl': stl_export,
             'ply': ply_export,
             'blender': blender_export,
             'gltf': gltf_export,
             'render': render_export}


def main():
    # get the args passed to blender after "--", all of which are ignored by
    # blender so scripts may receive their own arguments
    argv = sys.argv
    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--")+1:]  # get all args after "--"

    description = ("Blender script to export PCB3D files into various formats.\n"
                   "The pcb2blender_importer plug-in must be installed.\n"
                   "Consult: https://github.com/30350n/pcb2blender")
    prog = "blender -b --factory-startup -P blender_export.py --"
    epilog = "Valid formats:\n"
    for f, desc in VALID_FORMATS.items():
        epilog += f"{f}: {desc}\n"

    parser = argparse.ArgumentParser(description=description, prog=prog, epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-c", "--no_components", action="store_false", help="if the PCB components are discarded")
    parser.add_argument("-C", "--dont_cut_boards", action="store_false", help="do not separate sub-PCBs")
    parser.add_argument("-d", "--texture_dpi", type=float, help="textures density [508-2032] [1016]", default=1016.0)
    parser.add_argument("-D", "--dont_center", action="store_false", help="do not center the PCB at 0,0")
    parser.add_argument("-E", "--dont_enhance_materials", action="store_false", help="do not enhance materials")
    parser.add_argument("-f", "--format", type=str, required=True, nargs='+', choices=VALID_FORMATS.keys(),
                        help="output formats to export, can be repeated")
    parser.add_argument("-m", "--pcb_material", type=str, choices=["RASTERIZED", "3D"], default="RASTERIZED",
                        help="Rasterized (Cycles) or 3D (deprecated) [RASTERIZED]")
    parser.add_argument("-M", "--dont_merge_materials", action="store_false", help="do not merge materials")
    parser.add_argument("-o", "--output", type=str, required=True, nargs='+', help="output file name, can be repeated")
    parser.add_argument("-r", "--scene", type=str, help="JSON file containing camera, light and render options")
    parser.add_argument("-s", "--solder_joints", type=str, choices=["NONE", "SMART", "ALL"], default="SMART",
                        help="Add none, all or only for THT/SMD with solder paste [SMART]")
    parser.add_argument("-S", "--dont_stack_boards", action="store_false", help="do not stack sub-PCBs")

    parser.add_argument('PCB3D_file')
    args = parser.parse_args(argv)

    nformats = len(args.format)
    if nformats != len(args.output):
        print("Please use -f and -o the same amount of times")
        sys.exit(2)

    print("Importing PCB3D file ...")
    PCB3D_file = os.path.abspath(args.PCB3D_file)
    # Start with fresh settings
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Now enable the plug-in
    addon_utils.enable("pcb2blender_importer")
    # Import the PCB3D file
    bpy.ops.pcb2blender.import_pcb3d(filepath=PCB3D_file, pcb_material=args.pcb_material,
                                     import_components=args.no_components,
                                     add_solder_joints=args.solder_joints,
                                     center_boards=args.dont_center,
                                     merge_materials=args.dont_merge_materials,
                                     enhance_materials=args.dont_enhance_materials,
                                     cut_boards=args.dont_cut_boards,
                                     stack_boards=args.dont_stack_boards,
                                     texture_dpi=args.texture_dpi)
    # Apply the scene first scene
    c_views = apply_scene(args.scene)
    c_formats = len(args.format)
    if c_formats % c_views:
        print("The number of outputs must be a multiple of the views (views: {} outputs: {})".format(c_views, c_formats))
        sys.exit(2)
    per_pass = int(c_formats/c_views)
    for n in range(c_views):
        if n:
            # Apply scene N
            apply_scene(args.scene, n)
        # Get the current slice
        formats = args.format[n*per_pass:(n+1)*per_pass]
        outputs = args.output[n*per_pass:(n+1)*per_pass]
        # Do all the exports
        for f, o in zip(formats, outputs):
            print(f"Exporting {o} in {f} format")
            EXPORTERS[f](os.path.abspath(o))

    print("batch job finished, exiting")


if __name__ == "__main__":
    main()
