// static/js/script.js

document.addEventListener('DOMContentLoaded', function() {
    // Inizializza il calendario
    var calendarEl = document.getElementById('calendar');

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'it',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: ''
        },
        events: {
            url: '/api/meals/events',
            method: 'GET',
            failure: function() {
                alert('Errore nel caricamento degli eventi!');
            }
        },
        eventColor: '#378006',
        dateClick: function(info) {
            openMealModal(null, info.dateStr);
        },
        eventClick: function(info) {
            openMealModal(info.event.extendedProps, info.event.startStr);
        }
    });

    calendar.render();

    // Funzione per caricare i pasti divisi per settimana
    function loadMealsByWeek() {
        fetch('/api/meals/week')
        .then(response => response.json())
        .then(data => {
            var mealsByWeekEl = document.getElementById('mealsByWeek');
            mealsByWeekEl.innerHTML = '';
            data.forEach(function(day) {
                var dayDiv = document.createElement('div');
                dayDiv.className = 'mb-4';
                var dateHeading = document.createElement('h3');
                dateHeading.className = 'text-xl font-semibold mb-2';
                dateHeading.textContent = day.date;
                dayDiv.appendChild(dateHeading);

                if (day.meals.length > 0) {
                    day.meals.forEach(function(meal) {
                        var mealDiv = document.createElement('div');
                        mealDiv.className = 'ml-4 mb-2';
                        mealDiv.textContent = meal.meal_type.charAt(0).toUpperCase() + meal.meal_type.slice(1) + ': ' + meal.name;
                        dayDiv.appendChild(mealDiv);
                    });
                } else {
                    var noMealDiv = document.createElement('div');
                    noMealDiv.className = 'ml-4 mb-2 text-gray-600';
                    noMealDiv.textContent = 'Nessun pasto pianificato.';
                    dayDiv.appendChild(noMealDiv);
                }

                mealsByWeekEl.appendChild(dayDiv);
            });
        })
        .catch(error => {
            console.error('Errore:', error);
            alert('Errore durante il caricamento dei pasti.');
        });
    }

    // Carica i pasti all'avvio
    loadMealsByWeek();

    // Aggiorna i pasti dopo modifiche
    function refreshMeals() {
        calendar.refetchEvents();
        loadMealsByWeek();
    }

    // Gestione del modal (come precedentemente definito)
    // ...

    // Aggiorna le chiamate a calendar.refetchEvents() con refreshMeals()
    // Esempio:
    // calendar.refetchEvents();
    // diventa:
    // refreshMeals();

    // Nel submit del form:
    mealForm.addEventListener('submit', function(event) {
        event.preventDefault();
        // ... codice esistente ...
        fetch(url, {
            // ... codice esistente ...
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                refreshMeals();  // Aggiorna calendario e lista pasti
                closeMealModal();
            } else {
                alert('Errore durante il salvataggio del pasto.');
            }
        })
        .catch(error => {
            console.error('Errore:', error);
            alert('Errore durante il salvataggio del pasto.');
        });
    });

    // Nel deleteMealButton:
    deleteMealButton.addEventListener('click', function() {
        // ... codice esistente ...
        fetch('/api/meals', {
            // ... codice esistente ...
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                refreshMeals();  // Aggiorna calendario e lista pasti
                closeMealModal();
            } else {
                alert('Errore durante l\'eliminazione del pasto.');
            }
        })
        .catch(error => {
            console.error('Errore:', error);
            alert('Errore durante l\'eliminazione del pasto.');
        });
    });
});
