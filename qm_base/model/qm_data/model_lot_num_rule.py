# -*- coding: utf-8 -*-
import time
from openerp import models, fields, api
from openerp.exceptions import ValidationError


class LotNumRule(models.Model):
    _name = "qm.lot.num.rule"

    name = fields.Char("批次号")
    product_num = fields.Many2one("qm.product.num", string="物料编码")
    partner_num = fields.Many2one("qm.partner.num", string="供应商编码")
    equipment_num = fields.Many2one("qm.equipment.num", string="设备编码")

    customer_num = fields.Many2one("qm.customer.num", string="客户编码")
    pro_line_num = fields.Many2one("qm.pro.line.num", string="生产线编码")
    daytime_num = fields.Many2one("qm.daytime.num", string="日期编码")

    @api.multi
    def create_lot_num(self):
        product_num = str(self.product_num.name)
        partner_num = str(self.partner_num.name)
        equipment_num = str(self.equipment_num.name)
        customer_num = str(self.customer_num.name)
        pro_line_num = str(self.pro_line_num.name)
        daytime_num = str(self.daytime_num.name)

        lot_num = ""

        # 物料编码 和 日期编码 处理
        if product_num is "False":
            raise ValidationError('"物料编码" 不可为空，请从新选填！')
        else:
            if len(product_num) == 6:
                lot_num += product_num
            else:
                raise ValidationError('"物料编码" 位数有误，请从新选填！')
        # 供应商编码处理
        if partner_num is "False":
            print "======供应商编码为空======"
        else:
            if len(partner_num) == 7:
                lot_num += partner_num
            else:
                raise ValidationError('"物料编码" 位数有误，请从新选填！')
        # 设备编码处理
        if equipment_num is "False":
            print "======设备编码为空======"
        else:
            if len(equipment_num) == 7:
                lot_num += equipment_num
            else:
                raise ValidationError('"设备编码" 位数有误，请从新选填！')
        # 客户编码处理
        if customer_num is "False":
            print "======客户编码为空======"
        else:
            if len(customer_num) == 7:
                lot_num += customer_num
            else:
                raise ValidationError('"客户编码" 位数有误，请从新选填！')
        # 生产线编码处理
        if pro_line_num is "False":
            print "======生产线编码为空======"
        else:
            if len(pro_line_num) == 7:
                lot_num += pro_line_num
            else:
                raise ValidationError('"生产线编码" 位数有误，请从新选填！')
        # 日期编码处理
        if daytime_num is "False":
            raise ValidationError('"物料编码" 不可为空，请从新选填！')
        else:
            if len(product_num) == 6:
                lot_num += product_num
            else:
                raise ValidationError('"物料编码" 位数有误，请从新选填！')

        self.name = lot_num


# 物料编码
class ProductNum(models.Model):
    _name = "qm.product.num"
    name = fields.Char("物料编码名称")
    belong_product = fields.Many2one("product.template", string="所属物料")


# 供应商编码
class PartnerNum(models.Model):
    _name = "qm.partner.num"

    name = fields.Char("供应商编码")
    belong_partner = fields.Many2one("res.partner", string="所属供应商")
    belong_city = fields.Many2one("qm.city.code", string="所在城市")
    partner_num = fields.Char("序号（例：010）")

    @api.multi
    def create_partner_code(self):
        belong_city = str(self.belong_city.code)
        partner_num = str(self.partner_num)

        if belong_city is "False" or partner_num is "False":
            raise ValidationError('"所在城市" 或 "序号" 为空，请从新选填！')
        else:
            if len(belong_city) == 3 and len(partner_num) == 3:
                partner_code = "S" + belong_city + partner_num
            else:
                raise ValidationError('"所在城市" 或 "序号" 只能为3位数，请从新选填！')
        self.name = partner_code


# 设备编码
class EquipmentNum(models.Model):
    _name = "qm.equipment.num"

    name = fields.Char("设备编码")
    belong_equipment = fields.Many2one("hr.equipment", string="所属设备")
    max_type_code = fields.Char(string="大类别代号（0～9)")
    type_code = fields.Char(string="分类别代号（0～9)")
    group_code = fields.Char(string="组别代号（0～9)")
    equipment_num = fields.Char(string="序号(例：003)")

    @api.multi
    def create_equipment_code(self):
        max_type_code = str(self.max_type_code)
        type_code = str(self.type_code)
        group_code = str(self.group_code)
        equipment_num = str(self.equipment_num)
        if max_type_code is "False" or type_code is "False" or group_code is "False" or equipment_num is "False":
            raise ValidationError('所有字段不允许为空，请从新填写！')
        else:
            if len(max_type_code) == 1 and len(type_code) == 1 and len(group_code) == 1 and len(equipment_num) == 3:
                equipment_code = "P" + max_type_code + type_code + group_code + equipment_num
            else:
                raise ValidationError('字段位数不匹配，请从新选填！')
        self.name = equipment_code


# 生产线编码
class ProLineNum(models.Model):
    _name = "qm.pro.line.num"

    name = fields.Char("生产线编码")
    belong_factory = fields.Many2one('qm.factory', string="所属工厂")
    factory_code = fields.Char(related='belong_factory.code', string="工厂代码(例：03)")
    work_shop_code = fields.Char(string="车间代码(例：09)")
    product_line_num = fields.Char(string="生产线编号(例：03)")

    @api.multi
    def create_pro_line_code(self):
        factory_code = str(self.factory_code)
        work_shop_code = str(self.work_shop_code)
        product_line_num = str(self.product_line_num)
        if factory_code is "False" or work_shop_code is "False" or product_line_num is "False":
            raise ValidationError('"工厂代码" 或 "车间代码" 或 "生产线编号" 为空，请从新填写！')
        else:
            if len(factory_code) == 2 and len(work_shop_code) == 2 and len(product_line_num) == 2:
                product_line_code = "E" + factory_code + work_shop_code + product_line_num
            else:
                raise ValidationError('"工厂代码" 或 "车间代码" 或 "生产线编号" 位数不匹配，请从新选填！')
        self.name = product_line_code


# 客户编号编码
class CustomerNum(models.Model):
    _name = "qm.customer.num"
    name = fields.Char("客户编码名称")
    belong_customer = fields.Many2one("res.partner", string="所属客户")
    belong_city = fields.Many2one("qm.city.code", string="所在城市")
    customer_num = fields.Char("序号（例：010）")

    @api.multi
    def create_customer_code(self):
        belong_city = str(self.belong_city.code)
        customer_num = str(self.customer_num)
        if belong_city is "False" or customer_num is "False":
            raise ValidationError('"所在城市" 或 "序号" 为空，请从新选填！')
        else:
            if len(belong_city) == 3 and len(customer_num) == 3:
                customer_code = "C" + belong_city + customer_num
            else:
                raise ValidationError('"所在城市" 或 "序号" 只能为3位数，请从新选填！')
        self.name = customer_code


# 日期编码
class DayTimeNum(models.Model):
    _name = "qm.daytime.num"

    name = fields.Char("日期编码码")
    current_time = fields.Date(string="当前系统时间")

    _defaults = {'current_time': lambda *args: fields.date.today()}

    @api.multi
    @api.onchange('current_time')
    def create_date_code(self):
        # create_time = time.strftime("%Y%m%d", time.localtime(time.time()))
        list_time = str(self.current_time).split("-")
        current_time_str = list_time[0] + list_time[1] + list_time[2]
        self.name = current_time_str[-6:]
