(function ($) {
  'use strict';

  // Función para cargar los datos de pagos desde la base de datos
  function cargarDatosPagos() {
    return $.ajax({
      url: '/api/pagos-por-dia',
      method: 'GET',
      dataType: 'json'
    });
  }

  // Función para actualizar la gráfica
  function actualizarGrafica() {
    cargarDatosPagos().then(function (response) {
      if (salesTop) {
        // Actualizar datos del gráfico
        salesTop.data.datasets[0].data = response.thisWeek;
        salesTop.data.datasets[1].data = response.lastWeek;
        salesTop.update();
      }
    }).catch(function (error) {
      console.error("Error al cargar datos de pagos:", error);
    });
  }

  // Variable global para la gráfica
  var salesTop = null;

  $(function () {
    if ($("#performaneLine").length) {
      var graphGradient = document.getElementById("performaneLine").getContext('2d');
      var graphGradient2 = document.getElementById("performaneLine").getContext('2d');
      var saleGradientBg = graphGradient.createLinearGradient(5, 0, 5, 100);
      saleGradientBg.addColorStop(0, 'rgba(26, 115, 232, 0.18)');
      saleGradientBg.addColorStop(1, 'rgba(26, 115, 232, 0.02)');
      var saleGradientBg2 = graphGradient2.createLinearGradient(100, 0, 50, 150);
      saleGradientBg2.addColorStop(0, 'rgba(0, 208, 255, 0.19)');
      saleGradientBg2.addColorStop(1, 'rgba(0, 208, 255, 0.03)');

      // Inicializamos con datos vacíos, se llenarán cuando se carguen los datos reales
      var salesTopData = {
        labels: ["DOM", "LUN", "MAR", "MIE", "JUE", "VIE", "SAB"],
        datasets: [{
          label: 'Esta semana',
          data: [0, 0, 0, 0, 0, 0, 0],
          backgroundColor: saleGradientBg,
          borderColor: ['#1F3BB3'],
          borderWidth: 1.5,
          fill: true,
          pointBorderWidth: 1,
          pointRadius: [4, 4, 4, 4, 4, 4, 4],
          pointHoverRadius: [2, 2, 2, 2, 2, 2, 2],
          pointBackgroundColor: ['#1F3BB3', '#1F3BB3', '#1F3BB3', '#1F3BB3', '#1F3BB3', '#1F3BB3', '#1F3BB3'],
          pointBorderColor: ['#fff', '#fff', '#fff', '#fff', '#fff', '#fff', '#fff'],
        }, {
          label: 'Semana pasada',
          data: [0, 0, 0, 0, 0, 0, 0],
          backgroundColor: saleGradientBg2,
          borderColor: ['#52CDFF'],
          borderWidth: 1.5,
          fill: true,
          pointBorderWidth: 1,
          pointRadius: [4, 4, 4, 4, 4, 4, 4],
          pointHoverRadius: [2, 2, 2, 2, 2, 2, 2],
          pointBackgroundColor: ['#52CDFF', '#52CDFF', '#52CDFF', '#52CDFF', '#52CDFF', '#52CDFF', '#52CDFF'],
          pointBorderColor: ['#fff', '#fff', '#fff', '#fff', '#fff', '#fff', '#fff'],
        }]
      };

      var salesTopOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          yAxes: [{
            gridLines: {
              display: true,
              drawBorder: false,
              color: "#F0F0F0",
              zeroLineColor: '#F0F0F0',
            },
            ticks: {
              beginAtZero: false,
              autoSkip: true,
              maxTicksLimit: 4,
              fontSize: 10,
              color: "#6B778C"
            }
          }],
          xAxes: [{
            gridLines: {
              display: false,
              drawBorder: false,
            },
            ticks: {
              beginAtZero: false,
              autoSkip: true,
              maxTicksLimit: 7,
              fontSize: 10,
              color: "#6B778C"
            }
          }],
        },
        legend: false,
        legendCallback: function (chart) {
          var text = [];
          text.push('<div class="chartjs-legend"><ul>');
          for (var i = 0; i < chart.data.datasets.length; i++) {
            text.push('<li>');
            text.push('<span style="background-color:' + chart.data.datasets[i].borderColor + '">' + '</span>');
            text.push(chart.data.datasets[i].label);
            text.push('</li>');
          }
          text.push('</ul></div>');
          return text.join("");
        },
        elements: {
          line: {
            tension: 0.4,
          }
        },
        tooltips: {
          backgroundColor: 'rgba(31, 59, 179, 1)',
        }
      };

      // Crear la gráfica con datos iniciales vacíos
      salesTop = new Chart(graphGradient, {
        type: 'line',
        data: salesTopData,
        options: salesTopOptions
      });

      document.getElementById('performance-line-legend').innerHTML = salesTop.generateLegend();

      // Cargar datos iniciales
      actualizarGrafica();

      // Configurar actualización en tiempo real (cada 30 segundos)
      setInterval(actualizarGrafica, 30000);
    }
  });

  if ($("#datepicker-popup").length) {
    $('#datepicker-popup').datepicker({
      enableOnReadonly: true,
      todayHighlight: true,
    });
    $("#datepicker-popup").datepicker("setDate", "0");
  }
  if ($('#totalVisitors').length) {
    var bar = new ProgressBar.Circle(totalVisitors, {
      color: '#fff',
      // This has to be the same size as the maximum width to
      // prevent clipping
      strokeWidth: 15,
      trailWidth: 15,
      easing: 'easeInOut',
      duration: 1400,
      text: {
        autoStyleContainer: false
      },
      from: {
        color: '#52CDFF',
        width: 15
      },
      to: {
        color: '#677ae4',
        width: 15
      },
      // Set default step function for all animate calls
      step: function (state, circle) {
        circle.path.setAttribute('stroke', state.color);
        circle.path.setAttribute('stroke-width', state.width);

        var value = Math.round(circle.value() * 100);
        if (value === 0) {
          circle.setText('');
        } else {
          circle.setText(value);
        }

      }
    });

    bar.text.style.fontSize = '0rem';
    bar.animate(.64); // Number from 0.0 to 1.0
  }
  if ($('#visitperday').length) {
    var bar = new ProgressBar.Circle(visitperday, {
      color: '#fff',
      // This has to be the same size as the maximum width to
      // prevent clipping
      strokeWidth: 15,
      trailWidth: 15,
      easing: 'easeInOut',
      duration: 1400,
      text: {
        autoStyleContainer: false
      },
      from: {
        color: '#34B1AA',
        width: 15
      },
      to: {
        color: '#677ae4',
        width: 15
      },
      // Set default step function for all animate calls
      step: function (state, circle) {
        circle.path.setAttribute('stroke', state.color);
        circle.path.setAttribute('stroke-width', state.width);

        var value = Math.round(circle.value() * 100);
        if (value === 0) {
          circle.setText('');
        } else {
          circle.setText(value);
        }

      }
    });

    bar.text.style.fontSize = '0rem';
    bar.animate(.34); // Number from 0.0 to 1.0
  }

})(jQuery);