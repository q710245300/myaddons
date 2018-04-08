# -*- coding: utf-8 -*-
from openerp import models, fields, api


class qm_work_procedure(models.Model):
    _name = "qm.work_procedure"

    def compute_insp_plan_type(self, cr, uid, context=None):
        print '----------------------------------------------------------', context
        if context is None:
            context = {}
        return context.get('insp_plan_type', False)

    work_procedure_quality_ids_one = fields.One2many('qm.work_quality_insp', 'work_procedure_quality_id',
                                                     '定性')
    work_procedure_quantity_ids_one = fields.One2many('qm.work_quantity_insp', 'work_procedure_quantity_id',
                                                      string='定量')

    work_procedure_quality_ids_two = fields.One2many('qm.work_quality_insp', 'work_procedure_quality_id',
                                                     '定性')
    work_procedure_quantity_ids_two = fields.One2many('qm.work_quantity_insp', 'work_procedure_quantity_id',
                                                      '定量')
    work_procedure_quality_ids_three = fields.One2many('qm.work_quality_insp', 'work_procedure_quality_id',
                                                       '定性')
    work_procedure_quantity_ids_three = fields.One2many('qm.work_quantity_insp', 'work_procedure_quantity_id',
                                                        '定量')
    PLAN_TYPE = [
        ('import_material_insp', '进料检验'),
        ('making_product_insp', '在制品检验'),
        ('making_procedure_insp', '制程终验'),
        ('export_good_insp', '出货检验')
    ]
    INSP_MODE = [
        ('self_inspection', '自检'),
        ('mutual_inspection', '互检'),
        ('special_inspection', '专检')
    ]
    WORK_PROCEDURE_TYPE = [
        ('production', '生产'),
        ('inspection', '检验')
    ]

    name = fields.Char(string='名称', required=True)
    work_num = fields.Char(string='序号' , required=True)
    insp_plan_type = fields.Selection(PLAN_TYPE, string='检验计划类型' , required=True)
    key_work_procedure = fields.Boolean(string='关键工序?')
    quality_standard = fields.Many2one('qm.standard', string='质量标准')
    work_center = fields.Many2one('qm.work.center', string='工作中心')
    work_content_desc = fields.Text(string='工作内容描述')
    inspection_mode = fields.Selection(INSP_MODE, string='检验方式')
    work_procedure_type = fields.Selection(WORK_PROCEDURE_TYPE, string='工序类型')
    hour_count = fields.Float(string='工时数')
    resposible_person = fields.Many2one('res.users', string='检验员', default=lambda self: self.env.uid)
    check_group = fields.Many2one('qm.process.check.group', string='班次')

    _defaults = {
        'insp_plan_type': compute_insp_plan_type,
        'work_num': lambda self, cr, uid, context={}: self.pool.get('ir.sequence').get(cr, uid, 'qm.work_procedure'),
    }


class qm_work_quality_insp(models.Model):
    _name = "qm.work_quality_insp"

    work_procedure_quality_id = fields.Many2one('qm.work_procedure')
    # 检验项目表单关联的字段
    insp_project_def_id = fields.Many2one('qm.insp_project_def', string="检验项目")
    importance_degree = fields.Selection(related='insp_project_def_id.importance_degree', string='重要度 ')
    insp_method_id = fields.Many2one(related='insp_project_def_id.insp_method_id', string='检验方法 ')
    sample_plan_id = fields.Many2one(related='insp_project_def_id.sample_plan_id', string='采样方案')
    result_choice = fields.One2many(related='insp_project_def_id.insp_project_def_ids', string='结果选项')
    inspection_feature = fields.Boolean(related='insp_project_def_id.inspection_feature', string='必检？')
    destructive_inspection = fields.Boolean(related='insp_project_def_id.destructive_inspection', string='破坏性检验？')
    # 采样方案关联的字段
    depend_standard = fields.Many2one(related='sample_plan_id.gb_standard_id', string='依赖标准')
    # 采样方法关联的字段
    test_equipment = fields.Many2one(related='insp_method_id.inspect_equipment', string='测试设备')
    # 扩展字段
    quality_standard = fields.Char(string='质量标准')
    defect_mode = fields.Char(string='不良模式')
    dynamic_modify_rule = fields.Char(string='动态修改规则')
    insp_result = fields.Char(string='检验结果')


class qm_work_quantity_insp(models.Model):
    _name = "qm.work_quantity_insp"

    work_procedure_quantity_id = fields.Many2one('qm.work_procedure')
    # 检验项目表单关联的字段
    insp_project_def_id = fields.Many2one('qm.insp_project_def', string="检验项目")
    importance_degree = fields.Selection(related='insp_project_def_id.importance_degree', string='重要度 ')
    sample_plan_id = fields.Many2one(related='insp_project_def_id.sample_plan_id', string='采样方案')
    insp_method_id = fields.Many2one(related='insp_project_def_id.insp_method_id', string='检验方法 ')
    target_value = fields.Float(related='insp_project_def_id.target_value', string='目标值')
    lower_bound = fields.Float(related='insp_project_def_id.lower_bound_values', string='下限')
    upper_bound = fields.Float(related='insp_project_def_id.upper_bound_values', string='上限')
    measurement_units = fields.Many2one(related='insp_project_def_id.measurement_units', string='计量单位')
    inspection_feature = fields.Boolean(related='insp_project_def_id.inspection_feature', string='必检？')
    destructive_inspection = fields.Boolean(related='insp_project_def_id.destructive_inspection', string='破坏性检验？')
    # 采样方案关联的字段
    depend_standard = fields.Many2one(related='sample_plan_id.gb_standard_id', string='依赖标准')
    # 采样方法关联的字段
    test_equipment = fields.Many2one(related='insp_method_id.inspect_equipment', string='测试设备')
    # 扩展字段
    quality_standard = fields.Char(string='质量标准')
    inspection_site = fields.Char(string='检测部位')
    key_part_nun = fields.Char(string='关键件型号')
    dynamic_modify_rule = fields.Char(string='动态修改规则')

    inspection_points = fields.Float(string='检测点数')
