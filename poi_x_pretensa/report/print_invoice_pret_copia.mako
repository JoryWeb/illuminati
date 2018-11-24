<html>
<head>
   
    <style type="text/css">
        ${css}
.list_sale_table {
    border:thin solid #E3E4EA;
    text-align:center;
    border-collapse: collapse;
}

.list_sale_table th {
    background-color: #EEEEEE;
    border: thin solid #000000;
    text-align:center;
    font-size:12;
    font-weight:bold;
    padding-right:3px;
    padding-left:3px;
}
.list_sale_table td {
    border-top: thin solid #EEEEEE;
    text-align:left;
    font-size:12;
    padding-right:3px;
    padding-left:3px;
    padding-top:3px;
    padding-bottom:3px;
}
.list_sale_table thead {
    display:table-header-group;
}
.line{
height=293px;
}

td.formatted_note {
    text-align:left;
    border-right:thin solid #EEEEEE;
    border-left:thin solid #EEEEEE;
    border-top:thin solid #EEEEEE;
    padding-left:14px;
    font-size:11;
}



.no_bloc {
    border-top: thin solid  #ffffff ;
}

.right_table {
    right: 4cm;
    width:"100%";
}

.std_text {
    font-size:12;
}

tfoot.totals tr:first-child td{
    padding-top: 15px;
}


td.amount, th.amount {
    text-align: right;
    white-space: nowrap;
}


.address .recipient .shipping .invoice {
    font-size: 12px;
}


    </style>
</head>

<body style="margin-top: 0px; margin-bottom: 0px">

%for order in objects:
<div>
  <div class="line">
  <table  style="border-spacing: 0px; WIDTH: 200mm; HEIGHT: 200mm">
        <tr>
         <td style="text-align:left; font-size:14px;font-family: arial; border-top-left-radius: 20px;border-top: 1px solid black;border-left: 1px solid black; border-right: 1px solid white; height: 7mm" width="28%">
                <table  height="100%" width="100%" border-vertical="1"  CELLSPACING="0">
                    <tr height="50%">
                        <td style="text-align:left;font-weight:bold;" valign="top" rowspan="4" height="50%" align="left">
                          <br/> &nbsp; &nbsp;&nbsp;&nbsp;<img src="data:image/png;base64,${logo}"  width="140" height="60" />
                        </td>
                        <td height="50%" style="text-align:left;font-size:12px;font-weight:bold;" valign="bottom">
                           &nbsp;
                        </td>
                    </tr>
                    <tr height="50%">
                        <td style="text-align:left;font-weight:bold;" valign="top" height="50%">
                          &nbsp;
                        </td>

                    </tr>
                    <tr height="50%">
                        <td style="text-align:right;font-size:14px;font-weight:bold;" valign="top" height="50%">
                          LTDA.
                        </td>

                    </tr>
                    <tr height="50%">
                        <td style="text-align:left;font-weight:bold;" valign="top" height="50%">
                          &nbsp;
                        </td>
                    </tr>
                </table>
                </td>
                <td style="text-align:left; font-size:14px;font-family: arial; border-top: 1px solid black;border-right: 1px solid black;" width="29%" rowspan="" >

                <table  height="100%" width="100%">
                    <tr>
                        <td style="text-align:left;font-size:32px;font-weight:bold;HEIGHT: 11mm" valign="bottom" rowspan="">
                            &nbsp;FACTURA
                        </td>
                    </tr>
                </table>

                </td>
                <td style="text-align:left; font-size:14px;font-family: arial; border-top-right-radius: 20px; border-top: 1px solid black;border-right: 1px solid black;bold;border-bottom: 1px solid black;" width="43%" valign="top" rowspan="2">
                <table  height="100%" width="100%">
                    <tr>
                        <td style="text-align:center;font-size:16px;HEIGHT: 11mm" valign="bottom">
                            NIT:&nbsp;${nit or 0}
                        </td>
                    </tr>
                    <tr>
                        <td style="text-align:center;font-size:22px;HEIGHT: 8mm" valign="bottom">
                            Factura N°&nbsp; &nbsp;${order.cc_nro or ''}
                        </td>
                    </tr>
                    <tr>
                        <td style="text-align:center;font-size:16px;">
                            Autorización N°&nbsp; &nbsp;${order.cc_aut or ''}
                        </td>
                    </tr>
                    <tr>
                        <td style="text-align:center;font-size:14px;font-weight:bold;">
                            COPIA
                        </td>
                    </tr>
                    <tr>
                    </tr>
                    <tr>
                        %if order.cc_dos.multi_activity :
                            <td style="text-align:center;font-size:9px">
                                <div style="height: 40px; overflow:hidden;">
				${order.cc_dos.activity_id.name or ''}
                                </div>
                            </td>
                        %else:
                            <td style="text-align:center;font-size:9px;">
                                <div style="height: 53px; overflow:hidden;">
                                    ${order.cc_dos.company_id.actividad or ''}
                                </div>
                            </td>
                        %endif
                    </tr>
                </table>
                </td>
            </tr>
            <tr>
                <td style="text-align:center; font-size:14px;font-family: arial; border-left: 1px solid black;border-right: 1px solid black;border-bottom: 1px solid black;" colspan="2" >
                    <div style="text-align:center;">
                    <table width="100%">
                        <tr>
                            <td style="text-align:center;font-size:7px;HEIGHT: 3mm" width="40%">
                            CASA MATRIZ
                            </td>
                            <td style="text-align:center;font-size:7px;HEIGHT: 3mm" width="60%">
                            ${order.cc_dos.warehouse_id.other_info or ''}
                            </td>
                        </tr>
                        <tr>
                            <td style="text-align:center;font-size:7px;" width="40%">
                            ${direccion_compania1 or ''}<br>${direccion_compania2 or ''}
                            </td>
                            <td style="text-align:center;font-size:7px;" width="60%">
                            ${order.cc_dos.warehouse_id.address or ''}
                            </td>
                        </tr>

                        <tr>
                            <td style="text-align:center;font-size:7px;" width="40%">
                            TELEFONO&nbsp;&nbsp;${telefono_compania or ''}
                            </td>
                            <td style="text-align:center;font-size:7px;" width="60%">
                            TELEFONO&nbsp;&nbsp;${order.cc_dos.warehouse_id.phone or ''}
                            </td>
                        </tr>
                        <tr>
                            <td style="text-align:center;font-size:7px;" width="40%">
                            ${ciudad_compania or ''}&nbsp;-&nbsp;${pais_compania or ''}
                            </td>
                            <td style="text-align:center;font-size:7px;" width="60%">
                            ${order.cc_dos.warehouse_id.state_id.name or ''}&nbsp;-&nbsp;${order.cc_dos.shop_id.country_id.name or ''}
                            </td>
                        </tr>
                    </table>
                    </div>
                </td>
            </tr>

            <tr>
                <td style="text-align:left; font-size:14px;font-family: arial; border-left: 1px solid black;border-right: 1px solid black; border-bottom: 1px solid black;HEIGHT: 7mm" colspan="3"  width="45%"  >

		        <table width="100%" >
		            <tr>
		                <td width="10%" style="" colspan="2">${order.user_id.city or ''}, ${dia}&nbsp;de&nbsp;${mes}&nbsp;de&nbsp;${ano}</td>

		                <td width="20%">&nbsp;</td>
		                <td width="15%" style="font-weight:bold;">&nbsp;</td>
		                <td width="15%">&nbsp;</td>
		            </tr>
		            <tr>
		                <td width="10%" style="font-weight:bold;">Señor(es):</td>
		                <td width="40%" colspan="2">${order.razon or ''}</td>

		                <td width="15%" style="font-weight:bold;">NIT/C.I.:</td>
		                <td width="15%">${order.nit or ''}</td>
		            </tr>
		            <tr>
		                <td width="10%" style="font-weight:bold;">Dirección:</td>
		                <td width="40%" colspan="2">${order.partner_id.street or ''}</td>

		                <td width="15%" style="font-weight:bold;">Pedido de Venta:</td>
		                <td width="15%">${order.origin or ''}</td>
		            </tr>
		            <tr>
		                <td width="10%">&nbsp;</td>
		                <td width="40%">&nbsp;</td>
		                <td width="20%">&nbsp;</td>
		                <td width="15%" style="font-weight:bold;">Orden de Entrega:</td>
		                <td width="15%">${order.picking_id.name or ''}</td>
		            </tr>
		        </table>
                </td>
              </td>
            </tr>
            <tr>
                <td style="text-align:left; font-size:14px;font-family: arial; border-left: 1px solid black;border-right: 1px solid black; HEIGHT: 140mm" colspan="3"  width="45%" valign="top" >

                <table width="100%" cellpadding="0" cellspacing="0" border-vertical="1"  style="border-collapse: collapse" >
                    <tr>
                        <td width="15%" style="background-color: #D8D8D8;border-right: 1px solid black;border-bottom: 1px solid black;font-weight:bold;HEIGHT: 1mm">Código</td>
                        <td width="55%" style="background-color: #D8D8D8;border-right: 1px solid black;border-bottom: 1px solid black;font-weight:bold;">Descripción</td>
                        <td width="10%" style="text-align:center;background-color: #D8D8D8;border-right: 1px solid black;border-bottom: 1px solid black;font-weight:bold;">Cantidad</td>
                        <td width="5%" style="text-align:center;background-color: #D8D8D8;border-right: 1px solid black;border-bottom: 1px solid black;font-weight:bold;">Precio</td>

                        <td width="20%" style="text-align:center;background-color: #D8D8D8;border-bottom: 1px solid black;font-weight:bold;">Total</td>
                    </tr>

                    </tr>
                    %for line in order.invoice_line_ids:
                        <tr>
                            <td width="5%" style="text-align:left;border-right: 1px solid black;border-spacing: 5px; HEIGHT: 4.5mm">&nbsp;${line.product_id.default_code}</td>
                            <td width="55%" style="text-align:left;border-right: 1px solid black;">&nbsp;${line.name}</td>
                            <td width="10%" style="text-align:center;border-right: 1px solid black;">&nbsp;${line.quantity}</td>
                            <td width="10%" style="text-align:right;border-right: 1px solid black;">&nbsp;${line.price_unit}</td>
                            <td width="20%"style="text-align:right;">${formatLang(line.price_unit*line.quantity)}</td>
                        </tr>
                    %endfor
                    % for x in range(numero_filas-4):
                    <tr>
                        <td width="15%" style="text-align:left;border-right: 1px solid black; HEIGHT: 4.5mm">&nbsp;</td>
                        <td width="45%" style="border-right: 1px solid black">&nbsp;</td>
                        <td width="5%" style="border-right: 1px solid black">&nbsp;</td>
                        <td width="5%" style="border-right: 1px solid black">&nbsp;</td>
                        <td width="20%">&nbsp;</td>
                    </tr>
                    % endfor

                </table>

                </td>
             </tr>
            <tr>
                <td style="text-align:left; font-size:14px;  border-bottom-left-radius: 20px; border-bottom-right-radius: 20px;border-bottom: 1px solid black;border-top: 1px solid black;border-right: 1px solid black;border-left: 1px solid black;" width="70%" colspan="3">

                <table  width="100%" style="border-collapse: collapse">
                    <tr>
                        <td width="33%">
                        &nbsp;
                        </td>

                        <td colspan="4" style="border-right: 1px solid black;">
                        &nbsp;
                        </td>
                        <td width="9.9%">
                        Total:
                        </td>
                        <td style="text-align:right;" width="10%">
                        ${total_line_3 or 0}
                        </td>
                    </tr>
                    <tr>
                        <td style="border-bottom: 1px solid black" width="33%">
                        &nbsp;
                        </td>

                        <td colspan="4" style="border-right: 1px solid black;border-bottom: 1px solid black">
                        &nbsp;
                        </td>
                        <td  width="9.9%">
                        Descuento Bs:
                        </td>
                        <td style="text-align:right;" width="10%">
                        ${discount_bs or 0}
                        </td>
                    </tr>
                    <tr>
                        <td style="border-right: 1px solid black;border-bottom: 1px solid black" width="33%">
                        Recibí Conforme:
                        </td>

                        <td colspan="4" style="border-right: 1px solid black;border-bottom: 1px solid black">
                        Copia Sin Derecho A Credito Fiscal
                        </td>
                        <td style="border-bottom: 1px solid black" width="9.9%">
                        Total c/Desc.:
                        </td>
                        <td style="border-bottom: 1px solid black; text-align:right;" width="10%">
                        ${amount_total or 0}
                        </td>
                    </tr>
                    <tr>
                        <td style="border-right: 1px solid black; border-bottom: 1px solid black">
                        Firma:
                        </td>

                        <td colspan="4" style="border-right: 1px solid black;">
                        Son Bolivianos:
                        </td>

                        <td colspan="2" rowspan="4" style="text-align:center;">
                        <img src="data:image/png;base64,${order.qr_img}"  width="80px" height="80px" />
                        </td>

                    </tr>
                    <tr>
                        <td style="border-right: 1px solid black; border-bottom: 1px solid black">
                        Fecha (d/m/a):&nbsp;
                        </td>
                        <td colspan="4" rowspan="2" style="text-align:center;border-right: 1px solid black;border-bottom: 1px solid black;">
                        ${literal}&nbsp;&nbsp;&nbsp;&nbsp;${centavos}/100 Bolivianos
                        </td>
                    </tr>

                    <tr>
                        <td style="border-bottom: 1px solid black">
                        Codigo de control:&nbsp;&nbsp;${order.cc_cod or ''}
                        </td>
                    </tr>
                    <tr>
                        <td style="border-bottom: 1px solid black">
                        Feche limite de emision:&nbsp;&nbsp;${order.cc_dos.fecha_fin or ''}
                        </td>
                        <td colspan="4" style="border-right: 1px solid black;border-bottom: 1px solid black">
                        &nbsp;
                        </td>
                    </tr>
                    <tr>
                        <td colspan="7" style="text-align:center;font-weight:bold;background-color: #D8D8D8;border-bottom: 1px solid black">
                        El único documento que certifica el pago de la presente factura es nuestro recibo oficial de caja.
                        </td>
                    </tr>
                    <tr>
                        <td colspan="7" style="text-align:center;border-bottom: 1px solid black">
                        Esta Factura contribuye al desarrollo del país, el uso ilícito de esta será sancionado de acuerdo a Ley.
                        </td>
                    </tr>
                    <tr>
                        <td colspan="7" style="text-align:center;">
                        ${leyenda or 'S/L'}
                        </td>
                    </tr>
                </table>
          </td>
       </tr>
    </table>

  </div>
</div>

%endfor
</body>
</html>
