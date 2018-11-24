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
<%
    count= numero_filas
%>
<div>


  <div class="line">

    <table  style="border-spacing: 0px; WIDTH: 200mm;margin-top: 0px; margin-bottom: 0px" width="100%">
            <tr>
                <td style="text-align:left; font-size:14px;font-family: arial; border-left: 1px solid black;border-right: 1px solid black; border-spacing: 0px; margin-top: 0px; margin-bottom: 0px;HEIGHT: 172.3mm" colspan="3" valign="top" width="45%" >

                <table width="100%" cellpadding="0" cellspacing="0" border-vertical="1" style="border-collapse: collapse;border-spacing: 0px; margin-top: 0px; margin-bottom: 0px">
                    %for line in order.invoice_line:
                        <%
                            total_line_2= line.price_unit*line.quantity
                        %>
                        <tr>
                        <td width="15%" style="text-align:left;border-right: 1px solid black;border-spacing: 5px;border-bottom: 0px solid; HEIGHT: 4.5mm" valign="top">&nbsp;${line.product_id.default_code}</td>
                        <td width="55%" style="text-align:left;border-right: 1px solid black;"valign="top">&nbsp;${line.name}</td>
                        <td width="10%" style="text-align:center;border-right: 1px solid black;"valign="top">&nbsp;${line.quantity}</td>
                        <td width="10%" style="text-align:right;border-right: 1px solid black;"valign="top">&nbsp;${line.price_unit}</td>

                        <td width="20%"style="text-align:right;"valign="top">${formatLang(total_line_2)}</td>
                        </tr>
                    %endfor

                    % for x in range(count):
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


    </table>

    </div>
</div>

%endfor
</body>
</html>
