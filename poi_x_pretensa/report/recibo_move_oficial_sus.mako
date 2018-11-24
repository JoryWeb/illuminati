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
            height = 300px;
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
            page-break-after: always;
        }

    </style>
</head>

<body>

    %for order in objects:
        <table class="header" style="border-spacing:  0px; WIDTH: 200mm;">
            <tr>
                <td width="30%" rowspan="2">${helper.embed_logo_by_name('pretensa_logo')|safe}</td>
                <td style=" border-bottom-left-radius: 20px;border-bottom: 1px solid black;border-left: 1px solid black; border-top-left-radius: 20px;  border-left: 1px solid black; border-top: 1px solid black;font-size: 29px; font-weight:bold; font-family: Arial, serif;  width: 50%"
                    align="center" rowspan="2">RECIBO OFICIAL<br><span
                        style="font-size: 14px; font-weight:bold; font-family: Arial, serif;">${number or ''}<br>Original</span>
                </td>

            </tr>
            <tr>

                <td style="border-left: 1px solid black;  border-top: 1px solid black; border-right: 1px solid black; border-top-right-radius: 20px; width: 20%; border-left: 1px solid black; border-bottom: 1px solid black; border-bottom-right-radius: 20px;border-right: 1px solid black;font-size:14px;font-weight:bold;"
                    rowspan="2" align="center">&nbsp;$us.&nbsp;&nbsp;${amount_recibo_sus}</td>
            </tr>
        </table>
        <br>
        <div class="line">
            <table style=" width: 90%">
                <tr>
                    <td>
                        <span style="font-size:14px;">AD/RO version 1.0/11.14</span>
                    </td>
                </tr>
            </table>
            <table style="border-spacing: 0px; WIDTH: 200mm; HEIGHT: 200mm">


                <tr>
                    <td style="text-align:left; font-size:14px;font-family: arial; border-top-left-radius: 20px; border-top: 1px solid black;border-left: 1px solid black; HEIGHT: 7mm"
                        width="50%"><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Recibí del Señor (a):</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${cliente}
                    </td>
                    <td style="text-align:left; font-size:14px;font-family: arial; border-top-right-radius: 20px; border-top: 1px solid black;border-right: 1px solid black;"
                        width="50%"><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Teléfono / Celular:</b>&nbsp&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${telefono}
                        &nbsp;<b>-</b>&nbsp;${mobile}</td>
                </tr>

                <tr>
                    <td style="text-align:left; font-size:14px;font-family: arial;border-left: 1px solid black;border-right: 1px solid black;HEIGHT: 7mm"
                        width="50%" colspan="2">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>NIT:</b>&nbsp&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${nit}
                    </td>
                </tr>
                <tr>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-left: 1px solid black;border-right: 1px solid black; HEIGHT: 7mm"
                        width="70%" colspan="2">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Nombre a Facturar:</b>_______________________________<b>NIT:</b>____________________
                    </td>

                </tr>

                <tr>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-left: 1px solid black;border-right: 1px solid black; HEIGHT: 7mm"
                        width="70%" colspan="2">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>La suma de:</b>&nbsp&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${literal_sus}
                        &nbsp;&nbsp;&nbsp;&nbsp;${centavos_sus} / 100 Dólares
                    </td>

                </tr>

                <tr>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-left: 1px solid black;border-right: 1px solid black; HEIGHT: 7mm"
                        width="70%" colspan="2">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Por Concepto de:</b>

                        <table width="100%">
                            %for line in order.line_cr_ids:
                                <tr>
                                    <td width="16%">
                                        &nbsp;
                                    </td>
                                    <td width="14%" style="font-size:14px;">
                                        <span style="font-weight:bold;">${ line.move_line_id.ref}&nbsp;&nbsp;&nbsp;Fact. N°&nbsp;${ line.move_line_id.cc_nro or '' }</span>
                                    </td>
                                    <td width="70%" style="font-size:14px;">
                                        ${formatLang(line.amount*tc)}
                                    </td>
                                </tr>
                            %endfor
                            <tr>
                                <td width="16%">
                                    &nbsp;
                                </td>
                                <td width="34%">
                                    <span style="font-weight:bold; font-size:14px;">Adelanto:</span>
                                </td>
                                <td width="50%" style="font-size:14px;">
                                    ${monto_num_sus}
                                </td>
                            </tr>
                        </table>
                    </td>

                </tr>

                <tr>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-left: 1px solid black;border-right: 1px solid black; HEIGHT: 7mm"
                        width="70%" colspan="2">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Metodo de Pago:</b>&nbsp;&nbsp&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${metodo_pago}
                    </td>

                </tr>
                <tr>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-left: 1px solid black;border-right: 1px solid black; HEIGHT: 7mm"
                        width="70%" colspan="2" align="center">

                        <table>

                            <tr>
                                <td style="text-align:left; font-size:14px; font-family: arial;" valign="top">
                                    &nbsp;&nbsp;&nbsp;&nbsp;
                                </td>
                                <td style="text-align:left; font-size:14px; font-family: arial;" valign="top">
                                    <b>${efectivo}</b>
                                </td>
                                <td style="text-align:left; font-size:14px; font-family: arial;">
                                    &nbsp;
                                </td>
                            </tr>
                            <tr>
                                <td style="text-align:left; font-size:14px; font-family: arial;" valign="top">
                                    &nbsp;&nbsp;&nbsp;&nbsp;
                                </td>
                                <td style="text-align:left; font-size:14px; font-family: arial;" valign="top">
                                    <b>${cheque}</b>
                                </td>
                                <td style="text-align:left; font-size:14px; font-family: arial;">
                                    <br>
                                    <b>${name_bank_label}</b>&nbsp;&nbsp;${name_bank}<br>
                                    <b>${number_bank_label}</b>&nbsp;&nbsp;${number_bank}<br>

                                </td>
                            </tr>

                        </table>

                    </td>

                </tr>

                <tr>
                    <td style="text-align:left; font-size:14px; text-align:center; border-bottom-left-radius: 20px; border-bottom-right-radius: 20px;border-bottom: 1px solid black; border-top: 1px solid white; border-right: 1px solid black;border-left: 1px solid black;"
                        width="70%" colspan="2" valign="bottom">${order.user_id.city or ''},&nbsp; ${dia}
                        &nbsp;de&nbsp;${mes}&nbsp;de&nbsp;${ano} <br>&nbsp;</td>

                </tr>

            </table>

            <br>
            <table style="border-spacing: 0px; WIDTH: 200mm;">


                <tr>
                    <td style="text-align:left; font-size:14px;font-family: arial; border-top-left-radius: 20px; border-top: 1px solid black;border-left: 1px solid black;"
                        width="50%" colspan="2"><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Nombre:.......................................................
                    </td>
                    <td style="text-align:left; font-size:14px;font-family: arial;  border-top: 1px solid black;border-top-right-radius: 20px;border-right: 1px solid black;"
                        width="50%" colspan="2"><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Nombre:.......................................................
                    </td>

                </tr>
                <tr>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-left: 1px solid black;"
                        width="22%">&nbsp;</td>
                    <td style="text-align:left; font-size:14px; font-family: arial;" width="28%">&nbsp;</td>
                    <td style="text-align:left; font-size:14px; font-family: arial;" width="22%">&nbsp;</td>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-right: 1px solid black;"
                        width="28%">&nbsp;</td>
                </tr>
                <tr>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-left: 1px solid black;"
                        width="22%">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;C.I.:....................................
                    </td>
                    <td style="text-align:left; font-size:14px; font-family: arial;" width="28%">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>
                    <td style="text-align:left; font-size:14px; font-family: arial;" width="22%">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;C.I.:....................................</td>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-right: 1px solid black;"
                        width="28%">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>
                </tr>
                <tr>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-left: 1px solid black;"
                        width="22%">&nbsp;</td>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-bottom: 1px dotted black;"
                        width="28%">&nbsp;</td>
                    <td style="text-align:left; font-size:14px; font-family: arial;" width="22%">&nbsp;</td>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-right: 1px solid black;border-bottom: 1px dotted black;"
                        width="28%">&nbsp;</td>
                </tr>
                <tr>
                    <td style="text-align:left; font-size:14px;font-family: arial;border-left: 1px solid black;border-bottom: 1px solid black;border-bottom-left-radius: 20px;"
                        width="22%">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Tel.:....................................
                    </td>
                    <td style="text-align:center; font-size:12px; font-family: arial;border-bottom: 1px solid black"
                        width="28%">Recibí Conforme
                    </td>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-bottom: 1px solid black"
                        width="22%">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Tel.:....................................
                    </td>
                    <td style="text-align:center; font-size:12px; font-family: arial;border-bottom: 1px solid black; border-right: 1px solid black;  border-bottom-right-radius: 20px;"
                        width="28%">Entregué Conforme
                    </td>
                </tr>
            </table>
            <table style=" width: 100%">
                <tr>
                    <td>
                        <span style="font-weight:bold;font-size:14px;">Nota:</span><span style="font-size:14px;">&nbsp;&nbsp;Este Recibo deberá ser canjeado por la Nota Fiscal correspondiente a partir de la fecha del mismo.</span>
                    </td>
                </tr>
            </table>

        </div>

        <table class="header" style="border-spacing:  0px; WIDTH: 200mm;">
            <tr>
                <td width="30%" rowspan="2">${helper.embed_logo_by_name('pretensa_logo')|safe}</td>
                <td style=" border-bottom-left-radius: 20px;border-bottom: 1px solid black;border-left: 1px solid black; border-top-left-radius: 20px;  border-left: 1px solid black; border-top: 1px solid black;font-size: 29px; font-weight:bold; font-family: Arial, serif;  width: 50%"
                    align="center" rowspan="2">RECIBO OFICIAL<br><span
                        style="font-size: 14px; font-weight:bold; font-family: Arial, serif;">${number}<br>Copia</span>
                </td>

            </tr>
            <tr>

                <td style="border-left: 1px solid black;  border-top: 1px solid black; border-right: 1px solid black; border-top-right-radius: 20px; width: 20%; border-left: 1px solid black; border-bottom: 1px solid black; border-bottom-right-radius: 20px;border-right: 1px solid black;font-size:14px;font-weight:bold;"
                    rowspan="2" align="center">&nbsp;$us.&nbsp;&nbsp;${amount_recibo_sus}</td>
            </tr>
        </table>
        <br>
        <div class="line">
            <table style=" width: 90%">
                <tr>
                    <td>
                        <span style="font-size:14px;">AD/RO version 1.0/11.14</span>
                    </td>
                </tr>
            </table>
            <table style="border-spacing: 0px; WIDTH: 200mm; HEIGHT: 190mm">


                <tr>
                    <td style="text-align:left; font-size:14px;font-family: arial; border-top-left-radius: 20px; border-top: 1px solid black;border-left: 1px solid black; HEIGHT: 7mm"
                        width="50%"><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Recibí del Señor (a):</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${cliente}
                    </td>
                    <td style="text-align:left; font-size:14px;font-family: arial; border-top-right-radius: 20px; border-top: 1px solid black;border-right: 1px solid black;"
                        width="50%"><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Teléfono / Celular:</b>&nbsp&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${telefono}
                        &nbsp;<b>-</b>&nbsp;${mobile}</td>
                </tr>

                <tr>
                    <td style="text-align:left; font-size:14px;font-family: arial;border-left: 1px solid black;border-right: 1px solid black;HEIGHT: 7mm"
                        width="50%" colspan="2">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>NIT:</b>&nbsp&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${nit}
                    </td>
                </tr>
                <tr>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-left: 1px solid black;border-right: 1px solid black; HEIGHT: 7mm"
                        width="70%" colspan="2">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Nombre a Facturar:</b>_______________________________<b>NIT:</b>____________________
                    </td>

                </tr>

                <tr>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-left: 1px solid black;border-right: 1px solid black; HEIGHT: 7mm"
                        width="70%" colspan="2">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>La suma de:</b>&nbsp&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${literal_sus}
                        &nbsp;&nbsp;&nbsp;&nbsp;${centavos_sus} / 100 Dólares
                    </td>

                </tr>

                <tr>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-left: 1px solid black;border-right: 1px solid black; HEIGHT: 7mm"
                        width="70%" colspan="2">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Por Concepto de:</b>

                        <table width="100%">
                            %for line in order.line_cr_ids:
                                <tr>
                                    <td width="16%">
                                        &nbsp;
                                    </td>
                                    <td width="14%" style="font-size:14px;">
                                        <span style="font-weight:bold;">${ line.move_line_id.ref}&nbsp;&nbsp;&nbsp;Fact. N°&nbsp;${ line.move_line_id.cc_nro or '' }</span>
                                    </td>
                                    <td width="70%" style="font-size:14px;">
                                        ${formatLang(line.amount*tc)}
                                    </td>
                                </tr>
                            %endfor
                            <tr>
                                <td width="16%">
                                    &nbsp;
                                </td>
                                <td width="34%">
                                    <span style="font-weight:bold; font-size:14px;">Adelanto:</span>
                                </td>
                                <td width="50%" style="font-size:14px;">
                                    ${monto_num_sus}
                                </td>
                            </tr>
                        </table>
                    </td>

                </tr>

                <tr>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-left: 1px solid black;border-right: 1px solid black; HEIGHT: 7mm"
                        width="70%" colspan="2">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Metodo de Pago:</b>&nbsp;&nbsp&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${metodo_pago}
                    </td>

                </tr>
                <tr>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-left: 1px solid black;border-right: 1px solid black; HEIGHT: 7mm"
                        width="70%" colspan="2" align="center">

                        <table>

                            <tr>
                                <td style="text-align:left; font-size:14px; font-family: arial;" valign="top">
                                    &nbsp;&nbsp;&nbsp;&nbsp;
                                </td>
                                <td style="text-align:left; font-size:14px; font-family: arial;" valign="top">
                                    <b>${efectivo}</b>
                                </td>
                                <td style="text-align:left; font-size:14px; font-family: arial;">
                                    &nbsp;
                                </td>
                            </tr>
                            <tr>
                                <td style="text-align:left; font-size:14px; font-family: arial;" valign="top">
                                    &nbsp;&nbsp;&nbsp;&nbsp;
                                </td>
                                <td style="text-align:left; font-size:14px; font-family: arial;" valign="top">
                                    <b>${cheque}</b>
                                </td>
                                <td style="text-align:left; font-size:14px; font-family: arial;">
                                    <br>
                                    <b>${name_bank_label}</b>&nbsp;&nbsp;${name_bank}<br>
                                    <b>${number_bank_label}</b>&nbsp;&nbsp;${number_bank}<br>

                                </td>
                            </tr>

                        </table>

                    </td>

                </tr>

                <tr>
                    <td style="text-align:left; font-size:14px; text-align:center; border-bottom-left-radius: 20px; border-bottom-right-radius: 20px;border-bottom: 1px solid black; border-top: 1px solid white; border-right: 1px solid black;border-left: 1px solid black;"
                        width="70%" colspan="2" valign="bottom">${order.user_id.city or ''},&nbsp; ${dia}
                        &nbsp;de&nbsp;${mes}&nbsp;de&nbsp;${ano} <br>&nbsp;</td>

                </tr>

            </table>

            <br>
            <table style="border-spacing: 0px; WIDTH: 200mm;">


                <tr>
                    <td style="text-align:left; font-size:14px;font-family: arial; border-top-left-radius: 20px; border-top: 1px solid black;border-left: 1px solid black;"
                        width="50%" colspan="2"><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Nombre:.......................................................
                    </td>
                    <td style="text-align:left; font-size:14px;font-family: arial;  border-top: 1px solid black;border-top-right-radius: 20px;border-right: 1px solid black;"
                        width="50%" colspan="2"><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Nombre:.......................................................
                    </td>

                </tr>
                <tr>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-left: 1px solid black;"
                        width="22%">&nbsp;</td>
                    <td style="text-align:left; font-size:14px; font-family: arial;" width="28%">&nbsp;</td>
                    <td style="text-align:left; font-size:14px; font-family: arial;" width="22%">&nbsp;</td>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-right: 1px solid black;"
                        width="28%">&nbsp;</td>
                </tr>
                <tr>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-left: 1px solid black;"
                        width="22%">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;C.I.:....................................
                    </td>
                    <td style="text-align:left; font-size:14px; font-family: arial;" width="28%">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>
                    <td style="text-align:left; font-size:14px; font-family: arial;" width="22%">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;C.I.:....................................</td>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-right: 1px solid black;"
                        width="28%">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>
                </tr>
                <tr>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-left: 1px solid black;"
                        width="22%">&nbsp;</td>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-bottom: 1px dotted black;"
                        width="28%">&nbsp;</td>
                    <td style="text-align:left; font-size:14px; font-family: arial;" width="22%">&nbsp;</td>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-right: 1px solid black;border-bottom: 1px dotted black;"
                        width="28%">&nbsp;</td>
                </tr>
                <tr>
                    <td style="text-align:left; font-size:14px;font-family: arial;border-left: 1px solid black;border-bottom: 1px solid black;border-bottom-left-radius: 20px;"
                        width="22%">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Tel.:....................................
                    </td>
                    <td style="text-align:center; font-size:12px; font-family: arial;border-bottom: 1px solid black"
                        width="28%">Recibí Conforme
                    </td>
                    <td style="text-align:left; font-size:14px; font-family: arial;border-bottom: 1px solid black"
                        width="22%">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Tel.:....................................
                    </td>
                    <td style="text-align:center; font-size:12px; font-family: arial;border-bottom: 1px solid black; border-right: 1px solid black;  border-bottom-right-radius: 20px;"
                        width="28%">Entregué Conforme
                    </td>
                </tr>
            </table>
            <table style=" width: 100%">
                <tr>
                    <td>
                        <span style="font-weight:bold;font-size:14px;">Nota:</span><span style="font-size:14px;">&nbsp;&nbsp;Este Recibo deberá ser canjeado por la Nota Fiscal correspondiente a partir de la fecha del mismo.</span>
                    </td>
                </tr>
            </table>

        </div>
        <br>
        <br>
    %endfor
</body>
</html>
