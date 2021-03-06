<html>
<head>
    <style type="text/css">
        ${css}

.texto_left { font-family: Arial, arial, ARIAL, sans-serif;
         font-size:12px;
         text-align:left}

.texto_leftb { font-family: Arial, arial, ARIAL, sans-serif;
         font-size:12px;
         text-align:left;
         font-weight:bold}

.texto_right { font-family: Arial, arial, ARIAL, sans-serif;
         font-size:12px;
         text-align:right}

.texto { font-family: Arial, arial, ARIAL, sans-serif;}

.list_sale_table {
    border:thin solid #E3E4EA;
    text-align:center;
    border-collapse: collapse;
}
.list_sale_table th {
    background-color: #EEEEEE;
    border: thin solid #000000;
    text-align:center;
    font-size:12px;
    font-weight:bold;
    padding-right:3px;
    padding-left:3px;
}
.list_sale_table td {
    border-top: thin solid #EEEEEE;
    text-align:left;
    font-size:12px;
    padding-right:3px;
    padding-left:3px;
    padding-top:3px;
    padding-bottom:3px;
}
.list_sale_table thead {
    display:table-header-group;
}

td.formatted_note {
    text-align:left;
    border-right:thin solid #EEEEEE;
    border-left:thin solid #EEEEEE;
    border-top:thin solid #EEEEEE;
    padding-left:10px;
    font-size:11px;
}



.no_bloc {
    border-top: thin solid  #ffffff ;
}

.right_table {
    right: 4cm;
    width: 100%;
}

.std_text {
    font-size:12px;
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

<body>
    
    
%for order in objects:  


    <table  width="100%">
    <tr>
            <td class="texto_left" width="15%">Señor(es):</td>
            <td class="texto_right" width="15%" colspan="4">La Paz,&nbsp; ${dia}&nbsp;de&nbsp;${mes}&nbsp;de&nbsp;${ano} </td>
         </tr>   
        <tr>
            <td class="texto_left" width="15%" colspan="3"><b>${order.partner_id.name}</b></td>

            <td class="texto_right" width="22%">Celular:</td>
            <td class="texto_right" width="10%">${order.partner_id.mobile or ''}</td>
         </tr>   
             <tr>
         <td class="texto_left">Cotización N°:</td>
            <td class="texto_left" width="48%">${order.name}</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_right">Oficina: </td>
            <td class="texto_right" width="10%">${order.partner_id.phone or ''}</td>
         </tr> 
           <tr>
            <td class="texto_left">Presente</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left" width="10%">&nbsp;</td>
         </tr> 
         <tr>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left" colspan="3"><b>Ref.:</b>&nbsp;&nbsp;&nbsp;${order.product_type.ref}</td>
         </tr>
         <tr>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left" colspan="2">${order.note or ''}</td>


         </tr>
    </table>
    <table  width="100%">
        
        <tbody>
        <tr>
            <td class="texto_left">${order.product_type.consideracion | safe}</td>
        </tr>
<tr>

            <td><span class="texto_leftb"><br>1.&nbsp;${order.product_type.punto_dos}</span></td>
        </tr>
        <tr>
            <td><span class="texto_left">Poliestireno Expandido: Densidad ${densidad1 or ''} kg/m3<br>${order.product_type.especificaciones}</td>
        </tr>
        <tr>
            <td class="texto_leftb"><br>2.&nbsp;${order.product_type.punto_uno}</td>
        </tr>
        <br>
        <br>
        <br>
        <div>
        <br>
       <table border=0 width="100%">
       	<tr>
       		<td width="60%"> 
	   			<table cellspacing="0" width="80%">
	   				<tr>
	   					<td style="font-weight:bold; font-size:12px; text-align:center; font-family: Arial, arial, ARIAL, sans-serif; border-top: 1px solid black; border-bottom: 1px solid black; border-left: 1px solid black; border-right: 1px solid black; background-color: #D8D8D8" width="20%">DESCRIPCIÓN</td>

	   					<td style="font-weight:bold; font-size:12px; text-align:center; font-family: Arial, arial, ARIAL, sans-serif; border-top: 1px solid black; border-bottom: 1px solid black; border-right: 1px solid black; background-color: #D8D8D8" width="20%">CANTIDAD</td>
            		</tr>
        %for line in order.order_line:
            
            		<tr>
	   					<td style="font-weight:bold; font-size:12px; text-align:center; font-family: Arial, arial, ARIAL, sans-serif; border-bottom: 1px solid black; border-left: 1px solid black; border-right: 1px solid black" width="20%">[${line.product_id.default_code}]${line.product_id.name}</td>

	   					<td style="font-weight:bold; font-size:12px; text-align:center; font-family: Arial, arial, ARIAL, sans-serif; border-bottom: 1px solid black; border-right: 1px solid black" width="20%">${line.product_uom_qty}</td>
            		</tr>    
        
        %endfor
        		</table>
        </div>
        <br>
        		<table>
        			<tr>
            			<td><span class="texto_left">

                           <ul>
                                <li>
                                    Espesor:&nbsp;${espesor or ''}
                            </li><br>

                                ${order.product_type.consideraciones_propuesta | safe}<br>
                                </li>
                            </ul>
                    </span></td>
        			</tr>
        		</table>
        	</td>
        	<td width="40%" align="center">
            <img src="data:image/png;base64,${order.product_type.img_consideracion}"  width="280" height="105" />
        	</td>
        </tr>
        </table>
        <tr>
            <td><span class="texto_leftb"><br>3.&nbsp;PLAZO DE ENTREGA:&nbsp;</span><br><span style="font-size:12px;">${order.product_type.plazo_entrega | safe}</span></td>
            
        </tr>
        <tr>
            <td><span class="texto_leftb"><br>4.&nbsp;COSTO OFERTADO:<br> <br>${currency} ${formatLang(order.amount_total)}&nbsp;(${literal} &nbsp;&nbsp;&nbsp;&nbsp;${centavos} / 100 ${currency})</span></td>
        </tr>    
        <tr>
            <td><span class="texto_left">${order.product_type.firma | safe}</span></td>
        </tr>
        <tr>
        <td>
        <br /><br />
        	<table border=0 width="100%">
        		<tr>
        			<td width="30%">
        			&nbsp;
        			</td>
        			<td align="center" width="40%" style="text-align:center;font-size:12px; font-family: Arial, arial, ARIAL, sans-serif; border-top: 1px solid black;">
        			<span style="font-size:12px;">${user_name}&nbsp;-&nbsp;${mobile}</span>
        			</td>
        			<td width="30%">
        			&nbsp;
        			</td>
        		</tr>
        		<tr>
        		    <td width="30%">
        			&nbsp;
        			</td>
        			<td align="center" width="40%">
        			<span style="font-size:12px;">${puesto}</span>
        			</td>
        			<td width="30%">
        			&nbsp;
        			</td>
        		</tr>
        	</table>
        </td>
        </tr>  
        </tbody>
          %endfor
        <tfoot class="totals">
     
        </tfoot>
    </table>
  
</body>
</html>
