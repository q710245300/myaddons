# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import ValidationError


class qm_plan_instruction(models.Model):
    _name = "qm.plan.instruction"
    PLAN_TYPE = [
        ('import_material_insp', '进料检验'),
        ('making_product_insp', '在制品检验'),
        ('making_procedure_insp', '制程终验'),
        ('export_good_insp', '出货检验')
    ]
    DYNAMIC_MODIFY_RULE = [
        ('rule_1', '调整宽严程度'),
        ('rule_2', '调整检验水平'),
        ('rule_4', '调整抽样类型'),
        ('rule_4', '跳批状态调整'),
        ('rule_5', '跳批频率变更'),
        ('rule_6', 's法和σ法的转换'),
    ]
    name = fields.Char(u"检验计划", required=True)
    insp_plan_type = fields.Selection(PLAN_TYPE, u'检验计划类型', required=True)
    usage = fields.Many2one('qm.usage', string=u'使用方法')
    test_object = fields.Selection([('products', u'产品'), ('product_groups', u'产品组'), ], u'检验对象')
    product_id = fields.Many2one('product.template', u'产品名称')
    product_num = fields.Char(related='product_id.product_num', string=u'产品编码')
    # product_category = fields.Selection(related='product_id.type', string=u'产品类别')
    product_type = fields.Char(string=u'产品型号')
    lot_min_max = fields.Char(string=u'批量范围 ')
    lot_min = fields.Integer(u"批量范围下限")
    lot_max = fields.Integer(u"批量范围上限")
    key_parts_num = fields.Char(string=u'关键部件编号')
    key_parts_type = fields.Char(string=u'关键部件型号')
    technology = fields.Many2one('qm.technology', string=u'工艺')
    order_type = fields.Char(string=u'订单类型')
    delivery_type = fields.Char(string=u'交货类型')
    sample_plan_id = fields.Many2one('qm.sample_plan', string=u'采样方案(全局计数)', required=True)
    dynamic_modify_rule = fields.Selection(DYNAMIC_MODIFY_RULE, string=u'动态修改规则')
    interval_of_check = fields.Integer(string=u'检验间隔(天)')

    factory_id = fields.Many2one(related='product_id.factory_id', string=u'工厂')
    supplier_id = fields.Many2one('res.partner', string=u'供应商')
    customer = fields.Many2one('res.users', u'客户')
    stock_location = fields.Char(string=u'库位')
    sub_product_line = fields.Many2one('qm.pro.line.kid', string=u'子生产线')
    product_line = fields.Many2one(related='sub_product_line.belong_pro_line', string=u'生产线')

    test_charge_persion = fields.Many2one('res.users', u'检验责任人', default=lambda self: self.env.uid)
    planner_group = fields.Many2one('qm.plan.person.group', string=u'计划者组')
    date_start = fields.Date(string=u'有效起始日期', default=fields.Date.today())

    product_ids = fields.One2many('qm.plan.product.group', 'qm_plan_insp_id', u'产品组')

    stock_address = fields.Char(string=u'库存地点')

    workstage_one = fields.One2many('qm.workstage', 'qm_plan_inst_id', u'工序总览')
    workstage_two = fields.One2many('qm.workstage', 'qm_plan_inst_id', u'工序总览')
    workstage_three = fields.One2many('qm.workstage', 'qm_plan_inst_id', u'工序总览')
    workstage_four = fields.One2many('qm.workstage', 'qm_plan_inst_id', u'工序总览')

    @api.multi
    @api.onchange('lot_max')
    def _onchange_lot_min_max(self):
        if self.lot_max == self.lot_min == 0:
            print '创建过程批量范围都为零'
        elif self.lot_max <= self.lot_min:
            self.update({'lot_max': False})
            raise ValidationError('批量上限必须大于批量下限！')

    @api.multi
    @api.onchange('test_object')
    def _onchange_equipment(self):
        self.partner_object = False

    def create(self, cr, uid, vals, context=None):
        if vals['insp_plan_type'] == 'import_material_insp':
            if vals['test_object']:
                vals['product_type'] = False
                vals['key_parts_type'] = False
                vals['key_parts_num'] = False
                vals['order_type'] = False
                vals['stock_address'] = False
                vals['customer'] = False
                vals['delivery_type'] = False
                vals['technology'] = False
                if vals['test_object'] == 'products':
                    vals['product_ids'] = False
                else:
                    vals['product_id'] = False
                    vals['product_num'] = False
                    vals['product_category'] = False
                    vals['dynamic_modify_rule'] = False
                    vals['product_partner'] = False
                    vals['stock_location'] = False
            else:
                raise ValidationError('进料检验时需要选择检验对象！')

        else:
            vals['test_object'] = False
            vals['product_ids'] = False
            vals['product_partner'] = False
            vals['dynamic_modify_rule'] = False
            vals['product_num'] = False
            vals['product_category'] = False
            vals['stock_location'] = False
            if vals['insp_plan_type'] == 'making_product_insp':
                vals['key_parts_type'] = False
                vals['key_parts_num'] = False
                vals['order_type'] = False
                vals['stock_address'] = False
                vals['customer'] = False
                vals['delivery_type'] = False
            if vals['insp_plan_type'] == 'making_procedure_insp':
                vals['technology'] = False
                vals['order_type'] = False
                vals['stock_address'] = False
                vals['customer'] = False
                vals['delivery_type'] = False
            if vals['insp_plan_type'] == 'export_good_insp':
                vals['technology'] = False
                vals['key_parts_type'] = False
                vals['key_parts_num'] = False
                vals['product_line'] = False
                vals['sub_product_line'] = False
        return super(qm_plan_instruction, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        line = self.browse(cr, uid, ids[0], context=context)
        product_groups = self.pool.get('qm.plan.product.group').search(cr, uid, [('qm_plan_insp_id', '=', ids[0])],
                                                                       context=context)
        if 'insp_plan_type' in vals:
            if vals['insp_plan_type'] and vals['insp_plan_type'] == 'import_material_insp':
                vals['product_type'] = False
                vals['key_parts_type'] = False
                vals['key_parts_num'] = False
                vals['product_line'] = False
                vals['sub_product_line'] = False
                vals['order_type'] = False
                vals['stock_address'] = False
                vals['customer'] = False
                vals['delivery_type'] = False
                vals['technology'] = False
                if 'test_object' in vals and vals['test_object']:
                    if vals['test_object'] == 'products':
                        vals['product_ids'] = False
                        self.pool.get('qm.plan.product.group').unlink(cr, uid, product_groups, context=context)
                    else:
                        vals['product_id'] = False
                        vals['product_num'] = False
                        vals['product_category'] = False
                        vals['dynamic_modify_rule'] = False
                        vals['product_partner'] = False
                        vals['stock_location'] = False
                elif line.test_object:
                    if line.test_object == 'products':
                        vals['product_ids'] = False
                    else:
                        vals['product_id'] = False
                        vals['product_num'] = False
                        vals['product_category'] = False
                        vals['dynamic_modify_rule'] = False
                        vals['product_partner'] = False
                        vals['stock_location'] = False
                else:
                    raise ValidationError('进料检验时需要选择检验对象！')
            else:
                vals['test_object'] = False
                vals['product_ids'] = False
                vals['product_partner'] = False
                vals['dynamic_modify_rule'] = False
                vals['product_num'] = False
                vals['product_category'] = False
                vals['stock_location'] = False
                self.pool.get('qm.plan.product.group').unlink(cr, uid, product_groups, context=context)
                if vals['insp_plan_type'] == 'making_product_insp':
                    vals['key_parts_type'] = False
                    vals['key_parts_num'] = False
                    vals['order_type'] = False
                    vals['stock_address'] = False
                    vals['customer'] = False
                    vals['delivery_type'] = False
                if vals['insp_plan_type'] == 'making_procedure_insp':
                    vals['technology'] = False
                    vals['order_type'] = False
                    vals['stock_address'] = False
                    vals['customer'] = False
                    vals['delivery_type'] = False
                if vals['insp_plan_type'] == 'export_good_insp':
                    vals['technology'] = False
                    vals['key_parts_type'] = False
                    vals['key_parts_num'] = False
                    vals['product_line'] = False
                    vals['sub_product_line'] = False
        else:
            if line.insp_plan_type == 'import_material_insp':
                vals['product_type'] = False
                vals['key_parts_type'] = False
                vals['key_parts_num'] = False
                vals['order_type'] = False
                vals['stock_address'] = False
                vals['customer'] = False
                vals['delivery_type'] = False
                vals['technology'] = False
                if 'test_object' in vals and vals['test_object']:
                    if vals['test_object'] == 'products':
                        vals['product_ids'] = False
                        self.pool.get('qm.plan.product.group').unlink(cr, uid, product_groups, context=context)
                    else:
                        vals['product_id'] = False
                        vals['product_num'] = False
                        vals['product_category'] = False
                        vals['dynamic_modify_rule'] = False
                        vals['product_partner'] = False
                        vals['stock_location'] = False
                elif line.test_object:
                    if line.test_object == 'products':
                        vals['product_ids'] = False
                        self.pool.get('qm.plan.product.group').unlink(cr, uid, product_groups, context=context)
                    else:
                        vals['product_id'] = False
                        vals['product_num'] = False
                        vals['product_category'] = False
                        vals['dynamic_modify_rule'] = False
                        vals['product_partner'] = False
                        vals['stock_location'] = False
                else:
                    raise ValidationError('进料检验时需要选择检验对象！')
            else:
                vals['test_object'] = False
                vals['product_ids'] = False
                vals['product_partner'] = False
                vals['dynamic_modify_rule'] = False
                vals['product_num'] = False
                vals['product_category'] = False
                vals['stock_location'] = False
                self.pool.get('qm.plan.product.group').unlink(cr, uid, product_groups, context=context)
                if line.insp_plan_type == 'making_product_insp':
                    vals['key_parts_type'] = False
                    vals['key_parts_num'] = False
                    vals['order_type'] = False
                    vals['stock_address'] = False
                    vals['customer'] = False
                    vals['delivery_type'] = False
                if line.insp_plan_type == 'making_procedure_insp':
                    vals['technology'] = False
                    vals['order_type'] = False
                    vals['stock_address'] = False
                    vals['customer'] = False
                    vals['delivery_type'] = False
                if line.insp_plan_type == 'export_good_insp':
                    vals['technology'] = False
                    vals['key_parts_type'] = False
                    vals['key_parts_num'] = False
                    vals['product_line'] = False
                    vals['sub_product_line'] = False

        return super(qm_plan_instruction, self).write(cr, uid, ids, vals, context=context)


class qm_plan_product_group(models.Model):
    _name = "qm.plan.product.group"

    qm_plan_insp_id = fields.Many2one('qm.plan.instruction', '检验计划', select=True, ondelete='cascade')
    product_id = fields.Many2one('product.template', '产品')
    product_num = fields.Char('产品编号')
    factory = fields.Char('工厂')
    stock_location = fields.Char('库位')


class qm_workstage(models.Model):
    _name = "qm.workstage"

    qm_plan_inst_id = fields.Many2one('qm.plan.instruction', '检验计划', select=True, ondelete='cascade')
    workstage_id = fields.Many2one('qm.work_procedure', '工序名称')
    work_num = fields.Char(related='workstage_id.work_num', string='工序序号')
    work_procedure_type = fields.Selection(related='workstage_id.work_procedure_type', string='工序类型')
    key_work_procedure = fields.Boolean(related='workstage_id.key_work_procedure', string='关键工序？')
    work_content_desc = fields.Text(related='workstage_id.work_content_desc', string='工作内容描述')
    quality_standard = fields.Many2one(related='workstage_id.quality_standard', string='质量标准')
    work_center = fields.Many2one(related='workstage_id.work_center', string='工作中心')
    inspection_mode = fields.Selection(related='workstage_id.inspection_mode', string='检验方式')
    hour_count = fields.Float(related='workstage_id.hour_count', string='工时数')
    resposible_person = fields.Many2one(related='workstage_id.resposible_person', string='责任人')
    check_group = fields.Many2one(related='workstage_id.check_group', string='班次')
