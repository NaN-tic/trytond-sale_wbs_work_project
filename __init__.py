# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .sale import *
from .wbs import *


def register():
    Pool.register(
        Sale,
        SaleLine,
        WorkBreakdownStructure,
        Project,
        module='sale_wbs_work_project', type_='model')
