# -*- coding: utf-8 -*-
from openerp import models, fields, api


class qm_insp_task_quantify(models.Model):
    _name = "qm.insp.task.quantify"
    insp_task_record_id = fields.Many2one("qm.insp.task", string="质检工序工序单")

    # 检验计划数据
    name = fields.Char("定量项目单据")
    project_id = fields.Many2one("qm.insp_project_def", string="检验项目")
    project_type = fields.Selection([('quality', '定性特性'), ('quantify', '定量特性')], string="特性类型")
    importance_degree = fields.Selection([('key', '关键特性'),
                                          ('importance', '重要特性'),
                                          ('general', '一般特性')], string='特性权重')
    depend_standard = fields.Many2one('qm.standard', string='依赖标准')
    insp_method_id = fields.Many2one('qm.insp_method_def', string='检验方法')
    sample_count = fields.Integer(string='采样数量')
    target_value = fields.Float(string='目标值')
    u = fields.Float(string="规范上限")
    l = fields.Float(string="规范下线")
    measurement_units = fields.Many2one('product.uom', string='计量单位')
    result_record_way = fields.Selection([('single_record', '单个记录'),
                                          ('classified_record', '分类记录'),
                                          ('total_record', '总计记录')], string='记录方式')
    accept_depend = fields.Selection([('depend_1', '不合格品数检验'), ('depend_2', '不合格数检验')], string='接收性判定依据')

    # 样本检验结束之后的数据
    record_bill = fields.Many2one("qm.insp.task.record", string="结果记录")
    x_max = fields.Float(related='record_bill.x_max', string='最大值')
    x_min = fields.Float(related='record_bill.x_min', string='最小值')
    x_avg = fields.Float(related='record_bill.x_avg', string='平均值')
    s = fields.Float(related='record_bill.s', string='S')
    r = fields.Float(related='record_bill.r', string='R')
    me = fields.Float(related='record_bill.me', string='Me')
    out_limit_count = fields.Integer(related='record_bill.out_limit_count', string="超限数量")

    defect_record = fields.Many2one("qm.defect.records", string="缺陷记录")
    defect_level = fields.Many2one(string="缺陷等级")#, related='defect_record.heightest_defect_leval'
    project_accept = fields.Selection(related='record_bill.project_accept', string="状态")
