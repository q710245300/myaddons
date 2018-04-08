# -*- coding: utf-8 -*-
from openerp import models, fields, api


class Policy(models.Model):
    _name = 'qm.policy'

    # 使用决策
    name = fields.Char('使用决策', required=True)

