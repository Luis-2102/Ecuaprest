document.addEventListener('DOMContentLoaded', function () {
    const cobranzas = document.querySelectorAll('.cobranza-item');
    const paginacionCobranzas = document.getElementById('paginacion-cobranzas');
    const itemsPorPagina = 5;
    let paginaActual = 1;
    const totalPaginas = Math.ceil(cobranzas.length / itemsPorPagina);
    const maxPaginasMostrar = 5; // Puedes ajustar cuántas páginas quieres ver

    function mostrarPagina(pagina) {
        paginaActual = pagina;
        cobranzas.forEach((item, index) => {
            item.style.display = (index >= (pagina - 1) * itemsPorPagina && index < pagina * itemsPorPagina) ? '' : 'none';
        });
        renderizarPaginacion();
    }

    function renderizarPaginacion() {
        paginacionCobranzas.innerHTML = '';
        
        let inicio = Math.max(1, paginaActual - Math.floor(maxPaginasMostrar / 2));
        let fin = Math.min(totalPaginas, inicio + maxPaginasMostrar - 1);
        
        if (fin - inicio < maxPaginasMostrar - 1) {
            inicio = Math.max(1, fin - maxPaginasMostrar + 1);
        }

        for (let i = inicio; i <= fin; i++) {
            const li = document.createElement('li');
            li.className = `page-item ${i === paginaActual ? 'active' : ''}`;
            li.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            li.addEventListener('click', (e) => {
                e.preventDefault();
                mostrarPagina(i);
            });
            paginacionCobranzas.appendChild(li);
        }
    }

    if (cobranzas.length > 0) {
        mostrarPagina(1);
    }
});
