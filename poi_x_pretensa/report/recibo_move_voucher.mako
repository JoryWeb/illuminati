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

<table class="header" style="border-bottom: 0px solid black; width: 100%">
    <tr>
        <td><span style="font-size:10; font-family: arial">Version:&nbsp;&nbsp;1.1/D4.11 AD/MLL/RP</span></td>
    </tr>
    <tr>
        <td align="center" width="72%"><span
                style="font-size:18; font-family: arial; font-weight: bold">RECIBO DE PAGO</span></td>
        <td style="text-align:right" width="28%">
            <table class="header" style="border-bottom: 0px solid black; width: 100%">
                <tr>
                    <td><span style="font-size: 12; font-family: arial">N°&nbsp;${numero}</span></td>
                </tr>
                <tr>
                    <td><span style="font-size: 12; font-family: arial">${currency}&nbsp;${monto}</span></td>
                </tr>
                <tr>
                    <td><span style="font-size: 12; font-family: arial">Original</span></td>
                </tr>
                <tr>
                    <td><span style="font-size: 12; font-family: arial">${cuenta_analitica}</span></td>
                </tr>
            </table>
        </td>
    </tr>

</table>

<div class="line">
    <table width="100%" style="margin-top: 20px;">


        <tr>
            <td style="text-align:left; font-size:10px" width="10%"><span style="font-size: 12; font-family: arial">Hemos cancelado a:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${nombre_facturar}</span>
            </td>
        </tr>
        <tr>
            <td style="text-align:left; font-size:10px" width="10%"><span style="font-size: 12; font-family: arial">La suma de:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${literal}
                &nbsp;&nbsp;&nbsp;&nbsp;${centavos} / 100 ${currency}</span></td>
        </tr>
        <tr>
            <td style="text-align:left; font-size:10px" width="10%"><span style="font-size: 12; font-family: arial">Por concepto de:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${concepto}</span>
            </td>
        </tr>

    </table>
    <table width="100%" style="margin-top: 20px;">
        <thead>
        <tr>
            <th style="text-align:center; font-size:10px" width="10%">La Paz,&nbsp; ${dia}&nbsp;de&nbsp;${mes}&nbsp;de&nbsp;${ano} </th>
        </tr>
    </table>

</div>

<br>
<br>
<br>
<br>

<br>

<table style="border-top: 0px solid black; width: 100%">
    <tr>
        <td style="text-align:center;font-size:12;" width="10%">&nbsp;</td>
        <td style="text-align:center;font-size:12;  border-bottom: 2px solid black;" width="24%">&nbsp;</td>
        <td style="text-align:center;font-size:12;" width="5%">&nbsp;</td>
        <td style="text-align:center;font-size:12;  border-bottom: 2px solid black;" width="24%">&nbsp;</td>
        <td style="text-align:center;font-size:12;" width="5%">&nbsp;</td>
        <td style="text-align:center;font-size:12;  border-bottom: 2px solid black;" width="24%">&nbsp;</td>
        <td style="text-align:center;font-size:12;" width="10%">&nbsp;</td>
    </tr>
    <tr>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">Autorización</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">Entregué Conforme</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">Recibí Conforme</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
    </tr>
    <tr>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:left;font-size:12;">C.I. ...........................................</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
    </tr>
    <tr>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:left;font-size:12;">Nombre: .................................</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
    </tr>

</table>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<table class="header" style="border-bottom: 0px solid black; width: 100%">
    <tr>
        <td><span style="font-size:10; font-family: arial">Version:&nbsp;&nbsp;1.1/D4.11 AD/MLL/RP</span></td>
    </tr>
    <tr>
        <td align="center" width="72%"><span
                style="font-size:18; font-family: arial; font-weight: bold">RECIBO DE PAGO</span></td>
        <td style="text-align:right" width="28%">
            <table class="header" style="border-bottom: 0px solid black; width: 100%">
                <tr>
                    <td><span style="font-size: 12; font-family: arial">N°&nbsp;${numero}</span></td>
                </tr>
                <tr>
                    <td><span style="font-size: 12; font-family: arial">${currency}&nbsp;${monto}</span></td>
                </tr>
                <tr>
                    <td><span style="font-size: 12; font-family: arial">Copia</span></td>
                </tr>
                <tr>
                    <td><span style="font-size: 12; font-family: arial">${cuenta_analitica}</span></td>
                </tr>
            </table>
        </td>
    </tr>


</table>

<div class="line">
    <table width="100%" style="margin-top: 20px;">


        <tr>
            <td style="text-align:left; font-size:10px" width="10%"><span style="font-size: 12; font-family: arial">Hemos cancelado a:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${nombre_facturar}</span>
            </td>
        </tr>
        <tr>
            <td style="text-align:left; font-size:10px" width="10%"><span style="font-size: 12; font-family: arial">La suma de:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${literal}
                &nbsp;&nbsp;&nbsp;&nbsp;${centavos} / 100 ${currency}</span></td>
        </tr>
        <tr>
            <td style="text-align:left; font-size:10px" width="10%"><span style="font-size: 12; font-family: arial">Por concepto de:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${concepto}</span>
            </td>
        </tr>

    </table>
    <table width="100%" style="margin-top: 20px;">
        <thead>
        <tr>
            <th style="text-align:center; font-size:10px" width="10%">La Paz,&nbsp; ${dia}&nbsp;de&nbsp;${mes}&nbsp;de&nbsp;${ano} </th>
        </tr>
    </table>

</div>

<br>
<br>
<br>
<br>

<br>

<table style="border-top: 0px solid black; width: 100%">
    <tr>
        <td style="text-align:center;font-size:12;" width="10%">&nbsp;</td>
        <td style="text-align:center;font-size:12;  border-bottom: 2px solid black;" width="24%">&nbsp;</td>
        <td style="text-align:center;font-size:12;" width="5%">&nbsp;</td>
        <td style="text-align:center;font-size:12;  border-bottom: 2px solid black;" width="24%">&nbsp;</td>
        <td style="text-align:center;font-size:12;" width="5%">&nbsp;</td>
        <td style="text-align:center;font-size:12;  border-bottom: 2px solid black;" width="24%">&nbsp;</td>
        <td style="text-align:center;font-size:12;" width="10%">&nbsp;</td>
    </tr>
    <tr>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">Autorización</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">Entregué Conforme</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">Recibí Conforme</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
    </tr>
    <tr>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:left;font-size:12;">C.I. ...........................................</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
    </tr>
    <tr>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
        <td style="text-align:left;font-size:12;">Nombre: .................................</td>
        <td style="text-align:center;font-size:12;">&nbsp;</td>
    </tr>

</table>

</body>
</html>
