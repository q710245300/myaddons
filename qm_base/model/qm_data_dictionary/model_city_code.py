# -*- coding: utf-8 -*-
from openerp import models, fields, api


# 城市代码
class CityCode(models.Model):
    _name = "qm.city.code"

    CITY_CODE = [
        ('BJS', '北京'),
        ('SHA', '上海'),
        ('CAN', '广州'),
        ('SZX', '深圳'),
    ]

    name = fields.Selection(CITY_CODE, string="城市名称")
    code = fields.Char("城市代码")

    @api.multi
    @api.onchange('name')
    def create_city_code(self):
        self.code = self.name

