## -*- coding: utf-8 -*-
<html>
<head>
    <style type="text/css">
            ${css}
.texto_left { font-family: Arial, arial, ARIAL, sans-serif;
         font-size:12px;
         text-align:left}

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
    <table  width="100%" >
        <tr>
            <td class="texto_left"width="15%">Señor(es):</td>
            <td class="texto_right" width="15%" colspan="3">La Paz,&nbsp; ${dia}&nbsp;de&nbsp;${mes}&nbsp;de&nbsp;${ano} </td>
        </tr>
        <tr>
            <td class="texto_left" width="15%" colspan="2"><b>${order.partner_id.name}</b></td>
            <td class="texto_left" width="15%">&nbsp;</td>
            <td class="texto_left" width="10%">&nbsp;</td>
        </tr>
            <td class="texto_left" >Cotización:</td>
            <td class="texto_left">${order.name}</td>
            <td class="texto_left">&nbsp; </td>
            <td class="texto_left" width="10%">&nbsp;</td>
        </tr>
        <tr>
            <td class="texto_left">Presente</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left" width="10%">&nbsp;</td>
        </tr>
    </table>

    <table  width="100%">
        <tr>
            <td class="texto_left">
                ${order.product_type.consideracion | safe}
            </td>
        </tr>
        <br>
        <br>
        <br>
        <div>
        <br>
       <table border=0 width="100%">
       	<tr>
       		<td width="60%">
	   			<table cellspacing="0" width="100%">
	   				<tr>
	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; border-top: 1px solid black; border-bottom: 1px solid black; border-left: 1px solid black; border-right: 1px solid black; background-color: #D8D8D8" width="30%">Producto</td>
	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; border-top: 1px solid black; border-bottom: 1px solid black; border-right: 1px solid black; background-color: #D8D8D8" width="50%">Descripción</td>
	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; border-top: 1px solid black; border-bottom: 1px solid black; border-right: 1px solid black; background-color: #D8D8D8" width="20%">Dimensión</td>
	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; border-top: 1px solid black; border-bottom: 1px solid black; border-right: 1px solid black; background-color: #D8D8D8" width="20%">Cantidad</td>
	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; border-top: 1px solid black; border-bottom: 1px solid black; border-right: 1px solid black; background-color: #D8D8D8" width="20%">Métrica Total</td>

	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; border-top: 1px solid black; border-bottom: 1px solid black; border-right: 1px solid black; background-color: #D8D8D8" width="20%">Precio Unidad</td>
	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; border-top: 1px solid black; border-bottom: 1px solid black; border-right: 1px solid black; background-color: #D8D8D8" width="20%">Total</td>
            		</tr>
        %for line in order.order_line:

            		<tr>
            			<td class="texto" style="font-size:12px; text-align:center;  border-bottom: 1px solid black; border-left: 1px solid black; border-right: 1px solid black" width="30%">${line.product_id.name}</td>
	   					<td class="texto" style="font-size:12px; text-align:center;  border-bottom: 1px solid black; border-right: 1px solid black" width="50%">[${line.product_id.default_code}]${line.product_id.name}</td>
	   					<td class="texto" style="font-size:12px; text-align:center;  border-bottom: 1px solid black; border-right: 1px solid black" width="20%">${line.product_dimension.var_x or 0}</td>
	   					<td class="texto" style="font-size:12px; text-align:center;  border-bottom: 1px solid black; border-right: 1px solid black" width="20%">${line.product_uom_qty or 0}</td>
	   					<td class="texto" style="font-size:12px; text-align:center;  border-bottom: 1px solid black; border-right: 1px solid black" width="20%">${line.total_dimension_display or 0}</td>

            			<td class="texto" style="font-size:12px; text-align:center;  border-bottom: 1px solid black; border-right: 1px solid black" width="20%">${line.price_unit}</td>
                        <td class="texto" style="font-size:12px; text-align:center;  border-bottom: 1px solid black; border-right: 1px solid black" width="20%">${line.price_subtotal}</td>
            		</tr>

        %endfor
        			<tr>
            			<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; " width="20%">&nbsp;</td>
	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; " width="20%">&nbsp;</td>
	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; " width="20%">&nbsp;</td>

	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:left; " width="20%" colspan="3">COLOR:</td>

                        <td class="texto" style="font-size:12px; text-align:left;" width="20%" colspan="2">${color | safe}</td>
            		</tr>


            		<tr>
            			<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; " width="20%">&nbsp;</td>
	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; " width="20%">&nbsp;</td>
	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; " width="20%">&nbsp;</td>

	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:left; " width="20%" colspan="3">BASE IMPONIBLE:</td>

                        <td class="texto" style="font-size:12px; text-align:left; " width="20%" colspan="2">${order.amount_untaxed}&nbsp;Bs.</td>
            		</tr>
            		<tr>
            			<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; " width="20%">&nbsp;</td>
	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; " width="20%">&nbsp;</td>
	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; " width="20%">&nbsp;</td>

	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:left; " width="20%" colspan="3">IMPUESTOS:</td>

                        <td class="texto" style="font-size:12px; text-align:left; " width="20%" colspan="2">${order.amount_tax}&nbsp;Bs.</td>
            		</tr>
            		<tr>
            			<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; " width="20%">&nbsp;</td>
	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; " width="20%">&nbsp;</td>
	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:center; " width="20%">&nbsp;</td>

	   					<td class="texto" style="font-weight:bold; font-size:12px; text-align:left; " width="20%" colspan="3">TOTAL:</td>

                        <td class="texto" style="font-size:12px; text-align:left; " width="20%" colspan="2">${order.amount_total}&nbsp;Bs.</td>
            		</tr>
        		</table>
        </div>
        <br>
        <table>
        			<tr>
            			<td class="texto"><span style="font-size:12px; text-align:left">
                    <p>
                    Forma de Pago:&nbsp;Contado<br>
Validez: 30 días calendario<br>
                    </p>
                    </span></td>
        			</tr>
        			<tr>
            			<td class="texto"><span style="font-size:12px; text-align:left">${order.product_type.especificaciones | safe}</td>
        			</tr>

        			<tr>
            			<td class="texto"><span style="font-size:12px; text-align:left">${order.product_type.firma | safe}</span></td>
        			</tr>
        </table>
        </td>

        </table>


        <tr>
        <td>
        <br><br>
        	<table border=0 width="100%">
        		<tr>
        			<td width="30%">
        			&nbsp;
        			</td>
        			<td align="center" width="40%" style="text-align:center;font-size:12px; font-family: Arial, arial, ARIAL, sans-serif;  border-top: 1px solid black;">
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

    %endfor
        <tfoot class="totals">

        </tfoot>
    </table>

</body>
</html>
