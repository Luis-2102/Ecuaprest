document.addEventListener('DOMContentLoaded', function () {
    const actividades = document.querySelectorAll('.actividad-item');
    const paginacion = document.getElementById('paginacion-actividades');
    const itemsPorPagina = 5;
    let paginaActual = 1;
    const totalPaginas = Math.ceil(actividades.length / itemsPorPagina);
    const maxPaginasMostrar = 10; // Número máximo de páginas que se mostrarán

    function mostrarPagina(pagina) {
        paginaActual = pagina;
        actividades.forEach((item, index) => {
            item.style.display = (index >= (pagina - 1) * itemsPorPagina && index < pagina * itemsPorPagina) ? '' : 'none';
        });
        renderizarPaginacion();
    }

    function renderizarPaginacion() {
        paginacion.innerHTML = '';
        
        // Determinar el rango de páginas a mostrar
        let inicio = Math.max(1, paginaActual - Math.floor(maxPaginasMostrar / 2));
        let fin = Math.min(totalPaginas, inicio + maxPaginasMostrar - 1);
        
        // Ajustar el inicio si hay menos páginas que el máximo que queremos mostrar
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
            paginacion.appendChild(li);
        }
    }

    mostrarPagina(1);
});
