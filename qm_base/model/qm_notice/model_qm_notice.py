# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import ValidationError

class qm_notice(models.Model):
    _name = 'qm.notice'

    name = fields.Char('质量通知')
    notice_type = fields.Selection([('customer_complaint','客户投诉'),('complaint_partner','投诉供应商'),('inner_problem_report','内部问题报告'),('specific_qm_notice','用户特定的质量通知')],'通知类型',required=True)
    partner = fields.Many2one('res.users','合作伙伴')
    product_id = fields.Many2one('product.template','产品')
    material_code = fields.Char('物料编码')
    lot_num = fields.Char('批次号')
    test_lot = fields.Char('检验批')
    origin = fields.Char('源单据')
    original = fields.Selection([('quality_committee','质量委员会'),('direction_review','方向评审'),('inner_complain','内部客户投诉'),('outer_complain','外部客户投诉'),('inner_review','内部审核'),('outer_review','外部审核'),('process_execute','过程执行')],'起源')
    person_in_charge = fields.Many2one('res.users','责任人')
    zd_analysiser = fields.Many2one('res.users','指定分析人')
    manager = fields.Many2one('res.users','管理者')
    fill_in_person = fields.Many2one('res.users','填写人')
    send_date = fields.Datetime('发送日期')
    priority = fields.Selection([('urgency_0','不紧急'),('urgency_1','一般'),('urgency_2','紧急'),('urgency_3','非常紧急')],'优先级')
    deal_start_time = fields.Datetime('最晚处理开始时间')
    deal_end_time = fields.Datetime('最晚处理结束时间')
    problem_desc = fields.Text('问题描述')
    defect_analysis_ids = fields.One2many('qm.defect.analysis','notice_id','缺陷分析')
    action_at_once = fields.Char('立即行动')
    analysiser = fields.Boolean('分析人确认')
    analysis_date = fields.Datetime('分析日期')

    related_process_ids = fields.One2many('qm.related.process','notice_id','相关过程')
    action_ids = fields.One2many('qm.actions','notice_id','行动')
    plan_review = fields.Text('计划评审说明')
    action_plan_person = fields.Boolean('行动计划人确认')
    action_plan_date = fields.Datetime('行动计划日期')
    effect_review = fields.Text('实效评审说明')
    assess_person = fields.Boolean('评估人确认')
    assess_date = fields.Datetime('评估日期')

    state = fields.Selection([('draft_notice','草稿'),('analysis_notice','分析'),('wait_notice','等待审批'),('playing_notice','进行中'),('done_notice','完成'),('notice_cancel','取消')],'状态')#,('notice_cancel','取消')

    _defaults = {'name': lambda self, cr, uid, context={}: self.pool.get('ir.sequence').next_by_code(cr, uid, 'qm.notice'),
                 'send_date':fields.datetime.today(),
                 'state': lambda *a: 'draft_notice',
                 'person_in_charge':lambda self,cr,uid,context={}:self.pool.get('res.users').browse(cr,uid,uid,context=context).id,
                 'zd_analysiser':lambda self,cr,uid,context={}:self.pool.get('res.users').browse(cr,uid,uid,context=context).id,
                 'manager':lambda self,cr,uid,context={}:self.pool.get('res.users').browse(cr,uid,uid,context=context).id,
                 'fill_in_person':lambda self,cr,uid,context={}:self.pool.get('res.users').browse(cr,uid,uid,context=context).id
            }

    @api.model
    def default_get(self, fields):
        rec = super(qm_notice, self).default_get(fields)
        context = dict(self._context or {})

        if context.has_key('active_id'):
            usage_decision_id = context['active_id']
            usage_order = self.env['qm.usage.decision'].browse(usage_decision_id)

            rec['origin'] = usage_order.origin
            rec['product_id'] = usage_order.product_id.id
            rec['test_lot'] = usage_order.test_lot
            rec['lot_num'] = usage_order.lot_num
            rec['partner'] = usage_order.partner.id

            defect_order_ids = []
            defects = context['defect_struct_ids']
            for defect in defects:
                defect_order_id = defect[1]
                defect_order = self.env['qm.defect.struct'].browse(defect_order_id)
                if defect_order.notice_send and defect_order.defect_order_ids>0:
                    defece_analysis = [0,False,{
                        'test_lot':defect_order.test_lot,
                        'option':defect_order.option.id,
                        'test_feature':defect_order.test_feature.id,
                        'defect_type':defect_order.defect_type.id,
                        'defect_count':defect_order.defect_count,
                        'defect_position':defect_order.defect_position,
                        'defect_leval':defect_order.defect_leval.id,
                        'qm_insp_order_id':defect_order.qm_insp_order_id.id
                    }]
                    defect_order_ids.append(defece_analysis)
            rec['defect_analysis_ids'] = defect_order_ids
        return rec

    #分析人确认
    @api.multi
    @api.onchange('analysiser')
    def onchange_analysiser(self):
        if self.analysiser:
            self.analysis_date = fields.datetime.today()

    #行动计划人确认
    @api.multi
    @api.onchange('action_plan_person')
    def onchange_action_plan_person(self):
        if self.state == 'draft_notice':
            return
        action_ids = self.action_ids
        if self.action_plan_person:
            self.action_plan_date = fields.datetime.today()
            for action in action_ids:
                if action.state == 'draft_action':
                    self.pool['qm.actions'].write(self._cr,self._uid,action.id,{'state':'plan_to_action'},self._context)
        else:
            self.action_plan_person = True
            raise ValidationError('行动计划人确认后，不能再次确认')

    #评估人确认
    @api.multi
    @api.onchange('assess_person')
    def onchange_assess_person(self):
        if self.state == 'draft_notice':
            return
        action_ids = self.action_ids
        if self.assess_person:
            flag = True
            for action in action_ids:
                if action.state != 'done_action':
                    flag = False
                    self.assess_person = False
                    raise ValidationError('确认前所有行动必须是完成状态')
            if flag:
                self.assess_date = fields.datetime.today()
                for action in self.action_ids:
                    self.pool['qm.actions'].write(self._cr,self._uid,action.id,{'state':'success'},self._context)
        else:
            self.assess_person = True
            raise ValidationError('评估人确认后不能再次确认')

    def action_review(self):
        if self.analysiser:
            self.write({'state':'wait_notice'})
        else:
            raise ValidationError('需要分析人确认后才能发送去评审')
        return True

#缺陷记录
class qm_defect_analysis(models.Model):
    _name = "qm.defect.analysis"

    notice_id = fields.Many2one("qm.notice")
    test_lot = fields.Char("检验批")
    option= fields.Many2one("qm.work_procedure","操作工序")
    test_feature = fields.Many2one('qm.insp_project_def',"缺陷特性")
    defect_type = fields.Many2one('qm.defects',"缺陷类型")
    defect_count = fields.Integer("缺陷数量")
    defect_position = fields.Selection([('posion_A','上部分'),('posion_B','中部'),('posion_C','下部')],"缺陷位置")
    defect_leval = fields.Many2one('defects.level',"缺陷等级")
    defect_reason = fields.Char('缺陷原因')
    defect_analysis = fields.Text('分析')
    qm_insp_order_id = fields.Many2one("qm.inspection.order","质检订单")

#相关过程
class qm_related_process(models.Model):
    _name = 'qm.related.process'

    notice_id = fields.Many2one('qm.notice')
    file_name = fields.Char('文件名')

#行动
class qm_actions(models.Model):
    _name = 'qm.actions'

    notice_id = fields.Many2one('qm.notice','质量通知')
    name = fields.Char('行动编号')
    task = fields.Char('任务')
    desc = fields.Text('描述')
    related_defect = fields.Char('相关缺陷')
    response_type = fields.Selection([('action_now','立即行动'),('right_measure','纠正措施'),('defence_measure','防御措施'),('improve_changce','改进机会')],'相应类型')
    person_in_charge = fields.Many2one('res.users','责任人')
    dead_date = fields.Datetime('截止日期')
    date = fields.Datetime('日期')
    sell_team = fields.Char('销售团队')
    qm_system = fields.Char('质量体系')
    request = fields.Char('诉求')
    state = fields.Selection([('draft_action','草稿'),('plan_to_action','准备进行'),('playing_action','进行中'),('done_action','完成'),('success','成功'),('action_cancel','取消')],'状态')

    _defaults = { 'name': lambda self, cr, uid, context={}: self.pool.get('ir.sequence').get(cr, uid, 'qm.actions'),
        'state': 'draft_action',
        'person_in_charge':lambda self,cr,uid,context={}:self.pool.get('res.users').browse(cr,uid,uid,context=context).id,
        'date':fields.datetime.today()
    }