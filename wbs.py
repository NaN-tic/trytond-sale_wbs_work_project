# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal

from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

__all__ = ['WorkBreakdownStructure', 'Project']


class WorkBreakdownStructure:
    __name__ = 'work.breakdown.structure'
    __metaclass__ = PoolMeta

    project = fields.Many2One('work.project', 'Project', ondelete='CASCADE')

    @classmethod
    def __setup__(cls):
        super(WorkBreakdownStructure, cls).__setup__()
        if not cls.parent.domain:
            cls.parent.domain = []
        cls.parent.domain.append(('project', '=', Eval('project')))
        cls.parent.depends.append('project')
        cls.childs.domain.append(('project', '=', Eval('project')))
        cls.childs.depends.append('project')
        cls.sale_lines.domain.append(('sale.project', '=', Eval('project')))
        cls.sale_lines.depends.append('project')

    @classmethod
    def get_1st_level_chapters(cls, records):
        records_wo_project = [r for r in records if not r.project]
        if records_wo_project:
            for children in super(WorkBreakdownStructure,
                    cls).get_1st_level_chapters(records_wo_project):
                yield children
        for project in {l.project for l in records if l.project}:
            yield project.wbs_tree

    def get_sale_line(self, parent):
        pool = Pool()
        SaleLine = pool.get('sale.line')

        sale_line = SaleLine()
        sale_line.type = self.type
        sale_line.description = self.description
        sale_line.sequence = self.sequence
        if self.type == 'line':
            sale_line.product = self.product
            sale_line.unit = self.unit
            sale_line.quantity = 0.0
            sale_line.unit_price = Decimal('0.0')
        sale_line.wbs = self
        if parent:
            sale_line.parent = parent
        return sale_line


class Project:
    __name__ = 'work.project'
    __metaclass__ = PoolMeta

    wbs = fields.One2Many('work.breakdown.structure', 'project',
        'Work Breakdown Structure')
    wbs_tree = fields.Function(fields.One2Many('work.breakdown.structure',
            'project', 'Work Breakdown Structure'),
        'get_wbs_tree')

    def get_wbs_tree(self, name):
        return [x.id for x in self.wbs if not x.parent]

    @classmethod
    def copy(cls, projects, default=None):
        if default is None:
            default = {}
        default['wbs_tree'] = []
        return super(Project, cls).copy(projects, default=default)
