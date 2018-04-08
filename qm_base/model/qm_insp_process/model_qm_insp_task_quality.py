# -*- coding: utf-8 -*-
from openerp import models, fields, api


class InspectionTaskQuality(models.Model):
    _name = "qm.insp.task.quality"
    insp_task_record_id = fields.Many2one("qm.insp.task", string="质检工序工序单")

    # 检验计划数据
    name = fields.Char("定性项目单据")
    project_id = fields.Many2one("qm.insp_project_def", string="检验项目")
    project_type = fields.Selection([('quality', '定性特性'), ('quantify', '定量特性')], string="特性类型")
    importance_degree = fields.Selection([('key', '关键特性'),
                                          ('importance', '重要特性'),
                                          ('general', '一般特性')], string='特性权重')
    depend_standard = fields.Many2one('qm.standard', string='依赖标准')
    insp_method_id = fields.Many2one('qm.insp_method_def', string='检验方法')
    sample_count = fields.Integer(string='采样数量')
    ac = fields.Float(string="Ac")
    re = fields.Float(string="Re")
    result_record_way = fields.Selection([('single_record', '单个记录'),
                                          ('classified_record', '分类记录'),
                                          ('total_record', '总计记录')], string='记录方式')
    accept_depend = fields.Selection([('depend_1', '不合格品数检验'), ('depend_2', '不合格数检验')], string='接收性判定依据')

    # 样本检验结束之后的数据
    record_bill = fields.Many2one("qm.insp.task.record", string="结果记录")
    defect_record = fields.Many2one("qm.defect.records", string="缺陷记录")
    d = fields.Integer(related='record_bill.d', string="d")
    defect_level = fields.Many2one('defects.level',string="缺陷等级")#, related='defect_record.heightest_defect_leval'
    project_accept = fields.Selection(related='record_bill.project_accept', string="状态")

	
	#2016年9月28日10:49:28 zhaoli
    #def action_open_defect_records(self, cr, uid, ids, context=None):
    #    if context is None:
    #            context = {}
    #    #创建新的不合格品评审单
    #    defect_records = self.pool.get('qm.defect.records')
    #    #如果defect_records已经存在，则是编辑，如果不存在，则是新建页面
    #    qm_it_qty = self.browse(cr,uid,ids[0],context=context)
    #
    #    #创建基础关联数据
    #    defect_records_id = 0
    #    print qm_it_qty.insp_task_record_id
    #    print qm_it_qty.insp_task_record_id.product_id
    #    print qm_it_qty.insp_task_record_id.id
    #    print '====================='
    #    if qm_it_qty.defect_record:
    #        defect_records_id = qm_it_qty.defect_record.id
    #    else:
    #        vals={
    #            'name':self.pool.get('ir.sequence').get(cr, uid,'qm.defect.records'),
    #            'defect_record_leval':'检验特性',
    #           # 'product_id':qm_it_qty.insp_task_record_id.product_id.id,
    #           # 'test_process':qm_it_qty.insp_task_record_id.id,#检验工序
    #
    #        }
    #        defect_records_id = defect_records.create(cr,uid,vals,context)
    #    self.write(cr,uid,ids,{'defect_record':defect_records_id},context=context)
    #    #实现页面跳转
    #    return {
    #        'view_type': 'form',
    #        'view_mode': 'form',
    #        'res_model': 'qm.defect.records',
    #        'type': 'ir.actions.act_window',
    #        'res_id':defect_records_id,
    #        'context': context,
    #        'target':'new'
    #    }