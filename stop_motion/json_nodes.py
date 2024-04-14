# Copyright 2022 Bassam Kurdali / urchn.org
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import json
import os

# TODO Save Metadata (type information, read only)
# TODO Allow Saving multiple items in a single file
# TODO Include Item type (e.g. GeometryNodeTree) in save so we can make code generic
# TODO If None in a value, don't save (no point in setting it and we don't know type)
# TODO Recursive

# Fallback Functions

def is_socket(item):
    """Socket Test"""
    return issubclass(type(item), bpy.types.NodeSocket)

def get_socket_index(socket):
    """Socket Fallback: return index as name is not unique"""
    node = socket.node
    for io_type in ("inputs", "outputs"):
        for index, other_socket in enumerate(getattr(node, io_type)):
            if socket == other_socket:
                return index


class Node_Tree():
    """ Utilities for Converting Node Groups Back and Forth to Simnple Data """

    exclusion = [
        "dimensions", "height", "internal_links", "inputs",
        "outputs", "rna_type"]

    fall_backs = {is_socket: get_socket_index}

    def __init__(self, name, tree_data=None):
        """ name is a node group's name, tree data is it's serial form """
        self.tree_data = tree_data
        self.name = name
        self.node_group = bpy.data.node_groups.get(name)
        if self.node_group:
            self.serialize()

    def sanitize(self, datum, prin=""):
        """ Try to return something JSONable """
        if type(datum) in (int, str, float, bool):
            return datum
        try:
            iter(datum)
        except TypeError:
            for test, func in self.fall_backs.items():
                if test(datum):
                    return func(datum)
            if 'name' in dir(datum):
                return datum.name
            return datum
        return [self.sanitize(item) for item in datum]

    def include(self, data, prop):
        """ whether or not to include a prop in serialization """
        
        if any(prop.startswith(pre) for pre in ("bl_", "_", "is_", "rna_")):
            return False
        if prop in self.exclusion:
            return False
        value = getattr(data, prop)
        if callable(value):
            return False
        if value is None:
            return False

        return True

    def serialize_element(self, element, additions=[]):
        """ Turn an element of a group into it's serialized representation """
        props = (prop for prop in dir(element) if self.include(element, prop))
        items = {
            prop: self.sanitize(getattr(element, prop))
            for prop in props
            }
        for addition in additions:
            items[addition] = self.sanitize(getattr(element, addition))
        return items
                
    def serialize_node(self, node): 
        """  Serialize a Node """
        io_props = {
            "inputs": [
                'description', 'enabled', 'link_limit', 
                'name', 'node', 'show_expanded', 'type', 'default_value'
                ],
            "outputs": ['description', 'enabled', 'name',]
            }

        items = self.serialize_element(node, ["bl_idname",])
        
        for io, props in io_props.items():
            items[io] = [{
                    prop: self.sanitize(getattr(element, prop))
                    for prop in props if prop in dir(element)}
                for element in getattr(node, io)] 
        return items
    
    def serialize_link(self, link):
        """ Serialize a Link """
        items = self.serialize_element(link)
        return items

    def serialize_group_io(self, io, additions=[]):
        return self.serialize_element(io, ["bl_socket_idname",])

    def serialize(self):
        """Serialize a Node Tree """
        self.tree_data = {
            "nodes": {
                node.name: self.serialize_node(node)
                for node in self.node_group.nodes
                },
            "links": [
                self.serialize_link(link) for link in self.node_group.links
                ],
            "inputs": [
                self.serialize_group_io(input)
                for input in self.node_group.interface.items_tree
                if input.item_type == 'SOCKET' and input.in_out == "INPUT"
                ],
            "outputs": [
                self.serialize_group_io(output)
                for output in self.node_group.interface.items_tree
                if output.item_type == 'SOCKET' and output.in_out == "OUTPUT"
                ]
            }

    def set_element(self, element, items):
        """ Setting Properties for a new element in a node group """
        for prop, data in items:
            try:
                setattr(element, prop, data)
            except Exception as e:
                print(f"Warning: {e}: ", prop)        

    def create(self, tree_type="GeometryNodeTree"):
        """ Create a New Node Tree """

        if self.node_group:
            return self.node_group
        
        self.node_group = bpy.data.node_groups.new(
            self.name, tree_type)
        node_tree = self.node_group

        # Create Group inputs and outputs
        for ios in ('inputs', 'outputs'):
            in_out = ios[:-1].upper()
            for element in self.tree_data[ios]:
                new_io = node_tree.interface.new_socket(
                    element["name"], description="", in_out=in_out,
                    socket_type=element["bl_socket_idname"])
                self.set_element(new_io, element.items())   

        # Create Nodes
        node_list = [item for item in self.tree_data["nodes"].items()]
        node_list.sort(
            key=lambda item: item[-1].get("type") == 'FRAME',
            reverse=True
            )

        for node, node_data in node_list:
            new_node = node_tree.nodes.new(type=node_data["bl_idname"])
            new_node.name = node

            self.set_element(
                new_node,
                (item for item in node_data.items() if item[0] not in (
                    'parent', 'inputs', 'outputs'))
                )
            parent_name = node_data.get('parent')
            if parent_name:
                parent = node_tree.nodes[parent_name]
                new_node.parent = parent
                # Fixup locations post parenting
                new_node.location = node_data['location']
                parent.location = self.tree_data['nodes'][parent_name]['location']
            for ios in ('inputs', 'outputs'):
                for i, element in enumerate(node_data[ios]):
                    self.set_element(getattr(new_node,ios)[i], element.items())     

        for link in self.tree_data['links']:
            input = node_tree.nodes[link['from_node']].outputs[link['from_socket']]
            output = node_tree.nodes[link['to_node']].inputs[link['to_socket']]
            node_tree.links.new(input, output)

        return node_tree
        

def write_node(group_name, path):
    """ Write Serialized Node Group to JSON format file """
    group_data = Node_Tree(group_name).tree_data
    with open(path, 'w') as json_file:
        json_file.write(json.dumps(group_data))
        
        
def read_node(group_name, path, tree_type="GeometryNodeTree"):
    """ Return Serialized Node Group from JSON format """
    return Node_Tree(
        group_name,
        tree_data=json.loads(open(path).read())
        ).create(tree_type=tree_type)

if __name__ == "__main__":
    # Run this in resources/meshkey_devel.blend after tweaking MeshKey nodes
    filepath = os.path.abspath(os.path.join(
        os.path.split(bpy.context.blend_data.filepath)[0],
        "../stop_motion/modifier.json"
        ))
    write_node("MeshKey", filepath)

    filepath = filepath.replace("modifier.json", "realizer.json")
    write_node("Realize", filepath)

    filepath = filepath.replace("realizer.json", "materializer.json")
    write_node("Materialize", filepath)

    filepath = filepath.replace("materializer.json", "material.json")
    write_node("Oniony", filepath)
