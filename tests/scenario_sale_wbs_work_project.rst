==============================
Sale Work Project WBS Scenario
==============================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> today = datetime.date.today()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install sale::

    >>> Module = Model.get('ir.module.module')
    >>> module, = Module.find([('name', '=', 'sale_wbs_work_project')])
    >>> Module.install([module.id], config.context)
    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')

Create company::

    >>> Currency = Model.get('currency.currency')
    >>> CurrencyRate = Model.get('currency.currency.rate')
    >>> currencies = Currency.find([('code', '=', 'USD')])
    >>> if not currencies:
    ...     currency = Currency(name='U.S. Dollar', symbol='$', code='USD',
    ...         rounding=Decimal('0.01'), mon_grouping='[3, 3, 0]',
    ...         mon_decimal_point='.', mon_thousands_sep=',')
    ...     currency.save()
    ...     CurrencyRate(date=today + relativedelta(month=1, day=1),
    ...         rate=Decimal('1.0'), currency=currency).save()
    ... else:
    ...     currency, = currencies
    >>> Company = Model.get('company.company')
    >>> Party = Model.get('party.party')
    >>> company_config = Wizard('company.company.config')
    >>> company_config.execute('company')
    >>> company = company_config.form
    >>> party = Party(name='Dunder Mifflin')
    >>> party.save()
    >>> company.party = party
    >>> company.currency = currency
    >>> company_config.execute('add')
    >>> company, = Company.find([])

Reload the context::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')
    >>> config._context = User.get_preferences(True, config.context)

Create fiscal year::

    >>> FiscalYear = Model.get('account.fiscalyear')
    >>> Sequence = Model.get('ir.sequence')
    >>> SequenceStrict = Model.get('ir.sequence.strict')
    >>> fiscalyear = FiscalYear(name=str(today.year))
    >>> fiscalyear.start_date = today + relativedelta(month=1, day=1)
    >>> fiscalyear.end_date = today + relativedelta(month=12, day=31)
    >>> fiscalyear.company = company
    >>> post_move_seq = Sequence(name=str(today.year), code='account.move',
    ...     company=company)
    >>> post_move_seq.save()
    >>> fiscalyear.post_move_sequence = post_move_seq
    >>> invoice_seq = SequenceStrict(name=str(today.year),
    ...     code='account.invoice', company=company)
    >>> invoice_seq.save()
    >>> fiscalyear.out_invoice_sequence = invoice_seq
    >>> fiscalyear.in_invoice_sequence = invoice_seq
    >>> fiscalyear.out_credit_note_sequence = invoice_seq
    >>> fiscalyear.in_credit_note_sequence = invoice_seq
    >>> fiscalyear.save()
    >>> FiscalYear.create_period([fiscalyear.id], config.context)

Create chart of accounts::

    >>> AccountTemplate = Model.get('account.account.template')
    >>> Account = Model.get('account.account')
    >>> Journal = Model.get('account.journal')
    >>> account_template, = AccountTemplate.find([('parent', '=', None)])
    >>> create_chart = Wizard('account.create_chart')
    >>> create_chart.execute('account')
    >>> create_chart.form.account_template = account_template
    >>> create_chart.form.company = company
    >>> create_chart.execute('create_account')
    >>> receivable, = Account.find([
    ...         ('kind', '=', 'receivable'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> payable, = Account.find([
    ...         ('kind', '=', 'payable'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> revenue, = Account.find([
    ...         ('kind', '=', 'revenue'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> expense, = Account.find([
    ...         ('kind', '=', 'expense'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> create_chart.form.account_receivable = receivable
    >>> create_chart.form.account_payable = payable
    >>> create_chart.execute('create_properties')
    >>> cash, = Account.find([
    ...         ('kind', '=', 'other'),
    ...         ('name', '=', 'Main Cash'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> cash_journal, = Journal.find([('type', '=', 'cash')])
    >>> cash_journal.credit_account = cash
    >>> cash_journal.debit_account = cash
    >>> cash_journal.save()

Create parties::

    >>> Party = Model.get('party.party')
    >>> supplier = Party(name='Supplier')
    >>> supplier.save()
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create category::

    >>> ProductCategory = Model.get('product.category')
    >>> category = ProductCategory(name='Category')
    >>> category.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.category = category
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.purchasable = True
    >>> template.salable = True
    >>> template.list_price = Decimal('10')
    >>> template.cost_price = Decimal('8')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> product1, = template.products
    >>> product2 = template.products.new()
    >>> product2.save()

    >>> template = ProductTemplate()
    >>> template.name = 'service'
    >>> template.default_uom = unit
    >>> template.type = 'service'
    >>> template.salable = True
    >>> template.list_price = Decimal('30')
    >>> template.cost_price = Decimal('10')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> service1, = template.products
    >>> service2 = template.products.new()
    >>> service2.save()

Create payment term::

    >>> PaymentTerm = Model.get('account.invoice.payment_term')
    >>> PaymentTermLine = Model.get('account.invoice.payment_term.line')
    >>> payment_term = PaymentTerm(name='Direct')
    >>> payment_term_line = PaymentTermLine(type='remainder', days=0)
    >>> payment_term.lines.append(payment_term_line)
    >>> payment_term.save()

Create a Project::

    >>> Project = Model.get('work.project')
    >>> project = Project()
    >>> project.code = 'MAIN'
    >>> project.party = customer
    >>> project.save()

Create a Sale::

    >>> Sale = Model.get('sale.sale')
    >>> SaleLine = Model.get('sale.line')
    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale.invoice_method = 'shipment'
    >>> sale.project = project
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product1
    >>> sale_line.description = 'Product Line 1'
    >>> sale_line.quantity = 10
    >>> sale_line = sale.lines.new()
    >>> sale_line.type = 'title'
    >>> sale_line.description = 'Chapter 1'
    >>> sale.save()
    >>> product1_line, chapter1_line = sale.lines
    >>> child_sale_line = sale.lines.new()
    >>> child_sale_line.parent = SaleLine(chapter1_line.id)
    >>> child_sale_line.product = service1
    >>> child_sale_line.description = 'Service Line 1'
    >>> child_sale_line.quantity = 5
    >>> sale.save()

Sale's and project's WBS are computed when it is quoted::

    >>> sale.wbs_tree
    []
    >>> project.wbs_tree
    []
    >>> sale.click('quote')
    >>> len(sale.wbs_tree)
    2
    >>> for wbs in sale.wbs_tree:
    ...     len(wbs.childs), len(wbs.sale_lines)
    (0, 1)
    (1, 1)
    >>> all(bool(l.wbs) for l in sale.lines)
    True
    >>> project.reload()
    >>> len(project.wbs_tree)
    2
    >>> for wbs in project.wbs_tree:
    ...     len(wbs.childs)
    0
    1

Going back to draft deletes the structure::

    >>> sale.click('draft')
    >>> project.reload()
    >>> sale.wbs_tree
    []
    >>> project.wbs_tree
    []
    >>> sale.click('quote')

Create a second sale related to the same project::

    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale.invoice_method = 'shipment'
    >>> sale.project = project
    >>> sale_line = sale.lines.new()
    >>> sale_line.type = 'title'
    >>> sale_line.description = 'Chapter 1'
    >>> sale_line = sale.lines.new()
    >>> sale_line.type = 'title'
    >>> sale_line.description = 'Chapter 2'
    >>> sale.save()
    >>> chapter1_line, chapter2_line = sale.lines
    >>> child_sale_line = sale.lines.new()
    >>> child_sale_line.parent = SaleLine(chapter1_line.id)
    >>> child_sale_line.product = service1
    >>> child_sale_line.description = 'Service Line 1'
    >>> child_sale_line.quantity = 3
    >>> child_sale_line = sale.lines.new()
    >>> child_sale_line.parent = SaleLine(chapter1_line.id)
    >>> child_sale_line.product = product2
    >>> child_sale_line.description = 'Product Line 2'
    >>> child_sale_line.quantity = 15
    >>> child_sale_line = sale.lines.new()
    >>> child_sale_line.parent = SaleLine(chapter2_line.id)
    >>> child_sale_line.product = service2
    >>> child_sale_line.description = 'Service Line 2'
    >>> child_sale_line.quantity = 10
    >>> sale.save()

Check sale structure and sale's WBS::

    >>> len(sale.lines)
    5
    >>> len(sale.lines_tree)
    2
    >>> for line in sale.lines_tree:
    ...     len(line.childs), bool(line.wbs)
    (2, False)
    (1, False)
    >>> for wbs in sale.wbs_tree:
    ...     len(wbs.childs), len(wbs.sale_lines)
    (0, 1)
    (1, 1)

When the sale is quoted, it is completed with project's WBS and project's WBS
is completed with sale lines::

    >>> sale.click('quote')
    >>> len(sale.lines)
    6
    >>> len(sale.lines_tree)
    3
    >>> for line in sale.lines_tree:
    ...     len(line.childs), bool(line.wbs)
    (2, True)
    (1, True)
    (0, True)
    >>> for wbs in sale.wbs_tree:
    ...     len(wbs.childs), len(wbs.sale_lines)
    ...     for wbs_child in wbs.childs:
    ...         len(wbs_child.childs), len(wbs_child.sale_lines)
    (0, 2)
    (2, 2)
    (0, 2)
    (0, 1)
    (1, 1)
    (0, 1)
    >>> project.reload()
    >>> for wbs in project.wbs_tree:
    ...     len(wbs.childs), len(wbs.sale_lines)
    ...     for wbs_child in wbs.childs:
    ...         len(wbs_child.childs), len(wbs_child.sale_lines)
    (0, 2)
    (2, 2)
    (0, 2)
    (0, 1)
    (1, 1)
    (0, 1)

