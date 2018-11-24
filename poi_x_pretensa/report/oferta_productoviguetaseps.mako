<html>
<head>
    <style type="text/css">
            ${css}

        .texto_left {
            font-family: Arial, arial, ARIAL, sans-serif;
            font-size: 12px;
            text-align: left
        }

        .texto_leftb {
            font-family: Arial, arial, ARIAL, sans-serif;
            font-size: 12px;
            text-align: left;
            font-weight: bold
        }

        .texto_right {
            font-family: Arial, arial, ARIAL, sans-serif;
            font-size: 12px;
            text-align: right
        }

        .texto {
            font-family: Arial, arial, ARIAL, sans-serif;
        }

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

        td.formatted_note {
            text-align: left;
            border-right: thin solid #EEEEEE;
            border-left: thin solid #EEEEEE;
            border-top: thin solid #EEEEEE;
            padding-left: 10px;
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

    </style>
</head>

<body>


    %for order in objects:


    <table width="100%">
        <tr>
            <td class="texto_left" width="15%">Señor(es):</td>
            <td class="texto_right" width="15%" colspan="4">La Paz,&nbsp; ${dia}&nbsp;de&nbsp;${mes}
                &nbsp;de&nbsp;${ano} </td>

        </tr>
        <tr>
            <td class="texto_left" width="15%" colspan="3"><b>${order.partner_id.name}</b></td>

            <td class="texto_right" width="42%">Celular:</td>
            <td class="texto_right" width="10%">${order.partner_id.mobile or ''}</td>
        </tr>
        <tr>
            <td class="texto_left">Cotización N°:</td>
            <td class="texto_left" width="28%">${order.name}</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_right">Oficina:</td>
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
            <td class="texto_left" colspan="3"><b>Ref.:</b>&nbsp;&nbsp;&nbsp;${order.product_type.ref | safe}</td>

        </tr>
        <tr>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left" colspan="2">${order.note or ''}</td>

        </tr>
    </table>

    <table width="100%" style="margin-top: 20px;">

    <tbody>
    <tr>
        <td class="texto_left">${order.product_type.consideracion | safe}</td>
    </tr>
    <tr>
        <td class="texto_leftb"><br>1.&nbsp;${order.product_type.punto_uno | safe}</td>
    </tr>

    <table width="100%">
        <tr>
            <td class="texto_leftb" width="5%">&nbsp;</td>
            <td class="texto_leftb" width="5%">&nbsp;</td>
            <td class="texto_leftb" width="25%">&nbsp;</td>
            <td class="texto_leftb" width="5%">&nbsp;</td>
            <td class="texto_leftb" width="60%">&nbsp;</td>
        </tr>
        <tr>

            <td class="texto_leftb" rowspan=5 colspan="3" align="center"><img
                    src="data:image/png;base64,${order.product_type.img_consideracion  | safe}" width="280"
                    height="105"/></td>
            <td class="texto_leftb">A:</td>
            <td class="texto_leftb">${altura_compresion  | safe}&nbsp;cm</td>
        </tr>
        <tr>


            <td class="texto_leftb">B:</td>
            <td class="texto_leftb">${altura_eps  | safe}&nbsp;cm</td>
        </tr>
        <tr>

            <td class="texto_leftb">C:</td>
            <td class="texto_leftb">${total_eps  | safe}&nbsp;cm</td>
        </tr>
        <tr>
            <td class="texto_leftb">D:</td>
            <td class="texto_leftb">${eje  | safe}&nbsp;cm</td>
        </tr>
        <tr>

            <td class="texto_leftb">&nbsp;</td>
            <td class="texto_leftb">&nbsp;</td>
        </tr>
        <tr>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
        </tr>
        <tr>
            <td class="texto_left">Area Referencial:</td>
            <td class="texto_left">${area_referencial  | safe}&nbsp;m2</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
        </tr>
        <tr>
            <td class="texto_left">Peso propio:</td>
            <td class="texto_left">${peso_propio  | safe}&nbsp;kg/m2</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
        </tr>
        <tr>
            <td class="texto_left">Carga muerta:</td>
            <td class="texto_left">${carga_muerta  | safe}&nbsp;kg/m</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
        </tr>
        <tr>
            <td class="texto_left">Sobrecarga:</td>
            <td class="texto_left">${sobrecarga  | safe}&nbsp;kg/m2</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
        </tr>
        <tr>
            <td class="texto_leftb">Carga Total:</td>
            <td class="texto_leftb">${carga_total  | safe}&nbsp;kg/m2</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
        </tr>
        <tr>
            <td class="texto_left">V°H°:</td>
            <td class="texto_left">${vh  | safe}&nbsp;m3/m2</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
            <td class="texto_left">&nbsp;</td>
        </tr>
    </table>
    <table width="100%">
        <tr>
            <td class="texto_left">
                <span class="texto_left">
                   <ul>
                       ${order.product_type.consideraciones_propuesta | safe}
                   </ul>
                </span>
            </td>
        </tr>
        <tr>
            <td class="texto_leftb">2.&nbsp;${order.product_type.punto_dos | safe}</td>
        </tr>

        <tr valign="top">
            <td class="texto_left" valign="top"><br>${order.product_type.especificaciones | safe}</td>
        </tr>
        <br>
        <tr>
            <td class="texto_leftb">3.&nbsp;${order.product_type.punto_tres | safe}</td>
        </tr>

        <tr>
            <td class="texto_left"><br>${order.product_type.carpeta | safe}
                <ul>
                    <table width="30%">
                        <tr>
                            <td class="texto_left" width="10%">Hormigón:</td>
                            <td class="texto_left" width="20%">${hormigon or ''}&nbsp;m3</td>
                        </tr>
                        <tr>
                            <td class="texto_left" width="10%">Cemento:</td>
                            <td class="texto_left" width="20%">${cemento or ''}&nbsp;bolsas</td>
                        </tr>
                        <tr>
                            <td class="texto_left" width="10%">Arena:</td>
                            <td class="texto_left" width="20%">${arena or ''}&nbsp;m3</td>
                        </tr>
                        <tr>
                            <td class="texto_left" width="10%">Grava:</td>
                            <td class="texto_left" width="20%">${grava or ''}&nbsp;m3</td>
                        </tr>
                        <tr>
                            <td class="texto_left" width="10%">Acero:</td>
                            <td class="texto_left" width="20%">${acero or ''}&nbsp;barras Ø ¼"</td>
                        </tr>
                    </table>
                </ul>
            </td>
        </tr>
        <tr valign="top">
            <td class="texto_leftb"><br>4.&nbsp;PLAZO DE ENTREGA:</td>

        </tr>
        <tr>
            <td class="texto_left"><br>${order.product_type.plazo_entrega | safe}</td>

        </tr>
        <br>
        <tr>
            <td class="texto_leftb"><br>5.&nbsp;COSTO OFERTADO:</td>
        </tr>
        <tr>
            <td class="texto_leftb"><br>${formatLang(order.amount_total)}&nbsp;(${literal} &nbsp;&nbsp;&nbsp;&nbsp;${centavos} /
                100 ${currency})
            </td>
        </tr>
        <tr>
            <td class="texto_left"><br>${order.product_type.firma | safe}</td>
        </tr>
        <tr>
            <td>
                <br>
                <br>
                <table border="0" width="100%">
                    <tr>
                        <td width="10%">
                            &nbsp;
                        </td>
                        <td class="texto" align="center" width="40%"
                            style="text-align:center;font-size:12;  border-top: 1px solid black;">
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
                        <td class="texto" align="center" width="40%">
                            <span style="font-size:12px;">${puesto | safe}</span>
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
