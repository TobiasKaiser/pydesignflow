from docutils import nodes
from docutils.parsers.rst import Directive, directives
import importlib
from sphinx import addnodes
from docutils.statemachine import ViewList
from sphinx.util.docstrings import prepare_docstring
from .target import TargetId

def doc_to_viewlist(obj):
    rst = ViewList()
    if obj.__doc__:
        for idx, l in enumerate(prepare_docstring(obj.__doc__)):
            rst.append(l, f'{obj}.__doc__', idx+1)
    return rst

class DesignflowDirective(Directive):
    required_arguments = 1
    optional_arguments = 0
    has_content = False

    def gendoc_task(self, flow, block_id, task_id):
        target = flow.target(TargetId(block_id, task_id))

        domain = ''
        objtype = 'object'

        node = addnodes.desc()
        node.document = self.state.document
        node['domain'] = domain
        # 'desctype' is a backwards compatible attribute
        node['objtype'] = node['desctype'] = objtype
        node['noindex'] = noindex = True
        node['classes'].append(node['objtype'])

        sig = task_id

        signode = addnodes.desc_signature(sig, '')
        node.append(signode)
        if target.always_rebuild:
            signode.append(addnodes.desc_type("", "always_rebuild"))
            signode.append(nodes.Text(" ", " "))
        signode.append(addnodes.desc_type("target", "target"))
        signode.append(nodes.Text(" ", " "))
        signode += addnodes.desc_addname(block_id, block_id)
        signode += nodes.Text(".", ".")
        signode += addnodes.desc_name(sig, sig)

        
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
            #contentnode.append(nodes.Text("Dependencies:"))
            fbody = nodes.field_body()
            f.append(fbody)
            lst = nodes.bullet_list()
            fbody.append(lst)
            for _, t in target.resolve_requires():
                item = nodes.list_item()
                item.append(nodes.Text(f"{t.block_id}.{t.task_id}"))
                lst.append(item)

        rst = doc_to_viewlist(target)

        pnode = nodes.paragraph()
        contentnode.append(pnode)
        pnode.document = self.state.document
        self.state.nested_parse(rst, 0, pnode)

        return node

    def gendoc_block(self, flow, block_id):
        block = flow[block_id]

        domain = ''
        objtype = 'object'

        node = addnodes.desc()
        node.document = self.state.document
        node['domain'] = domain
        # 'desctype' is a backwards compatible attribute
        node['objtype'] = node['desctype'] = objtype
        node['noindex'] = noindex = True
        node['classes'].append(node['objtype'])

        sig = block_id

        signode = addnodes.desc_signature(sig, '')
        node.append(signode)
        signode.append(addnodes.desc_type("block", "block"))
        signode.append(nodes.Text(" ", " "))
        signode += addnodes.desc_name(sig, sig)
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


    def run_old(self):
        mod = importlib.import_module(self.arguments[0])
        flow = mod.flow
        #paragraph_node = nodes.paragraph(text='Hello World!')
        #return [paragraph_node]
        lst_blocks = nodes.bullet_list()

        for block_id in flow:
            block_item = nodes.list_item()
            block_item += nodes.inline(text=str(block_id))
            
            lst_tasks = nodes.bullet_list()

            for task_id in flow[block_id].tasks:
                task_item = nodes.list_item()
                task_item += nodes.inline(text=str(task_id))    

                lst_tasks += task_item

            block_item += lst_tasks

            lst_blocks += block_item


        return [lst_blocks]


def setup(app):
    app.add_directive("designflow", DesignflowDirective)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }