(() => {
    const ratingChartCanvas = document.getElementById("daily-rating-chart");
    const ratingChartDataElement = document.getElementById("daily-rating-chart-data");
    const dailyStatistics = JSON.parse(ratingChartDataElement.textContent);

    new Chart(ratingChartCanvas, {
        type: "line",
        data: {
            labels: dailyStatistics.dates,
            datasets: [
                {
                    label: "日別平均（左軸・星）",
                    data: dailyStatistics.averageRatings
                },
                {
                    type: "bar",
                    label: "投稿数（右軸・件）",
                    data: dailyStatistics.postCounts,
                    yAxisID: "y1"
                }
            ]
        },
        options: {
            scales: {
                y: {
                    position: "left",
                    min: 1,
                    max: 5
                },
                y1: {
                    position: "right",
                    beginAtZero: true,
                    ticks: { stepSize: 1 },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
})();
