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

"""
Experimental UI for overriding materials in Stop Motion branch.

Don't assume anything, that way we can deal with old files without any versioning
UNLESS UI becomes cumbersome

Two possible states:
1- no override: material comes from object in the frames collection
2- override: use a geometry nodes addon to set material

In the case of 1 we just need to update the material slot data on frame change in edit mode/other non object modes,
then the user can do their thing.

In the case of 2 we need to add (if it doesn't exist a materializer addon) (initialize override)


UI:
 Material popover

 - display active material slot of linked object
 - edit frame / assign frame

 - override
"""


