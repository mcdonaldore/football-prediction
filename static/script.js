async function predictMatch() {

    let homeTeam =
        document.getElementById("homeTeam").value;

    let awayTeam =
        document.getElementById("awayTeam").value;

    const response = await fetch("/predict", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            home: homeTeam,
            away: awayTeam
        })

    });

    const data = await response.json();

    document.getElementById("homeXG")
        .innerHTML = data.home_xg;

    document.getElementById("awayXG")
        .innerHTML = data.away_xg;

    document.getElementById("homeProb")
        .innerHTML = data.home_prob + "%";

    document.getElementById("awayProb")
        .innerHTML = data.away_prob + "%";

    document.getElementById("drawProb")
        .innerHTML = data.draw_prob + "%";

    document.getElementById("prediction")
        .innerHTML = data.prediction;
}