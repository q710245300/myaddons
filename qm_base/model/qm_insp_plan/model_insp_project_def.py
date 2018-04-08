# -*- coding: utf-8 -*-
from openerp import models, fields, api


class qm_insp_project_def(models.Model):
    _name = "qm.insp_project_def"
    name = fields.Many2one('qm.attributes', string='检验特性', required=True)
    quality_quantity_character = fields.Selection([('quality_character', '定性特性'), ('quantity_character', '定量特性')],
                                                  string='定性定量检验', required=True, default='quality_character')
    # 基础字段
    belong_to_plant = fields.Many2one('qm.factory', string='工厂', required=True)
    description = fields.Text(string='描述')
    create_person = fields.Many2one('res.users', string='创建人', default=lambda self: self.env.uid)
    create_time = fields.Datetime(string='创建日期', default=fields.Date.today())
    valid_start = fields.Boolean(string='有效')
    valid_start_date = fields.Datetime(string='有效起始日期')
    # page中的字段
    feature_class = fields.Many2one(related='name.type', string='分类')
    importance_degree = fields.Selection([('key', '关键特性'),
                                          ('importance', '重要特性'),
                                          ('general', '一般特性')], string='特性权重', required=True)
    insp_method_id = fields.Many2one('qm.insp_method_def', string='检验方法')
    result_record_way = fields.Selection([('totle_record', '总计记录'),
                                          ('single_record', '单个记录'),
                                          ('classified_record', '分类记录')]
                                         , string='结果记录方式', required=True)
    sample_plan_yn = fields.Boolean(string='使用独立采样方案')
    sample_plan_id = fields.Many2one('qm.sample_plan', string='采样方案')
    inspection_feature = fields.Boolean(string='必检特性？')
    destructive_inspection = fields.Boolean(string='破坏性检验？')
    spc_yn = fields.Boolean(string="SPC特性")
    spc = fields.Char(string="SPC特性")
    # 定性字段
    defect_record_sec = fields.Boolean(string='缺陷记录')
    accept_depend = fields.Selection([('depend_1', '不合格品数检验'), ('depend_2', '不合格数检验')], string='接收性判定')
    insp_project_def_ids = fields.One2many('qm.defact_records', 'insp_project_def_id', string="结果选项定义")
    # 定量字段
    check_upper_bound = fields.Boolean(string='规范上限')
    check_lower_bound = fields.Boolean(string='规范下线')
    check_target_value = fields.Boolean(string='规范目标值')
    measurement_units = fields.Many2one('product.uom', string='计量单位')
    round_precision = fields.Char(string='舍入精度')
    use_standard_tolerances = fields.Boolean(string='使用标准公差')
    target_value = fields.Float(string='目标值')
    upper_bound = fields.Float(string='上偏差')
    lower_bound = fields.Float(string='下偏差')
    lower_bound_values = fields.Float(string='规范下限(L)')
    upper_bound_values = fields.Float(string='规范上限(U)')
    measurement_classify_ids = fields.One2many('qm.measurement.classify', 'insp_project_def_id', string="定量分类")

    def create(self, cr, uid, vals, context=None):
        print '-------数据清空-------------'
        if vals['quality_quantity_character'] != 'quantity_character':
            if 'check_target_value' in vals:
                vals['check_target_value'] = False
            if 'measurement_units' in vals:
                vals['measurement_units'] = False
            if 'round_precision' in vals:
                vals['round_precision'] = 0.00
            if 'use_standard_tolerances' in vals:
                vals['use_standard_tolerances'] = False
            if 'target_value' in vals:
                vals['target_value'] = 0.00
            if 'lower_bound' in vals:
                vals['lower_bound'] = 0.00
            if 'upper_bound' in vals:
                vals['upper_bound'] = 0.00
            if 'measurement_classify_ids' in vals:
                vals['measurement_classify_ids'] = False
        elif vals['quality_quantity_character'] != 'quality_character':
            if 'defect_record_sec' in vals:
                vals['defect_record_sec'] = False
            if 'insp_project_def_ids' in vals:
                vals['insp_project_def_ids'] = False
        return super(qm_insp_project_def, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):

        if 'quality_quantity_character' in vals:
            if vals['quality_quantity_character'] == 'quantity_character':
                # 得到该记录的id
                defact_record = self.pool.get('qm.defact_records').search(cr, uid,
                                                                          [('insp_project_def_id', '=', ids[0])],
                                                                          context=context)
                vals['insp_project_def_ids'] = False
                # 在该 model中，删除该记录
                self.pool.get('qm.defact_records').unlink(cr, uid, defact_record, context=context)
                vals['defect_record_sec'] = False
            if vals['quality_quantity_character'] == 'quality_character':
                vals['specific_lower_limit'] = False
                vals['specific_upper_limit'] = False
                vals['check_target_value'] = False
                vals['measurement_units'] = False
                vals['round_precision'] = 0.00
                vals['use_standard_tolerances'] = 0.00
                vals['target_value'] = 0.00
                vals['lower_bound'] = 0.00
                vals['upper_bound'] = 0.00
        res = super(qm_insp_project_def, self).write(cr, uid, ids, vals, context=context)
        return res


class qm_defact_records(models.Model):
    _name = "qm.defact_records"

    insp_project_def_id = fields.Many2one('qm.insp_project_def', string='检验项目')
    result_option = fields.Many2one('attributes.values', string='结果选项')
    evaluation = fields.Selection(related='result_option.assess', string="评估")
    defect_class = fields.Many2one(related='result_option.defects', string="缺陷类型")
    defect_level = fields.Many2one(related='defect_class.level', string="缺陷等级")


class qm_measurement_classify(models.Model):
    _name = "qm.measurement.classify"
    insp_project_def_id = fields.Many2one('qm.insp_project_def', string='检验项目')
    name = fields.Char(string='定量分类')
    width = fields.Integer(string="宽度")
    mid_point = fields.Integer(string="中点")
