"""Billing helpers — payment <-> invoice coupling.

Mental model: a case has ONE agreed fee (`case.fee_amount`). Every payment
on that case chips away at it. So for case-linked payments we maintain a
single "master invoice" per case whose total equals the agreed fee, and all
case payments hang off it. Collection % is paid / fee_amount, capped at 100.

For ad-hoc payments with no case (or for a case with no agreed fee yet) we
fall back to an "invoice per payment" model: the invoice total equals the
payment amount.

Two entry points:

1. `record_payment` — creates the Payment, picks/creates the right invoice,
   recomputes status. Returns (payment, invoice).
2. `recompute_invoice_status` — re-derives paid/partially_paid/sent from
   the invoice's current linked payments. Called after add or delete.

Caller always commits.
"""
from decimal import Decimal
from sqlalchemy import func

from app.extensions import db
from app.models.financial import Payment, Invoice, InvoiceItem
from app.models.tenant import Tenant


AUTO_INVOICE_NOTE = 'فاتورة تم إنشاؤها تلقائياً من دفعة'


def _next_invoice_number(tenant_id):
    last = Invoice.query.filter_by(tenant_id=tenant_id).order_by(Invoice.id.desc()).first()
    if last and last.invoice_number:
        try:
            num = int(last.invoice_number.split('-')[-1]) + 1
        except (ValueError, IndexError):
            num = 1
    else:
        num = 1
    return f'INV-{num:05d}'


def _tenant_tax_rate(tenant_id):
    t = Tenant.query.get(tenant_id)
    if t is None or t.default_tax_rate is None:
        return Decimal('0')
    return Decimal(str(t.default_tax_rate))


def recompute_invoice_status(invoice):
    """Re-derive status from currently linked payments.

    Status transitions:
      paid == 0       → 'sent' (or stays at 'draft' if it was never sent)
      0 < paid < tot  → 'partially_paid'
      paid >= tot     → 'paid'

    'cancelled' invoices are left alone — a cancelled invoice that gets a
    payment recorded against it is a data-entry mistake, not a status change.
    'draft' invoices DO get promoted on payment: if money was received the
    invoice is no longer a draft.
    """
    if invoice is None or invoice.status == 'cancelled':
        return
    paid_so_far = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.invoice_id == invoice.id,
        Payment.tenant_id == invoice.tenant_id,
    ).scalar() or Decimal('0')
    paid_total = Decimal(str(paid_so_far))
    invoice_total = Decimal(str(invoice.total or 0))
    if invoice_total <= 0:
        return
    if paid_total >= invoice_total:
        invoice.status = 'paid'
    elif paid_total > 0:
        invoice.status = 'partially_paid'
    else:
        # Drop back to 'sent' rather than 'draft' — the invoice has been
        # active in our system; 'draft' implies "not yet finalized."
        invoice.status = 'sent'


def _find_or_create_case_master_invoice(case, tenant_id, payment_date):
    """Return the master invoice for a case (creates one if missing).

    Master invoice = invoice for this case whose subtotal equals
    case.fee_amount. There's at most one per case.

    If `case.fee_amount` changes after the master invoice already exists,
    we refresh its subtotal, items, and totals so the rollup stays honest.
    """
    if not case or not case.fee_amount or float(case.fee_amount) <= 0:
        return None

    fee_amount = Decimal(str(case.fee_amount))
    tax_rate = _tenant_tax_rate(tenant_id)

    # Identify the master invoice for this case. We can't filter on
    # Invoice.notes in SQL (it's an encrypted column) — so we fetch all
    # case invoices ordered by id and pick the earliest one tagged with
    # AUTO_INVOICE_NOTE via the decrypting Python property. This survives
    # changes to case.fee_amount: we resync the existing master's
    # subtotal/items below instead of creating a second one.
    master = next(
        (inv for inv in Invoice.query.filter_by(
            tenant_id=tenant_id, case_id=case.id,
        ).order_by(Invoice.id.asc()).all()
         if inv.notes == AUTO_INVOICE_NOTE),
        None,
    )

    if master:
        # Sync subtotal/total with current case.fee_amount in case the
        # lawyer updated it after the invoice was first issued.
        if Decimal(str(master.subtotal or 0)) != fee_amount:
            master.subtotal = fee_amount
            tax_amount = (fee_amount * tax_rate / Decimal('100')).quantize(Decimal('0.01'))
            master.tax_rate = tax_rate
            master.tax_amount = tax_amount
            master.total = fee_amount + tax_amount
            # Replace the single line item with the updated fee line.
            for it in master.items.all():
                db.session.delete(it)
            db.session.flush()
            db.session.add(InvoiceItem(
                invoice_id=master.id,
                description=_fee_line_description(case),
                item_type='fees',
                amount=fee_amount,
            ))
        return master

    # No master invoice yet — create one.
    tax_amount = (fee_amount * tax_rate / Decimal('100')).quantize(Decimal('0.01'))
    master = Invoice(
        tenant_id=tenant_id,
        client_id=case.client_id,
        case_id=case.id,
        issue_date=payment_date,
        status='sent',
        tax_rate=tax_rate,
        subtotal=fee_amount,
        tax_amount=tax_amount,
        total=fee_amount + tax_amount,
        notes=AUTO_INVOICE_NOTE,
    )
    master.invoice_number = _next_invoice_number(tenant_id)
    db.session.add(master)
    db.session.flush()
    db.session.add(InvoiceItem(
        invoice_id=master.id,
        description=_fee_line_description(case),
        item_type='fees',
        amount=fee_amount,
    ))
    db.session.flush()
    return master


def _fee_line_description(case):
    bits = ['أتعاب القضية']
    if case.case_number:
        bits.append(case.case_number)
    elif case.subject:
        bits.append(case.subject[:60])
    return ' — '.join(bits)


def record_payment(
    *,
    tenant_id,
    client_id,
    amount,
    payment_date,
    payment_method,
    case_id=None,
    invoice_id=None,
    reference_number=None,
    notes=None,
    recorded_by=None,
    auto_invoice_description=None,
):
    """Record a Payment with the right invoice attached.

    Linking rules (first match wins):
      1. Caller supplied `invoice_id` → use it as-is.
      2. Payment has a case AND the case has `fee_amount` set → find/create
         the case's master invoice (subtotal == case.fee_amount).
      3. Otherwise → auto-create a standalone paid invoice equal to the
         payment amount.
    """
    amount = Decimal(str(amount))
    invoice = None

    if invoice_id:
        invoice = Invoice.query.filter_by(id=invoice_id, tenant_id=tenant_id).first()
        if invoice is None:
            raise ValueError('invoice_id does not belong to this tenant')
        # If the linked invoice already belongs to a case and the caller
        # didn't specify one, inherit it. Otherwise the payment would be
        # missing from case.total_paid even though it clearly relates to
        # the case via the invoice.
        if case_id is None and invoice.case_id:
            case_id = invoice.case_id

    # Path 2: master invoice for a case with a known fee.
    if invoice is None and case_id:
        from app.models.case import Case
        case = Case.query.filter_by(id=case_id, tenant_id=tenant_id).first()
        if case is not None:
            invoice = _find_or_create_case_master_invoice(case, tenant_id, payment_date)

    payment = Payment(
        tenant_id=tenant_id,
        client_id=client_id,
        case_id=case_id,
        invoice_id=invoice.id if invoice else None,
        amount=amount,
        payment_date=payment_date,
        payment_method=payment_method,
        reference_number=reference_number,
        notes=notes,
        recorded_by=recorded_by,
    )
    db.session.add(payment)
    db.session.flush()

    if invoice is None:
        # Path 3: standalone auto-invoice = payment amount.
        tax_rate = _tenant_tax_rate(tenant_id)
        tax_amount = (amount * tax_rate / Decimal('100')).quantize(Decimal('0.01'))
        total = amount + tax_amount
        invoice = Invoice(
            tenant_id=tenant_id,
            client_id=client_id,
            case_id=case_id,
            issue_date=payment_date,
            status='paid',
            tax_rate=tax_rate,
            subtotal=amount,
            tax_amount=tax_amount,
            total=total,
            notes=AUTO_INVOICE_NOTE,
        )
        invoice.invoice_number = _next_invoice_number(tenant_id)
        db.session.add(invoice)
        db.session.flush()
        db.session.add(InvoiceItem(
            invoice_id=invoice.id,
            description=auto_invoice_description or 'أتعاب',
            item_type='fees',
            amount=amount,
        ))
        payment.invoice_id = invoice.id
        db.session.flush()
        recompute_invoice_status(invoice)
    else:
        # Paths 1+2 share this: the payment is now linked, recompute.
        recompute_invoice_status(invoice)

    return payment, invoice


def make_auto_invoice_description(*, case=None, client=None):
    """Line-item label for path-3 standalone invoices."""
    parts = []
    if case:
        if case.case_number:
            parts.append(f'قضية {case.case_number}')
        elif case.subject:
            parts.append(case.subject[:60])
    if client and client.full_name:
        parts.append(client.full_name)
    return 'أتعاب' if not parts else 'أتعاب — ' + ' · '.join(parts)
