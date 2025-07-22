function drawChart(raw_data) {

    let data = google.visualization.arrayToDataTable(raw_data);

    let options = {
        title: 'Ablehnungsgründe',
        backgroundColor: 'transparent'
    };

    let chart = new google.visualization.PieChart(document.getElementById('rejection_chart'));

    chart.draw(data, options);

    update_rejection_chart_colors();
}