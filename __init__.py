# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import sale
from . import wbs


def register():
    Pool.register(
        sale.Sale,
        sale.SaleLine,
        wbs.WorkBreakdownStructure,
        wbs.Project,
        module='sale_wbs_work_project', type_='model')
