function search_ticker() {
    let ticker = document.querySelector("#ticker_search_input").value
    window.location.href = "/trader/stockinfo/" + ticker + '/365/'
}