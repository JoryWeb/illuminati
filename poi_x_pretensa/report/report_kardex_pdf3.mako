<html>
<head>
   
<style type="text/css">
${css}

</style>
</head>

<body style="margin-top: 0px; margin-bottom: 0px; padding-top: 0;font-size: 11px;">
<div class="row">
    <div class="col-xs-4">
        <img src="data:image/png;base64,${logo}"  width="140" height="60" />
    </div>
    <div class="col-xs-4">
        <h3>Tarjeta de Existencias</h3>
    </div>
    <div class="col-xs-4">
        <strong>Nit:</strong> ${company.nit}
    </div>
</div>
<div class="row">
    <div class="col-xs-12">
     %if pro:      
        <strong>Articulo:</strong> ${pro.product_id.name}
      %else:
         <strong>Articulo:</strong> Todos
      %endif
    </div>
    <div class="col-xs-12">
      %if pro:      
        <strong>Codigo de Item:</strong> ${pro.product_id.default_code}
      %else:
        <strong>Codigo de Item:</strong> 
      %endif
    </div>
    <div class="col-xs-12">
      %if pro:      
        <strong>Lote: </strong> ${pro.name}
      %else:
        <strong>Lote: </strong>
      %endif
    </div>
    
</div>
%for o in objects:
<div>

    <table class="table table-bordered table-condensed">
        <thead>
          <tr>
            <th colspan="7"></th>
            <th colspan="3">Cantidad Pza.</th>
            
          </tr>
          <tr>
              <th>Nro. de Documento</th>
              <th>Tip. Movimiento</th>
              <th>Fecha</th>
              <th>Codigo</th>
              <th>Detalle</th>
              <th>Nombre</th>
              <th>Almacen</th>
              <th>Entrada Pza.</th>
              <th>Salida Pza.</th>
              <th>Saldo Pza.</th>
          </tr>
        </thead>
        <tbody>
          
        <% a = 0 %>
        <% b = 0 %>
        <% c = 0 %>
        <% d = 0 %>
        <% e = 0 %>
        <% f = 0 %>
        %for line in get_all_lines():
            
            <tr>
                <td>${line.pick_name or ''}</td>
                <td>${line.tipo}</td>
                <td>${line.date}</td>
                <td>${line.code}</td>
                <td>${line.detail}</td>
                <td>${line.lote}</td>
                <td>${line.warehouse_id.name}</td>
                %if line.tipo == 'SALDO' and (line.entrada-line.salida) >0:      
                <td class="text-right">${formatLang((line.entrada-line.salida), digits=get_digits(dp='Account'))}</td>
                %endif
                %if line.tipo == 'SALDO' and ((line.entrada-line.salida) <0 or (line.entrada-line.salida) == 0):      
                <td class="text-right">0.00</td>
                %endif
                %if line.tipo == 'SALDO' and (line.entrada-line.salida) <0:      
                <td class="text-right">${formatLang((line.entrada-line.salida), digits=get_digits(dp='Account'))}</td>
                %endif
                %if line.tipo == 'SALDO' and ((line.entrada-line.salida) >0 or (line.entrada-line.salida) == 0):      
                <td class="text-right">0.00</td>
                %endif

                %if line.tipo != 'SALDO':      
                <td class="text-right">${formatLang(line.entrada, digits=get_digits(dp='Account'))}</td>      
                <td class="text-right">${formatLang(line.salida, digits=get_digits(dp='Account'))}</td>
                %endif

                <td class="text-right">${formatLang(line.qtyy+c, digits=get_digits(dp='Account'))}</td>
            </tr>
            %if line.tipo == 'SALDO' and (line.entrada-line.salida) >0:      
              <% a = a + (line.entrada-line.salida) %>
            %endif
            %if line.tipo == 'SALDO' and (line.entrada-line.salida) <0:      
              <% a = a + 0 %>
            %endif
            %if line.tipo == 'SALDO' and (line.entrada-line.salida) <0:      
                <% b = b + (line.entrada-line.salida) %>
            %endif
            %if line.tipo == 'SALDO' and (line.entrada-line.salida) >0:      
                <% b = b + 0 %>
            %endif
            %if line.tipo != 'SALDO':  
              <% a = a + line.entrada %>
              <% b = b + line.salida %>  
            %endif  
            <% c = c + line.qtyy %>
        %endfor
          <tr>
          <td colspan="7"></td>
            <td class="text-right"><strong>${formatLang(a, digits=get_digits(dp='Account'))}</strong></td>
            <td class="text-right"><strong>${formatLang(b, digits=get_digits(dp='Account'))}</strong></td>
            <td class="text-right"><strong>${formatLang(c, digits=get_digits(dp='Account'))}</strong></td>
          </tr>
        </tbody>
    </table>
             
</div>

%endfor
</body>
</html>
