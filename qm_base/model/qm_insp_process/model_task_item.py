# -*- coding: utf-8 -*-
from openerp import models, fields, api


class qm_check_task_item(models.Model):
    _name = "qm.check_task_item"

    name = fields.Char(string="项目特性检验单")
    inspection_order_id = fields.Many2one('qm.inspection.order', string='质量订单', readonly=True)
    workstage_order = fields.Char(string='工序序号', readonly=True)
    workstage_name = fields.Char(string='工序名称', readonly=True)
    workstage_name_fu = fields.Char(string='工序名称', readonly=True)
    sample_count = fields.Integer(string='样本量')
    procedure_name = fields.Char(string='检验项目', readonly=True)
    check_task_item_ids = fields.One2many('qm.check_each_item', 'check_task_item_id', string='检验数据')
    is_acceptance = fields.Boolean(string='接收性')
    _defaults = {'name': lambda self, cr, uid, context: self.pool['ir.sequence'].next_by_code(cr, uid,
                                                                                              'qm.check_task_item.name',
                                                                                              context=context)}

    # 马立乾添加
    defect_counts = fields.Integer(string='不合格数')
    check_each_status = fields.Char(string='检测结果码')
    '''
    根据样本量值创建样本检验表单
        未能实现自动触发过程
    '''
    # @api.onchange('sample_count')
    @api.multi
    def create_sample_record(self):
        sample_count = self.sample_count
        # 数据存储
        lines = []
        if sample_count is not None and sample_count != 0:
            # 循环创建记录
            for x in range(sample_count):
                # 循环计量值
                line_item = {
                    'each_item_num': x + 1,
                    'each_item_result': '',
                    'is_qulified': False
                }
                lines.append(line_item)
        # 更新检记录
        self.update({'check_task_item_ids': lines})

    '''
    统计不合格数
    '''
    @api.multi
    @api.onchange('check_task_item_ids')
    def compute_defect_counts(self):
        check_each_item_records = self.check_task_item_ids
        if check_each_item_records is not None:
            # 工序数量统计
            records_len = len(check_each_item_records)

            if records_len != 0:
                check_each_status = str()
                defect_count = 0
                for x in range(records_len):
                    if check_each_item_records[x].is_qulified == False:
                        check_each_status += '1'
                        defect_count += 1
                    else:
                        check_each_status += '0'
                self.defect_counts = defect_count
                self.check_each_status = check_each_status

                print '========================', defect_count, check_each_status

    '''
    将值更新到质量订单的中
    '''
    @api.onchange('defect_counts')
    def update_insp_order(self):
        model_qm_insp_order = self.env['qm.inspection.order']
        # model_qm_insp_order.write({'product_defect_count': defect_count,'product_status_record':'check_each_status'})
        model_qm_insp_order.write(
            {'product_defect_count': self.defect_counts, 'product_status_record': 'check_each_status'})


'''
检验记录模型
 建议不同的定性或定量，定义不同的model  或使用同一model的不同字段
'''
class qm_check_each_item(models.Model):
    _name = "qm.check_each_item"
    check_task_item_id = fields.Many2one('qm.check_task_item', select=True, required=True, ondelete='cascade')
    name = fields.Char(string="检测记录")
    each_item_num = fields.Integer(string='样本编号')
    each_item_result = fields.Char(string='检验结果')
    is_qulified = fields.Boolean(string='合格性')
