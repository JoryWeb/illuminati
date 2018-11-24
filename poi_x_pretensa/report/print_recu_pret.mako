<html>
<head>

    <style type="text/css">
            ${css}
        .list_sale_table {
            border: thin solid #E3E4EA;
            text-align: center;
            border-collapse: collapse;
        }

        .list_sale_table th {
            background-color: #EEEEEE;
            border: thin solid #000000;
            text-align: center;
            font-size: 12px;
            font-weight: bold;
            padding-right: 3px;
            padding-left: 3px;
        }

        .list_sale_table td {
            border-top: thin solid #EEEEEE;
            text-align: left;
            font-size: 12px;
            padding-right: 3px;
            padding-left: 3px;
            padding-top: 3px;
            padding-bottom: 3px;
        }

        .list_sale_table thead {
            display: table-header-group;
        }

        .line {
            height:280px;
        }

        td.formatted_note {
            text-align: left;
            border-right: thin solid #EEEEEE;
            border-left: thin solid #EEEEEE;
            border-top: thin solid #EEEEEE;
            padding-left: 14px;
            font-size: 11px;
        }

        .no_bloc {
            border-top: thin solid #ffffff;
        }

        .right_table {
            right: 4cm;
            width: 100%;
        }

        .std_text {
            font-size: 12px;
        }

        tfoot.totals tr:first-child td {
            padding-top: 15px;
        }

        td.amount, th.amount {
            text-align: right;
            white-space: nowrap;
        }

        .address .recipient .shipping .invoice {
            font-size: 12px;
        }

        .page-break {
            page-break-after: auto;
        }

    </style>
</head>

<body>
    %for order in objects:
        <div class="page-break">
            <div class="line">
                <table style="border-spacing: 0px; WIDTH: 200mm; HEIGHT: 200mm">
                    <tr>
                        <td style="text-align:left; font-size:14px;font-family: arial;  border-top: 1px solid black;border-left: 1px solid black; border-right: 1px solid black;border-bottom: 1px solid black; HEIGHT: 7mm"
                            width="100%" colspan="3">
                            <table height="100%" width="100%" border-vertical="1" CELLSPACING="0">
                                <tr height="50%">
                                    <td style="text-align:left;font-weight:bold;" valign="top" rowspan="2" height="50%"
                                        align="left">
                                        <br/> &nbsp; &nbsp;&nbsp;&nbsp;<img src="data:image/png;base64,${logo}"
                                                                            width="140" height="60"/>
                                    </td>
                                    <td style="text-align:center;font-size:22px;HEIGHT: 11mm" valign="bottom">
                                        HOJA DE PRODUCTOS RECUPERADOS
                                    </td>
                                    <td style="text-align:center;font-size:22px;HEIGHT: 11mm" valign="bottom">
                                        &nbsp;
                                    </td>

                                </tr>
                                <tr height="50%">

                                    <td style="text-align:center;font-size:22px;HEIGHT: 11mm" valign="bottom">
                                        ALMACEN
                                    </td>
                                    <td style="text-align:center;font-size:12px;HEIGHT: 11mm" valign="bottom">
                                        HR-02<BR>Version: 2017
                                    </td>

                                </tr>

                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="text-align:left; font-size:14px;font-family: arial;  border-top: 1px solid black;border-left: 1px solid black; border-right: 1px solid black;border-bottom: 1px solid black; HEIGHT: 6mm"
                            width="100%" colspan="2">
                            <table width="100%" border-vertical="1" CELLSPACING="0">
                                <tr>
                                    <td style="text-align:left;font-size:14px;" valign="top" align="left"
                                        width="30%">
                                        RESPONSABLE DE ENTREGA:
                                    </td>

                                    <td style="text-align:left;font-weight:bold;" valign="top" align="left"
                                        width="30%">
                                        <br/> &nbsp; &nbsp;&nbsp;&nbsp;
                                    </td>
                                    <td style="text-align:left;font-weight:bold;" valign="top" align="left"
                                        width="30%">
                                        DIA&nbsp;FECHA DE ENTREGA &nbsp; ${fecha_salida or ''}
                                    </td>
                                </tr>
                                <tr>
                                    <td style="text-align:left;font-size:14px;" valign="top" align="left"
                                        width="30%">
                                        RESPONSABLE DE RECUPERADO:
                                    </td>

                                    <td style="text-align:left;font-weight:bold;" valign="top" align="left"
                                        width="30%">
                                        <br/> &nbsp; &nbsp;&nbsp;&nbsp;
                                    </td>
                                    <td style="text-align:left;font-weight:bold;" valign="top" align="left"
                                        width="30%">
                                        DIA&nbsp;FECHA DE RECUPERADO &nbsp;${fecha_entrada or ''}
                                    </td>

                                </tr>
                                <tr>
                                    <td style="text-align:left;font-weight:bold;font-size:15px;" valign="top" align="left">
                                        PRODUCTO RECUPERADO:
                                    </td>
                                </tr>
                                <tr>
                                    <td style="font-weight:bold;font-size:15px;border-top: 1px solid black;"
                                        valign="top" align="center" colspan="3">
                                        RECUPERADO
                                    </td>
                                </tr>

                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="text-align:left; font-size:14px;font-family: arial; border-left: 1px solid black;border-right: 1px solid black; HEIGHT: 160mm"
                            colspan="3" width="45%" valign="top">
                            <table width="100%" cellpadding="0" cellspacing="0" border-vertical="1"
                                   style="border-collapse: collapse">
                                <tr>
                                    <td width="1%"
                                        style="background-color: #D8D8D8;text-align: center; border-right: 1px solid black;border-bottom: 1px solid black;font-weight:bold;HEIGHT: 4.5mm"
                                        rowspan="2">No
                                    </td>
                                    <td width="5%"
                                        style="background-color: #D8D8D8;text-align: center;border-right: 1px solid black;border-bottom: 1px solid black;font-weight:bold;HEIGHT: 4.5mm"
                                        rowspan="2">Código
                                    </td>
                                    <td width="5%"
                                        style="background-color: #D8D8D8;border-right: 1px solid black;border-bottom: 1px solid black;font-weight:bold; text-align: center"
                                        colspan="2">Producto Observado
                                    </td>
                                    <td width="25%"
                                        style="background-color: #D8D8D8;border-right: 1px solid black;border-bottom: 1px solid black;font-weight:bold; text-align: center"
                                        rowspan="2">Productos Recuperados
                                    </td>
                                    <td width="25%"
                                        style="background-color: #D8D8D8;border-right: 1px solid black;border-bottom: 1px solid black;font-weight:bold; text-align: center"
                                        rowspan="2">Producto Recuperado Longitud real [m]
                                    </td>
                                    <td width="25%"
                                        style="text-align:center;background-color: #D8D8D8;border-right: 1px solid black;border-bottom: 1px solid black;font-weight:bold;"
                                        rowspan="2">Causas de la No Conformidad
                                    </td>
                                </tr>
                                <tr>
                                    <td width="5%"
                                        style="text-align:center;background-color: #D8D8D8;border-right: 1px solid black;border-bottom: 1px solid black;font-weight:bold;">
                                        Longitud [m]
                                    </td>
                                    <td width="5%"
                                        style="text-align:center;background-color: #D8D8D8;border-bottom: 1px solid black;font-weight:bold;">
                                        Desperdicio [m]
                                    </td>
                                </tr>
                                %for line in my_recuperado:
                                    <tr>
                                        <td width="1%"
                                            style="text-align:center;border-bottom: 1px solid black;border-right: 1px solid black;font-weight:bold;">
                                            ${line[0] or ''}
                                        </td>
                                        <td width="5%"
                                            style="text-align:center;border-bottom: 1px solid black;border-right: 1px solid black;font-weight:bold;">${line[2] or ''}</td>
                                        <td width="5%"
                                            style="text-align:center;border-bottom: 1px solid black;border-right: 1px solid black;font-weight:bold;">${ line[3] or ''}</td>
                                        <td width="5%"
                                            style="text-align:center;border-bottom: 1px solid black;border-right: 1px solid black;font-weight:bold;">${ line[6] or ''}</td>
                                        <td width="5%"
                                            style="text-align:center;border-bottom: 1px solid black;border-right: 1px solid black;font-weight:bold;">${ line[4] or ''}</td>
                                        <td width="5%"
                                            style="text-align:left;border-bottom: 1px solid black;border-right: 1px solid black;font-weight:bold; padding-left:10px;">${ line[7] or ''}</td>
                                        <td width="5%"
                                            style="text-align:center;border-bottom: 1px solid black;font-weight:bold;">${ line[8] or ''}</td>
                                    </tr>
                                %endfor
                                % for x in range(numero_filas):
                                    <tr>
                                        <td width="1%"
                                            style="text-align:center;border-bottom: 1px solid black; border-right: 1px solid black;font-weight:bold;">

                                        </td>
                                        <td width="5%"
                                            style="text-align:center;border-bottom: 1px solid black;border-right: 1px solid black;font-weight:bold;">
                                            &nbsp;</td>
                                        <td width="5%"
                                            style="text-align:center;border-bottom: 1px solid black;border-right: 1px solid black;font-weight:bold;">
                                            &nbsp;</td>
                                        <td width="5%"
                                            style="text-align:center;border-bottom: 1px solid black;border-right: 1px solid black;font-weight:bold;">
                                            &nbsp;</td>
                                        <td width="5%"
                                            style="text-align:center;border-bottom: 1px solid black;border-right: 1px solid black;font-weight:bold;">
                                            &nbsp;</td>
                                        <td width="5%"
                                            style="text-align:center;border-bottom: 1px solid black;border-right: 1px solid black;font-weight:bold;">
                                            &nbsp;</td>
                                        <td width="5%"
                                            style="text-align:center;border-bottom: 1px solid black;font-weight:bold;">
                                            &nbsp;</td>
                                    </tr>
                                % endfor

                                <tr>
                                    <td width="5%"
                                        style="text-align:right;border-right: 1px solid black;border-top: 1px solid black;border-bottom: 1px solid black;font-weight:bold;"
                                        colspan="3">Total:
                                    </td>
                                    <td width="5%"
                                        style="text-align:center;border-right: 1px solid black;border-top: 1px solid black;border-bottom: 1px solid black;font-weight:bold;">
                                    ${total_recuperado}
                                    </td>
                                    <td width="5%"
                                        style="text-align:center;border-top: 1px solid black;border-bottom: 1px solid black;"
                                        colspan="3">

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
