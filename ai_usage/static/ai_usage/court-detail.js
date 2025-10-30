function drawChart(raw_data) {

    let data = google.visualization.arrayToDataTable(raw_data);

    let options = {
        title: 'Nutzergruppen',
        backgroundColor: 'transparent'
    };

    let chart = new google.visualization.PieChart(document.getElementById('ai_usage_groups_chart'));

    chart.draw(data, options);

    update_google_chart_colors();
}