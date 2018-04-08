# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import ValidationError

class qm_defect_records(models.Model):
    _name = "qm.defect.records"

    name = fields.Char("缺陷记录", required=True, select=True, copy=False)

    defect_record_leval = fields.Char("缺陷记录水平")
    insp_order = fields.Many2one('qm.inspection.order','检验单')
    product_id = fields.Many2one("product.template","产品")
    test_lot = fields.Char("检验批")
    lot_num = fields.Char("批次")
    origin = fields.Char("源单据")
    partner= fields.Many2one('res.users','合作伙伴')
    defect_desc = fields.Text("缺陷概述")
    fectory = fields.Many2one(related='product_id.factory_id', string='工厂')#源于任务列表
    test_process = fields.Many2one("qm.work_procedure","检验工序")#源于任务列表
    test_project = fields.Many2one("qm.insp_project_def","检验项目")#源于任务列表
    product_owner = fields.Many2one("res.users","产品负责人")
    test_owner = fields.Many2one("res.users","检验责任人")
    defect_record_type = fields.Selection([('product_num','按产品序列号记录'),('defect','按缺陷记录')],"缺陷记录方式")

    tigger_work_flow = fields.Char("触发工作流")
    record_persion = fields.Many2one("res.users","记录人")
    record_date = fields.Datetime("记录日期")
    qm_notice_type = fields.Selection([('customer_complaint','客户投诉'),('complaint_partner','投诉供应商'),('inner_problem_report','内部问题报告'),('specific_qm_notice','用户特定的质量通知')],"质量通知类型",required=True)

    defect_record_ids1 = fields.One2many("qm.defect.record","defect_records_id","缺陷记录")#按产品记录
    defect_record_ids2 = fields.One2many("qm.defect.record","defect_records_id","缺陷记录")#按缺陷
    #heightest_defect_leval = fields.Many2one('defects.level','缺陷等级')#为了上一级目录呈现

    _defaults={'record_persion':lambda self,cr,uid,context:self.pool.get('res.users').browse(cr,uid,uid,context=context).id,
               'record_date':fields.datetime.today(),
               'name': lambda self, cr, uid, context={}: self.pool.get('ir.sequence').get(cr, uid, 'qm.defect.records')}

    def write(self,cr,uid,ids,vals,context=None):
        if not context:
            return super(qm_defect_records,self).write(cr,uid,ids,vals,context=context)
        record_id = context['record_id']
        test_feature = context['test_feature']
        result = super(qm_defect_records,self).write(cr,uid,ids,vals,context=context)
        record = self.browse(cr,uid,ids[0],context=context)
        dic=[]
        if record.defect_record_type == 'product_num':
            for item in record.defect_record_ids2:
                if item.defect_leval.leval in dic:
                    continue
                elif item.defect_leval.leval:
                    dic.append(item.defect_leval.leval)
        elif record.defect_record_type == 'defect':
           for item in record.defect_record_ids1:
                if item.defect_leval.leval in dic:
                    continue
                elif item.defect_leval.leval:
                    dic.append(item.defect_leval.leval)
        dic.sort()
        if dic:
            leval = dic[0]
            defect_leval_ids = self.pool.get('defects.level').search(cr,uid,[('leval','=',leval)],context=context)
            if defect_leval_ids:
                defect_leval = self.pool.get('defects.level').browse(cr,uid,defect_leval_ids[0],context=context)
                #super(qm_defect_records,self).write(cr,uid,ids,{'heightest_defect_leval':defect_leval.id})
                if test_feature == 'quality':
                    self.pool.get('qm.insp.task.quality').write(cr,uid,record_id,{'defect_level':defect_leval.id})
                elif test_feature == 'quantify':
                    self.pool.get('qm.insp.task.quantify').write(cr,uid,record_id,{'defect_level':defect_leval.id})
        return result

    @api.multi
    def send_defect_notice(self):
        context = dict(self._context or {})
        defect_records_id = context['record_id']
        defect_orders = self.browse(defect_records_id)
        if not defect_orders.qm_notice_type:
            raise ValueError('请选择通知类型')
        vals = {}
        vals['origin'] = defect_orders.origin
        vals['product_id'] = defect_orders.product_id.id
        vals['test_lot'] = defect_orders.test_lot
        vals['lot_num'] = defect_orders.lot_num
        vals['partner'] = defect_orders.partner.id
        vals['notice_type'] = defect_orders.qm_notice_type
        if context.has_key('defect_record_type'):
            defect_analysis_ids = []
            order_ids = []
            defect_record_type = context['defect_record_type']
            if defect_record_type == 'product_num':
                order_ids = defect_orders.defect_record_ids1
            else:
                order_ids = defect_orders.defect_record_ids2
            for defect_order in order_ids:
                if defect_order.notice_state:
                    defect_analysis = [0,False,{
                        'test_lot':defect_order.test_lot,
                        'option':defect_order.test_process.id,
                        'test_feature':defect_order.test_project.id,
                        'defect_type':defect_order.defect_type.id,
                        'defect_count':defect_order.defect_count,
                        'defect_position':defect_order.defect_position,
                        'defect_leval':defect_order.defect_leval.id,
                        'qm_insp_order_id':defect_order.insp_order.id
                    }]
                    defect_analysis_ids.append(defect_analysis)
            if len(defect_analysis_ids)==0:
                raise ValidationError('没有缺陷记录，不能生成不合格评审通知')
            vals['defect_analysis_ids']=defect_analysis_ids
        self.env['qm.notice'].create(vals)

class qm_defect_record(models.Model):
    _name = "qm.defect.record"

    defect_records_id = fields.Many2one("qm.defect.records")
    defect_product_num = fields.Char("缺陷产品序列号")
    defect_type = fields.Many2one('qm.defects',"缺陷类型")
    defect_count = fields.Integer("缺陷数量")
    defect_position = fields.Selection([('posion_A','上部分'),('posion_B','中部'),('posion_C','下部')],"缺陷位置")
    defect_leval = fields.Many2one('defects.level',"缺陷等级")
    unqualified_review_application = fields.Boolean("不合格评审申请")

    #需要treeview显示的字段
    defect_record_leval = fields.Char(string="缺陷记录水平",related="defect_records_id.defect_record_leval")
    test_project = fields.Many2one(related="defect_records_id.test_project",string="检验项目", store=True)
    product_id = fields.Many2one(string="产品",related="defect_records_id.product_id")
    lot_num = fields.Char(string="批次",related="defect_records_id.lot_num")
    test_lot = fields.Char(string="检验批",related="defect_records_id.test_lot")
    origin = fields.Char(string="源单据",related="defect_records_id.origin")
    fectory = fields.Many2one(string="工厂",related="defect_records_id.fectory")
    test_process = fields.Many2one(related="defect_records_id.test_process",string="检验工序", store=True)
    insp_order = fields.Many2one(related="defect_records_id.insp_order",string='检验单', store=True)
    #用来记录和判断是否已经发送不合格评申请
    notice_state = fields.Boolean('消息发送状态')
    #用来记录和判断使用决策里是否已发送该缺陷记录
    notice_usage_state = fields.Boolean('使用决策消息发送状态')

    _defaults = {'unqualified_review_application':False,
                 'notice_state':False,
                 'notice_usage_state':False
         }


    @api.model
    @api.onchange('unqualified_review_application')
    def onchange_unqualified_app(self):
        if self.unqualified_review_application:
            self.notice_state = True
            self.write({'notice_state':True})
        else:
            self.notice_state = False
            self.write({'notice_state':False})