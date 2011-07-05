# -*- encoding: utf-8 -*-
##############################################################################
#
#    Avanzosc, OpenERP Professional Services   
#    Copyright (C) 2010-2011 Avanzosc S.L (http://www.avanzosc.com). All Rights Reserved
#    
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from osv import osv
from osv import fields
from tools.translate import _
import netsvc

class mrp_loc_configurator(osv.osv_memory):

    _name = 'mrp.loc.configurator'
    _description = 'Loc Configurator'
    
    def view_init(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        order_obj = self.pool.get('mrp.production')
        sale_obj = self.pool.get('sale.order')
        if context['active_model'] != 'mrp.production':
            for sale in sale_obj.browse(cr, uid, context['active_ids']):
                id = (order_obj.search(cr, uid, [('origin', '=', sale.name)]))
        else:
            id = context['active_ids']
        for order in order_obj.browse(cr, uid, id):
            if order.state == 'done':
                raise osv.except_osv(_('User error'), _('The order is already configured !'))
 
    _columns = {
            'installer_loc_id': fields.many2one('stock.location', 'Installer Location', domain=[('usage', '=', 'internal')], required=True),
            'customer_loc_id': fields.many2one('stock.location', 'Customer Location', domain=[('usage', '=', 'internal')], required=True),
            'installer_id': fields.many2one('res.partner', 'Installer', readonly=True, required=True),
            'technician_id': fields.many2one('res.partner.address', 'Technician', required=True),
            'customer_id': fields.many2one('res.partner', 'Customer', readonly=True, required=True),
            'customer_addr_id': fields.many2one('res.partner.address', 'Customer Address', readonly=True, required=True),
    }
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        order_obj = self.pool.get('mrp.production')
        sale_obj = self.pool.get('sale.order')
        res = {}
        if context['active_model'] == 'mrp.production':
            raise osv.except_osv(_('User error'), _('This wizard cannot be executed from MRP view !'))
        else:
            id = context['active_ids']
        for order in sale_obj.browse(cr, uid, id):
            res = {
                'customer_id': order.partner_id.id,
                'customer_addr_id': order.partner_shipping_id.id,
            }
        return res
    
    def onchange_installer(self, cr, uid, ids, installer_loc_id, context=None):
        res ={}
        installer = self.pool.get('stock.location').browse(cr, uid, installer_loc_id)
        partner_ids = self.pool.get('res.partner').search(cr, uid, [('address', '=', installer.address_id.id)])
        for partner_id in partner_ids:
            res = {
                'installer_id': partner_id,
            }
        return {'value': res}
    
    def set_locations(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        order_obj = self.pool.get('mrp.production')
        sale_obj = self.pool.get('sale.order')
        if context['active_model'] != 'mrp.production':
            for sale in sale_obj.browse(cr, uid, context['active_ids']):
                id = (order_obj.search(cr, uid, [('origin', '=', sale.name)]))
        else:
            id = context['active_ids']
        for order in order_obj.browse(cr, uid, id):
            for conf in self.browse(cr, uid, ids):
                installer = self.pool.get('stock.location').browse(cr, uid, conf.installer_loc_id.id)
                installer_id = self.pool.get('res.partner').search(cr, uid, [('address', '=', installer.address_id.id)])[0]
                order_obj.write(cr, uid, order.id, {'location_src_id': conf.installer_loc_id.id, 'location_dest_id': conf.customer_loc_id.id})
                context.update({
                        'installer_id': installer_id, 
                        'technician_id': conf.technician_id.id, 
                        'customer_id': conf.customer_id.id,
                        'customer_addr_id': conf.customer_addr_id.id})
                wizard = {
                            'type': 'ir.actions.act_window',
                            'res_model': 'mrp.bom.configurator',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'target': 'new',
                            'context':context
                        }
                return wizard
        return {'type': 'ir.actions.act_window_close'}
    
mrp_loc_configurator()

class mrp_lot_configurator_list(osv.osv_memory):

    _name = 'mrp.lot.configurator.list'
    _description = 'Lot Configurator List'
 
    _columns = {
            'name': fields.char('Name', size=64),
            'product_id': fields.many2one('product.product', 'Product'),
            'prodlot_id': fields.many2one('stock.production.lot', 'MAC Address / Serial Nº'),
            'cofig_id': fields.many2one('mrp.bom.configurator', 'Configurator'),
    }
    
mrp_lot_configurator_list()

class mrp_lot_configurator(osv.osv_memory):

    _name = 'mrp.lot.configurator'
    _description = 'Lot Configurator List'
 
    _columns = {
            'fin_prod': fields.many2one('product.product', 'Finished Product', readonly=True),
            'fin_prodlot': fields.many2one('stock.production.lot', 'MAC Address'),
            'installer_id': fields.many2one('res.partner', 'Installer', readonly=True, required=True),
            'technician_id': fields.many2one('res.partner.address', 'Technician', required=True),
            'customer_id': fields.many2one('res.partner', 'Customer', readonly=True, required=True),
            'customer_addr_id': fields.many2one('res.partner.address', 'Customer Address', readonly=True, required=True),
            'config_ids': fields.one2many('mrp.lot.configurator.list', 'cofig_id', 'Configurator'),
    }
    
    def default_get(self, cr, uid, fields, context=None):
        option_obj = self.pool.get('mrp.bom.product.list')
        if context is None:
            context = {}
        order_obj = self.pool.get('mrp.production')
        sale_obj = self.pool.get('sale.order')
        move_obj = self.pool.get('stock.move')
        res = {}
        values = {}
        prods = []
        prods_fin = []
        if context['active_model'] != 'mrp.production':
            for sale in sale_obj.browse(cr, uid, context['active_ids']):
                id = (order_obj.search(cr, uid, [('origin', '=', sale.name)]))
        else:
            id = context['active_ids']
        for order in order_obj.browse(cr, uid, id):
            for move in order.move_lines:
                if move.product_id.track_production:
                    values = {
                        'name': '[' + move.product_id.code + '] ' + move.product_id.name,
                        'product_id': move.product_id.id
                    }
                    prods.append(values)
            for move in order.move_created_ids:
                prods_fin.append(move)    
            res = {
                'fin_prod': prods_fin[0].product_id.id,
                'installer_id': context.get('installer_id'),
                'technician_id': context.get('technician_id'),
                'customer_id': context.get('customer_id'),
                'customer_addr_id': context.get('customer_addr_id'),
                'config_ids': prods,
            }
        return res
    
    def set_lots(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        if context is None:
            context = {}
        order_obj = self.pool.get('mrp.production')
        prodlot_obj = self.pool.get('stock.production.lot')
        sale_obj = self.pool.get('sale.order')
        move_obj = self.pool.get('stock.move')
        config = self.browse(cr, uid, ids)[0]
        if context['active_model'] != 'mrp.production':
            for sale in sale_obj.browse(cr, uid, context['active_ids']):
                id = (order_obj.search(cr, uid, [('origin', '=', sale.name)]))
        else:
            id = context['active_ids']
        if id:
            for order in order_obj.browse(cr, uid, id):
                values = {
                    'installer': config.installer_id.id,
                    'technician': config.technician_id.id,
                    'customer': config.customer_id.id,
                    'cust_address': config.customer_addr_id.id,
                }
                for move in order.move_lines:
                    for list in config.config_ids:
                        if list.product_id.id == move.product_id.id:
                            prodlot_obj.write(cr, uid, list.prodlot_id.id, values)
                            move_obj.write(cr, uid, move.id, {'prodlot_id': list.prodlot_id.id})
                            wf_service.trg_validate(uid, 'stock.production.lot', list.prodlot_id.id, 'button_active', cr)
                for move in order.move_created_ids:
                    prodlot_obj.write(cr, uid, config.fin_prodlot.id, values)
                    move_obj.write(cr, uid, move.id, {'prodlot_id': config.fin_prodlot.id})
                    wf_service.trg_validate(uid, 'stock.production.lot', config.fin_prodlot.id, 'button_active', cr)
            if order_obj.browse(cr, uid, id[0]).state == 'confirmed':
                order_obj.force_production(cr, uid, id)
            wf_service.trg_validate(uid, 'mrp.production', id[0], 'button_produce', cr)
            wf_service.trg_validate(uid, 'mrp.production', id[0], 'button_produce_done', cr)
            context.update({'active_model': 'mrp.production',
                            'active_ids': id,
                            'active_id': id[0]})
            wizard = {
                    'type': 'ir.actions.act_window',
                    'res_model': 'mrp.product.produce',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'context':context
                }
            return wizard
        return {'type': 'ir.actions.act_window_close'}
    
mrp_lot_configurator()

class mrp_bom_product_list(osv.osv_memory):

    _name = 'mrp.bom.product.list'
    _description = 'BOM Configurator Product List'
 
    _columns = {
            'name': fields.char('Name', size=64),
            'product_id': fields.many2one('product.product', 'Product'),
            'checked': fields.boolean('Checked'),
            'cofig_id': fields.many2one('mrp.bom.configurator', 'Configurator'),
    }
    
mrp_bom_product_list()

class mrp_bom_product_list_one(osv.osv_memory):

    _name = 'mrp.bom.product.list.one'
    _description = 'BOM Configurator Product List'
 
    _columns = {
            'name': fields.char('Name', size=64),
            'product_id': fields.many2one('product.product', 'Product'),
            'cofig_one_id': fields.many2one('mrp.bom.configurator', 'Configurator'),
    }
    
mrp_bom_product_list_one()

class mrp_bom_configurator(osv.osv_memory):

    _name = 'mrp.bom.configurator'
    _description = 'BOM Configurator'
 
    _columns = {
            'mrp_production': fields.many2one('mrp.production', 'Production Order', readonly=True, required=True),
            'type': fields.selection([
                ('one','One'),
                ('multiple','Multiple')], 'Select'),
            'product_id': fields.many2one('product.product', 'Replace Product', readonly=True),
            'product_list':fields.one2many('mrp.bom.product.list', 'cofig_id','Product List for multiple selection'),
            'installer_id': fields.many2one('res.partner', 'Installer', readonly=True, required=True),
            'technician_id': fields.many2one('res.partner.address', 'Technician', required=True),
            'customer_id': fields.many2one('res.partner', 'Customer', readonly=True, required=True),
            'customer_addr_id': fields.many2one('res.partner.address', 'Customer Address', readonly=True, required=True),
    }
            
    def default_get(self, cr, uid, fields, context=None):
        option_obj = self.pool.get('mrp.bom.product.list')
        if context is None:
            context = {}
        order_obj = self.pool.get('mrp.production')
        sale_obj = self.pool.get('sale.order')
        res = {}
        items = []
        if context['active_model'] != 'mrp.production':
            for sale in sale_obj.browse(cr, uid, context['active_ids']):
                id = (order_obj.search(cr, uid, [('origin', '=', sale.name)]))
        else:
            id = context['active_ids']
        for order in order_obj.browse(cr, uid, id):
            for line in order.product_lines:
                if line.product_id.alt_product_ids:
                    res = {
                        'product_id': line.product_id.id,
                    }
                    for item in line.product_id.alt_product_ids:
                        values = {
                            'name': '[' + item.code + '] ' + item.name,
                            'product_id':item.id,
                        }
                        items.append(values)
                    res.update({
                        'mrp_production': order.id,
                        'product_list': items,
                        'type': line.product_id.selection_type,
                        'installer_id': context.get('installer_id'),
                        'technician_id': context.get('technician_id'),
                        'customer_id': context.get('customer_id'),
                        'customer_addr_id': context.get('customer_addr_id'),
                    })
                    break
        return res
    
    def next(self, cr, uid, ids, context=None):
        context.update({
                'installer_id': context.get('installer_id'),
                'technician_id': context.get('technician_id'),
                'customer_id': context.get('customer_id'),
                'customer_addr_id': context.get('customer_addr_id'),})
        wizard = {
                    'type': 'ir.actions.act_window',
                    'res_model': 'mrp.lot.configurator',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'context':context
                }
        return wizard 
    
    def product_replacement(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        order = self.pool.get('mrp.production')
        order_line = self.pool.get('mrp.production.product.line')
        items = []
        if context is None:
            context = {}
        for conf in self.browse(cr, uid, ids):
            for alt_prod in conf.product_list:
                if alt_prod.checked:
                    items.append(alt_prod)
            if conf.type == 'one':
                    if len(items) == 1:
                        alt_id = order_line.search(cr, uid, [('product_id', '=', conf.product_id.id), ('production_id', '=', conf.mrp_production.id)])
                        order_line.write(cr, uid, alt_id, {'product_id': items[0].product_id.id})
                    else:
                        raise osv.except_osv(_('User error'), _('Select only one product, please !'))
            else:
                for item in items:
                    alt_id = order_line.search(cr, uid, [('product_id', '=', conf.product_id.id), ('production_id', '=', conf.mrp_production.id)])
                    if alt_id:
                        order_line.write(cr, uid, alt_id, {'product_id': item.product_id.id})
                    else:
                        order_line.create(cr, uid, {'product_id': item.product_id.id,
                                                    'name': item.product_id.name,
                                                    'product_uom': item.product_id.uom_id.id,
                                                    'product_qty': 1,
                                                    'production_id': conf.mrp_production.id,
                                                    })

            if order.test_replacement(cr, uid, [conf.mrp_production.id], context):
                context.update({
                'installer_id': context.get('installer_id'),
                'technician_id': context.get('technician_id'),
                'customer_id': context.get('customer_id'),
                'customer_addr_id': context.get('customer_addr_id'),})
                wizard = {
                    'type': 'ir.actions.act_window',
                    'res_model': 'mrp.bom.configurator',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'context':context
                }
                return wizard
            else:
                wf_service.trg_validate(uid, 'mrp.production', conf.mrp_production.id, 'button_configure', cr)
                context.update({
                'installer_id': context.get('installer_id'),
                'technician_id': context.get('technician_id'),
                'customer_id': context.get('customer_id'),
                'customer_addr_id': context.get('customer_addr_id')})
                wizard = {
                    'type': 'ir.actions.act_window',
                    'res_model': 'mrp.lot.configurator',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'context':context
                }
                return wizard
        return {'type': 'ir.actions.act_window_close'}
    
mrp_bom_configurator()