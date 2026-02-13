# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

from docutils import nodes
from docutils.parsers.rst import Directive
import importlib
from sphinx import addnodes
from sphinx.domains import Domain, ObjType
from sphinx.directives import ObjectDescription
from sphinx.roles import XRefRole
from sphinx.util.nodes import make_refnode
from docutils.statemachine import ViewList
from sphinx.util.docstrings import prepare_docstring
from .target import TargetId

def doc_to_viewlist(obj):
    rst = ViewList()
    if obj.__doc__:
        for idx, l in enumerate(prepare_docstring(obj.__doc__)):
            rst.append(l, f'{obj}.__doc__', idx+1)
    return rst


def _register_flow_object(document, env, objtype, name, signode):
    """Register a flow object in the domain for cross-referencing."""
    targetname = f'flow.{objtype}.{name}'
    if targetname not in document.ids:
        signode['ids'].append(targetname)
        document.note_explicit_target(signode)
        flow_domain = env.get_domain('flow')
        flow_domain.data['objects'][(objtype, name)] = (env.docname, targetname)
    return targetname


class FlowDomain(Domain):
    """Domain for PyDesignFlow objects (blocks and tasks)."""

    name = 'flow'
    label = 'PyDesignFlow'

    object_types = {
        'block': ObjType('block', 'block'),
        'task': ObjType('task', 'task', 'target'),
        'target': ObjType('target', 'task', 'target'),  # alias for task
    }

    roles = {
        'block': XRefRole(),
        'task': XRefRole(),
        'target': XRefRole(),  # alias for task
    }

    initial_data = {
        'objects': {},  # (type, fullname) -> (docname, labelid)
    }

    def clear_doc(self, docname):
        """Remove traces of a document in the domain-specific inventories."""
        for (typ, name), (doc, _labelid) in list(self.data['objects'].items()):
            if doc == docname:
                del self.data['objects'][(typ, name)]

    def merge_domaindata(self, docnames, otherdata):
        """Merge in data from other domain."""
        for (typ, name), (docname, labelid) in otherdata['objects'].items():
            if docname in docnames:
                self.data['objects'][(typ, name)] = (docname, labelid)

    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        """Resolve cross-reference."""
        # Normalize type: 'target' is an alias for 'task'
        if typ == 'target':
            typ = 'task'

        # Try to find the object
        obj = self.data['objects'].get((typ, target))
        if obj is None:
            return None

        docname, labelid = obj
        return make_refnode(builder, fromdocname, docname, labelid, contnode, target)

    def resolve_any_xref(self, env, fromdocname, builder, target, node, contnode):
        """Resolve any cross-reference (when using :any: role)."""
        results = []

        # Try both block and task
        for typ in ['block', 'task']:
            obj = self.data['objects'].get((typ, target))
            if obj is not None:
                docname, labelid = obj
                results.append((
                    f'flow:{typ}',
                    make_refnode(builder, fromdocname, docname, labelid, contnode, target)
                ))

        return results

    def get_objects(self):
        """Return an iterable of "object descriptions".

        Yields tuples of (name, dispname, type, docname, anchor, priority).
        """
        for (typ, name), (docname, labelid) in self.data['objects'].items():
            yield (name, name, typ, docname, labelid, 1)


class FlowBlockDirective(ObjectDescription):
    """Directive for documenting a flow block."""

    def handle_signature(self, sig, signode):
        """Parse the signature and add nodes to signode."""
        # sig is the block_id
        block_id = sig.strip()

        signode += addnodes.desc_type('block', 'block')
        signode += nodes.Text(' ', ' ')
        signode += addnodes.desc_name(block_id, block_id)

        return block_id

    def add_target_and_index(self, name, sig, signode):
        """Add target and index entry."""
        _register_flow_object(self.state.document, self.env, 'block', name, signode)


class FlowTaskDirective(ObjectDescription):
    """Directive for documenting a flow task."""

    def handle_signature(self, sig, signode):
        """Parse the signature and add nodes to signode."""
        # sig should be in format "block_id.task_id"
        sig = sig.strip()

        if '.' not in sig:
            raise ValueError(f"Task signature must be in format 'block_id.task_id', got: {sig}")

        block_id, task_id = sig.rsplit('.', 1)

        signode += addnodes.desc_type('target', 'target')
        signode += nodes.Text(' ', ' ')
        signode += addnodes.desc_addname(block_id, block_id)
        signode += nodes.Text('.', '.')
        signode += addnodes.desc_name(task_id, task_id)

        return sig  # return full "block_id.task_id"

    def add_target_and_index(self, name, sig, signode):
        """Add target and index entry."""
        _register_flow_object(self.state.document, self.env, 'task', name, signode)


class DesignflowDirective(Directive):
    required_arguments = 1
    optional_arguments = 0
    has_content = False

    def _create_desc_node(self, objtype):
        """Create a description node for a flow object."""
        node = addnodes.desc()
        node.document = self.state.document
        node['domain'] = 'flow'
        node['objtype'] = node['desctype'] = objtype
        node['noindex'] = False
        node['classes'].append(objtype)
        return node

    def gendoc_task(self, flow, block_id, task_id):
        target = flow.target(TargetId(block_id, task_id))
        fullname = f"{block_id}.{task_id}"

        node = self._create_desc_node('task')
        signode = addnodes.desc_signature(task_id, '')
        node.append(signode)

        # Register in domain for cross-referencing
        env = self.state.document.settings.env
        _register_flow_object(self.state.document, env, 'task', fullname, signode)

        # Build signature
        if target.always_rebuild:
            signode.append(addnodes.desc_type("", "always_rebuild"))
            signode.append(nodes.Text(" ", " "))
        signode.append(addnodes.desc_type("target", "target"))
        signode.append(nodes.Text(" ", " "))
        signode += addnodes.desc_addname(block_id, block_id)
        signode += nodes.Text(".", ".")
        signode += addnodes.desc_name(task_id, task_id)


        contentnode = addnodes.desc_content()
        node.append(contentnode)

        if len(target.requires) > 0:
            fl = nodes.field_list()
            contentnode.append(fl)
            f = nodes.field()
            fl.append(f)
            fname = nodes.field_name()
            f.append(fname)
            fname.append(nodes.Text("Requires"))
            fbody = nodes.field_body()
            f.append(fbody)
            lst = nodes.bullet_list()
            fbody.append(lst)

            # Create clickable cross-references for dependencies
            for _, t in target.resolve_requires():
                item = nodes.list_item()
                para = nodes.paragraph()

                # Create a cross-reference to the dependency
                dep_name = f"{t.block_id}.{t.task_id}"
                xref = addnodes.pending_xref(
                    '',
                    refdomain='flow',
                    reftype='task',
                    reftarget=dep_name,
                    refwarn=True,
                )
                xref += nodes.literal(dep_name, dep_name)
                para += xref
                item.append(para)
                lst.append(item)

        rst = doc_to_viewlist(target)

        pnode = nodes.paragraph()
        contentnode.append(pnode)
        pnode.document = self.state.document
        self.state.nested_parse(rst, 0, pnode)

        return node

    def gendoc_block(self, flow, block_id):
        block = flow[block_id]

        node = self._create_desc_node('block')
        signode = addnodes.desc_signature(block_id, '')
        node.append(signode)

        # Register in domain for cross-referencing
        env = self.state.document.settings.env
        _register_flow_object(self.state.document, env, 'block', block_id, signode)

        # Build signature
        signode.append(addnodes.desc_type("block", "block"))
        signode.append(nodes.Text(" ", " "))
        signode += addnodes.desc_name(block_id, block_id)
        signode.append(nodes.Text(" ", " "))
        signode.append(addnodes.desc_annotation(f"(instance of {type(block).__name__})"))

        contentnode = addnodes.desc_content()
        node.append(contentnode)

        rst = doc_to_viewlist(block)

        pnode = nodes.paragraph()
        contentnode.append(pnode)
        pnode.document = self.state.document
        self.state.nested_parse(rst, 0, pnode)

        for task_id in flow[block_id].tasks:
            tasknode = self.gendoc_task(flow, block_id, task_id)
            contentnode.append(tasknode)

        return node

    def gendoc_flow(self, flow):
        return [self.gendoc_block(flow, block_id) for block_id in flow]

    def run(self):
        mod = importlib.import_module(self.arguments[0])
        flow = mod.flow
        return self.gendoc_flow(flow)


def setup(app):
    # Register the flow domain
    app.add_domain(FlowDomain)

    # Register domain directives explicitly
    app.add_directive_to_domain('flow', 'block', FlowBlockDirective)
    app.add_directive_to_domain('flow', 'task', FlowTaskDirective)
    app.add_directive_to_domain('flow', 'target', FlowTaskDirective)

    # Register the convenience directive for auto-documentation
    app.add_directive("designflow", DesignflowDirective)

    return {
        'version': '0.2',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
