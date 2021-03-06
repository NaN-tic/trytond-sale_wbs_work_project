# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Bool, Eval
from trytond.transaction import Transaction

__all__ = ['Sale', 'SaleLine']


class Sale:
    __name__ = 'sale.sale'
    __metaclass__ = PoolMeta

    @classmethod
    def __setup__(cls):
        super(Sale, cls).__setup__()
        cls.lines.context.update({
            'project': Eval('work_project'),
            })
        cls._buttons['update_structure'] = {
            'invisible': (Eval('state') != 'draft') | (
                ~Bool(Eval('work_project'))),
            'icon': 'tryton-refresh',
            }

    def get_wbs_tree(self, name):
        if not self.work_project:
            return super(Sale, self).get_wbs_tree(name)
        return [x.id for x in self.work_project.wbs_tree]

    @classmethod
    def quote(cls, sales):
        cls.update_structure(sales)
        super(Sale, cls).quote(sales)

    @classmethod
    @ModelView.button
    def update_structure(cls, sales):
        for sale in sales:
            sale.create_lines_from_wbs(sale.wbs_tree, sale.lines_tree)

    def create_lines_from_wbs(self, wbs_tree, lines_tree, parent_line=None):
        lines_by_description = {
            (x.description, x.product.id if x.product else None):
                x for x in lines_tree
            }
        for wbs in wbs_tree:
            sale_line = lines_by_description.get(
                (wbs.description, wbs.product.id if wbs.product else None)
                )
            if not sale_line:
                sale_line = wbs.get_sale_line(parent_line)
                sale_line.sale = self.id
                sale_line.save()
            elif not sale_line.wbs:
                sale_line.wbs = wbs
                sale_line.save()
            if wbs.childs:
                self.create_lines_from_wbs(wbs.childs, sale_line.childs,
                    parent_line=sale_line)

            if sale_line.sale.work_project and not wbs.project:
                wbs.project = sale_line.sale.work_project
                wbs.save()

    @classmethod
    def write(cls, *args):
        pool = Pool()
        WBS = pool.get('work.breakdown.structure')
        actions = iter(args)
        to_write = []
        for sales, values in zip(actions, actions):
            if 'work_project' in values:
                wbs = [l.wbs for sale in sales for l in sale.lines if l.wbs]
                to_write.extend((wbs, {'project': values.get('work_project')}))
        super(Sale, cls).write(*args)
        if to_write:
            with Transaction().set_context(_check_access=False):
                WBS.write(*to_write)


class SaleLine:
    __name__ = 'sale.line'
    __metaclass__ = PoolMeta

    project = fields.Function(fields.Many2One('work.project', 'Project'),
        'on_change_with_project')

    @classmethod
    def __setup__(cls):
        super(SaleLine, cls).__setup__()
        if not cls.wbs.domain:
            cls.wbs.domain = []
        cls.wbs.domain.append(('project', '=', Eval('project')))
        if not cls.wbs.depends:
            cls.wbs.depends = []
        cls.wbs.depends.append('project')

    @staticmethod
    def default_project():
        return Transaction().context.get('project')

    @fields.depends('_parent_sale.work_project')
    def on_change_with_project(self, name=None):
        if self.sale and self.sale.work_project:
            return self.sale.work_project.id

    def get_work_breakdown_structure(self, parent):
        wbs = super(SaleLine, self).get_work_breakdown_structure(parent)
        if self.project:
            wbs.project = self.project
        return wbs
