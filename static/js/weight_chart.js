// static/js/weight_chart.js

document.addEventListener('DOMContentLoaded', function() {
    const weightForm = document.getElementById('weightForm');
    const weightDateInput = document.getElementById('weightDate');
    const weightValueInput = document.getElementById('weightValue');
    const weightChartCtx = document.getElementById('weightChart').getContext('2d');

    let weightChart;

    // Carica i dati iniziali
    fetchWeightData();

    // Gestisci l'invio del form
    weightForm.addEventListener('submit', function(event) {
        event.preventDefault();

        const date = weightDateInput.value;
        const weight = parseFloat(weightValueInput.value);

        if (date && weight) {
            fetch('/weight_chart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ date: date, weight: weight }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Aggiorna il grafico
                    fetchWeightData();
                    // Resetta il form
                    weightForm.reset();
                } else {
                    alert('Errore durante il salvataggio del peso.');
                }
            })
            .catch((error) => {
                console.error('Errore:', error);
            });
        } else {
            alert('Per favore, inserisci una data e un peso validi.');
        }
    });

    function fetchWeightData() {
        fetch('/api/weight_entries')
        .then(response => response.json())
        .then(data => {
            const dates = data.map(entry => entry.date);
            const weights = data.map(entry => entry.weight);

            // Se il grafico esiste già, distruggilo
            if (weightChart) {
                weightChart.destroy();
            }

            // Crea il grafico
            weightChart = new Chart(weightChartCtx, {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: [{
                        label: 'Peso (kg)',
                        data: weights,
                        borderColor: 'rgba(54, 162, 235, 1)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        fill: false,
                        tension: 0.1,
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                unit: 'day',
                                displayFormats: {
                                    day: 'dd MMM yy'
                                }
                            }
                        },
                        y: {
                            beginAtZero: false,
                        }
                    }
                }
            });
        })
        .catch((error) => {
            console.error('Errore:', error);
        });
    }
});
