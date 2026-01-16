# -*- coding: utf-8 -*-
from odoo import fields, models

class TelebirrOrderMapping(models.Model):
    """
    Keeps the relationship between Telebirr's `merch_order_id`
    (returned in the asynchronous callback) and the *original*
    transaction reference *and* the database it lives in.
    """
    _name = "telebirr.order.mapping"
    _description = "Telebirr → Odoo transaction mapping"
    _rec_name = "merch_order_id"
    _order = 'id desc'

    _telebirr_merch_order_uniq = models.Constraint(
        'unique(merch_order_id, db_name)',
        'Each Telebirr merchant order id must be unique per database.'
    )

    merch_order_id   = fields.Char(required=True, index=True)
    original_reference = fields.Char(required=True)
    db_name            = fields.Char(required=True, default=lambda self: self.env.cr.dbname)
    tx_id            = fields.Many2one('payment.transaction', ondelete='cascade')
                 
